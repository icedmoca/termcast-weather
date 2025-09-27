#!/usr/bin/env python3
"""
TermCast Weather - Interactive ASCII Dashboard
"""

import curses
import argparse
import requests
import time
import math
import random
from datetime import datetime
from typing import Dict, Any, List
from enum import Enum


class ViewMode(Enum):
    RADAR = "RADAR"
    WIND = "WIND"
    PRESSURE = "PRESSURE"
    HEAT = "HEAT"
    AQI = "AQI"


class WeatherAPI:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.air_quality_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    def get_coordinates(self, location: str) -> tuple:
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": location, "count": 1, "language": "en", "format": "json"}
        response = requests.get(geocoding_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("results"):
            result = data["results"][0]
            return result["latitude"], result["longitude"]
        raise ValueError(f"Location '{location}' not found")

    def fetch_weather(self, location: str) -> Dict[str, Any]:
        lat, lon = self.get_coordinates(location)
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
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "visibility",
            ],
            "timezone": "auto",
        }
        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "location": location,
            "coordinates": (lat, lon),
            "timestamp": datetime.now(),
            "data": data.get("current", {}),
        }

    def fetch_air_quality(self, lat: float, lon: float) -> Dict[str, Any]:
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
                "ozone",
            ],
        }
        response = requests.get(self.air_quality_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("current", {})


class ASCIIWeather:
    def get_weather_icon(self, code: int, is_day: bool) -> str:
        icons = {
            0: "O" if is_day else "*",
            1: "o" if is_day else "*",
            2: "o" if is_day else "*",
            3: "8",
            45: ":",
            51: "/",
            61: "/",
            63: "\\",
            65: "|",
            71: "*",
            75: "*",
            80: "/",
            81: "\\",
            82: "|",
            95: "T",
        }
        return icons.get(code, "?")

    def format_temperature(self, t: float) -> str:
        return f"{t:.1f}C"

    def format_wind_direction(self, deg: float) -> str:
        arrows = ["│", "╱", "─", "╲", "│", "╱", "─", "╲"]
        return arrows[int((deg + 22.5) / 45) % 8]


class ASCIIMap:
    def __init__(self, width: int = 60, height: int = 12):
        self.width = width
        self.height = height
        self.levels = [" ", "░", "▒", "▓", "█"]
        self.data = [[0 for _ in range(width)] for _ in range(height)]

    def _add_cell(self, x: int, y: int, size: int, intensity: int):
        for dy in range(-size, size + 1):
            for dx in range(-size, size + 1):
                if 0 <= x + dx < self.width and 0 <= y + dy < self.height:
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist <= size:
                        self.data[y + dy][x + dx] = min(4, max(0, self.data[y + dy][x + dx] + intensity - int(dist)))

    def update_scalar(self, value: float, min_val: float, max_val: float):
        if max_val == min_val:
            return
        norm = max(0, min(1, (value - min_val) / (max_val - min_val)))
        base_intensity = int(norm * 4)
        cx, cy = self.width // 2, self.height // 2
        for y in range(self.height):
            for x in range(self.width):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2) / max(self.width/2, self.height/2)
                intensity = max(0, base_intensity - int(dist * (base_intensity + 1)))
                self.data[y][x] = intensity

    def display(self) -> List[List[str]]:
        return [
            [self.levels[min(max(0, self.data[y][x]), 4)] for x in range(self.width)]
            for y in range(self.height)
        ]

    def get_color(self, intensity: int) -> int:
        if intensity <= 0:
            return 1  # White (default)
        elif intensity == 1:
            return 3  # Green (low)
        elif intensity == 2:
            return 4  # Yellow (medium)
        else:
            return 5  # Red (high)


class ASCIIRadar(ASCIIMap):
    def __init__(self, width: int = 60, height: int = 12):
        super().__init__(width, height)
        self.sweep_angle = 0

    def update(self, precipitation: float = 0):
        self.sweep_angle = (self.sweep_angle + 5) % 360
        # Decay slower
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < 0.5:  # 50% chance to decay
                    self.data[y][x] = max(0, self.data[y][x] - 1)
        # Add precipitation
        num_cells = max(10, min(30, int(precipitation * 10 + 10)))  # Boost for visibility
        intensity = min(4, int(precipitation * 2) + 2)
        for _ in range(num_cells):
            cx, cy = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            self._add_cell(cx, cy, random.randint(2, 5), intensity)
        # Fallback increased
        if precipitation == 0:
            for _ in range(10):
                cx, cy = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
                self._add_cell(cx, cy, 2, 2)

    def _in_sweep(self, x: int, y: int) -> bool:
        cx, cy = self.width // 2, self.height // 2
        dx, dy = x - cx, y - cy
        if dx == dy == 0:
            return True
        angle = math.degrees(math.atan2(-dy, dx)) % 360
        return abs((angle - self.sweep_angle + 540) % 360 - 180) < 45

    def display(self) -> List[List[str]]:
        return [
            [self.levels[min(self.data[y][x], 4)] if self._in_sweep(x, y) else " "
             for x in range(self.width)]
            for y in range(self.height)
        ]


