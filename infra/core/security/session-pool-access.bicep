@description('Session Pool resource ID')
param sessionPoolId string

@description('Principal ID of the managed identity that needs session pool executor access')
param principalId string

// Reference the existing session pool
resource sessionPool 'Microsoft.App/sessionPools@2024-02-02-preview' existing = {
  name: split(sessionPoolId, '/')[8]
}

// Grant 'Azure ContainerApps Session Executor' role to the managed identity
// Role ID: 0fb8eba5-a2bb-4abe-b1c1-49dfad359bb0
resource sessionExecutorRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(sessionPool.id, principalId, 'SessionExecutor')
  scope: sessionPool
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '0fb8eba5-a2bb-4abe-b1c1-49dfad359bb0') // Azure ContainerApps Session Executor
    principalId: principalId
    principalType: 'ServicePrincipal'
  }
}

output roleAssignmentId string = sessionExecutorRole.id
