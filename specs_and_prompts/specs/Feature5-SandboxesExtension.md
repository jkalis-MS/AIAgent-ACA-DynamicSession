# Feature 5: Sandboxes Extension for Weather Research Tool

## Overview

This feature extends the travel agent system to support multiple sandbox execution environments for the `research_weather` tool. Different agents will execute weather research in different sandboxed environments (Local, E2B, Modal, Azure Container Apps) based on their configuration.

## Problem Statement

Currently, the `research_weather` tool executes directly in the local Python environment. To demonstrate secure code execution and isolation patterns, we want to:

1. Support multiple execution environments (sandboxes) for the same tool
2. Route tool execution to the appropriate sandbox based on the agent's configuration
3. Maintain a single tool interface while varying the implementation backend
4. Showcase different sandbox technologies: Local, E2B Code Interpreter, Modal, Azure Container Apps, and Daytona

## Architecture

### Agent Configuration

Five agents will be created, each associated with a different sandbox type:

```json
{
  "user_memories": {
    "Local": [ 
      { "description": "Researches the weather in the same instance where the agent runs." }, 
      { "insight": "Likes to explore any professional sports in the vicinity" } 
    ],
    "Sandbox-E2B": [ 
      { "description": "Researches the weather in the E2B Sandbox." }, 
      { "insight": "Prioritizes kids friendly activities" } 
    ],
    "Sandbox-Modal": [ 
      { "description": "Researches the weather in the Modal serverless environment." }, 
      { "insight": "Enjoys running in the morning" } 
    ],
    "Sandbox-ACA": [ 
      { "description": "ACA Dynamic Sessions" }, 
      { "insight": "Likes to explore any professional sports in the vicinity" } 
    ],
    "Sandbox-Daytona": [ 
      { "description": "Researches the weather in the Daytona Sandbox." }, 
      { "insight": "Prefers outdoor adventures and hiking trails" } 
    ]
  }
}
```

### Sandbox Types

1. **Local** - Direct execution in the current Python environment (no sandboxing)
2. **Sandbox-E2B** - Execution via E2B Code Interpreter SDK
3. **Sandbox-Modal** - Execution via Modal serverless platform
4. **Sandbox-ACA** - Execution via Azure Container Apps dynamic sessions or jobs
5. **Sandbox-Daytona** - Execution via Daytona secure sandbox environment


## Implementation Design

### 1. Tool Factory Pattern

Create a factory function that generates the appropriate `research_weather` tool implementation based on the sandbox type:

```python
def create_research_weather_tool(sandbox_type: str):
    """
    Factory function to create the research_weather tool 
    with the appropriate sandbox backend.
    
    Args:
        sandbox_type: One of "Local", "Sandbox-E2B", "Sandbox-Modal", "Sandbox-ACA", "Sandbox-Daytona"
    
    Returns:
        Callable tool function with the appropriate sandbox implementation
    """
    if sandbox_type == "Local":
        return research_weather_local
    elif sandbox_type == "Sandbox-E2B":
        return research_weather_e2b
    elif sandbox_type == "Sandbox-Modal":
        return research_weather_modal
    elif sandbox_type == "Sandbox-ACA":
        return research_weather_aca
    elif sandbox_type == "Sandbox-Daytona":
        return research_weather_daytona
    else:
        raise ValueError(f"Unknown sandbox type: {sandbox_type}")
```

### 2. Shared Weather Research Logic

Extract the core weather fetching logic into a reusable function that all sandbox implementations can use:

```python
def get_weather_data(destination: str, dates: str = "current") -> dict:
    """
    Core weather data fetching logic.
    Returns structured weather data that can be formatted by any sandbox.
    
    Returns:
        dict with keys: destination, current, daily, dates, error (if any)
    """
    # Existing logic from research_weather
    # Returns structured data instead of formatted string
```

### 3. Tool Implementations

#### Local Implementation (No Sandbox)

```python
def research_weather_local(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (Local execution)."""
    # Direct execution - current implementation
    # Returns formatted weather string
```

#### E2B Code Interpreter Implementation

```python
def research_weather_e2b(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (E2B sandbox)."""
    from e2b_code_interpreter import Sandbox
    
    # Create E2B sandbox
    with Sandbox() as sandbox:
        # Install requests if needed
        sandbox.run_code("pip install requests")
        
        # Execute weather fetching code in sandbox
        code = f"""
import requests

destination = "{destination}"
dates = "{dates}"

# Weather fetching logic here
# ... (core weather code)

result = format_weather_result(weather_data)
print(result)
"""
        execution = sandbox.run_code(code)
        
        if execution.error:
            return f"⚠️ E2B Sandbox Error: {execution.error}"
        
        return f"🔒 [E2B Sandbox]\n{execution.logs.stdout}"
```

