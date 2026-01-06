# Phase 4 Implementation: Azure Container Apps Sandbox

## Overview

This document describes the implementation of Phase 4 of the Sandboxes Extension feature - Azure Container Apps (ACA) dynamic sessions integration for the weather research tool.

## Implementation Date

January 2, 2026

## What Was Implemented

### 1. ACA Sandbox Implementation (`tools/weather_sandbox_aca.py`)

Created a new sandbox implementation using **direct REST API calls** to Azure Container Apps dynamic sessions.

**Key Features:**
- Uses `DefaultAzureCredential` from `azure-identity` for authentication
- Makes direct HTTP POST requests to ACA sessions API endpoint
- Executes Python code in isolated Hyper-V containers
- Includes comprehensive logging with millisecond timing
- Returns results with "☁️ [Azure Container Apps Sandbox]" prefix
- **No AI/ML frameworks required** - just REST API calls

**Authentication Flow:**
1. Uses `DefaultAzureCredential` (supports Azure CLI, Managed Identity, etc.)
2. Obtains tokens with audience `https://dynamicsessions.io/.default`
3. Requires `Azure ContainerApps Session Executor` role on session pool
4. Requires `Contributor` role on session pool for management operations

**API Endpoint:**
```
POST {pool_management_endpoint}/code/execute?api-version=2024-02-02-preview&identifier={session_id}
```

**Request Body:**
```json
{
    "properties": {
        "codeInputType": "inline",
        "executionType": "synchronous",
        "code": "print('Hello, world!')"
    }
}
```

**Code Execution:**
- Code runs in Azure Container Apps dynamic session pool
- Sessions provide isolated Python execution environments
- Pre-installed packages include NumPy, pandas, scikit-learn, requests
- Sessions are automatically created and reused based on session identifier

### 2. Factory Pattern Update (`tools/travel_tools.py`)

Updated the `create_research_weather_tool()` factory to route "Sandbox-ACA" requests to the new ACA implementation:

```python
elif sandbox_type == "Sandbox-ACA":
    return research_weather_aca
```

### 3. Dependencies (`requirements.txt`)

Added Azure Identity dependency:
```
azure-identity  # For Azure Container Apps authentication
```

**Note:** We use direct REST API calls instead of Semantic Kernel, keeping dependencies minimal. The implementation only requires:
- `azure-identity` - For getting Azure authentication tokens
- `requests` - For making HTTP calls (already in requirements)

### 4. Configuration (`.env.example`)

Added ACA configuration template:
```env
# Azure Container Apps Configuration (for ACA sandbox)
ACA_POOL_MANAGEMENT_ENDPOINT=https://your-region.dynamicsessions.io/subscriptions/your-subscription-id/resourceGroups/your-resource-group/sessionPools/your-pool-name
```

### 5. Test Script (`test_sandboxes.py`)

Extended test script to include ACA sandbox testing:
- Checks for `ACA_POOL_MANAGEMENT_ENDPOINT` environment variable
- Tests ACA execution alongside Local and E2B sandboxes
- Shows timing and output comparison

## Architecture

### Session Pool Management

The ACA implementation uses Azure Container Apps session pools:

1. **Session Pool**: Azure resource that manages a pool of code interpreter sessions
2. **Session Identifier**: Each user/conversation gets a unique session (default: random UUID)
3. **Session Reuse**: Same identifier reuses existing session for subsequent calls
4. **Automatic Cleanup**: Sessions auto-terminate after idle timeout (configurable)

### Code Execution Flow

```
1. Check for ACA_POOL_MANAGEMENT_ENDPOINT
2. Create DefaultAzureCredential
3. Get access token with audience "https://dynamicsessions.io/.default"
4. Generate session identifier (e.g., "weather-new-york")
5. Log: Sandbox session ready
6. Log: Code execution starting
7. Build REST API request payload
8. POST to {endpoint}/code/execute?api-version=2024-02-02-preview&identifier={session_id}
9. Wait for synchronous execution response
10. Log: Execution finished (Xms)
11. Parse response JSON for result
12. Log: Session complete (total: Xms)
13. Return formatted result
```

