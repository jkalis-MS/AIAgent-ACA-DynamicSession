# Feature 6: Microsoft Foundry Integration for Travel Agent

## Overview

This feature adds Microsoft Foundry (Azure AI Foundry) Control Plane integration to the Travel Agent application. The integration enables centralized management, observability, and governance of the travel agent through the Foundry portal while maintaining the existing DevUI functionality for direct testing.

## Problem Statement

Currently, the travel agent is exposed only through the Agent Framework DevUI for direct testing and demonstration. To enable enterprise-grade deployment with:

1. **Centralized Management**: Register and manage the agent in Foundry Control Plane
2. **Observability**: Leverage existing Application Insights integration for comprehensive telemetry
3. **Governance**: Enable AI Gateway for security, rate limiting, and access control
4. **Monitoring**: Track agent performance, errors, and usage across the fleet
5. **Proxy Architecture**: Route client requests through Foundry's API Management gateway

The agent needs to be registered as a custom agent in Microsoft Foundry while maintaining backward compatibility with existing DevUI access.

## Important: What You DON'T Need to Build

✅ **No New Code Required**
- Your existing DevUI endpoint works as-is
- Current OTEL/Application Insights integration is sufficient
- Agent card endpoint is OPTIONAL (only for A2A protocol)

✅ **No Infrastructure to Deploy**
- Microsoft provisions and manages APIM automatically when you enable AI Gateway
- No need to deploy Azure API Management yourself
- No Bicep changes required for APIM

✅ **No Changes to Existing Telemetry**
- Your agent continues exporting OTEL traces to Application Insights exactly as before
- Foundry reads from the SAME Application Insights resource
- No code changes needed for observability

## Architecture

### High-Level Architecture

```
┌─────────────┐
│   Clients   │
│  (Foundry)  │
└──────┬──────┘
       │
       ↓
┌──────────────────────────────┐
│  Microsoft Foundry Portal    │
│  (Control Plane)             │
└──────────────┬───────────────┘
               │
               ↓
┌──────────────────────────────┐
│  Azure API Management        │
│  (AI Gateway - Proxy)        │
│  - Security                  │
│  - Rate Limiting             │
│  - Observability             │
└──────────────┬───────────────┘
               │
               ↓
┌──────────────────────────────┐
│  Travel Agent Container App  │
│  - Original DevUI Endpoint   │
│  - Foundry Compatible API    │
│  - OpenTelemetry Tracing     │
└──────────────────────────────┘
```

### Dual Access Pattern

**Direct Access (Existing)**:
- DevUI at `https://<container-app>:8000/`
- Used for development and testing

**Foundry Access (New)**:
- Proxy URL: `https://apim-<foundry-resource>.azure-api.net/<agent-name>/`
- Used for production, monitoring, and governance
- Same authentication as original endpoint

## Requirements

### 1. Agent Registration Prerequisites

**Foundry Configuration** (Portal-based, no deployment needed):
- Azure subscription with active Foundry project
- **AI Gateway**: Enable in Foundry portal - Microsoft provisions APIM automatically (no deployment by you)
- **Application Insights**: Connect your EXISTING Application Insights resource to Foundry project
- Public endpoint or VNet-accessible endpoint for the agent

**Agent Endpoint Requirements** (already met!):
- ✅ Exclusive endpoint accessible from Foundry network (Container App URL)
- ✅ HTTP protocol support (existing FastAPI/DevUI) - **NO NEW CODE**
- ⚠️ **Optional**: A2A (Agent-to-Agent) protocol support for future enhancement
- ✅ OpenTelemetry semantic conventions for GenAI (already implemented via agent-framework)
- ⚠️ **Optional**: Agent card JSON specification at `/.well-known/agent-card.json` - **NOT REQUIRED**

### 2. Endpoint Compatibility

The existing DevUI endpoint must remain compatible with Foundry registration:

**Current Endpoint Structure**:
```
https://<container-app>.azurecontainerapps.io/
├── /                          # Agent Framework DevUI
├── /chat                      # Chat completions (if applicable)
└── /.well-known/agent-card.json  # Agent card (NEW - OPTIONAL)
```

**Agent URL for Registration**:
- Base URL: `https://<container-app>.azurecontainerapps.io/`
- Protocol: HTTP (or A2A if enhanced)
- ⚠️ **Note**: Registering the DevUI base URL means the proxy forwards to your agent's API endpoints, not the DevUI interface
- **Result**: Foundry proxy URL works for API calls, but won't display DevUI in a browser