#### Modal Implementation

```python
def research_weather_modal(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (Modal sandbox)."""
    import modal
    
    # Define Modal function
    stub = modal.Stub("weather-research")
    
    @stub.function(
        image=modal.Image.debian_slim().pip_install("requests")
    )
    def fetch_weather_modal(dest: str, travel_dates: str):
        # Weather fetching logic
        # ... (core weather code)
        return formatted_result
    
    # Execute in Modal sandbox
    with stub.run():
        result = fetch_weather_modal.remote(destination, dates)
        return f"🔒 [Modal Sandbox]\n{result}"
```

#### Azure Container Apps Implementation

```python
def research_weather_aca(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (ACA sandbox)."""
    # Option 1: Use Azure Container Apps Dynamic Sessions
    # Option 2: Trigger an Azure Container Apps Job
    
    # Placeholder implementation
    # Would use Azure SDK to trigger containerized execution
    
    return f"🔒 [Azure Container Apps Sandbox]\n{result}"
```

#### Daytona Implementation

```python
def research_weather_daytona(
    destination: Annotated[str, "The destination to research weather for"],
    dates: Annotated[str, "Travel dates (optional)"] = "current"
) -> str:
    """Get weather information for a destination (Daytona sandbox)."""
    from daytona import Daytona, DaytonaConfig
    
    # Initialize Daytona client
    config = DaytonaConfig(api_key=os.getenv('DAYTONA_API_KEY'))
    daytona = Daytona(config)
    
    # Create sandbox
    sandbox = daytona.create()
    
    try:
        # Execute weather fetching code in sandbox
        code = f"""
import requests

destination = "{destination}"
dates = "{dates}"

# Weather fetching logic here
# ... (core weather code)

print(result)
"""
        response = sandbox.process.code_run(code)
        
        if response.exit_code != 0:
            return f"⚠️ Daytona Sandbox Error: {response.result}"
        
        return f"🔒 [Daytona Sandbox]\n{response.result}"
    finally:
        sandbox.delete()
```

### 4. Main Application Integration

Modify `main.py` to create agent-specific tool instances:

```python
# Load users from seed.json
users = list(seed_data.get('user_memories', {}).keys())

for user_name in users:
    # Determine sandbox type from user name
    sandbox_type = user_name  # "Local", "Sandbox-E2B", etc.
    
    # Create sandbox-specific research_weather tool
    research_weather_tool = create_research_weather_tool(sandbox_type)
    
    # Create travel agent tools list with the appropriate weather tool
    travel_tools = [
        get_semantic_preferences,
        remember_pref_tool,
        research_weather_tool,  # Sandbox-specific implementation
        research_destination,
        find_flights,
        find_accommodation,
        booking_assistance,
        find_events,
        make_purchase
    ]
    
    # Create agent with sandbox-specific tools
    agent = responses_client.create_agent(
        name=f"{user_name}-cool-vibes-travel-agent",
        description=f"{TRAVEL_AGENT_DESCRIPTION} for {user_name} (using {sandbox_type})",
        instructions=TRAVEL_AGENT_INSTRUCTIONS,
        tools=travel_tools,
        chat_message_store_factory=chat_message_store_factory,
        context_providers=redis_provider
    )
```

## Environment Configuration

Add environment variables for sandbox credentials:

```env
# E2B Configuration
E2B_API_KEY=your_e2b_api_key_here

# Modal Configuration
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret

# Azure Container Apps Configuration
AZURE_CONTAINER_APPS_ENVIRONMENT_ID=your_aca_environment_id
AZURE_SUBSCRIPTION_ID=your_subscription_id

# Daytona Configuration
DAYTONA_API_KEY=your_daytona_api_key_here
```

## Dependencies

Update `requirements.txt`:

```txt
# Existing dependencies
agent-framework
agent-framework-redis
azure-monitor-opentelemetry-exporter
redisvl
azure-identity
redis
python-dotenv
requests

# Sandbox dependencies
e2b-code-interpreter  # For E2B sandbox
modal                 # For Modal sandbox
azure-mgmt-appcontainers  # For Azure Container Apps (if needed)
daytona              # For Daytona sandbox
```

