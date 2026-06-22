---
title: Layer 03 Orchestration
status: draft
owner: TODO
type: technical
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Layer 3: Orchestration Layer
## LangGraph + Temporal Workflow Engine - Healthcare Insurance PA Platform

**Layer Purpose**: Multi-agent workflow orchestration, state management, and durable execution  
**Services**: 3 services  
**Technology Stack**: LangGraph 0.2, Temporal.io 1.22, Python 3.11  
**Daily Volume**: 50,000 workflows/day  
**Performance**: <5ms state operations

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
The **Orchestration Layer** coordinates multi-agent workflows using:
- **LangGraph Supervisor Pattern**: Coordinates 11 AI agents in a directed graph
- **Temporal Durable Execution**: Ensures workflow reliability with automatic retries
- **State Management**: Redis for hot state, PostgreSQL for persistence
- **Checkpointing**: Workflow recovery from any point of failure
- **Timeout Management**: 30-minute SLA with automatic escalation
- **Conditional Routing**: Dynamic agent selection based on case complexity

This layer processes **50,000 PA workflows daily**, orchestrating an average of **7 agents per case**.

### Architecture Principles
- **Reliability**: Durable execution with automatic retries
- **Scalability**: Horizontal scaling of workflow workers
- **Visibility**: Complete workflow state visibility
- **Fault Tolerance**: Checkpoint-based recovery
- **Performance**: Sub-5ms state operations with Redis

### AI Gateway Integration
- Entry to orchestration is via **Kong AI Gateway**, not direct client-to-workflow service calls.
- Gateway enforces OAuth2/JWT, mTLS, PHI masking, prompt security, and per-tenant quotas.
- Kong forwards model-bound traffic to **LiteLLM Gateway** for provider/model routing and fallback.
- Correlation IDs and trace headers are propagated to Temporal and LangGraph for end-to-end observability.

---

## Service Architecture

### Service Inventory (3 Services)

#### 1. **workflow-engine-svc** - LangGraph Multi-Agent Orchestrator

**Purpose**: Coordinates 11 AI agents using LangGraph supervisor pattern

**Technology Stack**:
- Language: Python 3.11
- Framework: LangGraph 0.2.15
- API: FastAPI 0.104
- Protocol: gRPC (primary), REST (fallback)

**Core Capabilities**:
- **Supervisor Pattern**: Central supervisor routes requests to specialized agents
- **Conditional Edges**: Dynamic routing based on case complexity
- **Parallel Execution**: Run independent agents concurrently (eligibility + benefits)
- **Error Recovery**: Automatic retry with exponential backoff (3 attempts)
- **Timeout Management**: 30-minute workflow SLA with escalation
- **Human Handoff**: Route to HITL when confidence < 0.85

**Agent Orchestration Graph**:
```python
# LangGraph StateGraph Definition
from langgraph.graph import StateGraph, END

graph = StateGraph(PAWorkflowState)

# Add agent nodes
graph.add_node("supervisor", supervisor_agent)
graph.add_node("intake", intake_agent)
graph.add_node("eligibility", eligibility_agent)
graph.add_node("benefits", benefits_agent)
graph.add_node("clinical", clinical_review_agent)
graph.add_node("policy", policy_agent)
graph.add_node("fraud", fraud_detection_agent)
graph.add_node("decision", decision_agent)

# Conditional routing
graph.add_conditional_edges(
    "supervisor",
    route_to_agents,  # Returns list of agents to invoke
    {
        "intake": "intake",
        "eligibility": "eligibility",
        "benefits": "benefits",
        "clinical": "clinical",
        "policy": "policy",
        "fraud": "fraud",
        "decision": "decision",
        "hitl": "hitl",
        END: END
    }
)

# Workflow checkpointing
checkpointer = PostgresCheckpointer(db_conn)
workflow = graph.compile(checkpointer=checkpointer)
```

