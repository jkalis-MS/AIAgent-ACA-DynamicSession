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
    logger.info(f"🏠 Local execution starting for destination: {destination}")
    print(f"🏠 Local execution starting for destination: {destination}")
    
    execution_time = int((time.time() - start_time) * 1000)
    logger.info(f"▶️ Local code execution starting for destination: {destination} ({execution_time}ms)")
    print(f"▶️ Local code execution starting for destination: {destination} ({execution_time}ms)")
    
    weather_data = get_weather_data(destination, dates)
    result = format_weather_result(weather_data)
    
    execution_time = int((time.time() - start_time) * 1000)
    logger.info(f"✅ Local execution finished for destination: {destination} ({execution_time}ms)")
    print(f"✅ Local execution finished for destination: {destination} ({execution_time}ms)")
    
    return result
