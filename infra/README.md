# Infrastructure Deployment Guide

This directory contains the Infrastructure as Code (IaC) for deploying the Cool Vibes Travel Agent application to Azure using Azure Developer CLI (azd).

## Architecture

The deployment includes:
- **Azure OpenAI Service** - GPT-4o model for the AI agent
- **Azure Container Apps** - Hosting the Python application
- **Azure Container Apps Session Pool** - Python code interpreter sandbox for safe code execution
- **Azure Container Registry** - Storing the container image
- **Application Insights** - Application monitoring and observability
- **Log Analytics** - Monitoring and diagnostics

## Prerequisites

1. **Install Azure Developer CLI (azd)**
   ```powershell
   # Windows (PowerShell)
   powershell -ex AllSigned -c "Invoke-RestMethod 'https://aka.ms/install-azd.ps1' | Invoke-Expression"
   ```

2. **Install Azure CLI**
   ```powershell
   winget install Microsoft.AzureCLI
   ```

3. **Install Docker** (for building container images)
   - Download from https://www.docker.com/products/docker-desktop

4. **Azure Subscription** with permissions to create resources

## Deployment Steps

### 1. Login to Azure

```bash
azd auth login
```

### 2. Deploy infrastructure and application

```bash
azd up
```

When prompted:
- **Environment name**: Choose a name (e.g., `dev`, `prod`)
- **Location**: Choose an Azure region (e.g., `eastus`, `westus2`)

This command will:
1. Create all Azure resources defined in `infra/main.bicep`
2. Build the Docker container from `Dockerfile`
3. Push the container to Azure Container Registry
4. Deploy the container to Azure Container Apps

### 3. Access the application

After deployment completes, azd will output the application URL:

```
Service web URI: https://ca-xxxxx.region.azurecontainerapps.io
```

Navigate to this URL in your browser to access the DevUI interface.

## Environment Variables

The application automatically receives these environment variables from Azure:

- `AZURE_OPENAI_ENDPOINT` - OpenAI service endpoint
- `AZURE_OPENAI_API_KEY` - OpenAI API key (stored as secret)
- `AZURE_OPENAI_API_VERSION` - API version (preview)
- `AZURE_OPENAI_DEPLOYMENT_NAME` - Model deployment name (gpt-4o)
- `ACA_POOL_MANAGEMENT_ENDPOINT` - Container Apps Session Pool endpoint
- `AZURE_CLIENT_ID` - Managed identity client ID for session pool auth
- `APPLICATIONINSIGHTS_CONNECTION_STRING` - Application Insights connection

## Customization

### Change Azure OpenAI Model

Edit `infra/main.bicep`:

```bicep
param openAiModelName string = 'gpt-4o'          // Change model
param openAiModelVersion string = '2024-11-20'    // Change version
param openAiModelCapacity int = 10                // Change capacity
```

### Change Container Resources

Edit `infra/main.bicep`:

```bicep
param containerCpuCoreCount string = '1.0'       // CPU cores
param containerMemory string = '2.0Gi'           // Memory
param containerMinReplicas int = 1               // Min instances
param containerMaxReplicas int = 10              // Max instances
```

## Useful Commands

```bash
# Deploy only infrastructure changes
azd provision

# Deploy only application code changes
azd deploy

# View deployment logs
azd monitor --logs

# View all resources in the environment
azd show

# Delete all resources
azd down
```

## Monitoring

View application logs and metrics:

```bash
# Stream logs in terminal
azd monitor --logs

# Open Azure Portal
azd show --resource-group
```

Or navigate to Azure Portal → Container Apps → Logs

## Troubleshooting

### Container won't start

Check logs:
```bash
azd monitor --logs
```

Common issues:
- Missing environment variables
- Session pool endpoint not configured
- OpenAI API key invalid

### Deployment fails

```bash
# View detailed error
azd provision --debug
```

### Session Pool not working

1. Verify the managed identity has the 'Azure ContainerApps Session Executor' role
2. Check `ACA_POOL_MANAGEMENT_ENDPOINT` is set correctly
3. Ensure `AZURE_CLIENT_ID` matches the user-assigned managed identity

## Clean Up

To delete all resources:

```bash
azd down --purge
```

This will delete:
- Resource group and all resources
- Local environment configuration
