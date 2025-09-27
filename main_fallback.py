#!/usr/bin/env python3
"""
Fallback version for terminals that don't support curses
Simple text-based dashboard with keyboard navigation
"""

import argparse
import requests
import time
import math
import random
import sys
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum

class ViewMode(Enum):
    RADAR = "Radar"
    WIND = "Wind"
    PRESSURE = "Pressure"
    HEAT = "Heat"
    AQI = "AQI"

class WeatherAPI:
    """Handles weather data fetching from Open-Meteo API"""
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.air_quality_url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    
    def get_coordinates(self, location: str) -> tuple:
        """Get coordinates for a location using Open-Meteo geocoding"""
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": location,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        try:
            response = requests.get(geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                result = data["results"][0]
                return result["latitude"], result["longitude"]
            else:
                raise ValueError(f"Location '{location}' not found")
                
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch coordinates: {e}")
    
    def fetch_weather(self, location: str) -> Dict[str, Any]:
        """Fetch current weather data for a location"""
        try:
            lat, lon = self.get_coordinates(location)
        except (ValueError, ConnectionError) as e:
            raise e
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m", 
                "apparent_temperature",
                "is_day",
                "precipitation",
                "rain",
                "snowfall",
                "weather_code",
                "cloud_cover",
                "pressure_msl",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "visibility"
            ],
            "timezone": "auto"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "current" not in data:
                raise ValueError("Invalid weather data received")
                
            return {
                "location": location,
                "coordinates": (lat, lon),
                "timestamp": datetime.now(),
                "data": data["current"]
            }
            
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to fetch weather data: {e}")
    
    def fetch_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch air quality data"""
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "european_aqi",
                "pm10",
                "pm2_5",
                "carbon_monoxide",
                "nitrogen_dioxide",
                "sulphur_dioxide",
                "ozone"
            ]
        }
        
        try:
            response = requests.get(self.air_quality_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "current" not in data:
                return {}
                
            return data["current"]
            
        except requests.RequestException:
            return {}

class ASCIIWeather:
    """ASCII-only weather visualization"""
    
    def get_weather_icon(self, weather_code: int, is_day: bool) -> str:
        """Convert weather code to ASCII icon"""
        icons = {
            0: "O" if is_day else "*",      # Clear sky
            1: "o" if is_day else "*",      # Mainly clear
            2: "o" if is_day else "*",      # Partly cloudy
            3: "8",                         # Overcast
            45: ":",                        # Fog
            48: ":",                        # Depositing rime fog
            51: "/",                        # Light drizzle
            53: "/",                        # Moderate drizzle
            55: "\\",                       # Dense drizzle
            61: "/",                        # Slight rain
            63: "\\",                       # Moderate rain
            65: "|",                        # Heavy rain
            71: "*",                        # Slight snow
            73: "*",                        # Moderate snow
            75: "*",                        # Heavy snow
            77: "*",                        # Snow grains
            80: "/",                        # Slight rain showers
            81: "\\",                       # Moderate rain showers
            82: "|",                        # Violent rain showers
            85: "*",                        # Slight snow showers
            86: "*",                        # Heavy snow showers
            95: "T",                        # Thunderstorm
            96: "T",                        # Thunderstorm with slight hail
            99: "T"                         # Thunderstorm with heavy hail
        }
        return icons.get(weather_code, "?")
    
    def format_temperature(self, temp: float) -> str:
        """Format temperature"""
        return f"{temp:.1f}C"
    
    def format_wind_direction(self, direction: float) -> str:
        """Convert wind direction to ASCII arrow"""
        directions = ["^", "/", ">", "\\", "v", "\\", "<", "/"]
        index = int((direction + 22.5) / 45) % 8
        return directions[index]

class ASCIIRadar:
    """ASCII radar visualization"""
    
    def __init__(self, width: int = 60, height: int = 12):
        self.width = width
        self.height = height
        self.sweep_angle = 0
        self.intensity_levels = [' ', '.', '+', '#', '@']
        self.radar_data = self._generate_base_radar_data()
    
    def _generate_base_radar_data(self) -> List[List[int]]:
        """Generate base radar data with precipitation simulation"""
        data = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Add some simulated precipitation patterns
        for _ in range(random.randint(2, 5)):
            center_x = random.randint(0, self.width - 1)
            center_y = random.randint(0, self.height - 1)
            radius = random.randint(2, 5)
            intensity = random.randint(2, 4)
            
            self._add_precipitation_cell(data, center_x, center_y, radius, intensity)
        
        return data
    
    def _add_precipitation_cell(self, data: List[List[int]], x: int, y: int, radius: int, intensity: int):
        """Add a precipitation cell to radar data"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                distance = math.sqrt(dx*dx + dy*dy)
                if distance <= radius:
                    px, py = x + dx, y + dy
                    if 0 <= px < self.width and 0 <= py < self.height:
                        cell_intensity = max(1, intensity - int(distance))
                        data[py][px] = max(data[py][px], cell_intensity)
    
    def _update_sweep(self):
        """Update the radar sweep angle for animation"""
        self.sweep_angle = (self.sweep_angle + 3) % 360
    
    def _is_in_sweep(self, x: int, y: int) -> bool:
        """Check if a point is currently in the radar sweep"""
        center_x, center_y = self.width // 2, self.height // 2
        dx, dy = x - center_x, y - center_y
        
        if dx == 0 and dy == 0:
            return True
        
        angle = math.degrees(math.atan2(-dy, dx))
        angle = (angle + 360) % 360
        
        sweep_range = 30
        sweep_start = (self.sweep_angle - sweep_range/2) % 360
        sweep_end = (self.sweep_angle + sweep_range/2) % 360
        
        if sweep_start <= sweep_end:
            return sweep_start <= angle <= sweep_end
        else:
            return angle >= sweep_start or angle <= sweep_end
    
    def _get_radar_char(self, x: int, y: int) -> str:
        """Get the appropriate character for a radar position"""
        intensity = self.radar_data[y][x]
        
        if self._is_in_sweep(x, y):
            return self.intensity_levels[min(intensity, len(self.intensity_levels) - 1)]
        
        return ' ' if intensity == 0 else '.'
    
    def update_radar(self, precipitation: float = 0):
        """Update radar based on current precipitation"""
        self._update_sweep()
        
        # Occasionally add new precipitation cells
        if random.random() < 0.1 and precipitation > 0:
            center_x = random.randint(0, self.width - 1)
            center_y = random.randint(0, self.height - 1)
            intensity = min(4, int(precipitation / 2) + 1)
            self.add_storm_cell(center_x, center_y, intensity, random.randint(2, 4))
    
    def add_storm_cell(self, x: int, y: int, intensity: int = 3, size: int = 3):
        """Add a storm cell to the radar"""
        self._add_precipitation_cell(self.radar_data, x, y, size, intensity)
    
    def get_radar_display(self) -> List[str]:
        """Get radar display lines"""
        lines = []
        for y in range(self.height):
            line = ""
            for x in range(self.width):
                char = self._get_radar_char(x, y)
                line += char
            lines.append(line)
        return lines

