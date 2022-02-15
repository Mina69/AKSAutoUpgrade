locals {
  app_name  = yamldecode(file("./config-function.yaml"))["name"]
  version   = yamldecode(file("./config-function.yaml"))["version"]
  functions = yamldecode(file("./config-function.yaml"))["functions"]
}

data "azuread_client_config" "current" {}
data "azurerm_subscription" "current" {}

resource "azurerm_storage_account" "functionapp1" {
  name                     = "funcapp1demo${var.environment}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}
resource "azurerm_storage_table" "tb1" {
  name                 = "AKSVersion"
  storage_account_name = azurerm_storage_account.functionapp1.name
}
resource "azurerm_app_service_plan" "plan1" {
  name                = "azure-functions-service-plan-demo"
  location            = var.location
  resource_group_name = var.resource_group_name
  kind                = "linux"
  reserved            = true
  
  sku {
    tier = "Standard"
    size = "S1" 
  }
  tags= var.tags
}

resource "azurerm_function_app" "functionapp1" {
  name                       = "demo-app1-${var.environment}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  app_service_plan_id        = azurerm_app_service_plan.plan1.id
  storage_account_name       = azurerm_storage_account.functionapp1.name
  storage_account_access_key = azurerm_storage_account.functionapp1.primary_access_key
  os_type                    = "linux"
  version                    = "~3"

  site_config {
    always_on        = true
    linux_fx_version = "Python|3.7"
    use_32_bit_worker_process = false
    min_tls_version = "1.2"
   }

  identity {
     type         = "SystemAssigned"
   }
   
   app_settings = {
     FUNCTIONS_WORKER_RUNTIME       = "python"
     tenant_id                      = "****"
     function_client_id             = "@Microsoft.KeyVault(VaultName=kv-demo-${var.environment};SecretName=function-client-app-id;SecretVersion=****)"
     function_client_secret         = "@Microsoft.KeyVault(VaultName=kv-demo-${var.environment};SecretName=function-client-secret;SecretVersion=****)"
     slack_webhook_url              = "@Microsoft.KeyVault(VaultName=kv-demo-${var.environment};SecretName=slack-webhook-url;SecretVersion=****)"
     APPINSIGHTS_INSTRUMENTATIONKEY = "${azurerm_application_insights.app-insight1.instrumentation_key}"
     slack_channel_name             = "demo-webhook"
     BUILD_FLAGS                    = "UseExpressBuild"
   }
 }

###Application Insights
resource "azurerm_log_analytics_workspace" "workspace1" {
  name                = "workspace-demo-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Free"
  retention_in_days   = 7
}

resource "azurerm_application_insights" "app-insight1" {
  name                = "functions-appinsights-demo"
  location            = var.location
  resource_group_name = var.resource_group_name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.workspace1.id
}

resource "azuread_application" "func" {
  display_name = "sp-app-functions-demo-${var.environment}"
  owners       = [data.azuread_client_config.current.object_id]
}

resource "azuread_service_principal" "func" {
  application_id               = azuread_application.func.application_id
  app_role_assignment_required = true
  owners                       = [data.azuread_client_config.current.object_id]
}

resource "azurerm_role_assignment" "read" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Reader" 
  principal_id         = azuread_service_principal.func.id
}
resource "azurerm_role_definition" "func" {
  name        = "functionapp-custom-role"
  scope       = data.azurerm_subscription.current.id
  description = "This is a custom role created via Terraform"

  permissions {
    actions     = ["Microsoft.ContainerService/managedClusters/write", "Microsoft.ContainerService/managedClusters/read", "Microsoft.ContainerService/managedClusters/agentpools/write", "microsoft.web/sites/functions/write", "microsoft.web/sites/functions/read", "Microsoft.Storage/storageAccounts/tableServices/tables/read", "Microsoft.Storage/storageAccounts/tableServices/tables/write"]
    not_actions = []
  }

  assignable_scopes = [
    data.azurerm_subscription.current.id
  ]
}
resource "azurerm_role_assignment" "funcapp-clusteraceess" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = azurerm_role_definition.func.name 
  principal_id         = azuread_service_principal.func.id
}
##Give appfunction access to fetch sp client-id and secret in order to use this SP for action process.
resource "azurerm_role_assignment" "funcapp-read" {
  scope                = data.azurerm_subscription.current.id
  role_definition_name = "Key Vault Secrets Officer" 
  principal_id         = azurerm_function_app.functionapp1.identity.0.principal_id
}
