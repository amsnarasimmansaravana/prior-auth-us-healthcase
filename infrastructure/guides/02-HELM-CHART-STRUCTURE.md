---
title: PA Healthcare Helm Chart Structure
status: draft
owner: Platform Engineering
type: technical
version: 1.0.0
tags:
  - helm
  - kubernetes
  - deployment
  - charts
related:
  - infrastructure/guides/01-HPA-DEPLOYMENT-STRATEGY.md
  - infrastructure/terraform/aks-cluster.tf
last_updated: 2026-06-22
---

# PA Healthcare Platform - Helm Chart Structure

## Directory Layout

```
helm/pa-healthcare/
├── Chart.yaml                      # Chart metadata
├── Chart.lock                       # Locked dependency versions
├── values.yaml                      # Default values
├── values-staging.yaml             # Staging environment overrides
├── values-production.yaml           # Production environment overrides
├── README.md                        # Chart documentation
├── templates/
│   ├── namespace.yaml              # Kubernetes namespace
│   ├── serviceaccount.yaml         # Service accounts & RBAC
│   ├── configmap.yaml              # Application configuration
│   ├── secrets.yaml                # Secrets (managed by Vault)
│   ├── agents/
│   │   ├── intake-agent.yaml
│   │   ├── eligibility-agent.yaml
│   │   ├── benefits-agent.yaml
│   │   ├── clinical-agent.yaml
│   │   ├── policy-agent.yaml
│   │   ├── fraud-agent.yaml
│   │   ├── decision-agent.yaml
│   │   ├── appeals-agent.yaml
│   │   ├── notification-agent.yaml
│   │   ├── audit-agent.yaml
│   │   └── communication-agent.yaml
│   ├── services/
│   │   ├── member-service.yaml
│   │   ├── provider-service.yaml
│   │   ├── policy-service.yaml
│   │   ├── claims-service.yaml
│   │   ├── benefits-config-service.yaml
│   │   ├── network-service.yaml
│   │   ├── formulary-service.yaml
│   │   └── clinical-content-service.yaml
│   ├── api-gateway/
│   │   ├── kong-deployment.yaml
│   │   ├── kong-service.yaml
│   │   └── kong-ingress.yaml
│   ├── hpa/
│   │   ├── agent-hpa.yaml
│   │   ├── decision-hpa.yaml
│   │   └── support-hpa.yaml
│   ├── monitoring/
│   │   ├── prometheus-config.yaml
│   │   ├── grafana-dashboard.yaml
│   │   └── alerts.yaml
│   ├── vault/
│   │   ├── vault-auth.yaml
│   │   ├── vault-secrets.yaml
│   │   └── external-secrets-operator.yaml
│   └── ingress/
│       ├── api-ingress.yaml
│       └── admin-ingress.yaml
└── charts/
    └── (dependency charts)
```

## Chart.yaml

```yaml
apiVersion: v2
name: pa-healthcare
description: PA Healthcare Agentic AI Platform
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - healthcare
  - agentic-ai
  - multi-agent-orchestration
maintainers:
  - name: Platform Engineering
    email: platform@healthcare.local
dependencies:
  - name: kong
    version: "2.17.0"
    repository: "https://charts.konghq.com"
  - name: prometheus
    version: "25.3.0"
    repository: "https://prometheus-community.github.io/helm-charts"
  - name: grafana
    version: "6.60.0"
    repository: "https://grafana.github.io/helm-charts"
  - name: external-secrets
    version: "0.9.0"
    repository: "https://charts.external-secrets.io"
```

## values.yaml (Default)

```yaml
# Global configuration
global:
  environment: staging
  namespace: pa-healthcare
  domain: pa-healthcare.healthcare.local
  imageRegistry: acr.healthcare.com
  imagePullPolicy: IfNotPresent

# Namespace
namespace:
  name: pa-healthcare
  labels:
    environment: staging

# Service Accounts & RBAC
serviceAccount:
  create: true
  name: pa-healthcare-sa
  annotations:
    azure.workload.identity/client-id: "" # Set via Terraform

# Agent Services Configuration
agents:
  intake:
    replicas: 2
    image: pa-healthcare/intake-agent:1.0.0
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
    hpa:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilization: 70
      targetMemoryUtilization: 75

  eligibility:
    replicas: 2
    image: pa-healthcare/eligibility-agent:1.0.0
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
    hpa:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilization: 70

  benefits:
    replicas: 2
    image: pa-healthcare/benefits-agent:1.0.0
    resources:
      requests:
        cpu: 500m
        memory: 512Mi
      limits:
        cpu: 1000m
        memory: 1Gi
    hpa:
      enabled: true
      minReplicas: 2
      maxReplicas: 10
      targetCPUUtilization: 70

  # ... other agents follow similar pattern

# Decision Services (Tier 2)
decisionServices:
  decision:
    replicas: 3
    image: pa-healthcare/decision-agent:1.0.0
    resources:
      requests:
        cpu: 1000m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 2Gi
    hpa:
      enabled: true
      minReplicas: 3
      maxReplicas: 20
      targetCPUUtilization: 60

# Support Services (Tier 3)
supportServices:
  notification:
    replicas: 2
    image: pa-healthcare/notification-service:1.0.0
    resources:
      requests:
        cpu: 250m
        memory: 256Mi
      limits:
        cpu: 500m
        memory: 512Mi
    hpa:
      enabled: true
      minReplicas: 2
      maxReplicas: 8
      targetCPUUtilization: 80

# API Gateway (Kong)
apiGateway:
  enabled: true
  replicas: 3
  image: kong:3.3-alpine
  service:
    type: LoadBalancer
    port: 80
    tlsPort: 443
  ingress:
    enabled: true
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - host: api.pa-healthcare.healthcare.local
        paths:
          - path: /
            pathType: Prefix

# Monitoring (Prometheus & Grafana)
monitoring:
  enabled: true
  prometheus:
    enabled: true
    retention: 30d
  grafana:
    enabled: true
    adminPassword: "" # Set via secrets
    dashboards:
      - agents
      - services
      - system

# Vault Integration
vault:
  enabled: true
  address: "https://vault.healthcare.local"
  role: "pa-healthcare-k8s"
  secretPath: "secret/data/pa-healthcare"
  authPath: "auth/kubernetes/login"

# Logging
logging:
  enabled: true
  provider: datadog  # or elastic, loki, etc.
  logLevel: info

# Network Policies
networkPolicies:
  enabled: true
  
# Pod Disruption Budgets
pdb:
  enabled: true
  agents:
    minAvailable: 1
  decisionServices:
    minAvailable: 2
  supportServices:
    minAvailable: 1
```

