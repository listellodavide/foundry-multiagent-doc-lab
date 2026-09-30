# Optional Lab 8 Azure deployment

The workshop requires only the local Core Tools and Azurite run. This optional deployment creates
a Python 3.14 Flex Consumption Function App, storage account and system-assigned managed identity.

```bash
az group create --name rg-foundry-workshop-durable --location westeurope
az deployment group create \
  --resource-group rg-foundry-workshop-durable \
  --template-file infra/durable/main.bicep \
  --parameters projectEndpoint="$PROJECT_ENDPOINT" modelDeploymentName="$MODEL_DEPLOYMENT_NAME"
```

Grant the resulting Function App identity **Azure AI User** (or the workshop's approved equivalent)
on the Foundry project before publishing the Lab 8 function. The template does not contain model
keys. Delete the resource group after the optional exercise.
