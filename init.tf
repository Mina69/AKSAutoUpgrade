terraform {
  backend "azurerm" {
    subscription_id      = "****"
    resource_group_name  = "rg-demo-sandbox"
    storage_account_name = "satfbackenddemo"
    key                  = "terraform-sandbox.tfstate"
    container_name       = "demo"
  }
}

provider "azurerm" {
  subscription_id = "****"
  tenant_id = "****"
  features {}
}