**Routing Logic**:
| Case Complexity | Agents Invoked | Estimated Time |
|----------------|----------------|----------------|
| Simple (30%) | Intake → Eligibility → Benefits → Decision | 2-3 minutes |
| Standard (50%) | + Clinical (w/o RAG) + Policy | 5-8 minutes |
| Complex (20%) | + Clinical (with RAG) + Fraud + HITL | 15-30 minutes |

**Performance**:
- Throughput: 50,000 workflows/day (avg 35 workflows/min)
- P50 Latency: 4.2 minutes (full workflow)
- P95 Latency: 12.8 minutes
- P99 Latency: 28.5 minutes (near SLA limit)

**Deployment**:
```yaml
Replicas: 3-8 (HPA based on workflow queue depth)
Resources:
  requests: { cpu: 500m, memory: 1Gi }
  limits: { cpu: 2000m, memory: 4Gi }
Environment:
  LANGGRAPH_CHECKPOINT_DB: postgres://workflow_db
  MAX_CONCURRENT_WORKFLOWS: 100
  AGENT_TIMEOUT_SEC: 300
```

---

#### 2. **temporal-server** - Durable Workflow Execution

**Purpose**: Provides durable, fault-tolerant workflow execution with automatic retries

**Technology Stack**:
- Runtime: Temporal.io 1.22
- Language: Go 1.21 (Temporal server), Python 3.11 (workers)
- Storage: PostgreSQL 15 (workflow history)
- Queue: Redis (task queue)

**Core Capabilities**:
- **Durable Execution**: Workflow state persisted after every activity
- **Automatic Retries**: Exponential backoff (1s, 2s, 4s, 8s, 16s)
- **Long-Running Workflows**: Handle 30-minute workflows with checkpoints
- **Activity Heartbeats**: Detect stuck agent executions
- **Versioning**: Support multiple workflow versions simultaneously
- **Visibility**: Query workflow state via temporal UI/API

**Workflow Definition**:
```python
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class PAReviewWorkflow:
    @workflow.run
    async def run(self, request: PARequest) -> PADecision:
        # Step 1: Data Intake (timeout: 2min)
        intake_result = await workflow.execute_activity(
            invoke_intake_agent,
            request,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=3)
        )
        
        # Step 2: Parallel execution (eligibility + benefits)
        async with workflow.parallel():
            eligibility = workflow.execute_activity(
                invoke_eligibility_agent,
                intake_result,
                start_to_close_timeout=timedelta(seconds=30)
            )
            benefits = workflow.execute_activity(
                invoke_benefits_agent,
                intake_result,
                start_to_close_timeout=timedelta(seconds=30)
            )
        
        # Step 3: Clinical Review (timeout: 10min, may include RAG)
        clinical_result = await workflow.execute_activity(
            invoke_clinical_agent,
            ClinicalInput(intake_result, eligibility, benefits),
            start_to_close_timeout=timedelta(minutes=10),
            heartbeat_timeout=timedelta(seconds=30)
        )
        
        # Step 4: Policy Check
        policy_result = await workflow.execute_activity(
            invoke_policy_agent,
            clinical_result,
            start_to_close_timeout=timedelta(minutes=3)
        )
        
        # Step 5: Fraud Detection (async)
        fraud_result = await workflow.execute_activity(
            invoke_fraud_agent,
            FraudInput(intake_result, clinical_result),
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # Step 6: Decision Synthesis
        decision = await workflow.execute_activity(
            invoke_decision_agent,
            DecisionInput(clinical_result, policy_result, fraud_result),
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # Step 7: HITL routing if low confidence
        if decision.confidence < 0.85:
            decision = await workflow.execute_activity(
                route_to_hitl,
                decision,
                start_to_close_timeout=timedelta(hours=4)  # Human review SLA
            )
        
        return decision
```

**Activity Retry Configuration**:
```python
RetryPolicy(
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
    maximum_attempts=3,
    non_retryable_error_types=["InvalidInputError", "AuthorizationError"]
)
```

