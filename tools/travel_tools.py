"""Travel-related tools for the travel agent."""
from typing import Callable

# Import sandbox-specific implementations
from .weather_sandbox_local import research_weather_local
from .weather_sandbox_aca import research_weather_aca
from .chart_sandbox_local import chart_weather_local
from .chart_sandbox_aca import _create_chart_weather_aca


def create_research_weather_tool(sandbox_type: str) -> Callable:
    """
    Factory function to create the research_weather tool 
    with the appropriate sandbox backend.
    
    Args:
        sandbox_type: One of "Local", "ACA-DynamicSession"
    
    Returns:
        Callable tool function with the appropriate sandbox implementation
    """
    if sandbox_type == "Local":
        return research_weather_local
    elif sandbox_type == "ACA-DynamicSession":
        return research_weather_aca
    else:
        # Default to local if unknown type
        return research_weather_local


def create_chart_weather_tool(
    sandbox_type: str,
    azure_endpoint: str = "",
    azure_key: str = "",
    azure_deployment: str = "",
    azure_api_version: str = "preview",
) -> Callable:
    """
    Factory function to create the chart_weather tool
    with the appropriate sandbox backend.

    For ACA mode, this creates a closure with an Azure OpenAI client
    that generates chart code dynamically via LLM.

    Args:
        sandbox_type: One of "Local", "ACA-DynamicSession"
        azure_endpoint: Azure OpenAI endpoint (required for ACA)
        azure_key: Azure OpenAI API key (required for ACA)
        azure_deployment: Azure OpenAI deployment name (required for ACA)
        azure_api_version: Azure OpenAI API version

    Returns:
        Callable tool function
    """
    if sandbox_type == "ACA-DynamicSession" and azure_endpoint and azure_key:
        try:
            tool = _create_chart_weather_aca(
                azure_endpoint=azure_endpoint,
                azure_key=azure_key,
                azure_deployment=azure_deployment,
                azure_api_version=azure_api_version,
            )
            print(f"📊 Chart tool created: ACA mode (function={tool.__name__})")
            return tool
        except Exception as e:
            print(f"❌ Failed to create ACA chart tool: {e} — falling back to local")
            return chart_weather_local
    else:
        print(f"📊 Chart tool created: Local mode (sandbox_type={sandbox_type}, endpoint={'set' if azure_endpoint else 'empty'}, key={'set' if azure_key else 'empty'})")
        return chart_weather_local
