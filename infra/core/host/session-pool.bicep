param name string
param location string = resourceGroup().location
param tags object = {}

@description('Container Apps Environment resource ID')
param containerAppsEnvironmentId string

@description('Maximum number of concurrent sessions')
param maxConcurrentSessions int = 100

@description('Session idle timeout in seconds (default 10 minutes)')
param cooldownPeriodInSeconds int = 600

resource sessionPool 'Microsoft.App/sessionPools@2024-02-02-preview' = {
  name: name
  location: location
  tags: tags
  properties: {
    environmentId: containerAppsEnvironmentId
    poolManagementType: 'Dynamic'
    containerType: 'PythonLTS'
    scaleConfiguration: {
      maxConcurrentSessions: maxConcurrentSessions
    }
    dynamicPoolConfiguration: {
      cooldownPeriodInSeconds: cooldownPeriodInSeconds
      executionType: 'Timed'
    }
    sessionNetworkConfiguration: {
      status: 'EgressEnabled'
    }
  }
}

output id string = sessionPool.id
output name string = sessionPool.name
output poolManagementEndpoint string = sessionPool.properties.poolManagementEndpoint
