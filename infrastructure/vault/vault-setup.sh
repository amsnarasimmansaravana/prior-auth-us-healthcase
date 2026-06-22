#!/usr/bin/env bash
set -euo pipefail

# Vault bootstrap for PA Healthcare
# Usage: VAULT_ADDR and VAULT_TOKEN must be set in environment

: ${VAULT_ADDR:?Need VAULT_ADDR}
: ${VAULT_TOKEN:?Need VAULT_TOKEN}

export VAULT_ADDR
export VAULT_TOKEN

# Enable Kubernetes auth
vault auth enable kubernetes || true

# Configure k8s auth (requires service account JWT and CA cert setup)
# The following values must be adapted to your cluster and service account
K8S_HOST=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.server}')
K8S_CA_CERT=$(kubectl get secret -n kube-system -o jsonpath='{.data.ca\.crt}' 2>/dev/null || true)

vault write auth/kubernetes/config \
  token_reviewer_jwt="$(kubectl get secret $(kubectl get serviceaccount pa-healthcare-sa -n pa-healthcare -o jsonpath='{.secrets[0].name}') -n pa-healthcare -o jsonpath='{.data.token}' | base64 --decode)" \
  kubernetes_host="$K8S_HOST" \
  kubernetes_ca_cert="$K8S_CA_CERT" || true

# Create role
vault write auth/kubernetes/role/pa-healthcare-k8s \
  bound_service_account_names=pa-healthcare-sa \
  bound_service_account_namespaces=pa-healthcare \
  policies=pa-healthcare-policy \
  ttl=24h || true

# Create KV secret path and store sample secret
vault kv put secret/pa-healthcare/config DB_CONNECTION="postgres://user:pass@db:5432/pa" API_KEY="changeme" || true

echo "Vault bootstrap completed"
