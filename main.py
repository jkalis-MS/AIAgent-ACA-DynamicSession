"""Main application entry point for Travel Chat Agent."""
import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

import logging

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Reduce verbosity of noisy loggers
for logger_name in [
    'azure.core.pipeline.policies.http_logging_policy',
    'azure.monitor.opentelemetry',
    'opentelemetry',
    'uvicorn.access',
    'httpx',
    'httpcore',
]:
    logging.getLogger(logger_name).setLevel(logging.ERROR)

# Configure observability using Pattern #2: Custom Exporters
# Only Agent Framework spans (invoke_agent, chat, execute_tool) — no auto-instrumentation
# https://learn.microsoft.com/en-us/agent-framework/user-guide/observability?pivots=programming-language-python#2-custom-exporters
app_insights_conn_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
if app_insights_conn_string:
    try:
        from azure.monitor.opentelemetry.exporter import (
            AzureMonitorTraceExporter,
            AzureMonitorMetricExporter,
            AzureMonitorLogExporter,
        )
        from agent_framework.observability import configure_otel_providers

        configure_otel_providers(
            exporters=[
                AzureMonitorTraceExporter(connection_string=app_insights_conn_string),
                AzureMonitorMetricExporter(connection_string=app_insights_conn_string),
                AzureMonitorLogExporter(connection_string=app_insights_conn_string),
            ],
            enable_sensitive_data=False,
        )

        logger.info("✓ Agent Framework observability configured (Azure Monitor exporters)")

    except ImportError as e:
        logger.warning(f"⚠ Failed to import observability modules: {e}")
    except Exception as e:
        logger.error(f"✗ Failed to configure observability: {e}")
else:
    logger.info("⚠ APPLICATIONINSIGHTS_CONNECTION_STRING not found, skipping observability")

# NOW import agent_framework modules
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import Agent

# AMR/AF: Tools and Agent section
# Import tools
from tools.travel_tools import (
    create_research_weather_tool,
    create_chart_weather_tool,
)

# Import agent configurations
from agents.travel_agent import (
    TRAVEL_AGENT_NAME,
    TRAVEL_AGENT_DESCRIPTION,
    TRAVEL_AGENT_INSTRUCTIONS
)


def main():
    """Initialize and run the Travel Chat Agent."""
    
    # Get configuration (env vars already loaded at module level)
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
    
    if not all([azure_endpoint, azure_key, azure_deployment]):
        logger.error("Missing required environment variables. Please check your .env file.")
        logger.error("Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME")
        return
    
    # Initialize Azure OpenAI Responses client
    logger.info("Initializing Azure OpenAI Responses client...")
    try:
        # Set environment variables for Azure OpenAI
        os.environ["AZURE_OPENAI_ENDPOINT"] = azure_endpoint
        os.environ["AZURE_OPENAI_API_KEY"] = azure_key
        os.environ["AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME"] = azure_deployment
        
        # Use a supported API version for Responses/Assistants API
        azure_api_version = os.getenv('AZURE_OPENAI_API_VERSION', 'preview')
        os.environ["AZURE_OPENAI_API_VERSION"] = azure_api_version
        
        logger.info(f"Using Azure OpenAI API version: {azure_api_version}")
        logger.info(f"Using deployment: {azure_deployment}")
        
        responses_client = AzureOpenAIResponsesClient()
        logger.info("✓ Azure OpenAI Responses client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Azure OpenAI Responses client: {e}")
        return
    
    # Define agent configurations: (display_name, sandbox_key, description)
    # ACA Dynamic Session is first = default in DevUI
    agent_configs = [
        (
            "Tools run in ACA Dynamic Session",
            "ACA-DynamicSession",
            "Tools execute in a secure Azure Container Apps Dynamic Session sandbox — isolated from the main agent process.",
        ),
        (
            "Tools run along main Agent",
            "Local",
            "Tools execute locally in the same process as the agent — simple, no sandbox isolation.",
        ),
    ]
    logger.info(f"✓ Agents: {', '.join(name for name, _, _ in agent_configs)}")
    
    # Create one agent per configuration
    logger.info("Creating travel agents...")
    agents = []
    
    for display_name, sandbox_key, agent_description in agent_configs:
        
        # Create sandbox-specific research_weather tool
        research_weather_tool = create_research_weather_tool(sandbox_key)
        
        # Create sandbox-specific chart_weather tool
        chart_weather_tool = create_chart_weather_tool(
            sandbox_type=sandbox_key,
            azure_endpoint=azure_endpoint,
            azure_key=azure_key,
            azure_deployment=azure_deployment,
            azure_api_version=azure_api_version,
        )
        
        # Create travel agent tools list specific to this user
        travel_tools = [
            research_weather_tool,  # Sandbox-specific weather research
            chart_weather_tool,  # Sandbox-specific weather charting
        ]
        
        try:
            agent = Agent(
                responses_client,
                instructions=TRAVEL_AGENT_INSTRUCTIONS,
                name=display_name,
                description=agent_description,
                tools=travel_tools
            )
            agents.append(agent)
            
            tool_names = [getattr(t, '__name__', str(t)) for t in travel_tools]
            logger.info(f"✓ '{display_name}' created (sandbox={sandbox_key})")
            logger.info(f"  Tools: {tool_names}")
            
        except Exception as e:
            logger.error(f"Failed to create agent '{display_name}': {e}")
    
    logger.info(f"✓ Created {len(agents)} travel agents")
    
    # Start DevUI
    logger.info("Starting DevUI...")
    logger.info("=" * 60)
    logger.info("🚀 Travel Chat Agents are ready! V3.0")
    logger.info("=" * 60)
    logger.info("Access the DevUI in your browser to start chatting")
    logger.info(f"Available agents: {', '.join([a.name for a in agents])}")
    logger.info("Select an agent from the dropdown to start a conversation")
    logger.info("=" * 60)
    
    # Start DevUI with all user agents
    # Use 0.0.0.0 in containers, localhost for local dev
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '80'))

    # Use DevServer directly so we can serve chart images
    from agent_framework.devui import DevServer
    from tools.chart_server import CHART_DIR
    from starlette.staticfiles import StaticFiles
    from starlette.routing import Mount
    import uvicorn

    os.makedirs(CHART_DIR, exist_ok=True)

    dev_server = DevServer(port=port, host=host)
    dev_server._pending_entities = agents
    app = dev_server.get_app()

    # Insert a /charts static-file mount BEFORE the DevUI catch-all "/" mount.
    # Starlette iterates app.routes in order, so position 0 guarantees our
    # mount is checked first, preventing the "/" mount from shadowing it.
    app.routes.insert(0, Mount("/charts", app=StaticFiles(directory=CHART_DIR), name="charts"))

    logger.info(f"📂 Charts served at /charts from {CHART_DIR}")

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()