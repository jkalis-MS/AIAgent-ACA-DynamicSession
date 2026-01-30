# Travel Chat Agent with Azure Container Apps Dynamic Sessions

A Travel Chat Agent built with Microsoft Agent Framework and Azure OpenAI that handles destination research, real-time weather analysis, flight searches, hotel accommodations, and sports event bookings. The agent dynamically executes Python code in secure, isolated Azure Container Apps Session Pools for live calculations and API integrations.

## How Tools Execute Python in Session Pools

```python
# When the agent needs to check weather, it calls this tool:
async def get_weather_for_location(location: str, dates: list[str]) -> str:
    # Code that will run in the session pool
    code = f"""
import requests
from datetime import datetime

location = "{location}"
dates = {dates}

# Fetch weather data from API
response = requests.get(f"https://api.weather.com/forecast/{{location}}")
data = response.json()

# Process and format results
results = []
for date in dates:
    temp = data['forecast'][date]['temperature']
    conditions = data['forecast'][date]['conditions']
    results.append(f"{{date}}: {{temp}}°F, {{conditions}}")

print("\\n".join(results))
"""
    
    # Execute in isolated session pool
    result = await session_pool_client.execute_code(code)
    return result.stdout
```

## Setup Session Pool (Required for Local and Cloud)

Before running the application, create an Azure Container Apps Session Pool using `az containerapp up`:

```powershell
# Login to Azure
az login

# Set variables
$RESOURCE_GROUP = "rg-travel-agent"
$LOCATION = "eastus"

# Create session pool with az containerapp up
az containerapp up `
  --name travel-agent-sessionpool `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --environment travel-agent-env `
  --image mcr.microsoft.com/k8se/services/code-interpreter:latest `
  --session-pool `
  --max-sessions 10 `
  --cooldown-period 300

# Get the session pool management endpoint
az containerapp sessionpool show `
  --name travel-agent-sessionpool `
  --resource-group $RESOURCE_GROUP `
  --query "properties.poolManagementEndpoint" -o tsv
```

Save the endpoint URL for your `.env` configuration.## Run Locally

1. **Install Dependencies**
```powershell
pip install -r requirements.txt
```

2. **Configure Environment**

Create a `.env` file with your credentials:

```
# Session Pool Configuration (Required)
AZURE_CONTAINER_APP_SESSION_POOL_MANAGEMENT_ENDPOINT=https://your-session-pool-endpoint.region.azurecontainerapps.io

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-instance.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Application Insights (Optional - for monitoring and telemetry)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=your-key-here;IngestionEndpoint=https://region.in.applicationinsights.azure.com/;LiveEndpoint=https://region.livediagnostics.monitor.azure.com/
```

3. **Run the Application**
```powershell
python main.py
```

4. **Access DevUI**

Open your browser to `http://localhost:8000` to interact with the agent.

## Project Structure

```
travel-agent/
├── agents/
│   └── travel_agent.py              # Travel agent definition and instructions
├── tools/
│   ├── weather_sandbox_aca.py       # Weather tool using session pool
│   ├── weather_sandbox_local.py     # Local weather tool
│   ├── user_tools.py                # User preference tools
│   ├── travel_tools.py              # Travel research tools
│   └── sports_tools.py              # Sports event tools
├── data/
│   ├── sample_sport_events.py       # Sports event sample data
│   └── sample_sport_venues.py       # Venue seating sample data
├── infra/
│   └── main.bicep                   # Infrastructure as code
├── seed.json                        # User preferences seed data
├── main.py                          # Application entry point
└── requirements.txt                 # Python dependencies
```

## Agent Architecture

### Travel Agent
- Destination research and recommendations
- Real-time weather analysis (via session pool)
- Flight and accommodation search
- Sports event booking
- Preference learning and retrieval

### Tools

**Session Pool Tools:**
- `get_weather_for_location` - Dynamic weather analysis in isolated Python environment

**User Preference Tools:**
- `remember_preference` - Store user preferences with vector embeddings
- `get_semantic_preferences` - Semantic search for preferences

**Travel Tools:**
- `research_destination` - Destination information
- `find_flights` - Flight options
- `find_accommodation` - Hotel recommendations
- `booking_assistance` - General booking support

**Sports Tools:**
- `find_events` - Search professional sports events
- `make_purchase` - Book tickets

## How It Works

## How It Works

**Session Pool Execution:**
- Agent receives user request requiring live data/calculation
- Tool generates Python code dynamically
- Code executes in isolated session pool container
- Results returned to agent for response

**Conversation Memory:**
- All conversations stored in Azure Managed Redis
- User preferences stored with vector embeddings
- Semantic search retrieves relevant context automatically

**Example Interaction:**
```
User: "What's the weather in Seattle next week?"
→ Agent calls get_weather_for_location tool
→ Tool generates Python code to fetch and analyze weather data
→ Code executes in session pool with internet access
→ Results returned: "Feb 15: 52°F, Partly Cloudy..."
→ Agent responds with formatted weather information
```

## Troubleshooting

**Session Pool Connection Error:**
- Verify `AZURE_CONTAINER_APP_SESSION_POOL_MANAGEMENT_ENDPOINT` is set correctly
- Check that session pool is in "Succeeded" provisioning state
- Ensure your Azure credentials have access to the session pool
- Verify network configuration allows access from your environment

**Redis Connection Error:**
- Verify your REDIS_URL is correct
- Check firewall rules allow your IP
- Ensure SSL is enabled in connection string

**Azure OpenAI Error:**
- Verify endpoint and API key are correct
- Check your deployment name matches
- Ensure you have quota available
- In case Agent Framework shows API invalid, please make sure your env file states AZURE_OPENAI_API_VERSION=preview

**Vector Search Not Working:**
- Ensure RediSearch module is enabled in your Redis instance
- Check embedding deployment is configured correctly
- Verify `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` environment variable
- Azure Managed Redis Enterprise tier required for RediSearch

**Application Insights Not Capturing Telemetry:**
- Verify `APPLICATIONINSIGHTS_CONNECTION_STRING` is set correctly in `.env`
- Check Application Insights resource is created in Azure Portal
- The application captures Agent Framework spans: `invoke_agent`, `chat`, `execute_tool`
- View telemetry in Azure Portal → Application Insights → Transaction search
- Live metrics available for real-time monitoring

**Import Errors:**
- Run `pip install --upgrade -r requirements.txt`
- Ensure Python 3.10+ is being used
- Check virtual environment is activated

## License

MIT License - Sample/Demo Application