**Understanding the Registration**:
When you register `https://<container-app>.azurecontainerapps.io/`:
- ✅ API endpoints work through the proxy: `https://foundry-proxy/<agent>/api/...`
- ❌ DevUI doesn't work through the proxy (it's a web app, not an API)
- ✅ For DevUI, always use the original URL directly

### 3. OpenTelemetry Instrumentation

**Current Implementation** (already in place - NO CHANGES NEEDED):
```python
# main.py
from agent_framework.observability import setup_observability

setup_observability(
    enable_sensitive_data=True,
    applicationinsights_connection_string=app_insights_conn_string
)
```

**How It Works with Foundry**:
```
┌──────────────┐
│ Travel Agent │
│  Container   │──────OTEL Traces────▶┌────────────────────┐
└──────────────┘                      │ Application        │◀───Reads Traces───┐
                                      │ Insights           │                   │
                                      │ (SAME Resource)    │                   │
                                      └────────────────────┘                   │
                                                                               │
                                      ┌────────────────────┐                   │
                                      │ Foundry Portal     │───────────────────┘
                                      │ (Reads from AppIns)│
                                      └────────────────────┘
```

**Key Points**:
- ✅ **Your agent continues exporting traces exactly as before** - no code changes
- ✅ **Foundry reads from your existing Application Insights** - no new telemetry setup
- ✅ You just need to configure the SAME Application Insights resource in the Foundry project
- ✅ Traces already follow OpenTelemetry Generative AI semantic conventions (via agent-framework)
- ✅ Agent ID in traces: `gen_ai.agents.id="travel-agent"` (via agent-framework)

**What You Need to Do**:
1. Ensure your Application Insights resource is connected to the Foundry project
2. That's it! No code changes to the agent

### 4. Registration Configuration

**Properties to Register in Foundry**:

| Property | Value | Required | Notes |
|----------|-------|----------|-------|
| **Agent Details** |
| Agent URL | `https://<container-app>.azurecontainerapps.io/` | Yes | Base URL without specific routes |
| Protocol | HTTP | Yes | Current: HTTP, Future: A2A |
| A2A agent card URL | `/.well-known/agent-card.json` | No | Optional enhancement |
| OpenTelemetry Agent ID | `travel-agent` | No | Matches agent name in code |
| Admin portal URL | `https://<container-app>.azurecontainerapps.io/` | No | Points to DevUI for admin |
| **Foundry Configuration** |
| Project | `<foundry-project-name>` | Yes | Must have AI Gateway enabled |
| Agent name | `Cool Vibes Travel Agent` | Yes | Display name in Foundry |
| Description | `Comprehensive travel planning agent with destination research, booking assistance, sports events, and multi-sandbox weather research capabilities` | No | Descriptive text |

### 5. Agent Card Specification (Optional)

For A2A protocol support, create an agent card at `/.well-known/agent-card.json`:

```json
{
  "name": "Cool Vibes Travel Agent",
  "version": "1.0.0",
  "description": "Comprehensive travel planning agent with destination research, booking assistance, sports events, and multi-sandbox weather research capabilities",
  "capabilities": [
    "destination_research",
    "weather_research",
    "flight_search",
    "accommodation_search",
    "sports_events",
    "booking_assistance",
    "user_preferences"
  ],
  "sandbox_types": [
    "local",
    "e2b",
    "azure-container-apps",
    "daytona"
  ],
  "protocols": [
    "http"
  ],
  "endpoints": {
    "chat": "/",
    "health": "/"
  },
  "authentication": {
    "type": "none",
    "note": "DevUI handles session-based authentication"
  },
  "telemetry": {
    "provider": "azure-application-insights",
    "agent_id": "travel-agent"
  }
}
```

## Implementation Plan

### Phase 1: Foundry Registration Preparation

**Step 1.1: Verify Current Observability**
- [x] Confirm Application Insights connection string in environment
- [x] Verify OpenTelemetry traces are being exported
- [ ] Test trace visibility in Azure Portal Application Insights

**Step 1.2: Document Endpoint Information**
```bash
# Get current deployment information
azd env get-values | grep SERVICE_WEB_URI
azd env get-values | grep APPLICATIONINSIGHTS_CONNECTION_STRING
```

**Step 1.3: Add Agent Card Endpoint (Optional - SKIP FOR INITIAL REGISTRATION)**
⚠️ **This is OPTIONAL and can be added later for A2A protocol support**

If you want to add it later:
- Create `agent_card.py` with agent card JSON
- Add FastAPI route in `main.py`:
```python
@app.get("/.well-known/agent-card.json")
async def agent_card():
    return {
        "name": "Cool Vibes Travel Agent",
        "version": "1.0.0",
        # ... rest of agent card
    }
```

