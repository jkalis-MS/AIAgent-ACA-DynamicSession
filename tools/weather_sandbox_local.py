"""Local (non-sandboxed) weather research implementation."""
import logging
import time
import requests
from typing import Annotated, Dict, Any

logger = logging.getLogger(__name__)

# Simple in-memory TTL cache for weather data
# Avoids duplicate API calls when chart_weather runs right after research_weather
_weather_cache: Dict[str, tuple] = {}  # key -> (timestamp, data)
_CACHE_TTL = 600  # 10 minutes


def get_weather_data(destination: str, dates: str = "current") -> Dict[str, Any]:
    """
    Core weather data fetching logic.
    Returns structured weather data that can be formatted by any sandbox.
    
    Args:
        destination: The destination to research weather for
        dates: Travel dates (optional)
    
    Returns:
        dict with keys: destination, current, daily, dates, error (if any)
    """
    # Check cache first
    cache_key = destination.lower().strip()
    if cache_key in _weather_cache:
        cached_time, cached_data = _weather_cache[cache_key]
        if time.time() - cached_time < _CACHE_TTL:
            logger.info(f"♻️ Using cached weather data for {destination} ({int(time.time() - cached_time)}s old)")
            print(f"♻️ Using cached weather data for {destination} ({int(time.time() - cached_time)}s old)")
            return cached_data

    # Major city coordinates
    cities = {
        "new york": (40.7128, -74.0060), "los angeles": (34.0522, -118.2437),
        "chicago": (41.8781, -87.6298), "boston": (42.3601, -71.0589),
        "san francisco": (37.7749, -122.4194), "seattle": (47.6062, -122.3321),
        "miami": (25.7617, -80.1918), "las vegas": (36.1699, -115.1398),
        "orlando": (28.5383, -81.3792), "denver": (39.7392, -104.9903)
    }
    
    lat, lon = cities.get(destination.lower(), (None, None))
    
    # Fallback to geocoding if city not found
    if not lat:
        try:
            geo_resp = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={destination}&count=1&format=json",
                timeout=15
            ).json()
            if geo_resp.get('results'):
                lat, lon = geo_resp['results'][0]['latitude'], geo_resp['results'][0]['longitude']
            else:
                return {
                    "error": f"Could not find weather data for '{destination}'. Try a major city name.",
                    "destination": destination,
                    "dates": dates
                }
        except Exception as e:
            return {
                "error": f"Unable to fetch weather data: {str(e)}",
                "destination": destination,
                "dates": dates
            }
    
    try:
        # Fetch weather data
        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
            f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
            f"&temperature_unit=fahrenheit&forecast_days=14",
            timeout=15
        ).json()
        
        result = {
            "destination": destination,
            "dates": dates,
            "current": weather['current'],
            "daily": weather['daily'],
            "error": None
        }
        _weather_cache[cache_key] = (time.time(), result)
        return result
        
    except Exception as e:
        return {
            "error": f"Error fetching weather data: {str(e)}",
            "destination": destination,
            "dates": dates
        }


def format_weather_result(weather_data: Dict[str, Any]) -> str:
    """
    Format weather data into a human-readable string.
    
    Args:
        weather_data: Dictionary returned by get_weather_data()
    
    Returns:
        Formatted weather string
    """
    if weather_data.get('error'):
        return f"⚠️ {weather_data['error']}"
    
    destination = weather_data['destination']
    dates = weather_data['dates']
    curr = weather_data['current']
    daily = weather_data['daily']
    
    # Weather icons
    icons = {
        0: "☀️", 1: "🌤️", 2: "⛅", 3: "☁️", 45: "🌫️", 48: "🌫️",
        51: "🌧️", 53: "🌧️", 55: "🌧️", 61: "🌧️", 63: "🌧️", 65: "🌧️",
        71: "❄️", 73: "❄️", 75: "❄️", 80: "🌦️", 81: "🌦️", 82: "🌦️",
        95: "⛈️", 96: "⛈️", 99: "⛈️"
    }
    
    def f_to_c(f):
        return round((f - 32) * 5/9, 1)
    
    temp_f = curr['temperature_2m']
    feels_f = curr['apparent_temperature']
    
    result = f"""🌍 Weather for {destination.title()}

📅 Current: {icons.get(curr['weather_code'], '🌡️')} {temp_f}°F ({f_to_c(temp_f)}°C)
Feels like: {feels_f}°F ({f_to_c(feels_f)}°C) | Wind: {curr['wind_speed_10m']} mph

📆 14-Day Forecast:"""
    
    for i in range(len(daily['time'])):
        high, low = daily['temperature_2m_max'][i], daily['temperature_2m_min'][i]
        result += f"\n{daily['time'][i]}: {icons.get(daily['weather_code'][i], '🌡️')} {high}°F ({f_to_c(high)}°C) / {low}°F ({f_to_c(low)}°C)"
        if daily['precipitation_sum'][i] > 0:
            result += f" 🌧️ {daily['precipitation_sum'][i]}in"
    
    result += f"\n\n💡 Travel Dates: {dates}"
    
    # Add personalized weather tips
    num_days = len(daily['temperature_2m_max'])
    avg_high = sum(daily['temperature_2m_max'][:num_days]) / num_days
    has_rain = any(daily['precipitation_sum'][i] > 0.1 for i in range(num_days))
    
    result += "\n\n👔 Packing Tips:"
    if avg_high > 75:
        result += "\n• Light, breathable clothing recommended"
    elif avg_high < 50:
        result += "\n• Pack warm layers and a jacket"
    
    if has_rain:
        result += "\n• Don't forget an umbrella or rain jacket"
    
    return result


def research_weather_local(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (Local execution)."""
    start_time = time.time()
    checkpoint_1 = 0  # Start at 0ms
    
    logger.info(f"🏠 Local execution starting for destination: {destination}")
    print(f"🏠 Local execution starting for destination: {destination}")
    
    execution_time = int((time.time() - start_time) * 1000)
    logger.info(f"▶️ Local code execution starting for destination: {destination} ({execution_time}ms)")
    print(f"▶️ Local code execution starting for destination: {destination} ({execution_time}ms)")
    
    # Get weather data with timing
    weather_data = get_weather_data(destination, dates)
    checkpoint_3 = int((time.time() - start_time) * 1000)  # After data fetch
    
    # Format result with timing
    result = format_weather_result(weather_data)
    checkpoint_4 = int((time.time() - start_time) * 1000)  # After formatting
    
    # Append debug timing information
    execution_time = int((time.time() - start_time) * 1000)
    result += "\n\n⏱️ Debug Timing (Local Execution):"
    result += f"\n  [1] Weather data obtained: {checkpoint_4}ms"
    result += f"\n  [2] Total execution time: {execution_time}ms"
    result += f"\n  Infrastructure time: {execution_time - checkpoint_4}ms"
    
    logger.info(f"✅ Local execution finished for destination: {destination} ({execution_time}ms)")
    print(f"✅ Local execution finished for destination: {destination} ({execution_time}ms)")
    
    return f"🏠 [Local Execution]\n{result}"
