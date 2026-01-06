# Azure Container Apps REST API Implementation Summary

## Overview

The ACA sandbox implementation uses **direct REST API calls** instead of Semantic Kernel or any AI framework. This keeps the code minimal and eliminates unnecessary dependencies.

## What We Use

### ✅ Required Dependencies
- `azure-identity` - For Azure authentication (get tokens)
- `requests` - For making HTTP calls (already in requirements.txt)

### ❌ NOT Required
- ~~`semantic-kernel`~~ - Not needed, we call the API directly
- ~~`FunctionChoiceBehavior`~~ - AI agent feature, not needed
- ~~`ChatHistory`~~ - LLM conversation feature, not needed
- ~~`SessionsPythonTool`~~ - Wrapper around REST API, not needed

## How It Works

### 1. Authentication
```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
token = credential.get_token("https://dynamicsessions.io/.default")
auth_header = f"Bearer {token.token}"
```

### 2. Execute Code via REST API
```python
import requests

execute_url = f"{pool_management_endpoint}/code/execute?api-version=2024-02-02-preview&identifier={session_id}"

payload = {
    "properties": {
        "codeInputType": "inline",
        "executionType": "synchronous",
        "code": "print('Hello, world!')"
    }
}

headers = {
    "Authorization": auth_header,
    "Content-Type": "application/json"
}

response = requests.post(execute_url, json=payload, headers=headers, timeout=30)
result = response.json()
```

### 3. Parse Response
```python
# Response format
{
    "properties": {
        "result": "Hello, world!",  # Return value
        "stdout": "Hello, world!\n",  # Print output
        "stderr": ""  # Error output
    }
}
```

## REST API Endpoint

**Base URL**: From `ACA_POOL_MANAGEMENT_ENDPOINT` environment variable

Example:
```
https://eastasia.dynamicsessions.io/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/my-rg/sessionPools/my-pool
```

**Execute Code Endpoint**:
```
POST {base_url}/code/execute?api-version=2024-02-02-preview&identifier={session_id}
```

**Parameters**:
- `api-version`: `2024-02-02-preview` (current version)
- `identifier`: Unique session ID (e.g., `weather-new-york`)

**Headers**:
- `Authorization`: `Bearer {azure_token}`
- `Content-Type`: `application/json`

**Body**:
```json
{
    "properties": {
        "codeInputType": "inline",
        "executionType": "synchronous",
        "code": "# Your Python code here\nresult = 42\nresult"
    }
}
```

## Session Management

### Session Identifiers
- Used to identify and reuse sessions
- Format: `weather-{destination}` (e.g., `weather-new-york`)
- Same identifier = reuse existing session
- Different identifier = create new session

### Session Lifecycle
1. **First call**: ACA creates new session with the identifier
2. **Subsequent calls**: ACA reuses existing session if still active
3. **Idle timeout**: Session auto-terminates after cooldown period (configurable)

### Benefits of Session Reuse
- Faster execution (no cold start)
- Lower costs (billed per session duration)
- Persistent state within session (variables remain)

## Comparison to E2B

### E2B Implementation
```python
from e2b_code_interpreter import Sandbox

sandbox = Sandbox.create(api_key=api_key)
execution = sandbox.run_code(code)
sandbox.kill()
```

### ACA Implementation
```python
from azure.identity import DefaultAzureCredential
import requests

credential = DefaultAzureCredential()
token = credential.get_token("https://dynamicsessions.io/.default")

response = requests.post(
    f"{endpoint}/code/execute?api-version=2024-02-02-preview&identifier={session_id}",
    json={"properties": {"codeInputType": "inline", "executionType": "synchronous", "code": code}},
    headers={"Authorization": f"Bearer {token.token}", "Content-Type": "application/json"}
)
```

**Both approaches**:
- Make HTTP API calls to cloud sandboxes
- Execute code in isolated containers
- Return results synchronously
- Require API credentials/tokens

## Why No Semantic Kernel?

Semantic Kernel is designed for:
- Building AI agents that use LLMs
- Managing chat conversations
- Function calling with AI models
- Orchestrating multiple AI services

We only need:
- Execute Python code in a sandbox
- Get the result back

**Bottom line**: Semantic Kernel would add complexity and dependencies we don't need. Direct REST API calls are simpler and more transparent.

## Documentation References

- [ACA Sessions REST API](https://learn.microsoft.com/en-us/azure/container-apps/sessions-code-interpreter)
- [Execute Code Endpoint](https://learn.microsoft.com/en-us/azure/container-apps/sessions-code-interpreter#execute-code-in-a-session)
- [Azure Identity Library](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme)

## File Changes

```
tools/weather_sandbox_aca.py
├── Import: azure.identity.DefaultAzureCredential ✅
├── Import: requests ✅
├── Get token: credential.get_token("https://dynamicsessions.io/.default")
├── Build request: POST /code/execute with JSON payload
├── Parse response: Extract result from response.json()
└── Return: "☁️ [Azure Container Apps Sandbox]\n{result}"
```

## Testing

```bash
# Set environment variable
export ACA_POOL_MANAGEMENT_ENDPOINT="https://..."

# Run test
python test_sandboxes.py
```

Expected output shows:
- ☁️ ACA Sandbox session ready (Xms)
- ▶️ ACA Sandbox code execution starting
- ✅ ACA Sandbox execution finished (Xms)
- 🔒 ACA Sandbox session complete (total: Xms)
