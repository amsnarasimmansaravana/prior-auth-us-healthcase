---
title: HPA Deployment Strategy for PA Healthcare Platform
status: draft
owner: Platform Engineering
type: both
version: 1.0.0
tags:
  - hpa
  - kubernetes
  - autoscaling
  - deployment
related:
  - infrastructure/helm/Chart.yaml
  - infrastructure/terraform/aks-cluster.tf
  - infrastructure/vault/vault-setup.sh
last_updated: 2026-06-22
---

# HPA Deployment Strategy for PA Healthcare Platform

## Overview

This guide outlines the Horizontal Pod Autoscaler (HPA) deployment strategy for the PA Healthcare agentic AI platform, enabling automatic scaling based on workload demands while maintaining system stability and cost efficiency.

## Architecture Components

### 1. HPA Configuration Tiers

#### Tier 1: Agent Services (Base Scaling)
- **Min Replicas**: 2
- **Max Replicas**: 10
- **Target CPU**: 70%
- **Target Memory**: 75%
- **Scale-Up Window**: 30 seconds
- **Scale-Down Window**: 300 seconds

**Services**:
- Intake Agent
- Eligibility Agent
- Benefits Agent
- Clinical Agent
- Policy Agent
- Fraud Detection Agent

#### Tier 2: Decision & Processing Services (Aggressive Scaling)
- **Min Replicas**: 3
- **Max Replicas**: 20
- **Target CPU**: 60%
- **Target Memory**: 70%
- **Scale-Up Window**: 15 seconds
- **Scale-Down Window**: 180 seconds

**Services**:
- Decision Agent
- Appeals Agent
- Orchestration Engine

#### Tier 3: Data & Support Services (Conservative Scaling)
- **Min Replicas**: 2
- **Max Replicas**: 8
- **Target CPU**: 80%
- **Target Memory**: 80%
- **Scale-Up Window**: 60 seconds
- **Scale-Down Window**: 600 seconds

**Services**:
- Notification Service
- Audit Service
- Member Service
- Provider Service
- Claims Service

### 2. Scaling Metrics & Thresholds

#### CPU-Based Scaling
```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      type: Utilization
      averageUtilization: 70
```

#### Memory-Based Scaling
```yaml
metrics:
- type: Resource
  resource:
    name: memory
    target:
      type: Utilization
      averageUtilization: 75
```

#### Custom Metrics (Prometheus-based)
```yaml
metrics:
- type: Pods
  pods:
    metric:
      name: http_requests_per_second
    target:
      type: AverageValue
      averageValue: 1000
```

### 3. Behavior Policies

#### Aggressive Scale-Up
```yaml
behavior:
  scaleUp:
    stabilizationWindowSeconds: 15
    policies:
    - type: Percent
      value: 50
      periodSeconds: 15
    - type: Pods
      value: 2
      periodSeconds: 15
    selectPolicy: Max
```

#### Conservative Scale-Down
```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300
    policies:
    - type: Percent
      value: 10
      periodSeconds: 60
    selectPolicy: Min
```

## Deployment Strategy

### Phase 1: Initial Rollout
1. Deploy services with HPA at min replicas
2. Monitor for 7 days
3. Adjust thresholds based on metrics
4. Validate scaling behavior under load tests

### Phase 2: Load Testing
1. Execute gradual load increase tests
2. Verify scale-up/scale-down timing
3. Test burst handling scenarios
4. Measure response times during scaling

### Phase 3: Production Deployment
1. Enable HPA on staging environment first
2. Run 2-week validation period
3. Deploy to production with monitoring
4. Maintain manual scaling override capability

## Request/Limit Configuration

### Recommended Resources per Service Tier

#### Tier 1: Agent Services
```yaml
requests:
  cpu: 500m
  memory: 512Mi
limits:
  cpu: 1000m
  memory: 1Gi
```

#### Tier 2: Decision Services
```yaml
requests:
  cpu: 1000m
  memory: 1Gi
limits:
  cpu: 2000m
  memory: 2Gi
```

#### Tier 3: Support Services
```yaml
requests:
  cpu: 250m
  memory: 256Mi
limits:
  cpu: 500m
  memory: 512Mi
```

## Monitoring & Alerts

### Key Metrics to Monitor
- Current/Desired replica count
- HPA decision latency
- Pod startup time
- CPU/Memory utilization per pod
- Scaling event frequency
- Failed scaling attempts

### Alert Rules
```yaml
alerts:
  - name: HPAMaxedOut
    condition: desired_replicas == max_replicas
    threshold: 5 minutes
    severity: warning
    
  - name: HPAScalingFailures
    condition: scaling_failures > 0
    threshold: immediate
    severity: critical
    
  - name: HighResourceUtilization
    condition: cpu_utilization > 85% OR memory_utilization > 85%
    threshold: 2 minutes
    severity: warning
```

## Cost Optimization

### Node Pool Strategy
- **On-Demand Nodes**: For persistent workloads (30% of capacity)
- **Spot Nodes**: For scalable workloads (70% of capacity)
- **Reserved Instances**: For baseline load (predictable demand)

### Scaling Cost Impact
- Expected cost increase: 15-20% during peak hours
- Cost savings: 40-50% during off-peak hours
- Average cost optimization: 25% vs. static sizing

## Troubleshooting Guide

### Issue: HPA Not Scaling Up
**Diagnosis**:
1. Check Metrics Server: `kubectl get deployment metrics-server -n kube-system`
2. Verify resource requests/limits are set
3. Check pod metrics: `kubectl top pods -n production`

**Resolution**:
- Install/restart Metrics Server
- Ensure requests/limits properly configured
- Check HPA status: `kubectl describe hpa service-name`

### Issue: Rapid Scale Up/Down (Flapping)
**Cause**: Stabilization window too short
**Solution**: Increase `stabilizationWindowSeconds` to 60-300

### Issue: Pods Pending (Can't Scale)
**Cause**: Node pool capacity exhausted
**Solution**: Verify Cluster Autoscaler is enabled and configured

## Best Practices

1. **Always set resource requests/limits** - HPA requires these for accurate scaling
2. **Test scaling behavior** - Use load testing before production
3. **Monitor multiple metrics** - CPU + Memory + Custom metrics
4. **Implement graceful shutdown** - Ensure services handle SIGTERM
5. **Use pod disruption budgets** - Protect against unexpected terminations
6. **Regular capacity planning** - Review scaling patterns monthly
7. **Document scaling decisions** - Maintain runbooks for adjustments

## Integration with Helm

HPA resources are defined in Helm charts under `templates/hpa/`:
- `agent-hpa.yaml` - Agent services HPA
- `decision-hpa.yaml` - Decision services HPA
- `support-hpa.yaml` - Support services HPA

See `infrastructure/helm/` for chart structure and deployment.

## Integration with Terraform

Kubernetes autoscaler and metrics server are deployed via Terraform:
- `aks-addons.tf` - Container Insights, Autoscaler
- `aks-cluster.tf` - Cluster configuration
- `monitoring.tf` - Prometheus/Grafana setup

See `infrastructure/terraform/` for IaC configurations.

## Next Steps

1. Review Helm chart HPA configurations
2. Deploy Terraform infrastructure
3. Configure HashiCorp Vault for secrets
4. Execute load testing strategy
5. Monitor and optimize thresholds
