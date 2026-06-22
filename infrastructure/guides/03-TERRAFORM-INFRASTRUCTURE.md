---
title: Terraform Infrastructure as Code for PA Healthcare AKS Deployment
status: draft
owner: Platform Engineering
type: technical
version: 1.0.0
tags:
  - terraform
  - aks
  - infrastructure
  - iac
related:
  - infrastructure/guides/01-HPA-DEPLOYMENT-STRATEGY.md
  - infrastructure/guides/02-HELM-CHART-STRUCTURE.md
  - infrastructure/vault/vault-setup.sh
last_updated: 2026-06-22
---

# Terraform Infrastructure as Code for PA Healthcare AKS

## Overview

This document describes the Terraform configuration for provisioning and managing the PA Healthcare platform infrastructure on Azure Kubernetes Service (AKS) with HPA, monitoring, and HashiCorp Vault integration.

## Terraform File Structure

```
terraform/
├── main.tf                    # Main provider configuration
├── variables.tf               # Input variables
├── outputs.tf                 # Output values
├── aks-cluster.tf            # AKS cluster configuration
├── aks-addons.tf             # AKS add-ons (CNI, autoscaler, etc.)
├── aks-node-pools.tf         # Node pools configuration
├── monitoring.tf             # Prometheus, Grafana, alerts
├── vault.tf                  # Vault infrastructure
├── networking.tf             # Virtual networks, subnets
├── storage.tf                # Storage accounts, managed disks
├── secrets.tf                # Key Vault integration
├── environments/
│   ├── staging.tfvars        # Staging environment variables
│   ├── production.tfvars     # Production environment variables
│   └── development.tfvars    # Development environment variables
├── modules/
│   ├── aks/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── networking/
│   │   ├── main.tf
│   │   └── variables.tf
│   ├── monitoring/
│   │   ├── main.tf
│   │   └── variables.tf
│   └── vault/
│       ├── main.tf
│       └── variables.tf
└── terraform.tfstate         # State file (in remote backend)
```

## Core Configuration Files

### 1. main.tf - Provider & Backend

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.9"
    }
    vault = {
      source  = "hashicorp/vault"
      version = "~> 3.15"
    }
  }

  backend "azurerm" {
    resource_group_name  = "pa-healthcare-state"
    storage_account_name = "pahealthcarestate"
    container_name       = "tfstate"
    key                  = "aks.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
  subscription_id = var.azure_subscription_id
}

provider "kubernetes" {
  host                   = azurerm_kubernetes_cluster.aks.kube_config[0].host
  client_certificate    = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate)
  client_key            = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_key)
  cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate)
}

provider "helm" {
  kubernetes {
    host                   = azurerm_kubernetes_cluster.aks.kube_config[0].host
    client_certificate    = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_certificate)
    client_key            = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].client_key)
    cluster_ca_certificate = base64decode(azurerm_kubernetes_cluster.aks.kube_config[0].cluster_ca_certificate)
  }
}

provider "vault" {
  address = var.vault_address
  token   = var.vault_token
}
```

### 2. variables.tf - Input Variables

```hcl
# Azure Configuration
variable "azure_subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true
}

variable "azure_region" {
  description = "Azure region for resources"
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "pa-healthcare"
}

# AKS Configuration
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "aks_vm_size" {
  description = "VM size for AKS node pool"
  type        = string
  default     = "Standard_D4s_v3"
}

variable "aks_node_count" {
  description = "Initial node count"
  type        = number
  default     = 3
  validation {
    condition     = var.aks_node_count >= 2 && var.aks_node_count <= 100
    error_message = "Node count must be between 2 and 100."
  }
}

variable "aks_autoscale_min" {
  description = "Autoscaler minimum nodes"
  type        = number
  default     = 2
}

variable "aks_autoscale_max" {
  description = "Autoscaler maximum nodes"
  type        = number
  default     = 20
}

# Network Configuration
variable "vnet_cidr" {
  description = "Virtual Network CIDR"
  type        = string
  default     = "10.0.0.0/16"
}

variable "aks_subnet_cidr" {
  description = "AKS subnet CIDR"
  type        = string
  default     = "10.0.1.0/24"
}

