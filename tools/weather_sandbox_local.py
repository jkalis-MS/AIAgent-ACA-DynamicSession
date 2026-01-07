"""Local (non-sandboxed) weather research implementation."""
import logging
import time
from typing import Annotated
from .weather_core import get_weather_data, format_weather_result

logger = logging.getLogger(__name__)


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
    result += "\n\n⏱️ Debug Timing (Local Execution):"
    result += f"\n  [1] Code started: 0ms"
    result += f"\n  [2] GPS lookup completed: N/A (handled in get_weather_data)"
    result += f"\n  [3] Weather data obtained: {checkpoint_3}ms"
    result += f"\n  [4] Response formatted: {checkpoint_4}ms"
    result += f"\n  Total local execution: {checkpoint_4}ms"
    
    execution_time = int((time.time() - start_time) * 1000)
    result += f"\n  [5] Total end-to-end time: {execution_time}ms"
    
    logger.info(f"✅ Local execution finished for destination: {destination} ({execution_time}ms)")
    print(f"✅ Local execution finished for destination: {destination} ({execution_time}ms)")
    
    return f"🏠 [Local Execution]\n{result}"
