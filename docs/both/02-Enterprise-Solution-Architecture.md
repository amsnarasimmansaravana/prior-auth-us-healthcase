---
title: 02 Enterprise Solution Architecture
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Enterprise Healthcare Insurance Multi-Agent AI Platform
## Part 2: Enterprise Solution Architecture

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Enterprise Reference Architecture](#enterprise-reference-architecture)
3. [Architecture Layers](#architecture-layers)
4. [Agent Architecture](#agent-architecture)
5. [Multi-Agent Orchestration](#multi-agent-orchestration)
6. [Enterprise Integration Architecture](#enterprise-integration-architecture)
7. [Data Architecture](#data-architecture)
8. [Infrastructure Architecture](#infrastructure-architecture)
9. [Technology Stack](#technology-stack)
10. [Architecture Patterns](#architecture-patterns)

---

## Architecture Overview

### Executive Architecture Summary

The Enterprise Healthcare Insurance Multi-Agent AI Platform is a cloud-native, event-driven, microservices-based system that uses specialized AI agents orchestrated through a supervisor pattern to automate prior authorization and claims processing while maintaining human oversight, regulatory compliance, and clinical safety.

### Architecture Principles

1. **Business-First**: Every architectural decision serves business objectives
2. **Compliance-Native**: HIPAA, CMS, NCQA requirements embedded in design
3. **Human-Centric**: AI augments, not replaces, clinical judgment
4. **Explainable**: Every decision fully traceable and auditable
5. **Scalable**: Handle 3x peak load with auto-scaling
6. **Resilient**: 99.9% uptime with multi-region failover
7. **Secure**: Defense in depth, zero trust architecture
8. **Modular**: Loosely coupled, independently deployable services

### Architecture Goals

| Goal | Measure |
|------|---------|
| Performance | <30 min average TAT, 50K+ PAs/day |
| Availability | 99.9% uptime |
| Scalability | 3x peak load capacity |
| Security | Zero HIPAA violations |
| Compliance | 100% audit pass rate |
| Automation | 80% auto-adjudication |
| Accuracy | 96%+ clinical accuracy |
| Explainability | 100% decisions with rationale |

---

## Enterprise Reference Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHANNEL LAYER                                 │
│  Provider Portal │ API │ EDI │ FHIR │ Fax OCR │ Mobile │ IVR   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                API GATEWAY & SECURITY LAYER                      │
│  Kong/Apigee │ WAF │ OAuth2 │ Rate Limiting │ mTLS │ OPA       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                             │
│  Multi-Agent Orchestrator │ Temporal │ LangGraph │ Event Bus    │
│  SLA Engine │ Workflow Engine │ Agent-to-Agent Protocol         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT FABRIC                                  │
│  Intake │ Eligibility │ Benefits │ Clinical │ Policy │ Fraud    │
│  Decision │ Appeals │ COM │ Notification │ Audit                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                 AGENT GOVERNANCE PLATFORM                        │
│  Agent Registry │ Prompt Registry │ Model Governance             │
│  Safety Policies │ Runtime Guardrails │ Agent RBAC               │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│               MCP + TOOL DISCOVERY LAYER                         │
│  Tool Registry │ Capability Routing │ Tool Governance            │
│  Schema Validation │ Version Management │ Tool Telemetry         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                 MEMORY + KNOWLEDGE LAYER                         │
│  Vector DB (Milvus) │ Knowledge Graph (Neo4j)                   │
│  Working Memory (Redis) │ Episodic Memory (PostgreSQL)          │
│  Semantic Cache │ Context Management                             │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  RAG ARCHITECTURE                                │
│  Document Store │ Chunking │ Embeddings │ Hybrid Search         │
│  Reranking │ Context Compression │ Citation Engine              │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   DATA SERVICES LAYER                            │
│  Member Service │ Provider Service │ Policy Service │ Claims    │
│  Benefits Config │ Network │ Formulary │ Clinical Content       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   HUMAN-IN-THE-LOOP LAYER                        │
│  Reviewer UI │ Case Assignment │ Escalation Engine              │
│  Peer Review │ Appeals │ QA │ Audit Workbench                   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                EVENT-DRIVEN BACKBONE                             │
│  Kafka │ Schema Registry │ Event Store │ Dead Letter Queue      │
│  Event Replay │ CQRS │ Event Sourcing                           │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│             OBSERVABILITY & AI SAFETY LAYER                      │
│  OpenTelemetry │ LangSmith │ Prometheus │ Grafana │ ELK         │
│  Guardrails │ PHI Detection │ Hallucination Detection │ SIEM    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                    │
│  PostgreSQL │ Redis │ Milvus │ Neo4j │ Blob Storage             │
│  Data Warehouse │ Data Lake │ Backup & Archive                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### 1. Channel Layer

**Purpose**: Multi-channel request intake and normalization

**Components:**
- **Provider Portal**: Web-based submission interface
- **API Gateway**: RESTful and FHIR R4 APIs
- **EDI Processor**: X12 278 (PA), 837 (Claims)
- **Fax Server**: OCR and document extraction
- **Mobile App**: Provider mobile interface
- **IVR**: Phone-based intake with speech-to-text

**Key Capabilities:**
- Protocol translation (EDI → Internal format)
- Document OCR and extraction
- Request validation
- Member/Provider identification
- Case creation and routing

**Technologies:**
- **Portal**: React, Next.js
- **EDI**: X12 Parser libraries
- **OCR**: Azure Form Recognizer, Google Document AI
- **FHIR**: HAPI FHIR Server
- **IVR**: Twilio, Azure Communication Services

---

### 2. Enterprise Gateway Architecture

**Purpose**: Comprehensive gateway taxonomy for enterprise AI systems

**Architecture Philosophy**: Modern enterprise AI platforms require **multiple specialized gateways** working in concert, not a single monolithic gateway. Each gateway serves a distinct architectural layer with specific responsibilities.

---

#### Enterprise Gateway Taxonomy - 10 Types

##### 1. AI Gateway (Application Layer)

**Purpose**: Multi-model orchestration and cost optimization

**Responsibilities:**
- Multi-LLM routing (GPT-4o, Claude 3.5, Llama 3, Gemini)
- Load balancing across model instances
- Cost optimization (route simple queries to cheap models)
- Rate limiting per tenant
- Failover and retry strategies
- Token tracking and budgeting

**Flow Diagram:**
```
User Request
    ↓
[Route Decision Engine]
    ├→ Simple query (complexity < 0.3) → Llama 3 ($0.02)
    ├→ Medium query (0.3 - 0.7) → GPT-3.5 Turbo ($0.05)
    └→ Complex query (> 0.7) → GPT-4o ($0.30)
    ↓
[Load Balancer]
    ├→ Instance 1 (if available)
    ├→ Instance 2 (if Instance 1 busy)
    └→ Failover Region (if primary region down)
    ↓
Response + Cost Tracking
```

**Technologies**: Portkey, Kong AI Gateway, LiteLLM, Azure APIM, OpenRouter

**Example Configuration:**
```
Routing Rules:
  - FAQ queries → GPT-3.5 Turbo
  - Clinical reviews → GPT-4o
  - Code generation → Claude 3.5
  - High-priority requests → Dedicated instances
  - Budget exceeded → Rate limit or downgrade model
```

---

##### 2. Security Gateway (Security Layer)

**Purpose**: Protection against AI-specific threats (often called "LLM Firewall")

**Responsibilities:**
- **Input Protection:**
  - Prompt injection detection ("Ignore all previous instructions...")
  - Jailbreak prevention
  - Adversarial prompt detection
  
- **Data Protection:**
  - PHI/PII detection and masking
  - SSN/Credit card detection
  - HIPAA-sensitive data redaction
  
- **Content Protection:**
  - Toxicity filtering
  - Hate speech detection
  - Violence/abuse prevention
  
- **Output Validation:**
  - PHI leakage prevention
  - Hallucination detection
  - Policy compliance enforcement

**Flow Diagram:**
```
User Prompt: "Show me patient records for John Smith"
    ↓
[Input Scanner]
    ├→ Detect: Patient name (PII)
    ├→ Action: Mask → "Show me patient records for [REDACTED]"
    ↓
[Threat Detection]
    ├→ Prompt injection? NO
    ├→ Jailbreak attempt? NO
    ├→ Policy violation? NO
    ↓
[Send to LLM]
    ↓
LLM Response: "Here is the data for patient ID 123456..."
    ↓
[Output Scanner]
    ├→ PHI leaked? YES (patient ID)
    ├→ Action: Block or mask
    ↓
Final Response: "I cannot share identifiable patient information"
```

**Technologies**: Lakera AI, Protect AI, NVIDIA NeMo Guardrails, Azure AI Content Safety, Guardrails AI

---

##### 3. Agent Gateway (Agent Orchestration Layer)

**Purpose**: Agent-to-agent communication management

**Responsibilities:**
- Agent discovery and registration
- Agent routing and load balancing
- Agent versioning and blue/green deployment
- Agent health monitoring
- A2A (Agent-to-Agent) protocol enforcement
- Agent mesh coordination

**Flow Diagram:**
```
Source Agent: "I need benefits verification"
    ↓
[Agent Registry Lookup]
    ├→ Query: Which agent handles benefits?
    ├→ Response: Benefits Agent v2.1.0
    ↓
[Load Balancer]
    ├→ Replica 1 (80% capacity) → SELECT
    ├→ Replica 2 (60% capacity)
    ├→ Replica 3 (90% capacity)
    ↓
[Health Check]
    ├→ Is agent healthy? YES
    ├→ Version compatible? YES
    ↓
[Route Request]
    ↓
Benefits Agent → Process → Return Result
    ↓
[Telemetry]
    ├→ Log: Agent call successful
    ├→ Metrics: Latency 250ms
    └→ Trace: Update distributed trace
```

**Technologies**: Custom Kong/Apigee extensions, Dapr, Istio, Consul

---

##### 4. MCP Gateway (Tool Layer)

**Purpose**: Model Context Protocol tool discovery and governance

**Responsibilities:**
- Tool registry and metadata management
- Tool capability routing
- Tool authentication (OAuth, service accounts, API keys)
- Permission control (RBAC for tools)
- Tool usage auditing
- Schema validation
- Version management

**Flow Diagram:**
```
Agent: "I need to check MCG guidelines"
    ↓
[Tool Discovery]
    ├→ Query Registry: Tools with "guidelines" capability
    ├→ Results: [MCG Tool v1.2, InterQual Tool v2.0]
    ↓
[Permission Check]
    ├→ Does Clinical Agent have access to MCG? YES
    ├→ Is tool in approved list? YES
    ↓
[Authentication]
    ├→ Retrieve OAuth token for MCG
    ├→ Validate service account
    ↓
[Schema Validation]
    ├→ Validate request parameters
    ├→ Check required fields
    ↓
[Execute Tool]
    ↓
[Audit Log]
    └→ Record: Agent X called MCG Tool at timestamp
```

**Technologies**: MCP servers, Custom tool registry, HashiCorp Vault (secrets)

---

##### 5. LLM Gateway (Model Layer)

**Purpose**: LLM request/response management with semantic routing

**Responsibilities:**
- Model selection based on task type
- Prompt template management
- Fallback strategies (primary model down → backup)
- Latency optimization (caching)
- Cost per query tracking
- A/B testing support

**Flow Diagram:**
```
Request: Clinical review task
    ↓
[Task Classifier]
    ├→ Type: Clinical reasoning
    ├→ Complexity: High
    ├→ Required accuracy: >95%
    ↓
[Model Selection]
    ├→ Primary: GPT-4o (accuracy 96%)
    ├→ Fallback: Claude 3.5 (accuracy 95%)
    ↓
[Cache Check]
    ├→ Similar query in last 1 hour? NO
    ↓
[Send to LLM]
    ↓
[Retry Logic]
    ├→ Timeout? Retry
    ├→ Error? Try fallback model
    ↓
Response + Metadata (model used, tokens, cost)
```

**Technologies**: LiteLLM, Portkey, OpenRouter, Helicone

---

##### 6. Human Approval Gateway (HITL Layer)

**Purpose**: Mandatory human oversight for high-risk decisions

**Responsibilities:**
- Risk-based routing
- Approval workflow management
- Escalation rules
- SLA enforcement for reviews
- Override tracking and audit

**Flow Diagram:**
```
AI Decision: Approve $150,000 surgery PA
    ↓
[Risk Assessment]
    ├→ Amount: $150,000 (HIGH)
    ├→ Confidence: 78% (MEDIUM)
    ├→ Medical necessity: Complex case
    ↓
[Routing Decision]
    ├→ Risk Score: 0.85 (HIGH)
    ├→ Action: Require human approval
    ↓
[Assign Reviewer]
    ├→ Queue: Senior Clinical Reviewer
    ├→ SLA: 4 hours
    ↓
[Human Review]
    ├→ Reviewer: Dr. Smith
    ├→ Decision: Approve with modifications
    ├→ Override: Changed from full approval to partial
    ↓
[Audit Trail]
    └→ Log: AI recommended X, Human decided Y, Reason: Z
```

**Decision Rules:**
| Risk Level | Action |
|------------|--------|
| Low (< 0.4) | Auto-execute |
| Medium (0.4 - 0.75) | Supervisor review |
| High (0.75 - 0.9) | Senior approval required |
| Critical (> 0.9) | Multi-reviewer + Governance board |

**Technologies**: ServiceNow, Jira, Custom workflow engine

---

##### 7. Data Gateway (Data Security Layer)

**Purpose**: Secure enterprise data access with fine-grained controls

**Responsibilities:**
- Row-level security (RLS)
- Column-level masking
- Data lineage tracking
- Audit logging
- SQL injection prevention
- Query optimization

**Flow Diagram:**
```
Agent Query: SELECT * FROM patients WHERE id = 123456
    ↓
[Permission Check]
    ├→ Agent: Fraud Detection Agent
    ├→ Table: patients
    ├→ Allowed? YES (but restricted columns)
    ↓
[Row-Level Security]
    ├→ Apply filter: WHERE organization_id = agent_org_id
    ↓
[Column Masking]
    ├→ SSN → MASKED
    ├→ Home Address → MASKED
    ├→ Medical history → ALLOWED
    ↓
[Execute Query]
    ↓
[Audit Log]
    └→ Log: Agent accessed patient table, columns viewed: [...]
```

**Technologies**: PostgreSQL RLS, OPA policies, HashiCorp Boundary

---

##### 8. Vector Gateway (RAG Layer)

**Purpose**: Vector database access control and hybrid retrieval coordination

**Responsibilities:**
- Semantic search routing
- Metadata filtering
- Multi-vector database coordination
- Hybrid retrieval (BM25 + vector)
- Re-ranking coordination
- Cache management

**Flow Diagram:**
```
Query: "What are MCG criteria for knee replacement?"
    ↓
[Embedding Generation]
    ├→ Model: bge-large-en-v1.5
    ├→ Vector: [0.234, 0.567, ...]
    ↓
[Metadata Filters]
    ├→ Source: MCG guidelines
    ├→ Date: Last 12 months
    ├→ Category: Orthopedic
    ↓
[Hybrid Search]
    ├→ Vector Search (top 100 semantic matches)
    ├→ BM25 Search (top 100 keyword matches)
    ├→ Combine with RRF (Reciprocal Rank Fusion)
    ↓
[Re-ranking]
    ├→ Model: cross-encoder/ms-marco
    ├→ Top 10 results
    ↓
[Context Assembly]
    └→ Return top 5 chunks with metadata + citations
```

**Technologies**: Milvus gateway, Pinecone, Weaviate, Qdrant

---

##### 9. Workflow Gateway (Orchestration Layer)

**Purpose**: Multi-step workflow execution and state management

**Responsibilities:**
- Workflow state persistence
- Long-running process management
- Retry and compensation logic
- Checkpointing
- Saga pattern implementation
- Timeout handling

**Flow Diagram:**
```
PA Workflow Start
    ↓
[State: Step 1 - Intake]
    ├→ Execute
    ├→ Success? YES
    ├→ Save checkpoint
    ↓
[State: Step 2 - Eligibility]
    ├→ Execute
    ├→ Failed? YES
    ↓
[Retry Logic]
    ├→ Attempt 1: Failed
    ├→ Attempt 2: Failed
    ├→ Attempt 3: Success
    ├→ Save checkpoint
    ↓
[State: Step 3 - Clinical Review]
    ├→ Execute
    ├→ Timeout (> 5 min)
    ↓
[Compensation]
    ├→ Rollback eligibility check
    ├→ Mark workflow as failed
    ↓
[Audit]
    └→ Log full workflow state for debugging
```

**Technologies**: Temporal, Camunda, Apache Airflow, Step Functions

---

##### 10. Observability Gateway (Monitoring Layer)

**Purpose**: Comprehensive monitoring, tracing, and cost attribution

**Responsibilities:**
- Request/response logging
- Token usage tracking
- Latency measurement (TTFT, end-to-end)
- Error rate monitoring
- Cost attribution per tenant/workflow
- Distributed tracing

**Flow Diagram:**
```
Request arrives
    ↓
[Generate Trace ID]
    ├→ trace_id: abc-123
    ├→ span_id: span-456
    ↓
[Log Request]
    ├→ Timestamp
    ├→ User/Agent ID
    ├→ Request payload (sanitized)
    ↓
[Track Execution]
    ├→ AI Gateway call → 200ms
    ├→ Vector DB call → 150ms
    ├→ LLM call → 3000ms
    ├→ Total latency → 3350ms
    ↓
[Track Cost]
    ├→ LLM tokens: 8,500 ($0.30)
    ├→ Vector search: $0.02
    ├→ Total: $0.32
    ↓
[Export Metrics]
    ├→ Prometheus: Latency, error rate, throughput
    ├→ Langfuse: LLM traces, token usage
    ├→ OpenTelemetry: Distributed traces
    ↓
[Dashboards]
    └→ Grafana: Real-time monitoring
```

**Technologies**: OpenTelemetry, Langfuse, LangSmith, Prometheus, Grafana, Datadog

---

#### Gateway Coordination Architecture

**Production Deployment Flow:**

```
External User
    ↓
┌─────────────────────────────────────┐
│ LAYER 1: Security Gateway           │ ← Input Protection
│ (Lakera AI, NeMo Guardrails)        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ LAYER 2: AI Gateway                 │ ← Routing & Load Balancing
│ (Portkey, Kong AI)                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ LAYER 3: Agent Gateway              │ ← Agent Discovery
│ (Custom Kong/Apigee)                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ LAYER 4: Workflow Gateway           │ ← Orchestration
│ (Temporal)                          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ LAYER 5: Agent Execution            │
│   ↓                                 │
│   MCP Gateway → Tools               │
│   Vector Gateway → RAG              │
│   Data Gateway → Databases          │
│   LLM Gateway → Models              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ LAYER 6: Human Approval Gateway     │ ← HITL if needed
│ (ServiceNow)                        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ LAYER 7: Security Gateway           │ ← Output Protection
│ (Output Validation)                 │
└─────────────────────────────────────┘
    ↓
Response to User

[Observability Gateway monitors ALL layers]
```

---

#### Gateway vs Firewall - Critical Distinction

| Aspect | Gateway | Firewall |
|--------|---------|----------|
| **Purpose** | Traffic Management & Routing | Security Enforcement & Protection |
| **Layer** | Application/Orchestration | Security/Compliance |
| **Focus** | Efficiency, Optimization | Risk Mitigation, Policy Enforcement |
| **Examples** | AI Gateway, Agent Gateway | Security Gateway, Agent Firewall |
| **Deployment** | Between architectural layers | Protection boundary |
| **Users** | Platform Engineers | Security Teams |

**Both are necessary**: Modern enterprise AI requires **gateways for operational efficiency** AND **firewalls for security/compliance**. They complement each other.

---

**Legacy Section (Basic API Gateway):**

#### API Gateway (Core)
- Request routing
- Protocol translation
- Rate limiting (1000 req/min per client)
- API versioning
- Request/response transformation

#### Web Application Firewall (WAF)
- OWASP Top 10 protection
- SQL injection prevention
- XSS protection
- Bot detection

#### Authentication & Authorization
- OAuth 2.0 / OpenID Connect
- JWT token validation
- Multi-factor authentication (MFA)
- SAML federation

#### Policy Engine (OPA)
- Runtime authorization
- Attribute-based access control (ABAC)
- Policy-as-code
- Dynamic policy updates

**Core Technologies:**
- **API Gateway**: Kong, Apigee, Azure API Management
- **WAF**: Azure WAF, AWS WAF
- **Auth**: Azure AD, Okta, Auth0
- **Policy**: Open Policy Agent (OPA)
- **mTLS**: Istio service mesh

---

### 3. Orchestration Layer

**Purpose**: Multi-agent coordination, workflow management, SLA enforcement

#### Multi-Agent Orchestrator (LangGraph Supervisor)

**Responsibilities:**
- Agent task assignment
- Parallel agent execution
- Agent-to-agent communication
- Result aggregation
- Error handling and retry
- Circuit breaking

**Orchestration Patterns:**

##### Centralized Orchestration
```
Supervisor Agent
       │
       ├──► Eligibility Agent
       ├──► Benefits Agent
       ├──► Clinical Agent
       ├──► Policy Agent
       ├──► Fraud Agent
       └──► Decision Agent
```

##### Event-Driven Choreography
```
PA Intake Event
    │
    ├──► Eligibility Agent ──► Eligibility Complete Event
    │                                │
    │                                ▼
    ├──► Benefits Agent ──────► Benefits Complete Event
    │                                │
    └──► (Parallel execution)         ▼
                              Clinical Agent triggers
```

##### Hybrid Model
```
Supervisor orchestrates:
  - Deterministic workflows (eligibility → benefits → clinical)
  
Events trigger:
  - Fraud detection (parallel)
  - SLA monitoring (continuous)
  - Audit logging (async)
```

#### Workflow Engine (Temporal)

**Capabilities:**
- Durable execution
- Saga pattern for distributed transactions
- Long-running workflows (appeals can take 90 days)
- Workflow versioning
- Retry and timeout policies
- Human task integration

**Example PA Workflow:**

**Temporal Workflow Execution Flow:**
```
PA Request Received: PARequest(case_id="PA_12345", member_id="M789")
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Intake Activity (Timeout: 5 minutes)               │
└─────────────────────────────────────────────────────────────┘
    ├─ Activity: intake_activity(request)
    ├─ Processing:
    │   ├─ Extract documents from request
    │   ├─ OCR and classification
    │   ├─ Create case record
    │   └─ Generate case_id
    └─ Output: Case object (case_id, member_id, diagnosis, procedure)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Parallel Execution - Eligibility & Fraud Check      │
└─────────────────────────────────────────────────────────────┘
    ├─ Thread 1: check_eligibility(case)
    │   ├─ Query member database
    │   ├─ Verify active enrollment
    │   └─ Result: eligibility.is_eligible = True/False
    │
    └─ Thread 2: fraud_check(case)
        ├─ Anomaly detection
        ├─ Pattern matching
        └─ Result: fraud_score = 0.12 (Low risk)
    ↓
[Both Complete - Async Gather Results]
    ↓
[Decision Point: Check Eligibility]
    ├─ IF not eligibility.is_eligible:
    │   └─ RETURN: PADecision(
    │         status="DENIED",
    │         reason="NOT_ELIGIBLE",
    │         timestamp="2026-06-01T10:30:00Z"
    │       )
    │       ↓
    │   [END WORKFLOW] ✗
    │
    └─ ELSE (Member IS eligible):
        ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Benefits Check Activity                             │
└─────────────────────────────────────────────────────────────┘
    ├─ Activity: check_benefits(case)
    ├─ Processing:
    │   ├─ Query benefit configuration
    │   ├─ Check procedure coverage
    │   └─ Verify prior auth requirements
    └─ Output: benefits object (is_covered, limitations, exclusions)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Clinical Review - Risk-Based Routing                │
└─────────────────────────────────────────────────────────────┘
    ↓
[Decision Point: Risk Score]
    ├─ IF case.risk_score > 0.8 (HIGH RISK):
    │   ↓
    │   [Route to HUMAN Review]
    │   ├─ Activity: human_review_activity(case)
    │   ├─ Timeout: 24 hours
    │   ├─ Assigned to: Clinical Nurse Reviewer
    │   ├─ Processing:
    │   │   ├─ Manual chart review
    │   │   ├─ MCG guideline consultation
    │   │   ├─ Peer-to-peer if needed
    │   │   └─ Document clinical rationale
    │   └─ Output: review object (decision, rationale)
    │
    └─ ELSE case.risk_score ≤ 0.8 (STANDARD/LOW RISK):
        ↓
        [Route to AI Review]
        ├─ Activity: ai_clinical_review(case)
        ├─ Processing:
        │   ├─ RAG retrieval (MCG guidelines)
        │   ├─ LLM evaluation (GPT-4o)
        │   ├─ Medical necessity scoring
        │   └─ Generate clinical summary
        └─ Output: review object (decision, confidence, evidence)
    ↓
[Both Paths Converge]
    ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Final Decision Activity                             │
└─────────────────────────────────────────────────────────────┘
    ├─ Activity: make_decision(review)
    ├─ Processing:
    │   ├─ Aggregate all prior results
    │   ├─ Apply business rules
    │   ├─ Generate decision document
    │   └─ Prepare notifications
    └─ Output: decision object
    ↓
RETURN: PADecision(
    status="APPROVED",
    case_id="PA_12345",
    clinical_rationale="...",
    approved_quantity="30 days",
    authorization_number="AUTH_67890"
)
    ↓
[END WORKFLOW] ✓
```

**Workflow Characteristics:**
- **Durability**: State persisted across failures
- **Timeouts**: Each activity has SLA enforcement
- **Compensation**: Failed steps trigger rollback activities
- **Versioning**: Workflow code versioned independently

#### SLA Engine

**Responsibilities:**
- SLA calculation based on urgency
- Countdown timers
- Escalation triggers
- Priority queue management

**SLA Rules Configuration:**

**Case Priority & SLA Timers:**
```
┌──────────────────────────────────────────────────────────────┐
│ URGENT CASES (e.g., Emergency procedures, Hospitalizations) │
└──────────────────────────────────────────────────────────────┘
    ↓
[Timer Starts at Case Creation]
    ↓
├─ 0 hours → [Case Created] - Countdown begins
├─ 18 hours → [WARNING Threshold]
│   ├─ Alert: Case manager notified
│   ├─ Action: Priority flag updated
│   └─ Dashboard: Yellow indicator
├─ 22 hours → [ESCALATION Threshold]
│   ├─ Alert: Management notification
│   ├─ Action: Assign additional reviewer
│   ├─ Dashboard: Red indicator
│   └─ Auto-action: Consider auto-approval if risk_score < 0.3
└─ 24 hours → [TARGET Deadline]
    ├─ IF completed: SUCCESS ✓
    └─ IF not completed: BREACH ✗
        ├─ Incident logged
        ├─ Root cause analysis triggered
        └─ Compliance report updated

┌──────────────────────────────────────────────────────────────┐
│ STANDARD CASES (e.g., Elective procedures, DME requests)    │
└──────────────────────────────────────────────────────────────┘
    ↓
[Timer Starts at Case Creation]
    ↓
├─ 0 hours → [Case Created] - Countdown begins
├─ 48 hours → [WARNING Threshold]
│   ├─ Alert: Case manager review
│   ├─ Action: Queue priority adjustment
│   └─ Dashboard: Yellow indicator
├─ 60 hours → [ESCALATION Threshold]
│   ├─ Alert: Supervisor notification
│   ├─ Action: Additional resources assigned
│   ├─ Dashboard: Red indicator
│   └─ Auto-action: Expedite clinical review
└─ 72 hours → [TARGET Deadline]
    ├─ IF completed: SUCCESS ✓
    └─ IF not completed: BREACH ✗
        ├─ Incident logged
        ├─ Performance metrics updated
        └─ State compliance report filed
```

**Escalation Action Workflow:**
```
Escalation Triggered (22 hours for Urgent, 60 hours for Standard)
    ↓
[Automatic Actions]
    ├─ Step 1: Priority Boost
    │   ├─ Queue position: Move to top
    │   ├─ Flag: Set ESCALATED status
    │   └─ SLA: Reduce remaining time by 20%
    │
    ├─ Step 2: Assign Additional Reviewers
    │   ├─ Find available senior reviewer
    │   ├─ Duplicate assignment (parallel review)
    │   └─ Notification: "Escalated case assigned"
    │
    ├─ Step 3: Notify Management
    │   ├─ Email: Director of Clinical Operations
    │   ├─ Dashboard: Add to escalation report
    │   └─ Slack: #pa-escalations channel
    │
    └─ Step 4: Conditional Auto-Approval Check
        ↓
        [Risk-Based Decision]
        ├─ IF clinical_risk_score < 0.3 (LOW):
        │   ├─ AND procedure_cost < $5,000
        │   └─ AND no prior denials:
        │       ↓
        │       [AUTO-APPROVE]
        │       ├─ Decision: APPROVED
        │       ├─ Reason: "Auto-approved due to escalation + low risk"
        │       ├─ Audit: Log auto-approval event
        │       └─ Notification: Send approval to provider
        │
        └─ ELSE (Medium/High risk OR expensive):
            ├─ Maintain ESCALATED status
            └─ Require human review (no auto-approval)
```

#### Agent-to-Agent (A2A) Protocol

**Purpose**: Standardized communication between agents

**A2A Message Structure & Flow:**

**Message Communication Example:**
```
Scenario: Clinical Agent sends review results to Decision Agent
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Message Construction (Clinical Agent)                       │
└─────────────────────────────────────────────────────────────┘
    ↓
[Message Envelope]
    ├─ message_id: "msg_123" (Unique identifier)
    ├─ from_agent: "clinical_agent" (Sender)
    ├─ to_agent: "decision_agent" (Recipient)
    ├─ timestamp: "2026-06-01T10:30:00Z" (ISO 8601)
    ├─ correlation_id: "case_PA_456" (Case tracker)
    └─ message_type: "clinical_review_complete" (Event type)
    ↓
[Message Payload - Clinical Review Results]
    ├─ case_id: "PA_456"
    ├─ clinical_summary: "Patient meets MCG criteria for knee
    │                     replacement: Failed 6 months conservative
    │                     therapy, severe osteoarthritis confirmed
    │                     via X-ray, no contraindications."
    ├─ medical_necessity: "APPROVED" (Decision)
    ├─ confidence: 0.96 (96% confidence score)
    ├─ supporting_evidence:
    │   ├─ [1] "MCG_Guideline_123" (Knee replacement criteria)
    │   └─ [2] "CMS_LCD_456" (Local coverage determination)
    └─ clinical_findings:
        ├─ diagnosis_codes: ["M17.11", "M25.561"]
        ├─ procedure_code: "27447"
        ├─ failed_treatments: ["PT", "NSAIDs", "Injections"]
        └─ imaging_results: "Severe joint space narrowing"
    ↓
[Message Metadata - Traceability]
    ├─ agent_version: "v2.3.1" (Agent software version)
    ├─ model_version: "gpt-4o-2024" (LLM model used)
    ├─ prompt_version: "v1.5" (Prompt template version)
    ├─ execution_time_ms: 3400 (Processing duration)
    └─ trace_id: "trace_abc123" (OpenTelemetry trace)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Message Transmission (via Agent Gateway)                    │
└─────────────────────────────────────────────────────────────┘
    ├─ Step 1: Validate message schema
    ├─ Step 2: Route to destination agent
    ├─ Step 3: Log to audit trail
    └─ Step 4: Track delivery confirmation
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Message Receipt (Decision Agent)                            │
└─────────────────────────────────────────────────────────────┘
    ├─ Verify correlation_id matches case
    ├─ Extract payload and metadata
    ├─ Process clinical review results
    └─ Proceed to final decision logic
    ↓
[Decision Agent Processing]
    ├─ Input: Clinical review (APPROVED, 0.96 confidence)
    ├─ Input: Eligibility (ELIGIBLE)
    ├─ Input: Benefits (COVERED)
    ├─ Input: Fraud check (0.12 score - low)
    └─ Output: Final decision (APPROVED)
```

**A2A Protocol Benefits:**
- **Decoupling**: Agents evolve independently
- **Traceability**: Full audit trail via correlation_id + trace_id
- **Versioning**: Metadata tracks agent/model/prompt versions
- **Reliability**: Message queue ensures delivery
- **Schema Validation**: Enforced contract between agents

**Technologies:**
- **Orchestrator**: LangGraph, CrewAI, AutoGen
- **Workflow**: Temporal, Cadence, Apache Airflow
- **Messaging**: Azure Service Bus, RabbitMQ
- **State Management**: Redis, etcd

---

### 4. Agent Fabric

**Purpose**: Specialized AI agents for domain-specific tasks

#### Agent Catalog

| Agent | Purpose | Model | Tools |
|-------|---------|-------|-------|
| Intake Agent | Document classification, extraction | GPT-4o | OCR, NER, Document AI |
| Eligibility Agent | Enrollment verification | GPT-3.5 Turbo | Member API, EDI 270/271 |
| Benefits Agent | Coverage determination | GPT-3.5 Turbo | Benefit Config API |
| Clinical Agent | Medical necessity review | GPT-4o, Claude 3.5 Sonnet | RAG, Clinical Guidelines |
| Policy Agent | Policy retrieval and application | GPT-4o | RAG, Policy DB |
| Fraud Agent | Anomaly detection | GPT-4o + ML Models | Graph DB, Risk Scoring |
| Decision Agent | Final decision synthesis | GPT-4o | All prior agent outputs |
| Appeals Agent | Appeal processing | GPT-4o | Case history, IRO API |
| COM Agent | Coordination of Benefits | GPT-3.5 Turbo | Payer-to-payer API |
| Notification Agent | Member/provider notifications | GPT-3.5 Turbo | Email, SMS, Portal, EDI |
| Audit Agent | Compliance logging | GPT-4o | Audit DB, Event Store |

#### Agent Design Pattern

Each agent follows consistent structure:

```python
class BaseAgent:
    def __init__(self, agent_id: str, model: str, tools: List[Tool]):
        self.agent_id = agent_id
        self.model = model
        self.tools = tools
        self.prompt_registry = PromptRegistry()
        self.guardrails = GuardrailEngine()
        self.tracer = OpenTelemetry()
        
    async def execute(self, task: Task) -> AgentResponse:
        # 1. Input validation
        validated_input = self.validate_input(task)
        
        # 2. Safety checks
        safety_check = await self.guardrails.check_input(validated_input)
        if not safety_check.passed:
            return AgentResponse(error=safety_check.violations)
        
        # 3. Retrieve context (RAG if applicable)
        context = await self.retrieve_context(validated_input)
        
        # 4. Get versioned prompt
        prompt = self.prompt_registry.get_prompt(
            agent_id=self.agent_id,
            version=self.config.prompt_version
        )
        
        # 5. Execute LLM with tools
        with self.tracer.trace(f"{self.agent_id}.execute"):
            response = await self.llm_call(
                prompt=prompt,
                context=context,
                task=validated_input,
                tools=self.tools
            )
        
        # 6. Output validation and safety
        validated_response = await self.guardrails.check_output(response)
        
        # 7. Store episodic memory
        await self.store_memory(task, response)
        
        # 8. Return structured response
        return AgentResponse(
            agent_id=self.agent_id,
            result=validated_response,
            confidence=response.confidence,
            evidence=response.citations,
            metadata=self.get_metadata()
        )
```

---

### 5. Agent Governance Platform

**Purpose**: Centralized governance for all AI agents

#### Components

##### Agent Registry
```yaml
Agent: clinical_review_agent
Version: v2.3.1
Status: ACTIVE
Model: gpt-4o-2024-05-13
Prompt_Version: v1.5
Certification:
  - Certified_By: Clinical Team
  - Certified_Date: 2026-05-15
  - Expiry_Date: 2026-08-15
Safety_Score: 98.5
Performance:
  - Accuracy: 96.2%
  - Latency_p95: 3.2s
  - Token_Usage_Avg: 8500
Approval_Status: Production
RBAC:
  - Allowed_For: [PA_Workflow, Appeals_Workflow]
  - Restricted_From: [Claims_Workflow]
```

##### Prompt Registry

**Purpose**: Version control and governance for prompts

```python
class PromptRegistry:
    def register_prompt(
        self,
        agent_id: str,
        prompt_text: str,
        version: str,
        metadata: dict
    ):
        """Register new prompt version"""
        prompt = Prompt(
            agent_id=agent_id,
            text=prompt_text,
            version=version,
            created_at=datetime.now(),
            created_by=metadata["author"],
            approved=False,
            approval_status="PENDING"
        )
        
        # Safety evaluation
        safety_score = self.evaluate_safety(prompt_text)
        
        # Bias detection
        bias_score = self.detect_bias(prompt_text)
        
        # PHI detection
        phi_detected = self.scan_for_phi(prompt_text)
        
        if phi_detected:
            raise ValueError("PHI detected in prompt")
        
        prompt.safety_score = safety_score
        prompt.bias_score = bias_score
        
        return self.db.save(prompt)
    
    def approve_prompt(self, prompt_id: str, approver: str):
        """Clinical/Compliance approval workflow"""
        prompt = self.db.get(prompt_id)
        
        # A/B testing in shadow mode
        self.deploy_shadow(prompt)
        
        # After validation period
        prompt.approved = True
        prompt.approved_by = approver
        prompt.approved_at = datetime.now()
        
        return self.db.save(prompt)
```

##### Model Governance

**Capabilities:**
- Model version tracking
- Model certification
- Performance benchmarking
- Cost tracking
- Model fallback policies

**Example:**
```yaml
Model_Governance:
  Primary_Model: gpt-4o-2024-05-13
  Fallback_Model: gpt-4-turbo
  Cost_Threshold: $0.50 per case
  Latency_Threshold: 5 seconds p95
  
  Auto_Fallback_Triggers:
    - Primary model error rate > 1%
    - Primary model latency > 10s
    - Primary model unavailable
    
  Model_Evaluation:
    - Clinical_Accuracy_Benchmark: Monthly
    - Bias_Audit: Quarterly
    - Hallucination_Test: Weekly
```

##### Runtime Guardrails

**Input Guardrails:**
- PHI detection and redaction
- Prompt injection detection
- Input size limits
- Schema validation

**Output Guardrails:**
- PHI leakage detection
- Hallucination detection
- Clinical safety validation
- Toxicity filtering
- Regulatory compliance checks

**Example Implementation:**
```python
class GuardrailEngine:
    def __init__(self):
        self.phi_detector = PresidioAnalyzer()
        self.prompt_injection_detector = LakeraTool()
        self.clinical_safety = ClinicalSafetyValidator()
        
    async def check_input(self, input_text: str) -> SafetyResult:
        results = await asyncio.gather(
            self.phi_detector.analyze(input_text),
            self.prompt_injection_detector.detect(input_text),
            self.check_input_size(input_text)
        )
        
        phi_results, injection_results, size_check = results
        
        violations = []
        if phi_results.score > 0.8:
            violations.append("PHI_DETECTED")
        if injection_results.is_injection:
            violations.append("PROMPT_INJECTION")
        if not size_check.valid:
            violations.append("INPUT_TOO_LARGE")
        
        return SafetyResult(
            passed=len(violations) == 0,
            violations=violations
        )
    
    async def check_output(self, output_text: str) -> SafetyResult:
        # Check for PHI leakage
        phi_check = await self.phi_detector.analyze(output_text)
        
        # Check for hallucinations (no citations)
        citation_check = self.verify_citations(output_text)
        
        # Clinical safety validation
        clinical_check = await self.clinical_safety.validate(output_text)
        
        violations = []
        if phi_check.score > 0.5:
            violations.append("PHI_LEAKAGE")
        if not citation_check.all_cited:
            violations.append("UNCITED_FACTS")
        if not clinical_check.safe:
            violations.append("UNSAFE_CLINICAL_RECOMMENDATION")
        
        return SafetyResult(
            passed=len(violations) == 0,
            violations=violations,
            redacted_output=self.redact_phi(output_text)
        )
```

**Technologies:**
- **PHI Detection**: Microsoft Presidio, AWS Comprehend Medical
- **Prompt Injection**: Lakera, Rebuff
- **Guardrails**: NeMo Guardrails, Guardrails AI
- **Policy Engine**: OPA

---

### Enhanced Agent Governance Platform Implementation

#### Agent Registry Schema (Production Format)

**Complete Agent Metadata:**
```json
{
  "agent_id": "clinical-review-agent",
  "version": "v2.3.1",
  "status": "ACTIVE",
  "model": "gpt-4o-2024-05-13",
  "prompt_version": "v1.5",
  "certification": {
    "certified_by": "Clinical Team",
    "certification_date": "2026-05-15",
    "expiry_date": "2026-08-15",
    "recertification_required": true
  },
  "performance_metrics": {
    "accuracy": 0.962,
    "latency_p95_ms": 3200,
    "latency_p99_ms": 5800,
    "token_usage_avg": 8500,
    "token_usage_p95": 12000,
    "cost_per_request_usd": 0.12,
    "throughput_rps": 50
  },
  "quality_metrics": {
    "hallucination_rate": 0.015,
    "groundedness_score": 0.94,
    "faithfulness_score": 0.96,
    "citation_accuracy": 0.98
  },
  "safety_score": 98.5,
  "bias_score": {
    "gender_bias": 0.02,
    "age_bias": 0.01,
    "race_bias": 0.015,
    "overall_bias": 0.015
  },
  "approval_status": "Production",
  "rbac": {
    "allowed_workflows": ["PA_Workflow", "Appeals_Workflow"],
    "restricted_workflows": ["Claims_Workflow"],
    "allowed_roles": ["clinical_reviewer", "medical_director"],
    "restricted_roles": ["intake_specialist"]
  },
  "dependencies": {
    "tools": ["mcg_guidelines", "ehr_reader", "policy_db"],
    "models": ["gpt-4o", "text-embedding-3-large"],
    "databases": ["milvus_clinical", "neo4j_policy", "postgres_cases"],
    "external_apis": ["mcg_api", "interqual_api"]
  },
  "deployment": {
    "environment": "production",
    "region": "us-east-2",
    "replicas": 5,
    "auto_scaling": {
      "enabled": true,
      "min_replicas": 3,
      "max_replicas": 20,
      "target_cpu": 70,
      "target_memory": 80
    }
  },
  "monitoring": {
    "alerts_enabled": true,
    "log_level": "INFO",
    "trace_sampling_rate": 0.1,
    "metrics_endpoint": "/metrics"
  },
  "created_at": "2026-01-15T10:30:00Z",
  "updated_at": "2026-05-01T14:22:00Z",
  "created_by": "agent_team",
  "owner": "clinical_operations"
}
```

#### Prompt Registry Implementation (Production-Ready)

**Version Control and A/B Testing:**
```python
class EnhancedPromptRegistry:
    def __init__(self, db, safety_scanner, ab_testing_engine):
        self.db = db
        self.safety_scanner = safety_scanner
        self.ab_testing = ab_testing_engine
        
    def register_prompt(
        self,
        agent_id: str,
        prompt_text: str,
        version: str,
        metadata: dict
    ) -> PromptVersion:
        """Register new prompt version with comprehensive validation"""
        
        # Step 1: Safety Evaluation
        safety_results = self.safety_scanner.evaluate({
            "prompt_text": prompt_text,
            "checks": [
                "phi_detection",
                "bias_detection",
                "toxicity_detection",
                "prompt_injection_vulnerability"
            ]
        })
        
        if safety_results.phi_detected:
            raise ValueError(f"PHI detected in prompt: {safety_results.phi_entities}")
        
        if safety_results.toxicity_score > 0.3:
            raise ValueError(f"High toxicity score: {safety_results.toxicity_score}")
        
        # Step 2: Create Prompt Version
        prompt_version = PromptVersion(
            agent_id=agent_id,
            text=prompt_text,
            version=version,
            created_at=datetime.now(),
            created_by=metadata["author"],
            safety_score=safety_results.safety_score,
            bias_score=safety_results.bias_score,
            approval_status="PENDING",
            deployment_status="NOT_DEPLOYED"
        )
        
        # Step 3: Store in database
        saved_prompt = self.db.save(prompt_version)
        
        # Step 4: Trigger approval workflow
        self.initiate_approval_workflow(saved_prompt)
        
        return saved_prompt
    
    def approve_for_testing(
        self,
        prompt_id: str,
        approver: str,
        test_config: dict
    ):
        """Approve prompt for A/B testing in shadow mode"""
        prompt = self.db.get(prompt_id)
        
        # Deploy to shadow environment (no production impact)
        shadow_deployment = self.deploy_shadow(
            prompt=prompt,
            traffic_percentage=0,  # Shadow mode
            duration_hours=24
        )
        
        # Run automated evaluation
        eval_results = self.run_automated_evaluation(
            prompt=prompt,
            test_cases=test_config.get("test_cases", 100)
        )
        
        prompt.shadow_deployment_id = shadow_deployment.id
        prompt.shadow_results = eval_results
        prompt.approval_status = "TESTING"
        
        return self.db.save(prompt)
    
    def approve_for_production(
        self,
        prompt_id: str,
        approver: str,
        rollout_strategy: str = "canary"
    ):
        """Approve prompt for production with gradual rollout"""
        prompt = self.db.get(prompt_id)
        
        if prompt.approval_status != "TESTING":
            raise ValueError("Prompt must complete testing before production")
        
        # Verify shadow results meet thresholds
        if not self.meets_production_criteria(prompt.shadow_results):
            raise ValueError("Shadow results do not meet production criteria")
        
        # Create A/B test configuration
        ab_test = self.ab_testing.create_test(
            control_prompt=self.get_current_production_prompt(prompt.agent_id),
            variant_prompt=prompt,
            strategy=rollout_strategy,
            rollout_schedule={
                "week_1": 5,   # 5% traffic
                "week_2": 10,  # 10% traffic
                "week_3": 25,  # 25% traffic
                "week_4": 100  # Full rollout
            }
        )
        
        prompt.approval_status = "APPROVED"
        prompt.approved_by = approver
        prompt.approved_at = datetime.now()
        prompt.ab_test_id = ab_test.id
        prompt.deployment_status = "CANARY"
        
        return self.db.save(prompt)
    
    def monitor_prompt_drift(self, agent_id: str):
        """Detect prompt drift over time"""
        current_prompt = self.get_current_production_prompt(agent_id)
        
        # Get embedding of current prompt
        current_embedding = self.get_embedding(current_prompt.text)
        
        # Get historical embeddings (last 30 days)
        historical_embeddings = self.get_historical_embeddings(
            agent_id=agent_id,
            days=30
        )
        
        # Calculate drift
        drift_scores = []
        for historical in historical_embeddings:
            similarity = cosine_similarity(
                current_embedding,
                historical.embedding
            )
            drift_scores.append(1 - similarity)  # Drift = 1 - similarity
        
        avg_drift = np.mean(drift_scores)
        max_drift = np.max(drift_scores)
        
        # Alert if drift exceeds threshold
        if avg_drift > 0.15:  # 15% average drift
            self.trigger_alert({
                "agent_id": agent_id,
                "alert_type": "PROMPT_DRIFT",
                "avg_drift": avg_drift,
                "max_drift": max_drift,
                "recommendation": "Review prompt changes"
            })
        
        return {
            "avg_drift": avg_drift,
            "max_drift": max_drift,
            "drift_threshold": 0.15,
            "status": "OK" if avg_drift < 0.15 else "ALERT"
        }
```

#### Model Governance Dashboard

**Comprehensive Model Tracking:**
```yaml
Model_Governance_Dashboard:
  
  Primary_Models:
    - model_id: gpt-4o-2024-05-13
      purpose: Clinical reasoning, complex cases
      certification_status: CERTIFIED
      certification_date: 2026-01-15
      recertification_due: 2026-07-15
      performance_benchmarks:
        accuracy: 96.2%
        hallucination_rate: 1.5%
        latency_p95: 3.2s
        cost_per_1k_tokens: $0.015
      approved_for:
        - clinical_review_agent
        - appeals_agent
        - complex_case_agent
      restricted_from:
        - intake_agent  # Too expensive for simple tasks
      
    - model_id: gpt-4o-mini-2024-05-13
      purpose: Simple cases, routing decisions
      certification_status: CERTIFIED
      certification_date: 2026-02-01
      performance_benchmarks:
        accuracy: 92.8%
        hallucination_rate: 2.1%
        latency_p95: 1.8s
        cost_per_1k_tokens: $0.002
      approved_for:
        - intake_agent
        - routing_agent
        - notification_agent
  
  Fallback_Policies:
    primary_failure_response:
      - try: gpt-4o-2024-05-13
        on_failure: claude-3-5-sonnet
        on_failure: gpt-4-turbo
        final_fallback: human_escalation
    
    cost_optimization:
      - simple_queries: gpt-4o-mini
        medium_queries: gpt-4-turbo
        complex_queries: gpt-4o
    
    latency_optimization:
      - real_time_required: gpt-4o-mini
        standard: gpt-4-turbo
        batch_processing: gpt-4o
  
  Model_Evaluation_Schedule:
    clinical_accuracy_benchmark:
      frequency: Monthly
      test_cases: 500
      gold_standard: Physician review
      pass_threshold: 95%
    
    bias_audit:
      frequency: Quarterly
      demographics: [age, gender, race, geography]
      pass_threshold: <2% bias across all demographics
    
    hallucination_test:
      frequency: Weekly
      method: Human + LLM-as-judge
      pass_threshold: <2% hallucination rate
    
    cost_analysis:
      frequency: Daily
      alert_threshold: 20% cost increase
      optimization_trigger: Weekly
  
  Deprecation_Schedule:
    - model: gpt-4-0613
      status: DEPRECATED
      end_of_life: 2026-08-01
      migration_plan:
        target_model: gpt-4o-2024-05-13
        migration_start: 2026-06-01
        migration_complete: 2026-07-15
        rollback_plan: Available until EOL
```

---

### Enterprise Multi-Agent Design Patterns

**Purpose**: Proven patterns for orchestrating multiple AI agents in enterprise healthcare workflows

#### Pattern 1: Supervisor Pattern (Current Implementation)

**When to Use:**
- Deterministic workflows with clear steps
- Central control required for compliance
- Strong consistency requirements
- Audit trail critical

**Healthcare Example:** Prior Authorization Workflow
```
Supervisor Agent
    ├→ Intake Agent (Step 1)
    ├→ Eligibility Agent (Step 2)
    ├→ Benefits Agent (Step 3)
    ├→ Clinical Agent (Step 4)
    ├→ Policy Agent (Step 5)
    ├→ Fraud Agent (Step 6)
    └→ Decision Agent (Step 7)
```

**Benefits:**
- Clear control flow
- Easy debugging (centralized logs)
- Consistent state management
- Regulatory compliance (full audit trail)

**Limitations:**
- Single point of failure (supervisor)
- Sequential bottleneck (cannot parallelize)
- Tight coupling

---

#### Pattern 2: Sequential Pipeline Pattern

**When to Use:**
- Linear processing steps
- Output of step N is input to step N+1
- Simple workflows

**Healthcare Example:** Claims Processing
```
Claim Submission
    ↓
OCR Agent (extract data)
    ↓
Validation Agent (check completeness)
    ↓
Coding Agent (verify CPT/ICD-10)
    ↓
Fraud Detection Agent (screen for fraud)
    ↓
Pricing Agent (calculate payment)
    ↓
Approval Agent (final decision)
    ↓
Payment Agent (issue payment)
```

**Benefits:**
- Simple, predictable
- Easy to monitor (track progress through pipeline)
- Clear error handling (retry each stage)

**Limitations:**
- Cannot handle branches
- No parallel processing
- Inflexible

---

#### Pattern 3: Planner-Executor Pattern

**When to Use:**
- Complex, multi-step reasoning required
- Dynamic planning needed
- Steps depend on previous results

**Healthcare Example:** Appeals Processing
```
Appeals Agent (Planner)
    ↓
Creates Dynamic Plan:
    1. Identify denial reason
    2. Gather additional evidence
    3. Research case law / precedent
    4. Build argument
    5. Submit to IRO (if needed)
    ↓
Executor Agents carry out plan
    ├→ Research Agent
    ├→ Evidence Gathering Agent
    ├→ Legal Research Agent
    └→ IRO Submission Agent
```

**Benefits:**
- Handles complexity
- Adapts to case specifics
- Multi-step reasoning

**Limitations:**
- Higher latency (planning overhead)
- More expensive (additional LLM calls)
- Harder to debug

---

#### Pattern 4: Reflection/Critic Pattern

**When to Use:**
- Quality assurance required
- Self-correction needed
- High-stakes decisions

**Healthcare Example:** Clinical Decision Validation
```
Clinical Review Agent
    ↓
Generates Initial Decision
    ↓
Critic Agent Reviews
    ├→ Check: Evidence supports decision?
    ├→ Check: Guidelines followed?
    ├→ Check: No logical errors?
    ↓
IF issues found:
    └→ Clinical Agent revises decision
       └→ Critic re-reviews
          └→ Iterate until quality threshold met
```

**Benefits:**
- Self-correction
- Improved accuracy
- Catches errors before production

**Limitations:**
- Higher latency (multiple LLM calls)
- Higher cost
- Risk of infinite loops

---

#### Pattern 5: Debate Pattern

**When to Use:**
- High-stakes, controversial decisions
- Multiple valid perspectives
- Reduce bias

**Healthcare Example:** Experimental Treatment Approval
```
Decision Required: Approve experimental cancer treatment?
    ↓
Agent 1 (Advocate): Argues FOR approval
    ↓
Agent 2 (Skeptic): Argues AGAINST approval
    ↓
Agent 3 (Judge): Evaluates both arguments
    ↓
Final Decision with full justification
```

**Benefits:**
- Multiple perspectives
- Reduces bias
- Stronger justification

**Limitations:**
- Expensive (3+ LLM calls)
- Slow
- Complexity

---

#### Pattern 6: Event-Driven Pattern

**When to Use:**
- Asynchronous processing
- Scalability critical
- Loose coupling desired

**Healthcare Example:** Real-Time Fraud Detection
```
Event Bus (Kafka)
    │
    ├→ Claim Submitted Event
    │   ├→ Fraud Detection Agent (subscribes)
    │   ├→ Duplicate Check Agent (subscribes)
    │   └→ Pricing Agent (subscribes)
    │
    ├→ Fraud Detected Event
    │   ├→ Investigation Agent (subscribes)
    │   └→ Audit Log Agent (subscribes)
    │
    └→ Payment Approved Event
        └→ Payment Agent (subscribes)
```

**Benefits:**
- Loose coupling
- High scalability
- Fault isolation

**Limitations:**
- Eventually consistent (not immediate)
- Complex debugging (distributed traces)
- Requires event infrastructure

---

#### Pattern 7: HITL (Human-in-the-Loop) Pattern

**When to Use:**
- Regulatory requirements (mandatory human review)
- High-risk decisions
- Edge cases beyond AI capability

**Healthcare Example:** High-Value Approval
```
AI Decision: Approve $200K cancer treatment
    ↓
Risk Score: 0.92 (HIGH)
    ↓
Route to Human Reviewer
    ├→ Medical Director review required
    ├→ Reviewer sees AI recommendation + rationale
    ├→ Human can:
    │   ├→ Approve as-is
    │   ├→ Modify decision
    │   └→ Deny with explanation
    ↓
Final Decision logged with human override
```

**Decision Matrix:**
```
Risk Level     | Action
─────────────────────────────────────────────
Low (<0.4)     | Auto-execute
Medium (0.4-0.75) | Supervisor review
High (0.75-0.9)   | Senior approval required
Critical (>0.9)   | Multi-reviewer + Board
```

**Benefits:**
- Compliance (regulatory requirement)
- Safety net (human oversight)
- Trust (stakeholder confidence)

**Limitations:**
- Bottleneck (human availability)
- Cost (human time)
- SLA impact (review delays)

---

#### Pattern 8: Hierarchical Pattern

**When to Use:**
- Enterprise-scale complexity
- Multi-department workflows
- Clear organizational structure

**Healthcare Example:** Multi-Department Case Processing
```
Executive Supervisor Agent
    ├→ Clinical Department Supervisor
    │   ├→ Clinical Review Agent
    │   ├→ Medical Necessity Agent
    │   └→ Peer Review Agent
    │
    ├→ Operations Department Supervisor
    │   ├→ Eligibility Agent
    │   ├→ Benefits Agent
    │   └→ Network Agent
    │
    ├→ Compliance Department Supervisor
    │   ├→ Policy Agent
    │   ├→ Audit Agent
    │   └→ Regulatory Agent
    │
    └→ Finance Department Supervisor
        ├→ Pricing Agent
        ├→ Fraud Agent
        └→ Payment Agent
```

**Benefits:**
- Scales to enterprise complexity
- Clear responsibility boundaries
- Department isolation

**Limitations:**
- Complex coordination
- Higher latency (hierarchy overhead)

---

#### Pattern 9: Blackboard Pattern

**When to Use:**
- Shared intelligence needed
- Multiple agents contribute to shared knowledge
- Complex problem solving

**Healthcare Example:** Fraud Ring Detection
```
Shared Blackboard (Knowledge Graph)
    ↑                    ↑                    ↑
Pattern Agent      Network Agent      Anomaly Agent
    │                    │                    │
    └─→ Writes findings ←┘                    │
         └─→ All agents read and update ←─────┘
```

**Benefits:**
- Collaborative intelligence
- Emergent behavior
- Shared context

**Limitations:**
- Complex state management
- Race conditions
- Requires sophisticated coordination

---

#### Pattern 10: Swarm Pattern

**When to Use:**
- Decentralized decision-making
- Optimization problems
- No single authority

**Healthcare Example:** Provider Network Optimization
```
Multiple Optimizer Agents (swarm):
    Agent 1: Optimize for cost
    Agent 2: Optimize for quality
    Agent 3: Optimize for access
    Agent 4: Optimize for member satisfaction
    ↓
Each agent proposes solution
    ↓
Consensus algorithm selects best overall solution
```

**Benefits:**
- Emergent optimization
- No single point of failure
- Resilient

**Limitations:**
- Hard to predict behavior
- Debugging challenging
- Requires consensus mechanism

---

### A2A (Agent-to-Agent) Protocol Implementation

**Purpose**: Standardized communication protocol for multi-agent systems

#### Message Contract Schema

**Standard Message Format:**
```json
{
  "message_id": "msg-uuid-12345",
  "correlation_id": "workflow-pa-001234",
  "source_agent": "eligibility-agent",
  "source_version": "v2.1.0",
  "target_agent": "benefits-agent",
  "target_version": "v1.8.0",
  "message_type": "REQUEST",
  "priority": "NORMAL",
  "timestamp": "2026-06-01T10:30:00Z",
  "payload": {
    "task": "validate_coverage",
    "member_id": "M123456",
    "service_codes": ["97110", "97140"],
    "service_date": "2026-06-15"
  },
  "context": {
    "case_id": "PA-2026-001234",
    "workflow_id": "wf-12345",
    "step_number": 3,
    "previous_results": {
      "eligibility": "ELIGIBLE"
    }
  },
  "security": {
    "signed": true,
    "signature": "SHA256:abcd1234...",
    "jwt_token": "eyJhbGciOiJSUzI1NiIs...",
    "tenant_id": "payer-a",
    "encryption": "AES-256-GCM"
  },
  "observability": {
    "trace_id": "trace-uuid-67890",
    "span_id": "span-uuid-11111",
    "parent_span_id": "span-uuid-00000",
    "baggage": {
      "user_id": "reviewer-123",
      "session_id": "session-456"
    }
  },
  "sla": {
    "timeout_ms": 5000,
    "deadline": "2026-06-01T10:30:05Z",
    "retry_policy": {
      "max_retries": 3,
      "backoff_strategy": "exponential",
      "initial_delay_ms": 100,
      "max_delay_ms": 2000
    }
  },
  "quality_of_service": {
    "delivery_guarantee": "at_least_once",
    "ordering_guarantee": "fifo",
    "durability": "persistent"
  }
}
```

**Message Type Definitions:**
```
REQUEST:   Agent requests action from another agent
RESPONSE:  Agent responds to REQUEST
ERROR:     Agent reports error in processing
EVENT:     Agent publishes event (fire-and-forget)
ACK:       Agent acknowledges receipt of message
NACK:      Agent rejects message (invalid, unauthorized, etc.)
TIMEOUT:   Agent reports timeout waiting for response
```

**Priority Levels:**
```
LOW:       Background tasks, batch processing
NORMAL:    Standard workflow steps
HIGH:      Time-sensitive operations
URGENT:    Emergency cases, SLA at risk
CRITICAL:  Life-threatening, regulatory deadline
```

#### Agent Configuration Template

**Complete Agent Configuration:**
```json
{
  "agent_id": "clinical-review-agent",
  "version": "v2.3.1",
  
  "runtime": {
    "framework": "langgraph",
    "execution_mode": "distributed",
    "max_concurrency": 20,
    "timeout_seconds": 120,
    "memory_limit_mb": 4096,
    "cpu_limit_cores": 2,
    "retry_policy": {
      "max_retries": 3,
      "backoff_strategy": "exponential",
      "backoff_multiplier": 2,
      "initial_delay_ms": 100,
      "max_delay_ms": 5000,
      "jitter": true
    },
    "circuit_breaker": {
      "enabled": true,
      "failure_threshold": 5,
      "timeout_seconds": 30,
      "half_open_after_seconds": 60
    }
  },
  
  "communication": {
    "protocol": "A2A",
    "transport": "grpc",
    "serialization": "protobuf",
    "message_schema_version": "v2",
    "compression": "gzip",
    "max_message_size_mb": 10,
    "connection_pool_size": 50,
    "keep_alive_interval_seconds": 30
  },
  
  "capabilities": [
    {
      "name": "medical_necessity_review",
      "version": "v1.0",
      "input_schema": "medical_case",
      "output_schema": "clinical_decision"
    },
    {
      "name": "guideline_retrieval",
      "version": "v1.0",
      "input_schema": "diagnosis_code",
      "output_schema": "guideline_criteria"
    },
    {
      "name": "confidence_scoring",
      "version": "v1.0",
      "input_schema": "decision",
      "output_schema": "confidence_score"
    }
  ],
  
  "dependencies": {
    "vector_db": {
      "type": "milvus",
      "connection": "milvus://milvus-cluster:19530",
      "collection": "clinical_guidelines",
      "health_check_interval_seconds": 30
    },
    "llm_provider": {
      "type": "azure-openai",
      "endpoint": "https://myorg.openai.azure.com",
      "deployment": "gpt-4o",
      "api_version": "2024-05-13",
      "max_tokens": 16000,
      "temperature": 0.1,
      "fallback_provider": "anthropic"
    },
    "embedding_model": {
      "name": "bge-large-en-v1.5",
      "dimension": 1024,
      "max_batch_size": 32
    },
    "knowledge_graph": {
      "type": "neo4j",
      "uri": "neo4j://neo4j-cluster:7687",
      "database": "clinical_policies"
    }
  },
  
  "governance": {
    "human_approval_required_for": [
      "high_cost_procedures",
      "experimental_treatments",
      "off_label_use",
      "confidence_below_threshold"
    ],
    "auto_approve_thresholds": {
      "max_cost_usd": 5000,
      "min_confidence": 0.95,
      "guideline_match_required": true
    },
    "risk_scoring": {
      "enabled": true,
      "model": "clinical_risk_scorer_v1",
      "threshold": 0.75,
      "factors": [
        "procedure_cost",
        "medical_complexity",
        "experimental_status",
        "confidence_score"
      ]
    },
    "audit_logging": {
      "enabled": true,
      "log_level": "DETAILED",
      "include_prompts": true,
      "include_responses": true,
      "retention_days": 2555,
      "compliance_mode": "HIPAA"
    }
  },
  
  "security": {
    "authentication": {
      "method": "mtls",
      "cert_path": "/certs/agent.crt",
      "key_path": "/certs/agent.key",
      "ca_path": "/certs/ca.crt"
    },
    "authorization": {
      "rbac_enabled": true,
      "allowed_callers": [
        "supervisor-agent",
        "orchestrator"
      ],
      "allowed_tools": [
        "mcg_guidelines",
        "interqual",
        "policy_db"
      ]
    },
    "encryption": {
      "in_transit": "TLS_1_3",
      "at_rest": "AES_256_GCM",
      "phi_masking": true
    }
  },
  
  "observability": {
    "metrics": {
      "enabled": true,
      "port": 9090,
      "path": "/metrics",
      "format": "prometheus"
    },
    "logging": {
      "level": "INFO",
      "format": "json",
      "destination": "stdout",
      "correlation_id_header": "X-Correlation-ID"
    },
    "tracing": {
      "enabled": true,
      "sampler": "probability",
      "sampling_rate": 0.1,
      "exporter": "otlp",
      "endpoint": "otel-collector:4317"
    },
    "health_check": {
      "enabled": true,
      "port": 8080,
      "path": "/health",
      "interval_seconds": 10
    }
  },
  
  "scaling": {
    "auto_scaling": {
      "enabled": true,
      "min_replicas": 3,
      "max_replicas": 20,
      "metrics": [
        {
          "type": "cpu",
          "target_percentage": 70
        },
        {
          "type": "memory",
          "target_percentage": 80
        },
        {
          "type": "custom",
          "name": "queue_depth",
          "target_value": 100
        }
      ]
    }
  }
}
```

---

### 6. MCP (Model Context Protocol) Layer

**Purpose**: Dynamic tool discovery, capability negotiation, standardized tool integration

#### Why MCP in Healthcare Insurance?

**Problem**: Hardcoded tool integrations are brittle
- **InterQual API** changes frequently
- **MCG guidelines** update quarterly
- **FDA Drug Database** API versions
- **CMS NCD/LCD** policy updates
- **Internal payer policies** continuous updates

**Solution**: MCP enables dynamic discovery and adaptation

#### MCP Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 MCP GATEWAY                              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │Tool Registry │  │ Capability   │  │   Schema     │ │
│  │              │  │  Routing     │  │  Validation  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │Tool Auth     │  │  Version     │  │    Policy    │ │
│  │              │  │  Management  │  │  Enforcement │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │MCG Tool │     │InterQual│     │ FDA API │
    │ MCP     │     │  Tool   │     │  Tool   │
    └─────────┘     └─────────┘     └─────────┘
```

#### MCP Tool Discovery Flow

**Runtime Tool Discovery Process:**
```
Scenario: Clinical Agent needs guideline tools for knee replacement case
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent Initiates Discovery Request                          │
└─────────────────────────────────────────────────────────────┘
    ├─ Input: diagnosis = "M17.11" (Knee osteoarthritis)
    ├─ Determine specialty: get_specialty("M17.11") → "orthopedics"
    └─ Prepare discovery request
    ↓
[Discovery Request to MCP Gateway]
    ├─ Parameter 1: capability = "clinical_guidelines"
    ├─ Parameter 2: specialty = "orthopedics"
    ├─ Parameter 3: certification_level = "PRODUCTION"
    └─ Send request: mcp_client.discover_tools(...)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ MCP Gateway Processes Request                               │
└─────────────────────────────────────────────────────────────┘
    ↓
[Query Tool Registry]
    ├─ Filter 1: capability = "clinical_guidelines"
    ├─ Filter 2: specialty CONTAINS "orthopedics"
    ├─ Filter 3: status = "PRODUCTION" (not DEV/STAGING)
    └─ Filter 4: health_check = PASSING
    ↓
[Matching Tools Found]
    ├─ Tool 1 Found: MCG API v4
    │   ├─ tool_id: "mcg_api_v4"
    │   ├─ name: "MCG Clinical Guidelines"
    │   ├─ version: "4.2.1"
    │   ├─ provider: "Milliman"
    │   ├─ capabilities: ["medical_necessity"]
    │   ├─ specialties: ["orthopedics", "cardiology", ...]
    │   ├─ schema: {input/output definitions}
    │   ├─ auth_required: true
    │   └─ status: PRODUCTION ✓
    │
    └─ Tool 2 Found: InterQual API
        ├─ tool_id: "interqual_api"
        ├─ name: "InterQual Criteria"
        ├─ version: "2024.1"
        ├─ provider: "Change Healthcare"
        ├─ capabilities: ["medical_necessity", "level_of_care"]
        ├─ specialties: ["orthopedics", "general_surgery", ...]
        ├─ schema: {input/output definitions}
        ├─ auth_required: true
        └─ status: PRODUCTION ✓
    ↓
[MCP Returns Tool List to Agent]
    └─ Response: available_tools = [mcg_api_v4, interqual_api]
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Agent Selects and Invokes Tool                             │
└─────────────────────────────────────────────────────────────┘
    ├─ Agent logic: "I'll use MCG as primary, InterQual as secondary"
    ├─ Validate schema compatibility
    ├─ Prepare API call with case data
    └─ Invoke: mcg_api_v4.check_medical_necessity(case)
```

**Key Benefits:**
- **No Hardcoding**: Agent doesn't know tool IDs in advance
- **Dynamic Updates**: New guideline tools auto-discovered
- **Multi-Vendor**: Works with any compliant tool provider
- **Failover**: If MCG unavailable, agent can use InterQual

#### MCP Tool Registration

**Tool Provider Registration Process:**
```
Scenario: MCG (Milliman Care Guidelines) registers with MCP Gateway
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Build Tool Definition                                       │
└─────────────────────────────────────────────────────────────┘
    ↓
[Basic Metadata]
    ├─ tool_id: "mcg_api_v4" (Unique identifier)
    ├─ name: "MCG Clinical Guidelines" (Human-readable)
    ├─ version: "4.2.1" (Semantic versioning)
    └─ provider: "Milliman" (Vendor name)
    ↓
[Capabilities Declaration]
    ├─ Capability 1: "medical_necessity" (Core function)
    ├─ Capability 2: "level_of_care" (Inpatient/Outpatient determination)
    └─ Capability 3: "care_transitions" (Discharge planning)
    ↓
[Specialty Coverage]
    ├─ Specialty 1: "cardiology" (Heart conditions)
    ├─ Specialty 2: "oncology" (Cancer treatments)
    ├─ Specialty 3: "orthopedics" (Musculoskeletal)
    ├─ Specialty 4: "neurology" (Nervous system)
    ├─ ... (50+ specialties total)
    └─ Specialty Coverage: COMPREHENSIVE
    ↓
[Input/Output Schema Definition]
    ↓
    [Input Schema]
    ├─ diagnosis_code: "string (ICD-10 format)"
    │   └─ Example: "M17.11" (Knee osteoarthritis)
    ├─ procedure_code: "string (CPT format)"
    │   └─ Example: "27447" (Knee replacement)
    └─ clinical_findings: "object (structured data)"
        └─ Example: {age, comorbidities, prior_treatments}
    ↓
    [Output Schema]
    ├─ recommendation: "enum (APPROVE | DENY | MORE_INFO)"
    ├─ guideline_reference: "string (MCG guideline ID)"
    │   └─ Example: "MCG A-0527"
    └─ clinical_rationale: "string (explanation)"
        └─ Example: "Patient meets criteria: 6 mo PT failed..."
    ↓
[Authentication Configuration]
    ├─ type: "api_key" (Auth method)
    ├─ header: "X-MCG-API-Key" (Header name)
    └─ rotation_policy: "90 days" (Security requirement)
    ↓
[Rate Limits & SLA]
    ├─ requests_per_minute: 100 (Throttling limit)
    ├─ latency_p95: "500ms" (95th percentile response time)
    ├─ latency_p99: "1000ms" (99th percentile)
    └─ availability: "99.9%" (Uptime SLA)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Submit Registration to MCP Gateway                          │
└─────────────────────────────────────────────────────────────┘
    └─ API Call: mcp_gateway.register_tool(tool_definition)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ MCP Gateway Validation                                      │
└─────────────────────────────────────────────────────────────┘
    ↓
[Validation Steps]
    ├─ Check 1: Schema validation (JSON schema compliance) ✓
    ├─ Check 2: Unique tool_id (no duplicates) ✓
    ├─ Check 3: Provider verification (Milliman approved) ✓
    ├─ Check 4: Endpoint health check (API reachable) ✓
    └─ Check 5: Authentication test (API key valid) ✓
    ↓
[All Checks Passed]
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Tool Registered Successfully                                │
└─────────────────────────────────────────────────────────────┘
    ├─ Added to Tool Registry Database
    ├─ Status: ACTIVE (available for discovery)
    ├─ Notification: Agents can now discover "mcg_api_v4"
    └─ Monitoring: Health checks every 60 seconds
    ↓
[Tool Now Available for Discovery]
    └─ Any agent requesting capability="clinical_guidelines"
        + specialty="orthopedics" will receive MCG in results
```

**Registration Lifecycle:**
- **Registration**: Tool provider submits definition
- **Validation**: MCP Gateway validates and tests
- **Activation**: Tool appears in discovery results
- **Monitoring**: Continuous health checks
- **Update**: Provider can update version (MCG 4.2.1 → 4.3.0)
- **Deprecation**: Old versions marked deprecated but still available
- **Deactivation**: Tool removed from discovery (still in DB for audit)

#### MCP Benefits for Healthcare

1. **Dynamic Guideline Updates**
   - New MCG version released → Auto-discovered
   - No code changes required

2. **Multi-Source Evidence**
   - Agent requests "medical necessity" capability
   - MCP returns: MCG + InterQual + Internal policies
   - Agent uses all sources

3. **Graceful Degradation**
   - InterQual API down → MCP routes to MCG
   - Transparent failover

4. **Version Management**
   - Old cases use old tool versions (auditability)
   - New cases use current versions

5. **Tool Governance**
   - Only certified tools available
   - Policy enforcement (e.g., must cite primary source)
   - Cost tracking per tool

**Technologies:**
- **MCP Implementation**: Anthropic MCP SDK, LangChain Tools
- **Service Discovery**: Consul, etcd
- **API Gateway**: Kong, Apigee

---

## Detailed Solution Patterns & Integration Scenarios

This section provides in-depth technical solutions for real-world integration and processing scenarios.

### Solution Pattern 1: Real-Time Clinical Guidelines Integration

#### Business Problem
Clinical guidelines (MCG, InterQual, Hayes) update quarterly. Hardcoded guideline logic becomes outdated, leading to incorrect determinations and compliance risks.

#### Traditional Approach (Problems)
```python
# ANTI-PATTERN: Hardcoded guideline logic
def check_medical_necessity_pt(diagnosis_code, sessions_requested):
    # This code becomes outdated when guidelines change
    if diagnosis_code == "M54.5":  # Low back pain
        if sessions_requested <= 12:
            return "APPROVED"
        else:
            return "DENIED - Exceeds guideline maximum"
    # ... hundreds more hardcoded rules
```

**Problems:**
- ❌ Requires code deploy for guideline updates
- ❌ Version control nightmare (which guideline version was used?)
- ❌ Cannot explain which specific guideline section applied
- ❌ Audit trail incomplete
- ❌ Different reviewers might use different versions
- ❌ Regression risk with every update

#### AI + MCP Solution Architecture

**Component Overview:**
```
┌──────────────────────────────────────────────────────────┐
│                  CLINICAL AGENT                          │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Clinical Decision Engine (GPT-4o/Claude 3.5)      │ │
│  │                                                     │ │
│  │  Input: Diagnosis, Treatment Request, Clinical     │ │
│  │         Notes, Medical History                     │ │
│  │                                                     │ │
│  │  Process:                                          │ │
│  │  1. Extract clinical entities (NER)               │ │
│  │  2. Query guideline via MCP                        │ │
│  │  3. Apply guideline criteria                       │ │
│  │  4. Generate evidence-based recommendation         │ │
│  │                                                     │ │
│  └────────────────────────────────────────────────────┘ │
│                          │                               │
│                          ▼ MCP Protocol                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │         MCG GUIDELINES TOOL (MCP Server)           │ │
│  │                                                     │ │
│  │  Capabilities:                                     │ │
│  │  • search_guideline(diagnosis, procedure)          │ │
│  │  • get_criteria(guideline_id)                      │ │
│  │  • check_necessity(clinical_facts)                 │ │
│  │  • get_duration_limits(service_type)               │ │
│  │                                                     │ │
│  │  Version: MCG 29th Edition (Auto-updated)          │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

**Detailed Implementation:**

**Step 1: MCG Guidelines MCP Server Architecture**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MCG GUIDELINES MCP SERVER                            │
│                     (Dynamic Tool Provider)                             │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
         ┌────────────────────┐      ┌────────────────────┐
         │  TOOL 1:           │      │  TOOL 2:           │
         │  search_guideline  │      │  check_medical_    │
         │                    │      │  necessity         │
         └────────────────────┘      └────────────────────┘
                    │                           │
                    ▼                           ▼

╔════════════════════════════════════════════════════════════════════════╗
║              TOOL 1: SEARCH_GUIDELINE FLOW                             ║
╚════════════════════════════════════════════════════════════════════════╝

INPUT Parameters:
┌──────────────────────────────────────┐
│ • Diagnosis Code (ICD-10): "M54.5"   │
│ • Procedure Code (CPT): "97110"      │
│ • Service Type: "physical_therapy"   │
└──────────────────────────────────────┘
              │
              ▼
    ┌───────────────────┐
    │  MCG API Query    │
    │  - ICD-10 Lookup  │
    │  - CPT Match      │
    │  - Category Filter│
    └───────────────────┘
              │
              ▼
    ┌───────────────────┐
    │ Retrieve Results  │
    │ (Multiple Guidelines│
    │  may match)       │
    └───────────────────┘
              │
              ▼
    ┌───────────────────────────────────────────┐
    │  Structure Response Package               │
    │  ┌─────────────────────────────────────┐ │
    │  │ Guideline #1:                       │ │
    │  │  • ID: MCG-A-0442                   │ │
    │  │  • Title: "Low Back Pain - PT"      │ │
    │  │  • Version: 29.0                    │ │
    │  │  • Effective Date: 2026-01-01       │ │
    │  │  • Criteria:                        │ │
    │  │    - Clinical Indications ────────┐ │ │
    │  │    - Duration Limits              │ │ │
    │  │    - Frequency Limits             │ │ │
    │  │    - Required Documentation       │ │ │
    │  │    - Contraindications            │ │ │
    │  │  • Decision Tree                   │ │
    │  │  • Evidence References             │ │
    │  └─────────────────────────────────────┘ │
    └───────────────────────────────────────────┘
              │
              ▼
OUTPUT: Structured Guideline Data
┌──────────────────────────────────────┐
│ {                                    │
│   "guidelines_found": 1,             │
│   "guidelines": [...],               │
│   "metadata": {                      │
│     "mcg_version": "29.0",           │
│     "query_timestamp": "...",        │
│     "query_params": {...}            │
│   }                                  │
│ }                                    │
└──────────────────────────────────────┘


╔════════════════════════════════════════════════════════════════════════╗
║         TOOL 2: CHECK_MEDICAL_NECESSITY FLOW                           ║
╚════════════════════════════════════════════════════════════════════════╝

INPUT Parameters:
┌────────────────────────────────────────────────┐
│ Guideline ID: "MCG-A-0442"                     │
│ Clinical Facts:                                │
│  ├─ Diagnosis: "M54.5"                         │
│  ├─ Symptoms: ["chronic pain >8 weeks"]        │
│  ├─ Prior Treatments: ["NSAIDs", "rest"]       │
│  ├─ Duration: "8 weeks"                        │
│  ├─ Functional Impact: "ADL limitation"        │
│  └─ Comorbidities: []                          │
└────────────────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────┐
    │ Retrieve Guideline  │
    │ MCG-A-0442          │
    └─────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────────┐
    │      CRITERIA EVALUATION ENGINE         │
    └─────────────────────────────────────────┘
              │
    ┌─────────┴──────────┬──────────┬─────────┐
    ▼                    ▼          ▼         ▼
┌─────────┐      ┌──────────┐  ┌────────┐  ┌──────┐
│Clinical │      │  Prior   │  │Duration│  │Contra│
│Indica-  │      │Treatment │  │ Check  │  │indica│
│tions    │      │  Check   │  │        │  │tions │
└─────────┘      └──────────┘  └────────┘  └──────┘
    │                │              │          │
    ▼                ▼              ▼          ▼
  ┌───┐          ┌───┐          ┌───┐      ┌───┐
  │✓  │          │✓  │          │✓  │      │✓  │
  │MET│          │MET│          │MET│      │NONE│
  └───┘          └───┘          └───┘      └───┘
    │                │              │          │
    └────────────────┴──────────────┴──────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ Aggregate Results    │
          │ Medical Necessity:   │
          │      ✓ MET           │
          │ Confidence: 95%      │
          └──────────────────────┘
                     │
                     ▼
OUTPUT: Necessity Determination
┌─────────────────────────────────────────────┐
│ {                                           │
│   "medical_necessity": "MET",               │
│   "confidence": 0.95,                       │
│   "criteria_evaluation": {                  │
│     "clinical_indications": "PASS",         │
│     "prior_treatment": "PASS",              │
│     "duration": "PASS"                      │
│   },                                        │
│   "rationale": "All criteria met...",       │
│   "limitations": {                          │
│     "max_sessions": 12,                     │
│     "max_timeframe": "6 weeks"              │
│   },                                        │
│   "citations": [...]                        │
│ }                                           │
└─────────────────────────────────────────────┘
```

**Step 2: Clinical Agent Using MCP - Execution Flow**

```
╔════════════════════════════════════════════════════════════════════════╗
║           CLINICAL REVIEW AGENT - MCP INTEGRATION FLOW                 ║
╚════════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────┐
│                     AGENT INITIALIZATION                            │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐      ┌──────────────────┐                    │
│  │ LLM: GPT-4o      │      │ MCP Connection   │                    │
│  │ Temperature: 0.0 │◄────►│ MCG Guidelines   │                    │
│  │ (Deterministic)  │      │ Server           │                    │
│  └──────────────────┘      └──────────────────┘                    │
│                                    │                                │
│                                    ▼                                │
│                          ┌────────────────┐                         │
│                          │ Tool Registry  │                         │
│                          │ - search_guide │                         │
│                          │ - check_neces  │                         │
│                          │ - Other tools  │                         │
│                          └────────────────┘                         │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼

╔════════════════════════════════════════════════════════════════════════╗
║                  CASE REVIEW EXECUTION SEQUENCE                        ║
╚════════════════════════════════════════════════════════════════════════╝
┌─────────────────────────────────────────────────────────────────────┐
│                   STEP 1: EXTRACT CLINICAL FACTS                     │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
    Case Data ───► ┌────────────────────────────┐
                    │ NLP Entity Extraction    │
                    │ • Diagnosis: M54.5       │
                    │ • Symptoms: chronic pain │
                    │ • Duration: 8 weeks      │
                    │ • Prior Rx: NSAIDs       │
                    └────────────────────────────┘
                              │
                              ▼

┌─────────────────────────────────────────────────────────────────────┐
│                  STEP 2: AGENT REASONING LOOP                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
   ┌───────────────────┐       ┌───────────────────┐
   │  GPT-4o THINKS:    │       │  AGENT ACTION:   │
   │                   │       │                 │
   │  "I need to find  │       │  Call Tool:      │
   │  MCG guidelines   │─────►│  search_guideline│
   │  for M54.5 + PT"  │       │                 │
   │                   │       │  Params:         │
   └───────────────────┘       │  - M54.5         │
                               │  - 97110         │
                               └───────────────────┘
                                       │
                                       ▼
                           ┌────────────────────────┐
                           │ MCP PROTOCOL CALL     │
                           │ to MCG Server         │
                           └────────────────────────┘
                                       │
                                       ▼
                           ┌────────────────────────┐
                           │ TOOL RESPONSE:        │
                           │ MCG-A-0442 Guideline  │
                           │ with full criteria    │
                           └────────────────────────┘
                                       │
                                       ▼
   ┌───────────────────┐       ┌───────────────────┐
   │  GPT-4o THINKS:    │       │  AGENT ACTION:   │
   │                   │       │                 │
   │  "Now I need to   │       │  Call Tool:      │
   │  check if patient │─────►│  check_medical_  │
   │  meets criteria"  │       │  necessity       │
   │                   │       │                 │
   └───────────────────┘       │  Params:         │
                               │  - MCG-A-0442    │
                               │  - clinical_facts│
                               └───────────────────┘
                                       │
                                       ▼
                           ┌────────────────────────┐
                           │ CRITERIA EVALUATION   │
                           │ ✓ Indications: MET   │
                           │ ✓ Prior Rx: MET      │
                           │ ✓ Duration: MET      │
                           └────────────────────────┘
                                       │
                                       ▼
   ┌─────────────────────────────────────────────────────────┐
   │           GPT-4o FINAL SYNTHESIS                        │
   ├─────────────────────────────────────────────────────────┤
   │  "Based on MCG-A-0442 guidelines retrieved:           │
   │                                                        │
   │  DETERMINATION: APPROVED                              │
   │                                                        │
   │  RATIONALE: Member meets all MCG criteria for         │
   │  physical therapy. Documented chronic low back pain   │
   │  >8 weeks with failed conservative treatment (NSAIDs).│
   │  Functional limitations documented. Approve 12 sessions│
   │  per MCG-A-0442 guideline."                           │
   │                                                        │
   │  GUIDELINE CITATION: MCG-A-0442 v29.0                 │
   │  CRITERIA MET: All                                    │
   │  APPROVED QUANTITY: 12 sessions                       │
   │  CONDITIONS: Review if no improvement after 6 weeks   │
   │  CONFIDENCE: 95%                                      │
   └─────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                     ┌───────────────────────────┐
                     │  AUDIT TRAIL CREATED     │
                     ├───────────────────────────┤
                     │ • Agent: clinical_agent  │
                     │ • Model: GPT-4o         │
                     │ • MCG Version: 29.0     │
                     │ • Tools Used:           │
                     │   - search_guideline     │
                     │   - check_necessity      │
                     │ • Timestamp: 2026-06-01 │
                     └───────────────────────────┘
```

**Business Impact:**

| Metric | Before MCP | With MCP | Improvement |
|--------|-----------|----------|-------------|
| **Guideline Update Time** | 2 weeks (code deploy) | 0 (automatic) | Instant |
| **Version Accuracy** | 85% (version drift) | 100% | 18% improvement |
| **Audit Trail** | Partial | Complete | 100% traceability |
| **Compliance Risk** | Medium-High | Low | Risk reduction |
| **Consistency** | Variable (hardcoded logic varies) | High (same guideline source) | Better outcomes |
| **Maintenance Cost** | $200K/year | $50K/year | 75% reduction |

**Key Advantages:**

1. ✅ **Always Current**: MCG updates → Immediate availability
2. ✅ **Version Control**: Know exactly which guideline version used
3. ✅ **Auditability**: Complete trail of which guideline, which criteria
4. ✅ **Explainability**: Can show regulator the exact guideline section
5. ✅ **Flexibility**: Easy to add InterQual, Hayes, or internal guidelines
6. ✅ **Testing**: Can test against multiple guideline versions
7. ✅ **Rollback**: Can specify guideline version if needed

---

### Solution Pattern 2: Multi-Channel Intake Normalization

#### Business Problem
Prior authorization requests arrive via 5+ channels (portal, fax, EDI, FHIR, phone). Each has different formats, quality levels, and completeness. Manual processing is slow and error-prone.

#### Detailed Solution Architecture

```
┌────────────────────────────────────────────────────────────────┐
│            MULTI-CHANNEL INTAKE ORCHESTRATOR                   │
└────────────────────────────────────────────────────────────────┘
     │        │          │          │          │
     │        │          │          │          │
     ▼        ▼          ▼          ▼          ▼
┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
│Provider││  Fax   ││  EDI   ││  FHIR  ││  IVR   │
│ Portal ││ Server ││X12 278 ││  API   ││(Phone) │
└────────┘└────────┘└────────┘└────────┘└────────┘
     │        │          │          │          │
     │        │          │          │          │
     ▼        ▼          ▼          ▼          ▼
┌────────────────────────────────────────────────────────────────┐
│                    INTAKE AGENT (GPT-4o)                       │
│                                                                │
│  Capabilities:                                                 │
│  • Intelligent document parsing (PDF, images, EDI, JSON, XML) │
│  • OCR with medical terminology understanding                 │
│  • Multi-format normalization                                 │
│  • Missing information detection                              │
│  • Data quality assessment                                    │
│  • Automated follow-up requests                               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│              STANDARDIZED PA REQUEST (FHIR R4)                 │
│                                                                │
│  {                                                             │
│    "resourceType": "ServiceRequest",                          │
│    "status": "active",                                        │
│    "intent": "order",                                         │
│    "code": {...},                                             │
│    "subject": {...},                                          │
│    "reasonCode": [{...}],                                     │
│    "supportingInfo": [...]                                    │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
```

**Channel-Specific Processing:**

**Channel 1: Provider Portal (Structured)**
```python
class PortalIntakeProcessor:
    """Process structured portal submissions"""
    
    async def process(self, submission: dict) -> StandardizedRequest:
        # Portal submissions are already structured
        # Minimal AI processing needed
        
        return StandardizedRequest(
            channel="portal",
            member_id=submission["member_id"],
            provider_npi=submission["provider"]["npi"],
            diagnosis_codes=submission["diagnosis_codes"],
            procedure_codes=submission["procedure_codes"],
            clinical_notes=submission["clinical_notes"],
            attachments=submission["attachments"],
            completeness_score=0.95,  # Usually complete
            processing_time_seconds=2
        )
```

**Channel 2: Fax (Unstructured) - AI-Heavy**
```python
class FaxIntakeProcessor:
    """Process unstructured fax submissions using AI"""
    
    def __init__(self):
        self.ocr_engine = AzureFormRecognizer()
        self.document_ai = GPT4VisionAPI()  # GPT-4o with vision
        self.clinical_ner = MedicalNER()
    
    async def process(self, fax_image: bytes) -> StandardizedRequest:
        """
        Convert fax image to structured data using AI
        """
        
        # Step 1: OCR - Convert image to text
        ocr_result = await self.ocr_engine.analyze_document(
            document=fax_image,
            model="prebuilt-document"
        )
        raw_text = ocr_result.content
        
        # Step 2: Document Classification (AI)
        doc_classification = await self.classify_document(raw_text)
        
        # Step 3: Intelligent Extraction (GPT-4o)
        extraction_prompt = """
You are processing a prior authorization request received via fax.
Extract all relevant information and structure it in JSON format.

FAX CONTENT:
{raw_text}

EXTRACT THE FOLLOWING:
1. Member Information:
   - Member name, DOB, ID number
2. Provider Information:
   - Provider name, NPI, practice name, phone, fax
3. Requested Services:
   - Diagnosis codes (ICD-10)
   - Procedure codes (CPT/HCPCS)
   - Quantity/frequency
   - Duration
4. Clinical Justification:
   - Symptoms
   - Prior treatments
   - Medical necessity rationale
5. Supporting Documents:
   - Types of attachments (labs, imaging, notes)

OUTPUT FORMAT:
{{
  "member": {{
    "name": "Last, First",
    "dob": "YYYY-MM-DD",
    "member_id": "12345678"
  }},
  "provider": {{
    "name": "Dr. Name",
    "npi": "1234567890",
    "practice": "Practice Name",
    "phone": "555-555-5555"
  }},
  "services": [
    {{
      "diagnosis": {{
        "code": "M54.5",
        "description": "Low back pain"
      }},
      "procedure": {{
        "code": "97110",
        "description": "Therapeutic exercise"
      }},
      "quantity": 12,
      "frequency": "3x per week"
    }}
  ],
  "clinical_justification": "...",
  "completeness": {{
    "has_diagnosis": true/false,
    "has_procedure": true/false,
    "has_clinical_notes": true/false,
    "has_supporting_docs": true/false,
    "missing_info": ["list any missing required info"]
  }}
}}

IMPORTANT:
- If information is unclear or missing, note it in "missing_info"
- Preserve exact code numbers (don't guess)
- Include confidence level for extracted data
"""
        
        extracted_data = await self.document_ai.extract(
            prompt=extraction_prompt.format(raw_text=raw_text),
            response_format="json"
        )
        
        # Step 4: Medical Entity Recognition (specialized NER)
        entities = await self.clinical_ner.extract_entities(raw_text)
        
        # Step 5: Data Quality Assessment
        quality_score = self.assess_quality(extracted_data, entities)
        
        # Step 6: Identify Missing Information
        missing_info = self.identify_missing(extracted_data)
        
        # Step 7: Auto-Request Missing Info (if possible)
        if missing_info and extracted_data["provider"]["fax"]:
            await self.send_missing_info_request(
                provider_fax=extracted_data["provider"]["fax"],
                missing_items=missing_info
            )
        
        return StandardizedRequest(
            channel="fax",
            raw_ocr_text=raw_text,
            extracted_data=extracted_data,
            entities=entities,
            completeness_score=quality_score,
            missing_information=missing_info,
            processing_time_seconds=45,
            confidence_scores={
                "member_id": 0.98,
                "provider_npi": 0.95,
                "diagnosis": 0.92,
                "procedure": 0.88
            }
        )
```

**Channel 3: EDI X12 278 (Semi-Structured)**
```python
class EDIIntakeProcessor:
    """Process X12 278 transactions"""
    
    async def process(self, edi_message: str) -> StandardizedRequest:
        """
        Parse EDI 278 and convert to standard format
        """
        
        # Parse EDI
        parser = X12Parser()
        parsed = parser.parse(edi_message)
        
        # Map to FHIR ServiceRequest
        fhir_request = self.map_to_fhir(parsed)
        
        # EDI is structured but may have cryptic codes
        # Use AI to interpret ambiguous codes
        if self.has_ambiguous_codes(parsed):
            interpretation = await self.interpret_codes(parsed)
            fhir_request.update(interpretation)
        
        return StandardizedRequest(
            channel="edi_278",
            edi_transaction=edi_message,
            fhir_resource=fhir_request,
            completeness_score=0.85,  # EDI often complete but terse
            processing_time_seconds=5
        )
```

**Intelligent Missing Information Handler:**
```python
class MissingInformationManager:
    """Proactively request missing information"""
    
    async def handle_missing_info(
        self,
        case_id: str,
        missing_items: List[str],
        provider_contact: dict
    ):
        """
        Generate and send intelligent request for missing info
        """
        
        # AI generates natural language request
        request_letter = await self.generate_request_letter(
            missing_items=missing_items,
            case_context=case_id
        )
        
        # Multi-channel delivery
        delivery_results = await asyncio.gather(
            self.send_portal_message(provider_contact["portal_id"], request_letter),
            self.send_fax(provider_contact["fax"], request_letter),
            self.send_email(provider_contact["email"], request_letter),
            self.create_edi_request(provider_contact["payer_id"], missing_items)
        )
        
        # Track response
        await self.track_pending_info(
            case_id=case_id,
            missing_items=missing_items,
            request_sent=datetime.now(),
            follow_up_due=datetime.now() + timedelta(days=2)
        )
```

**Business Impact:**

| Channel | Volume | Processing Time | Accuracy | Completeness | Cost |
|---------|--------|-----------------|----------|--------------|------|
| **Portal** | 15,000/day | 2 sec | 99% | 95% | $0.10 |
| **Fax (Manual)** | 10,000/day | 15 min | 85% | 70% | $15.00 |
| **Fax (AI)** | 10,000/day | 45 sec | 96% | 88% | $2.50 |
| **EDI** | 20,000/day | 5 sec | 98% | 85% | $0.50 |
| **FHIR** | 5,000/day | 3 sec | 99% | 92% | $0.20 |

**Annual Savings from AI-Powered Fax Processing:**
- 10,000 faxes/day × 365 days = 3.65M faxes/year
- Manual cost: $15 × 3.65M = $54.75M
- AI cost: $2.50 × 3.65M = $9.13M  
- **Savings: $45.6M/year**

**Channel Processing Comparison Flow:**

```
┌────────────────────────────────────────────────────────────────────────┐
│                 MULTI-CHANNEL INTAKE ORCHESTRATOR                      │
└────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌─────────────────┴─────────────────┐
            ▼                 ▼              ▼          ▼
      ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
      │ Portal │  │  Fax   │  │  EDI   │  │  FHIR  │
      └────────┘  └────────┘  └────────┘  └────────┘
          │           │           │           │
          ▼           ▼           ▼           ▼

┌────────────────────────────────────────────────────────────────────────┐
│         CHANNEL 1: PORTAL (STRUCTURED) - Fast Track                  │
└────────────────────────────────────────────────────────────────────────┘

Portal Form Data (JSON)
         │
         ▼
  ┌───────────────────┐
  │ Schema Validation │ ──► 2 seconds
  └───────────────────┘
         │
         ▼
  ┌───────────────────┐
  │ Direct Mapping   │
  │ to FHIR Format   │
  └───────────────────┘
         │
         ▼
Standardized Request
┌──────────────────────┐
│ Completeness: 95%  │
│ Accuracy: 99%      │
│ Cost: $0.10        │
└──────────────────────┘


┌────────────────────────────────────────────────────────────────────────┐
│       CHANNEL 2: FAX (UNSTRUCTURED) - AI-Heavy Processing            │
└────────────────────────────────────────────────────────────────────────┘

Fax Image (TIFF/PDF)
         │
         ▼
  ┌───────────────────────────┐
  │ OCR - Azure Form Recognizer │ ──► 10 sec
  └───────────────────────────┘
         │
         ▼
  Raw Text
  ┌───────────────────────────┐
  │                           │
  │  PRIOR AUTHORIZATION        │
  │  Member: Sarah Johnson     │
  │  DOB: 03/15/1981           │
  │  Diagnosis: M54.5          │
  │  Service: Physical Therapy │
  │  12 sessions requested     │
  │  ...                       │
  └───────────────────────────┘
         │
         ▼
  ┌───────────────────────────┐
  │ GPT-4o Vision Extraction   │ ──► 25 sec
  │ Intelligent NLP Processing │
  └───────────────────────────┘
         │
         ▼
  Structured Extraction:
  ┌───────────────────────────┐
  │ member: {                  │
  │   name: "Johnson, Sarah",  │
  │   dob: "1981-03-15",       │
  │   member_id: "extracted"   │
  │ }                          │
  │ diagnosis: "M54.5"         │
  │ procedure: "97110"         │
  │ confidence: 0.92           │
  └───────────────────────────┘
         │
         ▼
  ┌───────────────────────────┐
  │ Medical NER                │ ──► 5 sec
  │ Entity Validation          │
  └───────────────────────────┘
         │
         ▼
  ┌───────────────────────────┐
  │ Quality Assessment         │ ──► 5 sec
  │ Missing Info Detection     │
  └───────────────────────────┘
         │
         ▼
Standardized Request
┌──────────────────────┐
│ Completeness: 88%  │
│ Accuracy: 96%      │
│ Cost: $2.50        │
│ Time: 45 seconds   │
└──────────────────────┘
         │
         ▼
If Missing Info:
  ┌───────────────────────────┐
  │ Auto-Request Generation    │
  │ ├─ Fax back to provider    │
  │ ├─ Portal notification     │
  │ └─ Email alert             │
  └───────────────────────────┘


┌────────────────────────────────────────────────────────────────────────┐
│                    ALL CHANNELS CONVERGE                              │
└────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                ┌──────────────────────────────────┐
                │ STANDARDIZED FHIR R4 REQUEST     │
                │ (Unified format for all channels)│
                └──────────────────────────────────┘
                              │
                              ▼
                    To Multi-Agent Workflow
```

---

### Solution Pattern 3: End-to-End Workflow Orchestration with Temporal

#### Business Problem
Prior authorization workflows are complex with multiple decision points, parallel processing, human interventions, SLA tracking, and error recovery. Traditional workflow engines struggle with long-running workflows, state management, and reliability.

#### Detailed Temporal Workflow Architecture

**Workflow Overview:**
```
PA Request Submitted
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│            TEMPORAL WORKFLOW: process_prior_auth            │
│                                                             │
│  State: Durable (survives process crashes/restarts)        │
│  Timeout: 72 hours (standard) / 24 hours (urgent)          │
│  Retry: Automatic with exponential backoff                 │
│  Visibility: Full execution history                        │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PARALLEL ACTIVITIES:                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Eligibility  │  │  Benefits    │  │   Intake     │    │
│  │   Check      │  │  Verification│  │  Processing  │    │
│  │  (Activity)  │  │  (Activity)  │  │  (Activity)  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                 │                 │              │
│         └─────────────────┴─────────────────┘              │
│                           │                                 │
│                    (All must complete)                      │
│                           │                                 │
│                           ▼                                 │
│  SEQUENTIAL ACTIVITIES:                                     │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Clinical Review (Activity)                          │ │
│  │  • May invoke sub-workflow for complex cases         │ │
│  │  • Timeout: 2 hours                                  │ │
│  │  • Retry: 3 attempts                                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  DECISION POINT:                                            │
│  if (confidence < 0.90):                                   │
│      → Human Review (Signal/Wait)                          │
│  else:                                                      │
│      → Auto-Decision                                       │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Generate Decision Letter (Activity)                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Notify Stakeholders (Activity)                      │ │
│  │  • Provider                                          │ │
│  │  • Member                                            │ │
│  │  • Care Manager (if applicable)                     │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Detailed Workflow State Machine:**

```
╔════════════════════════════════════════════════════════════════════════╗
║           TEMPORAL WORKFLOW STATE MACHINE - EXECUTION FLOW             ║
╚════════════════════════════════════════════════════════════════════════╝

START
  │
  ├─► Initialize Workflow
  │    ├─ case_id: PA-2026-001234
  │    ├─ SLA deadline: 2026-06-03 14:00
  │    └─ workflow_state: "INITIATED"
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: INTAKE & VALIDATION                      │
│                      workflow_state = "INTAKE"                       │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─► Activity: process_intake()
  │    ├─ Timeout: 5 minutes
  │    ├─ Retry: 3 attempts, exponential backoff
  │    └─ Heartbeat: Every 30 seconds
  │
  ▼
  ◇ Check: Is intake complete?
  │
  ├─YES─► Continue
  │
  └─NO──► Sub-Flow: Request Missing Info
           │
           ├─► Activity: request_missing_info()
           │    └─ Notify provider via Portal/Fax/Email
           │
           ├─► Wait for Signal: additional_info_received
           │    └─ Timeout: 5 days
           │         ├─ If timeout → Auto-deny
           │         └─ If received → Continue
           │
           ▼
           Resume main flow
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 PHASE 2: PARALLEL VERIFICATION                       │
│                  workflow_state = "VERIFICATION"                     │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├──────────────┬──────────────┬──────────────────┐
  │              │              │                  │
  ▼              ▼              ▼                  ▼
┌─────────┐  ┌─────────┐  ┌──────────┐     ┌──────────┐
│Activity │  │Activity │  │ Activity │     │ Activity │
│check_   │  │check_   │  │ check_   │     │ check_   │
│eligi-   │  │benefits │  │ fraud_   │     │ policy_  │
│bility   │  │         │  │ risk     │     │ limits   │
│         │  │         │  │          │     │          │
│Timeout: │  │Timeout: │  │Timeout:  │     │Timeout:  │
│30 sec   │  │1 min    │  │2 min     │     │1 min     │
└─────────┘  └─────────┘  └──────────┘     └──────────┘
     │            │              │                │
     └────────────┴──────────────┴────────────────┘
                  │
                  │ (All must complete via asyncio.gather)
                  │
                  ▼
           ◇ Validation Gate
           │
           ├─► IF eligibility.eligible == False
           │    └─► Create Denial → JUMP TO PHASE 5
           │
           ├─► IF benefits.covered == False
           │    └─► Create Denial → JUMP TO PHASE 5
           │
           ├─► IF fraud_check.risk_score > 0.8
           │    └─► Escalate to Fraud Investigation → JUMP TO PHASE 5
           │
           └─► ALL PASS → Continue
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   PHASE 3: CLINICAL REVIEW                           │
│                workflow_state = "CLINICAL_REVIEW"                    │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─► ◇ Check Complexity Score
  │    │
  │    ├─IF complexity > 0.7 (Complex Case)
  │    │   │
  │    │   └─► Child Workflow: ComplexClinicalReviewWorkflow
  │    │        ├─ Runs in separate task queue
  │    │        ├─ Multi-step peer review
  │    │        ├─ Specialist consultation
  │    │        └─ Returns: clinical_decision
  │    │
  │    └─IF complexity ≤ 0.7 (Standard Case)
  │         │
  │         └─► Activity: clinical_review()
  │              ├─ Timeout: 10 minutes
  │              ├─ Retry: 2 attempts
  │              ├─ Calls Clinical Agent (GPT-4o)
  │              ├─ Retrieves guidelines via MCP
  │              └─ Returns: clinical_decision
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     PHASE 4: DECISION LOGIC                          │
│                    workflow_state = "DECISION"                       │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─► ◇ Decision Routing Logic
  │    │
  │    ├─CASE 1: clinical_decision.confidence < 0.90
  │    │   │
  │    │   └─► Human Review Path
  │    │        │
  │    │        ├─► Activity: assign_to_reviewer()
  │    │        │    ├─ Smart assignment algorithm
  │    │        │    ├─ Based on specialty, workload
  │    │        │    └─ Timeout: 10 seconds
  │    │        │
  │    │        ├─► Wait for Signal: human_decision
  │    │        │    ├─ Timeout: sla_deadline - now()
  │    │        │    │    └─ If timeout → Escalate
  │    │        │    │
  │    │        │    └─ Signal received → final_decision
  │    │        │
  │    │        └─► final_decision = human_decision
  │    │
  │    ├─CASE 2: determination == "EXPERIMENTAL"
  │    │   │
  │    │   └─► Medical Director Review Path
  │    │        │
  │    │        ├─► Activity: assign_to_medical_director()
  │    │        │
  │    │        ├─► Wait for Signal: md_decision
  │    │        │    └─ Timeout: 4 hours (MD SLA)
  │    │        │
  │    │        └─► final_decision = md_decision
  │    │
  │    └─CASE 3: confidence ≥ 0.90 AND routine determination
  │         │
  │         └─► Auto-Decision Path
  │              └─► final_decision = clinical_decision
  │
  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   PHASE 5: FINALIZATION                              │
│                  workflow_state = "FINALIZATION"                     │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─► Activity: generate_decision_letter()
  │    ├─ Input: final_decision, clinical_rationale
  │    ├─ Timeout: 1 minute
  │    └─ Output: decision_letter (PDF)
  │
  ├─► Activity: store_decision()
  │    ├─ Database: Write decision record
  │    ├─ Includes: workflow_execution_id for audit
  │    └─ Timeout: 30 seconds
  │
  ├─► PARALLEL NOTIFICATIONS (asyncio.gather)
  │    │
  │    ├─────────────┬─────────────┬─────────────┐
  │    │             │             │             │
  │    ▼             ▼             ▼             ▼
  │  Activity     Activity      Activity      Activity
  │  notify_      notify_       send_edi_     update_care_
  │  provider     member        response      plan
  │    │             │             │             │
  │    │ Fax/EDI     │ Email/      │ X12 278     │ HL7 msg
  │    │ Portal      │ Portal      │ response    │ to EHR
  │    │             │             │             │
  │    └─────────────┴─────────────┴─────────────┘
  │                  │
  │                  │ (All must complete)
  │                  │
  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  PHASE 6: POST-DECISION                              │
│                  workflow_state = "COMPLETED"                        │
└─────────────────────────────────────────────────────────────────────┘
  │
  ├─► Activity: log_audit_trail()
  │    ├─ Capture: Full workflow execution history
  │    ├─ Includes: All activities, signals, decisions
  │    └─ Compliance requirement: HIPAA, state regulations
  │
  ├─► Activity: update_metrics()
  │    ├─ Processing time
  │    ├─ SLA compliance
  │    ├─ Automation rate
  │    └─ Cost tracking
  │
  ├─► ◇ Check Appeal Window
  │    └─ If DENIED → Start Appeal Monitoring Workflow
  │         └─ Monitor for appeal submission (60 days)
  │
  ▼
WORKFLOW COMPLETE
  │
  └─► Return: final_decision
       ├─ determination: "APPROVED" | "DENIED" | "PENDED"
       ├─ rationale: "..."
       ├─ approved_units: 12
       └─ workflow_execution_id: "pa-2026-001234-abc123"


╔════════════════════════════════════════════════════════════════════════╗
║                       ERROR HANDLING & RECOVERY                        ║
╚════════════════════════════════════════════════════════════════════════╝

At ANY point in workflow:

  ├─► Activity Failure
  │    └─► Automatic Retry (per RetryPolicy)
  │         ├─ Attempt 1: Immediate
  │         ├─ Attempt 2: 1 second delay
  │         ├─ Attempt 3: 2 seconds delay
  │         └─ If all fail → Escalate
  │
  ├─► Workflow Crash/Restart
  │    └─► Temporal RESTORES STATE
  │         └─ Resume from last completed activity
  │              └─ Durable execution guarantee
  │
  ├─► SLA Approaching
  │    └─► SLAMonitorWorkflow detects
  │         ├─ 4 hours remaining → Escalate priority
  │         ├─ 2 hours remaining → Notify management
  │         └─ 0 hours (breach) → Critical alert
  │
  ├─► Human Review Timeout
  │    └─► Auto-escalate to supervisor
  │         └─ Reassign to available reviewer
  │
  └─► Unhandled Exception
       └─► Activity: escalate_error()
            ├─ PagerDuty alert
            ├─ Slack notification
            └─ Case marked for manual intervention


╔════════════════════════════════════════════════════════════════════════╗
║                    WORKFLOW SIGNALS & QUERIES                          ║
╚════════════════════════════════════════════════════════════════════════╝

SIGNALS (External → Workflow):
  ├─ receive_additional_info(info: dict)
  │   └─ Provider submits missing documentation
  │
  ├─ receive_human_decision(decision: dict)
  │   └─ Reviewer makes determination
  │
  ├─ receive_md_decision(decision: dict)
  │   └─ Medical Director approves/denies
  │
  └─ cancel_request(reason: str)
       └─ Provider withdraws PA request

QUERIES (External → Workflow):
  ├─ get_status() → {state, sla_deadline, time_remaining}
  │   └─ Provider Portal: "What's the status?"
  │
  └─ get_full_history() → [all activities, timestamps]
       └─ Audit requirement

```
    """
    Durable workflow for prior authorization processing
    
    Features:
    - Automatic retry on failures
    - Durable state (survives crashes)
    - SLA tracking and enforcement
    - Human-in-the-loop support
    - Full execution history
    """
    
    def __init__(self):
        self.case_id: str = ""
        self.workflow_state: str = "INITIATED"
        self.sla_deadline: datetime = None
        self.escalation_count: int = 0
        
    @workflow.run
    async def run(self, pa_request: PriorAuthRequest) -> PriorAuthDecision:
        """
        Main workflow execution
        """
        
        self.case_id = pa_request.case_id
        
        # Calculate SLA deadline
        if pa_request.urgency == "URGENT":
            self.sla_deadline = workflow.now() + timedelta(hours=24)
        else:
            self.sla_deadline = workflow.now() + timedelta(hours=72)
        
        # Start SLA monitoring (side effect)
        workflow.set_update_handler(self.handle_sla_check)
        
        try:
            # ======================
            # PHASE 1: INTAKE & VALIDATION
            # ======================
            workflow.logger.info(f"Starting PA workflow for {self.case_id}")
            self.workflow_state = "INTAKE"
            
            intake_result = await workflow.execute_activity(
                activities.process_intake,
                pa_request,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(
                    maximum_attempts=3,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=10),
                    backoff_coefficient=2.0
                )
            )
            
            if not intake_result.complete:
                # Request missing information
                await self.request_missing_information(
                    missing_items=intake_result.missing_info
                )
                
                # Wait for provider response (signal)
                await workflow.wait_condition(
                    lambda: self.additional_info_received,
                    timeout=timedelta(days=5)
                )
            
            # ======================
            # PHASE 2: PARALLEL VERIFICATION
            # ======================
            self.workflow_state = "VERIFICATION"
            
            # Execute in parallel
            eligibility_task = workflow.execute_activity(
                activities.check_eligibility,
                intake_result.member_id,
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            benefits_task = workflow.execute_activity(
                activities.check_benefits,
                {
                    "member_id": intake_result.member_id,
                    "service_codes": intake_result.service_codes
                },
                start_to_close_timeout=timedelta(minutes=1)
            )
            
            fraud_task = workflow.execute_activity(
                activities.check_fraud_risk,
                {
                    "provider_npi": intake_result.provider_npi,
                    "member_id": intake_result.member_id,
                    "service_codes": intake_result.service_codes
                },
                start_to_close_timeout=timedelta(minutes=2)
            )
            
            # Wait for all parallel activities
            eligibility, benefits, fraud_check = await asyncio.gather(
                eligibility_task,
                benefits_task,
                fraud_task
            )
            
            # Validate results
            if not eligibility.eligible:
                return self.create_denial(reason="MEMBER_NOT_ELIGIBLE")
            
            if not benefits.covered:
                return self.create_denial(reason="SERVICE_NOT_COVERED")
            
            if fraud_check.risk_score > 0.8:
                # High fraud risk - escalate to fraud investigation
                return await self.escalate_to_fraud_investigation(
                    case_id=self.case_id,
                    risk_score=fraud_check.risk_score
                )
            
            # ======================
            # PHASE 3: CLINICAL REVIEW
            # ======================
            self.workflow_state = "CLINICAL_REVIEW"
            
            # Check complexity
            if intake_result.complexity_score > 0.7:
                # Complex case - use sub-workflow
                clinical_decision = await workflow.execute_child_workflow(
                    ComplexClinicalReviewWorkflow.run,
                    {
                        "case_id": self.case_id,
                        "clinical_data": intake_result.clinical_data
                    },
                    id=f"clinical-review-{self.case_id}",
                    task_queue="clinical-review-queue"
                )
            else:
                # Standard case
                clinical_decision = await workflow.execute_activity(
                    activities.clinical_review,
                    intake_result.clinical_data,
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(maximum_attempts=2)
                )
            
            # ======================
            # PHASE 4: DECISION LOGIC
            # ======================
            self.workflow_state = "DECISION"
            
            # Check if human review needed
            if clinical_decision.confidence < 0.90:
                workflow.logger.info(
                    f"Low confidence ({clinical_decision.confidence}), "
                    f"routing to human review"
                )
                
                # Assign to human reviewer
                await workflow.execute_activity(
                    activities.assign_to_reviewer,
                    {
                        "case_id": self.case_id,
                        "priority": self.calculate_priority(),
                        "ai_recommendation": clinical_decision
                    },
                    start_to_close_timeout=timedelta(seconds=10)
                )
                
                # Wait for human decision (signal from reviewer UI)
                human_decision = await workflow.wait_condition(
                    lambda: self.human_decision is not None,
                    timeout=self.sla_deadline - workflow.now()
                )
                
                final_decision = self.human_decision
                
            elif clinical_decision.determination == "EXPERIMENTAL":
                # Experimental treatments require MD review
                md_review = await self.route_to_medical_director(
                    case_id=self.case_id,
                    ai_analysis=clinical_decision
                )
                final_decision = md_review
                
            else:
                # Auto-approve/deny
                final_decision = clinical_decision
            
            # ======================
            # PHASE 5: FINALIZATION
            # ======================
            self.workflow_state = "FINALIZATION"
            
            # Generate decision letter
            decision_letter = await workflow.execute_activity(
                activities.generate_decision_letter,
                {
                    "case_id": self.case_id,
                    "decision": final_decision,
                    "clinical_rationale": final_decision.rationale,
                    "guidelines_applied": final_decision.guidelines
                },
                start_to_close_timeout=timedelta(minutes=1)
            )
            
            # Store decision in database
            await workflow.execute_activity(
                activities.store_decision,
                {
                    "case_id": self.case_id,
                    "decision": final_decision,
                    "decision_letter": decision_letter,
                    "workflow_execution_id": workflow.info().workflow_id
                },
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Notify stakeholders (parallel)
            await asyncio.gather(
                workflow.execute_activity(
                    activities.notify_provider,
                    {
                        "provider_npi": intake_result.provider_npi,
                        "decision_letter": decision_letter
                    },
                    start_to_close_timeout=timedelta(minutes=2)
                ),
                workflow.execute_activity(
                    activities.notify_member,
                    {
                        "member_id": intake_result.member_id,
                        "decision_summary": self.create_member_summary(final_decision)
                    },
                    start_to_close_timeout=timedelta(minutes=2)
                ),
                workflow.execute_activity(
                    activities.send_edi_response,
                    {
                        "original_edi": pa_request.original_edi,
                        "decision": final_decision
                    },
                    start_to_close_timeout=timedelta(minutes=1)
                )
            )
            
            # ======================
            # PHASE 6: POST-DECISION
            # ======================
            self.workflow_state = "COMPLETED"
            
            # Audit logging
            await workflow.execute_activity(
                activities.log_audit_trail,
                {
                    "case_id": self.case_id,
                    "workflow_history": await workflow.info().get_execution_history(),
                    "decision": final_decision
                },
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            # Update metrics
            await workflow.execute_activity(
                activities.update_metrics,
                {
                    "case_id": self.case_id,
                    "processing_time": workflow.now() - workflow.info().start_time,
                    "sla_met": workflow.now() < self.sla_deadline,
                    "automation_level": "AUTO" if final_decision.automated else "HUMAN"
                },
                start_to_close_timeout=timedelta(seconds=10)
            )
            
            workflow.logger.info(f"Workflow completed for {self.case_id}")
            
            return final_decision
            
        except Exception as e:
            workflow.logger.error(f"Workflow failed for {self.case_id}: {str(e)}")
            
            # Escalate to on-call
            await workflow.execute_activity(
                activities.escalate_error,
                {
                    "case_id": self.case_id,
                    "error": str(e),
                    "workflow_state": self.workflow_state
                },
                start_to_close_timeout=timedelta(minutes=1)
            )
            
            raise
    
    @workflow.signal
    async def receive_additional_info(self, info: dict):
        """Signal handler for receiving additional information"""
        self.additional_info = info
        self.additional_info_received = True
    
    @workflow.signal
    async def receive_human_decision(self, decision: dict):
        """Signal handler for human reviewer decision"""
        self.human_decision = decision
    
    @workflow.query
    def get_status(self) -> dict:
        """Query handler for workflow status"""
        return {
            "case_id": self.case_id,
            "state": self.workflow_state,
            "sla_deadline": self.sla_deadline.isoformat(),
            "time_remaining": (self.sla_deadline - workflow.now()).total_seconds(),
            "escalation_count": self.escalation_count
        }
    
    async def request_missing_information(self, missing_items: List[str]):
        """Request missing information from provider"""
        await workflow.execute_activity(
            activities.request_missing_info,
            {
                "case_id": self.case_id,
                "missing_items": missing_items
            },
            start_to_close_timeout=timedelta(minutes=1)
        )
    
    async def route_to_medical_director(self, case_id: str, ai_analysis: dict):
        """Route complex case to medical director"""
        # Assign to MD
        await workflow.execute_activity(
            activities.assign_to_medical_director,
            {"case_id": case_id, "ai_analysis": ai_analysis},
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Wait for MD decision
        md_decision = await workflow.wait_condition(
            lambda: self.md_decision is not None,
            timeout=timedelta(hours=4)  # MD SLA
        )
        
        return md_decision
    
    def calculate_priority(self) -> str:
        """Calculate case priority"""
        if workflow.now() > self.sla_deadline - timedelta(hours=4):
            return "CRITICAL"
        elif self.escalation_count > 0:
            return "HIGH"
        else:
            return "NORMAL"
```

**Activity Implementations (Samples):**

```python
# activities/clinical_review.py
from temporalio import activity
import anthropic

@activity.defn
async def clinical_review(clinical_data: dict) -> ClinicalDecision:
    """
    Perform clinical review using AI
    
    Note: Activities are automatically retried by Temporal
    """
    
    activity.logger.info(f"Clinical review for case {clinical_data['case_id']}")
    
    # Call Clinical Agent
    clinical_agent = ClinicalAgent()
    
    try:
        decision = await clinical_agent.review(clinical_data)
        
        # Record activity success
        activity.heartbeat({"status": "completed", "confidence": decision.confidence})
        
        return decision
        
    except Exception as e:
        activity.logger.error(f"Clinical review failed: {str(e)}")
        # Temporal will automatically retry based on RetryPolicy
        raise

@activity.defn
async def assign_to_reviewer(assignment_data: dict):
    """
    Assign case to human reviewer
    """
    
    # Smart assignment based on:
    # - Reviewer specialty
    # - Current workload
    # - Historical performance
    # - Availability
    
    assignment_engine = ReviewerAssignmentEngine()
    reviewer = await assignment_engine.assign_case(
        case_id=assignment_data["case_id"],
        specialty_required=assignment_data.get("specialty"),
        priority=assignment_data["priority"]
    )
    
    # Send to reviewer queue
    await reviewer.queue.add_case(
        case_id=assignment_data["case_id"],
        ai_recommendation=assignment_data["ai_recommendation"],
        priority=assignment_data["priority"]
    )
    
    # Notify reviewer
    await notification_service.notify_reviewer(
        reviewer_id=reviewer.id,
        case_id=assignment_data["case_id"],
        priority=assignment_data["priority"]
    )
```

**SLA Monitoring & Escalation:**

```python
# workflows/sla_monitor.py
@workflow.defn
class SLAMonitorWorkflow:
    """
    Side-car workflow for SLA monitoring
    
    Runs in parallel with main PA workflow
    """
    
    @workflow.run
    async def run(self, case_id: str, sla_deadline: datetime):
        """Monitor SLA and escalate if needed"""
        
        while True:
            time_remaining = sla_deadline - workflow.now()
            
            if time_remaining < timedelta(hours=0):
                # SLA BREACHED
                await workflow.execute_activity(
                    activities.handle_sla_breach,
                    {
                        "case_id": case_id,
                        "severity": "CRITICAL"
                    }
                )
                break
                
            elif time_remaining < timedelta(hours=4):
                # WARNING: Approaching SLA
                await workflow.execute_activity(
                    activities.escalate_case,
                    {
                        "case_id": case_id,
                        "reason": "SLA_WARNING",
                        "time_remaining_hours": time_remaining.total_seconds() / 3600
                    }
                )
                
                # Check every 15 minutes when close to SLA
                await asyncio.sleep(timedelta(minutes=15).total_seconds())
                
            else:
                # Normal monitoring
                await asyncio.sleep(timedelta(hours=1).total_seconds())
```

**Workflow Execution & Monitoring:**

```python
# main.py
from temporalio.client import Client
from temporalio.worker import Worker

async def main():
    # Connect to Temporal server
    client = await Client.connect("temporal.healthcare.internal:7233")
    
    # Start worker
    worker = Worker(
        client,
        task_queue="prior-auth-queue",
        workflows=[
            PriorAuthorizationWorkflow,
            ComplexClinicalReviewWorkflow,
            SLAMonitorWorkflow
        ],
        activities=[
            activities.process_intake,
            activities.check_eligibility,
            activities.check_benefits,
            activities.clinical_review,
            activities.assign_to_reviewer,
            activities.generate_decision_letter,
            # ... all other activities
        ]
    )
    
    await worker.run()

# Submit workflow
async def submit_pa_request(pa_request: PriorAuthRequest):
    client = await Client.connect("temporal.healthcare.internal:7233")
    
    # Start workflow
    handle = await client.start_workflow(
        PriorAuthorizationWorkflow.run,
        pa_request,
        id=f"pa-{pa_request.case_id}",
        task_queue="prior-auth-queue",
        execution_timeout=timedelta(days=7)  # Max workflow duration
    )
    
    # Also start SLA monitor
    await client.start_workflow(
        SLAMonitorWorkflow.run,
        args=[pa_request.case_id, calculate_sla_deadline(pa_request)],
        id=f"sla-monitor-{pa_request.case_id}",
        task_queue="sla-monitor-queue"
    )
    
    return handle

# Query workflow status
async def get_case_status(case_id: str):
    client = await Client.connect("temporal.healthcare.internal:7233")
    
    handle = client.get_workflow_handle(f"pa-{case_id}")
    
    # Query current status
    status = await handle.query(PriorAuthorizationWorkflow.get_status)
    
    return status
```

**Human Reviewer UI Integration:**

```python
# api/reviewer_endpoints.py
from fastapi import APIRouter, Depends
from temporalio.client import Client

router = APIRouter()

@router.post("/cases/{case_id}/decision")
async def submit_reviewer_decision(
    case_id: str,
    decision: ReviewerDecision,
    reviewer: Reviewer = Depends(get_current_reviewer)
):
    """
    Human reviewer submits decision via UI
    This sends a signal to the running workflow
    """
    
    client = await Client.connect("temporal.healthcare.internal:7233")
    handle = client.get_workflow_handle(f"pa-{case_id}")
    
    # Send signal to workflow
    await handle.signal(
        PriorAuthorizationWorkflow.receive_human_decision,
        {
            "determination": decision.determination,
            "rationale": decision.rationale,
            "reviewer_id": reviewer.id,
            "reviewed_at": datetime.now(),
            "modifications": decision.modifications
        }
    )
    
    return {"status": "Decision submitted to workflow"}

@router.get("/cases/{case_id}/status")
async def get_case_status(case_id: str):
    """
    Get real-time workflow status
    """
    
    client = await Client.connect("temporal.healthcare.internal:7233")
    handle = client.get_workflow_handle(f"pa-{case_id}")
    
    # Query workflow
    status = await handle.query(PriorAuthorizationWorkflow.get_status)
    
    # Get execution history for audit
    history = await handle.fetch_history()
    
    return {
        "status": status,
        "events": [
            {
                "event_type": event.event_type,
                "timestamp": event.event_time,
                "details": event
            }
            for event in history.events
        ]
    }
```

**Business Impact - Temporal vs Traditional Workflow:**

| Capability | Traditional | Temporal | Benefit |
|------------|-------------|----------|---------|
| **Process Crashes** | Workflows lost | Auto-resume | 100% reliability |
| **State Management** | Manual (DB) | Built-in durable | Zero lost state |
| **Retry Logic** | Manual code | Automatic | Simpler code |
| **Long-Running** | Complex polling | Native support | Clean design |
| **Human-in-Loop** | Polling/Webhooks | Signals/Queries | Real-time |
| **Visibility** | Custom logging | Full history | Complete audit |
| **Versioning** | Risky deploys | Safe rollouts | Zero downtime |
| **Testing** | Integration tests | Time-travel testing | Better quality |
| **Debugging** | Log analysis | Replay execution | Faster resolution |
| **SLA Monitoring** | External system | Built-in timers | Native support |

**Key Advantages:**

1. ✅ **Durability**: Workflows survive server crashes/restarts
2. ✅ **Reliability**: Automatic retries with exponential backoff
3. ✅ **Scalability**: Handles millions of concurrent workflows
4. ✅ **Visibility**: Complete execution history for audit/compliance
5. ✅ **Maintainability**: Workflow logic is plain code, not YAML/XML
6. ✅ **Testability**: Can replay workflows with different inputs
7. ✅ **Versioning**: Deploy new workflow versions without breaking running instances
8. ✅ **SLA Enforcement**: Built-in timers and timeouts
9. ✅ **Human-in-Loop**: Native support via signals/queries
10. ✅ **Debugging**: Can replay failed workflows locally

---

### 7. Memory + Knowledge Layer

**Purpose**: Multi-tier memory architecture for agent context and learning

#### Memory Architecture

```
┌─────────────────────────────────────────────────────────┐
│              MEMORY FABRIC                               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Working Memory (Redis)                                 │
│  - Current workflow state                                │
│  - Active reasoning chains                               │
│  - Intermediate outputs                                  │
│  TTL: Minutes to hours                                   │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Semantic Memory (Milvus Vector DB)                     │
│  - Clinical policies and guidelines                      │
│  - Medical knowledge                                     │
│  - Regulatory policies                                   │
│  - Coding logic and rules                                │
│  TTL: Updated on policy change                           │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Episodic Memory (PostgreSQL)                           │
│  - Prior reviewer decisions                              │
│  - Similar case outcomes                                 │
│  - Appeal results                                        │
│  - Provider behavior patterns                            │
│  TTL: 7 years (regulatory retention)                     │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Long-Term Archive (S3 / Glacier)                       │
│  - Historical cases (>7 years)                           │
│  - Immutable audit trail                                 │
│  - Compliance records                                    │
│  TTL: Indefinite                                         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### Working Memory (Redis)

**Purpose**: Fast, ephemeral storage for active workflow context

**Use Cases:**
- Store intermediate agent results
- Maintain conversation history
- Cache frequent lookups
- Distributed locks for concurrency

**Example:**
```python
class WorkingMemory:
    def __init__(self):
        self.redis = RedisClient()
    
    async def store_agent_result(self, case_id: str, agent_id: str, result: dict):
        key = f"case:{case_id}:agent:{agent_id}"
        await self.redis.setex(
            key,
            timedelta(hours=24),  # TTL
            json.dumps(result)
        )
    
    async def get_case_context(self, case_id: str) -> dict:
        """Retrieve all agent results for case"""
        pattern = f"case:{case_id}:agent:*"
        keys = await self.redis.keys(pattern)
        
        results = {}
        for key in keys:
            agent_id = key.split(":")[-1]
            result = await self.redis.get(key)
            results[agent_id] = json.loads(result)
        
        return results
```

#### Semantic Memory (Vector DB)

**Purpose**: Store and retrieve knowledge via semantic similarity

**Content:**
- **Clinical Guidelines**: MCG, InterQual, specialty society guidelines
- **Payer Policies**: Coverage policies, medical policies
- **Regulatory**: CMS NCDs/LCDs, state mandates
- **Drug Information**: Formularies, step therapy protocols
- **Coding**: ICD-10, CPT, HCPCS, and their relationships

**RAG Integration:**
```python
class SemanticMemory:
    def __init__(self):
        self.milvus = MilvusClient()
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-large")
    
    async def store_policy(self, policy: ClinicalPolicy):
        # Chunk policy into sections
        chunks = self.chunk_policy(policy)
        
        # Generate embeddings
        for chunk in chunks:
            embedding = await self.embedder.embed(chunk.text)
            
            # Store in Milvus
            await self.milvus.insert(
                collection="clinical_policies",
                data={
                    "id": chunk.id,
                    "policy_id": policy.id,
                    "text": chunk.text,
                    "embedding": embedding,
                    "metadata": {
                        "policy_name": policy.name,
                        "effective_date": policy.effective_date,
                        "specialty": policy.specialty,
                        "version": policy.version
                    }
                }
            )
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict = None
    ) -> List[Document]:
        # Embed query
        query_embedding = await self.embedder.embed(query)
        
        # Search Milvus
        results = await self.milvus.search(
            collection="clinical_policies",
            query_vector=query_embedding,
            top_k=top_k,
            filter=filters,  # e.g., {"specialty": "cardiology"}
            output_fields=["text", "metadata"]
        )
        
        return results
```

#### Episodic Memory (PostgreSQL)

**Purpose**: Store historical cases and outcomes for learning

**Schema:**
```sql
CREATE TABLE episodic_memory (
    id UUID PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    case_type VARCHAR(20), -- 'PA', 'CLAIM', 'APPEAL'
    
    -- Clinical details
    diagnosis_codes TEXT[],
    procedure_codes TEXT[],
    specialty VARCHAR(50),
    
    -- Decision
    decision VARCHAR(20), -- 'APPROVED', 'DENIED', 'PENDED'
    decision_rationale TEXT,
    decision_agent VARCHAR(50),
    decision_reviewer VARCHAR(100), -- if human
    
    -- Outcome tracking
    appealed BOOLEAN,
    appeal_outcome VARCHAR(20),
    overturned BOOLEAN,
    
    -- Context
    member_age INT,
    member_gender VARCHAR(10),
    provider_id VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP,
    confidence_score FLOAT,
    processing_time_ms INT,
    
    -- Embeddings for similarity search
    case_embedding vector(1536)
);

CREATE INDEX idx_diagnosis ON episodic_memory USING GIN(diagnosis_codes);
CREATE INDEX idx_procedure ON episodic_memory USING GIN(procedure_codes);
CREATE INDEX idx_embedding ON episodic_memory USING ivfflat(case_embedding);
```

**Usage:**
```python
class EpisodicMemory:
    async def find_similar_cases(
        self,
        current_case: Case,
        limit: int = 5
    ) -> List[HistoricalCase]:
        """Find similar historical cases to learn from"""
        
        # Generate case embedding
        case_embedding = await self.embed_case(current_case)
        
        # pgvector similarity search
        query = """
            SELECT 
                id,
                case_id,
                decision,
                decision_rationale,
                appealed,
                overturned,
                1 - (case_embedding <=> $1) AS similarity
            FROM episodic_memory
            WHERE diagnosis_codes && $2  -- overlapping diagnoses
              AND procedure_codes && $3  -- overlapping procedures
              AND specialty = $4
            ORDER BY case_embedding <=> $1
            LIMIT $5
        """
        
        results = await self.db.fetch(
            query,
            case_embedding,
            current_case.diagnosis_codes,
            current_case.procedure_codes,
            current_case.specialty,
            limit
        )
        
        return results
```

**Learning from Overturns:**
```python
async def learn_from_overturn(case_id: str):
    """When appeal overturns AI decision, learn from it"""
    
    # Retrieve original case
    original = await episodic_memory.get_case(case_id)
    
    # Store as negative example
    await training_dataset.add_example(
        input=original.clinical_summary,
        expected_output=original.appeal_decision,  # Correct decision
        actual_output=original.ai_decision,  # Wrong decision
        label="OVERTURN",
        priority="HIGH"  # High priority for retraining
    )
    
    # Flag similar cases for review
    similar = await episodic_memory.find_similar_cases(original)
    for case in similar:
        await quality_queue.add(case, reason="SIMILAR_TO_OVERTURN")
```

#### Knowledge Graph (Neo4j)

**Purpose**: Capture complex relationships for fraud detection and clinical reasoning

**Graph Model:**
```cypher
// Nodes
(Provider)
(Member)
(Claim)
(Diagnosis)
(Procedure)
(FraudCluster)
(PolicyRule)

// Relationships
(Provider)-[:SUBMITTED]->(Claim)
(Claim)-[:FOR_MEMBER]->(Member)
(Claim)-[:HAS_DIAGNOSIS]->(Diagnosis)
(Claim)-[:HAS_PROCEDURE]->(Procedure)
(Provider)-[:PART_OF]->(FraudCluster)
(Diagnosis)-[:REQUIRES]->(Procedure)
(PolicyRule)-[:COVERS]->(Procedure)
```

**Fraud Detection Example:**
```cypher
// Find providers with unusual billing patterns
MATCH (p:Provider)-[:SUBMITTED]->(c:Claim)-[:HAS_PROCEDURE]->(proc:Procedure)
WHERE proc.code = '70553'  // MRI Brain
WITH p, COUNT(c) as claim_count
MATCH (p2:Provider)-[:SUBMITTED]->(c2:Claim)-[:HAS_PROCEDURE]->(proc2:Procedure)
WHERE proc2.code = '70553'
WITH p, claim_count, AVG(COUNT(c2)) as avg_count, STDEV(COUNT(c2)) as stdev
WHERE claim_count > avg_count + (3 * stdev)  // 3 standard deviations
RETURN p.id, p.name, claim_count, avg_count
```

**Clinical Reasoning Example:**
```cypher
// Find typical treatment pathways
MATCH path = (d1:Diagnosis)-[:FOLLOWED_BY*1..5]->(d2:Diagnosis)
WHERE d1.code = 'I21.9'  // Acute MI
  AND d2.code = 'I25.10'  // Coronary artery disease
WITH path, COUNT(*) as frequency
ORDER BY frequency DESC
LIMIT 10
RETURN path, frequency
```

**Technologies:**
- **Working Memory**: Redis, Memcached
- **Vector DB**: Milvus, Pinecone, Weaviate, pgvector
- **Graph DB**: Neo4j, Amazon Neptune
- **Relational**: PostgreSQL with pgvector extension
- **Archive**: Azure Blob Storage, AWS S3 Glacier

---

### 8. RAG (Retrieval-Augmented Generation) Architecture

**Purpose**: Ground LLM responses in authoritative clinical and policy sources

#### Why RAG is Critical in Healthcare

**Problem**: LLMs hallucinate or use outdated knowledge
- **GPT-4 training cutoff**: October 2023
- **CMS policies**: Updated quarterly
- **Drug approvals**: Continuous
- **Clinical guidelines**: Annual updates

**Solution**: Retrieve current, authoritative sources before generation

#### RAG Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                  RAG PIPELINE                            │
└─────────────────────────────────────────────────────────┘

Clinical Question
      │
      ▼
┌──────────────┐
│  Query       │  "Is MRI brain medically necessary for
│  Formation   │   chronic headache >6 weeks?"
└──────────────┘
      │
      ▼
┌──────────────┐
│  Hybrid      │  Semantic Search + Keyword Search
│  Search      │  Sources: MCG, InterQual, CMS, Internal
└──────────────┘
      │
      ▼
┌──────────────┐
│  Initial     │  Retrieve top 50 candidate documents
│  Retrieval   │
└──────────────┘
      │
      ▼
┌──────────────┐
│  Reranking   │  Rerank by relevance (Cohere Rerank,
│              │  Cross-encoder)
└──────────────┘
      │
      ▼
┌──────────────┐
│  Context     │  Compress to fit context window
│  Compression │  Remove redundancy
└──────────────┘
      │
      ▼
┌──────────────┐
│  LLM         │  Generate response with citations
│  Generation  │
└──────────────┘
      │
      ▼
┌──────────────┐
│  Citation    │  Verify all claims cited
│  Validation  │  Flag hallucinations
└──────────────┘
      │
      ▼
Final Response with Evidence
```

#### Document Ingestion

```python
class RAGIngestion:
    async def ingest_clinical_guideline(self, guideline: Document):
        # 1. Document parsing
        parsed = await self.parse_pdf(guideline.file_path)
        
        # 2. Chunking strategy
        chunks = self.chunk_document(
            parsed,
            strategy="semantic",  # Preserve clinical meaning
            chunk_size=512,
            chunk_overlap=50
        )
        
        # 3. Metadata extraction
        for chunk in chunks:
            chunk.metadata = {
                "source": "MCG",
                "guideline_id": guideline.id,
                "specialty": guideline.specialty,
                "effective_date": guideline.effective_date,
                "version": guideline.version,
                "section": chunk.section_title,
                "page": chunk.page_number
            }
        
        # 4. Generate embeddings
        embeddings = await self.embedder.embed_batch(
            [chunk.text for chunk in chunks]
        )
        
        # 5. Store in vector DB
        await self.vector_db.insert_batch(
            collection="clinical_guidelines",
            texts=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadata=[chunk.metadata for chunk in chunks]
        )
        
        # 6. Index for keyword search (Elasticsearch)
        await self.es_client.bulk_index(
            index="clinical_guidelines",
            documents=chunks
        )
```

#### Hybrid Search

```python
class HybridRetriever:
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        semantic_weight: float = 0.7
    ) -> List[Document]:
        # Semantic search (vector)
        semantic_results = await self.vector_search(query, top_k=50)
        
        # Keyword search (BM25)
        keyword_results = await self.keyword_search(query, top_k=50)
        
        # Hybrid ranking (RRF - Reciprocal Rank Fusion)
        combined = self.reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            k=60  # RRF constant
        )
        
        return combined[:top_k]
    
    def reciprocal_rank_fusion(
        self,
        list1: List[Document],
        list2: List[Document],
        k: int = 60
    ) -> List[Document]:
        """Combine rankings from multiple sources"""
        scores = {}
        
        for rank, doc in enumerate(list1):
            scores[doc.id] = scores.get(doc.id, 0) + 1 / (rank + k)
        
        for rank, doc in enumerate(list2):
            scores[doc.id] = scores.get(doc.id, 0) + 1 / (rank + k)
        
        # Sort by combined score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return documents in ranked order
        doc_map = {d.id: d for d in list1 + list2}
        return [doc_map[doc_id] for doc_id, score in ranked]
```

#### Reranking

```python
class Reranker:
    def __init__(self):
        self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
    
    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 10
    ) -> List[Document]:
        # Create query-document pairs
        pairs = [[query, doc.text] for doc in documents]
        
        # Score with cross-encoder
        scores = self.model.predict(pairs)
        
        # Sort by relevance
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in doc_scores[:top_k]]
```

#### Context Compression

```python
class ContextCompressor:
    async def compress(
        self,
        documents: List[Document],
        query: str,
        max_tokens: int = 4000
    ) -> str:
        """Compress retrieved context to fit in prompt"""
        
        # Extractive summarization - keep only relevant sentences
        compressed_docs = []
        total_tokens = 0
        
        for doc in documents:
            # Extract most relevant sentences
            sentences = self.extract_relevant_sentences(
                doc.text,
                query,
                max_sentences=5
            )
            
            # Check token budget
            doc_tokens = self.count_tokens(" ".join(sentences))
            if total_tokens + doc_tokens > max_tokens:
                break
            
            compressed_docs.append({
                "source": doc.metadata["source"],
                "content": " ".join(sentences),
                "citation": self.format_citation(doc.metadata)
            })
            total_tokens += doc_tokens
        
        return compressed_docs
```

#### Citation Enforcement

```python
class CitationValidator:
    async def validate_response(
        self,
        response: str,
        source_documents: List[Document]
    ) -> ValidationResult:
        """Ensure all claims are cited"""
        
        # Extract claims from response
        claims = self.extract_claims(response)
        
        # Extract citations from response
        citations = self.extract_citations(response)
        
        # Verify each claim has citation
        uncited_claims = []
        for claim in claims:
            if not self.has_citation(claim, citations):
                uncited_claims.append(claim)
        
        # Verify citations are valid (in source documents)
        invalid_citations = []
        for citation in citations:
            if not self.verify_citation(citation, source_documents):
                invalid_citations.append(citation)
        
        is_valid = len(uncited_claims) == 0 and len(invalid_citations) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            uncited_claims=uncited_claims,
            invalid_citations=invalid_citations,
            confidence=1.0 - (len(uncited_claims) / max(len(claims), 1))
        )
```

**RAG Sources for Healthcare:**

| Source | Content | Update Frequency |
|--------|---------|------------------|
| MCG Guidelines | Medical necessity criteria | Quarterly |
| InterQual | Clinical appropriateness | Quarterly |
| CMS NCDs | National coverage | Continuous |
| CMS LCDs | Local coverage (MAC specific) | Continuous |
| FDA Drug Labels | Drug information | Continuous |
| Clinical Trials.gov | Trial data | Daily |
| PubMed | Medical literature | Daily |
| Internal Policies | Payer-specific policies | Monthly |
| Formulary | Drug coverage lists | Monthly |
| Historical Appeals | Prior case outcomes | Real-time |

**Technologies:**
- **Vector Store**: Milvus, Pinecone, Weaviate
- **Keyword Search**: Elasticsearch, OpenSearch
- **Embeddings**: OpenAI text-embedding-3-large, Cohere embed-v3
- **Reranker**: Cohere Rerank, Cross-Encoders
- **Chunking**: LangChain, LlamaIndex

---

## Data Architecture

### Data Flow

```
External Sources          Ingestion          Processing         Storage           Consumption
                                                                                  
Provider Portal  ────►   API Gateway  ────►  Validation  ────► PostgreSQL  ────►  Agent Fabric
EDI X12         ────►   EDI Parser   ────►  Transform   ────► Redis       ────►  Analytics
FHIR API        ────►   FHIR Server  ────►  Enrichment  ────► Milvus      ────►  Reporting
Fax             ────►   OCR Engine   ────►  Routing     ────► Neo4j       ────►  HITL UI
                                                         ────► Blob        ────►  APIs
                                                              Storage      ────►  Data Warehouse
```

### Data Domains

#### Transactional Data (PostgreSQL)
- Prior authorization cases
- Claims
- Member enrollment
- Provider contracts
- Audit logs

#### Cached Data (Redis)
- Active workflow state
- Session data
- Frequently accessed lookups
- Distributed locks

#### Vector Data (Milvus)
- Policy embeddings
- Guideline embeddings
- Case embeddings
- Medical knowledge

#### Graph Data (Neo4j)
- Provider networks
- Fraud rings
- Clinical pathways
- Policy dependencies

#### Unstructured Data (Blob Storage)
- PDF documents
- Fax images
- Medical records
- DICOM images

#### Analytical Data (Data Warehouse)
- Historical trends
- Performance metrics
- Business intelligence
- Regulatory reporting

### Data Governance

**PHI Protection:**
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Tokenization of sensitive fields
- De-identification for non-production
- Row-level security

**Data Retention:**
```yaml
Retention Policies:
  Active Cases: 90 days (hot storage)
  Closed Cases: 7 years (warm storage)
  Audit Logs: 10 years (cold storage)
  De-identified Analytics: Indefinite
```

**Data Quality:**
- Schema validation
- Referential integrity
- Duplicate detection
- Completeness checks
- Accuracy scoring

---

## Infrastructure Architecture

### Cloud Architecture (Azure Example)

```
┌─────────────────────────────────────────────────────────┐
│                    AZURE REGIONS                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │   East US 2      │         │   West US 2      │     │
│  │   (Primary)      │◄───────►│   (Secondary)    │     │
│  │                  │         │                  │     │
│  │  AKS Cluster     │         │  AKS Cluster     │     │
│  │  PostgreSQL HA   │         │  Read Replicas   │     │
│  │  Redis Cluster   │         │  Redis Replica   │     │
│  │  Milvus          │         │  Milvus Replica  │     │
│  │  Blob Storage    │         │  Geo-Redundant   │     │
│  └──────────────────┘         └──────────────────┘     │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 GLOBAL SERVICES                          │
├─────────────────────────────────────────────────────────┤
│  Azure Front Door (CDN + WAF)                           │
│  Traffic Manager (Global Load Balancing)                │
│  Azure AD (Identity)                                     │
│  Key Vault (Secrets)                                     │
│  Application Insights (Observability)                    │
└─────────────────────────────────────────────────────────┘
```

### Kubernetes Architecture (AKS)

```
┌─────────────────────────────────────────────────────────┐
│                 KUBERNETES CLUSTER                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │            ISTIO SERVICE MESH                     │  │
│  │  mTLS │ Traffic Management │ Observability       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Namespace: │  │  Namespace: │  │  Namespace: │    │
│  │   Agents    │  │  Platform   │  │   Data      │    │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤    │
│  │ Clinical    │  │ API Gateway │  │ PostgreSQL  │    │
│  │ Fraud       │  │ Orchestrator│  │ Redis       │    │
│  │ Policy      │  │ Temporal    │  │ Kafka       │    │
│  │ Decision    │  │ MCP Gateway │  │             │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         AUTO-SCALING (KEDA)                       │  │
│  │  Queue Depth │ CPU │ Memory │ Custom Metrics     │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Complete Technology Mapping

| Layer | Component | Technology |
|-------|-----------|------------|
| **Channel** | Provider Portal | React, Next.js |
| | API Gateway | Kong, Azure API Management |
| | EDI Processing | X12 Parser, Azure Service Bus |
| | FHIR Server | HAPI FHIR |
| | OCR | Azure Form Recognizer, Document AI |
| **Security** | Identity | Azure AD, Okta |
| | Secrets | HashiCorp Vault, Azure Key Vault |
| | WAF | Azure WAF, Cloudflare |
| | Policy Engine | Open Policy Agent (OPA) |
| | Service Mesh | Istio |
| **Orchestration** | Multi-Agent | LangGraph, CrewAI, AutoGen |
| | Workflow | Temporal, Cadence |
| | Event Bus | Apache Kafka, Azure Event Hubs |
| | State | Redis, etcd |
| **Agents** | LLM | GPT-4o, Claude 3.5 Sonnet, Gemini 1.5 Pro |
| | Framework | LangChain, LlamaIndex |
| | Observability | LangSmith, Prompt Layer |
| **Governance** | Guardrails | NeMo Guardrails, Guardrails AI |
| | PHI Detection | Microsoft Presidio |
| | Prompt Injection | Lakera, Rebuff |
| **MCP** | Gateway | Anthropic MCP SDK |
| | Discovery | Consul, etcd |
| **Memory** | Working | Redis |
| | Vector | Milvus, Pinecone, Weaviate |
| | Graph | Neo4j, Amazon Neptune |
| | Relational | PostgreSQL with pgvector |
| | Archive | Azure Blob, AWS S3 Glacier |
| **RAG** | Embeddings | text-embedding-3-large, Cohere |
| | Vector Search | Milvus, FAISS |
| | Keyword | Elasticsearch, OpenSearch |
| | Reranker | Cohere Rerank, Cross-Encoder |
| **Data** | OLTP | PostgreSQL, Azure SQL |
| | Cache | Redis, Memcached |
| | Warehouse | Snowflake, Azure Synapse |
| | Streaming | Kafka, Flink |
| **Infrastructure** | Container Orchestration | AKS, EKS, GKE |
| | CI/CD | GitHub Actions, Azure DevOps |
| | IaC | Terraform, Bicep |
| | Monitoring | Prometheus, Grafana |
| | Logging | ELK Stack, Azure Monitor |
| | Tracing | OpenTelemetry, Jaeger |

---

## Architecture Patterns

### Enterprise Multi-Agent Design Patterns

Modern enterprise AI platforms require sophisticated multi-agent coordination patterns. Below are **10 proven patterns** with real-world enterprise applications.

---

#### Pattern 1: Supervisor Pattern ⭐ (Current Implementation)

**When to Use**: Deterministic workflows with central control and state management

**How It Works:**
```
                    Supervisor Agent
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   Agent A             Agent B             Agent C
   (Task 1)           (Task 2)           (Task 3)
        │                  │                  │
        └──────────────────┴──────────────────┘
                      Report back
```

**Example**: Healthcare Prior Authorization Workflow
- Supervisor orchestrates: Intake → Eligibility → Benefits → Clinical → Decision
- Maintains shared state across all agents
- Decides routing based on business rules

**Benefits:**
- ✅ Centralized control and visibility
- ✅ Easy debugging (single orchestration point)
- ✅ Consistent state management
- ✅ Clear audit trail

**Limitations:**
- ❌ Single point of failure
- ❌ Can become bottleneck at scale

**Enterprise Use Cases**: UnitedHealth PA processing, Cigna claims workflows, Humana care management

---

#### Pattern 2: Sequential Pipeline Pattern

**When to Use**: Linear processing steps where output of one agent feeds next

**How It Works:**
```
Input → Agent 1 → Agent 2 → Agent 3 → Agent 4 → Output
       (Intake)  (OCR)     (Validate) (Fraud)   (Approve)
```

**Example**: Insurance Claims Processing
1. **Intake Agent**: Receive claim document
2. **OCR Agent**: Extract text from scanned PDFs
3. **Validation Agent**: Validate completeness
4. **Fraud Detection Agent**: Screen for red flags
5. **Approval Agent**: Final decision

**Benefits:**
- ✅ Simple to understand and implement
- ✅ Easy to monitor progress (current stage)
- ✅ Predictable flow

**Limitations:**
- ❌ No parallelism (slower)
- ❌ Failure in any stage blocks entire pipeline

**Enterprise Use Cases**: UnitedHealth claims pipeline, Cigna document processing, CVS Caremark prescription workflow

---

#### Pattern 3: Planner-Executor Pattern

**When to Use**: Complex tasks requiring dynamic multi-step reasoning

**How It Works:**
```
User Query → Planner Agent → [Plan]
                ↓
        Executor Agent
                ↓
    ┌───────────┼───────────┐
Tool 1      Tool 2      Tool 3
    │           │           │
    └───────────┴───────────┘
                ↓
          Synthesizer
```

**Example**: Appeals Processing
1. **Planner**: Analyze denial reason → Create investigation plan
   - Step 1: Retrieve original PA decision
   - Step 2: Get updated clinical evidence
   - Step 3: Check for policy changes
   - Step 4: Compare against guidelines

2. **Executor**: Execute plan dynamically

**Benefits:**
- ✅ Handles complexity and uncertainty
- ✅ Adaptive to changing requirements
- ✅ Can revise plan mid-execution

**Limitations:**
- ❌ Slower (extra planning step)
- ❌ More expensive (planner needs powerful LLM)

**Enterprise Use Cases**: Google Cloud AIOps, Datadog incident response, PagerDuty automation

---

#### Pattern 4: Reflection/Critic Pattern

**When to Use**: High-stakes decisions requiring self-validation

**How It Works:**
```
Task → Actor Agent → [Draft Response]
                          ↓
                   Critic Agent
                          ↓
                   Acceptable?
                    /         \
                  YES         NO
                   ↓           ↓
              Final Answer   Revise → Actor Agent
```

**Example**: Clinical Decision Validation
1. **Actor**: Clinical Review Agent proposes "APPROVE"
2. **Critic**: Safety Agent checks:
   - Is rationale medically sound?
   - Are all risk factors considered?
   - Is supporting evidence adequate?
3. If issues found → Actor revises decision

**Benefits:**
- ✅ Self-correction improves accuracy
- ✅ Catches errors before human review
- ✅ Built-in quality assurance

**Limitations:**
- ❌ 2x cost (two LLM calls)
- ❌ 2x latency

**Enterprise Use Cases**: GitHub Copilot code review, SonarQube auto-fix, Grammarly advanced suggestions

---

#### Pattern 5: Debate Pattern

**When to Use**: High-stakes decisions where multiple perspectives reduce risk

**How It Works:**
```
Controversial Case
        ↓
┌───────┴───────┐
│               │
Agent A      Agent B
(Approver)   (Denier)
│               │
└───────┬───────┘
        ↓
  Judge Agent
     (Final Decision)
```

**Example**: Experimental Treatment Approval
1. **Approver Agent**: "Evidence shows potential benefit..."
2. **Denier Agent**: "Risk of side effects outweighs..."
3. **Judge Agent**: Weighs both arguments → Final decision

**Benefits:**
- ✅ Reduces bias (multiple viewpoints)
- ✅ Higher quality decisions
- ✅ Built-in risk mitigation

**Limitations:**
- ❌ Expensive (3+ LLM calls)
- ❌ Slower

**Enterprise Use Cases**: JPMorgan credit risk assessment, Goldman Sachs investment analysis, Fidelity fraud detection

---

#### Pattern 6: Event-Driven Pattern ⭐

**When to Use**: Asynchronous, scalable, real-time processing

**How It Works:**
```
Event Bus (Kafka)
        │
    ┌───┴───┬───────┬───────┬───────┐
    │       │       │       │       │
Agent 1  Agent 2  Agent 3  Agent 4  Agent 5
(Listens) (Listens) (Listens) (Listens) (Listens)
    │       │       │       │       │
    └───┬───┴───────┴───────┴───────┘
        │
  Publish Events
```

**Example**: Real-Time Fraud Detection
- Event: New claim submitted
- Fraud Agent listens → Analyzes immediately
- If fraud detected → Publishes "Fraud Alert" event
- Approval Agent listens → Blocks claim automatically

**Benefits:**
- ✅ Loose coupling (agents don't know about each other)
- ✅ High scalability (add agents without changing others)
- ✅ Real-time processing

**Limitations:**
- ❌ Complex debugging (distributed events)
- ❌ Eventual consistency

**Enterprise Use Cases**: PayPal fraud detection, Visa transaction monitoring, Stripe payment processing

---

#### Pattern 7: HITL (Human-in-the-Loop) Pattern ⭐

**When to Use**: Regulated industries, high-stakes decisions, compliance requirements

**How It Works:**
```
AI Decision
    ↓
Risk Assessment
    ↓
Risk Score < 0.7?
 /           \
YES          NO
 │            │
Auto-Execute  Human Review
              ↓
         Approve/Override
```

**Example**: High-Value PA Approval
- AI recommends approval for $150,000 surgery
- Risk score: 0.82 (HIGH)
- Route to Senior Clinical Reviewer
- Human reviews → Approves with modifications

**Decision Matrix:**
| Risk Level | Confidence | Action |
|------------|------------|--------|
| Low | >95% | Auto-approve |
| Medium | 80-95% | Supervisor review |
| High | 60-80% | Human approval required |
| Critical | <60% | Escalate to board |

**Benefits:**
- ✅ Maintains human control
- ✅ Regulatory compliance (HIPAA, FDA)
- ✅ Builds trust

**Limitations:**
- ❌ Slower (human bottleneck)
- ❌ Expensive (human time)

**Enterprise Use Cases**: Pfizer drug approval, Roche clinical decisions, Johns Hopkins diagnosis support

---

#### Pattern 8: Hierarchical Pattern

**When to Use**: Enterprise-scale complexity with multiple departments/teams

**How It Works:**
```
            CEO Agent
                │
    ┌───────────┼───────────┐
    │           │           │
Dept 1 Agent  Dept 2 Agent  Dept 3 Agent
    │           │           │
┌───┴───┐   ┌───┴───┐   ┌───┴───┐
│   │   │   │   │   │   │   │   │
A   B   C   D   E   F   G   H   I
```

**Example**: Enterprise Customer Support
- **Tier 1 Agent**: Handles FAQs
- **Tier 2 Agent**: Handles complex issues
- **Tier 3 Agent**: Handles escalations
- **Manager Agent**: Oversees all tiers

**Benefits:**
- ✅ Scalability (delegation)
- ✅ Clear responsibility boundaries
- ✅ Parallel processing

**Limitations:**
- ❌ Complex coordination
- ❌ Communication overhead

**Enterprise Use Cases**: Salesforce Service Cloud, Zendesk automation, ServiceNow ITSM

---

#### Pattern 9: Blackboard Pattern

**When to Use**: Shared intelligence and collaborative problem-solving

**How It Works:**
```
        Shared Knowledge Base (Blackboard)
                    │
    ┌───────────────┼───────────────┐
    │               │               │
Agent A         Agent B         Agent C
(Writes)        (Reads)         (Writes)
    │               │               │
    └───────────────┴───────────────┘
         All agents contribute
```

**Example**: Medical Diagnosis Support
- **Blackboard**: Patient case
- **Radiology Agent**: Adds imaging findings
- **Lab Agent**: Adds test results
- **History Agent**: Adds medical history
- **Diagnosis Agent**: Synthesizes all findings → Diagnosis

**Benefits:**
- ✅ Collaborative intelligence
- ✅ No single agent has complete picture
- ✅ Emergent insights

**Limitations:**
- ❌ Coordination complexity
- ❌ Conflict resolution needed

**Enterprise Use Cases**: Mayo Clinic diagnostic support, Cerner clinical pathways, Epic care coordination

---

#### Pattern 10: Swarm Pattern

**When to Use**: Decentralized optimization problems

**How It Works:**
```
        Many Small Agents
        (Each optimizes locally)
                │
        ┌───────┼───────┐
        │       │       │
    Agent 1  Agent 2  Agent 3
        │       │       │
        └───────┴───────┘
    Emergent Global Behavior
```

**Example**: Provider Network Optimization
- Each agent optimizes provider selection for a region
- Local agents share information
- Global optimization emerges from local decisions

**Benefits:**
- ✅ Highly scalable
- ✅ Resilient (no single point of failure)
- ✅ Adaptive

**Limitations:**
- ❌ Hard to predict behavior
- ❌ May not find global optimum

**Enterprise Use Cases**: Amazon logistics, Walmart supply chain, FedEx route optimization

---

### Pattern Selection Guide

| Use Case | Recommended Pattern |
|----------|---------------------|
| Prior Authorization | Supervisor |
| Claims Processing | Sequential Pipeline |
| Appeals Analysis | Planner-Executor |
| Clinical Decision Validation | Reflection/Critic |
| Experimental Treatment Approval | Debate |
| Real-Time Fraud Detection | Event-Driven |
| High-Value Approvals | HITL |
| Multi-Department Workflows | Hierarchical |
| Complex Diagnosis | Blackboard |
| Network Optimization | Swarm |

**Current Healthcare PA Implementation**: **Supervisor + Event-Driven + HITL** (hybrid of 3 patterns)

---

### Legacy Patterns (Saga, Circuit Breaker, CQRS)

#### Pattern: Saga for Distributed Transactions

**Problem**: PA workflow spans multiple services/agents. If clinical agent fails after eligibility succeeds, need to rollback.

**Solution**: Saga pattern with compensating transactions

```python
@workflow.defn
class PASaga:
    async def run(self, request: PARequest):
        compensations = []
        
        try:
            # Step 1: Create case
            case = await self.create_case(request)
            compensations.append(lambda: self.delete_case(case.id))
            
            # Step 2: Check eligibility
            eligibility = await self.check_eligibility(case)
            compensations.append(lambda: self.reverse_eligibility(case.id))
            
            if not eligibility.is_eligible:
                raise EligibilityError("Member not eligible")
            
            # Step 3: Clinical review
            review = await self.clinical_review(case)
            compensations.append(lambda: self.reverse_review(case.id))
            
            # Step 4: Approval
            approval = await self.approve(case, review)
            
            return approval
            
        except Exception as e:
            # Execute compensations in reverse order
            for compensation in reversed(compensations):
                await compensation()
            
            raise
```

### Pattern: Circuit Breaker for External Services

**Problem**: MCG API is down, don't want to overwhelm it with retries

**Solution**: Circuit breaker pattern

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=60)
async def call_mcg_api(request):
    """Call MCG API with circuit breaker"""
    response = await mcg_client.get_guideline(request)
    return response

# Usage
try:
    guideline = await call_mcg_api(request)
except CircuitBreakerError:
    # Circuit open, use fallback
    guideline = await get_internal_policy(request)
```

### Pattern: CQRS for Read/Write Optimization

**Problem**: High read volume for reporting, don't want to impact transactional writes

**Solution**: Command Query Responsibility Segregation

```
Write Model (PostgreSQL):
  - High consistency
  - Normalized schema
  - Transaction support

Read Model (Data Warehouse):
  - Eventual consistency
  - Denormalized views
  - Optimized for analytics

Event Stream:
  - Sync via Kafka
  - CDC (Change Data Capture)
```

---

## Conclusion

This Enterprise Solution Architecture provides:
- **Scalable foundation**: Handles 50K+ PAs/day with auto-scaling
- **Resilient design**: Multi-region, failover, circuit breakers
- **Governance**: Agent, prompt, model governance built-in
- **Explainability**: RAG with citations, full audit trail
- **Security**: Zero trust, mTLS, HIPAA compliance
- **Modularity**: Microservices, event-driven, loosely coupled

All design decisions directly serve the business objectives defined in Part 1 (Business Architecture).

---

**Document Version:** 1.0  
**Last Updated:** June 1, 2026  
**Classification:** Enterprise Architecture - Solution  
**Audience:** Enterprise Architects, Solution Architects, Technical Leadership