For initial registration, you can skip this - HTTP protocol works without it.

### Phase 2: Foundry Project Configuration

**Step 2.1: Configure AI Gateway** (Microsoft provisions APIM automatically)
1. Navigate to Foundry portal: https://ai.azure.com/
2. Select **Operate** → **Admin console**
3. Open **AI Gateway** tab
4. Verify AI Gateway is configured for the Foundry resource
5. If not configured, click **Add AI Gateway**
   - ⚠️ **Important**: Microsoft provisions and manages the APIM instance automatically
   - You don't deploy or manage APIM yourself
   - AI Gateway setup is free and unlocks governance features

**Step 2.2: Configure Application Insights** (Use your existing resource)
1. In Admin console, search for the target project
2. Select project → **Connected resources** tab
3. Verify Application Insights resource is connected
4. If not connected, click **Add connection** → **Application Insights**
5. **Select the SAME Application Insights resource that your travel agent uses**
   - Resource name: (check your `azd env get-values | grep APPLICATIONINSIGHTS_CONNECTION_STRING`)
   - This is the ONLY connection needed - your agent continues exporting traces as before
   - Foundry will read traces from this shared resource

**Step 2.3: Document Configuration**
- Foundry resource name: `<to-be-configured>`
- Foundry project name: `<to-be-configured>`
- AI Gateway endpoint: `https://apim-<foundry-resource>.azure-api.net/`
- Application Insights resource: `<existing-appi-resource>`

### Phase 3: Agent Registration

**Step 3.1: Register in Foundry Portal**
1. Navigate to Foundry portal
2. Select **Operate** → **Overview**
3. Click **Register agent**
4. Fill in registration details:

**Agent Details**:
```
Agent URL: https://<container-app>.azurecontainerapps.io/
Protocol: HTTP
A2A agent card URL: /.well-known/agent-card.json (optional)
OpenTelemetry Agent ID: travel-agent
Admin portal URL: https://<container-app>.azurecontainerapps.io/
```

**Foundry Configuration**:
```
Project: <foundry-project-name>
Agent name: Cool Vibes Travel Agent
Description: Comprehensive travel planning agent with destination research, 
booking assistance, sports events, and multi-sandbox weather research capabilities
```

5. Click **Save**

**Step 3.2: Capture New Agent URL**
1. Select the registered agent
2. On details panel, under **Agent URL**, copy the new proxy URL
3. New URL format: `https://apim-<foundry-resource>.azure-api.net/cool-vibes-travel-agent/`

**Step 3.3: Document New Endpoint**
- Add to README.md:
```markdown
## Access Endpoints

### Development/Testing (Direct Access)
- DevUI: https://<container-app>.azurecontainerapps.io/

### Production (Foundry Proxy)
- Foundry URL: https://apim-<foundry-resource>.azure-api.net/cool-vibes-travel-agent/
- Use same authentication as direct access
```

### Phase 4: Testing and Verification

**Step 4.1: Test Direct Access (Existing)**
```bash
# Verify DevUI still works
curl https://<container-app>.azurecontainerapps.io/
# Expected: DevUI interface
```

**Step 4.2: Test Foundry Proxy Access (API Calls Only)**

⚠️ **Important**: Don't browse to the proxy URL in a browser - it won't show DevUI!

The Foundry proxy is for API calls. Test it programmatically:

```python
# Option 1: If using Agent Framework client
from agent_framework.devui import get_client

client = get_client(
    url="https://aca-amr-foundry.azure-api.net/cool-vibes-travel-agent-hoykur9h"
)

# Make an API call
response = await client.chat("What's the weather in Los Angeles?")
print(response)
```

```python
# Option 2: Direct HTTP API call
import requests

response = requests.post(
    "https://aca-amr-foundry.azure-api.net/cool-vibes-travel-agent-hoykur9h/chat",
    json={
        "message": "What's the weather in Los Angeles?"
    },
    headers={
        # Use same authentication as your original endpoint
        "Content-Type": "application/json"
    }
)

print(response.json())
```

**Common Mistake**:
```bash
# ❌ This won't work - proxy doesn't serve web pages
https://aca-amr-foundry.azure-api.net/cool-vibes-travel-agent-hoykur9h

# ✅ This works - direct access to DevUI
https://<container-app>.azurecontainerapps.io/

# ✅ This works - API call through proxy
curl -X POST https://aca-amr-foundry.azure-api.net/cool-vibes-travel-agent-hoykur9h/api/endpoint
```

**Step 4.3: Verify Traces in Foundry**
1. Navigate to Foundry portal
2. Select **Operate** → **Assets**
3. Select the registered agent
4. Check **Traces** section
5. Verify traces appear for test requests
6. Check trace details show:
   - HTTP calls to agent endpoint
   - Tool invocations (if instrumented)
   - LLM calls (if instrumented)
   - Token usage

