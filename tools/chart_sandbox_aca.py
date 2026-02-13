"""Azure Container Apps dynamic sessions weather chart with LLM-generated code."""
import os
import json
import base64
import logging
import time
from typing import Annotated

logger = logging.getLogger(__name__)

# System prompt for code generation — tightly scoped for safety
_CODE_GEN_SYSTEM_PROMPT = """You are a Python data visualization expert.
You will receive weather JSON data for one or more cities. Write a COMPLETE, 
self-contained Python script that:

1. Parses the provided weather data (it will be available as a variable called `weather_data`)
2. Creates a beautiful, dark-themed matplotlib chart comparing the cities
3. The chart should have TWO subplots stacked vertically:
   - Top (larger): Temperature high/low lines per city with fill between, colored distinctly
   - Bottom (smaller): Precipitation bars per city, offset so they don't overlap
4. Use a dark background (#1a1a2e for figure, #16213e for axes), white text/labels
5. Include a legend, grid lines (alpha=0.2), date labels on x-axis rotated 45°
6. Title: "14-Day Weather Comparison"
7. Save the chart to `/mnt/data/chart.png` at 120 DPI with tight bounding box
8. Print "CHART_SAVED" when done

RULES:
- Return ONLY executable Python code, no markdown fences, no explanations
- Do NOT make any network/HTTP calls — all data is already provided
- Do NOT import os, subprocess, sys, or any dangerous modules
- The following are ALREADY imported for you: json, datetime (module), timedelta,
  matplotlib, matplotlib.pyplot (as plt), matplotlib.dates (as mdates), numpy (as np)
- Use datetime.datetime.strptime() for date parsing (datetime is the MODULE, not the class)
- The weather_data variable is already defined before your code runs
- Each city in weather_data has: destination, daily.time[], daily.temperature_2m_max[], 
  daily.temperature_2m_min[], daily.precipitation_sum[]
"""