**REST API Details:**
- **Endpoint**: `{pool_management_endpoint}/code/execute`
- **Method**: POST
- **Query params**: `api-version=2024-02-02-preview&identifier={session_id}`
- **Headers**: `Authorization: Bearer {token}`, `Content-Type: application/json`
- **Body**: `{"properties": {"codeInputType": "inline", "executionType": "synchronous", "code": "..."}}`
- **Response**: `{"properties": {"result": "...", "stdout": "...", "stderr": "..."}}`

## Azure Setup Requirements

To use the ACA sandbox, you need:

### 1. Create Session Pool

```bash
az containerapp sessionpool create \
    --name code-interpreter-pool \
    --resource-group your-resource-group \
    --location eastasia \
    --max-sessions 100 \
    --container-type PythonLTS \
    --cooldown-period 300
```

### 2. Get Pool Management Endpoint

```bash
az containerapp sessionpool show \
    --name code-interpreter-pool \
    --resource-group your-resource-group \
    --query properties.poolManagementEndpoint \
    --output tsv
```

### 3. Assign Roles

For Azure CLI authentication:
```bash
# Get your user principal ID
az ad signed-in-user show --query id --output tsv

# Assign Session Executor role
az role assignment create \
    --role "Azure ContainerApps Session Executor" \
    --assignee <YOUR_USER_ID> \
    --scope <SESSION_POOL_RESOURCE_ID>

# Assign Contributor role
az role assignment create \
    --role "Contributor" \
    --assignee <YOUR_USER_ID> \
    --scope <SESSION_POOL_RESOURCE_ID>
```

For Managed Identity (production):
```bash
# Get managed identity principal ID
az identity show \
    --name your-identity-name \
    --resource-group your-resource-group \
    --query principalId \
    --output tsv

# Assign roles to managed identity
az role assignment create \
    --role "Azure ContainerApps Session Executor" \
    --assignee <MANAGED_IDENTITY_PRINCIPAL_ID> \
    --scope <SESSION_POOL_RESOURCE_ID>

az role assignment create \
    --role "Contributor" \
    --assignee <MANAGED_IDENTITY_PRINCIPAL_ID> \
    --scope <SESSION_POOL_RESOURCE_ID>
```

## Environment Variables

Add to your `.env` file:

```env
# Azure Container Apps Configuration
ACA_POOL_MANAGEMENT_ENDPOINT=https://eastasia.dynamicsessions.io/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/your-rg/sessionPools/code-interpreter-pool
```

## Testing

### Run Test Script

```bash
python test_sandboxes.py
```

Expected output for ACA sandbox:
```
============================================================
Testing ACA Sandbox - New York, February 2026
============================================================
ACA Pool Management Endpoint found: https://eastasia.dynamicsessions.io/subscriptions...

--- Starting ACA Execution ---
2026-01-02 12:00:00,000 - tools.weather_sandbox_aca - INFO - ☁️ ACA Sandbox creating for destination: New York
☁️ ACA Sandbox creating for destination: New York
2026-01-02 12:00:01,234 - tools.weather_sandbox_aca - INFO - ✓ ACA Sandbox created (1234ms)
✓ ACA Sandbox created (1234ms)
2026-01-02 12:00:01,235 - tools.weather_sandbox_aca - INFO - ▶️ ACA Sandbox code execution starting for destination: New York (1234ms)
▶️ ACA Sandbox code execution starting for destination: New York (1234ms)
2026-01-02 12:00:03,456 - tools.weather_sandbox_aca - INFO - ✅ ACA Sandbox execution finished for destination: New York (3456ms)
✅ ACA Sandbox execution finished for destination: New York (3456ms)
2026-01-02 12:00:03,500 - tools.weather_sandbox_aca - INFO - 🔒 ACA Sandbox closed for destination: New York (total: 3500ms)
🔒 ACA Sandbox closed for destination: New York (total: 3500ms)

--- Tool Output ---
☁️ [Azure Container Apps Sandbox]
🌍 Weather for New York
...
```

