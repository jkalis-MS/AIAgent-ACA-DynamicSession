"""Core weather data fetching logic shared across all sandbox implementations."""
import requests
from typing import Dict, Any, Optional


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
                timeout=5
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
            f"&temperature_unit=fahrenheit&forecast_days=5",
            timeout=5
        ).json()
        
        return {
            "destination": destination,
            "dates": dates,
            "current": weather['current'],
            "daily": weather['daily'],
            "error": None
        }
        
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

📆 5-Day Forecast:"""
    
    for i in range(5):
        high, low = daily['temperature_2m_max'][i], daily['temperature_2m_min'][i]
        result += f"\n{daily['time'][i]}: {icons.get(daily['weather_code'][i], '🌡️')} {high}°F ({f_to_c(high)}°C) / {low}°F ({f_to_c(low)}°C)"
        if daily['precipitation_sum'][i] > 0:
            result += f" 🌧️ {daily['precipitation_sum'][i]}in"
    
    result += f"\n\n💡 Travel Dates: {dates}"
    
    # Add personalized weather tips
    avg_high = sum(daily['temperature_2m_max'][:5]) / 5
    has_rain = any(daily['precipitation_sum'][i] > 0.1 for i in range(5))
    
    result += "\n\n👔 Packing Tips:"
    if avg_high > 75:
        result += "\n• Light, breathable clothing recommended"
    elif avg_high < 50:
        result += "\n• Pack warm layers and a jacket"
    
    if has_rain:
        result += "\n• Don't forget an umbrella or rain jacket"
    
    return result
