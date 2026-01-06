"""Azure Container Apps dynamic sessions weather research implementation."""
import os
import json
import logging
import time
import requests
from typing import Annotated

logger = logging.getLogger(__name__)


def research_weather_aca(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (ACA sandbox)."""
    
    # Check for required environment variables
    pool_management_endpoint = os.getenv('ACA_POOL_MANAGEMENT_ENDPOINT')
    
    if not pool_management_endpoint:
        return "⚠️ ACA_POOL_MANAGEMENT_ENDPOINT not found in environment variables. Please configure Azure Container Apps session pool."
    
    try:
        # Import Azure identity for authentication
        from azure.identity import DefaultAzureCredential
        
        start_time = time.time()
        logger.info(f"☁️ ACA Sandbox creating for destination: {destination}")
        print(f"☁️ ACA Sandbox creating for destination: {destination}")
        
        # Create DefaultAzureCredential for authentication
        credential = DefaultAzureCredential()
        
        # Get access token for Azure Container Apps sessions
        token = credential.get_token("https://dynamicsessions.io/.default")
        auth_header = f"Bearer {token.token}"
        
        # Generate a session identifier (use a consistent ID for session reuse)
        session_id = f"weather-{destination.lower().replace(' ', '-')}"
        
        create_time = int((time.time() - start_time) * 1000)
        logger.info(f"✓ ACA Sandbox session ready ({create_time}ms)")
        print(f"✓ ACA Sandbox session ready ({create_time}ms)")
        
        logger.info(f"▶️ ACA Sandbox code execution starting for destination: {destination} ({create_time}ms)")
        print(f"▶️ ACA Sandbox code execution starting for destination: {destination} ({create_time}ms)")
        
        # Prepare Python code to execute in the session
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

lat, lon = cities.get(destination.lower(), (None, None))

# Fallback to geocoding if city not found
if not lat:
    try:
        geo_resp = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={{destination}}&count=1&format=json",
            timeout=5
        ).json()
        if geo_resp.get('results'):
            lat, lon = geo_resp['results'][0]['latitude'], geo_resp['results'][0]['longitude']
        else:
            print(f"⚠️ Could not find weather data for '{{destination}}'. Try a major city name.")
            exit(0)
    except Exception as e:
        print(f"⚠️ Unable to fetch weather data: {{str(e)}}")
        exit(0)

try:
    # Fetch weather data
    weather = requests.get(
        f"https://api.open-meteo.com/v1/forecast?latitude={{lat}}&longitude={{lon}}"
        f"&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
        f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&temperature_unit=fahrenheit&forecast_days=5",
        timeout=5
    ).json()
    
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
    
    print(result)
    
except Exception as e:
    print(f"⚠️ Error fetching weather data: {{str(e)}}")
'''
        
        # Execute code in ACA session via REST API
        # POST https://<endpoint>/code/execute?api-version=2024-02-02-preview&identifier=<session_id>
        execute_url = f"{pool_management_endpoint}/code/execute?api-version=2024-02-02-preview&identifier={session_id}"
        
        payload = {
            "properties": {
                "codeInputType": "inline",
                "executionType": "synchronous",
                "code": code
            }
        }
        
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Explicitly encode payload as UTF-8 JSON
        json_payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        
        response = requests.post(
            execute_url, 
            data=json_payload, 
            headers=headers, 
            timeout=30
        )
        response.raise_for_status()
        
        execution_time = int((time.time() - start_time) * 1000)
        logger.info(f"✅ ACA Sandbox execution finished for destination: {destination} ({execution_time}ms)")
        print(f"✅ ACA Sandbox execution finished for destination: {destination} ({execution_time}ms)")
        
        # Parse response - explicitly handle UTF-8
        response.encoding = 'utf-8'
        result_data = response.json()
        
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"🔒 ACA Sandbox session complete for destination: {destination} (total: {total_time}ms)")
        print(f"🔒 ACA Sandbox session complete for destination: {destination} (total: {total_time}ms)")
        
        # Extract result from response
        # Response format: {"properties": {"result": "...", "stdout": "...", "stderr": "..."}}
        if result_data.get('properties'):
            props = result_data['properties']
            result_text = None
            
            if props.get('result'):
                result_text = props['result']
            elif props.get('stdout'):
                result_text = props['stdout']
            elif props.get('stderr'):
                return f"⚠️ ACA Sandbox Error:\n{props['stderr']}"
            
            if result_text:
                # Ensure proper UTF-8 handling for emoji and special characters
                if isinstance(result_text, bytes):
                    result_text = result_text.decode('utf-8', errors='replace')
                return f"☁️ [Azure Container Apps Sandbox]\n{result_text}"
        
        return f"☁️ [Azure Container Apps Sandbox]\n{str(result_data)}"
            
    except ImportError as e:
        return f"⚠️ Azure Identity not installed. Install with: pip install azure-identity\nError: {str(e)}"
    except requests.exceptions.HTTPError as e:
        return f"⚠️ ACA API Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"⚠️ Failed to execute in ACA sandbox: {str(e)}"
