# TermCast Weather

An interactive ASCII weather dashboard that runs directly in your terminal. Features a real-time TUI with multiple weather views, mouse and keyboard navigation, and live data updates.

![TermCast Weather](termcastimg.png)

## Features

- 🌤️ **Interactive Dashboard**: Single command launches full TUI experience
- 🎨 **ASCII-Only Display**: Pure ASCII characters, no Unicode or emoji
- 📡 **Live Radar**: Animated ASCII radar with sweep animation
- 💨 **Wind Visualization**: Direction arrows and speed indicators
- 📊 **Pressure Charts**: Bar charts for atmospheric pressure trends
- 🌡️ **Heat Index**: Temperature and heat level indicators
- 🌬️ **Air Quality**: AQI readings with pollutant breakdown
- 🖱️ **Mouse & Keyboard**: Full navigation support
- 🔄 **Auto-refresh**: Live data updates every 30 seconds
- 📱 **80x24 Terminal**: Designed for standard terminal size

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Single Command Launch

```bash
# Default location (Tucson, Arizona)
python3 main.py

# Any location worldwide
python3 main.py --location "New York"
python3 main.py --location "London, UK"
python3 main.py --location "Tokyo, Japan"
```

### Navigation

**Mouse Navigation:**
- Click on the ASCII buttons at the bottom to switch views

**Keyboard Navigation:**
- `←` `→` Arrow keys to move between views
- `Enter` or `Space` to cycle through views
- `r` to manually refresh data
- `q` to quit

## View Modes

### 1. Radar View (Default)
- ASCII radar with characters: `.`, `+`, `#`, `@`
- Animated sweep line showing coverage
- Live precipitation data overlay
- Intensity legend

### 2. Wind View
- ASCII compass with directional arrows
- Wind speed and gust information
- Direction in degrees

### 3. Pressure View
- ASCII bar chart (950-1350 hPa range)
- Current vs normal pressure comparison
- Pressure trend visualization

### 4. Heat View
- Temperature and humidity display
- Heat index calculation
- Temperature bar chart (-20°C to 40°C)
- Heat level indicators (Comfortable/Moderate/High/Extreme)

### 5. Air Quality View
- European AQI scale (0-100)
- PM2.5, PM10, CO, NO2 readings
- AQI level indicators (Good/Moderate/Unhealthy)

## Dashboard Layout

```
+----------------------------------------------------------------+
| TermCast Weather - Tucson                                      |
| O 30.0C (feels 27.4C) | Wind: \ 16.9km/h                     |
| Updated: 15:06:52 | Press 'q' to quit                         |
|----------------------------------------------------------------|
|                                                                |
| RADAR:                                                         |
|           .    .                                               |
| ..........                                                  |
| ..........                                                  |
| ...........                                                 |
| ..........                                                  |
| ..........                                                  |
| ...... .                                                    |
| .....                     .                                 |
|  .                    .......                              |
|                      .........                             |
|                                                                |
| Precipitation: 0.0mm/h                                       |
| Intensity: . light, + moderate, # heavy, @ severe           |
|                                                                |
|----------------------------------------------------------------|
|          [Radar] [Wind] [Pressure] [Heat] [AQI]              |
+----------------------------------------------------------------+
```

## ASCII Characters Used

### Weather Icons
- `O` Sun (clear sky, day)
- `*` Moon/Stars (clear sky, night)
- `8` Heavy clouds
- `o` Light clouds
- `/` Light rain
- `\` Moderate rain
- `|` Heavy rain
- `T` Thunderstorm
- `:` Fog

### Radar Visualization
- ` ` Empty space
- `.` Light precipitation
- `+` Moderate precipitation
- `#` Heavy precipitation
- `@` Severe precipitation

### Wind Direction
- `^` North
- `/` Northeast
- `>` East
- `\` Southeast
- `v` South
- `\` Southwest
- `<` West
- `/` Northwest

## Technical Details

### Requirements
- Python 3.7+
- `requests` - HTTP library for API calls
- `curses` - Built-in terminal UI library

### API Information
Uses the [Open-Meteo API](https://open-meteo.com/):
- Free weather data (no API key required)
- Air quality data via separate endpoint
- Global coverage
- Real-time updates

### Performance
- Designed for 80x24 terminal size
- Smooth 10fps refresh rate
- Efficient data caching
- Minimal network requests

## Examples

```bash
# Launch dashboard for your city
python3 main.py --location "San Francisco"

# Monitor storm activity with live radar
python3 main.py --location "Oklahoma City"

# Check air quality in polluted areas
python3 main.py --location "Delhi, India"

# Quick weather check for vacation spot
python3 main.py --location "Cancun, Mexico"
```

## Troubleshooting

### Terminal Compatibility
- Requires a terminal that supports curses
- Works best with 80x24 or larger terminals
- Some older terminals may not support mouse events

### Location Issues
If a location isn't found:
- Add country: `"Paris, France"`
- Use full names: `"New York City"`
- Include state: `"Portland, Oregon"`

### Network Issues
- Check internet connection
- API may be temporarily unavailable
- Data refreshes automatically on recovery

### Display Issues
- Ensure terminal supports ASCII characters
- Some terminals may render differently
- Try resizing terminal window

## Development

### Adding New Views
1. Add new ViewMode enum value
2. Implement draw method in WeatherDashboard
3. Add navigation button
4. Update help text

### Customizing Display
- Modify ASCII characters in respective classes
- Adjust refresh rates and timing
- Customize color schemes (if supported)

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve TermCast Weather!

## License

This project is open source and available under the MIT License.