### Install Dependencies

```bash
pip install azure-identity
```

Note: `requests` is already in requirements.txt

## Performance Characteristics

**Expected Timing:**
- Session creation: ~1-2 seconds (first call)
- Session reuse: ~50-100ms (subsequent calls with same identifier)
- Code execution: ~2-3 seconds (similar to E2B)
- Total time (first call): ~3-5 seconds
- Total time (reused session): ~2-3 seconds

**Comparison:**
- **Local**: ~500ms-2s (fastest, no isolation)
- **E2B**: ~3-5s (cloud sandbox, cold start)
- **ACA**: ~3-5s first call, ~2-3s with session reuse (cloud sandbox, Azure-native)

## Security & Isolation

- **Hyper-V Boundaries**: Each session runs in isolated Hyper-V container
- **Network Isolation**: Configurable network policies
- **Resource Limits**: CPU, memory, and storage limits per session
- **Automatic Cleanup**: Sessions auto-terminate after idle period
- **Audit Logging**: All session activity logged to Azure Monitor
- **Role-Based Access**: Fine-grained access control via Azure RBAC

## Error Handling

The implementation handles:
1. Missing `ACA_POOL_MANAGEMENT_ENDPOINT` - returns configuration error
2. Import errors - returns SDK installation instructions
3. Authentication failures - returns Azure credential error
4. Session creation failures - returns ACA error details
5. Code execution errors - returns execution error with context

## Logging

All ACA sandbox operations log to both:
1. **Python logger** (`tools.weather_sandbox_aca`) - for DevUI integration
2. **stdout/print** - for terminal visibility

Log levels:
- `INFO` - All operational events (sandbox lifecycle, timing)
- `ERROR` - Failures and exceptions

## Cost Considerations

Azure Container Apps dynamic sessions billing:
- Charged per session duration (not per API call)
- ~$0.000018 per session-second
- Idle sessions consume no resources after timeout
- Session reuse reduces costs significantly

**Optimization Tips:**
1. Use consistent session identifiers to enable reuse
2. Configure appropriate cooldown period (balance cost vs. cold start)
3. Monitor session pool utilization
4. Set appropriate max concurrent sessions

## Next Steps

1. **Install Dependencies**:
   ```bash
   pip install azure-identity
   ```
   (Note: `requests` is already installed)

2. **Create Azure Resources**:
   - Create session pool
   - Get management endpoint
   - Assign RBAC roles

3. **Configure Environment**:
   - Add `ACA_POOL_MANAGEMENT_ENDPOINT` to `.env`

4. **Test Implementation**:
   ```bash
   python test_sandboxes.py
   ```

5. **Integrate with Application**:
   - Restart main.py
   - Test with "Sandbox-ACA" agent in DevUI

## Files Modified

1. ✅ `tools/weather_sandbox_aca.py` - NEW (ACA implementation)
2. ✅ `tools/travel_tools.py` - Updated factory to route ACA
3. ✅ `requirements.txt` - Added semantic-kernel dependency
4. ✅ `.env.example` - Added ACA configuration template
5. ✅ `test_sandboxes.py` - Added ACA test case

## Success Criteria

- ✅ ACA sandbox implementation created
- ✅ Factory pattern routes "Sandbox-ACA" correctly
- ✅ Dependencies documented and added
- ✅ Configuration template provided
- ✅ Test script includes ACA testing
- ✅ Logging with millisecond timing implemented
- ✅ Error handling for missing configuration
- ✅ Documentation created

## References

- [Azure Container Apps Sessions Documentation](https://learn.microsoft.com/en-us/azure/container-apps/sessions-code-interpreter)
- [Semantic Kernel Tutorial](https://learn.microsoft.com/en-us/azure/container-apps/sessions-tutorial-semantic-kernel)
- [SessionsPythonTool Documentation](https://learn.microsoft.com/en-us/python/api/semantic-kernel/)
- [Azure Container Apps Pricing](https://azure.microsoft.com/en-us/pricing/details/container-apps/)