class FallbackDashboard:
    """Fallback dashboard for terminals without curses support"""
    
    def __init__(self, location: str):
        self.location = location
        self.weather_api = WeatherAPI()
        self.ascii_weather = ASCIIWeather()
        self.radar = ASCIIRadar(60, 12)
        self.current_view = ViewMode.RADAR
        self.weather_data = None
        self.air_quality_data = None
        
    def fetch_data(self):
        """Fetch weather and air quality data"""
        try:
            self.weather_data = self.weather_api.fetch_weather(self.location)
            if self.weather_data:
                lat, lon = self.weather_data["coordinates"]
                self.air_quality_data = self.weather_api.fetch_air_quality(lat, lon)
        except Exception as e:
            print(f"Error fetching data: {e}")
    
    def clear_screen(self):
        """Clear screen using ANSI escape codes"""
        print("\033[2J\033[H", end="")
    
    def draw_header(self):
        """Draw weather header section"""
        if not self.weather_data:
            return
        
        data = self.weather_data["data"]
        location = self.weather_data["location"]
        timestamp = self.weather_data["timestamp"].strftime("%H:%M:%S")
        
        # Weather icon and basic info
        weather_code = data.get("weather_code", 0)
        is_day = data.get("is_day", 1)
        icon = self.ascii_weather.get_weather_icon(weather_code, is_day)
        temp = self.ascii_weather.format_temperature(data.get("temperature_2m", 0))
        feels_like = self.ascii_weather.format_temperature(data.get("apparent_temperature", 0))
        
        # Wind info
        wind_speed = data.get("wind_speed_10m", 0)
        wind_direction = data.get("wind_direction_10m", 0)
        wind_arrow = self.ascii_weather.format_wind_direction(wind_direction)
        
        print("=" * 80)
        print(f"TermCast Weather - {location}")
        print(f"{icon} {temp} (feels {feels_like}) | Wind: {wind_arrow} {wind_speed:.1f}km/h")
        print(f"Updated: {timestamp}")
        print("-" * 80)
    
    def draw_radar_view(self):
        """Draw radar view"""
        if not self.weather_data:
            return
        
        data = self.weather_data["data"]
        precipitation = data.get("precipitation", 0)
        
        # Update radar
        self.radar.update_radar(precipitation)
        
        print("RADAR VIEW:")
        print()
        radar_lines = self.radar.get_radar_display()
        for line in radar_lines:
            print("  " + line)
        
        print()
        print(f"Precipitation: {precipitation:.1f}mm/h")
        print("Intensity: . light, + moderate, # heavy, @ severe")
        print()
    
    def draw_wind_view(self):
        """Draw wind view"""
        if not self.weather_data:
            return
        
        data = self.weather_data["data"]
        wind_speed = data.get("wind_speed_10m", 0)
        wind_direction = data.get("wind_direction_10m", 0)
        wind_gusts = data.get("wind_gusts_10m", 0)
        
        # Simple compass
        compass = [
            "     N",
            "     ^",
            "     |",
            "W <--+--> E",
            "     |",
            "     v",
            "     S"
        ]
        
        print("WIND VIEW:")
        print()
        for line in compass:
            print("  " + line)
        
        print()
        print(f"Speed: {wind_speed:.1f} km/h")
        print(f"Gusts: {wind_gusts:.1f} km/h")
        print(f"Direction: {wind_direction:.1f} degrees")
        print()
    
    def draw_pressure_view(self):
        """Draw pressure view"""
        if not self.weather_data:
            return
        
        data = self.weather_data["data"]
        pressure = data.get("pressure_msl", 1013.25)
        
        # Pressure bar chart
        normalized_pressure = int((pressure - 950) / 100 * 40)
        normalized_pressure = max(0, min(40, normalized_pressure))
        
        bar = "=" * normalized_pressure + "-" * (40 - normalized_pressure)
        
        print("PRESSURE VIEW:")
        print()
        print(f"Current: {pressure:.1f} hPa")
        print(f"Normal: 1013.25 hPa")
        print(f"Difference: {pressure - 1013.25:+.1f} hPa")
        print()
        print("950 hPa <" + bar + "> 1350 hPa")
        print()
    
    def draw_heat_view(self):
        """Draw heat index view"""
        if not self.weather_data:
            return
        
        data = self.weather_data["data"]
        temp = data.get("temperature_2m", 0)
        humidity = data.get("relative_humidity_2m", 0)
        feels_like = data.get("apparent_temperature", 0)
        
        # Temperature bar
        temp_bar_length = int((temp + 20) / 60 * 40)  # -20C to 40C range
        temp_bar_length = max(0, min(40, temp_bar_length))
        temp_bar = "=" * temp_bar_length + "-" * (40 - temp_bar_length)
        
        print("HEAT INDEX VIEW:")
        print()
        print(f"Temperature: {temp:.1f}C")
        print(f"Feels like: {feels_like:.1f}C")
        print(f"Humidity: {humidity:.1f}%")
        print()
        print("-20C <" + temp_bar + "> 40C")
        print()
        
        # Heat level indicator
        if feels_like > 35:
            heat_level = "EXTREME HEAT"
        elif feels_like > 30:
            heat_level = "HIGH HEAT"
        elif feels_like > 25:
            heat_level = "MODERATE HEAT"
        else:
            heat_level = "COMFORTABLE"
        
        print(f"Heat Level: {heat_level}")
        print()
    
    def draw_aqi_view(self):
        """Draw air quality view"""
        if not self.air_quality_data:
            print("AQI VIEW:")
            print()
            print("Air quality data not available")
            print()
            return
        
        aqi = self.air_quality_data.get("european_aqi", 0)
        pm25 = self.air_quality_data.get("pm2_5", 0)
        pm10 = self.air_quality_data.get("pm10", 0)
        co = self.air_quality_data.get("carbon_monoxide", 0)
        no2 = self.air_quality_data.get("nitrogen_dioxide", 0)
        
        # AQI bar
        aqi_bar_length = int(aqi / 100 * 40)  # 0-100 scale
        aqi_bar_length = max(0, min(40, aqi_bar_length))
        aqi_bar = "=" * aqi_bar_length + "-" * (40 - aqi_bar_length)
        
        print("AIR QUALITY VIEW:")
        print()
        print(f"European AQI: {aqi:.0f}")
        print("0 <" + aqi_bar + "> 100")
        print()
        print(f"PM2.5: {pm25:.1f} ug/m3")
        print(f"PM10: {pm10:.1f} ug/m3")
        print(f"CO: {co:.1f} mg/m3")
        print(f"NO2: {no2:.1f} ug/m3")
        print()
        
        # AQI level
        if aqi <= 50:
            aqi_level = "GOOD"
        elif aqi <= 100:
            aqi_level = "MODERATE"
        else:
            aqi_level = "UNHEALTHY"
        
        print(f"Level: {aqi_level}")
        print()
    
    def draw_navigation(self):
        """Draw navigation info"""
        print("Navigation: [1] Radar [2] Wind [3] Pressure [4] Heat [5] AQI [r] Refresh [q] Quit")
        print("=" * 80)
    
    def run(self):
        """Main dashboard loop"""
        self.fetch_data()
        
        while True:
            self.clear_screen()
            self.draw_header()
            
            # Draw current view
            if self.current_view == ViewMode.RADAR:
                self.draw_radar_view()
            elif self.current_view == ViewMode.WIND:
                self.draw_wind_view()
            elif self.current_view == ViewMode.PRESSURE:
                self.draw_pressure_view()
            elif self.current_view == ViewMode.HEAT:
                self.draw_heat_view()
            elif self.current_view == ViewMode.AQI:
                self.draw_aqi_view()
            
            self.draw_navigation()
            
            # Get user input
            try:
                choice = input("Enter choice: ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == 'r':
                    self.fetch_data()
                elif choice == '1':
                    self.current_view = ViewMode.RADAR
                elif choice == '2':
                    self.current_view = ViewMode.WIND
                elif choice == '3':
                    self.current_view = ViewMode.PRESSURE
                elif choice == '4':
                    self.current_view = ViewMode.HEAT
                elif choice == '5':
                    self.current_view = ViewMode.AQI
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fallback ASCII weather dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--location", 
        default="Tucson, Arizona",
        help="Location to get weather for (default: Tucson, Arizona)"
    )
    
    args = parser.parse_args()
    
    try:
        dashboard = FallbackDashboard(args.location)
        dashboard.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