## values-production.yaml

```yaml
global:
  environment: production
  namespace: pa-healthcare-prod

agents:
  intake:
    replicas: 5
    resources:
      requests:
        cpu: 1000m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 2Gi
    hpa:
      minReplicas: 5
      maxReplicas: 20
      targetCPUUtilization: 60

decisionServices:
  decision:
    replicas: 5
    hpa:
      minReplicas: 5
      maxReplicas: 30

monitoring:
  prometheus:
    retention: 90d
  grafana:
    adminPassword: "" # Must be set via secrets

vault:
  address: "https://vault-prod.healthcare.local"

pdb:
  agents:
    minAvailable: 2
  decisionServices:
    minAvailable: 3
```

## Deployment Commands

### Install Chart
```bash
helm install pa-healthcare ./helm/pa-healthcare \
  --namespace pa-healthcare \
  --create-namespace \
  -f helm/pa-healthcare/values.yaml
```

### Install Production Release
```bash
helm install pa-healthcare ./helm/pa-healthcare \
  --namespace pa-healthcare-prod \
  --create-namespace \
  -f helm/pa-healthcare/values-production.yaml
```

### Upgrade Existing Release
```bash
helm upgrade pa-healthcare ./helm/pa-healthcare \
  -f helm/pa-healthcare/values-production.yaml
```

### Validate Chart
```bash
helm lint ./helm/pa-healthcare
helm template pa-healthcare ./helm/pa-healthcare \
  -f helm/pa-healthcare/values-production.yaml | kubectl apply --dry-run=client -f -
```

## Template Examples

### Agent Deployment Template (agents/intake-agent.yaml)
```yaml
{{- if .Values.agents.intake.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intake-agent
  namespace: {{ .Values.global.namespace }}
  labels:
    app: intake-agent
    version: {{ .Chart.AppVersion }}
spec:
  replicas: {{ .Values.agents.intake.replicas }}
  selector:
    matchLabels:
      app: intake-agent
  template:
    metadata:
      labels:
        app: intake-agent
    spec:
      serviceAccountName: {{ .Values.serviceAccount.name }}
      containers:
      - name: intake-agent
        image: "{{ .Values.global.imageRegistry }}/{{ .Values.agents.intake.image }}"
        imagePullPolicy: {{ .Values.global.imagePullPolicy }}
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: ENVIRONMENT
          value: {{ .Values.global.environment }}
        - name: VAULT_ADDR
          value: {{ .Values.vault.address }}
        resources:
          requests:
            cpu: {{ .Values.agents.intake.resources.requests.cpu }}
            memory: {{ .Values.agents.intake.resources.requests.memory }}
          limits:
            cpu: {{ .Values.agents.intake.resources.limits.cpu }}
            memory: {{ .Values.agents.intake.resources.limits.memory }}
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
{{- end }}
```

### HPA Template (hpa/agent-hpa.yaml)
```yaml
{{- if .Values.agents.intake.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: intake-agent-hpa
  namespace: {{ .Values.global.namespace }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: intake-agent
  minReplicas: {{ .Values.agents.intake.hpa.minReplicas }}
  maxReplicas: {{ .Values.agents.intake.hpa.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.agents.intake.hpa.targetCPUUtilization }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.agents.intake.hpa.targetMemoryUtilization | default 75 }}
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 15
      policies:
      - type: Percent
        value: 50
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
{{- end }}
```

## Helm Hooks for Initialization

Helm hooks enable automated setup during deployment:

```yaml
# templates/vault-init.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: vault-init-{{ .Release.Revision }}
  namespace: {{ .Values.global.namespace }}
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
spec:
  template:
    spec:
      serviceAccountName: {{ .Values.serviceAccount.name }}
      containers:
      - name: vault-init
        image: vault:{{ .Values.vault.version }}
        command:
        - /bin/sh
        - -c
        - |
          vault auth kubernetes
          vault kv get secret/pa-healthcare
      restartPolicy: Never
```

## Best Practices

1. **Use separate values files** for each environment
2. **Version your charts** following semantic versioning
3. **Implement pre-installation hooks** for dependencies
4. **Use initContainers** for setup operations
5. **Test charts with `helm lint` and `helm template`**
6. **Maintain clean separation** of concerns (agents, services, monitoring)
7. **Document all values** with descriptions and defaults
8. **Use labels consistently** for querying and management

## Next Steps

1. Create Helm chart repository
2. Build agent and service container images
3. Configure CI/CD for chart updates
4. Test deployment in staging
5. Implement chart versioning and releases
