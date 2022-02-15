variable "location" {
  type    = string
  default = "West Europe"
}

variable "resource_group_name" {
  type    = string
  default = "rg-demo-sandbox"
}

variable "tags" {
  type    = map(any)
  default = {
    Env = "Sandbox",
    App = "Demo",
  }
}
variable "global_tags" {
  description = "Tags to attach to resource groups"
  type        = map(any)
  default = {
    manager = "terraform",
  }
}

variable "environment" {
  description = "Name of Environment"
  type        = string
  default = "sandbox"
}

