"""Azure Container Apps dynamic sessions weather research implementation."""
import os
import json
import logging
import time
import requests
from typing import Annotated
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Module-level credential and token cache
_aca_credential = None
_aca_token = None
_aca_token_expiry = None


def research_weather_aca(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (ACA sandbox)."""
    
    # Check for required environment variables
    pool_management_endpoint = os.getenv('ACA_POOL_MANAGEMENT_ENDPOINT')
    
    if not pool_management_endpoint:
        logger.warning("⚠️ ACA_POOL_MANAGEMENT_ENDPOINT not configured")
        return """⚠️ Azure Container Apps session pool not configured.

To use ACA sandboxes:
1. Create an ACA session pool in Azure Portal
2. Set ACA_POOL_MANAGEMENT_ENDPOINT environment variable
3. Ensure the container app's managed identity has 'Azure ContainerApps Session Executor' role

Using local weather data instead..."""
    
    try:
        # Import Azure identity for authentication
        from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
        
        start_time = time.time()
        logger.info(f"☁️ ACA Sandbox creating for destination: {destination}")
        print(f"☁️ ACA Sandbox creating for destination: {destination}")
        
        # Use module-level cached credential and token
        global _aca_credential, _aca_token, _aca_token_expiry
        
        # Check if we need to get a new token
        needs_new_token = (
            _aca_token is None or 
            _aca_token_expiry is None or 
            datetime.now() >= _aca_token_expiry
        )
        
        if needs_new_token:
            # Create credential if not exists
            if _aca_credential is None:
                # Check if running in Azure Container Apps
                managed_identity_client_id = os.getenv('AZURE_CLIENT_ID')
                container_app_name = os.getenv('CONTAINER_APP_NAME')
                
                if managed_identity_client_id:
                    # Use ManagedIdentityCredential with explicit client_id
                    logger.info(f"🔐 Using ManagedIdentityCredential with client_id (Container App: {container_app_name})")
                    _aca_credential = ManagedIdentityCredential(client_id=managed_identity_client_id)
                elif container_app_name or os.getenv('WEBSITE_INSTANCE_ID'):
                    # In Azure but no client_id provided, try system-assigned identity
                    logger.info(f"🔐 Using ManagedIdentityCredential with system-assigned identity (Container App: {container_app_name})")
                    _aca_credential = ManagedIdentityCredential()
                else:
                    # Running locally
                    logger.info("🔐 Using DefaultAzureCredential (running locally)")
                    _aca_credential = DefaultAzureCredential()
            
            # Get fresh access token
            token_response = _aca_credential.get_token("https://dynamicsessions.io/.default")
            _aca_token = token_response.token
            
            # Set expiry time (token valid for 1 hour, refresh 5 minutes early for safety)
            _aca_token_expiry = datetime.now() + timedelta(seconds=token_response.expires_on - time.time() - 300)
            
            auth_time = int((time.time() - start_time) * 1000)
            logger.info(f"🔑 New token obtained for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")
            print(f"🔑 New token obtained for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")
        else:
            auth_time = int((time.time() - start_time) * 1000)
            logger.info(f"♻️ Using cached token for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")
            print(f"♻️ Using cached token for ACA ({auth_time}ms, expires at {_aca_token_expiry.strftime('%H:%M:%S')})")
        
        auth_header = f"Bearer {_aca_token}"
        
        # Generate a session identifier (use timestamp for unique sessions to avoid caching issues)
        # Note: Each execution creates a new session - no session reuse
        session_id = f"weather-{destination.lower().replace(' ', '-')}-{int(time.time())}"
        
        auth_time = int((time.time() - start_time) * 1000)
        logger.info(f"🔑 Identity for ACA ready ({auth_time}ms)")
        print(f"🔑 Identity for ACA ready ({auth_time}ms)")
    
        
        # Prepare Python code to execute in the session
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
        
        # Execute code in ACA session via REST API
        # POST https://<endpoint>/code/execute?api-version=2024-02-02-preview&identifier=<session_id>
        ready_time = int((time.time() - start_time) * 1000)
        logger.info(f"▶️ ACA Sandbox code execution starting for destination: {destination} ({ready_time}ms)")
        print(f"▶️ ACA Sandbox code execution starting for destination: {destination} ({ready_time}ms)")
       
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
                
                # Append total execution time (includes network + ACA overhead)
                result_text += f"\n  [5] Total end-to-end time: {execution_time}ms"
                
                # Check if sandbox encountered network restrictions or errors
                network_error_indicators = [
                    "ProxyError", 
                    "Unable to connect to proxy", 
                    "Tunnel connection failed",
                    "Failed to resolve",
                    "NameResolutionError",
                    "Max retries exceeded",
                    "Error fetching weather data"
                ]
                
                if any(indicator in result_text for indicator in network_error_indicators):
                    logger.warning("⚠️ ACA sandbox network restriction detected - falling back to local execution")
                    from .weather_sandbox_local import research_weather_local
                    local_result = research_weather_local(destination, dates)
                    return f"⚠️ ACA sandbox has network restrictions - executed locally instead\n\n{local_result}"
                
                return f"☁️ [Azure Container Apps Sandbox]\n{result_text}"
        
        return f"☁️ [Azure Container Apps Sandbox]\n{str(result_data)}"
            
    except ImportError as e:
        logger.warning("⚠️ Azure Identity not available - falling back to local execution")
        from .weather_sandbox_local import research_weather_local
        return research_weather_local(destination, dates)
    except requests.exceptions.HTTPError as e:
        error_msg = f"⚠️ ACA API Error: {e.response.status_code} - {e.response.text}"
        logger.error(error_msg)
        logger.warning("Falling back to local execution...")
        from .weather_sandbox_local import research_weather_local
        return research_weather_local(destination, dates)
    except Exception as e:
        logger.error(f"⚠️ Failed to execute in ACA sandbox: {str(e)}")
        logger.warning("Falling back to local execution...")
        from .weather_sandbox_local import research_weather_local
        return research_weather_local(destination, dates)