**Step 4.4: Test Blocking/Unblocking**
1. Select agent in Foundry
2. Click **Update status** → **Block**
3. Attempt to call agent through Foundry proxy
4. Expected: Request should be blocked
5. Click **Update status** → **Unblock**
6. Retry request
7. Expected: Request should succeed

### Phase 5: Monitoring and Operations

**Step 5.1: Configure Azure Infrastructure**

Add Foundry endpoints to `.env` and Bicep configuration:

```bicep
// infra/main.bicep
// Add to container app environment variables
{
  name: 'FOUNDRY_AGENT_URL'
  value: 'https://apim-<foundry-resource>.azure-api.net/cool-vibes-travel-agent/'
}
{
  name: 'FOUNDRY_PROJECT_NAME'
  value: '<foundry-project-name>'
}
```

**Step 5.2: Monitor Agent Performance**
1. In Foundry portal, view agent dashboard
2. Monitor metrics:
   - Request count
   - Error rate
   - Average latency
   - Token usage (if available)
3. Set up alerts for:
   - High error rate (>5%)
   - Elevated latency (>2s)
   - Rate limit breaches

**Step 5.3: Access Control**
- AI Gateway provides centralized access control
- Configure authentication/authorization at AI Gateway level
- Original agent endpoint authentication still applies

## Integration with Existing Features

### Compatibility with Feature 5 (Sandboxes)

The Foundry integration is **fully compatible** with existing sandbox implementations:
- All sandbox types (Local, E2B, ACA, Daytona) continue to work
- Weather research tool routing remains unchanged
- Sandbox selection based on agent configuration persists
- Telemetry captures sandbox execution details

### Compatibility with Feature 1-4 (Core Features)

- **Feature 1 (Agents & Tools)**: All tools remain functional through Foundry proxy
- **Feature 2 (Seeding Preferences)**: User preference storage/retrieval works through proxy
- **Feature 3 (Caching & Conversations)**: Redis caching maintains state across Foundry requests
- **Feature 4 (Dynamic Preferences)**: Semantic search and vector operations unchanged

## Testing Strategy

### Unit Tests
```python
# tests/test_foundry_integration.py

def test_agent_card_endpoint():
    """Verify agent card endpoint returns valid JSON"""
    response = client.get("/.well-known/agent-card.json")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cool Vibes Travel Agent"
    assert "capabilities" in data
    assert "destination_research" in data["capabilities"]

def test_telemetry_export():
    """Verify traces are exported to Application Insights"""
    # Make a request through the agent
    response = client.post("/chat", json={
        "message": "What's the weather in Seattle?"
    })
    
    # Wait for trace export
    time.sleep(2)
    
    # Query Application Insights
    traces = query_app_insights_traces(
        agent_id="travel-agent",
        operation="create_agent"
    )
    
    assert len(traces) > 0
    assert traces[0]["gen_ai.agents.id"] == "travel-agent"
```

### Integration Tests

**Test 1: Direct Access Still Works**
```bash
# Verify DevUI accessible without Foundry
curl https://<container-app>.azurecontainerapps.io/
# Expected: 200 OK, DevUI interface
```

**Test 2: Foundry Proxy Access**
```bash
# Verify agent accessible through Foundry proxy
curl https://apim-<foundry-resource>.azure-api.net/cool-vibes-travel-agent/
# Expected: 200 OK, routed to agent
```

**Test 3: Trace Visibility**
1. Make request through Foundry proxy
2. Check Foundry portal → Agent → Traces
3. Verify trace appears with correct agent ID

**Test 4: Blocking/Unblocking**
1. Block agent in Foundry
2. Attempt request through proxy
3. Expected: 403 Blocked
4. Unblock agent
5. Retry request
6. Expected: 200 OK

## Documentation Updates

### README.md Updates

Add new section:
⚠️ **Important**: Foundry proxy is for API calls only, not web browsing!

**Development/Testing (Web Interface)**:
- DevUI: `https://<container-app>.azurecontainerapps.io/`
- Use this URL to access the web interface in your browser

**Production (API Calls via Foundry)**:
- Foundry Proxy: `https://aca-amr-foundry.azure-api.net/cool-vibes-travel-agent-hoykur9h`
- Use this URL for programmatic API calls only
- Same authentication applies
- **Do NOT browse to this URL** - it's an API endpoint, not a web page

### Why Two URLs?

