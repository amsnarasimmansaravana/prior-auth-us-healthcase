# Healthcare PA Platform — Complete Component, Flow & Use Case Reference

> **See also:** For maximum depth with **275 explicit connections** and per-component inbound/outbound maps, use [`13-Deep-Component-Connection-Reference.md`](./13-Deep-Component-Connection-Reference.md) (8,900+ lines).

**Source Diagram:** `plantuml/13-microservice-workflow-architecture.puml`  
**Version:** 3.0 Enhanced Edition  
**Last Updated:** June 8, 2026  
**Environment:** Production  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [End-to-End PA Workflow](#2-end-to-end-pa-workflow)
3. [Layer 1 — Presentation (6 Components)](#3-layer-1--presentation-6-components)
4. [Layer 1.5 — Integration Gateways (4 Components)](#4-layer-15--integration-gateways-4-components)
5. [Layer 2 — 60 GenAI Gateways](#5-layer-2--60-genai-gateways)
6. [Layer 3 — Orchestration (3 Components)](#6-layer-3--orchestration-3-components)
7. [Layer 4 — AI Agent Fabric (17 Agents)](#7-layer-4--ai-agent-fabric-17-agents)
8. [Layers 5–7 — Governance, MCP, Memory (8 Components)](#8-layers-57--governance-mcp-memory-8-components)
9. [Compliance & Security Layer (4 Components)](#9-compliance--security-layer-4-components)
10. [Operational Analytics Layer (5 Components)](#10-operational-analytics-layer-5-components)
11. [Layer 8 — RAG Retrieval (4 Components)](#11-layer-8--rag-retrieval-4-components)
12. [Layer 9 — Data Services (18 Components)](#12-layer-9--data-services-18-components)
13. [Layer 10 — HITL (3 Components)](#13-layer-10--hitl-3-components)
14. [Database Layer (8 Systems)](#14-database-layer-8-systems)
15. [Infrastructure Services (6 Components)](#15-infrastructure-services-6-components)
16. [Connection Flow Matrix](#16-connection-flow-matrix)
17. [State Machine & Conditional Routing](#17-state-machine--conditional-routing)
18. [Fallback, Security & Resilience Patterns](#18-fallback-security--resilience-patterns)
19. [Platform Metrics Summary](#19-platform-metrics-summary)

---

## 1. Executive Summary

### What This Platform Does

The Healthcare Insurance **Prior Authorization (PA) Multi-Agent AI Platform** automates the review and approval of medical services before they are performed. Providers submit PA requests; the platform validates eligibility, benefits, clinical necessity, policy compliance, and fraud risk; then approves, denies, or routes to human reviewers.

### Business Value

| Metric | Value | Business Impact |
|--------|-------|-----------------|
| Daily PA volume | 50,000 requests/day | Handles enterprise payer scale |
| Average turnaround | ~15 minutes | Down from 3–5 days manual |
| Automation rate | 72% auto-approved | Reduces nurse/clinical reviewer load |
| Human review rate | 28% (14,000/day) | Focuses humans on complex cases |
| Decision accuracy | 96% | Matches/exceeds manual reviewers |
| SLA compliance | 99.2% (30-min SLA) | CMS/NCQA regulatory adherence |
| Annual ROI | **$667M** | Operational savings + fraud prevention |
| System availability | 99.95% | Multi-region active-active |

### Architecture Scale (v3.0)

| Category | Count |
|----------|-------|
| Channel services | 6 |
| Healthcare integration gateways | 4 |
| GenAI orchestration gateways | 60 |
| Orchestration services | 3 |
| AI agents (core + PA-specific) | 17 |
| Governance / MCP / Memory services | 8 |
| Compliance & security services | 4 |
| Operational analytics services | 5 |
| RAG services | 4 |
| Data microservices | 18 |
| HITL services | 3 |
| Database systems | 8 |
| Infrastructure services | 6 |
| **Total components** | **70+** |

### Technology Backbone

- **Ingress:** Kong Enterprise 3.4 + LiteLLM model router
- **Orchestration:** LangGraph 0.2.15 + Temporal.io 1.22
- **LLMs:** GPT-4o (50%), Claude 3.5 Sonnet (25%), GPT-3.5 Turbo (20%), Custom ML (5%)
- **Data:** PostgreSQL, Redis, Milvus, Neo4j, Elasticsearch, Azure Blob, MongoDB, Vault
- **Events:** Kafka (200+ topics)
- **Observability:** Prometheus, Grafana, Jaeger, ELK
- **Identity:** Keycloak (OAuth2/OIDC, SSO, 2FA)
- **Cloud:** Azure (AKS, Blob, Healthcare APIs)

### Primary Bottleneck

**Clinical Agent** — 8 minutes average (53% of total processing time). LLM inference dominates; RAG retrieval is only ~5.3 seconds of the 8 minutes.

---

## 2. End-to-End PA Workflow

### Numbered Critical Path

```
① Provider submits via channel → Kong Hub
② Security validation (OAuth2, rate limit, Lakera firewall) → Workflow Engine
③ Intake Agent — OCR, classification, extraction (2 min)
④ Eligibility Agent — member/plan validation (15 sec)
⑤ Benefits Agent — coverage, tier, network (20 sec)
⑥ Clinical Agent — medical necessity + RAG (8 min) ★ BOTTLENECK
⑦ Policy Agent — rules, compliance (2.5 min)
⑧ Fraud Agent — graph ML scoring (45 sec)
⑨ Decision Agent — aggregate, confidence score (30 sec)
⑩ HITL Routing — 72% auto → Notification | 28% → Human Review Queue
```

### Phase Timing Breakdown

| Phase | Duration | % Total | Key Components |
|-------|----------|---------|----------------|
| Intake | 2 min | 13% | Intake Agent, Document Gateway, Blob Storage |
| Eligibility | 15 sec | 2% | Eligibility Agent, Member Service |
| Benefits | 20 sec | 2% | Benefits Agent, Policy/Network/Formulary Services |
| Clinical + RAG | 8 min | 53% | Clinical Agent, Milvus, Elasticsearch, Neo4j |
| Policy | 2.5 min | 17% | Policy Agent, Claude 3.5, OPA/Drools |
| Fraud | 45 sec | 5% | Fraud Agent, Neo4j GNN |
| Decision | 30 sec | 3% | Decision Agent, HITL Gateway |
| Notification | 1 min | 5% | Notification Agent, Kafka |
| **Total** | **~15 min** | **100%** | 70+ services orchestrated |

### Parallel Execution Optimizations

- **Benefits + Fraud** run concurrently after eligibility (saves ~20% vs sequential)
- **Notification + Audit** run asynchronously (non-blocking)
- **Expedited PA path:** all agents parallel for urgent cases

### Side Paths (Conditional)

| Trigger | Path |
|---------|------|
| Intake confidence <0.85 | HITL document review |
| Member ineligible | Auto-deny, terminate workflow |
| No PA required on plan | Auto-approve, skip clinical |
| Drug PA | Benefits → Step Therapy Agent |
| Duplicate PA detected | Registry Agent → reference existing |
| Missing clinical docs | Clinical → Doc Request Agent → pend |
| Denial + P2P requested | Decision → Medical Director Agent |
| Post-service ER claim | Retrospective Agent (async) |
| Urgent keywords | Expedited Agent (72hr SLA) |
| Appeal filed | Appeals Agent re-runs Clinical + Policy |

---

## 3. Layer 1 — Presentation (6 Components)

Entry points for all PA requests. **Business purpose:** meet providers and members where they work — portal, mobile, EDI, fax, phone — without forcing a single channel.

**Layer metrics:** 50,000 PA/day | 5 channels | Peak 2,500 req/hour | 99.95% SLA

---

### 3.1 Web Portal

| Attribute | Detail |
|-----------|--------|
| **Technology** | React + Node.js, WebSocket + REST |
| **Users** | Members and providers |
| **Capacity** | 100K concurrent sessions |
| **Business use case** | Primary self-service PA submission and status tracking for providers who prefer browser access |
| **Why implemented** | 50% of PA submissions historically come from web portals; real-time status reduces provider call volume |
| **Flow** | User submits PA → OAuth2 JWT → Kong Hub → Workflow Engine |
| **Also connects to** | FHIR Gateway (FHIR API submissions) |
| **Key features** | Document upload, multi-step wizard, WebSocket status updates |

---

### 3.2 Mobile App

| Attribute | Detail |
|-----------|--------|
| **Technology** | React Native (iOS/Android) |
| **Users** | Members and providers on mobile |
| **Capacity** | 50K DAU, offline-capable |
| **Business use case** | Mobile-first providers and members checking PA status on the go |
| **Why implemented** | Growing mobile usage; offline queue for rural/low-connectivity areas |
| **Flow** | Mobile API → Kong Hub; also → FHIR Gateway for SMART-on-FHIR |
| **Key features** | Push notifications, offline draft submissions |

---

### 3.3 Provider Portal

| Attribute | Detail |
|-----------|--------|
| **Technology** | Angular, SSO + 2FA |
| **Users** | Provider office staff, billing coordinators |
| **Business use case** | Admin dashboard, bulk PA upload, practice-level analytics |
| **Why implemented** | Large practices submit 100+ PAs/day; bulk upload reduces per-case overhead |
| **Flow** | SSO via Keycloak → Kong Hub → X12 Gateway for EDI bulk |
| **Also connects to** | Provider Portal Service (GraphQL backend), X12 278 Gateway |
| **Key features** | Bulk CSV/PDF upload, team management, denial analytics |

---

### 3.4 EDI Gateway

| Attribute | Detail |
|-----------|--------|
| **Technology** | X12 278/837, USTAR, AS2/SFTP |
| **Volume** | 10,000 transactions/day |
| **Business use case** | B2B machine-to-machine PA from practice management systems |
| **Why implemented** | 15% of PAs arrive via EDI; required for large hospital systems |
| **Flow** | EDI parse → Kong Hub → X12 Gateway → ePA Service → Intake Agent |
| **Standards** | ASC X12N 005010X217 (278 Health Care Services Review) |

---

### 3.5 Fax OCR Service

| Attribute | Detail |
|-----------|--------|
| **Technology** | Azure Form Recognizer |
| **Accuracy** | 98.5% (including handwriting) |
| **Business use case** | Legacy fax submissions still ~30% of PA volume in many markets |
| **Why implemented** | Cannot force all providers to digital; OCR eliminates manual data entry |
| **Flow** | Fax received → OCR → Kong Hub → Document Gateway → Intake Agent |
| **Business savings** | Eliminates 95% of manual intake FTE work ($25.3M/year) |

---

### 3.6 Voice IVR

| Attribute | Detail |
|-----------|--------|
| **Technology** | Azure Speech SDK |
| **Availability** | 24/7, multi-language |
| **Business use case** | Phone-based PA status inquiries and simple submissions for small practices |
| **Why implemented** | ~5% of providers still prefer phone; reduces call center agent load |
| **Flow** | Speech-to-text → Kong Hub → Workflow Engine (status lookup) or Intake (new submission) |

---

## 4. Layer 1.5 — Integration Gateways (4 Components)

Healthcare industry-standard interoperability layer. **Business purpose:** comply with CMS mandates for electronic PA (ePA) and enable EHR-integrated workflows that reduce provider abrasion.

---

### 4.1 HL7 FHIR Gateway

| Attribute | Detail |
|-----------|--------|
| **Standard** | FHIR R4 REST API |
| **Volume** | 100,000 calls/day |
| **Auth** | OAuth2 + SMART on FHIR |
| **Business use case** | Modern EHR integration (Epic, Cerner) for PA submission and status |
| **Why implemented** | CMS pushing FHIR-based interoperability; future-proofing against X12 deprecation |
| **Resources** | Patient/$everything, Condition, MedicationRequest, Task |
| **Flow** | EHR → FHIR Gateway → FHIR CDS Service / Workflow Engine |
| **CDS Hooks** | medication-prescribe, order-sign hooks for real-time PA alerts |

---

### 4.2 X12 278 Gateway

| Attribute | Detail |
|-----------|--------|
| **Standard** | ASC X12N 005010X217 |
| **Volume** | 30,000 transactions/day |
| **Transport** | AS2, SFTP, TA1 ACK |
| **Business use case** | Traditional EDI PA for medical services (surgery, imaging, DME) |
| **Why implemented** | Still dominant standard for medical PA; required by clearinghouses |
| **Message types** | 278 Request, Response, Inquiry, Notification |
| **Flow** | Clearinghouse → X12 Gateway → ePA Service → transform → Intake Agent |

---

### 4.3 NCPDP SCRIPT Gateway

| Attribute | Detail |
|-----------|--------|
| **Standard** | NCPDP SCRIPT 10.6 (XML) |
| **Volume** | 20,000 pharmacy PAs/day |
| **Business use case** | Pharmacy benefit manager (PBM) drug prior authorization |
| **Why implemented** | 40% of all PAs are drug-related; separate standard from medical X12 |
| **Messages** | PARequest, PAResponse, PANotification, PAAppealRequest |
| **Flow** | Pharmacy/PBM → NCPDP Gateway → ePA Service → Step Therapy Agent |

---

### 4.4 Direct Protocol Gateway

| Attribute | Detail |
|-----------|--------|
| **Standard** | HIPAA Direct (S/MIME, XDR/XDM) |
| **Volume** | 5,000 messages/day |
| **Business use case** | Secure clinical document exchange replacing fax |
| **Why implemented** | HIPAA-compliant alternative to fax; required for some state mandates |
| **Flow** | Provider Direct address → Direct Gateway → Attachment Service → Blob Storage |

---

## 5. Layer 2 — 60 GenAI Gateways

**Business purpose:** Centralize all AI/ML traffic through a governed control plane — authentication, cost control, model routing, safety, and observability — rather than letting each agent call LLMs directly.

**Control plane:** Kong Enterprise 3.4 (<50ms overhead, 10K req/sec) + LiteLLM ($52K/day, $1.04/PA)

### Tier 1 — Core Gateways (4)

| # | Gateway | Latency | Purpose | Business Why | Tech | Primary Flow |
|---|---------|---------|---------|--------------|------|--------------|
| 1 | **API Gateway** | 5ms | REST/gRPC routing | Single entry point for all API traffic | HTTP/2, gRPC, path-based routing | All channels → Kong → API Gateway |
| 2 | **AI Gateway** | 8ms | GenAI orchestration | Manage prompt chains and context centrally | Prompt templates, session state | API Gateway → AI Gateway → LiteLLM |
| 3 | **LLM Gateway** | 10ms | Model selection | Route to cheapest capable model (70% cost savings) | 3-tier fallback: GPT-4o → Claude → GPT-3.5 | AI Gateway → LLM Gateway → agents |
| 4 | **Agent Gateway** | 12ms | Multi-agent dispatch | Coordinate 17 agents via supervisor pattern | LangGraph supervisor, 11+6 agents | LLM Gateway → Agent Gateway → Workflow Engine |

### Tier 2 — Agent Communication (4)

| # | Gateway | Latency | Purpose | Business Why | Connected Agents |
|---|---------|---------|---------|--------------|------------------|
| 5 | **MCP Gateway** | 8ms | Model Context Protocol | Standardized tool sharing across agents | All agents via MCP Registry |
| 6 | **A2A Gateway** | 5ms | Agent-to-agent mesh | Direct agent messaging without orchestrator bottleneck | COM Agent, cross-agent handoffs |
| 7 | **Multi-Agent Gateway** | 15ms | Supervisor coordination | Centralized workflow state for complex cases | Workflow Engine, Decision Agent |
| 8 | **Agent Mesh Gateway** | 3ms | Service mesh for agents | Auto-scaling, health checks, failover | All agent instances |

### Tier 3 — Knowledge & Context (5)

| # | Gateway | Latency | Purpose | Business Why | Data Stores |
|---|---------|---------|---------|--------------|-------------|
| 9 | **RAG Gateway** | 45ms | Hybrid retrieval orchestration | Clinical decisions need evidence-based guidelines | Milvus + ES + Neo4j |
| 10 | **Knowledge Gateway** | 20ms | Semantic layer / ontology | Disease-drug-procedure relationships | Neo4j 500K nodes |
| 11 | **Context Gateway** | 5ms | Session state management | Maintain PA context across 7+ agent calls | Redis 6hr TTL |
| 12 | **Memory Gateway** | 8ms | Memory router | Episodic + semantic + working memory routing | Redis, PostgreSQL, Milvus |
| 13 | **Vector DB Gateway** | 50ms | Vector retrieval | Semantic search over 10M clinical embeddings | Milvus HNSW |

### Tier 4 — Tool & Integration (4)

| # | Gateway | Latency | Purpose | Business Why |
|---|---------|---------|---------|--------------|
| 14 | **Tool Gateway** | 5ms | Sandboxed tool dispatch | Secure execution of 50+ MCP tools (member lookup, tier calc) |
| 15 | **Function Calling Gateway** | 8ms | LLM tool execution | Bind LLM outputs to API calls with schema validation |
| 16 | **Enterprise Integration Gateway** | 25ms | SAP/Oracle/Salesforce | Connect to payer back-office systems |
| 17 | **SaaS Connector Gateway** | 15ms | Slack/Teams/Zendesk | Provider notifications in existing workflows |

### Tier 5 — Model & Inference (5)

| # | Gateway | Purpose | Business Why |
|---|---------|---------|--------------|
| 18 | **Model Gateway** | Model registry, canary rollout | Safe deployment of new model versions |
| 19 | **Inference Gateway** | Batch + streaming inference | Handle peak load without latency spikes |
| 20 | **GPU Gateway** | GPU acceleration | Fraud GNN and embedding generation |
| 21 | **Model Serving Gateway** | A/B testing, load balancing | Compare model performance in production |
| 22 | **Model Registry Gateway** | MLflow integration | Track model lineage for audit/compliance |

### Tier 6 — Governance & Security (8)

| # | Gateway | Latency | Purpose | Business Why | Flow |
|---|---------|---------|---------|--------------|------|
| 23 | **Guardrail Gateway** | 8ms | Hallucination detection | Prevent incorrect medical decisions (liability) | Clinical Agent output → Guardrail |
| 24 | **AI Firewall** | 10ms | Prompt injection (Lakera) | Block adversarial prompts accessing PHI | Every LLM request → Lakera |
| 25 | **Agent Firewall** | 5ms | Agent sandbox | Limit agent actions (prevent runaway API calls) | Agent execution boundary |
| 26 | **Security Gateway** | 5ms | OAuth2/JWT/mTLS | Zero-trust authentication | All ingress → Security Gateway |
| 27 | **Compliance Gateway** | 8ms | HIPAA/GDPR/SOC2 | Regulatory audit enforcement | Security → Compliance → Audit |
| 28 | **Policy Gateway** | 10ms | OPA/Drools rules | Deterministic business rules alongside LLM | Benefits/Policy agents |
| 29 | **Risk Management Gateway** | 12ms | Anomaly detection | Fraud and outlier case identification | Fraud Agent → Risk Gateway |
| 30 | **Audit Gateway** | 15ms | Immutable logging | 7-year HIPAA audit trail | All decisions → Audit Gateway → ES |

### Tier 7 — Workflow & Orchestration (5)

| # | Gateway | Purpose | Business Why |
|---|---------|---------|--------------|
| 31 | **Workflow Gateway** | LangGraph DAG execution | Visual workflow management for business users |
| 32 | **Orchestration Gateway** | Temporal durable workflows | Guarantee PA completes even if worker crashes |
| 33 | **HITL Gateway** | Route 28% to human review | Regulatory requirement for human oversight on denials |
| 34 | **Approval Gateway** | Multi-level sign-off chains | High-cost cases need director approval |
| 35 | **State Management Gateway** | Checkpoints every 30 sec | Recover from failures without restarting PA |

### Tier 8 — Observability & Operations (5)

| # | Gateway | Purpose | Business Why |
|---|---------|---------|--------------|
| 36 | **Observability Gateway** | Jaeger traces, Prometheus metrics | Debug 15-min workflows across 70+ services |
| 37 | **Monitoring Gateway** | Grafana dashboards, 50+ alerts | SLA breach detection before CMS penalties |
| 38 | **Cost Management Gateway** | $52K/day token tracking | Control LLM spend (biggest operational cost) |
| 39 | **Token Management Gateway** | Rate limiting 100 req/min | Prevent abuse and runaway costs |
| 40 | **Usage Analytics Gateway** | ROI metrics ($667M) | Prove platform value to executives |

### Tier 9 — Data & Enterprise (5)

| # | Gateway | Purpose | Business Why |
|---|---------|---------|--------------|
| 41 | **Data Gateway** | SQL/NoSQL/GraphQL routing | Unified data access for agents |
| 42 | **Data Access Gateway** | Row-level security | PHI isolation per tenant/payer |
| 43 | **Data Governance Gateway** | Lineage, PII handling | HIPAA data minimization |
| 44 | **Enterprise Data Gateway** | Data warehouse/lake federation | Analytics on PA trends |
| 45 | **Document Gateway** | OCR, PDF/DICOM processing | Intake document pipeline |

### Tier 10 — Enterprise Agent Platform (8)

| # | Gateway | Purpose | Business Why |
|---|---------|---------|--------------|
| 46 | **Agent Registry Gateway** | 50+ agent catalog | Version control and discovery |
| 47 | **Agent Discovery Gateway** | Skills-based search | Find right agent for new use cases |
| 48 | **Agent Marketplace Gateway** | Publish/deploy agents | Enable third-party agent ecosystem |
| 49 | **Agent Lifecycle Gateway** | Deploy/monitor/retire | Safe agent updates without downtime |
| 50 | **Agent Certification Gateway** | Quality + security validation | ISO 42001 compliance |
| 51 | **Agent Trust Gateway** | 96% accuracy reputation | Route to highest-trust agents |
| 52 | **Agent Identity Gateway** | mTLS + API keys | Agent-to-agent authentication |
| 53 | **Agent Governance Gateway** | RBAC permissions | Fine-grained agent access control |

### Tier 11 — Specialized Enterprise (7)

| # | Gateway | Purpose | Business Why |
|---|---------|---------|--------------|
| 54 | **Prompt Gateway** | A/B testing, LangSmith | Optimize prompts for accuracy/cost |
| 55 | **Evaluation Gateway** | HumanEval benchmarks | Continuous quality measurement |
| 56 | **Testing Gateway** | CI/CD test orchestration | Prevent regressions on deploy |
| 57 | **Simulation Gateway** | Monte Carlo what-if | Capacity planning and load testing |
| 58 | **Digital Worker Gateway** | RPA integration | Automate legacy system interactions |
| 59 | **Autonomous System Gateway** | Self-healing, auto-scaling | Reduce SRE toil |
| 60 | **Cognitive Services Gateway** | Azure Vision/Language/Speech | OCR, speech for IVR/fax pipeline |

---

## 6. Layer 3 — Orchestration (3 Components)

**Business purpose:** Reliably coordinate 17 agents across a 15-minute workflow with automatic retry, state recovery, and SLA enforcement.

---

### 6.1 Workflow Engine (LangGraph 0.2.15)

| Attribute | Detail |
|-----------|--------|
| **Pattern** | Supervisor multi-agent DAG (11 core nodes + conditional branches) |
| **Volume** | 50,000 workflows/day (2,500 peak/hour) |
| **Execution** | 72% synchronous auto | 28% async HITL pause |
| **Latency** | P50 4.2 min | P95 12.8 min | P99 28.5 min |
| **Business use case** | Route each PA through the correct sequence of AI agents based on case type |
| **Why LangGraph** | Native support for conditional edges, parallel branches, checkpointing, HITL interrupts |
| **State schema** | `PAState`: request_id, case_id, agent_outputs, messages (append-only audit) |
| **Checkpointing** | Every 30 seconds → PostgreSQL via PostgresSaver |
| **Inbound** | Security Gateway, Workflow Gateway, Multi-Tenant Config |
| **Outbound** | All 17 agents (sequential + parallel), Kafka events |
| **Implementation** | Python StateGraph with conditional_edges, interrupt_before=["decision"] for HITL |

---

### 6.2 Temporal Server (1.22)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Durable workflow execution with guaranteed completion |
| **Task queue** | pa-processing-queue (100 workers) |
| **Timeout** | 30-min execution (PA SLA), 5-min per activity |
| **Retry** | 3 attempts, exponential backoff (1s, 2s, 4s, max 60s) |
| **History** | 90-day retention, ~150 events/workflow, ~50KB each |
| **Business use case** | If Clinical Agent worker crashes at minute 6, Temporal resumes from checkpoint — no lost PA |
| **Why Temporal** | Healthcare requires durable execution; LangGraph alone cannot survive process restarts |
| **Activities** | 11 activities map 1:1 to agents (process_intake, check_eligibility, etc.) |
| **Inbound** | Orchestration Gateway, Workflow Engine |
| **Outbound** | PostgreSQL (event history) |

---

### 6.3 State Manager (Redis + PostgreSQL)

| Attribute | Detail |
|-----------|--------|
| **Hot store** | Redis 7.0 — 6-hour TTL, 500M ops/day, P50 <5ms |
| **Cold store** | PostgreSQL — 90-day snapshots, pa_workflow_state table |
| **Business use case** | Agents need shared context (member info, prior agent outputs) without re-querying |
| **Why two-tier** | Redis for speed during active PA; PostgreSQL for durability and audit |
| **Redis keys** | session:{workflow_id}, agent_state:{agent}:{workflow_id}, tool_result:{tool}:{call_id} |
| **Inbound** | State Management Gateway, Workflow Engine |
| **Outbound** | Redis cluster (3 shards), PostgreSQL |

---

## 7. Layer 4 — AI Agent Fabric (17 Agents)

**Business purpose:** Automate specialized decision domains that previously required human clinical reviewers, nurses, and analysts — while maintaining explainability and human oversight on edge cases.

**Aggregate metrics:** 450K+ invocations/day | 96.2% success | $58K/day LLM cost | 52K avg tokens/case

---

### 7.1 Agent 1 — Intake Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o Vision |
| **Latency** | 2 min avg (P95 3.5 min) |
| **Cost** | $0.285/execution |
| **Accuracy** | 97% field extraction |
| **Business purpose** | Eliminate manual data entry from faxes, portals, EDI into structured PA records |
| **Business impact** | $25.3M/year savings (450 FTEs → 50 FTEs) |
| **Use cases** | OCR fax PDFs, classify document type, extract ICD-10/CPT/NPI/member ID, validate completeness |
| **Tech stack** | Azure Form Recognizer, GPT-4o Vision, Pydantic v2, Azure Blob, PostgreSQL |
| **Gateway connections** | LiteLLM, Document Gateway, Agent Registry, Context Gateway, Observability |
| **Data connections** | Blob Storage (PDF), PostgreSQL (metadata), Registry Agent (de-dup) |
| **Output schema** | document_type, patient, provider, diagnosis, procedure, confidence_scores |
| **Fallback** | Chunking (>128K tokens) → OCR preprocessing → Claude 3.5 Vision → rule-based → HITL |
| **HITL trigger** | Confidence <0.85 (12% of cases) |

---

### 7.2 Agent 2 — Eligibility Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-3.5 Turbo |
| **Latency** | 15 sec (P95 25 sec) |
| **Cost** | $0.003/execution |
| **Cache hit** | 85% (Redis 24hr TTL) |
| **Business purpose** | Verify member has active coverage before expensive clinical review |
| **Business impact** | $12M/year cost avoidance (block 800K ineligible requests) |
| **Use cases** | Member lookup, plan active check, COB detection, duplicate PA check |
| **Validation rules** | Member exists, plan active on service date, PA benefit exists, in-network check |
| **Tech** | Member Service (gRPC), Redis cache, MCP member_lookup tool |
| **Auto-deny** | Member not found or inactive plan → terminate workflow |
| **Fallback** | Redis cache → PostgreSQL replica → HITL manual lookup |

---

### 7.3 Agent 3 — Benefits Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o |
| **Latency** | 20 sec (P95 35 sec) |
| **Cost** | $0.300/execution |
| **Business purpose** | Determine if service is covered, calculate cost-sharing, identify PA requirements |
| **Business impact** | $18M/year preventing incorrect approvals |
| **Use cases** | Tier determination (Bronze/Silver/Gold), network status, formulary tier, step therapy flag |
| **Decision trees** | 12 trees: plan type, service category, network, cost share, limits, step therapy, etc. |
| **Tech** | Policy Gateway (OPA 50+ rules), Benefits Config Service, Network Service, Formulary Service |
| **Side path** | Drug PA → Step Therapy Agent (Agent 13) |
| **Auto-approve path** | No PA required on plan → skip clinical, go to notification |

---

### 7.4 Agent 4 — Clinical Agent ★ BOTTLENECK

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o + Hybrid RAG |
| **Latency** | 8 min avg (53% of total time) |
| **Cost** | $0.780/execution (highest cost agent) |
| **Accuracy** | 96% medical necessity | 4% human overturn rate |
| **Business purpose** | Determine medical necessity using evidence-based guidelines (MCG, InterQual, CMS LCD) |
| **Business impact** | $57.6M/year (800 FTEs → 160 FTEs) |
| **Use cases** | Match patient presentation to guideline criteria, step therapy validation, contraindication check |
| **RAG queries** | 20 per request: 8 vector, 6 keyword, 4 graph, 2 episodic memory |
| **Guidelines** | MCG 80%, InterQual 60%, CMS LCD 25%, specialty societies 40% |
| **Latency breakdown** | RAG 2.7s (0.6%) + context prep 5s (1%) + **LLM inference 472s (98.4%)** |
| **Gateway connections** | RAG Gateway, VectorDB, Knowledge Gateway, Memory Gateway, Guardrail Gateway |
| **RAG flow** | Clinical → VectorSearch + HybridSearch + GraphRAG → RRF → ClinicalContentService |
| **HITL trigger** | Confidence <0.85 (15%) or <0.60 auto-deny |
| **Side path** | Low confidence → Doc Request Agent (Agent 17) for pend |
| **Optimization planned** | GPT-4o Turbo testing, 40% RAG cache hit, speculative Decision Agent start |

---

### 7.5 Agent 5 — Policy Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | Claude 3.5 Sonnet |
| **Latency** | 2.5 min (P95 4 min) |
| **Cost** | $0.111/execution (5x cheaper than GPT-4o for input) |
| **Business purpose** | Interpret 100K+ policy documents, validate regulatory compliance |
| **Use cases** | Medical/drug/admin policy evaluation, state mandate checking, OPA 50+ rules |
| **Why Claude** | 200K context window, superior logical reasoning for complex policies |
| **Compliance** | HIPAA, SOC2, NCQA HEDIS, 50-state mandate variations |
| **Connections** | Policy Gateway (OPA/Drools), Compliance Gateway, Policy Service, State Mandate Service |
| **Auto-deny** | Policy violation detected → terminate with compliance citation |

---

### 7.6 Agent 6 — Fraud Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | Custom Graph Neural Network (PyTorch Geometric) + GPT-4o narrative |
| **Latency** | 45 sec (P95 75 sec) |
| **Precision** | 94% | Recall 98% | F1 0.96 |
| **Business purpose** | Detect billing fraud, upcoding, phantom billing, kickback schemes |
| **Business impact** | $32M/year fraud prevention |
| **Use cases** | Provider billing pattern analysis, member collusion, duplicate services |
| **Risk scoring** | 0-30 low (auto) | 31-60 medium | 61-80 high (HITL mandatory) | 81-100 critical (deny) |
| **Tech** | Neo4j GNN (500K nodes, 2M edges), GPUGateway, Claims Service |
| **Runs parallel with** | Benefits Agent (20% time savings) |
| **HITL trigger** | Risk score >60 (0.8% of cases) |

---

### 7.7 Agent 7 — Decision Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o |
| **Latency** | 30 sec (P95 50 sec) |
| **Automation** | 72% auto-adjudicated |
| **Business purpose** | Synthesize all agent outputs into final APPROVE/DENY/PEND determination |
| **Decision logic** | Weighted confidence: Clinical 50%, Policy 30%, Fraud 20% |
| **Routing rules** | All >0.85 AND risk <30 → auto | Any <0.70 OR risk >30 → HITL |
| **HITL breakdown** | Low confidence 20%, fraud 5%, all denials 10%, high cost 3%, complex 12%, random 10% |
| **Connections** | HITL Gateway, Approval Gateway, Memory Gateway, Agent Governance Gateway |
| **Output** | decision, confidence, reasoning, citations, hitl_required, estimated_cost |
| **Side paths** | Denial + P2P → Medical Director Agent | HEDIS tracking → Quality Measure Service |

---

### 7.8 Agent 8 — Notification Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-3.5 Turbo |
| **Latency** | 1 min | Delivery rate 99.5% |
| **Business purpose** | Communicate PA decisions to members, providers, authorized reps |
| **Regulatory** | Appeal rights disclosure, denial reason codes, CMS letter formats |
| **Channels** | Email (SendGrid 100%), SMS (Twilio 80%), Portal (100%), Slack/Teams (20%) |
| **Templates** | 25 variants: approval, denial, pend, HITL, appeal decision |
| **Connections** | SaaS Connector Gateway, Kafka, Comm Preference Service, DLP Service (PHI scan) |
| **Personalization** | GPT-3.5 generates plain-language explanations for members |

---

### 7.9 Agent 9 — Audit Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o (async) |
| **Coverage** | 100% of PHI access and agent actions |
| **Retention** | 7 years (HIPAA) |
| **Business purpose** | Immutable audit trail for CMS, state DOI, NCQA accreditation audits |
| **Business impact** | $2.5M/year regulatory fines avoided |
| **Events logged** | User actions, agent executions, decision overrides, security events |
| **Tech** | PostgreSQL append-only, Elasticsearch full-text, Azure Confidential Ledger |
| **Connections** | Audit Gateway, Compliance Gateway, Data Governance Gateway |
| **Reports** | Quarterly HIPAA, continuous SOC2, state prior auth metrics |

---

### 7.10 Agent 10 — Appeals Agent

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o |
| **Latency** | 10 min avg |
| **Volume** | 1,000 appeals/day (2% of denials) |
| **Overturn rate** | 40% approved on appeal |
| **Business purpose** | Process member/provider appeals within regulatory timelines |
| **SLA** | 30-day review (95% compliance) |
| **Process** | Intake new evidence → re-run Clinical + Policy → peer review → determination |
| **Connections** | HITL Gateway, Grievance Track Service, all original agent tools |
| **Categories** | Clinical, administrative, experimental, network appeals |

---

### 7.11 Agent 11 — COM Agent (Coordination of Benefits)

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o + Drools rules engine |
| **Volume** | 5,000/day (multi-coverage cases) |
| **Business purpose** | Determine primary/secondary payer when member has multiple insurances |
| **Business impact** | $15M cost recovery + $8M duplicate payment prevention |
| **Rules** | Medicare MSP, birthday rule, court orders, dual eligible |
| **Connections** | A2A Gateway, Workflow Gateway, Provider Service, X12 270/271 |
| **Use cases** | Medicare + commercial, dual eligible, workers comp coordination |

---

### 7.12 Agent 12 — Expedited PA Agent (v3.0 NEW)

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o (priority queue) |
| **Volume** | 7,500/day (15%) |
| **SLA** | 72 hours regulatory (42 CFR 438.210) |
| **Business purpose** | CMS-mandated fast-track for urgent/life-threatening cases |
| **Triggers** | Keywords: "emergency", "urgent", "stat", "life-threatening" |
| **Workflow** | All agents run in parallel; 24/7 medical director; 85% auto-approve threshold |
| **Connections** | Workflow Engine (urgent route), SLAMonitorService |
| **State variance** | CA 24hr, TX 24hr, NY 72hr via State Mandate Engine |

---

### 7.13 Agent 13 — Step Therapy Agent (v3.0 NEW)

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o + OPA rule engine |
| **Volume** | 20,000 drug PAs/day (40% of drug PAs) |
| **Latency** | 30 sec |
| **Business purpose** | Validate patient tried cheaper drugs before approving brand/specialty |
| **Business impact** | $4.2M/month savings (12% generic utilization increase) |
| **Logic** | Tier 1-2: no step | Tier 3: 1 prior drug | Tier 4-5: 2 prior | Tier 6: 3 prior + specialist |
| **Connections** | Benefits Agent trigger, Claims Service (prior fills), Drug Reference Service, NCPDP Gateway |
| **Exceptions** | Allergy, contraindication, prior trial documented, emergency override |

---

### 7.14 Agent 14 — Medical Director Review Agent (v3.0 NEW)

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o (clinical summary generation) |
| **Volume** | 1,400 peer-to-peer reviews/day |
| **Business purpose** | Automate peer-to-peer scheduling for complex denials |
| **Workflow** | Generate 1-page clinical summary → match specialty → Calendly scheduling → Teams call |
| **Overturn rate** | 40% after P2P | 25% partial approval |
| **Connections** | Decision Agent trigger, Provider Portal Service, LiteLLM |
| **Time savings** | 15 min/call prep (vs 45 min manual) |

---

### 7.15 Agent 15 — Retrospective Review Agent (v3.0 NEW)

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o + RAG |
| **Volume** | 2,500/day (5%) |
| **SLA** | 30-day async |
| **Business purpose** | Validate medical necessity for ER/urgent care rendered before PA |
| **Business impact** | $8.5M/month cost recovery from inappropriate ER utilization |
| **Criteria** | Emergency necessity, appropriate setting, post-stabilization justification |
| **Connections** | Claims Service (UB-04), Workflow Engine (async), Clinical RAG pipeline |
| **Outcomes** | 70% approved, 20% partial, 10% denied |

---

### 7.16 Agent 16 — PA Registry Agent (v3.0 NEW)

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-3.5 Turbo |
| **Latency** | <1 sec (95% Redis cache hit) |
| **Volume** | 50,000 checks/day (100% screened) |
| **Business purpose** | Detect duplicate PAs and auto-renew chronic authorizations |
| **Business impact** | $2.1M/month (12% duplicates = 6,000/day avoided reprocessing) |
| **Duplicate logic** | Exact match, near match (±7 days), fuzzy ICD-10 chapter match |
| **Renewal** | Auto-approve 90-day extension for stable chronic conditions |
| **Connections** | Intake Agent trigger, Redis active PA cache, PostgreSQL 150M records |

---

### 7.17 Agent 17 — Clinical Doc Request Agent (v3.0 NEW)

| Attribute | Detail |
|-----------|--------|
| **Model** | GPT-4o |
| **Volume** | 12,500 pends/day (25% of PAs) |
| **Latency** | 2 min |
| **Business purpose** | Auto-generate specific documentation requests instead of generic "need more info" |
| **Top pend reasons** | Missing labs 35%, incomplete diagnosis 20%, no prior treatment 15% |
| **Workflow** | Clinical confidence <0.60 → identify gaps → generate questions → notify provider → re-trigger on upload |
| **Resolution** | 85% providers submit within 48hr; 80% approved post-docs |
| **Connections** | Clinical Agent trigger, Attachment Service, Notification Agent |

---

## 8. Layers 5–7 — Governance, MCP, Memory (8 Components)

---

### 8.1 Agent Registry

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Central catalog of 50+ agents with versioning and capabilities |
| **Business why** | ISO 42001 requires agent inventory; enables safe updates and rollbacks |
| **Tech** | PostgreSQL metadata store, semantic versioning |
| **Flow** | Intake Agent loads config v2.1.0 at startup; all agents register on deploy |
| **Volume** | 385,000 governance checks/day |

---

### 8.2 Prompt Management (LangSmith)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Version control, A/B testing, and optimization of LLM prompts |
| **Business why** | Prompt changes can shift approval rates 2-3%; must be tested before production |
| **Tech** | LangSmith, DSPy optimization, Chi-square significance testing |
| **Flow** | Policy Agent uses A/B tested prompt variants; 80/20 traffic split |
| **Example** | Intake "medical_form_v2.3" wins at 98% vs 95% baseline |

---

### 8.3 Safety Evaluation (Guardrails AI)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Hallucination detection, toxicity filtering, PII redaction on every agent output |
| **Business why** | Zero tolerance for incorrect medical decisions or PHI leakage |
| **Tech** | Guardrails AI, Presidio PII detection |
| **Flow** | Clinical Agent output → Safety Eval → pass/fail before Decision Agent |
| **Target** | 99.9% safe outputs |

---

### 8.4 MCP Registry

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Catalog 50+ MCP tools (member_lookup, tier_calculator, claims_history, etc.) |
| **Business why** | Standardized tool discovery prevents agents from calling APIs directly |
| **Tech** | Model Context Protocol, PostgreSQL tool registry, gRPC |
| **Volume** | 200,000+ tool invocations/day |

---

### 8.5 Tool Executor

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Sandboxed execution of MCP tools in Docker containers |
| **Business why** | Prevent agents from executing arbitrary code or accessing unauthorized data |
| **Tech** | Docker sandbox, CPU 1 core / 512MB RAM / 30sec timeout limits |
| **Flow** | Eligibility Agent → Tool Gateway → Tool Executor → Member Service |
| **Secrets** | HashiCorp Vault for API keys |

---

### 8.6 Working Memory (Redis)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Active session context during PA processing (agent outputs, conversation history) |
| **TTL** | 6 hours |
| **Volume** | 500M ops/day, P50 <5ms |
| **Business why** | Agents must share state without re-querying databases between steps |
| **Keys** | session:{workflow_id}, conversation:{workflow_id}, agent_state:{agent}:{wf_id} |

---

### 8.7 Episodic Memory (PostgreSQL)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Historical PA decisions for precedent lookup and audit |
| **Records** | 150M episodes, 550M agent execution logs |
| **Retention** | 7 years (HIPAA) |
| **Business why** | "Similar cases approved before" improves clinical consistency |
| **Algorithm** | Jaccard similarity on diagnosis/procedure codes + temporal decay |

---

### 8.8 Semantic Memory (Milvus)

| Attribute | Detail |
|-----------|--------|
| **Purpose** | Vector embeddings of case summaries for semantic similarity search |
| **Vectors** | 10M embeddings, 1024-dim BGE-large-en-v1.5 |
| **Business why** | Find conceptually similar cases even when codes differ |
| **Flow** | Clinical Agent → Memory Gateway → Semantic Memory → similar case precedents |

---

## 9. Compliance & Security Layer (4 Components)

---

### 9.1 DLP Service (Microsoft Purview)

| Purpose | Real-time PHI detection and blocking in outbound notifications and logs |
| Business why | HIPAA requires preventing PHI from leaking to unauthorized channels |
| Flow | Notification Agent output → DLP scan → block/redact if PHI detected |
| Also scans | Audit Agent logs before indexing |

---

### 9.2 Consent Management (OneTrust)

| Purpose | Track HIPAA authorizations for data sharing and payer exchange |
| Business why | CMS payer data portability rule requires documented consent |
| Flow | Payer Exchange Service → Consent check → allow/deny FHIR export |

---

### 9.3 Breach Notification (Automated)

| Purpose | Detect breaches and auto-generate HHS/OCR reports within 72-hour mandate |
| Business why | HIPAA Breach Notification Rule; manual process too slow and error-prone |
| Flow | DLP Service breach detect → Breach Notify → PostgreSQL incident log → HHS report |

---

### 9.4 State Mandate Engine

| Purpose | Apply 50-state variations in PA rules, SLAs, and notification requirements |
| Business why | Texas requires 24hr urgent PA; California has different appeal timelines |
| Rules | 500+ state-specific rules |
| Flow | Policy Agent → State Mandate Service → PostgreSQL 50-state DB |

---

## 10. Operational Analytics Layer (5 Components)

---

### 10.1 Capacity Planning (Prophet ML)

| Purpose | Forecast PA volume and HITL staffing needs |
| Business why | Under-staffing causes SLA breaches ($CMS penalties); over-staffing wastes budget |
| Accuracy | 92% volume forecast |
| Flow | Historical PostgreSQL data → Prophet → HITL Routing staffing plan |

---

### 10.2 Root Cause Analysis (ML Clustering)

| Purpose | Identify patterns in denials and auto-suggest fixes |
| Business why | Reduce appeal rate (8% → 3% target saves $23M/year) |
| Flow | Decision Agent denials → Elasticsearch logs → ML clustering → pattern report |

---

### 10.3 Provider Analytics (Power BI)

| Purpose | Track provider PA success rates, identify outliers |
| Business why | High-denial providers may need education; fraud patterns surface here |
| Flow | Provider Service data → Analytics DB → Power BI dashboards |

---

### 10.4 Member Communication Preference (Redis + PostgreSQL)

| Purpose | Route notifications to member's preferred channel and language |
| Business why | TCPA/SMS opt-in compliance; member satisfaction (4.5/5 notification clarity) |
| Delivery success | 95% |
| Flow | Notification Agent → Comm Preference Service → channel selection |

---

### 10.5 Multi-Tenant Config (MongoDB)

| Purpose | Per-payer workflow customization (5 payer profiles, 10M members) |
| Business why | SaaS model — each payer has different rules, thresholds, branding |
| Flow | Workflow Engine loads payer config at PA start → MongoDB config store |
| Examples | Auto-approve threshold $5K vs $2K; custom agent routing rules |

---

## 11. Layer 8 — RAG Retrieval (4 Components)

**Business purpose:** Ground clinical and policy decisions in evidence-based guidelines — not LLM training data — to reduce hallucination and support audit defensibility.

**Total pipeline:** ~250ms parallel | 20 queries/PA | 1M queries/day | 96% relevant in top 10

---

### 11.1 Vector Search (Milvus HNSW)

| Attribute | Detail |
|-----------|--------|
| **Embeddings** | BGE-large-en-v1.5, 1024-dim |
| **Index** | HNSW (M=16, ef=200) |
| **Collections** | clinical_guidelines (5M), policy_documents (3M), case_precedents (2M) |
| **Latency** | P50 25ms, P95 45ms |
| **Use case** | Semantic similarity: "diabetes management for CPT 99213" |
| **Flow** | Clinical Agent → VectorSearch → Milvus → scores to RRF |

---

### 11.2 Hybrid Search (Elasticsearch BM25)

| Attribute | Detail |
|-----------|--------|
| **Algorithm** | BM25 (k1=1.2, b=0.75) |
| **Index** | 500K+ documents, 400GB, 5 shards × 2 replicas |
| **Latency** | P50 50ms, P95 85ms |
| **Use case** | Exact code matching: "ICD-10 E11.9 prior authorization" |
| **Features** | Fuzzy matching (≤2 edits), field boosting (title^3), medical synonym expansion |
| **Flow** | Clinical Agent → HybridSearch → Elasticsearch → scores to RRF |

---

### 11.3 Graph RAG (Neo4j Cypher)

| Attribute | Detail |
|-----------|--------|
| **Graph** | 500K nodes, 2M relationships |
| **Node types** | Diagnosis, Procedure, Medication, Guideline, Provider, Policy |
| **Latency** | P50 80ms, P95 120ms |
| **Use case** | Relationship traversal: diagnosis → supports → guideline → supports → procedure |
| **Algorithms** | Community detection (fraud), path finding, centrality |
| **Flow** | Clinical Agent → GraphRAG → Neo4j → scores to RRF |

---

### 11.4 Reciprocal Rank Fusion (RRF)

| Attribute | Detail |
|-----------|--------|
| **Formula** | RRF_score(d) = Σ 1/(k + rank_i(d)), k=60 |
| **Latency** | 15ms |
| **Output** | Top 10 ranked documents with citations |
| **Dedup** | Exact ID match + cosine similarity >0.95 fuzzy dedup |
| **Flow** | Vector + BM25 + Graph scores → RRF → ClinicalContentService → Clinical Agent context |

---

## 12. Layer 9 — Data Services (18 Components)

**Business purpose:** Provide governed, cached access to payer domain data (members, providers, policies, claims) without agents querying databases directly.

**Aggregate:** 3.5M+ API calls/day | 75% cache hit | gRPC primary (70%) | REST fallback (30%)

---

### 12.1 Member Service

| Volume | 2M queries/day | P95 50ms |
| Purpose | Member demographics, eligibility, enrollment history |
| Business use | Every PA starts with "is this member covered?" |
| Tech | gRPC + REST, PostgreSQL (5M members), Redis 24hr cache |
| API | GetMember, ValidateEligibility, GetMemberPlans, SearchMembers |
| Used by | Eligibility Agent, Registry Agent, COM Agent |

---

### 12.2 Provider Service

| Volume | 500K queries/day | P95 75ms |
| Purpose | NPI registry, credentialing, network status, geo-search |
| Business use | Validate ordering provider is legitimate and in-network |
| Tech | gRPC + REST, PostgreSQL + PostGIS, NPPES daily sync |
| Used by | Eligibility Agent, Fraud Agent, Med Director Agent, Provider Analytics |

---

### 12.3 Policy Service

| Volume | 100K queries/day | P95 150ms |
| Purpose | 100K+ medical/drug policies, coverage rules, OPA evaluation |
| Business use | "Is this procedure covered under this plan?" |
| Tech | REST, PostgreSQL, OPA Rego rules engine |
| Used by | Benefits Agent, Policy Agent, FHIR CDS Service |

---

### 12.4 Claims Service

| Volume | 400K queries/day |
| Purpose | 150M+ claims history, payment patterns, prior fills |
| Business use | Step therapy validation, fraud detection, retrospective review |
| Tech | REST + batch, PostgreSQL, Kafka events |
| Used by | Fraud Agent, Step Therapy Agent, Retrospective Agent |

---

### 12.5 Benefits Config Service

| Volume | 300K queries/day |
| Purpose | Plan tier structures (Bronze/Silver/Gold/Platinum), cost-sharing rules |
| Used by | Benefits Agent |

---

### 12.6 Network Service

| Volume | 250K queries/day |
| Purpose | In/out-of-network status, tier levels, network adequacy |
| Used by | Benefits Agent, Eligibility Agent |

---

### 12.7 Formulary Service

| Volume | 80K queries/day |
| Purpose | Drug coverage tiers, PA requirements per NDC, quantity limits |
| Used by | Benefits Agent, Step Therapy Agent, FHIR CDS Service |

---

### 12.8 Clinical Content Service

| Volume | 50K queries/day |
| Purpose | MCG, InterQual, CMS LCD content serving for RAG pipeline |
| Tech | REST, Elasticsearch index, PostgreSQL metadata |
| Used by | RRF output delivery to Clinical Agent |

---

### 12.9 ePA Service (NEW)

| Volume | 30K/day (60% of total) |
| Purpose | Transform X12 278 / NCPDP SCRIPT to internal format and back |
| Business use | EHR-integrated PA without portal login (4.7/5 provider satisfaction) |
| EHR integrations | Epic 40%, Cerner 25%, Allscripts 10%, Athena 8% |
| Flow | X12/NCPDP → parse → Intake Agent JSON → decision → X12 response |
| Auto-approval | 75% (better data quality than manual submissions) |

---

### 12.10 FHIR CDS Hooks Service (NEW)

| Volume | 100K hooks/day |
| Purpose | Real-time alert at prescribing time if PA required |
| Business impact | 60% PA avoidance (provider chooses covered alternative) |
| Hook | medication-prescribe → check Formulary + Policy → card with alternatives |
| Flow | EHR → FHIR Gateway → CDS Hooks → FormularyService + PolicyService |

---

### 12.11 Attachment Handling Service (NEW)

| Volume | 40K/day (80% of PAs have attachments) |
| Purpose | HL7 CDA, DICOM, PDF document management |
| Flow | Upload → Blob Storage → Elasticsearch index → Clinical Agent RAG |
| Used by | Doc Request Agent, Direct Gateway |

---

### 12.12 Drug Reference Service (NEW)

| Volume | 120K/day | 95% cache hit |
| Purpose | RxNorm/NDC code lookup, drug interactions, formulary crosswalk |
| Used by | Step Therapy Agent, Code Validation Service |

---

### 12.13 Code Validation Service (NEW)

| Volume | 50K/day | 5% rejection rate |
| Purpose | Validate ICD-10 diagnosis and CPT/HCPCS procedure codes exist and are valid |
| Flow | Intake Agent → Code Validation → reject invalid codes before processing |
| Tech | Redis code cache, annual CMS code set updates |

---

### 12.14 SLA Monitor Service (NEW)

| Volume | 50K/day | 2% breach detection |
| Purpose | Track regulatory deadlines (72hr urgent, 30-day standard) |
| Flow | Workflow Engine → SLA Monitor → PostgreSQL deadlines → alert on breach |
| Tech | Temporal integration for timer-based SLA tracking |

---

### 12.15 Quality Measure Service (NEW)

| Volume | 10K/day |
| Purpose | HEDIS/NCQA quality measure tracking for Medicare Stars ratings |
| Business impact | $50M bonus impact from Stars rating improvement |
| Flow | Decision Agent → Quality Measure → PostgreSQL Stars data |

---

### 12.16 Payer Exchange Service (NEW)

| Volume | 5K/day |
| Purpose | CMS-mandated FHIR bulk export for payer-to-payer data portability |
| Flow | FHIR Gateway → Consent check → PostgreSQL PA transfer record |

---

### 12.17 Provider Portal Service (NEW)

| Volume | 20K logins/day | 70% adoption |
| Purpose | GraphQL backend for provider self-service portal |
| Flow | Provider Portal UI → GraphQL API → PostgreSQL PA status |

---

### 12.18 Grievance Track Service (NEW)

| Volume | 2K/day | 30-day SLA |
| Purpose | Appeal and grievance workflow tracking |
| Flow | Appeals Agent → Grievance Track → PostgreSQL timeline → Notification |

---

## 13. Layer 10 — HITL (3 Components)

**Business purpose:** Regulatory and clinical safety requirement — humans review cases the AI cannot confidently adjudicate.

**Volume:** 14,000 reviews/day (28%) | Auto-approved: 36,000/day (72%)

---

### 13.1 HITL Routing (Drools Rules)

| Attribute | Detail |
|-----------|--------|
| **Rules** | 50+ decision rules |
| **Triggers** | Low confidence <0.85 (20%), fraud risk >0.30 (5%), all denials (10%), high cost (3%), complex clinical (12%), random sample (10%) |
| **Priority** | Fraud > Denial > Complex > Low confidence |
| **Business why** | Automate routing logic that nurse managers previously did manually |
| **Inbound** | Decision Agent (step ⑩) |
| **Outbound** | Review Queue (28%) or Notification Agent (72%) |

---

### 13.2 Review Queue (React UI)

| Attribute | Detail |
|-----------|--------|
| **Reviewers** | 50+ clinical reviewers, nurses, medical directors |
| **Assignment** | Load-balanced, priority queue |
| **SLA** | <4 hours average, P95 <8 hours |
| **Features** | Full agent output visibility, guideline citations, override with reason |
| **Permissions** | RBAC — reviewers cannot approve above their authority level |

---

### 13.3 Approval Workflow (Temporal)

| Attribute | Detail |
|-----------|--------|
| **Stages** | Initial review → Escalation (5%) → Final approval |
| **Avg time** | 45 minutes (range 10–120 min) |
| **Audit** | 100% logged to PostgreSQL + Kafka |
| **Callback** | Approval/denial → Notification Agent (3 channels) |
| **Business why** | Multi-level approval for high-cost cases (>$50K) requires director sign-off |

---

## 14. Database Layer (8 Systems)

| Database | Size | Purpose | Used By | Business Why |
|----------|------|---------|---------|--------------|
| **PostgreSQL 15** | 6 TB, 6 DBs, 10K tps | Transactional data: members, claims, workflow state, audit | All data services, State Manager, Audit Agent | ACID compliance for financial/clinical records |
| **Redis 7.0** | 26 GB, 3 shards | Cache, working memory, rate limits, sessions | All services (85% hit rate), State Manager | Sub-5ms reads for 500M ops/day |
| **Milvus 2.3** | 1.2 TB, 10M vectors | Clinical/policy/case embeddings for RAG | Vector Search, Semantic Memory | Semantic search over medical content |
| **Neo4j 5.x** | 200 GB, 500K nodes | Knowledge graph, fraud patterns, clinical pathways | Graph RAG, Fraud Agent | Relationship queries impossible in SQL |
| **Elasticsearch 8** | 400 GB, 500K docs | BM25 full-text, audit log search, attachment index | Hybrid Search, Audit Agent, Attachment Service | Fast text search with fuzzy matching |
| **Azure Blob** | 10 TB, 2M objects | PDF, DICOM, TIFF document storage | Intake Agent, Attachment Service, Notification | Cheap durable storage for clinical documents |
| **MongoDB 7** | 500 GB | Multi-tenant payer configuration | Multi-Tenant Service | Flexible schema for per-payer customization |
| **HashiCorp Vault** | 50 GB | Secrets, API keys, PKI certificates | Tool Executor, all services | Zero-trust secret management |

---

## 15. Infrastructure Services (6 Components)

| Service | Purpose | Business Why | Connections |
|---------|---------|--------------|-------------|
| **Kafka** | Event bus, 6 brokers, 200+ topics | Decouple agents from downstream systems; enable replay | Workflow Engine, Notification, Audit, Claims publish; Notification consumes |
| **Prometheus** | 200+ metrics, 15-day retention | SLA monitoring, capacity planning | Scrapes Workflow Engine, Kafka, PostgreSQL, Redis |
| **Grafana** | 20+ dashboards | Executive and ops visibility into PA throughput, latency, cost | Queries Prometheus; caches in Redis |
| **Jaeger** | 100% distributed tracing | Debug 15-min workflows spanning 70+ services | Traces from Workflow Engine, all agents, RAG spans |
| **Keycloak** | OpenID Connect SSO + 2FA | Provider authentication, RBAC | Configures Security Gateway; user DB in PostgreSQL |
| **ELK Stack** | Centralized logging (via Observability Gateway) | Compliance log retention, slow query investigation | RAG query logs, audit events, error logs (30-day retention) |

---

## 16. Connection Flow Matrix

### Primary Request Flow

```
[Channel] → Kong Hub → Security Gateway → AIFirewall → Guardrail → Compliance → Audit
    → Workflow Engine → Agent Chain → Decision → HITL or Notification → Audit
```

### Agent → Gateway → Data Flow

| Agent | Upstream Gateways | Downstream Services | Databases |
|-------|-------------------|---------------------|-----------|
| Intake | LiteLLM, Document, Agent Registry, Context | Registry Agent, Code Validation | Blob, PostgreSQL |
| Eligibility | LiteLLM, Tool, DataAccess, Memory | Member Service | PostgreSQL, Redis |
| Benefits | LiteLLM, Policy, FunctionCalling, Knowledge | Policy, Benefits Config, Network, Formulary | PostgreSQL, Redis |
| Clinical | LiteLLM, RAG, VectorDB, Knowledge, Memory, Guardrail | VectorSearch, HybridSearch, GraphRAG, RRF | Milvus, ES, Neo4j |
| Policy | LiteLLM, Policy, Compliance, Prompt, Evaluation | Policy Service, State Mandate | PostgreSQL |
| Fraud | LiteLLM, GPU, Knowledge, RiskMgmt, DataGovernance | Claims Service | Neo4j, PostgreSQL |
| Decision | LiteLLM, HITL, Approval, Agent Governance, Memory | HITL Routing, Quality Measure | PostgreSQL, Redis |
| Notification | LiteLLM, SaaS Connector, Data, UsageAnalytics | Comm Preference, DLP | Kafka, Blob |
| Audit | LiteLLM, Audit, Compliance, DataGovernance, Observability | — | PostgreSQL, Elasticsearch |
| Appeals | All original + HITL, Grievance Track | — | PostgreSQL, Blob |
| COM | LiteLLM, A2A, Workflow, Context | Provider Service | PostgreSQL, Kafka |

### Security Chain (Every Request)

```
Kong Hub → SecurityGateway (OAuth2/JWT)
    → TokenMgmtGateway (100 req/min quota)
    → AIFirewallGateway (Lakera prompt injection)
    → GuardrailGateway (hallucination/content filter)
    → ComplianceGateway (HIPAA enforcement)
    → AuditGateway (immutable log)
    → WorkflowEngine
```

### Observability Chain (Dashed/Async)

```
Kong Hub → ObservabilityGateway → MonitoringGateway → CostMgmtGateway → TokenMgmtGateway
Workflow Engine → Kafka → Prometheus → Grafana
All agents → Jaeger (distributed traces)
```

---

## 17. State Machine & Conditional Routing

### Workflow States

| State | Description | Next States |
|-------|-------------|-------------|
| DRAFT | PA created, not submitted | SUBMITTED |
| SUBMITTED | Received by workflow engine | VALIDATING |
| VALIDATING | Intake Agent processing | IN_REVIEW, PENDED |
| IN_REVIEW | Clinical/Policy/Fraud evaluating | APPROVED, DENIED, PENDED, HITL_REVIEW |
| PENDING_INFO | Awaiting provider documents | IN_REVIEW (on resubmit) |
| HITL_REVIEW | Human review queue | APPROVED, DENIED |
| APPROVED | Auto or human approved | NOTIFIED |
| DENIED | Auto or human denied | NOTIFIED, APPEALED |
| PENDED | Missing information | IN_REVIEW |
| NOTIFIED | Decision communicated | CLOSED (after 30 days) |
| APPEALED | Appeal initiated | IN_REVIEW (re-evaluate) |

### 8 Conditional Routing Points

1. Intake confidence <0.85 → HITL document review
2. Eligibility inactive → auto-deny (END)
3. Benefits: no PA required → auto-approve (skip clinical)
4. Clinical confidence <0.60 → auto-deny with explanation
5. Policy violation → auto-deny (compliance)
6. Fraud risk >60 → HITL mandatory
7. Decision confidence <0.85 → HITL review queue
8. Is appeal → re-run Clinical + Policy with new evidence

---

## 18. Fallback, Security & Resilience Patterns

### Platform-Wide Resilience

| Pattern | Implementation | Business Why |
|---------|----------------|--------------|
| Multi-region active-active | US East + US West, RTO 5min, RPO 1min | Avoid downtime during regional outages |
| Circuit breaker | 5 consecutive failures → OPEN (60s cooldown) | Prevent cascade failures to external APIs |
| Graceful degradation | Cached data if DB unavailable | PA continues with slightly stale data vs complete failure |
| Chaos engineering | Monthly Litmus drills | Validate fallback paths work before real incidents |

### Per-Agent Fallback Summary

| Agent | Tier 1 Fallback | Tier 2 Fallback | Tier 3 / Emergency |
|-------|-----------------|-----------------|---------------------|
| Intake | Document chunking (>128K tokens) | OCR preprocessing (3 attempts) | Claude Vision → GPT-4 Turbo → HITL |
| Eligibility | Redis cache (85% hit) | PostgreSQL replica failover | HITL manual lookup |
| Benefits | OPA rule engine (deterministic) | Cached plan config | HITL |
| Clinical | Context pruning (overflow) | Partial RAG (vector only) | Model cascade GPT-4o→Claude→Med-PaLM |
| Policy | OPA/Drools (deterministic) | Cached policy version | HITL |
| Fraud | Rule-based scoring | Cached graph patterns | HITL mandatory |
| Decision | Rule-based matrix | HITL (default for low confidence) | — |

### Security Controls (All Agents)

- **Authentication:** OAuth2 JWT (1-hour expiry), mTLS via Istio
- **Authorization:** RBAC + ABAC via OPA
- **Encryption:** TLS 1.3 in transit, AES-256 at rest
- **PHI protection:** Presidio redaction in logs, DLP on outputs
- **Input validation:** File type whitelist, 50MB max, ClamAV malware scan
- **Audit:** 100% PHI access logged, 7-year retention

---

## 19. Platform Metrics Summary

### Production KPIs

| Metric | Value |
|--------|-------|
| Daily PA capacity | 50,000 |
| Average turnaround | 15 minutes |
| SLA compliance (30-min) | 99.2% |
| Auto-approval rate | 72% |
| Human review rate | 28% (14,000/day) |
| Decision accuracy | 96% |
| Clinical overturn rate | 4% |
| System uptime | 99.95% |
| ePA integration | 60% volume (30K/day) |
| FHIR CDS PA avoidance | 60% (100K alerts/day) |
| Duplicate detection | 12% (6,000/day saved) |
| Pend rate | 25% |
| Appeal overturn | 40% |
| Annual ROI | $667M |

### Cost Structure

| Category | Daily Cost |
|----------|------------|
| LLM inference (all agents) | $58,000 |
| Intake Agent alone | $14,250 |
| Gateway overhead | <$50ms (negligible $) |
| Memory storage | ~$167/day |
| MCP tool compute | ~$1,000/day |
| **Per PA request** | **~$1.16** |
| **Manual equivalent** | **~$15.00** |

### Agent Performance Summary

| Agent | Latency | Daily Volume | Success Rate |
|-------|---------|--------------|--------------|
| Intake | 2 min | 50,000 | 98.5% |
| Eligibility | 15 sec | 50,000 | 99.8% |
| Benefits | 20 sec | 50,000 | 99.2% |
| Clinical | 8 min | 50,000 | 96.2% |
| Policy | 2.5 min | 35,000 | 98.1% |
| Fraud | 45 sec | 50,000 | 99.5% |
| Decision | 30 sec | 50,000 | 99.9% |
| Notification | 1 min | 50,000 | 99.9% |
| Audit | async | 50,000 | 100% |
| Appeals | 10 min | 1,000 | 94.5% |
| COM | async | 5,000 | 97.8% |
| Expedited | 1.5 hr | 7,500 | 98% |
| Step Therapy | 30 sec | 20,000 | 96% |
| Med Director | 2 days | 1,400 | 95% |
| Retrospective | 5 days | 2,500 | 94% |
| Registry | <1 sec | 50,000 | 99.9% |
| Doc Request | 2 min | 12,500 | 97% |

---

## Document Metadata

| Field | Value |
|-------|-------|
| **Generated from** | plantuml/13-microservice-workflow-architecture.puml (5,637 lines) |
| **Companion docs** | MASTER_ARCHITECTURE_REFERENCE.md, doc/06-Complete-Microservice-Architecture.md |
| **Component count documented** | 70+ services, 60 gateways, 17 agents, 8 databases |
| **Version** | 3.0 Enhanced Edition |

---

*This document captures every component, flow, use case, technology choice, and business purpose defined in the v3.0 microservice workflow architecture diagram.*
