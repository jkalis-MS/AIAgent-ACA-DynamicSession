"""Daytona sandbox weather research implementation."""
import os
import logging
import time
from typing import Annotated

logger = logging.getLogger(__name__)


def research_weather_daytona(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (Daytona sandbox)."""
    
    # Check for Daytona API key
    api_key = os.getenv('DAYTONA_API_KEY')
    if not api_key:
        return "⚠️ DAYTONA_API_KEY not found in environment variables. Please configure Daytona credentials."
    
    try:
        from daytona import Daytona, DaytonaConfig
        
        start_time = time.time()
        logger.info(f"🚀 Daytona Sandbox creating for destination: {destination}")
        print(f"🚀 Daytona Sandbox creating for destination: {destination}")
        
        # Initialize Daytona client with configuration
        config = DaytonaConfig(api_key=api_key)
        daytona = Daytona(config)
        
        # Create the sandbox instance
        sandbox = daytona.create()
        create_time = int((time.time() - start_time) * 1000)
        logger.info(f"✓ Daytona Sandbox created ({create_time}ms)")
        print(f"✓ Daytona Sandbox created ({create_time}ms)")
        
        try:
            # Execute weather fetching code in sandbox
            logger.info(f"▶️ Daytona Sandbox code execution starting for destination: {destination} ({create_time}ms)")
            print(f"▶️ Daytona Sandbox code execution starting for destination: {destination} ({create_time}ms)")
            
            code = f'''
import requests

destination = "{destination}"
dates = "{dates}"

# Major city coordinates
cities = {{
    "new york": (40.7128, -74.0060), "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298), "boston": (42.3601, -71.0589),
    "san francisco": (37.7749, -122.4194), "seattle": (47.6062, -122.3321),
    "miami": (25.7617, -80.1918), "las vegas": (36.1699, -115.1398),
    "orlando": (28.5383, -81.3792), "denver": (39.7392, -104.9903)
}}

# Get coordinates
city_key = destination.lower().strip()
if city_key in cities:
    lat, lon = cities[city_key]
else:
    # Default to New York if city not found
    lat, lon = cities["new york"]

# Fetch weather data from Open-Meteo API
url = f"https://api.open-meteo.com/v1/forecast?latitude={{lat}}&longitude={{lon}}&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&temperature_unit=fahrenheit&timezone=auto&forecast_days=7"

try:
    response = requests.get(url)
    response.raise_for_status()
    weather_data = response.json()
    
    # Weather code mapping
    weather_codes = {{
        0: "☀️ Clear sky", 1: "🌤️ Mainly clear", 2: "⛅ Partly cloudy", 3: "☁️ Overcast",
        45: "🌫️ Foggy", 48: "🌫️ Rime fog", 51: "🌦️ Light drizzle", 53: "🌦️ Moderate drizzle",
        55: "🌧️ Dense drizzle", 61: "🌧️ Slight rain", 63: "🌧️ Moderate rain", 65: "🌧️ Heavy rain",
        71: "🌨️ Slight snow", 73: "🌨️ Moderate snow", 75: "❄️ Heavy snow", 77: "🌨️ Snow grains",
        80: "🌦️ Slight rain showers", 81: "🌧️ Moderate rain showers", 82: "⛈️ Violent rain showers",
        85: "🌨️ Slight snow showers", 86: "❄️ Heavy snow showers", 95: "⛈️ Thunderstorm",
        96: "⛈️ Thunderstorm with slight hail", 99: "⛈️ Thunderstorm with heavy hail"
    }}
    
    # Extract current weather
    current = weather_data.get("current", {{}})
    current_temp_f = current.get("temperature_2m", 0)
    current_temp_c = (current_temp_f - 32) * 5/9
    current_code = current.get("weather_code", 0)
    current_condition = weather_codes.get(current_code, "Unknown")
    
    # Extract daily forecast
    daily = weather_data.get("daily", {{}})
    times = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    codes = daily.get("weather_code", [])
    
    # Build result string
    result = f"🌍 Weather for {{destination.title()}}\\n"
    result += f"📅 Current: {{current_condition}} {{current_temp_f:.1f}}°F ({{current_temp_c:.1f}}°C)\\n\\n"
    
    if dates.lower() != "current" and len(times) > 0:
        result += "📆 7-Day Forecast:\\n"
        for i in range(min(7, len(times))):
            date = times[i]
            max_temp = max_temps[i]
            min_temp = min_temps[i]
            condition = weather_codes.get(codes[i], "Unknown")
            max_temp_c = (max_temp - 32) * 5/9
            min_temp_c = (min_temp - 32) * 5/9
            result += f"  {{date}}: {{condition}} High: {{max_temp:.1f}}°F ({{max_temp_c:.1f}}°C), Low: {{min_temp:.1f}}°F ({{min_temp_c:.1f}}°C)\\n"
    
    print(result)
    
except Exception as e:
    error_msg = f"⚠️ Error fetching weather data: {{str(e)}}"
    print(error_msg)
'''
            
            # Run the code in the Daytona sandbox
            response = sandbox.process.code_run(code)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            if response.exit_code != 0:
                error_msg = f"⚠️ Daytona Sandbox Error: Exit code {response.exit_code}\n{response.result}"
                logger.error(f"❌ Daytona execution failed: {error_msg} ({execution_time}ms)")
                print(f"❌ Daytona execution failed ({execution_time}ms)")
                return error_msg
            
            logger.info(f"✅ Daytona execution finished for destination: {destination} ({execution_time}ms)")
            print(f"✅ Daytona execution finished for destination: {destination} ({execution_time}ms)")
            
            # Return the output with Daytona sandbox indicator
            return f"🔒 [Daytona Sandbox]\n{response.result}"
            
        finally:
            # Clean up the sandbox
            try:
                sandbox.delete()
                logger.info("🧹 Daytona Sandbox cleaned up")
                print("🧹 Daytona Sandbox cleaned up")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error cleaning up Daytona sandbox: {cleanup_error}")
                print(f"⚠️ Error cleaning up Daytona sandbox: {cleanup_error}")
    
    except ImportError:
        error_msg = "⚠️ Daytona SDK not installed. Install with: pip install daytona"
        logger.error(error_msg)
        return error_msg
    
    except Exception as e:
        error_msg = f"⚠️ Daytona Sandbox Error: {str(e)}"
        logger.error(f"Daytona sandbox error: {error_msg}")
        print(f"❌ Daytona error: {error_msg}")
        return error_msg