def _create_chart_weather_aca(azure_endpoint: str, azure_key: str, 
                               azure_deployment: str, azure_api_version: str):
    """Factory: returns a chart_weather tool function with Azure OpenAI client in closure."""
    
    from openai import AzureOpenAI
    
    # Build a dedicated client inside the closure
    # The Agent Framework uses 'preview' as a shorthand, but the openai SDK
    # needs a real Azure API version string for chat completions
    if azure_api_version in ('preview', 'latest'):
        chart_api_version = '2024-12-01-preview'
    else:
        chart_api_version = azure_api_version
    
    openai_client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=azure_key,
        api_version=chart_api_version,
    )
    
    async def chart_weather_aca(
        destinations: Annotated[str, "Comma-separated list of destinations to chart (e.g. 'Miami, New York, Seattle')"],
        dates: Annotated[str, "Travel dates (optional)"] = "current"
    ) -> str:
        """Generate a multi-city weather comparison chart using AI-generated code in an ACA sandbox."""
        import sys, traceback as _tb
        print(f"\n{'='*60}\n🔵 chart_weather_aca ENTERED (destinations={destinations})\n{'='*60}", flush=True)
        
        try:
            from .aca_auth import get_pool_endpoint, get_aca_auth_header, execute_in_sandbox, download_file_from_sandbox
            from .weather_sandbox_local import get_weather_data
        except Exception as e:
            print(f"❌ IMPORT FAILED: {e}", flush=True)
            return f"⚠️ [ACA CHART IMPORT ERROR: {e}]\n(falling back to local)"
        
        pool_management_endpoint = get_pool_endpoint()
        if not pool_management_endpoint:
            print("❌ FALLBACK: ACA_POOL_MANAGEMENT_ENDPOINT not configured", flush=True)
            from .chart_sandbox_local import chart_weather_local
            local_result = chart_weather_local(destinations, dates)
            return f"⚠️ [FALLBACK: pool endpoint not set]\n{local_result}"
        
        city_list = [c.strip() for c in destinations.split(',') if c.strip()]
        if not city_list:
            return "⚠️ Please provide at least one destination."
        if len(city_list) > 4:
            city_list = city_list[:4]
        
        start_time = time.time()
        city_names = ', '.join(c.title() for c in city_list)
        logger.info(f"📊 ACA chart generation starting for: {city_names}")
        print(f"📊 ACA chart generation starting for: {city_names}")
        
        # Step 1: Fetch weather data locally (fast, no sandbox needed)
        all_data = []
        for city in city_list:
            data = get_weather_data(city, dates)
            if data.get('error'):
                return f"⚠️ {data['error']}"
            # Keep only what the chart code needs (strip non-serializable bits)
            all_data.append({
                "destination": data['destination'],
                "daily": data['daily']
            })
        
        data_time = int((time.time() - start_time) * 1000)
        logger.info(f"📊 Weather data fetched for {len(city_list)} cities ({data_time}ms)")
        print(f"📊 Weather data fetched for {len(city_list)} cities ({data_time}ms)")
        
        # Step 2: Ask Azure OpenAI to generate the charting code
        try:
            weather_json_str = json.dumps(all_data, indent=2)
            
            user_prompt = (
                f"Here is weather data for {len(all_data)} cities. "
                f"The data is already available as a Python variable `weather_data` "
                f"(a list of dicts). Generate the chart code.\n\n"
                f"Data preview:\n```json\n{weather_json_str[:2000]}\n```"
            )
            
            llm_start = time.time()
            response = openai_client.chat.completions.create(
                model=azure_deployment,
                messages=[
                    {"role": "system", "content": _CODE_GEN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,  # Low temperature for deterministic code
                max_tokens=3000,
            )
            
            generated_code = response.choices[0].message.content.strip()
            
            # Strip markdown fences if the LLM included them anyway
            if generated_code.startswith("```"):
                lines = generated_code.split('\n')
                # Remove first line (```python) and last line (```)
                lines = [l for l in lines if not l.strip().startswith('```')]
                generated_code = '\n'.join(lines)
            
            llm_time = int((time.time() - llm_start) * 1000)
            logger.info(f"🤖 LLM generated chart code ({llm_time}ms, {len(generated_code)} chars)")
            print(f"🤖 LLM generated chart code ({llm_time}ms, {len(generated_code)} chars)")
            
        except Exception as e:
            logger.error(f"⚠️ LLM code generation failed: {e}")
            print(f"❌ FALLBACK: LLM code generation failed: {e}", flush=True)
            from .chart_sandbox_local import chart_weather_local
            local_result = chart_weather_local(destinations, dates)
            return f"⚠️ [FALLBACK: LLM failed: {e}]\n{local_result}"
        
        # Step 3: Basic safety check on generated code
        forbidden = ['subprocess', 'os.system', 'os.popen', 'eval(', 'exec(', 
                      '__import__', 'shutil', 'socket', 'urllib', 'requests', 'http']
        for term in forbidden:
            if term in generated_code:
                print(f"❌ FALLBACK: Generated code contains forbidden term '{term}'", flush=True)
                from .chart_sandbox_local import chart_weather_local
                local_result = chart_weather_local(destinations, dates)
                return f"⚠️ [FALLBACK: forbidden term '{term}']\n{local_result}"
        
        # Step 4: Wrap the generated code with the data injection preamble
        # Pre-import everything the LLM might use so it can't fail on missing imports
        # Import datetime MODULE so both datetime.datetime.strptime() and datetime.strptime() work
        # (LLMs inconsistently use the module vs class form)
        sandbox_code = f"""
import json
import datetime
from datetime import timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Inject weather data (fetched by the host, not by the sandbox)
weather_data = json.loads('''{json.dumps(all_data)}''')

# === LLM-generated chart code below ===
{generated_code}
"""
        
        # Step 5: Execute in ACA sandbox
        try:
            auth_header, auth_time = get_aca_auth_header()
            session_id = f"chart-{'-'.join(c.lower().replace(' ', '') for c in city_list)}-{int(time.time())}"
            
            exec_start = time.time()
            logger.info(f"▶️ ACA Sandbox executing chart code...")
            print(f"▶️ ACA Sandbox executing chart code...")
            
            ## MAGIC: The execute_in_sandbox function will run the code and return stdout, stderr, and result.
            exec_result = execute_in_sandbox(
                code=sandbox_code,
                session_id=session_id,
                pool_management_endpoint=pool_management_endpoint,
                auth_header=auth_header,
                timeout=60,
            )
            
            exec_time = int((time.time() - exec_start) * 1000)
            logger.info(f"✅ ACA Sandbox chart execution finished ({exec_time}ms)")
            print(f"✅ ACA Sandbox chart execution finished ({exec_time}ms)")
            
            stdout = exec_result.get('stdout', '')
            stderr = exec_result.get('stderr', '')
            
            if stderr and 'CHART_SAVED' not in stdout:
                print(f"❌ FALLBACK: Sandbox stderr: {stderr[:500]}", flush=True)
                from .chart_sandbox_local import chart_weather_local
                local_result = chart_weather_local(destinations, dates)
                return f"⚠️ [FALLBACK: sandbox stderr]\n{local_result}"
            
        except Exception as e:
            print(f"❌ FALLBACK: ACA sandbox execution failed: {e}", flush=True)
            from .chart_sandbox_local import chart_weather_local
            local_result = chart_weather_local(destinations, dates)
            return f"⚠️ [FALLBACK: sandbox exec failed: {e}]\n{local_result}"
        
        # Step 6: Download the chart image from sandbox
        try:
            download_start = time.time()
            img_bytes = download_file_from_sandbox(
                filename="chart.png",
                session_id=session_id,
                pool_management_endpoint=pool_management_endpoint,
                auth_header=auth_header,
            )
            download_time = int((time.time() - download_start) * 1000)
            logger.info(f"📥 Chart image downloaded ({download_time}ms, {len(img_bytes)} bytes)")
            print(f"📥 Chart image downloaded ({download_time}ms, {len(img_bytes)} bytes)")
            
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
        except Exception as e:
            print(f"❌ FALLBACK: Failed to download chart: {e}", flush=True)
            # Try extracting base64 from stdout as fallback
            if 'data:image/png;base64,' in stdout:
                img_base64 = stdout.split('data:image/png;base64,')[1].split('"')[0].split("'")[0].strip()
            else:
                print("❌ FALLBACK: No base64 in stdout either", flush=True)
                from .chart_sandbox_local import chart_weather_local
                local_result = chart_weather_local(destinations, dates)
                return f"⚠️ [FALLBACK: download failed: {e}]\n{local_result}"
        
        # Step 7: Save chart locally and build response
        try:
            from .chart_server import CHART_DIR, ensure_chart_server, get_chart_url
            os.makedirs(CHART_DIR, exist_ok=True)
            filename = f"weather_{'_'.join(c.lower().replace(' ', '') for c in city_list)}_{int(time.time())}.png"
            chart_path = os.path.join(CHART_DIR, filename)
            with open(chart_path, 'wb') as f:
                f.write(base64.b64decode(img_base64))
            logger.info(f"💾 Chart saved to {chart_path}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save chart locally: {e}")
            chart_path = "(could not save locally)"
        
        total_time = int((time.time() - start_time) * 1000)
        
        # Get URL for the saved chart
        ensure_chart_server()
        chart_url = get_chart_url(filename)
        
        result = f"📊 Weather Comparison: {city_names}\n"
        result += f"🤖 Chart code generated by AI, executed in ACA sandbox\n\n"
        result += f"📈 Chart: {chart_url}\n\n"
        
        # Add text summary
        result += "Summary (14-day forecast):\n"
        for data in all_data:
            city = data['destination']
            daily = data['daily']
            avg_high = sum(daily['temperature_2m_max']) / len(daily['temperature_2m_max'])
            avg_low = sum(daily['temperature_2m_min']) / len(daily['temperature_2m_min'])
            total_precip = sum(daily['precipitation_sum'])
            rainy_days = sum(1 for p in daily['precipitation_sum'] if p > 0.1)
            result += f"  • {city.title()}: Avg High {avg_high:.0f}°F / Low {avg_low:.0f}°F | Precip: {total_precip:.1f}in ({rainy_days} rainy days)\n"
        
        result += f"\n⏱️ Debug Timing (ACA Sandbox):\n"
        result += f"  [1] Weather data fetched: {data_time}ms\n"
        result += f"  [2] LLM code generation: {llm_time}ms\n"
        result += f"  [3] Sandbox execution: {exec_time}ms\n"
        result += f"  [4] Total execution time: {total_time}ms\n"

        logger.info(f"✅ ACA chart complete for {city_names} ({total_time}ms)")
        print(f"✅ ACA chart complete for {city_names} ({total_time}ms)")
        
        return f"☁️ [Azure Container Apps Sandbox]\n{result}"
    
    chart_weather_aca.__name__ = "chart_weather"
    return chart_weather_aca
