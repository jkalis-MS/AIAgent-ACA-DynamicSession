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

# Configure Azure Monitor FIRST (before any agent framework imports)
# Following Pattern #3: Third party setup from Agent Framework documentation
# https://learn.microsoft.com/en-us/agent-framework/user-guide/observability?pivots=programming-language-python#3-third-party-setup
app_insights_conn_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
if app_insights_conn_string:
    conn_parts = dict(part.split('=', 1) for part in app_insights_conn_string.split(';') if '=' in part)
    endpoint = conn_parts.get('IngestionEndpoint', 'unknown')
    logger.info(f"🔗 Application Insights Connection String detected")
    logger.info(f"   Endpoint: {endpoint}")
    logger.info(f"   InstrumentationKey: {conn_parts.get('InstrumentationKey', 'unknown')[:8]}...")
    
    try:
        # CRITICAL: Disable ALL auto-instrumentations BEFORE importing Azure Monitor
        # Azure Monitor's configure_azure_monitor() enables many instrumentations by default
        # We ONLY want Agent Framework's manual spans (invoke_agent, chat, execute_tool)
        os.environ["OTEL_PYTHON_DISABLED_INSTRUMENTATIONS"] = (
            "httpx,httpcore,urllib,urllib3,requests,asgi,fastapi,flask,django,"
            "psycopg2,dbapi,system_metrics"
        )
        
        from azure.monitor.opentelemetry import configure_azure_monitor
        from agent_framework.observability import create_resource, enable_instrumentation
        
        # Configure Azure Monitor with minimal instrumentation
        resource = create_resource(
            service_name="cool-vibes-travel-agent",
            service_version="2.0.0"
        )
        
        # Disable all auto-instrumentations via instrumentation_options
        configure_azure_monitor(
            connection_string=app_insights_conn_string,
            resource=resource,
            enable_live_metrics=True,
            # Disable ALL instrumentations - we only want manual Agent Framework spans
            instrumentation_options={
                "azure_sdk": {"enabled": False},
                "django": {"enabled": False},
                "fastapi": {"enabled": False},
                "flask": {"enabled": False},
                "psycopg2": {"enabled": False},
                "requests": {"enabled": False},
                "urllib": {"enabled": False},
                "urllib3": {"enabled": False},
            }
        )
        
        # Then activate Agent Framework's telemetry code paths
        # Only captures: invoke_agent, chat, execute_tool spans (the important ones)
        enable_instrumentation(enable_sensitive_data=False)
        
        logger.info("✓ Azure Monitor configured with MINIMAL instrumentation")
        logger.info("   ALL auto-instrumentations disabled (HTTP, DB, frameworks)")
        logger.info("   ONLY Agent Framework manual spans enabled (invoke_agent, chat, execute_tool)")
        
    except ImportError as e:
        logger.warning(f"⚠ Failed to import observability modules: {e}")
    except Exception as e:
        logger.error(f"✗ Failed to configure Azure Monitor: {e}")
else:
    logger.info("⚠ APPLICATIONINSIGHTS_CONNECTION_STRING not found, skipping observability")

# NOW import agent_framework modules
import asyncio
from agent_framework.azure import AzureOpenAIResponsesClient
from agent_framework import ChatAgent
from agent_framework.devui import serve
from azure.identity import AzureCliCredential
from agent_framework.observability import get_tracer

# AMR/AF: Tools and Agent section
# Import tools
from tools.user_tools import create_remember_preference_for_user
from tools.travel_tools import (
    create_research_weather_tool,
    research_destination,
    find_flights,
    find_accommodation,
    booking_assistance
)
from tools.sports_tools import find_events, make_purchase

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
    
    # Load users from seed.json
    logger.info("Loading users from seed.json...")
    users = []
    try:
        with open('seed.json', 'r') as f:
            seed_data = json.load(f)
            users = list(seed_data.get('user_memories', {}).keys())
        logger.info(f"✓ Found {len(users)} users: {', '.join(users)}")
    except Exception as e:
        logger.error(f"Failed to load users: {e}")
        # Default to these users if seed.json fails
        users = ["Local", "ACA-DynamicSession"]
        logger.info(f"✓ Using default users: {', '.join(users)}")
    
    # Create one agent per user
    logger.info("Creating travel agents for each user...")
    agents = []
    
    for user_name in users:
        agent_name = f"{user_name}-cool-vibes-travel-agent"
        
        # Create user-specific remember_preference tool
        remember_pref_tool = create_remember_preference_for_user(user_name)
        
        # Create sandbox-specific research_weather tool
        research_weather_tool = create_research_weather_tool(user_name)
        
        # Create travel agent tools list specific to this user
        travel_tools = [
            remember_pref_tool,  # User-specific remember function
            research_weather_tool,  # Sandbox-specific weather research
            # research_destination,
            # find_flights,
            # find_accommodation,
            # booking_assistance,
            # find_events,
            # make_purchase
        ]
        
        try:
            agent = ChatAgent(
                name=agent_name,
                chat_client=responses_client,
                description=f"{TRAVEL_AGENT_DESCRIPTION} for {user_name} (using {user_name} sandbox)",
                instructions=TRAVEL_AGENT_INSTRUCTIONS,
                tools=travel_tools
            )
            agents.append(agent)
            
            sandbox_info = f"using {user_name} sandbox" if user_name != "Local" else "local execution"
            logger.info(f"✓ {agent_name} created ({sandbox_info})")
            
        except Exception as e:
            logger.error(f"Failed to create agent for {user_name}: {e}")
    
    logger.info(f"✓ Created {len(agents)} travel agents")
    
    # Start DevUI
    logger.info("Starting DevUI...")
    logger.info("=" * 60)
    logger.info("🚀 Travel Chat Agents are ready! V3.0 (No Redis)")
    logger.info("=" * 60)
    logger.info("Access the DevUI in your browser to start chatting")
    logger.info(f"Available agents: {', '.join([a.name for a in agents])}")
    logger.info("Select an agent from the dropdown to start a conversation")
    logger.info("=" * 60)
    
    # Start DevUI with all user agents
    # Use 0.0.0.0 in containers, localhost for local dev
    host = os.getenv('HOST', '0.0.0.0')
    serve(
        entities=agents,
        host=host,
        port=8000,
        auto_open=False
    )


if __name__ == "__main__":
    main()