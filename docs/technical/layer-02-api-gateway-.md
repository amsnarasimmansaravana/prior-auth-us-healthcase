# Layer 2: API Gateway Layer
## Kong Enterprise - 10 Gateway Types - Healthcare Insurance PA Platform

**Layer Purpose**: API Gateway management, authentication, rate limiting, security, and LLM request routing  
**Services**: 10 services  
**Technology Stack**: Kong Enterprise 3.4, Lua Plugins, Redis  
**Daily Volume**: 3.5M+ API calls/day  
**Performance**: <50ms total overhead

---

## Table of Contents
1. [Layer Overview](#layer-overview)
2. [Service Architecture](#service-architecture)
3. [Technical Implementation](#technical-implementation)
4. [API Specifications](#api-specifications)
5. [Data Flow](#data-flow)
6. [Database Connectivity](#database-connectivity)
7. [Performance & Scaling](#performance--scaling)
8. [Security & Compliance](#security--compliance)
9. [Monitoring & Operations](#monitoring--operations)

---

## Layer Overview

### Purpose
The **API Gateway Layer** serves as the single entry point for all API traffic, providing:
- **Authentication & Authorization**: OAuth2, JWT validation, RBAC
- **Rate Limiting**: Token bucket algorithm with Redis-backed counters
- **LLM Request Routing**: Intelligent routing to GPT-4o, Claude, GPT-3.5
- **Security**: WAF, prompt injection detection, jailbreak prevention
- **Observability**: Request tracing, metrics collection, logging
- **Caching**: Response caching with TTL-based invalidation

Kong Enterprise manages **10 specialized gateway types**, each handling specific concerns while maintaining a unified API surface.

### Architecture Principles
- **Single Entry Point**: All API traffic flows through Kong
- **Zero Trust**: Every request authenticated and authorized
- **Defense in Depth**: Multiple security layers (WAF, firewall, rate limit)
- **Observability First**: Every request traced and metered
- **High Availability**: 5 Kong nodes in active-active configuration

---

## Service Architecture

### Service Inventory (10 Services)


The API Gateway Layer consists of **10 services**:

- **auth-gateway**: Core 2 layer component
- **rate-limit-gateway**: Core 2 layer component
- **llm-gateway**: Core 2 layer component
- **vector-gateway**: Core 2 layer component
- **graph-gateway**: Core 2 layer component
- **cache-gateway**: Core 2 layer component
- **firewall-gateway**: Core 2 layer component
- **observability-gateway**: Core 2 layer component
- **data-gateway**: Core 2 layer component
- **compliance-gateway**: Core 2 layer component

**Deployment**: Azure Kubernetes Service (AKS)  
**Scaling**: Horizontal Pod Autoscaler (HPA)  
**High Availability**: Multi-zone deployment


---

## Technical Implementation

### Deployment Architecture

```yaml
Kubernetes Namespace: api-gateway-layer

Services:
  - auth-gateway:
      replicas: 2-5 (HPA)
      resources:
        requests: { cpu: 200m, memory: 512Mi }
        limits: { cpu: 1000m, memory: 2Gi }
  - rate-limit-gateway:
      replicas: 2-5 (HPA)
      resources:
        requests: { cpu: 200m, memory: 512Mi }
        limits: { cpu: 1000m, memory: 2Gi }
  # ... (10 total services)


Ingress:
  Controller: nginx-ingress
  TLS: Let's Encrypt (cert-manager)
```

### Technology Stack


**Primary Technologies**: See service details above  
**Container Runtime**: containerd 1.7  
**Orchestration**: Kubernetes 1.28  
**Service Mesh**: Istio 1.20 (optional)


---

## API Specifications


### Common API Patterns

**Authentication**: JWT Bearer tokens  
**Rate Limiting**: 100 requests/minute per client  
**Error Responses**: RFC 7807 Problem Details


---

## Data Flow


### Request Flow

1. Request enters Layer 2
2. Service processes request
3. Data persisted/retrieved as needed
4. Response returned to caller


---

## Database Connectivity


### Database Access Patterns

**PostgreSQL**: Transactional data  
**Redis**: Caching and state  
**Connection Pooling**: 50 connections per service


---

## Performance & Scaling

### Auto-Scaling Configuration


```yaml
HorizontalPodAutoscaler:
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: 70%
```


### Performance Metrics


| Service | P50 | P95 | P99 | Throughput |
|---------|-----|-----|-----|------------|
| Primary | 50ms | 120ms | 350ms | 1000 req/s |


---

## Security & Compliance


**Encryption**: TLS 1.3 (transit), AES-256 (rest)  
**Authentication**: OAuth 2.0 + JWT  
**Authorization**: RBAC with OPA policies  
**Compliance**: HIPAA, SOC 2, ISO 27001


---

## Monitoring & Operations

### Observability Stack

**Metrics**: Prometheus + Grafana
```yaml
Dashboards:
  - Layer 2 Overview
    * Request rate per service
    * Error rate (4xx, 5xx)
    * Latency percentiles (P50, P95, P99)
    * Pod CPU/memory usage
```

**Logging**: Azure Log Analytics  
**Tracing**: Jaeger (OpenTelemetry)

### Alerting


```yaml
Alerts:
  - name: HighErrorRate
    condition: error_rate > 5% for 5 minutes
    severity: critical
  - name: SlowResponseTime
    condition: p95_latency > 2s for 10 minutes
    severity: warning
```


---

## Summary

The **API Gateway Layer** processes **3.5M+ API calls/day** with **<50ms total overhead** latency. It provides critical API gateway, security, and routing functionality for the PA platform.

**Key Metrics**:
- **10 services** deployed on AKS
- **99.95%** uptime SLA
- **<50ms total overhead** response times
- **HIPAA compliant** with end-to-end encryption

---

*Generated: June 02, 2026 | Version: 1.0*