| URL Type | Purpose | Access Method | Works In Browser? |
|----------|---------|---------------|-------------------|
| Original Container App | DevUI Web Interface + API | Direct | ✅ Yes (DevUI) |
| Foundry Proxy | API Only (with governance) | Through APIM | ❌ No (API only) |

**Example Usage**:
```python
# For web interface - use original URL
# Browse to: https://<container-app>.azurecontainerapps.io/

# For API calls - use Foundry proxy
import requests
response = requests.post(
    "https://aca-amr-foundry.azure-api.net/cool-vibes-travel-agent-hoykur9h/api/chat",
    json={"message": "What's the weather?"}
)
```
### Access Methods

**Development/Testing**:
- Direct DevUI: `https://<container-app>.azurecontainerapps.io/`

**Production (via Foundry)**:
- Foundry Proxy: `https://apim-<foundry-resource>.azure-api.net/cool-vibes-travel-agent/`
- Same authentication applies

### Monitoring

View agent telemetry in:
- Foundry Portal: https://ai.azure.com/ → Operate → Assets → Cool Vibes Travel Agent
- Application Insights: Azure Portal → Application Insights resource

### Management Operations

**Block Agent**:
```bash
# Via Foundry Portal
Operate → Assets → Select Agent → Update status → Block
```

**View Traces**:
```bash
# Via Foundry Portal
Operate → Assets → Select Agent → Traces section
```

### Agent Card

View agent capabilities: `https://<container-app>.azurecontainerapps.io/.well-known/agent-card.json`
```

### Deployment Guide Updates

Add to `IMPLEMENTATION_PHASE4_ACA.md` or create `IMPLEMENTATION_PHASE6_FOUNDRY.md`:

```markdown
## Phase 6: Microsoft Foundry Registration

### Prerequisites
1. Foundry project with AI Gateway configured
2. Application Insights shared between agent and Foundry project
3. Agent deployed and accessible from Foundry network

### Registration Steps
[Include detailed registration steps from Phase 3]

### Post-Deployment Verification
[Include verification steps from Phase 4]
```

## Success Criteria

- [ ] Agent successfully registered in Microsoft Foundry
- [ ] Traces visible in Foundry portal with correct agent ID
- [ ] Agent accessible through both direct endpoint and Foundry proxy
- [ ] Block/unblock functionality works correctly
- [ ] Agent card endpoint returns valid JSON (if implemented)
- [ ] All existing features (tools, sandboxes, preferences) work through Foundry proxy
- [ ] Documentation updated with Foundry access methods
- [ ] Monitoring dashboard configured in Foundry portal

## Future Enhancements

### A2A Protocol Support
- Implement Agent-to-Agent (A2A) protocol for cross-agent communication
- Enable agent-to-agent orchestration scenarios
- Update protocol in registration from HTTP to A2A

### Enhanced Agent Card
- Add more detailed capability descriptions
- Include tool schemas in agent card
- Specify rate limits and quota information

### Multi-Region Deployment
- Register agents in multiple regions
- Configure geo-load balancing through AI Gateway
- Implement region-specific routing policies

### Advanced Governance
- Configure rate limiting per client
- Implement role-based access control (RBAC)
- Set up cost allocation and chargeback

## References

- [Microsoft Foundry - Register Custom Agents](https://learn.microsoft.com/en-us/azure/ai-foundry/control-plane/register-custom-agent?view=foundry)
- [OpenTelemetry Semantic Conventions for GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
- [Configure AI Gateway](https://learn.microsoft.com/en-us/azure/ai-foundry/configuration/enable-ai-api-management-gateway-portal?view=foundry)
- [Enable Tracing in Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/trace-application?view=foundry)

## Appendix

### Environment Variables

Add to `.env`:
```bash
# Microsoft Foundry Configuration
FOUNDRY_AGENT_URL=https://apim-<foundry-resource>.azure-api.net/cool-vibes-travel-agent/
FOUNDRY_PROJECT_NAME=<foundry-project-name>
FOUNDRY_RESOURCE_NAME=<foundry-resource-name>
```

### Bicep Configuration

Add to `infra/main.bicep`:
```bicep
// Foundry-specific environment variables
{
  name: 'FOUNDRY_AGENT_URL'
  value: foundryAgentUrl
}
{
  name: 'FOUNDRY_PROJECT_NAME'
  value: foundryProjectName
}
```

### OpenTelemetry Agent ID Configuration

Ensure consistent agent ID across:
1. Agent name in code: `"travel-agent"`
2. OpenTelemetry traces: `gen_ai.agents.id="travel-agent"`
3. Foundry registration: OpenTelemetry Agent ID = `travel-agent`

This ensures Foundry can correctly match traces to the registered agent.