# Vault Configuration
variable "vault_address" {
  description = "Vault server address"
  type        = string
}

variable "vault_token" {
  description = "Vault authentication token"
  type        = string
  sensitive   = true
}

variable "vault_kubernetes_role" {
  description = "Kubernetes auth role in Vault"
  type        = string
  default     = "pa-healthcare-k8s"
}

# Monitoring Configuration
variable "enable_monitoring" {
  description = "Enable Prometheus and Grafana"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Log retention in days"
  type        = number
  default     = 30
}

# Tags
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "pa-healthcare"
  }
}
```

### 3. aks-cluster.tf - AKS Cluster

```hcl
resource "azurerm_resource_group" "aks" {
  name     = "${var.project_name}-${var.environment}-rg"
  location = var.azure_region
  tags     = var.common_tags
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                = "${var.project_name}-${var.environment}-aks"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  dns_prefix          = "${var.project_name}-${var.environment}"

  kubernetes_version = var.kubernetes_version

  default_node_pool {
    name                = "default"
    node_count          = var.aks_node_count
    vm_size             = var.aks_vm_size
    vnet_subnet_id      = azurerm_subnet.aks.id
    enable_auto_scaling = true
    min_count           = var.aks_autoscale_min
    max_count           = var.aks_autoscale_max

    node_labels = {
      Environment = var.environment
      NodeType    = "system"
    }

    tags = var.common_tags
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
    dns_service_ip = "10.0.0.10"
    service_cidr   = "10.0.0.0/16"
  }

  identity {
    type = "SystemAssigned"
  }

  workload_identity_enabled = true
  oidc_issuer_enabled       = true

  tags = var.common_tags

  depends_on = [
    azurerm_virtual_network.aks
  ]
}

# Additional node pools for different workload types
resource "azurerm_kubernetes_cluster_node_pool" "agent_services" {
  name                  = "agents"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = "Standard_D4s_v3"
  node_count            = 3
  enable_auto_scaling   = true
  min_count             = 2
  max_count             = 15

  node_labels = {
    workload = "agents"
    tier     = "compute"
  }

  tags = var.common_tags
}

resource "azurerm_kubernetes_cluster_node_pool" "decision_services" {
  name                  = "decision"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = "Standard_E4s_v3"
  node_count            = 3
  enable_auto_scaling   = true
  min_count             = 3
  max_count             = 20

  node_labels = {
    workload = "decision"
    tier     = "critical"
  }

  tags = var.common_tags
}

resource "azurerm_kubernetes_cluster_node_pool" "data_services" {
  name                  = "data"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id
  vm_size               = "Standard_D8s_v3"
  node_count            = 2
  enable_auto_scaling   = true
  min_count             = 2
  max_count             = 10

  node_labels = {
    workload = "data"
    tier     = "storage"
  }

  tags = var.common_tags
}
```

### 4. aks-addons.tf - Add-ons Configuration

```hcl
# Container Insights
resource "azurerm_log_analytics_workspace" "aks" {
  name                = "${var.project_name}-${var.environment}-log"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_retention_days

  tags = var.common_tags
}

# Enable Container Insights
resource "azurerm_kubernetes_cluster_addon_profile" "oms_agent" {
  kubernetes_cluster_id = azurerm_kubernetes_cluster.aks.id

  oms_agent {
    enabled                    = true
    log_analytics_workspace_id = azurerm_log_analytics_workspace.aks.id
  }
}

# Cluster Autoscaler (already configured via default_node_pool)
# Metrics Server
resource "helm_release" "metrics_server" {
  name             = "metrics-server"
  repository       = "https://kubernetes-sigs.github.io/metrics-server/"
  chart            = "metrics-server"
  namespace        = "kube-system"
  create_namespace = false

  values = [
    yamlencode({
      args = [
        "--kubelet-insecure-tls",
        "--kubelet-preferred-address-types=InternalIP"
      ]
    })
  ]

  depends_on = [azurerm_kubernetes_cluster.aks]
}