**Performance**:
- Workers: 20 Python workers (4 per pod × 5 pods)
- Throughput: 50,000 workflows/day
- Workflow History: 90-day retention in PostgreSQL
- Task Queue Depth: Avg 120, Max 500 (triggers HPA)

**Deployment**:
```yaml
Temporal Server:
  replicas: 3 (HA cluster)
  resources:
    requests: { cpu: 1000m, memory: 2Gi }
    limits: { cpu: 4000m, memory: 8Gi }

Temporal Workers:
  replicas: 5-15 (HPA based on task queue depth)
  resources:
    requests: { cpu: 500m, memory: 1Gi }
    limits: { cpu: 2000m, memory: 4Gi }
```

---

#### 3. **state-manager-svc** - Redis-Backed State Management

**Purpose**: High-performance state storage for workflow context and agent memory

**Technology Stack**:
- Language: Python 3.11
- Framework: FastAPI 0.104
- Cache: Redis 7.0 (cluster mode, 3 shards)
- Persistence: PostgreSQL 15 (state snapshots)

**Core Capabilities**:
- **Hot State Storage**: Redis for active workflows (<5ms access)
- **TTL Management**: 6-hour TTL (workflow timeout + buffer)
- **State Snapshots**: Periodic snapshots to PostgreSQL
- **Atomic Operations**: MULTI/EXEC for state updates
- **Pub/Sub**: State change notifications for monitoring
- **Recovery**: Restore state from PostgreSQL on workflow resume

**State Schema**:
```python
from pydantic import BaseModel
from typing import Dict, List, Optional

class WorkflowState(BaseModel):
    workflow_id: str
    request_id: str
    status: str  # "running", "completed", "failed", "paused"
    current_agent: str
    completed_agents: List[str]
    agent_outputs: Dict[str, Any]  # Agent name -> output
    context: Dict[str, Any]  # Shared context across agents
    confidence_scores: Dict[str, float]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    
    # Working memory (agent scratchpad)
    working_memory: Dict[str, Any]
    
    # Episodic memory (conversation history)
    conversation_history: List[Dict[str, str]]
    
    # Checkpoints for recovery
    checkpoints: List[Dict[str, Any]]
```

**API Endpoints**:
```python
# State Operations
POST   /state/workflows                    # Create workflow state
GET    /state/workflows/{workflow_id}      # Get current state
PUT    /state/workflows/{workflow_id}      # Update state
DELETE /state/workflows/{workflow_id}      # Delete state

# Agent State
GET    /state/workflows/{id}/agents/{agent}      # Get agent output
PUT    /state/workflows/{id}/agents/{agent}      # Update agent output

# Checkpoints
POST   /state/workflows/{id}/checkpoints         # Create checkpoint
GET    /state/workflows/{id}/checkpoints/latest  # Get latest checkpoint
```

**Redis Data Structures**:
```redis
# Workflow state (Hash)
HSET workflow:{workflow_id} status "running"
HSET workflow:{workflow_id} current_agent "clinical_agent"
HSET workflow:{workflow_id} completed_agents '["intake", "eligibility"]'
EXPIRE workflow:{workflow_id} 21600  # 6 hours

# Agent outputs (Hash)
HSET workflow:{workflow_id}:agents intake_agent '{...json...}'
HSET workflow:{workflow_id}:agents eligibility_agent '{...json...}'

# Working memory (String with JSON)
SET workflow:{workflow_id}:memory '{...json...}' EX 21600

# State change pub/sub
PUBLISH workflow:events '{"workflow_id": "...", "event": "agent_completed"}'
```

**Performance**:
- Throughput: 500M operations/day (10K ops/sec)
- P50 Latency: 2.1ms
- P95 Latency: 4.8ms
- P99 Latency: 12.5ms
- Cache Hit Rate: 98.5% (Redis)
- State Size: Avg 45KB per workflow

**Deployment**:
```yaml
State Manager Service:
  replicas: 3-6 (HPA on request rate)
  resources:
    requests: { cpu: 300m, memory: 512Mi }
    limits: { cpu: 1000m, memory: 2Gi }

Redis Cluster:
  shards: 3
  replicas_per_shard: 2 (primary + replica)
  memory_per_shard: 8GB
  eviction_policy: allkeys-lru
  persistence: RDB snapshots every 5 minutes
```

