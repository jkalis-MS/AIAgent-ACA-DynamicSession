"""E2B Code Interpreter sandbox weather research implementation."""
import os
import logging
import time
from typing import Annotated
from e2b_code_interpreter import Sandbox

logger = logging.getLogger(__name__)


def research_weather_e2b(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (E2B sandbox)."""
    
    # Check for E2B API key
    api_key = os.getenv('E2B_API_KEY')
    if not api_key:
        return "⚠️ E2B_API_KEY not found in environment variables. Please configure E2B credentials."
    
    try:
        # Create E2B sandbox
        start_time = time.time()
        logger.info(f"🚀 E2B Sandbox creating for destination: {destination}")
        print(f"🚀 E2B Sandbox creating for destination: {destination}")
        sandbox = Sandbox.create(api_key=api_key)
        create_time = int((time.time() - start_time) * 1000)
        logger.info(f"✓ E2B Sandbox created ({create_time}ms)")
        print(f"✓ E2B Sandbox created ({create_time}ms)")
        
        try:
            # Execute weather fetching code in sandbox
            logger.info(f"▶️ E2B Sandbox code execution starting for destination: {destination} ({create_time}ms)")
            print(f"▶️ E2B Sandbox code execution starting for destination: {destination} ({create_time}ms)")
            code = f'''
import requests
import time

# Checkpoint 1: Started running code
start_time = time.time()
checkpoint_1 = 0  # Start at 0ms

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

lat, lon = cities.get(destination.lower(), (None, None))

# Checkpoint 2 will be set after GPS lookup
checkpoint_2 = None

# Fallback to geocoding if city not found
if not lat:
    try:
        geo_resp = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={{destination}}&count=1&format=json",
            timeout=5
        ).json()
        checkpoint_2 = int((time.time() - start_time) * 1000)  # Time after GPS lookup
        if geo_resp.get('results'):
            lat, lon = geo_resp['results'][0]['latitude'], geo_resp['results'][0]['longitude']
        else:
            print(f"⚠️ Could not find weather data for '{{destination}}'. Try a major city name.")
            exit(0)
    except Exception as e:
        checkpoint_2 = int((time.time() - start_time) * 1000)
        print(f"⚠️ Unable to fetch weather data: {{str(e)}}")
        exit(0)
else:
    # City found in local dict, no external call needed
    checkpoint_2 = int((time.time() - start_time) * 1000)

try:
    # Fetch weather data
    weather = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={{lat}}&longitude={{lon}}"
        f"&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&temperature_unit=fahrenheit&forecast_days=5",
        timeout=5
    ).json()
    
    # Checkpoint 3: Obtained weather forecast
    checkpoint_3 = int((time.time() - start_time) * 1000)
    
    curr = weather['current']
    daily = weather['daily']
    
    # Weather icons
    icons = {{
        0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
        51: "🌧️", 53: "🌧️", 55: "🌧️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
        71: "❄️", 73: "❄️", 75: "❄️", 80: "🌦️", 81: "🌦️", 82: "🌦️",
        95: "⛈️", 96: "⛈️", 99: "⛈️"
    }}
    
    def f_to_c(f):
        return round((f - 32) * 5/9, 1)
    
    temp_f = curr['temperature_2m']
    feels_f = curr['apparent_temperature']
    
    result = f"""🌍 Weather for {{destination.title()}}

📅 Current: {{icons.get(curr['weather_code'], '🌡️')}} {{temp_f}}°F ({{f_to_c(temp_f)}}°C)
Feels like: {{feels_f}}°F ({{f_to_c(feels_f)}}°C) | Wind: {{curr['wind_speed_10m']}} mph

📆 5-Day Forecast:"""
    
    for i in range(5):
        high, low = daily['temperature_2m_max'][i], daily['temperature_2m_min'][i]
        result += f"\\n{{daily['time'][i]}}: {{icons.get(daily['weather_code'][i], '🌡️')}} {{high}}°F ({{f_to_c(high)}}°C) / {{low}}°F ({{f_to_c(low)}}°C)"
        if daily['precipitation_sum'][i] > 0:
            result += f" 🌧️ {{daily['precipitation_sum'][i]}}in"
    
    result += f"\\n\\n💡 Travel Dates: {{dates}}"
    
    # Add personalized weather tips
    avg_high = sum(daily['temperature_2m_max'][:5]) / 5
    has_rain = any(daily['precipitation_sum'][i] > 0.1 for i in range(5))
    
    result += "\\n\\n👔 Packing Tips:"
    if avg_high > 75:
        result += "\\n• Light, breathable clothing recommended"
    elif avg_high < 50:
        result += "\\n• Pack warm layers and a jacket"
    
    if has_rain:
        result += "\\n• Don't forget an umbrella or rain jacket"
    
    # Checkpoint 4: Finished formatting response
    checkpoint_4 = int((time.time() - start_time) * 1000)
    
    # Append debug timing information
    result += "\\n\\n⏱️ Debug Timing (Sandbox Execution):"
    result += f"\\n  [1] Code started: 0ms"
    result += f"\\n  [2] GPS lookup completed: {{checkpoint_2}}ms"
    result += f"\\n  [3] Weather data obtained: {{checkpoint_3}}ms"
    result += f"\\n  [4] Response formatted: {{checkpoint_4}}ms"
    result += f"\\n  Total sandbox execution: {{checkpoint_4}}ms"
    
    print(result)
    
except Exception as e:
    print(f"⚠️ Error fetching weather data: {{str(e)}}")
'''
            
            execution = sandbox.run_code(code)
            execution_time = int((time.time() - start_time) * 1000)
            logger.info(f"✅ E2B Sandbox execution finished for destination: {destination} ({execution_time}ms)")
            print(f"✅ E2B Sandbox execution finished for destination: {destination} ({execution_time}ms)")
            
            if execution.error:
                return f"⚠️ E2B Sandbox Error: {execution.error.name}: {execution.error.value}"
            
            result_text = execution.logs.stdout[0] if execution.logs.stdout else 'No output'
            
            # Append total execution time (includes E2B overhead)
            result_text += f"\n  [5] Total end-to-end time: {execution_time}ms"
            
            result = f"🔒 [E2B Sandbox]\n{result_text}"
            return result
            
        finally:
            # Clean up sandbox
            sandbox.kill()
            total_time = int((time.time() - start_time) * 1000)
            logger.info(f"🔒 E2B Sandbox closed for destination: {destination} (total: {total_time}ms)")
            print(f"🔒 E2B Sandbox closed for destination: {destination} (total: {total_time}ms)")
    
    except Exception as e:
        return f"⚠️ Failed to execute in E2B sandbox: {str(e)}"