# Cert-Manager for HTTPS
resource "helm_release" "cert_manager" {
  name             = "cert-manager"
  repository       = "https://charts.jetstack.io"
  chart            = "cert-manager"
  namespace        = "cert-manager"
  create_namespace = true
  version          = "v1.13.0"

  set {
    name  = "installCRDs"
    value = "true"
  }

  depends_on = [azurerm_kubernetes_cluster.aks]
}

# Ingress Controller (Nginx)
resource "helm_release" "nginx_ingress" {
  name             = "nginx-ingress"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  namespace        = "ingress-nginx"
  create_namespace = true

  values = [
    yamlencode({
      controller = {
        service = {
          type = "LoadBalancer"
        }
        resources = {
          requests = {
            cpu    = "100m"
            memory = "90Mi"
          }
        }
      }
    })
  ]

  depends_on = [azurerm_kubernetes_cluster.aks]
}

# Workload Identity Setup
resource "azurerm_user_assigned_identity" "pa_healthcare" {
  name                = "${var.project_name}-${var.environment}-identity"
  resource_group_name = azurerm_resource_group.aks.name
  location            = azurerm_resource_group.aks.location
}

resource "azurerm_federated_identity_credential" "pa_healthcare" {
  name                = "${var.project_name}-${var.environment}-fic"
  resource_group_name = azurerm_resource_group.aks.name
  audience            = ["api://AzureADTokenExchange"]
  issuer              = azurerm_kubernetes_cluster.aks.oidc_issuer_url
  parent_id           = azurerm_user_assigned_identity.pa_healthcare.id
  subject             = "system:serviceaccount:pa-healthcare:pa-healthcare-sa"
}

# Role Assignment for User Identity
resource "azurerm_role_assignment" "pa_healthcare_contributor" {
  scope              = azurerm_resource_group.aks.id
  role_definition_name = "Contributor"
  principal_id       = azurerm_user_assigned_identity.pa_healthcare.principal_id
}
```

### 5. monitoring.tf - Prometheus & Grafana

```hcl
# Prometheus
resource "helm_release" "prometheus" {
  count            = var.enable_monitoring ? 1 : 0
  name             = "prometheus"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  namespace        = "monitoring"
  create_namespace = true
  version          = "55.0.0"

  values = [
    yamlencode({
      prometheus = {
        prometheusSpec = {
          retention = "30d"
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = "managed-premium"
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = "50Gi"
                  }
                }
              }
            }
          }
        }
      }
      grafana = {
        enabled = true
        adminPassword = random_password.grafana_password.result
      }
    })
  ]

  depends_on = [azurerm_kubernetes_cluster.aks]
}

resource "random_password" "grafana_password" {
  length  = 16
  special = true
}

# Service Monitor for HPA metrics
resource "kubernetes_manifest" "servicemonitor_hpa" {
  count     = var.enable_monitoring ? 1 : 0
  manifest  = yamldecode(file("${path.module}/manifests/servicemonitor-hpa.yaml"))
  depends_on = [helm_release.prometheus]
}
```

### 6. vault.tf - Vault Configuration

```hcl
# Azure Key Vault for Secrets
resource "azurerm_key_vault" "pa_healthcare" {
  name                        = "${var.project_name}-${var.environment}-kv"
  location                    = azurerm_resource_group.aks.location
  resource_group_name         = azurerm_resource_group.aks.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  sku_name                    = "premium"
  enabled_for_disk_encryption = true
  purge_protection_enabled    = true

  tags = var.common_tags
}

# Access Policy for Workload Identity
resource "azurerm_key_vault_access_policy" "pa_healthcare" {
  key_vault_id = azurerm_key_vault.pa_healthcare.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.pa_healthcare.principal_id

  secret_permissions = [
    "Get",
    "List"
  ]

  key_permissions = [
    "Get",
    "List"
  ]
}

# External Secrets Operator for Vault integration
resource "helm_release" "external_secrets" {
  name             = "external-secrets"
  repository       = "https://charts.external-secrets.io"
  chart            = "external-secrets"
  namespace        = "external-secrets-system"
  create_namespace = true
  version          = "0.9.0"

  depends_on = [azurerm_kubernetes_cluster.aks]
}

# Secret Store for Vault
resource "kubernetes_manifest" "secretstore_vault" {
  manifest = yamldecode(file("${path.module}/manifests/secretstore-vault.yaml"))
  depends_on = [helm_release.external_secrets]
}

