# Complete Microservice Architecture
## Healthcare Insurance Multi-Agent AI Platform - End-to-End Implementation Guide

**Document Version**: 1.0  
**Last Updated**: June 2, 2026  
**Owner**: Platform Architecture Team  
**Status**: Production

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Microservices Inventory](#microservices-inventory)
4. [Database Architecture](#database-architecture)
5. [End-to-End Request Flow](#end-to-end-request-flow)
6. [Service Connectivity Matrix](#service-connectivity-matrix)
7. [Database Connectivity Patterns](#database-connectivity-patterns)
8. [Business + Technical Workflow](#business--technical-workflow)
9. [Integration Patterns](#integration-patterns)
10. [Performance & Scaling](#performance--scaling)

---

## Executive Summary

This document provides a **complete implementation guide** for the Healthcare Insurance Prior Authorization (PA) platform, covering:

- **55+ microservices** across 10 architectural layers
- **11 AI agents** with LLM orchestration (LangGraph)
- **6 database systems** (PostgreSQL, Redis, Milvus, Neo4j, Elasticsearch, Blob Storage)
- **50-step end-to-end workflow** from submission to decision
- **Multi-database interaction** patterns and data flows
- **Business + technical architecture** combined view

### Platform Metrics
- **Capacity**: 50,000 PA requests/day
- **Turnaround**: 15-minute average (30-min SLA)
- **Accuracy**: 96% on automated decisions
- **Automation**: 72% (28% human review)
- **Availability**: 99.95% uptime
- **ROI**: $667M annually

---

## Architecture Overview

### 10-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAYER 1: CHANNEL LAYER                            │
│  Web Portal | Mobile App | Provider Portal | EDI Gateway | Fax OCR  │
│  (5 services)                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 LAYER 2: API GATEWAY LAYER (Kong)                    │
│  Auth | Rate Limit | LLM | Vector | Graph | Cache | Firewall | ...  │
│  (10 gateway types)                                                  │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│          LAYER 3: ORCHESTRATION LAYER (LangGraph + Temporal)         │
│  Workflow Engine | State Manager | Temporal Server                  │
│  (3 services)                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│               LAYER 4: AGENT FABRIC LAYER (AI)                       │
│  Intake | Eligibility | Benefits | Clinical | Policy | Fraud | ...  │
│  (11 AI agent services)                                              │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│              LAYER 5: GOVERNANCE LAYER                               │
│  Agent Registry | Prompt Mgmt | Safety Eval | Compliance Monitor    │
│  (4 services)                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   LAYER 6: MCP LAYER                                 │
│  MCP Registry | Tool Executor                                        │
│  (2 services)                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  LAYER 7: MEMORY LAYER                               │
│  Working Memory | Episodic | Semantic | Procedural                  │
│  (4 services)                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   LAYER 8: RAG LAYER                                 │
│  Vector Search | Hybrid Search | Graph RAG                          │
│  (3 services)                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│              LAYER 9: DATA SERVICES LAYER                            │
│  Member | Provider | Policy | Claims | Benefits | Network | ...     │
│  (8 microservices)                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                 LAYER 10: HITL LAYER                                 │
│  HITL Routing | Review Queue | Approval Workflow                    │
│  (3 services)                                                        │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     DATABASE LAYER                                   │
│  PostgreSQL | Redis | Milvus | Neo4j | Elasticsearch | Blob Storage │
│  (6 database systems)                                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Microservices Inventory

### Complete Service Catalog (55+ Services)

#### **LAYER 1: Channel Services (5 services)**

| Service Name | Purpose | Technology Stack | Port | Endpoints |
|--------------|---------|------------------|------|-----------|
| `web-portal-svc` | Member/provider web UI | React 18, Node.js 20, TypeScript | 3000 | `/`, `/submit-pa`, `/track-status` |
| `mobile-api-svc` | Mobile app backend API | FastAPI, Python 3.11, Pydantic | 8001 | `/api/mobile/v1/*` |
| `edi-gateway-svc` | X12 EDI processing (278/837) | Go 1.21, HL7 FHIR | 8002 | `/edi/inbound`, `/edi/outbound` |
| `fax-ocr-svc` | Fax intake with OCR | Azure Form Recognizer, Python | 8003 | `/fax/receive`, `/fax/process` |
| `voice-ivr-svc` | Phone IVR integration | Azure Speech SDK, Node.js | 8004 | `/ivr/callback` |

**Deployment**: Azure Kubernetes Service (AKS)  
**Scaling**: 3-10 replicas per service  
**Load Balancer**: Azure Application Gateway (Layer 7)

---

#### **LAYER 2: API Gateway Services (Kong Enterprise - 10 Gateway Types)**

| Gateway Type | Purpose | Implementation | Latency |
|--------------|---------|----------------|---------|
| `auth-gateway` | OAuth2, JWT validation, SSO | Kong plugin (Lua) + Keycloak | 5ms |
| `rate-limit-gateway` | Token bucket rate limiting | Kong + Redis (distributed counters) | 2ms |
| `llm-gateway` | LLM request routing, caching, load balancing | LiteLLM proxy | 10ms |
| `vector-gateway` | Vector search routing, request batching | Custom Python service | 8ms |
| `graph-gateway` | Neo4j Cypher query routing | Custom Go service | 5ms |
| `cache-gateway` | Response caching, cache invalidation | Kong + Redis | 3ms |
| `firewall-gateway` | LLM security (prompt injection, jailbreak) | Kong plugin + Lakera AI | 15ms |
| `observability-gateway` | OpenTelemetry traces, metrics | Kong + Jaeger + Prometheus | 5ms |
| `data-gateway` | Database access control, query validation | OPA policies, Kong plugin | 8ms |
| `compliance-gateway` | Audit logging, HIPAA compliance | Custom Python, Kafka producer | 10ms |

**Base URL**: `https://api.pahealthcare.com`  
**Kong Configuration**: Declarative (YAML), GitOps managed  
**High Availability**: 5 Kong nodes (active-active)

---

#### **LAYER 3: Orchestration Services (3 services)**

| Service Name | Purpose | Technology | Database | Metrics |
|--------------|---------|------------|----------|---------|
| `workflow-engine-svc` | LangGraph multi-agent orchestration | LangGraph 0.2, Python 3.11 | Redis (state), PostgreSQL (history) | 50K workflows/day |
| `temporal-server` | Workflow durability, retries, timeouts | Temporal.io 1.22 | PostgreSQL (persistence) | 99.99% uptime |
| `state-manager-svc` | Workflow state persistence | FastAPI, Redis, PostgreSQL | Redis (hot), PostgreSQL (cold) | <5ms read/write |

**Workflow Patterns**: Supervisor, Map-Reduce, Human-in-the-Loop  
**Retry Policy**: Exponential backoff (1s → 60s, max 5 attempts)  
**Timeout**: 30 minutes per PA workflow

---

#### **LAYER 4: Agent Services (11 AI Agents)**

| Service Name | Agent Purpose | LLM Model | Temperature | Max Tokens | Avg Latency |
|--------------|---------------|-----------|-------------|------------|-------------|
| `intake-agent-svc` | Document classification, OCR, entity extraction | GPT-4o Vision (gpt-4o-2024-05-13) | 0.0 | 2,000 | 7.4s |
| `eligibility-agent-svc` | Member enrollment verification, COB detection | GPT-3.5 Turbo (gpt-3.5-turbo-0125) | 0.0 | 500 | 1.2s |
| `benefits-agent-svc` | Coverage determination, cost-sharing calculation | GPT-4o (gpt-4o-2024-05-13) | 0.1 | 1,500 | 3.1s |
| `clinical-agent-svc` | Medical necessity review with RAG pipeline | GPT-4o (gpt-4o-2024-05-13) | 0.2 | 8,000 | 8.3s |
| `policy-agent-svc` | Policy retrieval, rules engine, compliance | Claude 3.5 Sonnet (claude-3-5-sonnet) | 0.1 | 4,000 | 4.2s |
| `fraud-agent-svc` | Anomaly detection, graph analytics | GPT-4o + scikit-learn | 0.0 | 1,000 | 2.8s |
| `decision-agent-svc` | Final decision aggregation, confidence scoring | GPT-4o (gpt-4o-2024-05-13) | 0.2 | 2,000 | 2.5s |
| `appeals-agent-svc` | Appeals processing, IRO coordination | GPT-4o (gpt-4o-2024-05-13) | 0.1 | 3,000 | 4.1s |
| `notification-agent-svc` | Multi-channel communications (email, SMS, portal) | GPT-3.5 Turbo | 0.3 | 1,000 | 1.5s |
| `audit-agent-svc` | Compliance logging, blockchain audit trail | GPT-4o | 0.0 | 1,500 | 2.2s |
| `com-agent-svc` | Coordination of benefits, MSP rules | GPT-4o | 0.1 | 2,000 | 3.5s |

**Total Agent Metrics**:
- **Daily Executions**: 385,000 agent invocations (7 agents × 55,000 cases)
- **Success Rate**: 96.2%
- **Total Tokens/Day**: ~2.6 billion tokens
- **Daily LLM Cost**: ~$52,000
- **Average Agent Chain**: 7 agents per PA request

---

#### **LAYER 5: Governance Services (4 services)**

| Service Name | Purpose | Technology | Storage |
|--------------|---------|------------|---------|
| `agent-registry-svc` | Agent metadata, versioning, capabilities | FastAPI, PostgreSQL | PostgreSQL (agent_db.agent_registry) |
| `prompt-mgmt-svc` | Prompt templates, A/B testing, versioning | LangSmith, Python | PostgreSQL + S3 (prompt versions) |
| `safety-eval-svc` | Hallucination detection, toxicity check | Guardrails AI, HuggingFace | Redis (cache), PostgreSQL (results) |
| `compliance-monitor-svc` | ISO 42001 AIMS, agent certification | Custom Python, Prometheus | PostgreSQL + Elasticsearch (audit logs) |

---

#### **LAYER 6: MCP Services (2 services)**

| Service Name | Purpose | Technology | Protocols |
|--------------|---------|------------|-----------|
| `mcp-registry-svc` | Tool discovery, catalog, governance | FastAPI, PostgreSQL | MCP Protocol, gRPC |
| `tool-executor-svc` | Tool invocation runtime, sandboxing | MCP SDK (Python), Docker | MCP Protocol, REST |

**MCP Tools**: 45+ tools (database queries, API calls, calculations, validations)

---

#### **LAYER 7: Memory Services (4 services)**

| Service Name | Memory Type | Purpose | Technology | TTL |
|--------------|-------------|---------|------------|-----|
| `working-memory-svc` | Short-term | Agent scratchpad, workflow context | Redis (in-memory) | 5 minutes |
| `episodic-memory-svc` | Conversational | Case history, conversation threads | PostgreSQL (agent_db) | 90 days |
| `semantic-memory-svc` | Knowledge | Embeddings, similar case retrieval | Milvus (vector DB) | Permanent |
| `procedural-memory-svc` | Workflows | Workflow templates, best practices | PostgreSQL (agent_db) | Permanent |

---

#### **LAYER 8: RAG Services (3 services)**

| Service Name | Retrieval Method | Technology | Latency | Top-K |
|--------------|------------------|------------|---------|-------|
| `vector-search-svc` | Dense retrieval (embeddings) | Milvus 2.3, HNSW index | 45ms | 20 |
| `hybrid-search-svc` | Vector + BM25 (lexical + semantic) | Elasticsearch 8.x | 85ms | 20 |
| `graph-rag-svc` | Knowledge graph traversal | Neo4j 5.x, Cypher | 120ms | 10 |

**Retrieval Fusion**: Reciprocal Rank Fusion (RRF) with k=60

---

#### **LAYER 9: Data Services (8 Microservices)**

| Service Name | Purpose | API Type | Database | Daily Queries | Latency (P95) |
|--------------|---------|----------|----------|---------------|---------------|
| `member-service` | Member enrollment, demographics | gRPC, REST | PostgreSQL (member_db) | 2M+ | 25ms |
| `provider-service` | NPI registry, credentialing, network status | gRPC, REST | PostgreSQL (provider_db) | 500K+ | 30ms |
| `policy-service` | Plan policies, coverage rules | REST | PostgreSQL (policy_db) | 100K+ | 50ms |
| `claims-service` | Claims history, payment data | REST, Batch | PostgreSQL (claims_db) | 400K+ | 100ms |
| `benefits-config-service` | Plan design, cost-sharing, limits | gRPC, REST | PostgreSQL (policy_db) | 300K+ | 40ms |
| `network-service` | Provider networks, tier management | REST | PostgreSQL (provider_db) | 250K+ | 35ms |
| `formulary-service` | Drug coverage, tier placement, PA rules | REST | PostgreSQL (policy_db) | 80K+ | 45ms |
| `clinical-content-service` | MCG/InterQual guidelines, RAG corpus | REST | Elasticsearch, PostgreSQL | 50K+ | 120ms |

**Total Data Service Metrics**:
- **Daily API Calls**: 3.5M+
- **Cache Hit Rate**: 75% average (Redis)
- **Database Connection Pool**: 50 connections per service
- **API Gateway**: All traffic through Kong

---

#### **LAYER 10: HITL Services (3 services)**

| Service Name | Purpose | Technology | SLA |
|--------------|---------|------------|-----|
| `hitl-routing-svc` | Risk-based routing to human reviewers | Drools rules engine, Python | <100ms routing decision |
| `review-queue-svc` | Human review UI/API, task management | React, FastAPI, PostgreSQL | 99.9% availability |
| `approval-workflow-svc` | Multi-level approvals, escalations | Temporal workflows | <4 hour turnaround |

**Human Review Rate**: 28% of cases (14,000/day)

---

#### **Infrastructure Services (6 services)**

| Service Name | Purpose | Technology | Endpoints |
|--------------|---------|------------|-----------|
| `prometheus` | Metrics collection, time-series DB | Prometheus 2.45 | :9090 |
| `grafana` | Dashboards, visualization, alerting | Grafana 10.0 | :3001 |
| `jaeger` | Distributed tracing, span analysis | Jaeger 1.47 | :16686 |
| `kafka` | Event streaming, async messaging | Apache Kafka 3.5 (6 brokers) | :9092 |
| `keycloak` | Identity provider, SSO, RBAC | Keycloak 22 | :8080 |
| `vault` | Secrets management, encryption keys | HashiCorp Vault 1.14 | :8200 |

---

## Database Architecture

### Multi-Database Ecosystem (6 Systems)

#### **Database 1: PostgreSQL 15 (Primary Transactional DB)**

**Purpose**: Relational data, ACID transactions, audit trails  
**Size**: 6 TB (production)  
**Configuration**:
```yaml
Host: pa-postgres-primary.postgres.database.azure.com
Port: 5432
Version: PostgreSQL 15.3
High Availability: Zone-redundant (East US 2)
Replication: 2 read replicas (async streaming)
Backup: Daily full + hourly incremental (35-day retention)
Connection Pool: PgBouncer (500 max connections)
Performance: 5,000 IOPS, 500 GB/s throughput
```

**Databases & Schema**:

##### **Database: member_db (1.2 TB)**
```sql
-- Table: members (5M rows)
CREATE TABLE members (
    member_id VARCHAR(20) PRIMARY KEY,
    ssn_encrypted BYTEA NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    dob DATE NOT NULL,
    gender CHAR(1),
    plan_id VARCHAR(20) REFERENCES plans(plan_id),
    enrollment_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_members_plan ON members(plan_id);
CREATE INDEX idx_members_dob ON members(dob);

-- Table: eligibility_history (50M rows)
CREATE TABLE eligibility_history (
    id BIGSERIAL PRIMARY KEY,
    member_id VARCHAR(20) REFERENCES members(member_id),
    plan_id VARCHAR(20),
    start_date DATE NOT NULL,
    end_date DATE,
    coverage_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_eligibility_member ON eligibility_history(member_id, start_date);

-- Table: dependents (8M rows)
CREATE TABLE dependents (
    dependent_id VARCHAR(20) PRIMARY KEY,
    subscriber_member_id VARCHAR(20) REFERENCES members(member_id),
    relationship VARCHAR(20),
    dob DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

##### **Database: provider_db (800 GB)**
```sql
-- Table: providers (1.2M rows)
CREATE TABLE providers (
    provider_id BIGSERIAL PRIMARY KEY,
    npi VARCHAR(10) UNIQUE NOT NULL,
    tax_id VARCHAR(20),
    name VARCHAR(200),
    specialty VARCHAR(100),
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state CHAR(2),
    zip VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_providers_npi ON providers(npi);
CREATE INDEX idx_providers_specialty ON providers(specialty);

-- Table: credentials (500K rows)
CREATE TABLE credentials (
    credential_id BIGSERIAL PRIMARY KEY,
    provider_npi VARCHAR(10) REFERENCES providers(npi),
    license_number VARCHAR(50),
    license_state CHAR(2),
    issue_date DATE,
    expiration_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: network_contracts (8,500 rows)
CREATE TABLE network_contracts (
    contract_id BIGSERIAL PRIMARY KEY,
    plan_id VARCHAR(20),
    provider_npi VARCHAR(10) REFERENCES providers(npi),
    network_tier VARCHAR(20), -- Tier 1, Tier 2, Out-of-Network
    effective_date DATE,
    termination_date DATE,
    reimbursement_rate DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_contracts_plan_provider ON network_contracts(plan_id, provider_npi);
```

##### **Database: policy_db (500 GB)**
```sql
-- Table: plan_policies (1,200 rows)
CREATE TABLE plan_policies (
    policy_id BIGSERIAL PRIMARY KEY,
    plan_id VARCHAR(20) UNIQUE NOT NULL,
    plan_name VARCHAR(200),
    plan_type VARCHAR(50), -- HMO, PPO, EPO, POS
    coverage_year INT,
    policy_document_url TEXT,
    effective_date DATE,
    termination_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: benefits_config (15K rows)
CREATE TABLE benefits_config (
    benefit_id BIGSERIAL PRIMARY KEY,
    plan_id VARCHAR(20) REFERENCES plan_policies(plan_id),
    service_category VARCHAR(100), -- MRI, CT, Surgery, etc.
    copay DECIMAL(10,2),
    coinsurance DECIMAL(5,4), -- 0.20 = 20%
    deductible DECIMAL(10,2),
    oop_max DECIMAL(10,2), -- Out-of-pocket maximum
    requires_pa BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_benefits_plan_service ON benefits_config(plan_id, service_category);

-- Table: formulary (12K rows)
CREATE TABLE formulary (
    formulary_id BIGSERIAL PRIMARY KEY,
    plan_id VARCHAR(20) REFERENCES plan_policies(plan_id),
    drug_ndc VARCHAR(11),
    drug_name VARCHAR(200),
    tier INT, -- 1-5
    requires_pa BOOLEAN,
    quantity_limit INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

##### **Database: claims_db (2.5 TB)**
```sql
-- Table: claims (150M rows, partitioned by service_date year)
CREATE TABLE claims (
    claim_id VARCHAR(30) PRIMARY KEY,
    member_id VARCHAR(20),
    provider_npi VARCHAR(10),
    service_date DATE NOT NULL,
    diagnosis_codes TEXT[], -- Array of ICD-10 codes
    procedure_codes TEXT[], -- Array of CPT codes
    billed_amount DECIMAL(12,2),
    allowed_amount DECIMAL(12,2),
    paid_amount DECIMAL(12,2),
    claim_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (service_date);

CREATE TABLE claims_2026 PARTITION OF claims
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

CREATE INDEX idx_claims_member ON claims(member_id);
CREATE INDEX idx_claims_provider ON claims(provider_npi);
CREATE INDEX idx_claims_service_date ON claims(service_date);

-- Table: claim_lines (800M rows)
CREATE TABLE claim_lines (
    line_id BIGSERIAL PRIMARY KEY,
    claim_id VARCHAR(30) REFERENCES claims(claim_id),
    line_number INT,
    procedure_code VARCHAR(10),
    units INT,
    billed_amount DECIMAL(12,2),
    allowed_amount DECIMAL(12,2)
);
```

##### **Database: workflow_db (400 GB)**
```sql
-- Table: pa_cases (20M rows)
CREATE TABLE pa_cases (
    case_id VARCHAR(30) PRIMARY KEY,
    member_id VARCHAR(20),
    provider_npi VARCHAR(10),
    submission_date TIMESTAMP DEFAULT NOW(),
    decision_date TIMESTAMP,
    status VARCHAR(20), -- pending, in_progress, completed, denied
    decision VARCHAR(20), -- APPROVED, DENIED, MODIFIED
    auth_number VARCHAR(30),
    extracted_data JSONB,
    clinical_decision JSONB,
    final_rationale TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_cases_member ON pa_cases(member_id);
CREATE INDEX idx_cases_status ON pa_cases(status);
CREATE INDEX idx_cases_submission_date ON pa_cases(submission_date);

-- Table: case_events (200M rows) - Audit trail
CREATE TABLE case_events (
    event_id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(30) REFERENCES pa_cases(case_id),
    event_type VARCHAR(50), -- agent_executed, status_changed, etc.
    event_data JSONB,
    user_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_events_case ON case_events(case_id);
CREATE INDEX idx_events_timestamp ON case_events(timestamp);
```

##### **Database: agent_db (100 GB)**
```sql
-- Table: agent_registry (11 rows)
CREATE TABLE agent_registry (
    agent_id VARCHAR(50) PRIMARY KEY,
    agent_name VARCHAR(100),
    agent_version VARCHAR(20),
    llm_model VARCHAR(100),
    capabilities JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: prompt_templates (500 rows)
CREATE TABLE prompt_templates (
    template_id BIGSERIAL PRIMARY KEY,
    agent_id VARCHAR(50) REFERENCES agent_registry(agent_id),
    template_name VARCHAR(100),
    template_version INT,
    prompt_text TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Table: agent_executions (100M rows, partitioned)
CREATE TABLE agent_executions (
    execution_id BIGSERIAL PRIMARY KEY,
    case_id VARCHAR(30),
    agent_id VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    input_data JSONB,
    output_data JSONB,
    tokens_used INT,
    cost_usd DECIMAL(10,4),
    status VARCHAR(20),
    error_message TEXT
) PARTITION BY RANGE (start_time);
```

**Services Connected**: All 8 data services, workflow-engine-svc, all 11 agents, audit-agent-svc

---

#### **Database 2: Redis 7.0 (In-Memory Cache & State Store)**

**Purpose**: Caching, session state, rate limiting, working memory  
**Size**: 26 GB (Premium P4)  
**Configuration**:
```yaml
Host: pa-redis.redis.cache.windows.net
Port: 6380 (SSL/TLS)
Version: Redis 7.0.12
Cluster Mode: Enabled (3 shards, 6 nodes)
Shards: 3 primary + 3 replica nodes
Eviction Policy: allkeys-lru
Max Memory: 26 GB
Persistence: AOF (Append-Only File, fsync every second)
High Availability: Zone-redundant
```

**Key Namespaces & TTL Policies**:

```redis
# Working Memory (TTL: 5 minutes)
working_memory:{case_id}:context → JSON string (workflow state)
working_memory:{case_id}:agents → Hash (agent results)
TTL: 300 seconds

# Cache Layer (TTL: varies by data type)
cache:member:{member_id} → JSON string (member data)
TTL: 3600 seconds (1 hour)

cache:provider:{npi} → JSON string (provider data)
TTL: 86400 seconds (24 hours)

cache:policy:{plan_id} → JSON string (policy rules)
TTL: 43200 seconds (12 hours)

cache:benefits:{plan_id}:{service} → JSON string (benefits config)
TTL: 21600 seconds (6 hours)

# Rate Limiting (TTL: 1 minute)
ratelimit:{client_id}:{endpoint} → Integer (token count)
TTL: 60 seconds (sliding window)

# Session State (TTL: 30 minutes)
session:{session_id} → JSON string (user session)
TTL: 1800 seconds

# LLM Response Cache (TTL: 24 hours)
llm_cache:{prompt_hash} → JSON string (LLM response)
TTL: 86400 seconds

# Locks (distributed locks for concurrency)
lock:case:{case_id} → String (lock owner)
TTL: 30 seconds (auto-release)
```

**Example Operations**:
```python
# Working memory store
await redis.setex(
    f"working_memory:{case_id}:context",
    300,  # 5 minutes
    json.dumps(context_dict)
)

# Cache-aside pattern
cached = await redis.get(f"cache:member:{member_id}")
if not cached:
    member = await db.fetch_member(member_id)
    await redis.setex(f"cache:member:{member_id}", 3600, json.dumps(member))

# Rate limiting (token bucket)
current = await redis.incr(f"ratelimit:{client_id}:pa_submit")
if current == 1:
    await redis.expire(f"ratelimit:{client_id}:pa_submit", 60)
if current > 100:
    raise RateLimitExceeded()
```

**Services Connected**: ALL services (universal caching layer)  
**Daily Operations**: ~500M cache operations  
**Cache Hit Rate**: 75% average (85% for member data)

---

#### **Database 3: Milvus 2.3 (Vector Database)**

**Purpose**: Semantic search, RAG retrieval, embedding storage  
**Size**: 1.2 TB (10M+ vectors)  
**Configuration**:
```yaml
Host: pa-milvus.eastus2.cloudapp.azure.com
Port: 19530 (gRPC), 9091 (HTTP metrics)
Version: Milvus 2.3.4 (Distributed cluster)
Cluster Topology:
  - 8 data nodes (storage)
  - 2 query nodes (search)
  - 2 index nodes (index building)
  - 1 coordinator (metadata)
Index Type: HNSW (Hierarchical Navigable Small World)
Metric Type: COSINE (cosine similarity)
Embedding Model: text-embedding-ada-002 (OpenAI, 1536 dims)
```

**Collections**:

##### **Collection: clinical_guidelines (5M vectors)**
```python
{
  "collection_name": "clinical_guidelines",
  "description": "Medical necessity guidelines (MCG, InterQual, Milliman)",
  "schema": {
    "fields": [
      {"name": "guideline_id", "type": "VARCHAR", "max_length": 100, "is_primary": True},
      {"name": "guideline_text", "type": "VARCHAR", "max_length": 65535},
      {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1536},
      {"name": "source", "type": "VARCHAR", "max_length": 50},  # MCG, InterQual, Milliman
      {"name": "specialty", "type": "VARCHAR", "max_length": 100},
      {"name": "procedure_codes", "type": "ARRAY", "element_type": "VARCHAR"},
      {"name": "effective_date", "type": "INT64"}  # Unix timestamp
    ]
  },
  "index_params": {
    "metric_type": "COSINE",
    "index_type": "HNSW",
    "params": {"M": 16, "efConstruction": 200}
  },
  "search_params": {"nprobe": 10, "ef": 64}
}
```

##### **Collection: policy_embeddings (2M vectors)**
```python
{
  "collection_name": "policy_embeddings",
  "description": "Insurance plan policy documents",
  "schema": {
    "fields": [
      {"name": "policy_id", "type": "VARCHAR", "max_length": 100, "is_primary": True},
      {"name": "policy_section", "type": "VARCHAR", "max_length": 10000},
      {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1536},
      {"name": "plan_id", "type": "VARCHAR", "max_length": 50},
      {"name": "coverage_category", "type": "VARCHAR", "max_length": 100}
    ]
  }
}
```

##### **Collection: historical_decisions (3M vectors)**
```python
{
  "collection_name": "historical_decisions",
  "description": "Past PA decisions for similar case retrieval",
  "schema": {
    "fields": [
      {"name": "case_id", "type": "VARCHAR", "max_length": 30, "is_primary": True},
      {"name": "case_summary", "type": "VARCHAR", "max_length": 5000},
      {"name": "embedding", "type": "FLOAT_VECTOR", "dim": 1536},
      {"name": "decision", "type": "VARCHAR", "max_length": 20},  # APPROVED, DENIED, MODIFIED
      {"name": "diagnosis_codes", "type": "ARRAY", "element_type": "VARCHAR"},
      {"name": "procedure_codes", "type": "ARRAY", "element_type": "VARCHAR"},
      {"name": "decision_date", "type": "INT64"}
    ]
  }
}
```

**Search Example**:
```python
# Vector search for similar clinical guidelines
results = milvus_client.search(
    collection_name="clinical_guidelines",
    data=[query_embedding],  # 1536-dim vector
    limit=20,
    output_fields=["guideline_id", "guideline_text", "source"],
    search_params={"metric_type": "COSINE", "params": {"ef": 64}}
)

# Results format:
# [
#   {"id": "MCG-A-0582", "distance": 0.92, "entity": {"guideline_text": "..."}},
#   {"id": "IQ-OP-123", "distance": 0.89, "entity": {"guideline_text": "..."}},
#   ...
# ]
```

**Services Connected**: vector-search-svc, clinical-agent-svc, policy-agent-svc, semantic-memory-svc  
**Daily Searches**: ~50,000 vector searches  
**Average Search Latency**: 45ms (P95)

---

#### **Database 4: Neo4j 5.x (Graph Database)**

**Purpose**: Knowledge graphs, relationship queries, fraud detection  
**Size**: 200 GB  
**Configuration**:
```yaml
Host: bolt://pa-neo4j.eastus2.cloudapp.azure.com
Port: 7687 (Bolt protocol), 7474 (HTTP)
Version: Neo4j 5.12 Enterprise
Cluster: Causal cluster (3 core servers + 2 read replicas)
Nodes: 500,000+
Relationships: 2,000,000+
Indexes: 15 composite indexes
```

**Graph Schema (Nodes & Relationships)**:

```cypher
// Node Types
(:Member {member_id, name, dob, plan_id})
(:Provider {npi, name, specialty, network_tier})
(:Claim {claim_id, service_date, amount, diagnosis_codes, procedure_codes})
(:Diagnosis {icd10_code, description})
(:Procedure {cpt_code, description})
(:Plan {plan_id, name, type})
(:PACase {case_id, status, decision, submission_date})
(:Facility {facility_id, name, type, address})

// Relationship Types
(:Member)-[:ENROLLED_IN]->(:Plan)
(:Member)-[:FILED]->(:Claim)
(:Claim)-[:SERVICED_BY]->(:Provider)
(:Claim)-[:AT_FACILITY]->(:Facility)
(:Claim)-[:HAS_DIAGNOSIS]->(:Diagnosis)
(:Claim)-[:HAS_PROCEDURE]->(:Procedure)
(:Provider)-[:CONTRACTS_WITH]->(:Plan)
(:Provider)-[:PRACTICES_AT]->(:Facility)
(:Member)-[:SUBMITTED]->(:PACase)
(:PACase)-[:REFERENCES]->(:Claim)  // Prior claims
(:Provider)-[:REFERRED_BY]->(:Provider)  // Referral networks
(:Diagnosis)-[:REQUIRES]->(:Procedure)  // Clinical pathways
(:Procedure)-[:HAS_CRITERIA]->(:Guideline)  // Medical necessity
```

**Sample Queries**:

```cypher
// 1. Fraud Detection: Provider billing patterns
MATCH (p:Provider {npi: '1234567890'})-[:SERVICED]->(c:Claim)
      -[:HAS_PROCEDURE]->(proc:Procedure {cpt_code: '99214'})
WHERE c.service_date > date() - duration({days: 90})
WITH p, count(c) as claim_count, avg(c.billed_amount) as avg_amount

// Compare to peer group (same specialty)
MATCH (peer:Provider {specialty: p.specialty})-[:SERVICED]->(peer_claim:Claim)
      -[:HAS_PROCEDURE]->(peer_proc:Procedure {cpt_code: '99214'})
WHERE peer.npi <> '1234567890'
  AND peer_claim.service_date > date() - duration({days: 90})

WITH p, claim_count, avg_amount,
     avg(peer_claim.billed_amount) as peer_avg,
     stddev(peer_claim.billed_amount) as peer_stddev

WHERE claim_count > peer_avg + (2 * peer_stddev)  // 2 std deviations

RETURN p.npi, p.name, claim_count, avg_amount, peer_avg
ORDER BY claim_count DESC;

// 2. Network Analysis: Member-provider affinity
MATCH (m:Member {member_id: 'M-987654321'})-[:FILED]->(c:Claim)
      -[:SERVICED_BY]->(p:Provider)
RETURN p.npi, p.name, count(c) as visit_count
ORDER BY visit_count DESC
LIMIT 10;

// 3. Clinical Pathways: Diagnosis → Procedure recommendations
MATCH (dx:Diagnosis {icd10_code: 'M54.5'})-[:REQUIRES]->(proc:Procedure)
      -[:HAS_CRITERIA]->(g:Guideline)
WHERE g.source = 'MCG'
RETURN proc.cpt_code, proc.description, g.guideline_text
ORDER BY proc.cpt_code;

// 4. Referral Network: Provider referral patterns
MATCH path = (p1:Provider)-[:REFERRED_BY*1..3]->(p2:Provider)
WHERE p1.npi = '1234567890'
RETURN p1.name as source_provider,
       p2.name as referred_to,
       length(path) as degrees_separation;
```

**Services Connected**: graph-rag-svc, fraud-agent-svc, network-service  
**Daily Queries**: ~10,000 Cypher queries  
**Average Query Latency**: 120ms (P95)

---

#### **Database 5: Elasticsearch 8.x (Full-Text Search)**

**Purpose**: Hybrid search (BM25 + vector), policy search, audit log search  
**Size**: 400 GB  
**Configuration**:
```yaml
Cluster Name: pa-elasticsearch-cluster
Version: Elasticsearch 8.10.2
Nodes: 6 (3 master-eligible, 3 data nodes)
Shards: 5 primary + 1 replica per index
Refresh Interval: 1 second
Memory: 32 GB per node (16 GB heap)
```

**Indices**:

##### **Index: clinical_guidelines**
```json
{
  "index": "clinical_guidelines",
  "mappings": {
    "properties": {
      "guideline_id": {"type": "keyword"},
      "guideline_text": {
        "type": "text",
        "analyzer": "english",
        "fields": {
          "keyword": {"type": "keyword"}
        }
      },
      "embedding": {
        "type": "dense_vector",
        "dims": 1536,
        "index": true,
        "similarity": "cosine"
      },
      "source": {"type": "keyword"},
      "specialty": {"type": "keyword"},
      "procedure_codes": {"type": "keyword"},
      "effective_date": {"type": "date"}
    }
  },
  "settings": {
    "number_of_shards": 5,
    "number_of_replicas": 1,
    "analysis": {
      "analyzer": {
        "medical_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball"]
        }
      }
    }
  }
}
```

##### **Index: policy_documents**
```json
{
  "index": "policy_documents",
  "mappings": {
    "properties": {
      "policy_id": {"type": "keyword"},
      "plan_id": {"type": "keyword"},
      "policy_text": {
        "type": "text",
        "analyzer": "english"
      },
      "embedding": {
        "type": "dense_vector",
        "dims": 1536,
        "index": true,
        "similarity": "cosine"
      },
      "effective_date": {"type": "date"},
      "coverage_category": {"type": "keyword"}
    }
  }
}
```

##### **Index: audit_logs**
```json
{
  "index": "audit_logs",
  "mappings": {
    "properties": {
      "timestamp": {"type": "date"},
      "user_id": {"type": "keyword"},
      "action": {"type": "keyword"},
      "resource": {"type": "keyword"},
      "case_id": {"type": "keyword"},
      "details": {"type": "text"},
      "ip_address": {"type": "ip"}
    }
  },
  "settings": {
    "index.lifecycle.name": "audit-retention-policy",
    "index.lifecycle.rollover_alias": "audit_logs"
  }
}
```

**Hybrid Search Example**:
```python
# Combined lexical (BM25) + semantic (vector) search
response = es_client.search(
    index="clinical_guidelines",
    body={
        "query": {
            "script_score": {
                "query": {
                    "multi_match": {
                        "query": "MRI lumbar spine low back pain",
                        "fields": ["guideline_text^2", "specialty"]
                    }
                },
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": query_embedding}
                }
            }
        },
        "size": 20
    }
)
```

**Services Connected**: hybrid-search-svc, clinical-content-service, audit-agent-svc, compliance-monitor-svc  
**Daily Searches**: ~100,000 queries  
**Average Search Latency**: 85ms (P95)

---

#### **Database 6: Azure Blob Storage (Object Storage)**

**Purpose**: Document storage (PDFs, DICOM images, fax TIFFs, attachments)  
**Size**: 10 TB (Hot tier)  
**Configuration**:
```yaml
Account Name: pahealthcarestorage
Account Type: StorageV2 (general purpose v2)
Access Tier: Hot (frequently accessed)
Redundancy: Zone-redundant storage (ZRS)
Encryption: AES-256 (Microsoft-managed keys)
Lifecycle Management:
  - Hot tier: 0-90 days
  - Cool tier: 91 days - 7 years
  - Archive tier: 7+ years
```

**Container Structure**:
```
pa-documents/
├── intake/
│   ├── 2026/
│   │   ├── 06/
│   │   │   ├── PA-2026-123456/
│   │   │   │   ├── physician_order.pdf (2.3 MB)
│   │   │   │   ├── medical_records.pdf (8.5 MB)
│   │   │   │   ├── lab_results.pdf (1.2 MB)
│   │   │   │   ├── imaging_study.dcm (45 MB DICOM)
│   │   │   │   └── metadata.json (5 KB)
│   │   │   └── PA-2026-123457/
│   │   │       └── ...
├── fax/
│   ├── 2026/
│   │   ├── 06/
│   │   │   ├── 02/
│   │   │   │   ├── fax-20260602-001.tiff (1.5 MB)
│   │   │   │   ├── fax-20260602-002.tiff (1.8 MB)
│   │   │   │   └── ...
├── decisions/
│   ├── 2026/
│   │   ├── 06/
│   │   │   ├── PA-2026-123456-decision.pdf (125 KB)
│   │   │   ├── PA-2026-123457-decision.pdf
│   │   │   └── ...
└── audit/
    ├── 2026/
    │   ├── 06/
    │   │   ├── audit-log-20260602.json (500 KB)
    │   │   └── ...
```

**Access Patterns**:
```python
# Upload document
blob_client = blob_service_client.get_blob_client(
    container="pa-documents",
    blob=f"intake/2026/06/PA-2026-123456/physician_order.pdf"
)
blob_client.upload_blob(
    file_stream,
    metadata={
        "case_id": "PA-2026-123456",
        "document_type": "physician_order",
        "upload_date": "2026-06-02T10:30:00Z"
    }
)

# Download document
blob_data = blob_client.download_blob()
content = blob_data.readall()
```

**Services Connected**: intake-agent-svc, fax-ocr-svc, notification-agent-svc, audit-agent-svc, web-portal-svc  
**Daily Operations**: ~150,000 blob operations (100K reads, 50K writes)  
**Average Latency**: 150ms (upload), 80ms (download)

---

## End-to-End Request Flow

### Complete PA Request Lifecycle (50 Steps, ~15 minutes)

#### **PHASE 1: INTAKE & DOCUMENT PROCESSING (Steps 1-13, Duration: 2 minutes)**

```
Step 1: User Submission via Web Portal
──────────────────────────────────────────────────────────────────
Component: web-portal-svc (React UI)
User: Provider office staff
Action: Upload physician order PDF (2.5 MB) + clinical notes
Protocol: HTTPS POST /api/v1/pa/submit
Payload: multipart/form-data
Timestamp: T+0s
──────────────────────────────────────────────────────────────────

Step 2: API Gateway - Authentication
──────────────────────────────────────────────────────────────────
Component: auth-gateway (Kong plugin)
Action: Validate OAuth2 JWT token
Database: Redis → GET session:{token_hash}
Latency: 5ms
Result: Authenticated user (provider_id: P-12345)
Timestamp: T+5ms
──────────────────────────────────────────────────────────────────

Step 3: API Gateway - Rate Limiting
──────────────────────────────────────────────────────────────────
Component: rate-limit-gateway (Kong + Redis)
Algorithm: Token bucket (100 req/min per client)
Database: Redis → INCR ratelimit:{client_id}:pa_submit
Latency: 2ms
Result: 23/100 tokens used, request allowed
Timestamp: T+7ms
──────────────────────────────────────────────────────────────────

Step 4: Upload Documents to Blob Storage
──────────────────────────────────────────────────────────────────
Component: web-portal-svc
Storage: Azure Blob Storage
Path: pa-documents/intake/2026/06/PA-2026-123456/physician_order.pdf
Operation: PUT blob with metadata
Latency: 150ms
Result: Document stored, blob URL returned
Timestamp: T+157ms
──────────────────────────────────────────────────────────────────

Step 5: Create PA Case Record in PostgreSQL
──────────────────────────────────────────────────────────────────
Component: web-portal-svc
Database: PostgreSQL (workflow_db.pa_cases)
Query:
  INSERT INTO pa_cases (
    case_id, member_id, provider_npi, submission_date,
    status, channel, document_urls
  ) VALUES (
    'PA-2026-123456', 'M-987654321', '1234567890',
    NOW(), 'pending', 'web_portal',
    '["https://blob.../physician_order.pdf"]'
  )
Latency: 8ms
Result: case_id = PA-2026-123456
Timestamp: T+165ms
──────────────────────────────────────────────────────────────────

Step 6: Publish Kafka Event - PA Case Created
──────────────────────────────────────────────────────────────────
Component: web-portal-svc → Kafka
Topic: pa.case.created
Partition: Hash(member_id) % 10 = 3
Message:
  {
    "case_id": "PA-2026-123456",
    "member_id": "M-987654321",
    "provider_npi": "1234567890",
    "timestamp": "2026-06-02T10:30:00.165Z",
    "channel": "web_portal"
  }
Latency: 5ms
Timestamp: T+170ms
──────────────────────────────────────────────────────────────────

Step 7: Workflow Engine Consumes Kafka Event
──────────────────────────────────────────────────────────────────
Component: workflow-engine-svc (LangGraph)
Trigger: Kafka consumer on pa.case.created topic
Action: Initialize PAWorkflow for case PA-2026-123456
Workflow: 11 agent nodes, supervisor pattern
State: Initialize in Redis working memory
Database: Redis → SETEX working_memory:PA-2026-123456:context 300 "{...}"
Latency: 20ms
Timestamp: T+190ms
──────────────────────────────────────────────────────────────────

Step 8: Temporal - Create Durable Workflow
──────────────────────────────────────────────────────────────────
Component: temporal-server
Workflow ID: PA-2026-123456-workflow
Timeout: 30 minutes
Retry Policy: Exponential backoff (1s → 60s, max 5 attempts)
Database: PostgreSQL (temporal persistence)
Latency: 15ms
Timestamp: T+205ms
──────────────────────────────────────────────────────────────────

Step 9: Intake Agent - Document Classification (LLM Call #1)
──────────────────────────────────────────────────────────────────
Component: intake-agent-svc
LLM: GPT-4o Vision (gpt-4o-2024-05-13)
Input: physician_order.pdf from Blob Storage
Prompt:
  "Classify this document. Options: physician_order, medical_records,
   lab_results, imaging, pharmacy, other. Return JSON."
Temperature: 0.0 (deterministic)
Max Tokens: 500
Database: Redis → GET llm_cache:{prompt_hash} → MISS
LLM API Latency: 2.1s
Output: {"type": "physician_order", "confidence": 0.98}
Cache: Redis → SETEX llm_cache:{hash} 86400 "{...}"
Timestamp: T+2.3s
──────────────────────────────────────────────────────────────────

Step 10: Intake Agent - OCR with Azure Form Recognizer
──────────────────────────────────────────────────────────────────
Component: intake-agent-svc → Azure Form Recognizer
API: POST https://eastus2.api.cognitive.microsoft.com/formrecognizer/
Model: prebuilt-healthInsuranceCard.us
Input: physician_order.pdf blob URL
Latency: 3.5s
Output:
  {
    "member_id": "M-987654321",
    "provider_npi": "1234567890",
    "diagnosis": "M54.5 - Low back pain",
    "procedure": "72148 - MRI Lumbar Spine without contrast",
    "urgency": "Routine",
    "clinical_notes": "Patient experiencing chronic low back pain..."
  }
Timestamp: T+5.8s
──────────────────────────────────────────────────────────────────

Step 11: Intake Agent - Entity Extraction (LLM Call #2)
──────────────────────────────────────────────────────────────────
Component: intake-agent-svc
LLM: GPT-4o (structured output mode)
Prompt:
  "Extract structured medical entities from this OCR text.
   Return JSON matching this schema: {MedicalRequest}"
Schema: Pydantic model (member, diagnosis_codes, procedure_codes, clinical_summary)
Temperature: 0.1
Max Tokens: 2000
LLM Latency: 1.8s
Output:
  {
    "member": {"member_id": "M-987654321", ...},
    "diagnosis_codes": ["M54.5"],
    "procedure_codes": ["72148"],
    "clinical_summary": "Patient experiencing chronic low back pain...",
    "urgency": "routine"
  }
Timestamp: T+7.6s
──────────────────────────────────────────────────────────────────

Step 12: Store Extracted Data in PostgreSQL
──────────────────────────────────────────────────────────────────
Component: intake-agent-svc
Database: PostgreSQL (workflow_db.pa_cases)
Query:
  UPDATE pa_cases
  SET extracted_data = $1, status = 'intake_complete'
  WHERE case_id = 'PA-2026-123456'
Latency: 12ms
Timestamp: T+7.612s
──────────────────────────────────────────────────────────────────

Step 13: Update Working Memory
──────────────────────────────────────────────────────────────────
Component: working-memory-svc
Database: Redis
Query:
  HSET working_memory:PA-2026-123456:agents
       "intake_agent" "{...result JSON...}"
  EXPIRE working_memory:PA-2026-123456:agents 300
Latency: 3ms
Timestamp: T+7.615s (End of Intake Phase)
──────────────────────────────────────────────────────────────────
```

#### **PHASE 2: ELIGIBILITY VERIFICATION (Steps 14-18, Duration: 15 seconds)**

```
Step 14: Eligibility Agent - Call Member Service
──────────────────────────────────────────────────────────────────
Component: eligibility-agent-svc → member-service
API: gRPC MemberService/GetMember
Request: {member_id: "M-987654321"}
Protocol: gRPC (binary, HTTP/2)
Latency: 2ms (gRPC overhead)
Timestamp: T+7.617s
──────────────────────────────────────────────────────────────────

Step 15: Member Service - Cache Check (Redis)
──────────────────────────────────────────────────────────────────
Component: member-service
Database: Redis
Query: GET cache:member:M-987654321
Result: HIT (cached, TTL remaining: 2,400s)
Cached Data:
  {
    "member_id": "M-987654321",
    "name": "John Doe",
    "dob": "1980-05-15",
    "plan_id": "PLAN-2024-GOLD",
    "enrollment_status": "Active",
    "enrollment_start": "2024-01-01",
    "enrollment_end": "2024-12-31"
  }
Latency: 2ms
Timestamp: T+7.619s
──────────────────────────────────────────────────────────────────

Step 16: Eligibility Agent - COB Check (PostgreSQL)
──────────────────────────────────────────────────────────────────
Component: eligibility-agent-svc
Database: PostgreSQL (member_db.coordination_of_benefits)
Query:
  SELECT * FROM coordination_of_benefits
  WHERE member_id = 'M-987654321' AND status = 'active'
Result: No rows (no secondary insurance)
Latency: 8ms
Timestamp: T+7.627s
──────────────────────────────────────────────────────────────────

Step 17: Eligibility Agent - LLM Decision (LLM Call #3)
──────────────────────────────────────────────────────────────────
Component: eligibility-agent-svc
LLM: GPT-3.5 Turbo (fast, cheap for simple task)
Prompt:
  "Determine if member M-987654321 is eligible for PA.
   Member data: {member_data}
   Current date: 2026-06-02
   Return JSON: {eligible: boolean, reason: string}"
Temperature: 0.0
Max Tokens: 200
LLM Latency: 0.8s
Output: {"eligible": true, "reason": "Active enrollment in PLAN-2024-GOLD"}
Timestamp: T+8.4s
──────────────────────────────────────────────────────────────────

Step 18: Update Workflow State
──────────────────────────────────────────────────────────────────
Component: workflow-engine-svc
Database: Redis
Query:
  HSET working_memory:PA-2026-123456:agents
       "eligibility_agent" "{...result...}"
Latency: 3ms
Timestamp: T+8.403s (End of Eligibility Phase)
──────────────────────────────────────────────────────────────────
```

#### **PHASE 3: BENEFITS DETERMINATION (Steps 19-23, Duration: 20 seconds)**

```
Step 19: Benefits Agent - Policy Lookup
──────────────────────────────────────────────────────────────────
Component: benefits-agent-svc → policy-service
API: GET /api/v1/policies/PLAN-2024-GOLD
Database: PostgreSQL (policy_db.plan_policies)
Query:
  SELECT * FROM plan_policies
  WHERE plan_id = 'PLAN-2024-GOLD'
Latency: 25ms
Output: Policy rules for PLAN-2024-GOLD (JSON, 15 KB)
Timestamp: T+8.428s
──────────────────────────────────────────────────────────────────

Step 20: Benefits Agent - Benefits Config Lookup
──────────────────────────────────────────────────────────────────
Component: benefits-agent-svc → benefits-config-service
API: GET /api/v1/benefits/PLAN-2024-GOLD/MRI
Database: PostgreSQL (policy_db.benefits_config)
Query:
  SELECT copay, coinsurance, deductible, oop_max, requires_pa
  FROM benefits_config
  WHERE plan_id = 'PLAN-2024-GOLD'
    AND service_category = 'MRI'
Latency: 18ms
Output:
  {
    "copay": 0,
    "coinsurance": 0.20,  // 20% after deductible
    "deductible": 2000,
    "oop_max": 8000,
    "requires_pa": true
  }
Timestamp: T+8.446s
──────────────────────────────────────────────────────────────────

Step 21: Benefits Agent - Cost Calculation (LLM Call #4)
──────────────────────────────────────────────────────────────────
Component: benefits-agent-svc
LLM: GPT-4o (math reasoning with code interpreter)
Prompt:
  "Calculate member cost-sharing for MRI lumbar spine.
   Estimated charge: $1,500
   Plan: PLAN-2024-GOLD
   Benefits: {benefits_config}
   Member YTD: deductible met = $1,200, OOP = $3,500
   Return JSON: {estimated_charge, member_responsibility, plan_pays}"
Tool: Python code interpreter
Temperature: 0.1
Max Tokens: 1000
LLM Latency: 2.3s
Output:
  {
    "estimated_charge": 1500,
    "deductible_remaining": 800,  // $2000 - $1200
    "after_deductible": 700,      // $1500 - $800
    "coinsurance_amount": 140,    // $700 * 0.20
    "member_responsibility": 940, // $800 + $140
    "plan_pays": 560              // $1500 - $940
  }
Timestamp: T+10.7s
──────────────────────────────────────────────────────────────────

Step 22: Benefits Agent - Network Tier Check
──────────────────────────────────────────────────────────────────
Component: benefits-agent-svc → network-service
API: GET /api/v1/network/check?plan=PLAN-2024-GOLD&npi=1234567890
Database: PostgreSQL (provider_db.network_contracts)
Query:
  SELECT network_tier FROM network_contracts
  WHERE plan_id = 'PLAN-2024-GOLD'
    AND provider_npi = '1234567890'
    AND effective_date <= CURRENT_DATE
    AND (termination_date IS NULL OR termination_date > CURRENT_DATE)
Latency: 15ms
Output: {"tier": "In-Network Tier 1"}
Timestamp: T+10.715s
──────────────────────────────────────────────────────────────────

Step 23: Update Benefits Decision
──────────────────────────────────────────────────────────────────
Component: benefits-agent-svc
Database: Redis
Query:
  HSET working_memory:PA-2026-123456:agents
       "benefits_agent" "{...}"
Latency: 3ms
Timestamp: T+10.718s (End of Benefits Phase)
──────────────────────────────────────────────────────────────────
```

#### **PHASE 4: CLINICAL REVIEW WITH RAG (Steps 24-34, Duration: 8 minutes) - BOTTLENECK**

```
Step 24: Clinical Agent - Generate Search Query (LLM Call #5)
──────────────────────────────────────────────────────────────────
Component: clinical-agent-svc
LLM: GPT-4o (query generation)
Prompt:
  "Generate a search query to find medical necessity guidelines for:
   - Diagnosis: M54.5 (Low back pain)
   - Procedure: 72148 (MRI lumbar spine without contrast)
   - Patient age: 46 years old
   Return only the search query string."
Temperature: 0.3
Max Tokens: 200
LLM Latency: 1.2s
Output: "MRI lumbar spine indications low back pain radicular symptoms
         medical necessity criteria conservative treatment failure"
Timestamp: T+11.9s
──────────────────────────────────────────────────────────────────

Step 25: Generate Query Embedding
──────────────────────────────────────────────────────────────────
Component: clinical-agent-svc
API: OpenAI Embeddings API
Model: text-embedding-ada-002
Input: Search query string (120 characters)
Output: 1536-dimensional vector [0.012, -0.045, 0.089, ...]
Latency: 0.3s
Timestamp: T+12.2s
──────────────────────────────────────────────────────────────────

Step 26: Vector Search in Milvus (Parallel Operation 1/3)
──────────────────────────────────────────────────────────────────
Component: vector-search-svc
Database: Milvus (clinical_guidelines collection)
Query:
  milvus_client.search(
    collection_name="clinical_guidelines",
    data=[query_embedding],
    limit=20,
    metric_type="COSINE",
    params={"nprobe": 10, "ef": 64}
  )
Latency: 45ms
Output: Top 20 guidelines with similarity scores
  [
    {id: "MCG-A-0582", score: 0.92, text: "MRI Lumbar Spine..."},
    {id: "IQ-OP-123", score: 0.89, text: "Low Back Pain Imaging..."},
    ...
  ]
Timestamp: T+12.245s
──────────────────────────────────────────────────────────────────

Step 27: BM25 Search in Elasticsearch (Parallel Operation 2/3)
──────────────────────────────────────────────────────────────────
Component: hybrid-search-svc
Database: Elasticsearch (clinical_guidelines index)
Query:
  {
    "query": {
      "multi_match": {
        "query": "MRI lumbar spine low back pain",
        "fields": ["guideline_text^2", "specialty"]
      }
    },
    "size": 20
  }
Latency: 85ms
Output: Top 20 BM25-ranked guidelines
  [
    {_id: "MCG-A-0582", _score: 18.5, ...},
    {_id: "MILL-LBP-01", _score: 16.2, ...},
    ...
  ]
Timestamp: T+12.285s
──────────────────────────────────────────────────────────────────

Step 28: Graph RAG - Knowledge Graph Traversal (Parallel Operation 3/3)
──────────────────────────────────────────────────────────────────
Component: graph-rag-svc
Database: Neo4j
Query:
  MATCH (dx:Diagnosis {icd10_code: 'M54.5'})
        -[:REQUIRES]->(proc:Procedure {cpt_code: '72148'})
        -[:HAS_CRITERIA]->(g:Guideline)
  WHERE g.source IN ['MCG', 'InterQual', 'Milliman']
  RETURN g.guideline_id, g.guideline_text, g.source
  LIMIT 10
Latency: 120ms
Output: 5 guidelines from knowledge graph
  [
    {guideline_id: "MCG-A-0582", source: "MCG", ...},
    {guideline_id: "IQ-OP-123", source: "InterQual", ...},
    ...
  ]
Timestamp: T+12.320s
──────────────────────────────────────────────────────────────────

Step 29: Merge & Rerank Results (Reciprocal Rank Fusion)
──────────────────────────────────────────────────────────────────
Component: clinical-agent-svc
Algorithm: RRF = Σ (1 / (k + rank_i)) where k=60
Inputs:
  - Vector search results (20 docs)
  - BM25 results (20 docs)
  - Graph results (5 docs)
Latency: 15ms (in-memory computation)
Output: Top 10 merged & reranked guidelines
  [
    {guideline_id: "MCG-A-0582", rrf_score: 0.035, ...},
    {guideline_id: "IQ-OP-123", rrf_score: 0.031, ...},
    ...
  ]
Timestamp: T+12.335s
──────────────────────────────────────────────────────────────────

Step 30: Retrieve Full Guideline Text from PostgreSQL
──────────────────────────────────────────────────────────────────
Component: clinical-content-service
Database: PostgreSQL (policy_db.clinical_guidelines)
Query:
  SELECT guideline_id, guideline_text, source
  FROM clinical_guidelines
  WHERE guideline_id IN ('MCG-A-0582', 'IQ-OP-123', ...)
Latency: 45ms
Output: Full text of 10 guidelines (~15,000 tokens total)
Timestamp: T+12.380s
──────────────────────────────────────────────────────────────────

Step 31: Clinical Agent - Medical Necessity Determination (LLM Call #6)
──────────────────────────────────────────────────────────────────
Component: clinical-agent-svc
LLM: GPT-4o (128k context window)
Prompt:
  "You are a clinical reviewer for a health insurance company.
   Based on these medical necessity guidelines, determine if
   MRI lumbar spine (CPT 72148) is medically necessary for a
   46-year-old patient with M54.5 (low back pain).
   
   Guidelines:
   {15,000 tokens of guidelines}
   
   Patient clinical notes:
   {clinical_summary from intake}
   
   Return JSON:
   {
     decision: 'Approve' | 'Deny' | 'Modify',
     rationale: string (detailed explanation),
     guidelines_cited: array of guideline IDs,
     confidence: float (0-1)
   }"
Temperature: 0.2
Max Tokens: 2000
LLM Latency: 4.5s
Output:
  {
    "decision": "Approve",
    "rationale": "Patient meets MCG criteria A-0582 for MRI lumbar spine: 
                  (1) 6+ weeks of conservative treatment failure documented,
                  (2) Radicular symptoms present (leg pain with numbness),
                  (3) No red flags requiring urgent imaging,
                  (4) Failed physical therapy and NSAIDs.
                  InterQual OP-123 criteria also met.",
    "guidelines_cited": ["MCG-A-0582", "InterQual OP-123"],
    "confidence": 0.94
  }
Timestamp: T+16.880s
──────────────────────────────────────────────────────────────────

Step 32: Safety Evaluation - Hallucination Check
──────────────────────────────────────────────────────────────────
Component: safety-eval-svc (Guardrails AI)
Check: Verify LLM output against source guidelines
Method:
  1. Semantic similarity between rationale and cited guidelines
  2. Fact verification (do guidelines actually say this?)
  3. Consistency check (decision matches rationale?)
Latency: 1.2s
Output:
  {
    "hallucination_detected": false,
    "confidence": 0.96,
    "issues": []
  }
Timestamp: T+18.080s
──────────────────────────────────────────────────────────────────

Step 33: Store Clinical Decision
──────────────────────────────────────────────────────────────────
Component: clinical-agent-svc
Database 1: Redis (working memory)
Query:
  HSET working_memory:PA-2026-123456:agents
       "clinical_agent" "{...}"
Latency: 3ms

Database 2: PostgreSQL (persistent)
Query:
  UPDATE pa_cases
  SET clinical_decision = $1
  WHERE case_id = 'PA-2026-123456'
Latency: 12ms

Total Latency: 15ms
Timestamp: T+18.095s (End of Clinical Phase)
──────────────────────────────────────────────────────────────────

Note: Clinical RAG phase accounts for 53% of total workflow time.
Optimization opportunity: Pre-index common diagnosis-procedure pairs.
```

_(Continuing in similar detail for remaining phases...)_

#### **PHASE 5: POLICY & FRAUD ANALYSIS (Steps 35-37, Duration: 3 minutes)**

```
Steps 35-36: Policy Agent (runs in parallel with Clinical Agent)
──────────────────────────────────────────────────────────────────
Duration: 2.5 minutes
LLM: Claude 3.5 Sonnet (excellent at rules reasoning)
Output: {policy_compliant: true, exclusions: []}

Step 37: Fraud Agent (Graph Analytics)
──────────────────────────────────────────────────────────────────
Duration: 45 seconds
Neo4j queries + Isolation Forest anomaly detection
Output: {fraud_risk: "Low", score: 0.12}
```

#### **PHASE 6: FINAL DECISION (Steps 38-42, Duration: 1 minute)**

```
Step 38: Decision Agent - Aggregate All Results (LLM Call #12)
──────────────────────────────────────────────────────────────────
LLM: GPT-4o
Inputs: Results from 7 agents (intake, eligibility, benefits, clinical,
        policy, fraud, COM)
Output:
  {
    "decision": "APPROVED",
    "confidence": 0.94,
    "auth_number": "AUTH-2026-123456",
    "valid_through": "2026-09-01",
    "requires_human_review": false
  }

Step 39: HITL Routing - Risk Assessment
──────────────────────────────────────────────────────────────────
Rules Engine: Drools
Rules Applied:
  - IF confidence < 0.85 THEN human_review = true
  - IF fraud_risk > 0.30 THEN human_review = true
  - IF decision = 'DENIED' THEN human_review = true
  - IF high_cost_procedure (>$10K) THEN 10% random sample
Result: requires_review = false (confidence=0.94, approved decision)
Action: Skip human review queue
```

#### **PHASE 7: FINALIZATION (Steps 43-50, Duration: 1 minute)**

```
Step 43: Update PostgreSQL Case Record
──────────────────────────────────────────────────────────────────
Query:
  UPDATE pa_cases
  SET decision = 'APPROVED',
      auth_number = 'AUTH-2026-123456',
      decision_date = NOW(),
      status = 'completed'
  WHERE case_id = 'PA-2026-123456'

Step 44: Blockchain Audit Trail (Hyperledger Fabric)
──────────────────────────────────────────────────────────────────
Immutable audit log for compliance

Step 45: Generate Decision Letter PDF
──────────────────────────────────────────────────────────────────
Template: Jinja2, Library: WeasyPrint
Upload to: Azure Blob Storage

Step 46-47: Notifications
──────────────────────────────────────────────────────────────────
- Email via SendGrid (350ms)
- WebSocket push to web portal (50ms)

Step 48: Kafka Event - Case Completed
──────────────────────────────────────────────────────────────────
Topic: pa.case.completed
Consumers: Analytics, reporting, billing systems

Step 49: Episodic Memory Storage
──────────────────────────────────────────────────────────────────
PostgreSQL + Milvus embedding for future retrieval

Step 50: Temporal Workflow Completion
──────────────────────────────────────────────────────────────────
Status: COMPLETED
Duration: 14 minutes 32 seconds (under 30-min SLA)
Metrics:
  - Agents executed: 7
  - LLM calls: 12
  - Total tokens: 47,523
  - Total cost: $0.95
  - Database queries: 38
```

---

## Service Connectivity Matrix

### Complete Service-to-Service Dependencies

| Source Service | Target Service | Protocol | Port | Purpose | Avg Latency |
|----------------|----------------|----------|------|---------|-------------|
| web-portal-svc | Kong Gateway | HTTPS | 443 | All API requests | 5ms |
| Kong Gateway | workflow-engine-svc | gRPC | 8010 | Start workflow | 10ms |
| workflow-engine-svc | intake-agent-svc | gRPC | 8100 | Invoke agent | 8ms |
| intake-agent-svc | Azure Form Recognizer | HTTPS | 443 | OCR processing | 3.5s |
| intake-agent-svc | Azure Blob Storage | HTTPS | 443 | Document I/O | 150ms |
| intake-agent-svc | llm-gateway | gRPC | 8005 | LLM requests | 2-5s |
| eligibility-agent-svc | member-service | gRPC | 8500 | Member lookup | 2ms (cache) |
| member-service | PostgreSQL | TCP | 5432 | SQL query | 8ms |
| member-service | Redis | TCP | 6380 | Cache check | 2ms |
| benefits-agent-svc | policy-service | gRPC | 8502 | Policy lookup | 25ms |
| benefits-agent-svc | benefits-config-service | gRPC | 8504 | Benefits query | 18ms |
| benefits-agent-svc | network-service | REST | 8505 | Network check | 15ms |
| clinical-agent-svc | vector-search-svc | gRPC | 8402 | Vector search | 45ms |
| vector-search-svc | Milvus | gRPC | 19530 | Dense retrieval | 40ms |
| clinical-agent-svc | hybrid-search-svc | REST | 8200 | BM25 search | 85ms |
| hybrid-search-svc | Elasticsearch | REST | 9200 | Full-text search | 80ms |
| clinical-agent-svc | graph-rag-svc | gRPC | 8300 | Graph query | 120ms |
| graph-rag-svc | Neo4j | Bolt | 7687 | Cypher execution | 115ms |
| clinical-agent-svc | clinical-content-service | gRPC | 8507 | Guideline retrieval | 45ms |
| fraud-agent-svc | Neo4j | Bolt | 7687 | Graph analytics | 200ms |
| all agents | llm-gateway | gRPC | 8005 | LLM routing | 1-5s |
| llm-gateway | OpenAI API | HTTPS | 443 | GPT-4o/3.5 | 1-5s |
| llm-gateway | Anthropic API | HTTPS | 443 | Claude 3.5 | 1-4s |
| llm-gateway | Redis | TCP | 6380 | Response cache | 2ms |
| safety-eval-svc | Guardrails AI API | HTTPS | 443 | Safety check | 1.2s |
| notification-agent-svc | SendGrid API | HTTPS | 443 | Email delivery | 350ms |
| notification-agent-svc | Azure Blob Storage | HTTPS | 443 | PDF storage | 150ms |
| all services | Prometheus | HTTP | 9090 | Metrics push | 5ms |
| all services | Jaeger | gRPC | 14250 | Trace export | 10ms |
| workflow-engine-svc | Kafka | TCP | 9092 | Event publish | 5ms |
| all services | Keycloak | HTTPS | 8080 | Token validate | 15ms |
| all services | Vault | HTTPS | 8200 | Secrets fetch | 10ms |

**Total Service Dependencies**: 140+ direct connections

---

## Database Connectivity Patterns

### Pattern 1: Cache-Aside (Redis + PostgreSQL)

**Use Case**: Member/Provider/Policy lookups with high read frequency

```python
# Example: Member Service
async def get_member(member_id: str) -> Member:
    # Step 1: Check Redis cache
    cache_key = f"cache:member:{member_id}"
    cached = await redis.get(cache_key)
    
    if cached:
        logger.info(f"Cache HIT: {member_id}")
        metrics.increment("member_cache_hit")
        return Member.parse_raw(cached)
    
    # Step 2: Cache MISS - Query PostgreSQL
    logger.info(f"Cache MISS: {member_id}")
    metrics.increment("member_cache_miss")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM members WHERE member_id = $1",
            member_id
        )
    
    if not row:
        raise MemberNotFoundError(member_id)
    
    member = Member(**dict(row))
    
    # Step 3: Store in cache (TTL: 1 hour)
    await redis.setex(
        cache_key,
        3600,  # 1 hour TTL
        member.json()
    )
    
    return member
```

**Performance**:
- Cache hit: 2ms
- Cache miss: 10ms (8ms PostgreSQL + 2ms Redis write)
- Cache hit rate: 85%

---

### Pattern 2: Hybrid Retrieval (Milvus + Elasticsearch + Neo4j + PostgreSQL)

**Use Case**: Clinical guideline retrieval with RAG

```python
async def retrieve_guidelines(
    query: str,
    diagnosis_codes: List[str],
    procedure_codes: List[str],
    top_k: int = 10
) -> List[Guideline]:
    
    # Step 1: Generate query embedding
    query_embedding = await openai.embeddings.create(
        model="text-embedding-ada-002",
        input=query
    )
    embedding = query_embedding.data[0].embedding
    
    # Step 2: Parallel retrieval from 3 sources
    vector_task = milvus_client.search(
        collection_name="clinical_guidelines",
        data=[embedding],
        limit=20,
        metric_type="COSINE",
        params={"nprobe": 10, "ef": 64}
    )
    
    bm25_task = elasticsearch_client.search(
        index="clinical_guidelines",
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["guideline_text^2", "specialty"]
                }
            },
            "size": 20
        }
    )
    
    graph_task = neo4j_session.run(
        """
        MATCH (dx:Diagnosis)-[:REQUIRES]->(proc:Procedure)
              -[:HAS_CRITERIA]->(g:Guideline)
        WHERE dx.icd10_code IN $diagnosis_codes
          AND proc.cpt_code IN $procedure_codes
        RETURN g.guideline_id, g.guideline_text
        LIMIT 10
        """,
        diagnosis_codes=diagnosis_codes,
        procedure_codes=procedure_codes
    )
    
    # Step 3: Await all parallel tasks
    vector_results, bm25_results, graph_results = await asyncio.gather(
        vector_task, bm25_task, graph_task
    )
    
    # Step 4: Reciprocal Rank Fusion
    merged = reciprocal_rank_fusion(
        [vector_results, bm25_results, graph_results],
        k=60
    )
    
    # Step 5: Retrieve full text from PostgreSQL
    guideline_ids = [doc.id for doc in merged[:top_k]]
    full_guidelines = await postgres_client.fetch(
        "SELECT * FROM clinical_guidelines WHERE guideline_id = ANY($1)",
        guideline_ids
    )
    
    return full_guidelines
```

**Performance**:
- Milvus vector search: 45ms
- Elasticsearch BM25: 85ms
- Neo4j graph traversal: 120ms
- PostgreSQL full text: 45ms
- **Total (parallel)**: ~250ms (max of parallel operations + fusion)

---

### Pattern 3: Graph Analytics (Neo4j)

**Use Case**: Fraud detection, provider network analysis

```python
async def detect_billing_anomalies(
    provider_npi: str,
    procedure_code: str,
    lookback_days: int = 90
) -> dict:
    
    # Step 1: Graph query for provider patterns
    result = await neo4j_session.run(
        """
        // Provider's billing for this procedure
        MATCH (p:Provider {npi: $npi})-[:SERVICED]->(c:Claim)
              -[:HAS_PROCEDURE]->(proc:Procedure {cpt_code: $proc_code})
        WHERE c.service_date > date() - duration({days: $lookback_days})
        
        // Calculate statistics
        WITH p, count(c) as claim_count,
             avg(c.billed_amount) as avg_amount,
             stddev(c.billed_amount) as stddev_amount
        
        // Compare to peer group (same specialty)
        MATCH (peer:Provider {specialty: p.specialty})
              -[:SERVICED]->(peer_claim:Claim)
              -[:HAS_PROCEDURE]->(peer_proc:Procedure {cpt_code: $proc_code})
        WHERE peer.npi <> $npi
          AND peer_claim.service_date > date() - duration({days: $lookback_days})
        
        WITH p, claim_count, avg_amount, stddev_amount,
             avg(peer_claim.billed_amount) as peer_avg,
             stddev(peer_claim.billed_amount) as peer_stddev,
             count(DISTINCT peer.npi) as peer_count
        
        RETURN claim_count, avg_amount, stddev_amount,
               peer_avg, peer_stddev, peer_count
        """,
        npi=provider_npi,
        proc_code=procedure_code,
        lookback_days=lookback_days
    )
    
    data = await result.single()
    
    # Step 2: Anomaly detection with Isolation Forest
    features = np.array([[
        data['claim_count'],
        data['avg_amount'],
        data['stddev_amount']
    ]])
    
    anomaly_score = isolation_forest.predict(features)[0]
    
    # Step 3: Risk scoring
    if anomaly_score == -1:  # Anomaly detected
        z_score = (data['avg_amount'] - data['peer_avg']) / data['peer_stddev']
        risk_score = min(1.0, abs(z_score) / 3.0)  # Normalize to 0-1
        return {
            "fraud_risk": "High",
            "score": risk_score,
            "details": {
                "claim_count": data['claim_count'],
                "avg_amount": data['avg_amount'],
                "peer_avg": data['peer_avg'],
                "z_score": z_score
            }
        }
    else:
        return {"fraud_risk": "Low", "score": 0.12}
```

**Performance**:
- Neo4j query: 200ms
- Isolation Forest: 10ms
- **Total**: 210ms

---

### Pattern 4: Working Memory (Redis Only)

**Use Case**: Workflow state, agent context

```python
class WorkingMemory:
    def __init__(self, case_id: str, ttl: int = 300):
        self.case_id = case_id
        self.ttl = ttl
        self.key_prefix = f"working_memory:{case_id}"
    
    async def store_context(self, context: dict):
        """Store entire workflow context"""
        await redis.setex(
            f"{self.key_prefix}:context",
            self.ttl,
            json.dumps(context)
        )
    
    async def get_context(self) -> dict:
        """Retrieve workflow context"""
        data = await redis.get(f"{self.key_prefix}:context")
        return json.loads(data) if data else {}
    
    async def update_agent_result(self, agent_name: str, result: dict):
        """Store individual agent result"""
        await redis.hset(
            f"{self.key_prefix}:agents",
            agent_name,
            json.dumps(result)
        )
        await redis.expire(f"{self.key_prefix}:agents", self.ttl)
    
    async def get_all_agent_results(self) -> dict:
        """Get results from all agents"""
        data = await redis.hgetall(f"{self.key_prefix}:agents")
        return {
            k.decode(): json.loads(v.decode())
            for k, v in data.items()
        }
```

**Performance**: 3ms per operation

---

## Business + Technical Workflow

### Combined Business Process + Technical Implementation

```
BUSINESS FLOW                          TECHNICAL IMPLEMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PROVIDER SUBMITS PA REQUEST        web-portal-svc → Kong Gateway
   - Upload physician order            - HTTPS POST /api/v1/pa/submit
   - Provide clinical notes            - OAuth2 authentication
   - Member demographics               - Rate limiting (100 req/min)
                                       → Azure Blob Storage (document upload)
                                       → PostgreSQL (create pa_cases record)
                                       → Kafka (publish pa.case.created event)
                                       
2. HEALTH PLAN RECEIVES REQUEST        workflow-engine-svc (LangGraph)
   - Create case number                - Initialize PAWorkflow
   - Assign to review queue            - Temporal.io (durable execution)
   - Start 30-min SLA timer            → Redis (working memory)
                                       
3. INTAKE PROCESSING                   intake-agent-svc
   - Classify documents                - GPT-4o Vision (document classification)
   - Extract key data                  - Azure Form Recognizer (OCR)
   - Identify member, provider         - GPT-4o (entity extraction)
   → Business Decision: Valid request? → PostgreSQL (store extracted_data)
                                       
4. VERIFY MEMBER ELIGIBILITY           eligibility-agent-svc
   - Check active enrollment           → member-service → Redis/PostgreSQL
   - Verify coverage dates             - gRPC GetMember call
   - Check coordination of benefits    - SQL query on eligibility_history
   → Business Decision: Member eligible? - GPT-3.5 Turbo (eligibility determination)
                                       → Redis (cache result)
                                       
5. DETERMINE BENEFITS                  benefits-agent-svc
   - Lookup plan coverage              → policy-service → PostgreSQL
   - Calculate cost-sharing            → benefits-config-service → PostgreSQL
   - Check network tier                → network-service → PostgreSQL
   - Estimate member cost              - GPT-4o (cost calculation with code)
   → Business Decision: Covered service? → Redis (store benefits decision)
                                       
6. CLINICAL REVIEW                     clinical-agent-svc
   - Retrieve medical guidelines       → vector-search-svc → Milvus (vector search)
   - Search policy documents           → hybrid-search-svc → Elasticsearch (BM25)
   - Check clinical pathways           → graph-rag-svc → Neo4j (graph traversal)
   - Assess medical necessity          → clinical-content-service → PostgreSQL
   - Review prior treatments           - GPT-4o 128k (medical necessity review)
   → Business Decision: Medically necessary? - Guardrails AI (hallucination check)
                                       → PostgreSQL + Redis (store decision)
                                       
7. POLICY COMPLIANCE CHECK             policy-agent-svc
   - Verify plan exclusions            - Claude 3.5 Sonnet (policy reasoning)
   - Check prior authorization rules   → Elasticsearch (policy search)
   - Review step therapy requirements  → PostgreSQL (policy_db)
   → Business Decision: Policy compliant? → Redis (store policy decision)
                                       
8. FRAUD DETECTION                     fraud-agent-svc
   - Analyze provider patterns         → Neo4j (graph analytics)
   - Check billing anomalies           - Cypher queries on claims graph
   - Review claim history              - Isolation Forest (ML anomaly detection)
   → Business Decision: Fraud risk?    → PostgreSQL (log fraud score)
                                       
9. FINAL DECISION                      decision-agent-svc
   - Aggregate all findings            - GPT-4o (decision aggregation)
   - Calculate confidence score        - Inputs from 7 agents
   - Generate authorization number     - Output: APPROVED/DENIED/MODIFIED
   → Business Decision: APPROVE/DENY   
                                       
10. HUMAN REVIEW ROUTING               hitl-routing-svc
    - Check confidence threshold       - Drools rules engine
    - Route to clinical reviewers      - Rules: confidence < 0.85 → review
    - Assign priority (urgent/routine) - Rules: fraud_risk > 0.30 → review
    → Business Decision: Human review? → review-queue-svc (if needed)
                                       
11. NOTIFICATION                       notification-agent-svc
    - Generate decision letter         - Jinja2 template → WeasyPrint PDF
    - Email provider                   → SendGrid API (email delivery)
    - Update member portal             → WebSocket (real-time notification)
    - Send EDI 278 response            → Azure Blob Storage (PDF storage)
    → Business Process: Complete       
                                       
12. AUDIT & COMPLIANCE                 audit-agent-svc
    - Log all actions                  → Hyperledger Fabric (blockchain)
    - Store decision rationale         → PostgreSQL (audit trail)
    - Generate compliance reports      → Elasticsearch (audit_logs index)
    - Archive documents (7 years)      → Azure Blob Storage (lifecycle management)
    → Regulatory: HIPAA compliance     

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BUSINESS METRICS                       TECHNICAL METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 50,000 PA requests/day               - 55+ microservices running
- $667M annual ROI                     - 6 database systems
- 72% automation rate                  - 500M cache operations/day
- 96% accuracy                         - 50,000 vector searches/day
- 15-min average TAT                   - 47,523 tokens per request
- 28% human review                     - $0.95 LLM cost per request
- 99.95% uptime                        - 38 database queries per request
                                       - 12 LLM calls per request
```

---

## Integration Patterns

### Pattern 1: Synchronous Request-Response (gRPC)

**Use Case**: Low-latency agent-to-service communication

```protobuf
// member-service/proto/member.proto
syntax = "proto3";

package healthinsurance.pa.member;

service MemberService {
  rpc GetMember (GetMemberRequest) returns (MemberResponse);
  rpc CheckEligibility (EligibilityRequest) returns (EligibilityResponse);
  rpc GetMemberClaims (ClaimsRequest) returns (ClaimsResponse);
}

message GetMemberRequest {
  string member_id = 1;
  bool include_dependents = 2;
}

message MemberResponse {
  string member_id = 1;
  string first_name = 2;
  string last_name = 3;
  string dob = 4;
  string plan_id = 5;
  string enrollment_status = 6;
  string enrollment_start = 7;
  string enrollment_end = 8;
  repeated Dependent dependents = 9;
}
```

**Client Code**:
```python
# eligibility-agent-svc calling member-service
async with grpc.aio.insecure_channel('member-service:8500') as channel:
    stub = MemberServiceStub(channel)
    response = await stub.GetMember(
        GetMemberRequest(member_id="M-987654321")
    )
```

---

### Pattern 2: Asynchronous Event-Driven (Kafka)

**Use Case**: Cross-service notifications, audit trail

```python
# Event publisher (workflow-engine-svc)
from aiokafka import AIOKafkaProducer

producer = AIOKafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode()
)

await producer.send(
    topic="pa.case.created",
    key=case_id.encode(),
    value={
        "case_id": case_id,
        "member_id": member_id,
        "provider_npi": provider_npi,
        "timestamp": datetime.utcnow().isoformat(),
        "channel": "web_portal"
    },
    partition=hash(member_id) % 10  # Partition by member_id
)

# Event consumer (analytics-service)
from aiokafka import AIOKafkaConsumer

consumer = AIOKafkaConsumer(
    'pa.case.created',
    'pa.case.completed',
    bootstrap_servers='kafka:9092',
    group_id='analytics-group',
    auto_offset_reset='earliest'
)

async for msg in consumer:
    event = json.loads(msg.value.decode())
    await process_case_event(event)
```

---

### Pattern 3: Batch Processing (ETL)

**Use Case**: Nightly data synchronization, analytics aggregation

```python
# Nightly ETL job: Sync claims from external EDI system
import schedule

@schedule.cron("0 2 * * *")  # 2 AM daily
async def sync_claims_batch():
    logger.info("Starting nightly claims sync")
    
    # Step 1: Extract from external EDI system
    claims = await edi_client.fetch_claims(
        from_date=yesterday(),
        to_date=today()
    )
    logger.info(f"Extracted {len(claims)} claims")
    
    # Step 2: Transform
    transformed = []
    for claim in claims:
        transformed.append({
            'claim_id': claim['claimID'],
            'member_id': map_member_id(claim['subscriberID']),
            'provider_npi': claim['providerNPI'],
            'service_date': parse_date(claim['serviceDate']),
            'diagnosis_codes': claim['diagnosisCodes'],
            'procedure_codes': claim['procedureCodes'],
            'billed_amount': Decimal(claim['billedAmount'])
        })
    
    # Step 3: Load into PostgreSQL (batch insert)
    async with db_pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO claims (
                claim_id, member_id, provider_npi, service_date,
                diagnosis_codes, procedure_codes, billed_amount
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (claim_id) DO UPDATE
            SET billed_amount = EXCLUDED.billed_amount
            """,
            [(c['claim_id'], c['member_id'], ...) for c in transformed]
        )
    
    logger.info(f"Loaded {len(transformed)} claims to database")
```

---

## Performance & Scaling

### Horizontal Scaling Configuration

| Service | Min Replicas | Max Replicas | CPU/Pod | Memory/Pod | Auto-Scale Trigger |
|---------|--------------|--------------|---------|------------|-------------------|
| web-portal-svc | 3 | 10 | 0.5 cores | 1 GB | CPU > 70% |
| workflow-engine-svc | 5 | 20 | 2 cores | 4 GB | Queue depth > 100 |
| intake-agent-svc | 10 | 30 | 1 core | 2 GB | Request rate > 50/s |
| clinical-agent-svc | 15 | 40 | 4 cores | 8 GB | GPU util > 60% |
| member-service | 5 | 15 | 1 core | 2 GB | CPU > 60% |
| vector-search-svc | 3 | 10 | 2 cores | 4 GB | Query latency > 100ms |

### Database Scaling Strategy

| Database | Strategy | Current | Max Capacity |
|----------|----------|---------|--------------|
| PostgreSQL | Read replicas (2), vertical scaling | 6 TB | 50 TB |
| Redis | Cluster mode (3 shards), horizontal scaling | 26 GB | 120 GB |
| Milvus | Horizontal (8 data nodes → 32 nodes) | 1.2 TB | 10 TB |
| Neo4j | Causal cluster (3 core + 2 read replicas) | 200 GB | 2 TB |
| Elasticsearch | Node addition (6 → 12 nodes) | 400 GB | 5 TB |

### AKS Cluster Configuration

```yaml
# Azure Kubernetes Service
apiVersion: v1
kind: Cluster
metadata:
  name: pa-healthcare-aks-prod
  region: eastus2
spec:
  kubernetesVersion: "1.28"
  
  nodePools:
    # System node pool (control plane workloads)
    - name: system
      mode: System
      vmSize: Standard_D4s_v5
      count: 3
      minCount: 3
      maxCount: 5
      
    # General workload node pool
    - name: general
      mode: User
      vmSize: Standard_D8s_v5
      count: 10
      minCount: 5
      maxCount: 30
      enableAutoScaling: true
      
    # GPU node pool (for clinical agent with image processing)
    - name: gpu
      mode: User
      vmSize: Standard_NC6s_v3  # Tesla V100
      count: 2
      minCount: 2
      maxCount: 8
      enableAutoScaling: true
      
  networking:
    networkPlugin: azure
    networkPolicy: calico
    serviceCIDR: 10.0.0.0/16
    dnsServiceIP: 10.0.0.10
    
  ingress:
    class: azure/application-gateway
    gateway: pa-appgw-prod
```

### Load Balancing

```yaml
# Azure Application Gateway (Layer 7)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pa-platform-ingress
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/backend-protocol: https
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
    appgw.ingress.kubernetes.io/connection-draining: "true"
    appgw.ingress.kubernetes.io/connection-draining-timeout: "30"
spec:
  tls:
    - hosts:
        - api.pahealthcare.com
      secretName: tls-secret
  rules:
    - host: api.pahealthcare.com
      http:
        paths:
          - path: /api/v1/pa/*
            pathType: Prefix
            backend:
              service:
                name: workflow-engine-svc
                port:
                  number: 8010
          - path: /api/v1/members/*
            pathType: Prefix
            backend:
              service:
                name: member-service
                port:
                  number: 8500
```

---

## Appendix: Latency Budget

### End-to-End Latency Breakdown (15-minute average)

| Phase | Services Involved | Duration | % of Total |
|-------|------------------|----------|------------|
| Intake | intake-agent (OCR + LLM) | 2 min | 13% |
| Eligibility | eligibility-agent + member-service | 15 sec | 2% |
| Benefits | benefits-agent + 3 data services | 20 sec | 2% |
| **Clinical RAG** | **clinical-agent + 4 databases** | **8 min** | **53%** |
| Policy | policy-agent + elasticsearch | 2.5 min | 17% |
| Fraud | fraud-agent + neo4j | 45 sec | 5% |
| Decision | decision-agent | 30 sec | 3% |
| Notification | notification-agent | 1 min | 5% |
| **Total** | | **~15 min** | **100%** |

**Primary Bottleneck**: Clinical Agent RAG retrieval (53% of total time)

**Optimization Strategies**:
1. Pre-index common diagnosis-procedure pairs (50K most frequent)
2. Cache frequently accessed guidelines in Redis (top 1,000)
3. Parallel execution of vector/BM25/graph searches (already implemented)
4. Upgrade Milvus HNSW index parameters (M=32, efConstruction=400)

---

## Related Documentation

- [Business Architecture](01-Business-Architecture.md) - Business case, ROI, workflows
- [Enterprise Solution Architecture](02-Enterprise-Solution-Architecture.md) - 10-layer architecture
- [Agentic AI Platform Architecture](03-Agentic-AI-Platform-Architecture.md) - Agent details, RAG
- [Security & Compliance](04-Enterprise-Security-Governance-Compliance.md) - Zero Trust, ISO 42001
- [Deployment & Operations](05-Deployment-Operations-Runbook.md) - IaC, CI/CD, evaluation
- [Agent Documentation](../agents/README.md) - Individual agent deep-dives
- [Service Documentation](../services/README.md) - Data service APIs
- [PlantUML Diagrams](../plantuml/README.md) - Visual architecture

---

**Document End**  
*For questions or clarifications, contact: platform-architecture@healthinsurance.com*
