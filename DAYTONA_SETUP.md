# Daytona Sandbox Setup Guide

## Overview

Daytona provides secure, isolated code execution environments (sandboxes) that allow you to run untrusted code safely. This guide will help you set up Daytona for use with the Weather Research Tool in the Travel Agent system.

## What is Daytona?

Daytona is a cloud-based sandbox service that allows you to:
- Execute code in isolated, secure environments
- Run untrusted code without risk to your local system
- Get fast, reliable execution with automatic resource management
- Clean up resources automatically after execution

Learn more at: https://www.daytona.io/

## Setup Steps

### 1. Create a Daytona Account

1. Visit the [Daytona Dashboard](https://app.daytona.io/dashboard)
2. Sign up for a free account (if you don't have one)

### 2. Get Your API Key

1. Navigate to [API Keys](https://app.daytona.io/dashboard/keys) in the dashboard
2. Click "Create New API Key"
3. Give it a descriptive name (e.g., "Travel Agent Weather Tool")
4. **Important**: Copy and save the API key immediately - it won't be shown again!

### 3. Install the Daytona SDK

In your project directory, install the Daytona Python SDK:

```bash
pip install daytona
```

Or update your requirements:

```bash
pip install -r requirements.txt
```

### 4. Configure Your Environment

Add your Daytona API key to your `.env` file:

```env
# Daytona Configuration
DAYTONA_API_KEY=your_daytona_api_key_here
```

Replace `your_daytona_api_key_here` with the actual API key you copied from the dashboard.

## Testing Your Setup

Run the sandbox test script to verify everything is working:

```bash
python test_sandboxes.py
```

You should see output like:

```
============================================================
Testing Daytona Sandbox - New York, February 2026
============================================================
Daytona API Key found: dtna_xxxxx...

--- Starting Daytona Execution ---
🚀 Daytona Sandbox creating for destination: New York
✓ Daytona Sandbox created (XXXms)
▶️ Daytona Sandbox code execution starting for destination: New York (XXXms)
✅ Daytona execution finished for destination: New York (XXXms)
🧹 Daytona Sandbox cleaned up

--- Tool Output ---
🔒 [Daytona Sandbox]
🌍 Weather for New York
📅 Current: ☀️ 72°F (22.2°C)
...
```

## Using the Daytona Agent

Once configured, you can use the Sandbox-Daytona agent in your travel agent system:

```python
# The agent will automatically use the Daytona sandbox for weather research
agent_name = "Sandbox-Daytona-cool-vibes-travel-agent"
```

The agent has the following preferences (from `seed.json`):
- Loves sunset photography
- Enjoys running in the morning

## How It Works

When you use the Daytona sandbox:

1. **Sandbox Creation**: A new isolated environment is created in Daytona's cloud
2. **Code Execution**: The weather research code runs securely in the sandbox
3. **Result Retrieval**: Results are returned to your application
4. **Cleanup**: The sandbox is automatically deleted to free resources

## Pricing & Limits

- Check current pricing at: https://www.daytona.io/pricing
- Free tier includes limited sandbox executions per month
- Sandboxes are automatically cleaned up after use to minimize costs

## Troubleshooting

### API Key Not Found

**Error**: `⚠️ DAYTONA_API_KEY not found in environment variables`

**Solution**: 
1. Verify your `.env` file contains the DAYTONA_API_KEY
2. Make sure you've loaded the environment variables (the app uses `python-dotenv`)
3. Restart your application after adding the key

### Import Error

**Error**: `⚠️ Daytona SDK not installed`

**Solution**:
```bash
pip install daytona
```

### Execution Timeout

If execution takes too long, check:
1. Your internet connection
2. Daytona service status
3. Consider fallback to Local sandbox if Daytona is unavailable

### Authentication Error

**Error**: Invalid API key or authentication failed

**Solution**:
1. Verify your API key is correct
2. Check if the key has been revoked in the dashboard
3. Generate a new API key if needed

## Advantages of Daytona Sandbox

✅ **Security**: Code runs in complete isolation from your system  
✅ **Simplicity**: Easy setup with just an API key  
✅ **Reliability**: Managed infrastructure with automatic scaling  
✅ **Clean**: Automatic resource cleanup after execution  
✅ **Fast**: Optimized for quick sandbox creation and execution  

## Comparing Sandboxes

The Travel Agent system supports multiple sandbox types:

| Sandbox | Setup Complexity | Isolation | Best For |
|---------|-----------------|-----------|----------|
| Local | None | ❌ No isolation | Development |
| E2B | Low | ✅ Full isolation | General purpose |
| Daytona | Low | ✅ Full isolation | Quick secure execution |
| ACA | High | ✅ Full isolation | Enterprise Azure |
| Modal | Medium | ✅ Full isolation | Serverless workloads |

## Additional Resources

- [Daytona Documentation](https://www.daytona.io/docs/)
- [Daytona Python SDK](https://github.com/daytonaio/daytona-sdk-python)
- [Getting Started Guide](https://www.daytona.io/docs/en/getting-started)
- [Support Slack](https://go.daytona.io/slack)

## Next Steps

1. ✅ Set up your Daytona API key
2. ✅ Test the sandbox with `test_sandboxes.py`
3. ✅ Use the Sandbox-Daytona agent in your travel agent application
4. 📖 Explore other sandbox options (E2B, ACA, Modal) for comparison
5. 🚀 Deploy your application with secure code execution

Happy coding! 🎉
