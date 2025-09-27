#!/usr/bin/env python3
"""
ASCII Radar Module - Block-based radar visualization for weather data
"""

import time
import random
import math
from typing import Dict, Any, List
from datetime import datetime

class ASCIIRadar:
    """Creates ASCII radar visualizations using block characters"""
    
    def __init__(self, width: int = 60, height: int = 30):
        self.width = width
        self.height = height
        self.sweep_angle = 0
        self.intensity_levels = [' ', '░', '▒', '▓', '@', '#']
        self.radar_data = self._generate_base_radar_data()
    
    def _generate_base_radar_data(self) -> List[List[int]]:
        """Generate base radar data with some precipitation simulation"""
        data = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # Add some simulated precipitation patterns
        for _ in range(random.randint(3, 8)):
            center_x = random.randint(0, self.width - 1)
            center_y = random.randint(0, self.height - 1)
            radius = random.randint(3, 8)
            intensity = random.randint(2, 5)
            
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
                        # Intensity decreases with distance from center
                        cell_intensity = max(1, intensity - int(distance))
                        data[py][px] = max(data[py][px], cell_intensity)
    
    def _update_sweep(self):
        """Update the radar sweep angle for animation"""
        self.sweep_angle = (self.sweep_angle + 2) % 360
    
    def _is_in_sweep(self, x: int, y: int) -> bool:
        """Check if a point is currently in the radar sweep"""
        # Convert to polar coordinates relative to center
        center_x, center_y = self.width // 2, self.height // 2
        dx, dy = x - center_x, y - center_y
        
        if dx == 0 and dy == 0:
            return True
        
        # Calculate angle from center
        angle = math.degrees(math.atan2(-dy, dx))  # -dy because screen y is inverted
        angle = (angle + 360) % 360
        
        # Check if within sweep range (30 degree sweep)
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
        
        # If in sweep, show the intensity
        if self._is_in_sweep(x, y):
            return self.intensity_levels[min(intensity, len(self.intensity_levels) - 1)]
        
        # If not in sweep, show as empty or very light
        return ' ' if intensity == 0 else '.'
    
    def create_radar_view(self, weather_data: Dict[str, Any]) -> str:
        """Create ASCII radar visualization"""
        data = weather_data["data"]
        location = weather_data["location"]
        timestamp = weather_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        
        # Update sweep for animation
        self._update_sweep()
        
        # Get current precipitation data
        precipitation = data.get("precipitation", 0)
        rain = data.get("rain", 0)
        snowfall = data.get("snowfall", 0)
        
        # Build radar display
        radar_lines = []
        
        # Header
        radar_lines.append("╔" + "═" * (self.width + 2) + "╗")
        radar_lines.append("║" + f" ASCII RADAR - {location:<{self.width-12}}" + "║")
        radar_lines.append("║" + f" {timestamp:<{self.width}}" + "║")
        radar_lines.append("╠" + "═" * (self.width + 2) + "╣")
        
        # Radar grid
        for y in range(self.height):
            line = "║"
            for x in range(self.width):
                char = self._get_radar_char(x, y)
                line += char
            line += "║"
            radar_lines.append(line)
        
        # Footer with legend and data
        radar_lines.append("╠" + "═" * (self.width + 2) + "╣")
        
        # Legend
        legend = "Intensity: "
        for i, char in enumerate(self.intensity_levels):
            if i == 0:
                legend += f"'{char}'=none "
            elif i == 1:
                legend += f"'{char}'=light "
            elif i == 2:
                legend += f"'{char}'=moderate "
            elif i == 3:
                legend += f"'{char}'=heavy "
            elif i == 4:
                legend += f"'{char}'=severe "
            elif i == 5:
                legend += f"'{char}'=extreme"
        
        radar_lines.append("║" + f" {legend:<{self.width}}" + "║")
        
        # Current precipitation data
        radar_lines.append("║" + f" Current: {precipitation:.1f}mm/h  Rain: {rain:.1f}mm  Snow: {snowfall:.1f}mm"[:self.width+1].ljust(self.width+2) + "║")
        
        # Sweep indicator
        sweep_indicator = " " * (self.width // 2 - 5) + "╱ SWEEP ╲" + " " * (self.width // 2 - 5)
        radar_lines.append("║" + sweep_indicator[:self.width+2].ljust(self.width+2) + "║")
        
        radar_lines.append("╚" + "═" * (self.width + 2) + "╝")
        
        return "\n".join(radar_lines)
    
    def create_live_radar(self, weather_data: Dict[str, Any], duration: int = 30):
        """Create a live updating radar view"""
        import sys
        
        print("\033[2J\033[H", end="")  # Clear screen and move cursor to top
        
        start_time = time.time()
        while time.time() - start_time < duration:
            radar_view = self.create_radar_view(weather_data)
            print(radar_view)
            print(f"\nLive radar updating... Press Ctrl+C to stop")
            
            time.sleep(1)  # Update every second
            
            # Clear screen for next update
            print("\033[2J\033[H", end="")
    
    def add_storm_cell(self, x: int, y: int, intensity: int = 4, size: int = 5):
        """Add a storm cell to the radar"""
        self._add_precipitation_cell(self.radar_data, x, y, size, intensity)
    
    def clear_radar(self):
        """Clear all radar data"""
        self.radar_data = [[0 for _ in range(self.width)] for _ in range(self.height)]
    
    def update_precipitation_data(self, precipitation_data: Dict[str, float]):
        """Update radar based on real precipitation data"""
        # This could be expanded to use actual precipitation radar data
        # For now, we'll just regenerate some cells based on current precipitation
        if precipitation_data.get("precipitation", 0) > 0:
            # Add some precipitation cells
            for _ in range(random.randint(1, 3)):
                center_x = random.randint(self.width // 4, 3 * self.width // 4)
                center_y = random.randint(self.height // 4, 3 * self.height // 4)
                intensity = min(5, int(precipitation_data["precipitation"] / 2) + 1)
                self.add_storm_cell(center_x, center_y, intensity, random.randint(3, 6))

# Example usage and testing
if __name__ == "__main__":
    radar = ASCIIRadar()
    
    # Create sample weather data
    sample_weather = {
        "location": "Test Location",
        "timestamp": datetime.now(),
        "data": {
            "precipitation": 2.5,
            "rain": 2.0,
            "snowfall": 0.5
        }
    }
    
    # Test radar view
    radar_view = radar.create_radar_view(sample_weather)
    print(radar_view)