class ASCIIWindMap(ASCIIMap):
    def __init__(self, width: int = 60, height: int = 12):
        super().__init__(width, height)
        self.arrows = ["│", "╱", "─", "╲", "│", "╱", "─", "╲"]
        self.direction = 0

    def update_wind(self, speed: float, direction: float):
        self.direction = direction
        self.data = [[0 for _ in range(self.width)] for _ in range(self.height)]
        norm = min(1, speed / 50.0)
        base_intensity = int(norm * 4) + 1
        dir_rad = math.radians(direction)
        spacing = 5
        offset_length = max(1, int(norm * 5))  # Longer lines for higher speed
        for base_y in range(0, self.height, spacing):
            for base_x in range(0, self.width, spacing):
                current_intensity = base_intensity
                for i in range(offset_length):
                    nx = (base_x + i * math.cos(dir_rad) * 2) % self.width
                    ny = (base_y + i * math.sin(dir_rad) * 2) % self.height
                    if 0 <= int(nx) < self.width and 0 <= int(ny) < self.height:
                        self.data[int(ny)][int(nx)] = max(self.data[int(ny)][int(nx)], current_intensity)
                    current_intensity -= 1
                    if current_intensity <= 0:
                        break

    def display(self) -> List[List[str]]:
        arrow_idx = int((self.direction + 22.5) / 45) % 8
        arrow = self.arrows[arrow_idx]
        return [
            [arrow if self.data[y][x] > 0 else " " for x in range(self.width)]
            for y in range(self.height)
        ]

    def get_color(self, intensity: int) -> int:
        if intensity <= 0:
            return 1
        return 4 if intensity < 3 else 5