## File Structure Changes

```
tools/
├── __init__.py
├── travel_tools.py             # Modified to support sandbox factory
├── weather_sandbox_local.py    # Local implementation
├── weather_sandbox_e2b.py      # E2B implementation
├── weather_sandbox_modal.py    # Modal implementation
├── weather_sandbox_aca.py      # Azure Container Apps implementation
├── weather_sandbox_daytona.py  # Daytona implementation
├── sports_tools.py
└── user_tools.py
```

## User Experience

When users interact with different agents:

1. **Local Agent** - Standard execution with no sandbox indicator
   ```
   🌍 Weather for New York
   📅 Current: ☀️ 72°F (22.2°C)
   ...
   ```

2. **Sandbox-E2B Agent** - Execution with E2B indicator
   ```
   🔒 [E2B Sandbox]
   🌍 Weather for New York
   📅 Current: ☀️ 72°F (22.2°C)
   ...
   ```

3. **Sandbox-Modal Agent** - Execution with Modal indicator
   ```
   🔒 [Modal Sandbox]
   🌍 Weather for New York
   📅 Current: ☀️ 72°F (22.2°C)
   ...
   ```

4. **Sandbox-ACA Agent** - Execution with ACA indicator
   ```
   🔒 [Azure Container Apps Sandbox]
   🌍 Weather for New York
   📅 Current: ☀️ 72°F (22.2°C)
   ...
   ```

5. **Sandbox-Daytona Agent** - Execution with Daytona indicator
   ```
   🔒 [Daytona Sandbox]
   🌍 Weather for New York
   📅 Current: ☀️ 72°F (22.2°C)
   ...
   ```

## Testing Strategy

1. **Local Testing** - Verify baseline functionality works
2. **E2B Testing** - Test with valid E2B API key, verify sandbox isolation
3. **Modal Testing** - Test with Modal credentials, verify serverless execution
4. **ACA Testing** - Test with Azure credentials, verify container execution
5. **Daytona Testing** - Test with Daytona API key, verify secure sandbox execution
6. **Agent Routing** - Verify each agent uses the correct sandbox implementation
7. **Error Handling** - Test behavior when sandbox credentials are missing or invalid
8. **Performance** - Compare execution times across sandbox types

## Security Considerations

1. **Credential Management** - All sandbox API keys stored in environment variables
2. **Code Isolation** - Each sandbox execution is isolated from the main application
3. **Network Security** - Sandboxes may have restricted network access
4. **Rate Limiting** - Implement rate limiting for sandbox API calls
5. **Cost Control** - Monitor sandbox usage to prevent unexpected costs

## Future Enhancements

1. **Dynamic Sandbox Selection** - Allow users to choose sandbox at runtime
2. **Sandbox Health Monitoring** - Track sandbox availability and performance
3. **Fallback Mechanism** - Automatically fallback to Local if sandbox unavailable
4. **Additional Sandboxes** - Support for Docker, Kubernetes, AWS Lambda, etc.
5. **Sandbox Metrics** - Collect and display execution metrics per sandbox type
6. **Cost Tracking** - Track and report sandbox usage costs

## Success Criteria

- ✅ Five agents created with different sandbox configurations
- ✅ Each agent correctly routes weather research to its designated sandbox
- ✅ Local execution works without external dependencies
- ✅ E2B sandbox execution works with valid credentials
- ✅ Modal sandbox execution works with valid credentials
- ✅ ACA sandbox execution works with valid credentials
- ✅ Daytona sandbox execution works with valid credentials
- ✅ Clear sandbox indicators in agent responses
- ✅ Proper error handling for sandbox failures
- ✅ Documentation for setup and configuration

## Implementation Order

1. **Phase 1: Core Refactoring**
   - Extract `get_weather_data()` shared logic
   - Create tool factory pattern
   - Update `main.py` for agent-specific tool creation

2. **Phase 2: Local + E2B**
   - Implement Local (existing code)
   - Implement E2B sandbox integration
   - Test with two agents

3. **Phase 3: Modal**
   - Implement Modal sandbox integration
   - Test with three agents

4. **Phase 4: Azure Container Apps**
   - Implement ACA sandbox integration
   - Test with four agents

5. **Phase 5: Daytona**
   - Implement Daytona sandbox integration
   - Test with all five agents

6. **Phase 6: Polish & Documentation**
   - Add error handling
   - Update README
   - Add environment variable documentation