# Retrieve current Azure context
data "azurerm_client_config" "current" {}
```

### 7. networking.tf - Network Configuration

```hcl
resource "azurerm_virtual_network" "aks" {
  name                = "${var.project_name}-${var.environment}-vnet"
  address_space       = [var.vnet_cidr]
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name

  tags = var.common_tags
}

resource "azurerm_subnet" "aks" {
  name                 = "${var.project_name}-${var.environment}-subnet"
  resource_group_name  = azurerm_resource_group.aks.name
  virtual_network_name = azurerm_virtual_network.aks.name
  address_prefixes     = [var.aks_subnet_cidr]
}

# Network Security Group
resource "azurerm_network_security_group" "aks" {
  name                = "${var.project_name}-${var.environment}-nsg"
  location            = azurerm_resource_group.aks.location
  resource_group_name = azurerm_resource_group.aks.name

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 101
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = var.common_tags
}
```

### 8. outputs.tf - Output Values

```hcl
output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.aks.name
}

output "aks_kube_config" {
  value     = azurerm_kubernetes_cluster.aks.kube_config_raw
  sensitive = true
}

output "aks_endpoint" {
  value = azurerm_kubernetes_cluster.aks.kube_config[0].host
}

output "oidc_issuer_url" {
  value = azurerm_kubernetes_cluster.aks.oidc_issuer_url
}

output "grafana_password" {
  value     = random_password.grafana_password.result
  sensitive = true
}

output "key_vault_id" {
  value = azurerm_key_vault.pa_healthcare.id
}

output "identity_principal_id" {
  value = azurerm_user_assigned_identity.pa_healthcare.principal_id
}

output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.aks.id
}
```

## Environment Configuration Files

### staging.tfvars
```hcl
environment                = "staging"
azure_region              = "eastus"
aks_vm_size               = "Standard_D4s_v3"
aks_node_count            = 3
aks_autoscale_min         = 2
aks_autoscale_max         = 10
log_retention_days        = 30
enable_monitoring         = true
```

### production.tfvars
```hcl
environment                = "prod"
azure_region              = "eastus"
aks_vm_size               = "Standard_D8s_v3"
aks_node_count            = 5
aks_autoscale_min         = 5
aks_autoscale_max         = 30
log_retention_days        = 90
enable_monitoring         = true
```

## Deployment Commands

### Initialize Terraform
```bash
cd infrastructure/terraform
terraform init -upgrade
```

### Plan Deployment
```bash
terraform plan \
  -var-file="environments/staging.tfvars" \
  -var="azure_subscription_id=$AZURE_SUBSCRIPTION_ID" \
  -var="vault_address=$VAULT_ADDR" \
  -var="vault_token=$VAULT_TOKEN" \
  -out=tfplan
```

### Apply Changes
```bash
terraform apply tfplan
```

### Get Kubeconfig
```bash
terraform output -raw aks_kube_config > ~/.kube/config-pa-healthcare
chmod 600 ~/.kube/config-pa-healthcare
```

### Destroy Infrastructure (Carefully!)
```bash
terraform destroy -var-file="environments/staging.tfvars"
```

## Best Practices

1. **Use Remote State**: Store `.tfstate` in Azure Storage with encryption and locking
2. **Separate Concerns**: Keep infrastructure, monitoring, and app configs in separate files
3. **Version Control**: Commit `.tf` and `.tfvars` files; never commit `.tfstate`
4. **Use Modules**: Abstract complex resources into reusable modules
5. **Implement Workload Identity**: Avoid managing credentials manually
6. **Enable Backup**: Configure cluster backup policies
7. **Auto-scaling**: Enable both Cluster Autoscaler and HPA
8. **Network Policies**: Enforce Azure Network Policies for security
9. **RBAC**: Implement Kubernetes RBAC with proper service accounts
10. **Monitoring**: Always enable Container Insights and Prometheus

## Next Steps

1. Configure Azure CLI with subscription
2. Create storage account for Terraform state
3. Set up Vault for secrets management
4. Run `terraform init` and validate
5. Deploy to staging first
6. Validate HPA and monitoring
7. Deploy to production
