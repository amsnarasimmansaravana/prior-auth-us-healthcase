# Healthcare Prior Authorization Platform - Master Architecture Reference (v3.0)

This document provides the definitive technical specification for the Healthcare Prior Authorization (PA) platform, synthesized from the 5,637-line master architectural diagram (v3.0, Release 2026-06-08).

---

## 1. GenAI Orchestration Plane (60-Gateways)
The platform utilizes a **Kong Enterprise** control plane combined with a **LiteLLM** model router to orchestrate 60 specialized gateways across 11 functional tiers.

### Hub Architecture
- **Control Plane:** Kong Enterprise 3.4 (Admin API, Dynamic Plugin Management).
- **Model Router:** LiteLLM (GPT-4o: 50%, Claude 3.5: 25%, GPT-3.5: 20%, Custom ML: 5%).
- **Performance:** Total overhead <50ms | Peak throughput: 10,000 req/sec.

### Gateway Tiers (Summary)
| Tier | Description | Count | Key Gateways |
| :--- | :--- | :--- | :--- |
| **T1: Core** | Foundation routing & AI control | 4 | API, AI, LLM, Agent |
| **T2: Comm** | Inter-agent communication mesh | 4 | MCP, A2A, Multi-Agent, Mesh |
| **T3: Context** | RAG, Memory, & State management | 5 | RAG, Knowledge, Context, Memory, Vector |
| **T4: Tools** | Tool dispatch & ERP/SaaS integration | 4 | Tool, Function Call, Enterprise, SaaS |
| **T5: Inference** | GPU acceleration & Model registry | 5 | Model, Inference, GPU, Serving, Registry |
| **T6: Security** | Zero Trust, Firewalls, & Guardrails | 8 | Guardrails AI, AI Firewall, Compliance, Risk |
| **T7: Workflow** | Temporal/LangGraph orchestration | 5 | Workflow, Orchestration, HITL, Approval |
| **T8: Ops** | Observability, Cost, & Token mgmt | 5 | Observability, Monitoring, Cost Mgmt |
| **T9: Data** | Data fabric & Document processing | 5 | Data Access, Governance, Document (OCR) |
| **T10: Platform** | Agent lifecycle & Marketplace | 8 | Agent Registry, Discovery, Trust, Identity |
| **T11: Advanced** | Simulation, Eval, & Autonomous ops | 7 | Prompt, Eval, Simulation, Digital Worker |

---

## 2. Agent Fabric (17 Specialists)
The system employs 17 specialized AI agents, categorized into **Core Agents** (11) and **PA-Specific Agents** (6).

### 2.1. Core Agents (Intake to Decision)
- **Intake Agent (GPT-4o Vision):** 2 min latency | 97% extraction accuracy | 40% chunking fallback.
- **Eligibility Agent (GPT-3.5):** 15 sec latency | 85% cache hit rate | member/plan validation.
- **Benefits Agent (OPA + GPT-4o):** 20 sec latency | 50+ OPA rules | cost sharing calculation.
- **Clinical Agent (GPT-4o + RAG):** 8 min latency (**Bottleneck**) | Hybrid RAG (Vector, Keyword, Graph).
- **Policy Agent (Claude 3.5 Sonnet):** 2.5 min latency | 100K+ policy docs | state mandate compliance.
- **Fraud Agent (Custom GNN):** 45 sec latency | PRECISION: 94% | Neo4j graph analysis.
- **Decision Agent (GPT-4o):** 30 sec latency | 72% auto-approval rate | Weighted ensemble logic.
- **Notification Agent (GPT-3.5):** 1 min latency | Multi-channel (Email, SMS, Portal).
- **Audit Agent (GPT-4o):** Async | 100% PHI access coverage | HIPAA immutable logs.

### 2.2. New PA-Specific Agents (v3.0)
- **Expedited Agent:** prioritized path for urgent cases | 2-hour target latency (regulatory).
- **Step Therapy Agent:** Validates drug trials (NCPDP SCRIPT standards) | 40% of drug PAs.
- **Medical Director Agent:** Automates peer-to-peer scheduling | 15 min/call prep time savings.
- **Retrospective Agent:** Post-service necessity validation | ER/Urgent care specialized.
- **Registry Agent:** 12% duplicate detection | Automatic chronic case renewals.
- **Doc Request Agent:** Pend management | 25% case pend rate | Auto-generated clinical questions.

---

## 3. High-Fidelity Infrastructure & Data
### 3.1. Polyglot Persistence (8 Systems)
- **PostgreSQL 15 (6 TB):** Primary ACID store | 5M members | 150M claims | 10K trans/sec.
- **Redis 7.0 (26 GB):** 3-shard cluster | 500M ops/day | 85% hit rate | 6-hour TTL.
- **Milvus 2.3 (1.2 TB):** 10M embeddings | HNSW index | 45ms P95 latency.
- **Neo4j 5.x (200 GB):** 500K nodes | 2M relationships | Graph neural network fraud detection.
- **Elasticsearch 8 (400 GB):** BM25 + Vector hybrid search | 85ms P95 latency.
- **Azure Blob (10 TB):** PDF/DICOM/TIFF storage | 150K ops/day.
- **MongoDB 7 (500 GB):** Multi-tenant configuration store | 5 Payer profiles.
- **HashiCorp Vault (50 GB):** Secrets management | Zero-trust PKI.

### 3.2. Healthcare Interoperability Gateways
- **HL7 FHIR R4:** 100K calls/day | OAuth2 + SMART on FHIR.
- **X12 278 EDI:** 30K transactions/day | AS2/SFTP transport.
- **NCPDP SCRIPT:** 20K pharmacy PAs/day | XML messaging.
- **Direct Protocol:** 5K messages/day | S/MIME encryption (Fax replacement).

---

## 4. Resilience & Security Patterns
### 4.1. 4-Tier Fallback Strategy (Clinical Agent Example)
1. **Tier 1 (Context Overflow):** Intelligent pruning (summarization) → 98% recovery.
2. **Tier 2 (RAG Failure):** Partial source fallback (Vector → Keyword) → 92% accuracy.
3. **Tier 3 (LLM Failure):** Model Cascade (GPT-4o → Claude 3.5 → Med-PaLM 2).
4. **Tier 4 (Hallucination):** Guardrails AI detection + constrained re-generation.

### 4.2. Security Layers
- **Zero Trust:** mTLS via Istio | OPA for fine-grained RBAC/ABAC.
- **DLP:** Real-time PHI scanning via Microsoft Purview.
- **Safety:** Lakera AI (Firewall) + Guardrails AI (Hallucination detection).
- **Compliance:** 50-state mandate engine (500+ rules) | 72-hour breach notification mandate.

---

## 5. Platform Economics & ROI
- **Efficiency:** 15 min avg processing vs. 45 min manual.
- **Automation:** 72% auto-approval rate (member/provider satisfaction).
- **Cost Reduction:** $1.16/request AI cost vs. $15.00 manual labor.
- **Annual Savings:** **$667M/year** projection (v3.0 efficiency).
- **Clinical Bottleneck:** Clinical Review (8 min, 53% time) is the primary target for Q2 2026 optimization.

---
> **Artifact Status:** Definitive v3.0 Specification (Sync with `13-microservice-workflow-architecture.puml`)