---

**Deployment**: Azure Kubernetes Service (AKS)  
**Scaling**: Horizontal Pod Autoscaler (HPA)  
**High Availability**: Multi-zone deployment (3 availability zones)

---

## Technical Implementation

### Deployment Architecture

```yaml
Kubernetes Namespace: orchestration-layer

Services:
  - workflow-engine-svc:
      replicas: 3-8 (HPA on workflow queue depth)
      resources:
        requests: { cpu: 500m, memory: 1Gi }
        limits: { cpu: 2000m, memory: 4Gi }
      ports:
        - name: grpc
          containerPort: 50051
        - name: http
          containerPort: 8080
      env:
        - name: LANGGRAPH_CHECKPOINT_DB
          value: postgres://workflow_db
        - name: MAX_CONCURRENT_WORKFLOWS
          value: "100"
  
  - temporal-server:
      replicas: 3 (HA cluster)
      resources:
        requests: { cpu: 1000m, memory: 2Gi }
        limits: { cpu: 4000m, memory: 8Gi }
      ports:
        - name: frontend
          containerPort: 7233
        - name: ui
          containerPort: 8088
  
  - temporal-workers:
      replicas: 5-15 (HPA on task queue depth)
      resources:
        requests: { cpu: 500m, memory: 1Gi }
        limits: { cpu: 2000m, memory: 4Gi }
  
  - state-manager-svc:
      replicas: 3-6 (HPA on request rate)
      resources:
        requests: { cpu: 300m, memory: 512Mi }
        limits: { cpu: 1000m, memory: 2Gi }
      ports:
        - name: http
          containerPort: 8000

ConfigMaps:
  - langgraph-config:
      checkpoint_interval: 30s
      max_agent_retries: 3
      agent_timeout: 300s
  
  - temporal-config:
      max_workflow_duration: 1800s  # 30 minutes
      activity_heartbeat_timeout: 30s
      retention_period: 90d

Ingress:
  Controller: nginx-ingress
  TLS: Let's Encrypt (cert-manager)
  Rules:
    - host: workflow.pa-platform.internal
      path: /
      service: workflow-engine-svc:8080
    - host: temporal-ui.pa-platform.internal
      path: /
      service: temporal-server:8088
```

### Technology Stack

**Workflow Orchestration**:
- **LangGraph 0.2.15**: Multi-agent graph orchestration
- **Temporal.io 1.22**: Durable workflow execution
- **Python 3.11**: Primary language for workers
- **FastAPI 0.104**: REST API framework
- **gRPC 1.59**: High-performance RPC

**State Management**:
- **Redis 7.0**: Hot state cache (cluster mode, 3 shards)
- **PostgreSQL 15**: Workflow history & checkpoints
- **Pydantic v2**: Data validation

**Observability**:
- **OpenTelemetry**: Distributed tracing
- **Prometheus**: Metrics collection
- **Grafana**: Dashboards

**Container Runtime**: containerd 1.7  
**Orchestration**: Kubernetes 1.28  
**Service Mesh**: Istio 1.20 (for mTLS between agents)


---

## API Specifications


### Common API Patterns

**Authentication**: JWT Bearer tokens  
**Rate Limiting**: 100 requests/minute per client  
**Error Responses**: RFC 7807 Problem Details


---

## Data Flow


### Request Flow

1. Request enters Layer 3
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
  - Layer 3 Overview
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

The **Orchestration Layer** processes **50,000 workflows/day** with **<5ms state operations** latency. It provides critical workflow orchestration and state management functionality for the PA platform.

**Key Metrics**:
- **3 services** deployed on AKS
- **99.95%** uptime SLA
- **<5ms state operations** response times
- **HIPAA compliant** with end-to-end encryption

---

*Generated: June 02, 2026 | Version: 1.0*