class WeatherDashboard:
    def __init__(self, location: str):
        self.location = location
        self.api = WeatherAPI()
        self.ascii = ASCIIWeather()
        self.radar = ASCIIRadar()
        self.wind_map = ASCIIWindMap()
        self.pressure_map = ASCIIMap()
        self.heat_map = ASCIIMap()
        self.aqi_map = ASCIIMap()
        self.view = ViewMode.RADAR
        self.weather = None
        self.aqi = None
        self.running = True
        self.last_update = 0
        self.update_interval = 30
        self.stdscr = curses.initscr()
        curses.noecho(); curses.cbreak(); curses.curs_set(0)
        self.stdscr.keypad(True); self.stdscr.nodelay(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_CYAN, curses.COLOR_BLACK)

    def __del__(self):
        try:
            curses.nocbreak(); self.stdscr.keypad(False); curses.echo(); curses.endwin()
        except: pass

    def fetch(self):
        try:
            self.weather = self.api.fetch_weather(self.location)
            if self.weather:
                lat, lon = self.weather["coordinates"]
                self.aqi = self.api.fetch_air_quality(lat, lon)
            self.last_update = time.time()
        except Exception as e:
            pass

    def header(self):
        if not self.weather: return
        d = self.weather["data"]
        icon = self.ascii.get_weather_icon(d.get("weather_code", 0), d.get("is_day", 1))
        temp = self.ascii.format_temperature(d.get("temperature_2m", 0))
        feels = self.ascii.format_temperature(d.get("apparent_temperature", 0))
        wind = f"{self.ascii.format_wind_direction(d.get('wind_direction_10m', 0))} {d.get('wind_speed_10m', 0):.1f}km/h"
        ts = self.weather["timestamp"].strftime("%H:%M:%S")
        self.stdscr.addstr(0, 0, f"TermCast Weather - {self.location}")
        self.stdscr.addstr(1, 0, f"{icon} {temp} (feels {feels}) | Wind: {wind}")
        self.stdscr.addstr(2, 0, f"Updated: {ts} | Press 'q' to quit")
        self.stdscr.addstr(3, 0, "-" * 80)

    def draw_border(self, map_obj, start_y=5, start_x=10):
        self.stdscr.addstr(start_y - 1, start_x - 1, "+" + "-" * map_obj.width + "+")
        for i in range(map_obj.height):
            self.stdscr.addstr(start_y + i, start_x - 1, "|")
            self.stdscr.addstr(start_y + i, start_x + map_obj.width, "|")
        self.stdscr.addstr(start_y + map_obj.height, start_x - 1, "+" + "-" * map_obj.width + "+")
        # Compass labels
        self.stdscr.addstr(start_y - 2, start_x + map_obj.width // 2 - 1, "N")
        self.stdscr.addstr(start_y + map_obj.height + 1, start_x + map_obj.width // 2 - 1, "S")
        self.stdscr.addstr(start_y + map_obj.height // 2 - 1, start_x - 3, "W")
        self.stdscr.addstr(start_y + map_obj.height // 2 - 1, start_x + map_obj.width + 1, "E")
        # Scale
        self.stdscr.addstr(start_y + map_obj.height + 2, start_x, "Scale: ~50km radius centered on location")
        # Legend
        self.stdscr.addstr(start_y + map_obj.height + 3, start_x, "Legend: ░ low ▒ med ▓ high █ very high (elevation-like shading) | Colors: Green low, Yellow med, Red high")

    def draw_map(self, map_obj, start_y=5, start_x=10):
        self.draw_border(map_obj, start_y, start_x)
        lines = map_obj.display()
        for i, row in enumerate(lines):
            for j, char in enumerate(row):
                intensity = map_obj.data[i][j]
                color = map_obj.get_color(intensity)
                if self.view == ViewMode.HEAT and intensity < 2:
                    color = 6  # Cyan for cool
                if char != " ":
                    self.stdscr.addstr(start_y + i, start_x + j, char, curses.color_pair(color))
                else:
                    self.stdscr.addstr(start_y + i, start_x + j, char)
        # Center marker
        self.stdscr.addstr(start_y + map_obj.height // 2, start_x + map_obj.width // 2, "X", curses.color_pair(2))

    def draw_radar(self):
        if not self.weather:
            self.stdscr.addstr(5, 10, "Weather data not available")
            return
        d = self.weather["data"]
        p = d.get("precipitation", 0)
        self.radar.update(p)
        self.draw_map(self.radar)
        self.stdscr.addstr(19, 10, f"Precipitation: {p:.2f}mm/h{' (simulated view)' if p == 0 else ''}")

    def draw_wind(self):
        if not self.weather:
            self.stdscr.addstr(5, 10, "Weather data not available")
            return
        d = self.weather["data"]
        spd, gust, deg = d.get("wind_speed_10m", 0), d.get("wind_gusts_10m", 0), d.get("wind_direction_10m", 0)
        self.wind_map.update_wind(spd, deg)
        self.draw_map(self.wind_map)
        self.stdscr.addstr(19, 10, f"Speed: {spd:.1f} km/h | Gusts: {gust:.1f} km/h | Dir: {deg:.1f}°")

    def draw_pressure(self):
        if not self.weather:
            self.stdscr.addstr(5, 10, "Weather data not available")
            return
        p = self.weather["data"].get("pressure_msl", 1013.25)
        self.pressure_map.update_scalar(p, 950, 1050)
        self.draw_map(self.pressure_map)
        self.stdscr.addstr(19, 10, f"Pressure: {p:.1f} hPa")

    def draw_heat(self):
        if not self.weather:
            self.stdscr.addstr(5, 10, "Weather data not available")
            return
        d = self.weather["data"]
        t, hum, feels = d.get("temperature_2m", 0), d.get("relative_humidity_2m", 0), d.get("apparent_temperature", 0)
        self.heat_map.update_scalar(feels, -20, 40)
        self.draw_map(self.heat_map)
        self.stdscr.addstr(19, 10, f"Temp: {t:.1f}C | Feels: {feels:.1f}C | Hum: {hum:.1f}%")

    def draw_aqi(self):
        if not self.aqi:
            self.stdscr.addstr(5, 10, "AQI data not available")
            return
        aqi = self.aqi.get("european_aqi", 0)
        self.aqi_map.update_scalar(aqi, 0, 100)
        self.draw_map(self.aqi_map)
        self.stdscr.addstr(19, 10, f"AQI: {aqi:.0f}")

    def nav(self):
        buttons = ["Radar","Wind","Pressure","Heat","AQI"]
        for i, b in enumerate(buttons):
            x = 10 + i*12
            if self.view == ViewMode[b.upper()]:
                self.stdscr.addstr(23, x, f"[{b}]", curses.color_pair(2))
            else:
                self.stdscr.addstr(23, x, f"[{b}]", curses.color_pair(1))

    def panel(self):
        for y in range(5, 22): self.stdscr.addstr(y, 0, " "*80)
        if self.view == ViewMode.RADAR: self.draw_radar()
        elif self.view == ViewMode.WIND: self.draw_wind()
        elif self.view == ViewMode.PRESSURE: self.draw_pressure()
        elif self.view == ViewMode.HEAT: self.draw_heat()
        elif self.view == ViewMode.AQI: self.draw_aqi()

    def handle_key(self, k):
        if k == ord("q"): self.running = False
        elif k in (curses.KEY_LEFT, curses.KEY_RIGHT, ord("\n"), ord(" ")):
            v = list(ViewMode); i = v.index(self.view)
            self.view = v[(i-1)%len(v)] if k==curses.KEY_LEFT else v[(i+1)%len(v)]

    def run(self):
        self.fetch()
        while self.running:
            self.stdscr.clear()
            self.header(); self.panel(); self.nav()
            try:
                k = self.stdscr.getch()
                if k != curses.ERR: self.handle_key(k)
            except curses.error: pass
            if time.time()-self.last_update > self.update_interval: self.fetch()
            self.stdscr.refresh(); time.sleep(0.1)


def main():
    p = argparse.ArgumentParser(description="Interactive ASCII weather dashboard")
    p.add_argument("--location", default="Seattle, Washington")
    args = p.parse_args()
    try:
        WeatherDashboard(args.location).run()
    finally:
        curses.endwin()


if __name__ == "__main__":
    main()