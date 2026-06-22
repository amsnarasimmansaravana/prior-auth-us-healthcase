# Healthcare PA Platform — Deep Component & Connection Reference (v3.2)

> **Source of truth:** `plantuml/13-microservice-workflow-architecture.puml` (5,637 lines)
> **Scope:** Every tier, gateway, agent, service, and database with **architecture patterns**, **technology stacks**, **business use cases**, **metrics**, and **explicit connections**.

| Metric | Value |
|--------|-------|
| Explicit connections (visible) | 275 |
| Hidden layout connections | 10 |
| Unique components in connection graph | 138 |
| Daily PA volume | 50,000 |
| Avg turnaround | ~15 min (ClinicalAgent bottleneck: 8 min / 53%) |
| Auto-approve / HITL split | 72% / 28% |

---

## Table of Contents

1. [Master Connection Index (All Arrows)](#1-master-connection-index-all-arrows)
2. [Critical Path Trace (Steps ①–⑩)](#2-critical-path-trace-steps-)
3. [Security Chain Connection Trace](#3-security-chain-connection-trace)
4. [Clinical Agent → RAG Sub-Pipeline](#4-clinical-agent--rag-sub-pipeline)
5. [HITL Branch Connection Map](#5-hitl-branch-connection-map)
6. [Integration Gateway Side Paths](#6-integration-gateway-side-paths)
7. [v3.0 New Agent Side Paths](#7-v30-new-agent-side-paths)
8. [Database Write Map](#8-database-write-map)
9. [Per-Component Deep Profiles + Connections](#9-per-component-deep-profiles--connections)
10. [Embedded Orchestration Specifications](#10-embedded-orchestration-specifications)
11. [Embedded Agent Specifications (All 17)](#11-embedded-agent-specifications-all-17)
12. [Embedded RAG / Data / Gateway Notes](#12-embedded-rag--data--gateway-notes)
13. [Load Performance Metrics & Detailed Report](#13-load-performance-metrics--detailed-report)
14. [OPA Decision Optimization](#14-opa-decision-optimization)
15. [Ollama GPU Tuning](#15-ollama-gpu-tuning)
16. [Kong Worker Tuning](#16-kong-worker-tuning)

---

## 1. Master Connection Index (All Arrows)

Complete **275 visible connections** from diagram 13. Each row documents:

- **Flow type** — Sync (blocking), Async (fire-and-forget), or Async non-blocking (observability)
- **Protocol** — wire protocol or integration style
- **Payload / data** — what crosses the arrow
- **Business purpose** — why this connection exists in the PA workflow
- **Failure behavior** — retry, fallback, or escalation on error

Connections are grouped by architectural flow category, then numbered globally.

### A. Presentation → Ingress

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 7 | `WebPortal` → `KongHub` | ① WebSocket (100K users) | Sync | HTTPS / WebSocket | PA submit request (JSON/FHIR Bundle), OAuth2 Bearer JWT, member_id, provider_npi, CPT/ICD-10, attached PDF base64 or blob URI | Primary member/provider web ingress (step ①); 100K concurrent users submit and track PA status in real time | 401 if JWT invalid; 429 if rate limited at KongHub; client retries with backoff |
| 8 | `MobileApp` → `KongHub` | Mobile App (50K DAU) | Sync | HTTPS REST + push token registration | Mobile-optimized PA payload, device push token, offline-sync draft_id if reconnecting | 50K DAU mobile channel; camera-captured documents and push notification registration | Offline queue stores draft locally; sync-on-connect replays to KongHub |
| 9 | `ProviderPortal` → `KongHub` | Provider Portal (SSO) | Sync | HTTPS + SSO SAML/OIDC | Provider SSO session, bulk CSV PA batch or single PA form, NPI-authenticated requests | Provider admin dashboard ingress with SSO+2FA; bulk upload for high-volume practices | SSO redirect on session expiry; partial batch failures return per-row error report |
| 10 | `EDIGateway` → `KongHub` | EDI X12 (10K/day) | Async | HTTPS + X12 278 EDI | Raw ASC X12N 005010X217 278 transaction set, clearinghouse envelope, TA1 correlation ID | Legacy B2B EDI prior auth (10K/day); hospital EMR batch submissions | TA1 reject ACK on parse failure; dead-letter queue for malformed X12 |
| 11 | `FaxOCR` → `KongHub` | OCR Docs (98.5%) | Async | HTTPS + Kafka trigger | OCR-extracted text + original fax TIFF/PDF blob URI + confidence scores per field | Legacy fax channel (8% volume); Azure Form Recognizer output forwarded for IntakeAgent | OCR confidence <0.70 routes to HITL document review queue without workflow start |
| 12 | `VoiceIVR` → `KongHub` | IVR (24/7) | Sync | HTTPS (Twilio webhook) | IVR intent (status_check/submit_urgent), member_id, DOB verification, DTMF digits | 24/7 phone channel for PA status and urgent keyword detection | Transfer to live agent on 3 failed auth attempts |
| 205 | `WebPortal` → `FHIRGateway` | FHIR API | Sync | FHIR R4 HTTPS + SMART on FHIR | FHIR Bundle (Patient, ServiceRequest), OAuth2 SMART scopes, CDS Hooks context | Direct FHIR API path for web portal CDS Hooks and CRD/DTR prior auth checks | OperationOutcome error returned; fallback to REST via KongHub |
| 206 | `ProviderPortal` → `X12Gateway` | X12 278 | Sync | Healthcare standard API (FHIR/X12/NCPDP/Direct) | Request/response between `ProviderPortal` and `X12Gateway` | Standards-based healthcare interoperability ingress bypassing generic REST | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 207 | `EDIGateway` → `X12Gateway` | EDI Feed | Sync | Internal X12 pipe (post-Mirth parse) | Pre-parsed X12 278 segments from clearinghouse before KongHub canonical transform | EDI channel internal route — EDIGateway forwards raw 278 to X12Gateway for ASC X12N validation | TA1 reject on segment validation failure; never reaches WorkflowEngine |
| 208 | `MobileApp` → `FHIRGateway` | Mobile API | Sync | Healthcare standard API (FHIR/X12/NCPDP/Direct) | Request/response between `MobileApp` and `FHIRGateway` | Standards-based healthcare interoperability ingress bypassing generic REST | Standard 3-retry exponential backoff; circuit breaker on sustained failure |

### B. Healthcare Integration

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 209 | `FHIRGateway` → `FHIRCDSService` | CDS Hooks | Sync | REST/gRPC microservice API | Request/response between `FHIRGateway` and `FHIRCDSService` | Compliance, analytics, or specialty data service integration: CDS Hooks | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 210 | `X12Gateway` → `ePAService` | ePA Process | Sync | REST/gRPC microservice API | Request/response between `X12Gateway` and `ePAService` | Compliance, analytics, or specialty data service integration: ePA Process | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 211 | `NCPDPGateway` → `ePAService` | Pharmacy PA | Sync | REST/gRPC microservice API | Request/response between `NCPDPGateway` and `ePAService` | Compliance, analytics, or specialty data service integration: Pharmacy PA | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 212 | `DirectGateway` → `AttachmentService` | Secure Docs | Sync | REST/gRPC microservice API | Request/response between `DirectGateway` and `AttachmentService` | Compliance, analytics, or specialty data service integration: Secure Docs | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 213 | `FHIRGateway` → `WorkflowEngine` | Trigger PA | Sync | gRPC trigger_pa_from_fhir | FHIR Bundle: Patient, Condition, MedicationRequest/ServiceRequest, Practitioner, Coverage | Standards-based PA trigger from EHR CDS Hooks / CRD/DTR | OperationOutcome FHIR error returned to EHR; no workflow started |
| 214 | `X12Gateway` → `WorkflowEngine` | Trigger PA | Sync | gRPC trigger_pa_from_x12 | Canonical PA model transformed from X12 278 by ePAService | EDI prior auth workflow trigger (30K/day) | X12 278 reject response generated; EDI logged in PostgreSQL |
| 250 | `PayerExchangeService` → `FHIRGateway` | FHIR Export | Sync | REST/gRPC microservice API | Request/response between `PayerExchangeService` and `FHIRGateway` | Compliance, analytics, or specialty data service integration: FHIR Export | Standard 3-retry exponential backoff; circuit breaker on sustained failure |

### C. Gateway Control Plane & Mesh

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 1 | `KongHub` → `LiteLLMRouter` | Model Requests\n$52K/day | Sync | Kong Enterprise upstream → LiteLLM proxy | All LLM inference requests from agents; model hint, prompt, max_tokens; $52K/day aggregate | Central model traffic routing — 50% GPT-4o, 25% Claude 3.5, 20% GPT-3.5, 5% custom ML | 3-tier model fallback; circuit breaker per model provider |
| 2 | `KongHub` → `CoreGWs` | Core Routing | Sync | Kong logical tier routing | Authenticated request routed to Tier 1 Core Gateways group (APIGateway, AIGateway, LLMGateway, AgentGateway) | KongHub distributes traffic to Tier 1 foundation gateways — API, AI, LLM, and Agent dispatch | Kong upstream health-check failover; 503 if all Tier 1 instances down |
| 3 | `KongHub` → `AgentCommGWs` | Agent Mesh | Sync | Kong logical tier routing | Agent-bound requests routed to Tier 2 Agent Communication group (MCP, A2A, MultiAgent, AgentMesh) | Route inter-agent communication traffic to Tier 2 agent mesh gateways | Failover to AgentMeshGateway replica set |
| 4 | `KongHub` → `KnowledgeGWs` | RAG Control | Sync | Kong logical tier routing | RAG/knowledge requests to Tier 3 group (RAGGateway, KnowledgeGateway, ContextGateway, MemoryGateway, VectorDBGateway) | Central RAG control plane ingress — all clinical retrieval routes through Knowledge tier | RAG degradation path if KnowledgeGWs unavailable; ClinicalAgent uses cached guidelines |
| 5 | `LiteLLMRouter` → `ModelGWs` | Model Selection | Sync | LiteLLM → model tier routing | Model inference request with model_hint, token budget, agent_id for cost attribution | Route to Tier 5 Model & Inference gateways (ModelGateway, InferenceGateway, GPUGateway, etc.) | 3-tier model fallback chain; CostMgmtGateway logs failed routing attempts |
| 6 | `LiteLLMRouter` → `InferenceGateway` | Inference | Sync | LiteLLM async/stream API | Batch or streaming inference job: prompt, model_id, max_tokens, stream=true\|false | Dispatch LLM inference to GPU-backed inference gateway (12ms routing overhead) | Queue to RabbitMQ async batch queue on GPU saturation |
| 13 | `KongHub` → `APIGateway` | API Routing | Sync | Kong HTTP/2 routing | REST/gRPC API requests with path-based routing headers, tenant_id, correlation_id | Route non-LLM API calls to backend microservices and GenAI gateway tier | 503 if upstream unavailable; Kong health-check failover to replica |
| 14 | `KongHub` → `SecurityGateway` | OAuth2/JWT Auth | Sync | Internal gRPC + JWT | Authorization header, client_id, scopes, token expiry, request correlation trace_id | Mandatory auth gate before any PA processing; enforces OAuth2/JWT validation (step ② prerequisite) | HTTP 403 + AuditGateway log; request never reaches WorkflowEngine |
| 15 | `KongHub` → `TokenMgmtGateway` | Rate Limit | Sync | Internal HTTP | client_id, tenant_id, current token bucket counter, requested operation cost units | Rate limit enforcement 100 req/min per client; prevents LLM cost runaway ($52K/day budget) | HTTP 429 Too Many Requests; TokenMgmtGateway increments Redis rate state |
| 16 | `APIGateway` → `AIGateway` | GenAI Requests | Sync | Kong upstream HTTP/2 | REST API request classified as GenAI; forwarded with X-Route-Tier: ai header | Tier 1 API Gateway routes GenAI-classified requests to AI Gateway controller (8ms) | Fallback route to LiteLLMRouter direct if AIGateway unhealthy |
| 17 | `AIGateway` → `LiteLLMRouter` | Model Select | Sync | LiteLLM proxy HTTPS | GenAI request from AIGateway: prompt chain, session_id, model preference, temperature | Second path to LiteLLMRouter from AI Gateway (GenAI controller) — model selection for orchestrated prompt chains | Duplicate path redundant with KongHub→LiteLLMRouter; either path can serve request |
| 18 | `LiteLLMRouter` → `LLMGateway` | Routing Logic | Sync | LiteLLM internal routing | Model routing decision: selected_model, fallback_chain[], token_budget | LLM Gateway applies 3-tier fallback strategy and cost optimization rules (10ms) | Automatic downgrade GPT-4o → Claude 3.5 → GPT-3.5 on primary failure |
| 19 | `LLMGateway` → `AgentGateway` | Agent Dispatch | Sync | Kong upstream to agent tier | Model-ready prompt dispatched to agent supervisor with agent_id hint | Route post-model-selection traffic to Multi-Agent Hub for agent dispatch (12ms) | AgentGateway circuit breaker; queue depth alert if agents saturated |
| 20 | `AgentGateway` → `MultiAgentGateway` | Supervisor | Sync | Supervisor pattern API | Supervisor coordination command: workflow_id, active_agent, next_agent_hint | LangGraph supervisor pattern — centralized multi-agent coordination (15ms) | Fallback to sequential agent dispatch without parallel optimization |
| 21 | `AgentGateway` → `MCPGateway` | Context Protocol | Sync | Model Context Protocol | MCP context share request: tools[], resources[], agent_session_id | Enable agent tool discovery and cross-agent context propagation (8ms) | Agents operate without MCP tools; reduced automation capability logged |
| 22 | `AgentGateway` → `A2AGateway` | Agent-to-Agent | Sync | gRPC bidirectional streaming | Inter-agent message: {from_agent, to_agent, message_type, payload} | Agent-to-agent direct messaging for COM and Appeals coordination (5ms) | Message queued in Kafka agent-mesh topic for async delivery |
| 23 | `AgentGateway` → `AgentMeshGateway` | Load Balance | Sync | Envoy service mesh | Load-balanced agent invocation with health-checked endpoint selection | Distribute agent workload across replicas; auto-scaling during peak (3ms) | Unhealthy agent pods removed from pool; auto-failover to standby replicas |
| 24 | `SecurityGateway` → `AIFirewallGateway` | Prompt Check | Sync | Internal security pipeline API | Sanitized user prompt text, request metadata, provider free-text fields, trace_id | First AI security gate — scan for prompt injection and jailbreak before any LLM call (Lakera Guard) | Threat detected → block request, HTTP 403, AuditGateway incident log; no LLM invocation |
| 25 | `AIFirewallGateway` → `GuardrailGateway` | Safety | Sync | Internal security pipeline API | Lakera-passed prompt, threat_score=0, scan_id, original request context | Second gate — content safety and toxicity filter before HIPAA compliance check | Unsafe content blocked; returns structured rejection to channel |
| 26 | `GuardrailGateway` → `ComplianceGateway` | HIPAA | Sync | Internal security pipeline API | Safety-filtered content, PII detection flags, content classification tags | Third gate — enforce HIPAA PHI handling rules and data residency policies | PHI policy violation blocks request; compliance incident recorded |
| 27 | `ComplianceGateway` → `AuditGateway` | Logging | Sync | Append-only audit API | Audit event: {request_id, user_id, action, timestamp, pass/fail, compliance_tags, ip_address} | Fourth gate — immutable audit log for every request (pass or fail) for 7-year retention | Audit write failure is critical alert; request may proceed but alert fires (never skip audit) |
| 28 | `AgentGateway` → `ToolGateway` | Tool Registry | Sync | MCP tool dispatch API | Tool invocation: {tool_name, parameters, sandbox_id, timeout_sec=30} | Route agent tool calls to sandboxed Tool Gateway (50+ tools, 5ms) | Tool timeout at 30s; agent receives tool_error and may escalate to HITL |
| 29 | `ToolGateway` → `FunctionCallingGateway` | Exec Functions | Sync | OpenAI function calling bridge | LLM-extracted function call: {function_name, arguments JSON, call_id} | Bind LLM function calling output to validated backend execution (8ms) | JSON schema validation failure returns error to agent for re-prompt |
| 30 | `FunctionCallingGateway` → `EnterpriseIntGateway` | SAP/Oracle | Sync | SAP RFC / Oracle REST / Salesforce API | Enterprise function call: ERP module, BAPI name, or SOQL query parameters | Execute enterprise ERP/CRM integrations from agent tool calls (25ms) | ERP timeout 30s; circuit breaker stops calling failing ERP for 60s |
| 31 | `KongHub` → `ObservabilityGateway` | Traces | Async (non-blocking) | OpenTelemetry trace export | Trace spans: trace_id, span_id, parent_span, kong.route, latency_ms | Non-blocking distributed trace propagation from central ingress (dashed line in diagram) | Non-blocking; trace loss does not affect PA processing |
| 32 | `ObservabilityGateway` → `MonitoringGateway` | Metrics | Async (non-blocking) | Prometheus metrics push | Aggregated metrics: request_count, latency_histogram, error_rate by route | Feed real-time Prometheus metrics for Grafana dashboards | Non-blocking; metrics buffer locally until Prometheus available |
| 33 | `MonitoringGateway` → `CostMgmtGateway` | $$Track | Sync | Internal metrics API | Token usage metrics: {agent_id, model, input_tokens, output_tokens, cost_usd} | Track $52K/day LLM spend with per-agent cost attribution | Cost data queued; reconciled when CostMgmtGateway recovers |
| 34 | `CostMgmtGateway` → `TokenMgmtGateway` | Tokens | Sync | Internal quota API | Token budget update: client_id, tokens_consumed, remaining_budget, alert_threshold | Close the loop — cost tracking feeds back into rate limiting and quota enforcement | Rate limiting continues with last-known budget; alert on stale data >5min |
| 35 | `SecurityGateway` → `WorkflowEngine` | ② Token Valid (OAuth2) | Sync | gRPC start_workflow | Validated JWT claims, tenant config ref, canonical PA request ID, trace_id, security_passed=true | Step ② — authorized PA workflow start; creates LangGraph DAG execution with workflow_id | Workflow not started; error returned to channel with auth error code |
| 36 | `TokenMgmtGateway` → `WorkflowEngine` | Quota OK (100/min) | Sync | gRPC quota_check | quota_ok=true, remaining_tokens, rate_limit_window_reset_at | Confirms client within quota before WorkflowEngine accepts DAG execution | WorkflowEngine rejects start if quota_ok=false (429 to client) |
| 37 | `AIGateway` → `LiteLLMRouter` | AI Request | Sync | LiteLLM proxy HTTPS | GenAI request from AIGateway: prompt chain, session_id, model preference, temperature | Second path to LiteLLMRouter from AI Gateway (GenAI controller) — model selection for orchestrated prompt chains | Duplicate path redundant with KongHub→LiteLLMRouter; either path can serve request |
| 38 | `LiteLLMRouter` → `WorkflowEngine` | Model Response | Sync | Internal completion callback | Model routing metadata, selected_model, token_count, cost_usd, routing_latency_ms | Report model selection outcome to workflow for cost tracking and audit trail | Non-blocking; workflow continues if callback fails; CostMgmtGateway reconciles async |
| 39 | `AIFirewallGateway` → `WorkflowEngine` | Security OK (Lakera) | Sync | Internal signal | security_ok=true, lakera_scan_id, threat_score=0, sanitized_prompt_hash | Confirms Lakera prompt injection scan passed before AI agents execute | security_ok=false blocks workflow; incident logged to AuditGateway |
| 40 | `WorkflowGateway` → `WorkflowEngine` | DAG Control | Sync | LangGraph API (gRPC) | DAG command: start\|pause\|resume\|cancel; workflow_id; interrupt_before node list | External DAG control API for sub-workflows (COM, Appeals) and admin operations | Invalid state transition rejected; workflow remains in current checkpoint |
| 41 | `OrchestrationGateway` → `Temporal` | Durable Exec | Sync | Temporal gRPC | SignalWorkflowExecution or StartWorkflowExecution with task_queue=pa-processing-queue | Gateway facade for durable Temporal workflow operations from external systems | Temporal unavailable → workflow queued in Kafka for delayed retry |
| 42 | `StateManagementGateway` → `StateManager` | Snapshots | Sync | State snapshot API | Checkpoint trigger: workflow_id, checkpoint_name, full_state JSON snapshot | Gateway-initiated state snapshot (every 30s) for failure recovery — dual path with WorkflowEngine→StateManager | Snapshot failure logged; WorkflowEngine direct checkpoint path remains active |
| 43 | `DataAccessGateway` → `Redis` | Token Cache | Sync | Redis GET/SET | Cache key: member_id+service_date or token cache key; cached Member/Policy JSON blob | Row-level secured cached data access — 75% cache hit rate saves MemberService round-trips | Cache miss falls through to PostgreSQL via DataAccessGateway (higher latency) |
| 44 | `TokenMgmtGateway` → `Redis` | Rate State | Sync | Redis INCR + EXPIRE | Rate limit counter key: client_id:window; incremented on each request | Token bucket rate state persistence — 100 req/min enforcement across Kong cluster | Redis down → in-memory local counter (per-node, less accurate); alert fired |
| 45 | `ContextGateway` → `Redis` | Session Context | Sync | Redis Hash HSET/HGET | Session context stack: workflow_id → {channel, tenant, user_id, context_frames[]} | Session-scoped context isolation for multi-step agent pipeline (6-hour TTL) | Context lost on Redis failure; agents re-fetch from PostgreSQL checkpoint |
| 46 | `MemoryGateway` → `Redis` | Working Memory | Sync | Redis Hash (working memory tier) | Working memory key: workflow_id → agent_outputs partial state, 5-min hot TTL | Hot working memory tier before Episodic (PostgreSQL) and Semantic (Milvus) backends | Fallback to WorkingMemory service direct PostgreSQL read |
| 49 | `StateManagementGateway` → `StateManager` | Snapshot Mgmt | Sync | State snapshot API | Checkpoint trigger: workflow_id, checkpoint_name, full_state JSON snapshot | Gateway-initiated state snapshot (every 30s) for failure recovery — dual path with WorkflowEngine→StateManager | Snapshot failure logged; WorkflowEngine direct checkpoint path remains active |
| 51 | `DataGateway` → `Kafka` | Data Events | Async | Kafka producer (Avro schema) | Event: Data Events; topic keyed by workflow_id | Async event publish from `DataGateway` — decouples downstream consumers | Producer acks=all; retry until ack; dead-letter topic on persistent failure |
| 79 | `NotificationAgent` → `LiteLLMGW` | GPT-3.5 | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-3.5 | `NotificationAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 81 | `AuditAgent` → `LiteLLMGW` | GPT-4o Log | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Log | `AuditAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 84 | `COMAgent` → `LiteLLMRouter` | GPT-4o COB | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o COB | `COMAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 124 | `NotificationAgent` → `LiteLLMRouter` | GPT-3.5 | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-3.5 | `NotificationAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 125 | `NotificationAgent` → `SaaSConnectorGateway` | Slack/Teams | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `NotificationAgent` invokes gateway `SaaSConnectorGateway` capability: Slack/Teams | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 126 | `NotificationAgent` → `DataGateway` | Event Pub | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `NotificationAgent` invokes gateway `DataGateway` capability: Event Pub | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 127 | `NotificationAgent` → `UsageAnalyticsGateway` | Behavior Track | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `NotificationAgent` invokes gateway `UsageAnalyticsGateway` capability: Behavior Track | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 128 | `AuditAgent` → `LiteLLMRouter` | GPT-4o Logging | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Logging | `AuditAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 129 | `AuditAgent` → `AuditGateway` | Immutable Log | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `AuditAgent` invokes gateway `AuditGateway` capability: Immutable Log | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 130 | `AuditAgent` → `ComplianceGateway` | HIPAA/SOC2 | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `AuditAgent` invokes gateway `ComplianceGateway` capability: HIPAA/SOC2 | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 131 | `AuditAgent` → `DataGovernanceGateway` | Lineage Track | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `AuditAgent` invokes gateway `DataGovernanceGateway` capability: Lineage Track | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 132 | `AuditAgent` → `ObservabilityGateway` | Audit Metrics | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `AuditAgent` invokes gateway `ObservabilityGateway` capability: Audit Metrics | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 133 | `COMAgent` → `LiteLLMRouter` | GPT-4o COB | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o COB | `COMAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 134 | `COMAgent` → `A2AGateway` | Agent-to-Agent | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `COMAgent` invokes gateway `A2AGateway` capability: Agent-to-Agent | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 135 | `COMAgent` → `WorkflowGateway` | Sub-workflow | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `COMAgent` invokes gateway `WorkflowGateway` capability: Sub-workflow | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 136 | `COMAgent` → `ContextGateway` | Multi-Context | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `COMAgent` invokes gateway `ContextGateway` capability: Multi-Context | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 200 | `Keycloak` → `AuthGW` | Auth Config | Sync | Internal platform API | Auth Config | Platform connection `Keycloak` → `AuthGW`: Auth Config | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 216 | `ExpeditedAgent` → `LiteLLMRouter` | GPT-4o Priority | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Priority | `ExpeditedAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 219 | `StepTherapyAgent` → `LiteLLMRouter` | GPT-4o | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o | `StepTherapyAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 223 | `MedDirectorAgent` → `LiteLLMRouter` | GPT-4o Summary | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Summary | `MedDirectorAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 226 | `RetrospectiveAgent` → `LiteLLMRouter` | GPT-4o + RAG | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o + RAG | `RetrospectiveAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 229 | `RegistryAgent` → `LiteLLMRouter` | GPT-3.5 | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-3.5 | `RegistryAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 233 | `DocRequestAgent` → `LiteLLMRouter` | GPT-4o Gen | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Gen | `DocRequestAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |

### D. Agents ↔ Gateways & Models

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 55 | `WorkflowEngine` → `IntakeAgent` | ③ Intake | Sync | LangGraph node invoke | Raw PA request, workflow_id, tenant_id, channel_source, document URIs, prior agent_outputs={} | Step ③ — first agent in DAG; OCR, classify, extract structured fields (2 min avg) | 3 retries with exponential backoff; then HITL document review escalation |
| 62 | `IntakeAgent` → `LiteLLMGW` | GPT-4o Vision | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Vision | `IntakeAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 63 | `IntakeAgent` → `BlobStorage` | Store PDF | Sync | Database native protocol | Store PDF — direct persistence or query from `IntakeAgent` | Binary document blob upload (PDF/DICOM/TIFF) | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 64 | `IntakeAgent` → `PostgreSQL` | Metadata | Sync | Database native protocol | Metadata — direct persistence or query from `IntakeAgent` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 65 | `EligibilityAgent` → `LiteLLMGW` | GPT-3.5 | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-3.5 | `EligibilityAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 66 | `EligibilityAgent` → `MemberService` | Member Lookup | Sync | gRPC GetMember + ValidateEligibility | member_id, service_date ISO8601; returns Member proto with plans[], status, effective_date | Authoritative member eligibility lookup (2M queries/day across platform) | Circuit breaker after 5 failures; HITL manual lookup fallback |
| 67 | `EligibilityAgent` → `CacheGW` | Cache Hit | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `EligibilityAgent` invokes gateway `CacheGW` capability: Cache Hit | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 68 | `BenefitsAgent` → `LiteLLMGW` | GPT-4o | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o | `BenefitsAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 69 | `BenefitsAgent` → `PolicyService` | Policy Lookup | Sync | gRPC primary (REST fallback) | Domain query/command from `BenefitsAgent`: Policy Lookup; OAuth2 service token | Agent enriches decision with authoritative data from `PolicyService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 70 | `BenefitsAgent` → `BenefitsConfigService` | Tier Matching | Sync | gRPC primary (REST fallback) | Domain query/command from `BenefitsAgent`: Tier Matching; OAuth2 service token | Agent enriches decision with authoritative data from `BenefitsConfigService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 71 | `BenefitsAgent` → `NetworkService` | Network Check | Sync | gRPC primary (REST fallback) | Domain query/command from `BenefitsAgent`: Network Check; OAuth2 service token | Agent enriches decision with authoritative data from `NetworkService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 72 | `PolicyAgent` → `LiteLLMGW` | Claude 3.5 | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: Claude 3.5 | `PolicyAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 73 | `PolicyAgent` → `PolicyService` | Rule Lookup | Sync | gRPC + REST /v1/policies/evaluate | policy_id, evaluation input {age, diagnosis, cpt, state}, OPA Rego context | Fetch and evaluate policy rules from authoritative PolicyService (100K+ documents) | 24-hour cached policy fallback; HITL if cache stale >24h |
| 74 | `FraudAgent` → `LiteLLMGW` | ML Scoring | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: ML Scoring | `FraudAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 75 | `FraudAgent` → `Neo4j` | Graph Patterns | Sync | Bolt Cypher queries | Graph pattern queries: provider-patient-procedure relationships, community detection, centrality | Detect billing fraud patterns via 500K-node knowledge graph | Skip graph analysis; ML score only (logged warning); lower fraud recall |
| 76 | `FraudAgent` → `ClaimsService` | Claim History | Sync | gRPC primary (REST fallback) | Domain query/command from `FraudAgent`: Claim History; OAuth2 service token | Agent enriches decision with authoritative data from `ClaimsService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 77 | `DecisionAgent` → `LiteLLMGW` | GPT-4o | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o | `DecisionAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 78 | `DecisionAgent` → `WorkingMemory` | Final Decision | Sync | Redis HSET via MemoryGateway | final_decision: {decision, auth_number, reasoning, confidence, effective_dates, denial_code} | Persist final decision for NotificationAgent and portal status display | Retry 3x; decision still held in WorkflowEngine state until Redis confirms |
| 87 | `IntakeAgent` → `LiteLLMRouter` | GPT-4o Vision (47K tokens) | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Vision (47K tokens) | `IntakeAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 88 | `IntakeAgent` → `DocumentGateway` | OCR Extract | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `IntakeAgent` invokes gateway `DocumentGateway` capability: OCR Extract | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 89 | `IntakeAgent` → `AgentRegistryGateway` | Agent Config | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `IntakeAgent` invokes gateway `AgentRegistryGateway` capability: Agent Config | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 90 | `IntakeAgent` → `ContextGateway` | Init Context | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `IntakeAgent` invokes gateway `ContextGateway` capability: Init Context | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 91 | `IntakeAgent` → `ObservabilityGateway` | Trace Start | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `IntakeAgent` invokes gateway `ObservabilityGateway` capability: Trace Start | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 92 | `EligibilityAgent` → `LiteLLMRouter` | GPT-3.5 Turbo | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-3.5 Turbo | `EligibilityAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 93 | `EligibilityAgent` → `ToolGateway` | Member Lookup Tool | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `EligibilityAgent` invokes gateway `ToolGateway` capability: Member Lookup Tool | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 94 | `EligibilityAgent` → `DataAccessGateway` | Member DB (Cache Hit) | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `EligibilityAgent` invokes gateway `DataAccessGateway` capability: Member DB (Cache Hit) | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 95 | `EligibilityAgent` → `MemoryGateway` | Episode Recall | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `EligibilityAgent` invokes gateway `MemoryGateway` capability: Episode Recall | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 96 | `EligibilityAgent` → `TokenMgmtGateway` | Token Count | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `EligibilityAgent` invokes gateway `TokenMgmtGateway` capability: Token Count | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 97 | `BenefitsAgent` → `LiteLLMRouter` | GPT-4o | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o | `BenefitsAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 98 | `BenefitsAgent` → `PolicyGateway` | Rule Evaluation | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `BenefitsAgent` invokes gateway `PolicyGateway` capability: Rule Evaluation | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 99 | `BenefitsAgent` → `FunctionCallingGateway` | Tier Calc | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `BenefitsAgent` invokes gateway `FunctionCallingGateway` capability: Tier Calc | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 100 | `BenefitsAgent` → `KnowledgeGateway` | Plan Ontology | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `BenefitsAgent` invokes gateway `KnowledgeGateway` capability: Plan Ontology | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 101 | `BenefitsAgent` → `CostMgmtGateway` | $$ Track | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `BenefitsAgent` invokes gateway `CostMgmtGateway` capability: $$ Track | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 102 | `ClinicalAgent` → `LiteLLMRouter` | GPT-4o + RAG (8 min) | Sync | LiteLLM chat/completions API | GPT-4o prompt: system + 20K token RAG context + chain-of-thought template; max_tokens=8000 | Core medical necessity LLM inference — 98.4% of ClinicalAgent 8-min latency (472 sec) | 3-tier model fallback GPT-4o → Claude 3.5 → retry shorter context |
| 103 | `ClinicalAgent` → `RAGGateway` | Hybrid Retrieval (45ms) | Sync | Internal RAG orchestration API | 20 retrieval queries: {diagnosis, procedure, clinical_question, query_type: vector\|keyword\|graph} | Hybrid clinical guideline retrieval (45ms); feeds GPT-4o context window | RAG failure degrades to LLM-only (lower accuracy); logged as graceful degradation |
| 104 | `ClinicalAgent` → `VectorDBGateway` | Milvus Search | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `ClinicalAgent` invokes gateway `VectorDBGateway` capability: Milvus Search | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 105 | `ClinicalAgent` → `KnowledgeGateway` | Neo4j Cypher | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `ClinicalAgent` invokes gateway `KnowledgeGateway` capability: Neo4j Cypher | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 106 | `ClinicalAgent` → `MemoryGateway` | Semantic Memory | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `ClinicalAgent` invokes gateway `MemoryGateway` capability: Semantic Memory | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 107 | `ClinicalAgent` → `GuardrailGateway` | Hallucination Check | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `ClinicalAgent` invokes gateway `GuardrailGateway` capability: Hallucination Check | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 108 | `ClinicalAgent` → `ObservabilityGateway` | RAG Spans | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `ClinicalAgent` invokes gateway `ObservabilityGateway` capability: RAG Spans | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 109 | `PolicyAgent` → `LiteLLMRouter` | Claude 3.5 Sonnet | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: Claude 3.5 Sonnet | `PolicyAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 110 | `PolicyAgent` → `PolicyGateway` | OPA/Drools | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `PolicyAgent` invokes gateway `PolicyGateway` capability: OPA/Drools | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 111 | `PolicyAgent` → `ComplianceGateway` | HIPAA Check | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `PolicyAgent` invokes gateway `ComplianceGateway` capability: HIPAA Check | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 112 | `PolicyAgent` → `PromptGateway` | LangSmith A/B | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `PolicyAgent` invokes gateway `PromptGateway` capability: LangSmith A/B | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 113 | `PolicyAgent` → `EvaluationGateway` | Quality Metrics | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `PolicyAgent` invokes gateway `EvaluationGateway` capability: Quality Metrics | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 114 | `FraudAgent` → `LiteLLMRouter` | Custom ML Model | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: Custom ML Model | `FraudAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 115 | `FraudAgent` → `GPUGateway` | GPU Acceleration | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `FraudAgent` invokes gateway `GPUGateway` capability: GPU Acceleration | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 116 | `FraudAgent` → `KnowledgeGateway` | Fraud Patterns | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `FraudAgent` invokes gateway `KnowledgeGateway` capability: Fraud Patterns | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 117 | `FraudAgent` → `RiskMgmtGateway` | Anomaly Detection | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `FraudAgent` invokes gateway `RiskMgmtGateway` capability: Anomaly Detection | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 118 | `FraudAgent` → `DataGovernanceGateway` | PII Mask | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `FraudAgent` invokes gateway `DataGovernanceGateway` capability: PII Mask | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 119 | `DecisionAgent` → `LiteLLMRouter` | GPT-4o Decision | Sync | LiteLLM chat/completions (HTTPS) | LLM prompt with agent context, tool results, and structured output schema; label: GPT-4o Decision | `DecisionAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing | 3-tier model fallback; token limit truncation retry; CostMgmtGateway tracks spend |
| 120 | `DecisionAgent` → `HITLGateway` | Route (28% Human) | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `DecisionAgent` invokes gateway `HITLGateway` capability: Route (28% Human) | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 121 | `DecisionAgent` → `ApprovalGateway` | Workflow Trigger | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `DecisionAgent` invokes gateway `ApprovalGateway` capability: Workflow Trigger | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 122 | `DecisionAgent` → `AgentGovernanceGateway` | Permission Check | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `DecisionAgent` invokes gateway `AgentGovernanceGateway` capability: Permission Check | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 123 | `DecisionAgent` → `MemoryGateway` | Store Decision | Sync | Gateway mesh internal API (gRPC/HTTP) | Agent `DecisionAgent` invokes gateway `MemoryGateway` capability: Store Decision | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction | Gateway circuit breaker opens after 5 failures; agent may degrade gracefully |
| 137 | `ClinicalAgent` → `VectorSearch` | Semantic Search | Sync | RAG pipeline internal | Retrieval pipeline data: Semantic Search | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 138 | `ClinicalAgent` → `HybridSearch` | Keyword Search | Sync | RAG pipeline internal | Retrieval pipeline data: Keyword Search | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 139 | `ClinicalAgent` → `GraphRAG` | Relationship Query | Sync | RAG pipeline internal | Retrieval pipeline data: Relationship Query | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 149 | `PolicyAgent` → `PolicyService` | — | Sync | gRPC + REST /v1/policies/evaluate | policy_id, evaluation input {age, diagnosis, cpt, state}, OPA Rego context | Fetch and evaluate policy rules from authoritative PolicyService (100K+ documents) | 24-hour cached policy fallback; HITL if cache stale >24h |
| 150 | `FraudAgent` → `Neo4j` | — | Sync | Bolt Cypher queries | Graph pattern queries: provider-patient-procedure relationships, community detection, centrality | Detect billing fraud patterns via 500K-node knowledge graph | Skip graph analysis; ML score only (logged warning); lower fraud recall |
| 151 | `DecisionAgent` → `HITLRouting` | ⑩ Risk Assessment | Sync | LangGraph conditional edge | decision_draft: {recommendation, weighted_confidence, fraud_risk, cost_estimate, hitl_required, denial_reason} | Step ⑩ — route 72% auto-approve vs 28% human review (14K/day) | Low confidence always routes HITL; denials always get human review |
| 169 | `AgentRegistry` → `IntakeAgent` | Agent Config | Sync | Internal platform API | Config/tool/memory operation: Agent Config | Governance, MCP tool, or tiered memory integration for agent context and safety | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 171 | `PromptMgmt` → `PolicyAgent` | Prompt | Sync | Internal platform API | Config/tool/memory operation: Prompt | Governance, MCP tool, or tiered memory integration for agent context and safety | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 173 | `SafetyEval` → `ClinicalAgent` | Validate | Sync | RAG pipeline internal | Retrieval pipeline data: Validate | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 175 | `MCPRegistry` → `IntakeAgent` | Tools | Sync | Internal platform API | Config/tool/memory operation: Tools | Governance, MCP tool, or tiered memory integration for agent context and safety | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 177 | `ToolExecutor` → `EligibilityAgent` | Execute | Sync | Internal platform API | Config/tool/memory operation: Execute | Governance, MCP tool, or tiered memory integration for agent context and safety | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 179 | `WorkingMemory` → `IntakeAgent` | Context | Sync | Internal platform API | Config/tool/memory operation: Context | Governance, MCP tool, or tiered memory integration for agent context and safety | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 181 | `EpisodicMemory` → `FraudAgent` | History | Sync | Internal platform API | Config/tool/memory operation: History | Governance, MCP tool, or tiered memory integration for agent context and safety | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 183 | `SemanticMemory` → `ClinicalAgent` | Knowledge | Sync | RAG pipeline internal | Retrieval pipeline data: Knowledge | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 184 | `DecisionAgent` → `HITLRouting` | ⑩ Risk Assessment | Sync | LangGraph conditional edge | decision_draft: {recommendation, weighted_confidence, fraud_risk, cost_estimate, hitl_required, denial_reason} | Step ⑩ — route 72% auto-approve vs 28% human review (14K/day) | Low confidence always routes HITL; denials always get human review |
| 197 | `Jaeger` → `IntakeAgent` | Agent Spans | Async (non-blocking) | OpenTelemetry / Prometheus scrape | Metrics span or trace: Agent Spans | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting | Non-blocking; observability loss does not affect PA processing |
| 198 | `Jaeger` → `ClinicalAgent` | RAG Spans | Sync | RAG pipeline internal | Retrieval pipeline data: RAG Spans | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 218 | `BenefitsAgent` → `StepTherapyAgent` | Drug PA | Sync | LangGraph conditional branch | drug_pa_context: {ndc, formulary_tier, member_id, step_therapy_rules} | Route pharmacy PAs to step therapy validation (20K drug PAs/day, 40% of volume) | StepTherapy failure → pend for manual pharmacy review |
| 222 | `DecisionAgent` → `MedDirectorAgent` | P2P Request | Async | LangGraph conditional branch | denial_context: {denial_reason, clinical_summary, provider_p2p_requested=true} | Trigger peer-to-peer review scheduling on provider denial appeal (1,400/day) | P2P scheduling failure → manual coordinator assignment |
| 228 | `IntakeAgent` → `RegistryAgent` | De-dup Check | Sync | LangGraph parallel branch invoke | member_id, procedure_cpt, service_date — de-duplication check request | Prevent duplicate PA submissions; return existing auth if active PA found (12% renewals) | Registry unavailable → skip dedup with warning log; proceed to Eligibility |
| 232 | `ClinicalAgent` → `DocRequestAgent` | Pend Trigger | Async | LangGraph conditional branch + Kafka | pend_context: {missing_docs[], clinical_confidence, provider_npi, pend_reason} | Trigger clinical documentation request when evidence insufficient (25% pend rate) | Workflow enters PENDED state; resumes on AttachmentService upload event |
| 236 | `ePAService` → `IntakeAgent` | Transform PA | Sync | REST/gRPC microservice API | Request/response between `ePAService` and `IntakeAgent` | Compliance, analytics, or specialty data service integration: Transform PA | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 244 | `CodeValidationService` → `IntakeAgent` | ICD/CPT Check | Sync | REST/gRPC microservice API | Request/response between `CodeValidationService` and `IntakeAgent` | Compliance, analytics, or specialty data service integration: ICD/CPT Check | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 248 | `QualityMeasureService` → `DecisionAgent` | HEDIS Track | Sync | REST/gRPC microservice API | Request/response between `QualityMeasureService` and `DecisionAgent` | Compliance, analytics, or specialty data service integration: HEDIS Track | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 263 | `StateMandateService` → `PolicyAgent` | State Rules | Sync | REST/gRPC microservice API | Request/response between `StateMandateService` and `PolicyAgent` | Compliance, analytics, or specialty data service integration: State Rules | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 267 | `RootCauseService` → `DecisionAgent` | Denial Pattern | Sync | REST/gRPC microservice API | Request/response between `RootCauseService` and `DecisionAgent` | Compliance, analytics, or specialty data service integration: Denial Pattern | Standard 3-retry exponential backoff; circuit breaker on sustained failure |

### E. Agent Pipeline (Critical Path)

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 56 | `IntakeAgent` → `EligibilityAgent` | ④ Eligibility | Sync | LangGraph edge + shared state | Structured intake JSON: patient, provider, diagnosis ICD-10[], procedure CPT, confidence_scores, document_type | Step ④ handoff — member/plan verification after successful field extraction | If intake confidence <0.85, conditional edge routes to HITL instead of Eligibility |
| 57 | `EligibilityAgent` → `BenefitsAgent` | ⑤ Benefits | Sync | LangGraph edge | eligibility_result: {is_eligible, plan_id, tier, effective_date, network_hint, member_id} | Step ⑤ — tier/network/PA-required determination after member verified active | is_eligible=false triggers auto-deny END node (workflow terminates) |
| 58 | `BenefitsAgent` → `ClinicalAgent` | ⑥ Clinical | Sync | LangGraph edge | benefits_context: {pa_required, tier, network_status, cost_share, formulary_tier, step_therapy_flag} | Step ⑥ — medical necessity evaluation (pipeline bottleneck: 8 min, 53% of total time) | pa_required=false skips Clinical via conditional edge to auto-approve path |
| 59 | `ClinicalAgent` → `PolicyAgent` | ⑦ Policy | Sync | LangGraph edge | clinical_result: {medical_necessity, confidence, guideline_citations[], reasoning, pend_flag} | Step ⑦ — regulatory/policy compliance check after clinical necessity determined | confidence <0.60 triggers auto-deny; pend_flag triggers DocRequestAgent branch |
| 60 | `PolicyAgent` → `FraudAgent` | ⑧ Fraud Check | Sync | LangGraph edge | policy_result: {compliant, rules_evaluated[], violations[], state_mandate_applied} | Step ⑧ — fraud risk scoring after policy clearance | Policy violation triggers auto-deny END (skips Fraud) |
| 61 | `FraudAgent` → `DecisionAgent` | ⑨ Decision | Sync | LangGraph edge | fraud_result: {risk_score 0-100, patterns_detected[], graph_anomalies[], shap_explanation} | Step ⑨ — aggregate all agent outputs into final approve/deny/HITL decision | risk_score >60 sets hitl_mandatory=true in shared state |

### F. RAG Retrieval Pipeline

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 140 | `VectorSearch` → `RRF` | Vector Scores | Sync | In-process Python | ranked_list: [{doc_id, vector_score, rank}] for 8 vector queries | Feed semantic similarity scores into Reciprocal Rank Fusion merger | Empty result set contributes zero scores; other retrieval paths compensate |
| 141 | `HybridSearch` → `RRF` | BM25 Scores | Sync | In-process Python | ranked_list: [{doc_id, bm25_score, rank}] for 6 keyword queries | Feed ICD/CPT exact-match BM25 scores into RRF fusion | Same as VectorSearch — partial fusion still produces results |
| 142 | `GraphRAG` → `RRF` | Relevance | Sync | In-process Python | ranked_list: [{doc_id, graph_relevance, cypher_path}] for 4 graph queries | Feed diagnosis→procedure→guideline graph traversal scores into RRF | Neo4j timeout returns empty; RRF proceeds with vector+BM25 only |
| 143 | `RRF` → `ClinicalContentService` | Top 10 Ranked Results | Sync | REST GET /content/batch | top_10_doc_ids from RRF fusion (k=60); request full text chunks for LLM context | Hydrate ranked document IDs into full guideline text for ClinicalAgent prompt | Missing doc falls back to metadata-only snippet from PostgreSQL |
| 144 | `VectorSearch` → `Milvus` | Vector Lookup | Sync | Database native protocol | Vector Lookup — direct persistence or query from `VectorSearch` | Vector embedding upsert/search index | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 145 | `HybridSearch` → `Elasticsearch` | Index Scan | Sync | Database native protocol | Index Scan — direct persistence or query from `HybridSearch` | Full-text index write or BM25 search | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 146 | `GraphRAG` → `Neo4j` | Graph Traverse | Sync | Database native protocol | Graph Traverse — direct persistence or query from `GraphRAG` | Graph node/relationship read or pattern query | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 165 | `VectorSearch` → `Milvus` | — | Sync | Database native protocol |  — direct persistence or query from `VectorSearch` | Vector embedding upsert/search index | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 166 | `HybridSearch` → `Elasticsearch` | — | Sync | Database native protocol |  — direct persistence or query from `HybridSearch` | Full-text index write or BM25 search | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 167 | `GraphRAG` → `Neo4j` | — | Sync | Database native protocol |  — direct persistence or query from `GraphRAG` | Graph node/relationship read or pattern query | Retry with backoff; critical writes queued to Kafka for eventual consistency |

### G. Data Services Layer

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 85 | `COMAgent` → `ProviderService` | Network Lookup | Sync | gRPC primary (REST fallback) | Domain query/command from `COMAgent`: Network Lookup; OAuth2 service token | Agent enriches decision with authoritative data from `ProviderService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 147 | `ClinicalContentService` → `Elasticsearch` | Content | Sync | SQL / Redis protocol / Bolt / ES API | Content — domain entity read/write from `ClinicalContentService` | Full-text index write or BM25 search | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 148 | `ClinicalContentService` → `PostgreSQL` | Metadata | Sync | SQL / Redis protocol / Bolt / ES API | Metadata — domain entity read/write from `ClinicalContentService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 152 | `MemberService` → `PostgreSQL` | Member DB | Sync | SQL / Redis protocol / Bolt / ES API | Member DB — domain entity read/write from `MemberService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 153 | `MemberService` → `Redis` | Cache | Sync | SQL / Redis protocol / Bolt / ES API | Cache — domain entity read/write from `MemberService` | Cache/session write — TTL-managed hot data | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 154 | `ProviderService` → `PostgreSQL` | Provider DB | Sync | SQL / Redis protocol / Bolt / ES API | Provider DB — domain entity read/write from `ProviderService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 155 | `ProviderService` → `Redis` | Cache | Sync | SQL / Redis protocol / Bolt / ES API | Cache — domain entity read/write from `ProviderService` | Cache/session write — TTL-managed hot data | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 156 | `PolicyService` → `PostgreSQL` | Policy DB | Sync | SQL / Redis protocol / Bolt / ES API | Policy DB — domain entity read/write from `PolicyService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 157 | `PolicyService` → `Redis` | Cache | Sync | SQL / Redis protocol / Bolt / ES API | Cache — domain entity read/write from `PolicyService` | Cache/session write — TTL-managed hot data | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 158 | `ClaimsService` → `PostgreSQL` | Claims DB | Sync | SQL / Redis protocol / Bolt / ES API | Claims DB — domain entity read/write from `ClaimsService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 159 | `ClaimsService` → `Kafka` | Events | Async | Kafka producer (Avro schema) | Event: Events; topic keyed by workflow_id | Async event publish from `ClaimsService` — decouples downstream consumers | Producer acks=all; retry until ack; dead-letter topic on persistent failure |
| 160 | `BenefitsConfigService` → `PostgreSQL` | Config DB | Sync | SQL / Redis protocol / Bolt / ES API | Config DB — domain entity read/write from `BenefitsConfigService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 161 | `NetworkService` → `PostgreSQL` | Network DB | Sync | SQL / Redis protocol / Bolt / ES API | Network DB — domain entity read/write from `NetworkService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 162 | `FormularyService` → `PostgreSQL` | Formulary DB | Sync | SQL / Redis protocol / Bolt / ES API | Formulary DB — domain entity read/write from `FormularyService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 163 | `ClinicalContentService` → `Elasticsearch` | Content Index | Sync | SQL / Redis protocol / Bolt / ES API | Content Index — domain entity read/write from `ClinicalContentService` | Full-text index write or BM25 search | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 164 | `ClinicalContentService` → `PostgreSQL` | Metadata | Sync | SQL / Redis protocol / Bolt / ES API | Metadata — domain entity read/write from `ClinicalContentService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 217 | `ExpeditedAgent` → `SLAMonitorService` | 72hr Track | Sync | gRPC primary (REST fallback) | Domain query/command from `ExpeditedAgent`: 72hr Track; OAuth2 service token | Agent enriches decision with authoritative data from `SLAMonitorService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 220 | `StepTherapyAgent` → `ClaimsService` | Prior Fills | Sync | gRPC primary (REST fallback) | Domain query/command from `StepTherapyAgent`: Prior Fills; OAuth2 service token | Agent enriches decision with authoritative data from `ClaimsService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 221 | `StepTherapyAgent` → `DrugReferenceService` | NDC Lookup | Sync | gRPC primary (REST fallback) | Domain query/command from `StepTherapyAgent`: NDC Lookup; OAuth2 service token | Agent enriches decision with authoritative data from `DrugReferenceService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 224 | `MedDirectorAgent` → `ProviderPortalService` | Schedule P2P | Sync | gRPC primary (REST fallback) | Domain query/command from `MedDirectorAgent`: Schedule P2P; OAuth2 service token | Agent enriches decision with authoritative data from `ProviderPortalService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 227 | `RetrospectiveAgent` → `ClaimsService` | UB-04/1500 | Sync | gRPC primary (REST fallback) | Domain query/command from `RetrospectiveAgent`: UB-04/1500; OAuth2 service token | Agent enriches decision with authoritative data from `ClaimsService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 234 | `DocRequestAgent` → `AttachmentService` | Doc Upload | Sync | gRPC primary (REST fallback) | Domain query/command from `DocRequestAgent`: Doc Upload; OAuth2 service token | Agent enriches decision with authoritative data from `AttachmentService` (cache-aside pattern) | Circuit breaker → Redis cache stale read → HITL manual lookup |
| 237 | `ePAService` → `PostgreSQL` | EDI Log | Sync | SQL / Redis protocol / Bolt / ES API | EDI Log — domain entity read/write from `ePAService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 238 | `FHIRCDSService` → `FormularyService` | PA Check | Sync | REST/gRPC microservice API | Request/response between `FHIRCDSService` and `FormularyService` | Compliance, analytics, or specialty data service integration: PA Check | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 239 | `FHIRCDSService` → `PolicyService` | Rules Check | Sync | REST/gRPC microservice API | Request/response between `FHIRCDSService` and `PolicyService` | Compliance, analytics, or specialty data service integration: Rules Check | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 240 | `AttachmentService` → `BlobStorage` | Store Docs | Sync | SQL / Redis protocol / Bolt / ES API | Store Docs — domain entity read/write from `AttachmentService` | Binary document blob upload (PDF/DICOM/TIFF) | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 241 | `AttachmentService` → `Elasticsearch` | Index Content | Sync | SQL / Redis protocol / Bolt / ES API | Index Content — domain entity read/write from `AttachmentService` | Full-text index write or BM25 search | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 242 | `DrugReferenceService` → `Redis` | 95% Cache | Sync | SQL / Redis protocol / Bolt / ES API | 95% Cache — domain entity read/write from `DrugReferenceService` | Cache/session write — TTL-managed hot data | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 243 | `DrugReferenceService` → `PostgreSQL` | NDC/RxNorm | Sync | SQL / Redis protocol / Bolt / ES API | NDC/RxNorm — domain entity read/write from `DrugReferenceService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 245 | `CodeValidationService` → `Redis` | Code Cache | Sync | SQL / Redis protocol / Bolt / ES API | Code Cache — domain entity read/write from `CodeValidationService` | Cache/session write — TTL-managed hot data | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 246 | `SLAMonitorService` → `WorkflowEngine` | Track SLA | Sync | REST/gRPC microservice API | Request/response between `SLAMonitorService` and `WorkflowEngine` | Compliance, analytics, or specialty data service integration: Track SLA | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 247 | `SLAMonitorService` → `PostgreSQL` | Deadline Store | Sync | SQL / Redis protocol / Bolt / ES API | Deadline Store — domain entity read/write from `SLAMonitorService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 249 | `QualityMeasureService` → `PostgreSQL` | Stars Data | Sync | SQL / Redis protocol / Bolt / ES API | Stars Data — domain entity read/write from `QualityMeasureService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 251 | `PayerExchangeService` → `PostgreSQL` | PA Transfer | Sync | SQL / Redis protocol / Bolt / ES API | PA Transfer — domain entity read/write from `PayerExchangeService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 252 | `ProviderPortalService` → `ProviderPortal` | GraphQL API | Sync | REST/gRPC microservice API | Request/response between `ProviderPortalService` and `ProviderPortal` | Compliance, analytics, or specialty data service integration: GraphQL API | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 253 | `ProviderPortalService` → `PostgreSQL` | PA Status | Sync | SQL / Redis protocol / Bolt / ES API | PA Status — domain entity read/write from `ProviderPortalService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 254 | `GrievanceTrackService` → `AppealsAgent` | Appeal Track | Sync | REST/gRPC microservice API | Request/response between `GrievanceTrackService` and `AppealsAgent` | Compliance, analytics, or specialty data service integration: Appeal Track | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 255 | `GrievanceTrackService` → `PostgreSQL` | Timeline Store | Sync | SQL / Redis protocol / Bolt / ES API | Timeline Store — domain entity read/write from `GrievanceTrackService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 256 | `DLPService` → `NotificationAgent` | PHI Scan | Sync | REST/gRPC microservice API | Request/response between `DLPService` and `NotificationAgent` | Compliance, analytics, or specialty data service integration: PHI Scan | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 257 | `DLPService` → `AuditAgent` | Log Scan | Sync | REST/gRPC microservice API | Request/response between `DLPService` and `AuditAgent` | Compliance, analytics, or specialty data service integration: Log Scan | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 258 | `DLPService` → `PostgreSQL` | Incident Log | Sync | SQL / Redis protocol / Bolt / ES API | Incident Log — domain entity read/write from `DLPService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 259 | `ConsentMgmtService` → `PayerExchangeService` | Consent Check | Sync | REST/gRPC microservice API | Request/response between `ConsentMgmtService` and `PayerExchangeService` | Compliance, analytics, or specialty data service integration: Consent Check | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 260 | `ConsentMgmtService` → `PostgreSQL` | Consent DB | Sync | SQL / Redis protocol / Bolt / ES API | Consent DB — domain entity read/write from `ConsentMgmtService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 261 | `BreachNotifyService` → `DLPService` | Breach Detect | Sync | REST/gRPC microservice API | Request/response between `BreachNotifyService` and `DLPService` | Compliance, analytics, or specialty data service integration: Breach Detect | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 262 | `BreachNotifyService` → `PostgreSQL` | Breach Log | Sync | SQL / Redis protocol / Bolt / ES API | Breach Log — domain entity read/write from `BreachNotifyService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 264 | `StateMandateService` → `PostgreSQL` | 50-State DB | Sync | SQL / Redis protocol / Bolt / ES API | 50-State DB — domain entity read/write from `StateMandateService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 265 | `CapacityPlanningService` → `HITLRouting` | Staffing Plan | Sync | Internal platform API | HITL work item: Staffing Plan | Human-in-the-loop path — 28% of cases (14K/day) require clinical reviewer action | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 266 | `CapacityPlanningService` → `PostgreSQL` | Historical Data | Sync | SQL / Redis protocol / Bolt / ES API | Historical Data — domain entity read/write from `CapacityPlanningService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 268 | `RootCauseService` → `Elasticsearch` | Log Analysis | Sync | SQL / Redis protocol / Bolt / ES API | Log Analysis — domain entity read/write from `RootCauseService` | Full-text index write or BM25 search | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 269 | `ProviderAnalyticsService` → `ProviderService` | Provider Score | Sync | REST/gRPC microservice API | Request/response between `ProviderAnalyticsService` and `ProviderService` | Compliance, analytics, or specialty data service integration: Provider Score | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 270 | `ProviderAnalyticsService` → `PostgreSQL` | Analytics DB | Sync | SQL / Redis protocol / Bolt / ES API | Analytics DB — domain entity read/write from `ProviderAnalyticsService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 271 | `CommPreferenceService` → `NotificationAgent` | Channel Select | Sync | REST/gRPC microservice API | Request/response between `CommPreferenceService` and `NotificationAgent` | Compliance, analytics, or specialty data service integration: Channel Select | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 272 | `CommPreferenceService` → `Redis` | Pref Cache | Sync | SQL / Redis protocol / Bolt / ES API | Pref Cache — domain entity read/write from `CommPreferenceService` | Cache/session write — TTL-managed hot data | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 273 | `CommPreferenceService` → `PostgreSQL` | Member Prefs | Sync | SQL / Redis protocol / Bolt / ES API | Member Prefs — domain entity read/write from `CommPreferenceService` | Relational persistence — transactional ACID write | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |
| 274 | `MultiTenantService` → `WorkflowEngine` | Payer Config | Sync | REST/gRPC microservice API | Request/response between `MultiTenantService` and `WorkflowEngine` | Compliance, analytics, or specialty data service integration: Payer Config | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 275 | `MultiTenantService` → `MongoDB` | Config Store | Sync | SQL / Redis protocol / Bolt / ES API | Config Store — domain entity read/write from `MultiTenantService` | Document store write for multi-tenant config | Connection pool exhaustion → circuit breaker; read replica failover for PostgreSQL |

### H. Database & Storage

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 52 | `StateManager` → `Redis` | Hot Store (5min) | Sync | Redis HSET | Hash key=workflow_id, fields=status, current_agent, agent_outputs JSON, TTL=6h | Hot working memory for sub-5ms state reads during active PA processing | Fallback to PostgreSQL cold store; P95 latency increases to ~50ms |
| 53 | `StateManager` → `PostgreSQL` | Cold Store (90d) | Sync | SQL INSERT pa_workflow_checkpoints | checkpoint_id UUID, workflow_id, checkpoint_name, state_snapshot JSONB, created_at | Cold persistence 90-day retention for audit and failure recovery | Critical alert; workflow continues in Redis-only mode until DB restored |
| 54 | `Temporal` → `PostgreSQL` | Event History | Sync | Database native protocol | Event History — direct persistence or query from `Temporal` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 82 | `AuditAgent` → `PostgreSQL` | Compliance | Sync | SQL INSERT audit_records (WORM table) | Full agent I/O audit record: {workflow_id, agent_name, input_hash, output, timestamp, user_id} | HIPAA-compliant immutable audit storage — 6-year minimum retention | Critical PagerDuty alert; write queued to Kafka audit-backup topic |
| 83 | `AuditAgent` → `Elasticsearch` | Audit Index | Async | Elasticsearch bulk index API | Searchable audit document for RootCauseService and compliance queries | Index audit events for full-text forensic search and denial pattern analysis | Non-blocking; PostgreSQL is source of truth; ES catch-up on recovery |
| 168 | `AgentRegistry` → `PostgreSQL` | Agent Metadata | Sync | Database native protocol | Agent Metadata — direct persistence or query from `AgentRegistry` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 170 | `PromptMgmt` → `PostgreSQL` | Prompt Versions | Sync | Database native protocol | Prompt Versions — direct persistence or query from `PromptMgmt` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 172 | `SafetyEval` → `Redis` | Cache Scores | Sync | Database native protocol | Cache Scores — direct persistence or query from `SafetyEval` | Cache/session write — TTL-managed hot data | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 174 | `MCPRegistry` → `PostgreSQL` | Tool Registry | Sync | Database native protocol | Tool Registry — direct persistence or query from `MCPRegistry` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 176 | `ToolExecutor` → `Vault` | Secrets | Sync | Database native protocol | Secrets — direct persistence or query from `ToolExecutor` | Secret read for tool credentials | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 178 | `WorkingMemory` → `Redis` | Cache | Sync | Database native protocol | Cache — direct persistence or query from `WorkingMemory` | Cache/session write — TTL-managed hot data | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 180 | `EpisodicMemory` → `PostgreSQL` | Storage | Sync | Database native protocol | Storage — direct persistence or query from `EpisodicMemory` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 182 | `SemanticMemory` → `Milvus` | Vectors | Sync | Database native protocol | Vectors — direct persistence or query from `SemanticMemory` | Vector embedding upsert/search index | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 187 | `ApprovalWorkflow` → `PostgreSQL` | Approval Log | Sync | Database native protocol | Approval Log — direct persistence or query from `ApprovalWorkflow` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 193 | `Prometheus` → `PostgreSQL` | Metrics | Sync | Database native protocol | Metrics — direct persistence or query from `Prometheus` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 195 | `Grafana` → `Redis` | Dashboard Cache | Sync | Database native protocol | Dashboard Cache — direct persistence or query from `Grafana` | Cache/session write — TTL-managed hot data | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 199 | `Jaeger` → `PostgreSQL` | Store | Sync | Database native protocol | Store — direct persistence or query from `Jaeger` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 201 | `Keycloak` → `PostgreSQL` | User DB | Sync | Database native protocol | User DB — direct persistence or query from `Keycloak` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 203 | `Kafka` → `PostgreSQL` | Event Log | Sync | Database native protocol | Event Log — direct persistence or query from `Kafka` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 204 | `Kafka` → `Elasticsearch` | Event Index | Sync | Database native protocol | Event Index — direct persistence or query from `Kafka` | Full-text index write or BM25 search | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 230 | `RegistryAgent` → `Redis` | Active PA Cache | Sync | Database native protocol | Active PA Cache — direct persistence or query from `RegistryAgent` | Cache/session write — TTL-managed hot data | Retry with backoff; critical writes queued to Kafka for eventual consistency |
| 231 | `RegistryAgent` → `PostgreSQL` | PA History | Sync | Database native protocol | PA History — direct persistence or query from `RegistryAgent` | Relational persistence — transactional ACID write | Retry with backoff; critical writes queued to Kafka for eventual consistency |

### I. HITL Human Review

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 185 | `HITLRouting` → `ReviewQueue` | 28% Human (14K/day) | Sync | Queue enqueue API | review_item: {workflow_id, priority_score, specialty, fraud_flag, sla_deadline, clinical_summary} | Queue 28% cases for human clinical reviewer (<4hr SLA) | Queue full triggers CapacityPlanningService alert + priority overflow routing |
| 186 | `ReviewQueue` → `ApprovalWorkflow` | — | Sync | Temporal human task + PostgreSQL queue | Reviewer assignment: {reviewer_id, decision pending, clinical_summary, sla_deadline, workflow_id} | Assign queued HITL case to human reviewer for approve/deny decision (<4hr SLA) | SLA breach escalates priority; CapacityPlanningService alerts staffing |
| 188 | `ApprovalWorkflow` → `Kafka` | Event Stream | Async | Kafka producer (Avro schema) | Event: Event Stream; topic keyed by workflow_id | Async event publish from `ApprovalWorkflow` — decouples downstream consumers | Producer acks=all; retry until ack; dead-letter topic on persistent failure |
| 189 | `HITLRouting` → `NotificationAgent` | 72% Auto-Approve (36K/day) | Async | Kafka topic pa.auto_approved | auto_decision: {workflow_id, decision=approved, auth_number, effective_dates, member_letter_text} | Fire-and-forget notification for 72% auto-approved cases (36K/day) | Kafka retry 3x; dead-letter triggers manual notification job |
| 190 | `ApprovalWorkflow` → `AuditAgent` | Log | Async | Kafka pa.hitl.decided | Human decision: {reviewer_id, decision, reasoning, timestamp, override_ai=true} | Log human reviewer decision for compliance; 100% HITL decisions audited | Kafka retry; synchronous PostgreSQL audit as backup path |

### J. Infrastructure & Observability

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 50 | `WorkflowEngine` → `Kafka` | Event Stream | Async | Kafka producer (Avro schema) | Event: Event Stream; topic keyed by workflow_id | Async event publish from `WorkflowEngine` — decouples downstream consumers | Producer acks=all; retry until ack; dead-letter topic on persistent failure |
| 80 | `NotificationAgent` → `Kafka` | Events | Async | Kafka producer pa.notification.sent | notification_event: {workflow_id, channel, recipient, template_id, delivery_status} | Publish notification delivery events for audit trail and downstream analytics | Producer retry 3x; notification still sent even if Kafka publish fails |
| 86 | `COMAgent` → `Kafka` | COB Events | Async | Kafka producer (Avro schema) | Event: COB Events; topic keyed by workflow_id | Async event publish from `COMAgent` — decouples downstream consumers | Producer acks=all; retry until ack; dead-letter topic on persistent failure |
| 191 | `Prometheus` → `WorkflowEngine` | Metrics | Async (non-blocking) | OpenTelemetry / Prometheus scrape | Metrics span or trace: Metrics | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting | Non-blocking; observability loss does not affect PA processing |
| 192 | `Prometheus` → `Kafka` | Metrics | Async | Kafka producer (Avro schema) | Event: Metrics; topic keyed by workflow_id | Async event publish from `Prometheus` — decouples downstream consumers | Producer acks=all; retry until ack; dead-letter topic on persistent failure |
| 194 | `Grafana` → `Prometheus` | Query | Async (non-blocking) | OpenTelemetry / Prometheus scrape | Metrics span or trace: Query | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting | Non-blocking; observability loss does not affect PA processing |
| 196 | `Jaeger` → `WorkflowEngine` | Traces | Async (non-blocking) | OpenTelemetry / Prometheus scrape | Metrics span or trace: Traces | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting | Non-blocking; observability loss does not affect PA processing |
| 202 | `Kafka` → `NotificationAgent` | Consume | Async | Kafka consumer (consumer group) | Consumed event: Consume; at-least-once delivery | `NotificationAgent` reacts to platform events asynchronously | Standard 3-retry exponential backoff; circuit breaker on sustained failure |

### K. Compliance, Analytics & Other

| # | Connection | Label | Flow | Protocol | Payload / Data | Business Purpose | On Failure |
|---|------------|-------|------|----------|----------------|------------------|------------|
| 47 | `WorkflowEngine` → `Temporal` | Persist State | Sync | Temporal gRPC StartWorkflowExecution | workflow_type=PA_Request_Workflow, task_queue=pa-processing-queue, input=PARequest, workflow_id | Durable execution — survive worker crashes during 8-min ClinicalAgent inference | Temporal retries start; existing workflow_id provides idempotency |
| 48 | `WorkflowEngine` → `StateManager` | Checkpoint | Sync | Redis SET + PostgreSQL INSERT | Full workflow state JSON snapshot: agent_outputs, progress, checkpoints[], updated_at | Checkpoint every 30s for failure recovery (RPO 1 min, RTO 5 min) | Redis failure falls back to PostgreSQL-only (slower but durable) |
| 215 | `WorkflowEngine` → `ExpeditedAgent` | Urgent Route | Sync | LangGraph priority queue branch | urgent_flag=true, keyword_matches[], expedited_sla=72hr, parallel_execution=true | CMS expedited PA fast-track for urgent/emergency cases (7,500/day, 15% volume) | SLAMonitorService alerts at 24hr mark if not complete |
| 225 | `WorkflowEngine` → `RetrospectiveAgent` | Post-Service | Sync | Internal platform API | Request/response between `WorkflowEngine` and `RetrospectiveAgent` | PA-specific agent side-path (v3.0): Post-Service — regulatory or specialty workflow branch | Standard 3-retry exponential backoff; circuit breaker on sustained failure |
| 235 | `DocRequestAgent` → `NotificationAgent` | Provider Alert | Sync | Internal platform API | Request/response between `DocRequestAgent` and `NotificationAgent` | PA-specific agent side-path (v3.0): Provider Alert — regulatory or specialty workflow branch | Standard 3-retry exponential backoff; circuit breaker on sustained failure |

### Full Index — Compact Reference

| # | Source → Target | Flow | Purpose (summary) |
|---|-----------------|------|-------------------|
| 1 | `KongHub` → `LiteLLMRouter` | Sync | Central model traffic routing — 50% GPT-4o, 25% Claude 3.5, 20% GPT-3.5, 5% custom ML |
| 2 | `KongHub` → `CoreGWs` | Sync | KongHub distributes traffic to Tier 1 foundation gateways — API, AI, LLM, and Agent dispatch |
| 3 | `KongHub` → `AgentCommGWs` | Sync | Route inter-agent communication traffic to Tier 2 agent mesh gateways |
| 4 | `KongHub` → `KnowledgeGWs` | Sync | Central RAG control plane ingress — all clinical retrieval routes through Knowledge tier |
| 5 | `LiteLLMRouter` → `ModelGWs` | Sync | Route to Tier 5 Model & Inference gateways (ModelGateway, InferenceGateway, GPUGateway, etc.) |
| 6 | `LiteLLMRouter` → `InferenceGateway` | Sync | Dispatch LLM inference to GPU-backed inference gateway (12ms routing overhead) |
| 7 | `WebPortal` → `KongHub` | Sync | Primary member/provider web ingress (step ①); 100K concurrent users submit and track PA status in real time |
| 8 | `MobileApp` → `KongHub` | Sync | 50K DAU mobile channel; camera-captured documents and push notification registration |
| 9 | `ProviderPortal` → `KongHub` | Sync | Provider admin dashboard ingress with SSO+2FA; bulk upload for high-volume practices |
| 10 | `EDIGateway` → `KongHub` | Async | Legacy B2B EDI prior auth (10K/day); hospital EMR batch submissions |
| 11 | `FaxOCR` → `KongHub` | Async | Legacy fax channel (8% volume); Azure Form Recognizer output forwarded for IntakeAgent |
| 12 | `VoiceIVR` → `KongHub` | Sync | 24/7 phone channel for PA status and urgent keyword detection |
| 13 | `KongHub` → `APIGateway` | Sync | Route non-LLM API calls to backend microservices and GenAI gateway tier |
| 14 | `KongHub` → `SecurityGateway` | Sync | Mandatory auth gate before any PA processing; enforces OAuth2/JWT validation (step ② prerequisite) |
| 15 | `KongHub` → `TokenMgmtGateway` | Sync | Rate limit enforcement 100 req/min per client; prevents LLM cost runaway ($52K/day budget) |
| 16 | `APIGateway` → `AIGateway` | Sync | Tier 1 API Gateway routes GenAI-classified requests to AI Gateway controller (8ms) |
| 17 | `AIGateway` → `LiteLLMRouter` | Sync | Second path to LiteLLMRouter from AI Gateway (GenAI controller) — model selection for orchestrated prompt chains |
| 18 | `LiteLLMRouter` → `LLMGateway` | Sync | LLM Gateway applies 3-tier fallback strategy and cost optimization rules (10ms) |
| 19 | `LLMGateway` → `AgentGateway` | Sync | Route post-model-selection traffic to Multi-Agent Hub for agent dispatch (12ms) |
| 20 | `AgentGateway` → `MultiAgentGateway` | Sync | LangGraph supervisor pattern — centralized multi-agent coordination (15ms) |
| 21 | `AgentGateway` → `MCPGateway` | Sync | Enable agent tool discovery and cross-agent context propagation (8ms) |
| 22 | `AgentGateway` → `A2AGateway` | Sync | Agent-to-agent direct messaging for COM and Appeals coordination (5ms) |
| 23 | `AgentGateway` → `AgentMeshGateway` | Sync | Distribute agent workload across replicas; auto-scaling during peak (3ms) |
| 24 | `SecurityGateway` → `AIFirewallGateway` | Sync | First AI security gate — scan for prompt injection and jailbreak before any LLM call (Lakera Guard) |
| 25 | `AIFirewallGateway` → `GuardrailGateway` | Sync | Second gate — content safety and toxicity filter before HIPAA compliance check |
| 26 | `GuardrailGateway` → `ComplianceGateway` | Sync | Third gate — enforce HIPAA PHI handling rules and data residency policies |
| 27 | `ComplianceGateway` → `AuditGateway` | Sync | Fourth gate — immutable audit log for every request (pass or fail) for 7-year retention |
| 28 | `AgentGateway` → `ToolGateway` | Sync | Route agent tool calls to sandboxed Tool Gateway (50+ tools, 5ms) |
| 29 | `ToolGateway` → `FunctionCallingGateway` | Sync | Bind LLM function calling output to validated backend execution (8ms) |
| 30 | `FunctionCallingGateway` → `EnterpriseIntGateway` | Sync | Execute enterprise ERP/CRM integrations from agent tool calls (25ms) |
| 31 | `KongHub` → `ObservabilityGateway` | Async (non-blocking) | Non-blocking distributed trace propagation from central ingress (dashed line in diagram) |
| 32 | `ObservabilityGateway` → `MonitoringGateway` | Async (non-blocking) | Feed real-time Prometheus metrics for Grafana dashboards |
| 33 | `MonitoringGateway` → `CostMgmtGateway` | Sync | Track $52K/day LLM spend with per-agent cost attribution |
| 34 | `CostMgmtGateway` → `TokenMgmtGateway` | Sync | Close the loop — cost tracking feeds back into rate limiting and quota enforcement |
| 35 | `SecurityGateway` → `WorkflowEngine` | Sync | Step ② — authorized PA workflow start; creates LangGraph DAG execution with workflow_id |
| 36 | `TokenMgmtGateway` → `WorkflowEngine` | Sync | Confirms client within quota before WorkflowEngine accepts DAG execution |
| 37 | `AIGateway` → `LiteLLMRouter` | Sync | Second path to LiteLLMRouter from AI Gateway (GenAI controller) — model selection for orchestrated prompt chains |
| 38 | `LiteLLMRouter` → `WorkflowEngine` | Sync | Report model selection outcome to workflow for cost tracking and audit trail |
| 39 | `AIFirewallGateway` → `WorkflowEngine` | Sync | Confirms Lakera prompt injection scan passed before AI agents execute |
| 40 | `WorkflowGateway` → `WorkflowEngine` | Sync | External DAG control API for sub-workflows (COM, Appeals) and admin operations |
| 41 | `OrchestrationGateway` → `Temporal` | Sync | Gateway facade for durable Temporal workflow operations from external systems |
| 42 | `StateManagementGateway` → `StateManager` | Sync | Gateway-initiated state snapshot (every 30s) for failure recovery — dual path with WorkflowEngine→StateManager |
| 43 | `DataAccessGateway` → `Redis` | Sync | Row-level secured cached data access — 75% cache hit rate saves MemberService round-trips |
| 44 | `TokenMgmtGateway` → `Redis` | Sync | Token bucket rate state persistence — 100 req/min enforcement across Kong cluster |
| 45 | `ContextGateway` → `Redis` | Sync | Session-scoped context isolation for multi-step agent pipeline (6-hour TTL) |
| 46 | `MemoryGateway` → `Redis` | Sync | Hot working memory tier before Episodic (PostgreSQL) and Semantic (Milvus) backends |
| 47 | `WorkflowEngine` → `Temporal` | Sync | Durable execution — survive worker crashes during 8-min ClinicalAgent inference |
| 48 | `WorkflowEngine` → `StateManager` | Sync | Checkpoint every 30s for failure recovery (RPO 1 min, RTO 5 min) |
| 49 | `StateManagementGateway` → `StateManager` | Sync | Gateway-initiated state snapshot (every 30s) for failure recovery — dual path with WorkflowEngine→StateManager |
| 50 | `WorkflowEngine` → `Kafka` | Async | Async event publish from `WorkflowEngine` — decouples downstream consumers |
| 51 | `DataGateway` → `Kafka` | Async | Async event publish from `DataGateway` — decouples downstream consumers |
| 52 | `StateManager` → `Redis` | Sync | Hot working memory for sub-5ms state reads during active PA processing |
| 53 | `StateManager` → `PostgreSQL` | Sync | Cold persistence 90-day retention for audit and failure recovery |
| 54 | `Temporal` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 55 | `WorkflowEngine` → `IntakeAgent` | Sync | Step ③ — first agent in DAG; OCR, classify, extract structured fields (2 min avg) |
| 56 | `IntakeAgent` → `EligibilityAgent` | Sync | Step ④ handoff — member/plan verification after successful field extraction |
| 57 | `EligibilityAgent` → `BenefitsAgent` | Sync | Step ⑤ — tier/network/PA-required determination after member verified active |
| 58 | `BenefitsAgent` → `ClinicalAgent` | Sync | Step ⑥ — medical necessity evaluation (pipeline bottleneck: 8 min, 53% of total time) |
| 59 | `ClinicalAgent` → `PolicyAgent` | Sync | Step ⑦ — regulatory/policy compliance check after clinical necessity determined |
| 60 | `PolicyAgent` → `FraudAgent` | Sync | Step ⑧ — fraud risk scoring after policy clearance |
| 61 | `FraudAgent` → `DecisionAgent` | Sync | Step ⑨ — aggregate all agent outputs into final approve/deny/HITL decision |
| 62 | `IntakeAgent` → `LiteLLMGW` | Sync | `IntakeAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 63 | `IntakeAgent` → `BlobStorage` | Sync | Binary document blob upload (PDF/DICOM/TIFF) |
| 64 | `IntakeAgent` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 65 | `EligibilityAgent` → `LiteLLMGW` | Sync | `EligibilityAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 66 | `EligibilityAgent` → `MemberService` | Sync | Authoritative member eligibility lookup (2M queries/day across platform) |
| 67 | `EligibilityAgent` → `CacheGW` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 68 | `BenefitsAgent` → `LiteLLMGW` | Sync | `BenefitsAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 69 | `BenefitsAgent` → `PolicyService` | Sync | Agent enriches decision with authoritative data from `PolicyService` (cache-aside pattern) |
| 70 | `BenefitsAgent` → `BenefitsConfigService` | Sync | Agent enriches decision with authoritative data from `BenefitsConfigService` (cache-aside pattern) |
| 71 | `BenefitsAgent` → `NetworkService` | Sync | Agent enriches decision with authoritative data from `NetworkService` (cache-aside pattern) |
| 72 | `PolicyAgent` → `LiteLLMGW` | Sync | `PolicyAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 73 | `PolicyAgent` → `PolicyService` | Sync | Fetch and evaluate policy rules from authoritative PolicyService (100K+ documents) |
| 74 | `FraudAgent` → `LiteLLMGW` | Sync | `FraudAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 75 | `FraudAgent` → `Neo4j` | Sync | Detect billing fraud patterns via 500K-node knowledge graph |
| 76 | `FraudAgent` → `ClaimsService` | Sync | Agent enriches decision with authoritative data from `ClaimsService` (cache-aside pattern) |
| 77 | `DecisionAgent` → `LiteLLMGW` | Sync | `DecisionAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 78 | `DecisionAgent` → `WorkingMemory` | Sync | Persist final decision for NotificationAgent and portal status display |
| 79 | `NotificationAgent` → `LiteLLMGW` | Sync | `NotificationAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 80 | `NotificationAgent` → `Kafka` | Async | Publish notification delivery events for audit trail and downstream analytics |
| 81 | `AuditAgent` → `LiteLLMGW` | Sync | `AuditAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 82 | `AuditAgent` → `PostgreSQL` | Sync | HIPAA-compliant immutable audit storage — 6-year minimum retention |
| 83 | `AuditAgent` → `Elasticsearch` | Async | Index audit events for full-text forensic search and denial pattern analysis |
| 84 | `COMAgent` → `LiteLLMRouter` | Sync | `COMAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 85 | `COMAgent` → `ProviderService` | Sync | Agent enriches decision with authoritative data from `ProviderService` (cache-aside pattern) |
| 86 | `COMAgent` → `Kafka` | Async | Async event publish from `COMAgent` — decouples downstream consumers |
| 87 | `IntakeAgent` → `LiteLLMRouter` | Sync | `IntakeAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 88 | `IntakeAgent` → `DocumentGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 89 | `IntakeAgent` → `AgentRegistryGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 90 | `IntakeAgent` → `ContextGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 91 | `IntakeAgent` → `ObservabilityGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 92 | `EligibilityAgent` → `LiteLLMRouter` | Sync | `EligibilityAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 93 | `EligibilityAgent` → `ToolGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 94 | `EligibilityAgent` → `DataAccessGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 95 | `EligibilityAgent` → `MemoryGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 96 | `EligibilityAgent` → `TokenMgmtGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 97 | `BenefitsAgent` → `LiteLLMRouter` | Sync | `BenefitsAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 98 | `BenefitsAgent` → `PolicyGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 99 | `BenefitsAgent` → `FunctionCallingGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 100 | `BenefitsAgent` → `KnowledgeGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 101 | `BenefitsAgent` → `CostMgmtGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 102 | `ClinicalAgent` → `LiteLLMRouter` | Sync | Core medical necessity LLM inference — 98.4% of ClinicalAgent 8-min latency (472 sec) |
| 103 | `ClinicalAgent` → `RAGGateway` | Sync | Hybrid clinical guideline retrieval (45ms); feeds GPT-4o context window |
| 104 | `ClinicalAgent` → `VectorDBGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 105 | `ClinicalAgent` → `KnowledgeGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 106 | `ClinicalAgent` → `MemoryGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 107 | `ClinicalAgent` → `GuardrailGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 108 | `ClinicalAgent` → `ObservabilityGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 109 | `PolicyAgent` → `LiteLLMRouter` | Sync | `PolicyAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 110 | `PolicyAgent` → `PolicyGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 111 | `PolicyAgent` → `ComplianceGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 112 | `PolicyAgent` → `PromptGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 113 | `PolicyAgent` → `EvaluationGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 114 | `FraudAgent` → `LiteLLMRouter` | Sync | `FraudAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 115 | `FraudAgent` → `GPUGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 116 | `FraudAgent` → `KnowledgeGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 117 | `FraudAgent` → `RiskMgmtGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 118 | `FraudAgent` → `DataGovernanceGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 119 | `DecisionAgent` → `LiteLLMRouter` | Sync | `DecisionAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 120 | `DecisionAgent` → `HITLGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 121 | `DecisionAgent` → `ApprovalGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 122 | `DecisionAgent` → `AgentGovernanceGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 123 | `DecisionAgent` → `MemoryGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 124 | `NotificationAgent` → `LiteLLMRouter` | Sync | `NotificationAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 125 | `NotificationAgent` → `SaaSConnectorGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 126 | `NotificationAgent` → `DataGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 127 | `NotificationAgent` → `UsageAnalyticsGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 128 | `AuditAgent` → `LiteLLMRouter` | Sync | `AuditAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 129 | `AuditAgent` → `AuditGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 130 | `AuditAgent` → `ComplianceGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 131 | `AuditAgent` → `DataGovernanceGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 132 | `AuditAgent` → `ObservabilityGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 133 | `COMAgent` → `LiteLLMRouter` | Sync | `COMAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 134 | `COMAgent` → `A2AGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 135 | `COMAgent` → `WorkflowGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 136 | `COMAgent` → `ContextGateway` | Sync | Agent accesses platform capability (RAG, tools, security, observability) via gateway abstraction |
| 137 | `ClinicalAgent` → `VectorSearch` | Sync | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) |
| 138 | `ClinicalAgent` → `HybridSearch` | Sync | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) |
| 139 | `ClinicalAgent` → `GraphRAG` | Sync | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) |
| 140 | `VectorSearch` → `RRF` | Sync | Feed semantic similarity scores into Reciprocal Rank Fusion merger |
| 141 | `HybridSearch` → `RRF` | Sync | Feed ICD/CPT exact-match BM25 scores into RRF fusion |
| 142 | `GraphRAG` → `RRF` | Sync | Feed diagnosis→procedure→guideline graph traversal scores into RRF |
| 143 | `RRF` → `ClinicalContentService` | Sync | Hydrate ranked document IDs into full guideline text for ClinicalAgent prompt |
| 144 | `VectorSearch` → `Milvus` | Sync | Vector embedding upsert/search index |
| 145 | `HybridSearch` → `Elasticsearch` | Sync | Full-text index write or BM25 search |
| 146 | `GraphRAG` → `Neo4j` | Sync | Graph node/relationship read or pattern query |
| 147 | `ClinicalContentService` → `Elasticsearch` | Sync | Full-text index write or BM25 search |
| 148 | `ClinicalContentService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 149 | `PolicyAgent` → `PolicyService` | Sync | Fetch and evaluate policy rules from authoritative PolicyService (100K+ documents) |
| 150 | `FraudAgent` → `Neo4j` | Sync | Detect billing fraud patterns via 500K-node knowledge graph |
| 151 | `DecisionAgent` → `HITLRouting` | Sync | Step ⑩ — route 72% auto-approve vs 28% human review (14K/day) |
| 152 | `MemberService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 153 | `MemberService` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 154 | `ProviderService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 155 | `ProviderService` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 156 | `PolicyService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 157 | `PolicyService` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 158 | `ClaimsService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 159 | `ClaimsService` → `Kafka` | Async | Async event publish from `ClaimsService` — decouples downstream consumers |
| 160 | `BenefitsConfigService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 161 | `NetworkService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 162 | `FormularyService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 163 | `ClinicalContentService` → `Elasticsearch` | Sync | Full-text index write or BM25 search |
| 164 | `ClinicalContentService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 165 | `VectorSearch` → `Milvus` | Sync | Vector embedding upsert/search index |
| 166 | `HybridSearch` → `Elasticsearch` | Sync | Full-text index write or BM25 search |
| 167 | `GraphRAG` → `Neo4j` | Sync | Graph node/relationship read or pattern query |
| 168 | `AgentRegistry` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 169 | `AgentRegistry` → `IntakeAgent` | Sync | Governance, MCP tool, or tiered memory integration for agent context and safety |
| 170 | `PromptMgmt` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 171 | `PromptMgmt` → `PolicyAgent` | Sync | Governance, MCP tool, or tiered memory integration for agent context and safety |
| 172 | `SafetyEval` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 173 | `SafetyEval` → `ClinicalAgent` | Sync | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) |
| 174 | `MCPRegistry` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 175 | `MCPRegistry` → `IntakeAgent` | Sync | Governance, MCP tool, or tiered memory integration for agent context and safety |
| 176 | `ToolExecutor` → `Vault` | Sync | Secret read for tool credentials |
| 177 | `ToolExecutor` → `EligibilityAgent` | Sync | Governance, MCP tool, or tiered memory integration for agent context and safety |
| 178 | `WorkingMemory` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 179 | `WorkingMemory` → `IntakeAgent` | Sync | Governance, MCP tool, or tiered memory integration for agent context and safety |
| 180 | `EpisodicMemory` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 181 | `EpisodicMemory` → `FraudAgent` | Sync | Governance, MCP tool, or tiered memory integration for agent context and safety |
| 182 | `SemanticMemory` → `Milvus` | Sync | Vector embedding upsert/search index |
| 183 | `SemanticMemory` → `ClinicalAgent` | Sync | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) |
| 184 | `DecisionAgent` → `HITLRouting` | Sync | Step ⑩ — route 72% auto-approve vs 28% human review (14K/day) |
| 185 | `HITLRouting` → `ReviewQueue` | Sync | Queue 28% cases for human clinical reviewer (<4hr SLA) |
| 186 | `ReviewQueue` → `ApprovalWorkflow` | Sync | Assign queued HITL case to human reviewer for approve/deny decision (<4hr SLA) |
| 187 | `ApprovalWorkflow` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 188 | `ApprovalWorkflow` → `Kafka` | Async | Async event publish from `ApprovalWorkflow` — decouples downstream consumers |
| 189 | `HITLRouting` → `NotificationAgent` | Async | Fire-and-forget notification for 72% auto-approved cases (36K/day) |
| 190 | `ApprovalWorkflow` → `AuditAgent` | Async | Log human reviewer decision for compliance; 100% HITL decisions audited |
| 191 | `Prometheus` → `WorkflowEngine` | Async (non-blocking) | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting |
| 192 | `Prometheus` → `Kafka` | Async | Async event publish from `Prometheus` — decouples downstream consumers |
| 193 | `Prometheus` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 194 | `Grafana` → `Prometheus` | Async (non-blocking) | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting |
| 195 | `Grafana` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 196 | `Jaeger` → `WorkflowEngine` | Async (non-blocking) | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting |
| 197 | `Jaeger` → `IntakeAgent` | Async (non-blocking) | Platform observability — SLO monitoring, bottleneck analysis, SLA alerting |
| 198 | `Jaeger` → `ClinicalAgent` | Sync | Clinical guideline retrieval sub-pipeline supporting ClinicalAgent medical necessity (45ms retrieval vs 472s LLM) |
| 199 | `Jaeger` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 200 | `Keycloak` → `AuthGW` | Sync | Platform connection `Keycloak` → `AuthGW`: Auth Config |
| 201 | `Keycloak` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 202 | `Kafka` → `NotificationAgent` | Async | `NotificationAgent` reacts to platform events asynchronously |
| 203 | `Kafka` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 204 | `Kafka` → `Elasticsearch` | Sync | Full-text index write or BM25 search |
| 205 | `WebPortal` → `FHIRGateway` | Sync | Direct FHIR API path for web portal CDS Hooks and CRD/DTR prior auth checks |
| 206 | `ProviderPortal` → `X12Gateway` | Sync | Standards-based healthcare interoperability ingress bypassing generic REST |
| 207 | `EDIGateway` → `X12Gateway` | Sync | EDI channel internal route — EDIGateway forwards raw 278 to X12Gateway for ASC X12N validation |
| 208 | `MobileApp` → `FHIRGateway` | Sync | Standards-based healthcare interoperability ingress bypassing generic REST |
| 209 | `FHIRGateway` → `FHIRCDSService` | Sync | Compliance, analytics, or specialty data service integration: CDS Hooks |
| 210 | `X12Gateway` → `ePAService` | Sync | Compliance, analytics, or specialty data service integration: ePA Process |
| 211 | `NCPDPGateway` → `ePAService` | Sync | Compliance, analytics, or specialty data service integration: Pharmacy PA |
| 212 | `DirectGateway` → `AttachmentService` | Sync | Compliance, analytics, or specialty data service integration: Secure Docs |
| 213 | `FHIRGateway` → `WorkflowEngine` | Sync | Standards-based PA trigger from EHR CDS Hooks / CRD/DTR |
| 214 | `X12Gateway` → `WorkflowEngine` | Sync | EDI prior auth workflow trigger (30K/day) |
| 215 | `WorkflowEngine` → `ExpeditedAgent` | Sync | CMS expedited PA fast-track for urgent/emergency cases (7,500/day, 15% volume) |
| 216 | `ExpeditedAgent` → `LiteLLMRouter` | Sync | `ExpeditedAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 217 | `ExpeditedAgent` → `SLAMonitorService` | Sync | Agent enriches decision with authoritative data from `SLAMonitorService` (cache-aside pattern) |
| 218 | `BenefitsAgent` → `StepTherapyAgent` | Sync | Route pharmacy PAs to step therapy validation (20K drug PAs/day, 40% of volume) |
| 219 | `StepTherapyAgent` → `LiteLLMRouter` | Sync | `StepTherapyAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 220 | `StepTherapyAgent` → `ClaimsService` | Sync | Agent enriches decision with authoritative data from `ClaimsService` (cache-aside pattern) |
| 221 | `StepTherapyAgent` → `DrugReferenceService` | Sync | Agent enriches decision with authoritative data from `DrugReferenceService` (cache-aside pattern) |
| 222 | `DecisionAgent` → `MedDirectorAgent` | Async | Trigger peer-to-peer review scheduling on provider denial appeal (1,400/day) |
| 223 | `MedDirectorAgent` → `LiteLLMRouter` | Sync | `MedDirectorAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 224 | `MedDirectorAgent` → `ProviderPortalService` | Sync | Agent enriches decision with authoritative data from `ProviderPortalService` (cache-aside pattern) |
| 225 | `WorkflowEngine` → `RetrospectiveAgent` | Sync | PA-specific agent side-path (v3.0): Post-Service — regulatory or specialty workflow branch |
| 226 | `RetrospectiveAgent` → `LiteLLMRouter` | Sync | `RetrospectiveAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 227 | `RetrospectiveAgent` → `ClaimsService` | Sync | Agent enriches decision with authoritative data from `ClaimsService` (cache-aside pattern) |
| 228 | `IntakeAgent` → `RegistryAgent` | Sync | Prevent duplicate PA submissions; return existing auth if active PA found (12% renewals) |
| 229 | `RegistryAgent` → `LiteLLMRouter` | Sync | `RegistryAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 230 | `RegistryAgent` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 231 | `RegistryAgent` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 232 | `ClinicalAgent` → `DocRequestAgent` | Async | Trigger clinical documentation request when evidence insufficient (25% pend rate) |
| 233 | `DocRequestAgent` → `LiteLLMRouter` | Sync | `DocRequestAgent` LLM inference call — model selected by LiteLLMRouter cost/accuracy routing |
| 234 | `DocRequestAgent` → `AttachmentService` | Sync | Agent enriches decision with authoritative data from `AttachmentService` (cache-aside pattern) |
| 235 | `DocRequestAgent` → `NotificationAgent` | Sync | PA-specific agent side-path (v3.0): Provider Alert — regulatory or specialty workflow branch |
| 236 | `ePAService` → `IntakeAgent` | Sync | Compliance, analytics, or specialty data service integration: Transform PA |
| 237 | `ePAService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 238 | `FHIRCDSService` → `FormularyService` | Sync | Compliance, analytics, or specialty data service integration: PA Check |
| 239 | `FHIRCDSService` → `PolicyService` | Sync | Compliance, analytics, or specialty data service integration: Rules Check |
| 240 | `AttachmentService` → `BlobStorage` | Sync | Binary document blob upload (PDF/DICOM/TIFF) |
| 241 | `AttachmentService` → `Elasticsearch` | Sync | Full-text index write or BM25 search |
| 242 | `DrugReferenceService` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 243 | `DrugReferenceService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 244 | `CodeValidationService` → `IntakeAgent` | Sync | Compliance, analytics, or specialty data service integration: ICD/CPT Check |
| 245 | `CodeValidationService` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 246 | `SLAMonitorService` → `WorkflowEngine` | Sync | Compliance, analytics, or specialty data service integration: Track SLA |
| 247 | `SLAMonitorService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 248 | `QualityMeasureService` → `DecisionAgent` | Sync | Compliance, analytics, or specialty data service integration: HEDIS Track |
| 249 | `QualityMeasureService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 250 | `PayerExchangeService` → `FHIRGateway` | Sync | Compliance, analytics, or specialty data service integration: FHIR Export |
| 251 | `PayerExchangeService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 252 | `ProviderPortalService` → `ProviderPortal` | Sync | Compliance, analytics, or specialty data service integration: GraphQL API |
| 253 | `ProviderPortalService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 254 | `GrievanceTrackService` → `AppealsAgent` | Sync | Compliance, analytics, or specialty data service integration: Appeal Track |
| 255 | `GrievanceTrackService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 256 | `DLPService` → `NotificationAgent` | Sync | Compliance, analytics, or specialty data service integration: PHI Scan |
| 257 | `DLPService` → `AuditAgent` | Sync | Compliance, analytics, or specialty data service integration: Log Scan |
| 258 | `DLPService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 259 | `ConsentMgmtService` → `PayerExchangeService` | Sync | Compliance, analytics, or specialty data service integration: Consent Check |
| 260 | `ConsentMgmtService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 261 | `BreachNotifyService` → `DLPService` | Sync | Compliance, analytics, or specialty data service integration: Breach Detect |
| 262 | `BreachNotifyService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 263 | `StateMandateService` → `PolicyAgent` | Sync | Compliance, analytics, or specialty data service integration: State Rules |
| 264 | `StateMandateService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 265 | `CapacityPlanningService` → `HITLRouting` | Sync | Human-in-the-loop path — 28% of cases (14K/day) require clinical reviewer action |
| 266 | `CapacityPlanningService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 267 | `RootCauseService` → `DecisionAgent` | Sync | Compliance, analytics, or specialty data service integration: Denial Pattern |
| 268 | `RootCauseService` → `Elasticsearch` | Sync | Full-text index write or BM25 search |
| 269 | `ProviderAnalyticsService` → `ProviderService` | Sync | Compliance, analytics, or specialty data service integration: Provider Score |
| 270 | `ProviderAnalyticsService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 271 | `CommPreferenceService` → `NotificationAgent` | Sync | Compliance, analytics, or specialty data service integration: Channel Select |
| 272 | `CommPreferenceService` → `Redis` | Sync | Cache/session write — TTL-managed hot data |
| 273 | `CommPreferenceService` → `PostgreSQL` | Sync | Relational persistence — transactional ACID write |
| 274 | `MultiTenantService` → `WorkflowEngine` | Sync | Compliance, analytics, or specialty data service integration: Payer Config |
| 275 | `MultiTenantService` → `MongoDB` | Sync | Document store write for multi-tenant config |

---

## 2. Critical Path Trace (Steps ①–⑩)

Sequential PA processing path with **every hop** and what crosses each connection.

| Step | From | To | Data / Control Passed |
|------|------|-----|----------------------|
| ① | WebPortal / MobileApp / ProviderPortal / EDIGateway / FaxOCR / VoiceIVR | `KongHub` | HTTPS/WebSocket/EDI; OAuth2 JWT; PA request payload (FHIR Bundle or X12 278 or PDF) |
|  | KongHub | `SecurityGateway` | JWT validation request; client_id, scopes, token expiry |
|  | KongHub | `TokenMgmtGateway` | Rate limit check; client quota state (100 req/min) |
|  | KongHub | `APIGateway` | REST/gRPC route to backend services |
|  | SecurityGateway | `AIFirewallGateway` | Sanitized prompt + metadata for Lakera injection scan |
|  | AIFirewallGateway | `GuardrailGateway` | Passed prompt → content safety filter |
|  | GuardrailGateway | `ComplianceGateway` | Filtered content → HIPAA PHI rules |
|  | ComplianceGateway | `AuditGateway` | Compliance event → immutable audit record |
| ② | SecurityGateway | `WorkflowEngine` | Token valid signal → start LangGraph DAG |
|  | TokenMgmtGateway | `WorkflowEngine` | Quota OK → allow workflow execution |
|  | AIFirewallGateway | `WorkflowEngine` | Security OK (Lakera passed) |
|  | WorkflowEngine | `Temporal` | Persist durable workflow state |
|  | WorkflowEngine | `StateManager` | Checkpoint workflow snapshot |
|  | WorkflowEngine | `Kafka` | Workflow lifecycle events |
| ③ | WorkflowEngine | `IntakeAgent` | Raw PA request → OCR/classification task |
|  | IntakeAgent | `LiteLLMRouter` | GPT-4o Vision (47K tokens); document images |
|  | IntakeAgent | `DocumentGateway` | OCR extract via Azure Form Recognizer |
|  | IntakeAgent | `BlobStorage` | Store original PDF |
|  | IntakeAgent | `PostgreSQL` | Extracted metadata (pa_documents) |
|  | IntakeAgent | `RegistryAgent` | De-dup check against active PA cache |
| ④ | IntakeAgent | `EligibilityAgent` | Structured intake JSON → member verification |
|  | EligibilityAgent | `MemberService` | Member lookup by member_id + service_date |
|  | EligibilityAgent | `ToolGateway` | member_lookup MCP tool |
| ⑤ | EligibilityAgent | `BenefitsAgent` | Eligibility result → tier/network calculation |
|  | BenefitsAgent | `PolicyService / BenefitsConfigService / NetworkService` | Plan rules, tiers, network |
|  | BenefitsAgent | `StepTherapyAgent` | Drug PA → step therapy validation (side path) |
| ⑥ | BenefitsAgent | `ClinicalAgent` | Benefits context → medical necessity evaluation |
|  | ClinicalAgent | `RAGGateway` | Hybrid retrieval (45ms); 20 queries |
|  | ClinicalAgent | `VectorSearch / HybridSearch / GraphRAG` | Parallel RAG sub-searches |
|  | RRF | `ClinicalContentService` | Top 10 ranked guideline chunks |
|  | ClinicalAgent | `LiteLLMRouter` | GPT-4o + RAG context (8 min inference) |
|  | ClinicalAgent | `DocRequestAgent` | Pend trigger if missing clinical docs |
| ⑦ | ClinicalAgent | `PolicyAgent` | Clinical necessity result → policy compliance |
|  | PolicyAgent | `PolicyGateway` | OPA/Drools 50+ rules evaluation |
|  | PolicyAgent | `StateMandateService` | 50-state mandate rules injection |
| ⑧ | PolicyAgent | `FraudAgent` | Policy-cleared case → fraud scoring |
|  | FraudAgent | `Neo4j` | Graph pattern analysis |
|  | FraudAgent | `ClaimsService` | Historical claim history |
| ⑨ | FraudAgent | `DecisionAgent` | All agent outputs → final aggregation |
|  | DecisionAgent | `WorkingMemory` | Final decision stored in session memory |
|  | DecisionAgent | `QualityMeasureService` | HEDIS/Stars measure capture |
| ⑩ | DecisionAgent | `HITLRouting` | Risk assessment → auto (72%) or human (28%) |
|  | HITLRouting | `ReviewQueue` | 28% → human review queue (<4hr SLA) |
|  | HITLRouting | `NotificationAgent` | 72% → auto-approve notification |
|  | ReviewQueue | `ApprovalWorkflow` | Human reviewer decision |
|  | ApprovalWorkflow | `AuditAgent` | Approval/denial logged |

---

## 3. Security Chain Connection Trace

Every connection in the **defense-in-depth** path from ingress to workflow start.

| Order | Connection | Label |
|-------|------------|-------|
| 1 | `KongHub` → `LiteLLMRouter` | Model Requests\n$52K/day |
| 2 | `KongHub` → `CoreGWs` | Core Routing |
| 3 | `KongHub` → `AgentCommGWs` | Agent Mesh |
| 4 | `KongHub` → `KnowledgeGWs` | RAG Control |
| 5 | `KongHub` → `APIGateway` | API Routing |
| 6 | `KongHub` → `SecurityGateway` | OAuth2/JWT Auth |
| 7 | `KongHub` → `TokenMgmtGateway` | Rate Limit |
| 8 | `SecurityGateway` → `AIFirewallGateway` | Prompt Check |
| 9 | `AIFirewallGateway` → `GuardrailGateway` | Safety |
| 10 | `GuardrailGateway` → `ComplianceGateway` | HIPAA |
| 11 | `ComplianceGateway` → `AuditGateway` | Logging |
| 12 | `KongHub` → `ObservabilityGateway` | Traces |
| 13 | `SecurityGateway` → `WorkflowEngine` | ② Token Valid (OAuth2) |
| 14 | `TokenMgmtGateway` → `WorkflowEngine` | Quota OK (100/min) |
| 15 | `LiteLLMRouter` → `WorkflowEngine` | Model Response |
| 16 | `AIFirewallGateway` → `WorkflowEngine` | Security OK (Lakera) |
| 17 | `WorkflowGateway` → `WorkflowEngine` | DAG Control |
| 18 | `TokenMgmtGateway` → `Redis` | Rate State |
| 19 | `ClinicalAgent` → `GuardrailGateway` | Hallucination Check |
| 20 | `PolicyAgent` → `ComplianceGateway` | HIPAA Check |
| 21 | `AuditAgent` → `AuditGateway` | Immutable Log |
| 22 | `AuditAgent` → `ComplianceGateway` | HIPAA/SOC2 |
| 23 | `Prometheus` → `WorkflowEngine` | Metrics |
| 24 | `Jaeger` → `WorkflowEngine` | Traces |
| 25 | `Keycloak` → `AuthGW` | Auth Config |
| 26 | `Keycloak` → `PostgreSQL` | User DB |
| 27 | `FHIRGateway` → `WorkflowEngine` | Trigger PA |
| 28 | `X12Gateway` → `WorkflowEngine` | Trigger PA |
| 29 | `SLAMonitorService` → `WorkflowEngine` | Track SLA |
| 30 | `MultiTenantService` → `WorkflowEngine` | Payer Config |

**Failure behavior:** Any security gateway rejection terminates the request at KongHub with HTTP 403; no WorkflowEngine invocation. AuditGateway always receives a log entry (pass or fail).

---

## 4. Clinical Agent → RAG Sub-Pipeline

```
ClinicalAgent
  ├─(up)→ RAGGateway ─ hybrid orchestration (45ms)
  ├─(up)→ VectorDBGateway → Milvus
  ├─(up)→ KnowledgeGateway → Neo4j Cypher
  ├─(up)→ MemoryGateway → SemanticMemory → Milvus
  ├─(down)→ VectorSearch ──┐
  ├─(down)→ HybridSearch ──┼→ RRF → ClinicalContentService → ClinicalAgent context
  └─(down)→ GraphRAG ──────┘
       VectorSearch → Milvus (dashed)
       HybridSearch → Elasticsearch (dashed)
       GraphRAG → Neo4j (dashed)
  ├─(up)→ GuardrailGateway — hallucination check before LLM
  └─(up)→ LiteLLMRouter — GPT-4o inference (472 sec = 98.4% of 8 min)
```

| # | Connection | Label |
|---|------------|-------|
| 1 | `AIFirewallGateway` → `GuardrailGateway` | Safety |
| 2 | `GuardrailGateway` → `ComplianceGateway` | HIPAA |
| 3 | `MemoryGateway` → `Redis` | Working Memory |
| 4 | `BenefitsAgent` → `ClinicalAgent` | ⑥ Clinical |
| 5 | `ClinicalAgent` → `PolicyAgent` | ⑦ Policy |
| 6 | `FraudAgent` → `Neo4j` | Graph Patterns |
| 7 | `AuditAgent` → `Elasticsearch` | Audit Index |
| 8 | `EligibilityAgent` → `MemoryGateway` | Episode Recall |
| 9 | `BenefitsAgent` → `KnowledgeGateway` | Plan Ontology |
| 10 | `ClinicalAgent` → `LiteLLMRouter` | GPT-4o + RAG (8 min) |
| 11 | `ClinicalAgent` → `RAGGateway` | Hybrid Retrieval (45ms) |
| 12 | `ClinicalAgent` → `VectorDBGateway` | Milvus Search |
| 13 | `ClinicalAgent` → `KnowledgeGateway` | Neo4j Cypher |
| 14 | `ClinicalAgent` → `MemoryGateway` | Semantic Memory |
| 15 | `ClinicalAgent` → `GuardrailGateway` | Hallucination Check |
| 16 | `ClinicalAgent` → `ObservabilityGateway` | RAG Spans |
| 17 | `FraudAgent` → `KnowledgeGateway` | Fraud Patterns |
| 18 | `DecisionAgent` → `MemoryGateway` | Store Decision |
| 19 | `ClinicalAgent` → `VectorSearch` | Semantic Search |
| 20 | `ClinicalAgent` → `HybridSearch` | Keyword Search |
| 21 | `ClinicalAgent` → `GraphRAG` | Relationship Query |
| 22 | `VectorSearch` → `RRF` | Vector Scores |
| 23 | `HybridSearch` → `RRF` | BM25 Scores |
| 24 | `GraphRAG` → `RRF` | Relevance |
| 25 | `RRF` → `ClinicalContentService` | Top 10 Ranked Results |
| 26 | `VectorSearch` → `Milvus` | Vector Lookup |
| 27 | `HybridSearch` → `Elasticsearch` | Index Scan |
| 28 | `GraphRAG` → `Neo4j` | Graph Traverse |
| 29 | `ClinicalContentService` → `Elasticsearch` | Content |
| 30 | `ClinicalContentService` → `PostgreSQL` | Metadata |
| 31 | `FraudAgent` → `Neo4j` | — |
| 32 | `ClinicalContentService` → `Elasticsearch` | Content Index |
| 33 | `ClinicalContentService` → `PostgreSQL` | Metadata |
| 34 | `VectorSearch` → `Milvus` | — |
| 35 | `HybridSearch` → `Elasticsearch` | — |
| 36 | `GraphRAG` → `Neo4j` | — |
| 37 | `SafetyEval` → `ClinicalAgent` | Validate |
| 38 | `SemanticMemory` → `Milvus` | Vectors |
| 39 | `SemanticMemory` → `ClinicalAgent` | Knowledge |
| 40 | `Jaeger` → `ClinicalAgent` | RAG Spans |
| 41 | `Kafka` → `Elasticsearch` | Event Index |
| 42 | `ClinicalAgent` → `DocRequestAgent` | Pend Trigger |
| 43 | `AttachmentService` → `Elasticsearch` | Index Content |
| 44 | `RootCauseService` → `Elasticsearch` | Log Analysis |

---

## 5. HITL Branch Connection Map

**Routing logic (DecisionAgent → HITLRouting):**

- Confidence ≥0.85 AND fraud risk <30 → **auto-approve** (72%, 36K/day) → NotificationAgent
- Confidence <0.85 OR fraud risk ≥30 OR denial OR cost >$50K → **HITL** (28%, 14K/day) → ReviewQueue

| Connection | Label |
|------------|-------|
| `FraudAgent` → `DecisionAgent` | ⑨ Decision |
| `DecisionAgent` → `LiteLLMGW` | GPT-4o |
| `DecisionAgent` → `WorkingMemory` | Final Decision |
| `NotificationAgent` → `LiteLLMGW` | GPT-3.5 |
| `NotificationAgent` → `Kafka` | Events |
| `DecisionAgent` → `LiteLLMRouter` | GPT-4o Decision |
| `DecisionAgent` → `HITLGateway` | Route (28% Human) |
| `DecisionAgent` → `ApprovalGateway` | Workflow Trigger |
| `DecisionAgent` → `AgentGovernanceGateway` | Permission Check |
| `DecisionAgent` → `MemoryGateway` | Store Decision |
| `NotificationAgent` → `LiteLLMRouter` | GPT-3.5 |
| `NotificationAgent` → `SaaSConnectorGateway` | Slack/Teams |
| `NotificationAgent` → `DataGateway` | Event Pub |
| `NotificationAgent` → `UsageAnalyticsGateway` | Behavior Track |
| `DecisionAgent` → `HITLRouting` | ⑩ Risk Assessment |
| `DecisionAgent` → `HITLRouting` | ⑩ Risk Assessment |
| `HITLRouting` → `ReviewQueue` | 28% Human (14K/day) |
| `ReviewQueue` → `ApprovalWorkflow` | — |
| `ApprovalWorkflow` → `PostgreSQL` | Approval Log |
| `ApprovalWorkflow` → `Kafka` | Event Stream |
| `HITLRouting` → `NotificationAgent` | 72% Auto-Approve (36K/day) |
| `ApprovalWorkflow` → `AuditAgent` | Log |
| `Kafka` → `NotificationAgent` | Consume |
| `DecisionAgent` → `MedDirectorAgent` | P2P Request |
| `MedDirectorAgent` → `LiteLLMRouter` | GPT-4o Summary |
| `MedDirectorAgent` → `ProviderPortalService` | Schedule P2P |
| `DocRequestAgent` → `NotificationAgent` | Provider Alert |
| `QualityMeasureService` → `DecisionAgent` | HEDIS Track |
| `DLPService` → `NotificationAgent` | PHI Scan |
| `CapacityPlanningService` → `HITLRouting` | Staffing Plan |
| `CapacityPlanningService` → `PostgreSQL` | Historical Data |
| `RootCauseService` → `DecisionAgent` | Denial Pattern |
| `CommPreferenceService` → `NotificationAgent` | Channel Select |

---

## 6. Integration Gateway Side Paths

- `WebPortal` → `FHIRGateway`: FHIR API
- `ProviderPortal` → `X12Gateway`: X12 278
- `EDIGateway` → `X12Gateway`: EDI Feed
- `MobileApp` → `FHIRGateway`: Mobile API
- `FHIRGateway` → `FHIRCDSService`: CDS Hooks
- `X12Gateway` → `ePAService`: ePA Process
- `NCPDPGateway` → `ePAService`: Pharmacy PA
- `DirectGateway` → `AttachmentService`: Secure Docs
- `FHIRGateway` → `WorkflowEngine`: Trigger PA
- `X12Gateway` → `WorkflowEngine`: Trigger PA
- `DocRequestAgent` → `AttachmentService`: Doc Upload
- `ePAService` → `IntakeAgent`: Transform PA
- `ePAService` → `PostgreSQL`: EDI Log
- `FHIRCDSService` → `FormularyService`: PA Check
- `FHIRCDSService` → `PolicyService`: Rules Check
- `AttachmentService` → `BlobStorage`: Store Docs
- `AttachmentService` → `Elasticsearch`: Index Content
- `PayerExchangeService` → `FHIRGateway`: FHIR Export
- `PayerExchangeService` → `PostgreSQL`: PA Transfer
- `ConsentMgmtService` → `PayerExchangeService`: Consent Check

---

## 7. v3.0 New Agent Side Paths

### `DocRequestAgent`

**Inbound:**
- `ClinicalAgent` → Pend Trigger

**Outbound:**
- → `LiteLLMRouter`: GPT-4o Gen
- → `AttachmentService`: Doc Upload
- → `NotificationAgent`: Provider Alert

### `ExpeditedAgent`

**Inbound:**
- `WorkflowEngine` → Urgent Route

**Outbound:**
- → `LiteLLMRouter`: GPT-4o Priority
- → `SLAMonitorService`: 72hr Track

### `MedDirectorAgent`

**Inbound:**
- `DecisionAgent` → P2P Request

**Outbound:**
- → `LiteLLMRouter`: GPT-4o Summary
- → `ProviderPortalService`: Schedule P2P

### `RegistryAgent`

**Inbound:**
- `IntakeAgent` → De-dup Check

**Outbound:**
- → `LiteLLMRouter`: GPT-3.5
- → `Redis`: Active PA Cache
- → `PostgreSQL`: PA History

### `RetrospectiveAgent`

**Inbound:**
- `WorkflowEngine` → Post-Service

**Outbound:**
- → `LiteLLMRouter`: GPT-4o + RAG
- → `ClaimsService`: UB-04/1500

### `StepTherapyAgent`

**Inbound:**
- `BenefitsAgent` → Drug PA

**Outbound:**
- → `LiteLLMRouter`: GPT-4o
- → `ClaimsService`: Prior Fills
- → `DrugReferenceService`: NDC Lookup

---

## 8. Database Write Map

### `PostgreSQL`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `StateManager` | Cold Store (90d) |
| `Temporal` | Event History |
| `IntakeAgent` | Metadata |
| `AuditAgent` | Compliance |
| `ClinicalContentService` | Metadata |
| `MemberService` | Member DB |
| `ProviderService` | Provider DB |
| `PolicyService` | Policy DB |
| `ClaimsService` | Claims DB |
| `BenefitsConfigService` | Config DB |
| `NetworkService` | Network DB |
| `FormularyService` | Formulary DB |
| `ClinicalContentService` | Metadata |
| `AgentRegistry` | Agent Metadata |
| `PromptMgmt` | Prompt Versions |
| `MCPRegistry` | Tool Registry |
| `EpisodicMemory` | Storage |
| `ApprovalWorkflow` | Approval Log |
| `Prometheus` | Metrics |
| `Jaeger` | Store |
| `Keycloak` | User DB |
| `Kafka` | Event Log |
| `RegistryAgent` | PA History |
| `ePAService` | EDI Log |
| `DrugReferenceService` | NDC/RxNorm |
| `SLAMonitorService` | Deadline Store |
| `QualityMeasureService` | Stars Data |
| `PayerExchangeService` | PA Transfer |
| `ProviderPortalService` | PA Status |
| `GrievanceTrackService` | Timeline Store |
| `DLPService` | Incident Log |
| `ConsentMgmtService` | Consent DB |
| `BreachNotifyService` | Breach Log |
| `StateMandateService` | 50-State DB |
| `CapacityPlanningService` | Historical Data |
| `ProviderAnalyticsService` | Analytics DB |
| `CommPreferenceService` | Member Prefs |

### `Redis`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `DataAccessGateway` | Token Cache |
| `TokenMgmtGateway` | Rate State |
| `ContextGateway` | Session Context |
| `MemoryGateway` | Working Memory |
| `StateManager` | Hot Store (5min) |
| `MemberService` | Cache |
| `ProviderService` | Cache |
| `PolicyService` | Cache |
| `SafetyEval` | Cache Scores |
| `WorkingMemory` | Cache |
| `Grafana` | Dashboard Cache |
| `RegistryAgent` | Active PA Cache |
| `DrugReferenceService` | 95% Cache |
| `CodeValidationService` | Code Cache |
| `CommPreferenceService` | Pref Cache |

### `Milvus`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `VectorSearch` | Vector Lookup |
| `VectorSearch` | read/write |
| `SemanticMemory` | Vectors |

### `Neo4j`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `FraudAgent` | Graph Patterns |
| `GraphRAG` | Graph Traverse |
| `FraudAgent` | read/write |
| `GraphRAG` | read/write |

### `Elasticsearch`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `AuditAgent` | Audit Index |
| `HybridSearch` | Index Scan |
| `ClinicalContentService` | Content |
| `ClinicalContentService` | Content Index |
| `HybridSearch` | read/write |
| `Kafka` | Event Index |
| `AttachmentService` | Index Content |
| `RootCauseService` | Log Analysis |

### `BlobStorage`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `IntakeAgent` | Store PDF |
| `AttachmentService` | Store Docs |

### `MongoDB`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `MultiTenantService` | Config Store |

### `Vault`

| Writer Component | Operation (from arrow label) |
|------------------|-----------------------------|
| `ToolExecutor` | Secrets |

---

## 9. Per-Component Deep Profiles + Connections

Each component profile includes:

- **Architecture Pattern** — design pattern and integration style
- **Technology Stack** — frameworks, protocols, versions
- **Business Use Cases** — why it exists, who benefits, regulatory drivers
- **Key Metrics** — volume, latency, accuracy, cost
- **Implementation & Flow Position** — where it sits in the PA pipeline
- **Inbound / Outbound Connections** — every diagram arrow

### Layer 1 — Presentation

*Six ingress channels feeding 50K PA/day into KongHub. Pattern: **Channel Adapter → API Gateway**.*

#### `EDIGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1 — Presentation |
| **Role** | EDI X12 Ingress Adapter |
| **Architecture Pattern** | Adapter pattern; Mirth Connect → canonical PA model → KongHub |

**Technology Stack:**

- Mirth Connect
- X12 278/837
- USTAR clearinghouse
- TA1 ACK generation

**Business Use Cases:**

- Receive batch EDI 278 prior auth requests from clearinghouses (10K/day)
- Transform X12 to internal PA canonical model for IntakeAgent
- Send X12 278 response back to provider systems
- Support legacy hospital EMR integrations without FHIR

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 10K/day |
| Parse Success | 99.7% |

**Implementation & Flow Position:** Feeds X12Gateway and KongHub; triggers WorkflowEngine on validated 278.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `KongHub` | EDI X12 (10K/day) |
| 2 | `X12Gateway` | EDI Feed |

**Connection narrative:** sends to `KongHub` (EDI X12 (10K/day)); sends to `X12Gateway` (EDI Feed).

---

#### `FaxOCR`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1 — Presentation |
| **Role** | Fax/OCR Document Capture |
| **Architecture Pattern** | Event-driven OCR pipeline; fax → blob → Form Recognizer → IntakeAgent queue |

**Technology Stack:**

- Azure Form Recognizer
- Twilio Fax API
- Azure Blob Storage
- Kafka event trigger

**Business Use Cases:**

- Capture legacy fax-based PA submissions (still 8% of volume)
- OCR handwritten and typed medical forms (98.5% accuracy)
- Support UB-04, CMS-1500, HCFA form templates
- Auto-route low-confidence OCR to HITL document review

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Ocr Accuracy | 98.5% |
| Avg Processing | 2 min |

**Implementation & Flow Position:** Stores originals in BlobStorage; extracted text sent to KongHub → IntakeAgent.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `KongHub` | OCR Docs (98.5%) |

**Connection narrative:** sends to `KongHub` (OCR Docs (98.5%)).

---

#### `MobileApp`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1 — Presentation |
| **Role** | Native Mobile Application |
| **Architecture Pattern** | React Native cross-platform; offline-first draft PA with sync-on-connect |

**Technology Stack:**

- React Native
- FHIR R4 client
- Push notifications (FCM/APNs)
- Keycloak mobile OAuth

**Business Use Cases:**

- Mobile PA submission with camera document capture
- Push notification on PA decision (approve/deny/pend)
- Offline draft PA forms for rural/low-connectivity providers
- Biometric login for provider quick access

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Dau | 50K |
| Offline Sync Success | 99.1% |

**Implementation & Flow Position:** Connects to KongHub and FHIRGateway for mobile-optimized FHIR Bundle submission.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `KongHub` | Mobile App (50K DAU) |
| 2 | `FHIRGateway` | Mobile API |

**Connection narrative:** sends to `KongHub` (Mobile App (50K DAU)); sends to `FHIRGateway` (Mobile API).

---

#### `ProviderPortal`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1 — Presentation |
| **Role** | Provider Admin Dashboard |
| **Architecture Pattern** | Angular SPA + GraphQL API (ProviderPortalService); SSO with 2FA |

**Technology Stack:**

- Angular 17
- GraphQL
- Keycloak SSO+2FA
- Bulk CSV upload

**Business Use Cases:**

- Provider PA dashboard: pending, approved, denied counts
- Bulk PA upload for high-volume practices (orthopedics, oncology)
- Peer-to-peer review request (triggers MedDirectorAgent)
- Document re-submission for pended cases (DocRequestAgent flow)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Providers | 85K active |
| Bulk Upload Max | 500 PA/batch |

**Implementation & Flow Position:** Primary channel for X12Gateway 278 submissions; SSO federated through KongHub SecurityGateway.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ProviderPortalService` | GraphQL API |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `KongHub` | Provider Portal (SSO) |
| 2 | `X12Gateway` | X12 278 |

**Connection narrative:** receives from `ProviderPortalService` (GraphQL API); sends to `KongHub` (Provider Portal (SSO)); sends to `X12Gateway` (X12 278).

---

#### `VoiceIVR`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1 — Presentation |
| **Role** | IVR Voice Channel |
| **Architecture Pattern** | IVR state machine; Azure Speech STT/TTS → API lookup |

**Technology Stack:**

- Twilio Voice
- Azure Speech Services
- Multi-language (EN/ES)
- DTMF + voice intent

**Business Use Cases:**

- 24/7 PA status check by member ID + DOB
- Route urgent cases to expedited queue (keyword detection)
- Provider callback scheduling for peer-to-peer reviews
- Accessibility channel for members without internet access

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Availability | 24/7 |
| Call Volume | 3K/day |
| Containment Rate | 72% |

**Implementation & Flow Position:** Voice intents translated to REST calls via KongHub; no direct agent access.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `KongHub` | IVR (24/7) |

**Connection narrative:** sends to `KongHub` (IVR (24/7)).

---

#### `WebPortal`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1 — Presentation |
| **Role** | Member/Provider Web Application |
| **Architecture Pattern** | BFF (Backend-for-Frontend) + SPA; WebSocket push for real-time PA status |

**Technology Stack:**

- React 18
- Node.js BFF
- WebSocket
- OAuth2/JWT (Keycloak)
- REST + GraphQL

**Business Use Cases:**

- Submit prior authorization requests with document upload (PDF, DICOM)
- Track PA status in real time (WebSocket updates every 30 sec)
- View approval/denial letters and appeal options
- Member self-service: check benefits, find in-network providers
- Provider bulk upload: CSV batch PA submission (up to 500/request)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Concurrent Users | 100K |
| Peak Load | 2,500 req/hour |
| Availability | 99.95% |

**Implementation & Flow Position:** Routes all traffic through KongHub (step ①). SSO via Keycloak; optional FHIRGateway for CDS Hooks integration.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `KongHub` | ① WebSocket (100K users) |
| 2 | `FHIRGateway` | FHIR API |

**Connection narrative:** sends to `KongHub` (① WebSocket (100K users)); sends to `FHIRGateway` (FHIR API).

---

### Layer 1.5 — Healthcare Integration

*Standards-based interoperability (FHIR, X12, NCPDP, Direct). Pattern: **Anti-Corruption Layer → Canonical PA Model**.*

#### `DirectGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1.5 — Healthcare Integration |
| **Role** | Direct Secure Messaging Gateway |
| **Architecture Pattern** | DirectTrust S/MIME secure messaging; XDR/XDR document push/pull |

**Technology Stack:**

- DirectTrust
- S/MIME encryption
- XDR/XDM packaging
- HIPAA compliant transport

**Business Use Cases:**

- Secure clinical document exchange between providers (5K/day)
- Receive supporting clinical notes for pended PAs
- Send PA decision letters via secure Direct address
- AttachmentService integration for encrypted doc storage

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 5K/day |
| Encryption | S/MIME AES-256 |

**Implementation & Flow Position:** Documents routed to AttachmentService → BlobStorage → IntakeAgent re-processing.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `AttachmentService` | Secure Docs |

**Connection narrative:** sends to `AttachmentService` (Secure Docs).

---

#### `FHIRGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1.5 — Healthcare Integration |
| **Role** | HL7 FHIR R4 API Gateway |
| **Architecture Pattern** | FHIR facade + CDS Hooks 2.0; CRD/DTR for prior auth at point of care |

**Technology Stack:**

- HAPI FHIR R4
- CDS Hooks 2.0
- OAuth2 SMART on FHIR
- PA CRD/DTR IG

**Business Use Cases:**

- Real-time PA requirement check during EHR ordering (CDS Hooks)
- Submit PA via FHIR MedicationRequest/ServiceRequest resources
- Patient/$everything for clinical context enrichment
- Interoperability with Epic, Cerner, Athena EHR systems (100K/day)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 100K/day |
| Cds Hook Latency P95 | <500ms |

**Implementation & Flow Position:** FHIRCDSService for formulary/rules; triggers WorkflowEngine on PA submission.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `WebPortal` | FHIR API |
| 2 | `MobileApp` | Mobile API |
| 3 | `PayerExchangeService` | FHIR Export |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `FHIRCDSService` | CDS Hooks |
| 2 | `WorkflowEngine` | Trigger PA |

**Connection narrative:** receives from `WebPortal` (FHIR API); receives from `MobileApp` (Mobile API); receives from `PayerExchangeService` (FHIR Export); sends to `FHIRCDSService` (CDS Hooks); sends to `WorkflowEngine` (Trigger PA).

---

#### `NCPDPGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1.5 — Healthcare Integration |
| **Role** | Pharmacy PA Gateway (NCPDP SCRIPT) |
| **Architecture Pattern** | Pharmacy-specific adapter; SCRIPT 10.6 PARequest/PAResponse |

**Technology Stack:**

- NCPDP SCRIPT 10.6
- Surescripts integration
- NDC/RxNorm mapping

**Business Use Cases:**

- Pharmacy prior auth for specialty/high-cost drugs (20K/day)
- Real-time PA at pharmacy counter (reduce abandonment)
- Integrate with StepTherapyAgent for drug protocol validation
- Electronic PA response to pharmacy management systems

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 20K/day |
| Avg Response | 45 sec |

**Implementation & Flow Position:** Routes to ePAService → StepTherapyAgent for drug PAs.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ePAService` | Pharmacy PA |

**Connection narrative:** sends to `ePAService` (Pharmacy PA).

---

#### `X12Gateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 1.5 — Healthcare Integration |
| **Role** | X12 278 Prior Auth Processor |
| **Architecture Pattern** | EDI translation layer; ASC X12N 005010X217 ↔ canonical PA model |

**Technology Stack:**

- Edifabric X12 parser
- ASC X12N 005010X217
- TA1/999 ACK
- ePAService transform

**Business Use Cases:**

- Process standard 278 prior auth request/response (30K/day)
- Support ASC X12N compliance for payer-provider B2B
- Inquiry/response loop for PA status checks
- Bridge hospital billing systems to AI PA workflow

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 30K/day |
| Compliance | ASC X12N 005010X217 |

**Implementation & Flow Position:** ePAService transforms to IntakeAgent input; triggers WorkflowEngine.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ProviderPortal` | X12 278 |
| 2 | `EDIGateway` | EDI Feed |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ePAService` | ePA Process |
| 2 | `WorkflowEngine` | Trigger PA |

**Connection narrative:** receives from `ProviderPortal` (X12 278); receives from `EDIGateway` (EDI Feed); sends to `ePAService` (ePA Process); sends to `WorkflowEngine` (Trigger PA).

---

### Layer 2 — Gateway Control Plane

*Kong + LiteLLM hub-and-spoke control plane managing 60 specialized gateways. Pattern: **Gateway Mesh + Model Router**.*

#### `KongHub`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Control Plane |
| **Role** | Central API Ingress & Gateway Orchestrator |
| **Architecture Pattern** | API Gateway + Control Plane hub; all 60 gateways managed centrally (hub-and-spoke) |

**Technology Stack:**

- Kong Enterprise 3.4
- Plugin manager
- Rate limiting
- Zone-redundant HA
- Admin API

**Business Use Cases:**

- Single secure entry point for 50K PA/day across all channels
- Route requests to appropriate gateway tier (core, agent, RAG, security)
- Enforce rate limits and OAuth2 before any AI processing ($52K/day LLM cost control)
- Plugin-based extensibility for new payer integrations

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Throughput | 10K req/sec |
| Overhead | <50ms |
| Availability | 99.95% |

**Implementation & Flow Position:** All presentation channels connect here (step ①). Fans out to APIGateway, SecurityGateway, LiteLLMRouter.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `WebPortal` | ① WebSocket (100K users) |
| 2 | `MobileApp` | Mobile App (50K DAU) |
| 3 | `ProviderPortal` | Provider Portal (SSO) |
| 4 | `EDIGateway` | EDI X12 (10K/day) |
| 5 | `FaxOCR` | OCR Docs (98.5%) |
| 6 | `VoiceIVR` | IVR (24/7) |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | Model Requests\n$52K/day |
| 2 | `CoreGWs` | Core Routing |
| 3 | `AgentCommGWs` | Agent Mesh |
| 4 | `KnowledgeGWs` | RAG Control |
| 5 | `APIGateway` | API Routing |
| 6 | `SecurityGateway` | OAuth2/JWT Auth |
| 7 | `TokenMgmtGateway` | Rate Limit |
| 8 | `ObservabilityGateway` | Traces |

**Connection narrative:** receives from `WebPortal` (① WebSocket (100K users)); receives from `MobileApp` (Mobile App (50K DAU)); receives from `ProviderPortal` (Provider Portal (SSO)); sends to `LiteLLMRouter` (Model Requests\n$52K/day); sends to `CoreGWs` (Core Routing); sends to `AgentCommGWs` (Agent Mesh); + 3 more inbound; + 5 more outbound.

---

#### `LiteLLMRouter`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Control Plane |
| **Role** | Multi-Model LLM Router |
| **Architecture Pattern** | Model router with 3-tier fallback; cost-aware routing by agent complexity |

**Technology Stack:**

- LiteLLM 1.30
- GPT-4o
- Claude 3.5 Sonnet
- GPT-3.5 Turbo
- Custom PyTorch GNN

**Business Use Cases:**

- Route Intake/Clinical/Decision to GPT-4o (50% traffic, highest accuracy)
- Route Policy/Appeals to Claude 3.5 (25%, long-context policy docs)
- Route Eligibility/Benefits to GPT-3.5 (20%, cost-efficient simple tasks)
- Automatic failover on model outage (primary → secondary → tertiary)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Daily Cost | $52K |
| Cost Per Request | $1.04 |
| Routing Latency | 10ms |

**Implementation & Flow Position:** Every agent calls upward to LiteLLMRouter; ModelGWs tier below for inference dispatch.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | Model Requests\n$52K/day |
| 2 | `AIGateway` | Model Select |
| 3 | `AIGateway` | AI Request |
| 4 | `COMAgent` | GPT-4o COB |
| 5 | `IntakeAgent` | GPT-4o Vision (47K tokens) |
| 6 | `EligibilityAgent` | GPT-3.5 Turbo |
| 7 | `BenefitsAgent` | GPT-4o |
| 8 | `ClinicalAgent` | GPT-4o + RAG (8 min) |
| 9 | `PolicyAgent` | Claude 3.5 Sonnet |
| 10 | `FraudAgent` | Custom ML Model |
| 11 | `DecisionAgent` | GPT-4o Decision |
| 12 | `NotificationAgent` | GPT-3.5 |
| 13 | `AuditAgent` | GPT-4o Logging |
| 14 | `COMAgent` | GPT-4o COB |
| 15 | `ExpeditedAgent` | GPT-4o Priority |
| 16 | `StepTherapyAgent` | GPT-4o |
| 17 | `MedDirectorAgent` | GPT-4o Summary |
| 18 | `RetrospectiveAgent` | GPT-4o + RAG |
| 19 | `RegistryAgent` | GPT-3.5 |
| 20 | `DocRequestAgent` | GPT-4o Gen |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ModelGWs` | Model Selection |
| 2 | `InferenceGateway` | Inference |
| 3 | `LLMGateway` | Routing Logic |
| 4 | `WorkflowEngine` | Model Response |

**Connection narrative:** receives from `KongHub` (Model Requests\n$52K/day); receives from `AIGateway` (Model Select); receives from `AIGateway` (AI Request); sends to `ModelGWs` (Model Selection); sends to `InferenceGateway` (Inference); sends to `LLMGateway` (Routing Logic); + 17 more inbound; + 1 more outbound.

---

### Layer 2 — Core Gateways

#### `AIGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 1 Core |
| **Role** | Gateway #2: GenAI Controller |
| **Architecture Pattern** | AI orchestration facade |

**Technology Stack:**

- Kong AI plugin
- Prompt chain manager
- Session context store

**Business Use Cases:**

- Orchestrate multi-step LLM prompt chains for complex agents
- Manage conversation context across agent handoffs
- Route to LiteLLMRouter for model selection

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** Receives from APIGateway; primary path to LiteLLMRouter and WorkflowEngine.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `APIGateway` | GenAI Requests |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | Model Select |
| 2 | `LiteLLMRouter` | AI Request |

**Connection narrative:** receives from `APIGateway` (GenAI Requests); sends to `LiteLLMRouter` (Model Select); sends to `LiteLLMRouter` (AI Request).

---

#### `APIGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 1 Core |
| **Role** | Gateway #1: REST/gRPC Router |
| **Architecture Pattern** | Reverse proxy + path-based routing |

**Technology Stack:**

- Kong
- HTTP/2
- gRPC
- WebSocket
- Weighted round-robin LB

**Business Use Cases:**

- Route REST/gRPC API calls to backend microservices
- Protocol translation HTTP/2 ↔ gRPC
- Header-based tenant routing for multi-payer

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 5ms |

**Implementation & Flow Position:** Entry from KongHub; forwards GenAI requests to AIGateway.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | API Routing |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `AIGateway` | GenAI Requests |

**Connection narrative:** receives from `KongHub` (API Routing); sends to `AIGateway` (GenAI Requests).

---

#### `SecurityGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 6 Governance |
| **Role** | Gateway #26: OAuth2/JWT/mTLS Security |
| **Architecture Pattern** | Zero-trust ingress; token validation gate |

**Technology Stack:**

- Keycloak OAuth2
- JWT RS256 verification
- mTLS cert management
- TOTP 2FA

**Business Use Cases:**

- Validate OAuth2 JWT before any PA processing (step ②)
- Enforce MFA for provider portal access
- Terminate unauthorized requests with HTTP 403

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 5ms |

**Implementation & Flow Position:** KongHub → SecurityGateway → WorkflowEngine. First security gate.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | OAuth2/JWT Auth |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `AIFirewallGateway` | Prompt Check |
| 2 | `WorkflowEngine` | ② Token Valid (OAuth2) |

**Connection narrative:** receives from `KongHub` (OAuth2/JWT Auth); sends to `AIFirewallGateway` (Prompt Check); sends to `WorkflowEngine` (② Token Valid (OAuth2)).

---

#### `TokenMgmtGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Core Gateways |
| **Role** | Rate limiting |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Redis token bucket

**Business Use Cases:**

- 100 req/min per client; quota gate to WorkflowEngine.

**Implementation & Flow Position:** Component `TokenMgmtGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | Rate Limit |
| 2 | `CostMgmtGateway` | Tokens |
| 3 | `EligibilityAgent` | Token Count |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `WorkflowEngine` | Quota OK (100/min) |
| 2 | `Redis` | Rate State |

**Connection narrative:** receives from `KongHub` (Rate Limit); receives from `CostMgmtGateway` (Tokens); receives from `EligibilityAgent` (Token Count); sends to `WorkflowEngine` (Quota OK (100/min)); sends to `Redis` (Rate State).

---

### Layer 2 — Model Gateways

#### `LLMGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 1 Core |
| **Role** | Gateway #3: Model Selector |
| **Architecture Pattern** | Strategy pattern model routing with 3-tier fallback |

**Technology Stack:**

- LiteLLM proxy
- Model registry
- Cost optimizer
- Automatic downgrade for simple queries

**Business Use Cases:**

- Select optimal model per task complexity and cost
- Failover: GPT-4o → Claude 3.5 → GPT-3.5 on outage
- Track token usage for CostMgmtGateway

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 10ms |

**Implementation & Flow Position:** Between LiteLLMRouter and AgentGateway in model dispatch chain.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `LiteLLMRouter` | Routing Logic |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `AgentGateway` | Agent Dispatch |

**Connection narrative:** receives from `LiteLLMRouter` (Routing Logic); sends to `AgentGateway` (Agent Dispatch).

---

#### `LiteLLMGW`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Model Gateways |
| **Role** | LiteLLM shortcut |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- LiteLLM

**Business Use Cases:**

- Direct agent→model path (legacy alias).

**Implementation & Flow Position:** Component `LiteLLMGW` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `IntakeAgent` | GPT-4o Vision |
| 2 | `EligibilityAgent` | GPT-3.5 |
| 3 | `BenefitsAgent` | GPT-4o |
| 4 | `PolicyAgent` | Claude 3.5 |
| 5 | `FraudAgent` | ML Scoring |
| 6 | `DecisionAgent` | GPT-4o |
| 7 | `NotificationAgent` | GPT-3.5 |
| 8 | `AuditAgent` | GPT-4o Log |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `IntakeAgent` (GPT-4o Vision); receives from `EligibilityAgent` (GPT-3.5); receives from `BenefitsAgent` (GPT-4o); + 5 more inbound.

---

### Layer 2 — Agent Gateways

#### `A2AGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 2 Agent Comm |
| **Role** | Gateway #6: Agent-to-Agent Mesh |
| **Architecture Pattern** | Message bus; point-to-point and broadcast agent messaging |

**Technology Stack:**

- gRPC bidirectional streaming
- Kafka agent topics
- Message routing table

**Business Use Cases:**

- Enable COM agent multi-payer coordination
- Appeals agent requests new evidence from Intake agent
- Broadcast fraud alerts to Policy agent

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 5ms |

**Implementation & Flow Position:** COMAgent and AppealsAgent primary consumers.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `AgentGateway` | Agent-to-Agent |
| 2 | `COMAgent` | Agent-to-Agent |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `AgentGateway` (Agent-to-Agent); receives from `COMAgent` (Agent-to-Agent).

---

#### `AgentGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 1 Core |
| **Role** | Gateway #4: Multi-Agent Hub |
| **Architecture Pattern** | Supervisor dispatch pattern (LangGraph) |

**Technology Stack:**

- LangGraph 0.2.15 supervisor
- Agent registry
- Dynamic agent selection

**Business Use Cases:**

- Dispatch PA request to correct agent in DAG sequence
- Coordinate parallel Benefits+Fraud execution
- Fan-out to MCP/A2A/Mesh gateways

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 12ms |

**Implementation & Flow Position:** Central agent dispatch; connects to all 17 agents via AgentMeshGateway.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `LLMGateway` | Agent Dispatch |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `MultiAgentGateway` | Supervisor |
| 2 | `MCPGateway` | Context Protocol |
| 3 | `A2AGateway` | Agent-to-Agent |
| 4 | `AgentMeshGateway` | Load Balance |
| 5 | `ToolGateway` | Tool Registry |

**Connection narrative:** receives from `LLMGateway` (Agent Dispatch); sends to `MultiAgentGateway` (Supervisor); sends to `MCPGateway` (Context Protocol); sends to `A2AGateway` (Agent-to-Agent); + 2 more outbound.

---

#### `AgentMeshGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 2 Agent Comm |
| **Role** | Gateway #8: Service Mesh |
| **Architecture Pattern** | Sidecar proxy; auto-scaling load balancer |

**Technology Stack:**

- Envoy proxy
- Consul service discovery
- Health check failover

**Business Use Cases:**

- Load balance agent replicas during peak (2,500/hour)
- Auto-failover on agent pod crash
- Circuit breaker on agent timeout

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 3ms |

**Implementation & Flow Position:** Sits between AgentGateway and individual agent instances.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `AgentGateway` | Load Balance |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `AgentGateway` (Load Balance).

---

#### `MCPGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 2 Agent Comm |
| **Role** | Gateway #5: Model Context Protocol |
| **Architecture Pattern** | MCP client-server; tool discovery and invocation |

**Technology Stack:**

- Model Context Protocol 1.0
- Tool registry (50+ tools)
- Resource quota manager

**Business Use Cases:**

- Share context across agents without re-fetching member data
- Discover and invoke MCP tools (member_lookup, tier_calc)
- Enforce per-agent memory/compute quotas

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** All agents access tools via MCPGateway → ToolGateway → MCPRegistry.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `AgentGateway` | Context Protocol |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `AgentGateway` (Context Protocol).

---

#### `MultiAgentGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 2 Agent Comm |
| **Role** | Gateway #7: Supervisor Pattern |
| **Architecture Pattern** | Supervisor/worker; centralized workflow coordination |

**Technology Stack:**

- LangGraph supervisor node
- Global Redis state
- Confidence-based agent selection

**Business Use Cases:**

- Orchestrate which agent runs next based on DAG state
- Manage global workflow state across agent boundaries
- Handle conditional routing decisions

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 15ms |

**Implementation & Flow Position:** Pairs with WorkflowEngine LangGraph DAG implementation.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `AgentGateway` | Supervisor |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `AgentGateway` (Supervisor).

---

### Layer 2 — Security Gateways

#### `AIFirewallGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 6 Governance |
| **Role** | Gateway #24: Prompt Injection Defense |
| **Architecture Pattern** | Inline security filter; threat pattern matching |

**Technology Stack:**

- Lakera Guard
- Rebuff adversarial detection
- 10K+ attack pattern DB

**Business Use Cases:**

- Block prompt injection and jailbreak attempts before LLM
- Scan provider free-text fields for adversarial content
- Log blocked attempts to AuditGateway

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 10ms |

**Implementation & Flow Position:** SecurityGateway → AIFirewallGateway → GuardrailGateway chain.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `SecurityGateway` | Prompt Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `GuardrailGateway` | Safety |
| 2 | `WorkflowEngine` | Security OK (Lakera) |

**Connection narrative:** receives from `SecurityGateway` (Prompt Check); sends to `GuardrailGateway` (Safety); sends to `WorkflowEngine` (Security OK (Lakera)).

---

#### `AuditGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 6 Governance |
| **Role** | Gateway #30: Immutable Compliance Audit |
| **Architecture Pattern** | Append-only audit log; WORM storage |

**Technology Stack:**

- Elasticsearch WORM index
- Immutable append-only log
- 7-year archive

**Business Use Cases:**

- Create forensic audit trail for every PA decision
- Support CMS/state regulatory audit requests
- Enable RootCauseService log analysis

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 15ms |

**Implementation & Flow Position:** Terminus of security chain; all requests logged pass or fail.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ComplianceGateway` | Logging |
| 2 | `AuditAgent` | Immutable Log |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `ComplianceGateway` (Logging); receives from `AuditAgent` (Immutable Log).

---

#### `AuthGW`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Security Gateways |
| **Role** | Auth config |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Keycloak adapter

**Business Use Cases:**

- Keycloak integration config.

**Implementation & Flow Position:** Component `AuthGW` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `Keycloak` | Auth Config |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `Keycloak` (Auth Config).

---

#### `ComplianceGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 6 Governance |
| **Role** | Gateway #27: HIPAA/GDPR/SOC2 Compliance |
| **Architecture Pattern** | Policy enforcement point; data residency router |

**Technology Stack:**

- HIPAA middleware
- Geographic routing US/EU
- 6-year retention enforcement

**Business Use Cases:**

- Enforce PHI handling rules on all AI requests/responses
- Route data to correct geographic region (data residency)
- Trigger AuditGateway logging on every request

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** GuardrailGateway → ComplianceGateway → AuditGateway → WorkflowEngine.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `GuardrailGateway` | HIPAA |
| 2 | `PolicyAgent` | HIPAA Check |
| 3 | `AuditAgent` | HIPAA/SOC2 |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `AuditGateway` | Logging |

**Connection narrative:** receives from `GuardrailGateway` (HIPAA); receives from `PolicyAgent` (HIPAA Check); receives from `AuditAgent` (HIPAA/SOC2); sends to `AuditGateway` (Logging).

---

#### `GuardrailGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 6 Governance |
| **Role** | Gateway #23: AI Safety Guardrails |
| **Architecture Pattern** | Output validation pipeline |

**Technology Stack:**

- Guardrails AI
- Hallucination detector
- PII content filter
- Citation validator

**Business Use Cases:**

- Validate ClinicalAgent output for medical hallucinations (99.9% safe)
- Require guideline citations on all clinical claims
- Filter toxic/inappropriate LLM output

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** ClinicalAgent output validation; ComplianceGateway upstream chain.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `AIFirewallGateway` | Safety |
| 2 | `ClinicalAgent` | Hallucination Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ComplianceGateway` | HIPAA |

**Connection narrative:** receives from `AIFirewallGateway` (Safety); receives from `ClinicalAgent` (Hallucination Check); sends to `ComplianceGateway` (HIPAA).

---

### Layer 2 — Tool Gateways

#### `FunctionCallingGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 4 Tool |
| **Role** | Gateway #15: LLM Function Calling |
| **Architecture Pattern** | OpenAI function calling binding; JSON schema validation |

**Technology Stack:**

- OpenAI function calling API
- JSON Schema validator
- Sync + async execution modes

**Business Use Cases:**

- Extract structured parameters from LLM output automatically
- Execute BenefitsAgent tier_calc function against BenefitsConfigService
- Validate types before data service calls

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** BenefitsAgent tier calculation; binds LLM output to backend APIs.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ToolGateway` | Exec Functions |
| 2 | `BenefitsAgent` | Tier Calc |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `EnterpriseIntGateway` | SAP/Oracle |

**Connection narrative:** receives from `ToolGateway` (Exec Functions); receives from `BenefitsAgent` (Tier Calc); sends to `EnterpriseIntGateway` (SAP/Oracle).

---

#### `ToolGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 4 Tool |
| **Role** | Gateway #14: Tool Dispatcher |
| **Architecture Pattern** | Tool registry + sandboxed execution |

**Technology Stack:**

- Docker sandbox
- 50+ tool catalog
- CPU 1 core / 512MB limits

**Business Use Cases:**

- Dispatch member_lookup tool to EligibilityAgent
- Execute tier_calculator for BenefitsAgent
- Sandbox all tool execution (30 sec timeout)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 5ms |

**Implementation & Flow Position:** EligibilityAgent primary consumer via MCP tool calling.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `AgentGateway` | Tool Registry |
| 2 | `EligibilityAgent` | Member Lookup Tool |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `FunctionCallingGateway` | Exec Functions |

**Connection narrative:** receives from `AgentGateway` (Tool Registry); receives from `EligibilityAgent` (Member Lookup Tool); sends to `FunctionCallingGateway` (Exec Functions).

---

### Layer 2 — Integration Gateways

#### `EnterpriseIntGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 4 Tool |
| **Role** | Gateway #16: Enterprise ERP Integration |
| **Architecture Pattern** | Anti-corruption layer for ERP systems |

**Technology Stack:**

- SAP RFC/BAPI
- Oracle PL/SQL
- Salesforce SOQL/Streaming API

**Business Use Cases:**

- Sync PA decisions to SAP claims module
- Update Oracle member enrollment on eligibility change
- Create Salesforce case for HITL review queue

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 25ms |

**Implementation & Flow Position:** FunctionCallingGateway downstream; enterprise back-office integration.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FunctionCallingGateway` | SAP/Oracle |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `FunctionCallingGateway` (SAP/Oracle).

---

#### `SaaSConnectorGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 4 Tool |
| **Role** | Gateway #17: SaaS Communication Platforms |
| **Architecture Pattern** | Webhook adapter pattern |

**Technology Stack:**

- Slack Bot API
- Microsoft Teams Graph API
- Zendesk Ticket API

**Business Use Cases:**

- Send PA decision alerts to provider Slack channels
- Post adaptive cards to Teams for HITL reviewers
- Create Zendesk tickets for complex pended cases

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 15ms |

**Implementation & Flow Position:** NotificationAgent primary consumer for multi-channel dispatch.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `NotificationAgent` | Slack/Teams |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `NotificationAgent` (Slack/Teams).

---

### Layer 2 — Ops Gateways

#### `CostMgmtGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Ops Gateways |
| **Role** | LLM cost tracking |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Custom cost engine

**Business Use Cases:**

- Token cost attribution per agent.

**Implementation & Flow Position:** Component `CostMgmtGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `MonitoringGateway` | $$Track |
| 2 | `BenefitsAgent` | $$ Track |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `TokenMgmtGateway` | Tokens |

**Connection narrative:** receives from `MonitoringGateway` ($$Track); receives from `BenefitsAgent` ($$ Track); sends to `TokenMgmtGateway` (Tokens).

---

#### `MonitoringGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Ops Gateways |
| **Role** | Metrics collection |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Prometheus

**Business Use Cases:**

- Gateway-level metrics.

**Implementation & Flow Position:** Component `MonitoringGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ObservabilityGateway` | Metrics |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `CostMgmtGateway` | $$Track |

**Connection narrative:** receives from `ObservabilityGateway` (Metrics); sends to `CostMgmtGateway` ($$Track).

---

#### `ObservabilityGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 8 Ops |
| **Role** | Gateway #36: Distributed Tracing Hub |
| **Architecture Pattern** | OpenTelemetry collector; trace propagation |

**Technology Stack:**

- Jaeger
- OpenTelemetry
- Trace ID propagation

**Business Use Cases:**

- Propagate trace ID from KongHub through all 17 agents
- Enable ClinicalAgent RAG span visualization
- Feed Grafana dashboards with trace-derived metrics

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** KongHub dashed trace line; all agents emit spans.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | Traces |
| 2 | `IntakeAgent` | Trace Start |
| 3 | `ClinicalAgent` | RAG Spans |
| 4 | `AuditAgent` | Audit Metrics |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `MonitoringGateway` | Metrics |

**Connection narrative:** receives from `KongHub` (Traces); receives from `IntakeAgent` (Trace Start); receives from `ClinicalAgent` (RAG Spans); sends to `MonitoringGateway` (Metrics); + 1 more inbound.

---

### Layer 2 — Workflow Gateways

#### `OrchestrationGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Workflow Gateways |
| **Role** | Durable execution |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Temporal client

**Business Use Cases:**

- Temporal workflow triggers.

**Implementation & Flow Position:** Component `OrchestrationGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Temporal` | Durable Exec |

**Connection narrative:** sends to `Temporal` (Durable Exec).

---

#### `StateManagementGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Workflow Gateways |
| **Role** | State snapshots |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Redis + PostgreSQL

**Business Use Cases:**

- Checkpoint management.

**Implementation & Flow Position:** Component `StateManagementGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `StateManager` | Snapshots |
| 2 | `StateManager` | Snapshot Mgmt |

**Connection narrative:** sends to `StateManager` (Snapshots); sends to `StateManager` (Snapshot Mgmt).

---

#### `WorkflowGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 7 Workflow |
| **Role** | Gateway #31: LangGraph DAG Controller |
| **Architecture Pattern** | Workflow API facade over LangGraph |

**Technology Stack:**

- LangGraph 0.2.15 API
- DAG execution engine
- Conditional branch controller

**Business Use Cases:**

- Start/pause/resume PA workflow DAG
- Trigger COM/Appeals sub-workflows
- Expose workflow status API to ProviderPortalService

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** WorkflowGateway → WorkflowEngine. COMAgent sub-workflow trigger.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `COMAgent` | Sub-workflow |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `WorkflowEngine` | DAG Control |

**Connection narrative:** receives from `COMAgent` (Sub-workflow); sends to `WorkflowEngine` (DAG Control).

---

### Layer 2 — Data Gateways

#### `CacheGW`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Data Gateways |
| **Role** | Cache layer |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Redis

**Business Use Cases:**

- Eligibility cache hits.

**Implementation & Flow Position:** Component `CacheGW` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `EligibilityAgent` | Cache Hit |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `EligibilityAgent` (Cache Hit).

---

#### `DataAccessGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Data Gateways |
| **Role** | Cached DB access |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Redis + PostgreSQL

**Business Use Cases:**

- Token cache, member DB with cache layer.

**Implementation & Flow Position:** Component `DataAccessGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `EligibilityAgent` | Member DB (Cache Hit) |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Redis` | Token Cache |

**Connection narrative:** receives from `EligibilityAgent` (Member DB (Cache Hit)); sends to `Redis` (Token Cache).

---

#### `DataGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Data Gateways |
| **Role** | Event publishing |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Kafka producer

**Business Use Cases:**

- Data layer event pub.

**Implementation & Flow Position:** Component `DataGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `NotificationAgent` | Event Pub |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Kafka` | Data Events |

**Connection narrative:** receives from `NotificationAgent` (Event Pub); sends to `Kafka` (Data Events).

---

#### `DataGovernanceGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Data Gateways |
| **Role** | PII masking |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Microsoft Presidio

**Business Use Cases:**

- PHI de-identification.

**Implementation & Flow Position:** Component `DataGovernanceGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FraudAgent` | PII Mask |
| 2 | `AuditAgent` | Lineage Track |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `FraudAgent` (PII Mask); receives from `AuditAgent` (Lineage Track).

---

### Layer 2 — Memory Gateways

#### `ContextGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 3 Knowledge |
| **Role** | Gateway #11: Session Context Management |
| **Architecture Pattern** | Context stack pattern; session-scoped isolation |

**Technology Stack:**

- Redis 6h TTL
- Context push/pop stack
- PostgreSQL archival

**Business Use Cases:**

- Initialize session context at IntakeAgent start
- Pass extracted fields to downstream agents without re-OCR
- Isolate multi-tenant payer contexts

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 5ms |

**Implementation & Flow Position:** IntakeAgent init; COMAgent multi-context for multi-payer cases.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `IntakeAgent` | Init Context |
| 2 | `COMAgent` | Multi-Context |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Redis` | Session Context |

**Connection narrative:** receives from `IntakeAgent` (Init Context); receives from `COMAgent` (Multi-Context); sends to `Redis` (Session Context).

---

#### `MemoryGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 3 Knowledge |
| **Role** | Gateway #12: Memory Router |
| **Architecture Pattern** | Tiered memory router; episodic + semantic + working |

**Technology Stack:**

- Redis working memory
- PostgreSQL episodic
- Milvus semantic vectors

**Business Use Cases:**

- Route EligibilityAgent to episodic memory (repeat member lookup)
- Route ClinicalAgent to semantic memory (similar cases)
- Store DecisionAgent final decision in working memory

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 8ms |

**Implementation & Flow Position:** Bridges agents to WorkingMemory/EpisodicMemory/SemanticMemory services.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `EligibilityAgent` | Episode Recall |
| 2 | `ClinicalAgent` | Semantic Memory |
| 3 | `DecisionAgent` | Store Decision |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Redis` | Working Memory |

**Connection narrative:** receives from `EligibilityAgent` (Episode Recall); receives from `ClinicalAgent` (Semantic Memory); receives from `DecisionAgent` (Store Decision); sends to `Redis` (Working Memory).

---

### Layer 2 — RAG Gateways

#### `KnowledgeGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 3 Knowledge |
| **Role** | Gateway #10: Semantic Knowledge Layer |
| **Architecture Pattern** | Knowledge graph facade; ontology-driven queries |

**Technology Stack:**

- Neo4j 500K nodes
- Disease/drug/procedure ontology
- Cypher path finding

**Business Use Cases:**

- Query plan ontology for BenefitsAgent tier determination
- Traverse drug interaction graphs for ClinicalAgent safety checks
- Fraud pattern graph queries for FraudAgent

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 20ms |

**Implementation & Flow Position:** BenefitsAgent, ClinicalAgent, FraudAgent all consume KnowledgeGateway.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BenefitsAgent` | Plan Ontology |
| 2 | `ClinicalAgent` | Neo4j Cypher |
| 3 | `FraudAgent` | Fraud Patterns |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `BenefitsAgent` (Plan Ontology); receives from `ClinicalAgent` (Neo4j Cypher); receives from `FraudAgent` (Fraud Patterns).

---

#### `RAGGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 3 Knowledge |
| **Role** | Gateway #9: Retrieval Orchestration |
| **Architecture Pattern** | Hybrid RAG orchestrator; parallel retrieval + RRF fusion |

**Technology Stack:**

- Milvus HNSW
- Elasticsearch BM25
- Neo4j Cypher
- RRF k=60 fusion

**Business Use Cases:**

- Orchestrate 20 parallel retrieval queries for ClinicalAgent
- Fuse vector + keyword + graph results into top-10 context
- Cache frequent guideline queries (40% hit rate)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 45ms |

**Implementation & Flow Position:** ClinicalAgent primary consumer; bottleneck is LLM inference not RAG (45ms vs 472 sec).

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ClinicalAgent` | Hybrid Retrieval (45ms) |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `ClinicalAgent` (Hybrid Retrieval (45ms)).

---

#### `VectorDBGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 3 Knowledge |
| **Role** | Gateway #13: Vector DB Proxy |
| **Architecture Pattern** | Vector DB abstraction; multi-backend support |

**Technology Stack:**

- Milvus 2.3 primary
- 1024-dim BGE-large embeddings
- HNSW M=16 index

**Business Use Cases:**

- Proxy vector similarity search for ClinicalAgent (10M embeddings)
- Support Pinecone/Weaviate/Qdrant as failover backends
- Batch embedding queries for RAG efficiency

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 50ms |

**Implementation & Flow Position:** ClinicalAgent → VectorDBGateway → Milvus. Also SemanticMemory backend.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ClinicalAgent` | Milvus Search |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `ClinicalAgent` (Milvus Search).

---

### Layer 2 — Policy Gateways

#### `PolicyGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 6 Governance |
| **Role** | Gateway #28: OPA/Drools Rule Engine |
| **Architecture Pattern** | Policy-as-code; declarative rule evaluation |

**Technology Stack:**

- Open Policy Agent (Rego)
- Drools BRMS
- 50+ decision trees

**Business Use Cases:**

- Evaluate 50+ OPA rules for PolicyAgent in <100ms
- Execute BenefitsAgent tier decision trees
- Version-controlled Git-based rule deployment

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 10ms |

**Implementation & Flow Position:** PolicyAgent and BenefitsAgent primary consumers.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BenefitsAgent` | Rule Evaluation |
| 2 | `PolicyAgent` | OPA/Drools |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `BenefitsAgent` (Rule Evaluation); receives from `PolicyAgent` (OPA/Drools).

---

### Layer 2 — Prompt Gateways

#### `EvaluationGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Prompt Gateways |
| **Role** | Quality metrics |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- LangSmith eval

**Business Use Cases:**

- Agent output quality tracking.

**Implementation & Flow Position:** Component `EvaluationGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `PolicyAgent` | Quality Metrics |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `PolicyAgent` (Quality Metrics).

---

#### `PromptGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Prompt Gateways |
| **Role** | Prompt A/B testing |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- LangSmith

**Business Use Cases:**

- 5 prompt variants per agent.

**Implementation & Flow Position:** Component `PromptGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `PolicyAgent` | LangSmith A/B |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `PolicyAgent` (LangSmith A/B).

---

### Layer 2 — HITL Gateways

#### `ApprovalGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — HITL Gateways |
| **Role** | Approval workflow |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Temporal

**Business Use Cases:**

- Triggers human approval sub-workflow.

**Implementation & Flow Position:** Component `ApprovalGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DecisionAgent` | Workflow Trigger |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `DecisionAgent` (Workflow Trigger).

---

#### `HITLGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 7 Workflow |
| **Role** | Gateway #33: Human-in-the-Loop Router |
| **Architecture Pattern** | Rules-based human routing; priority queue assignment |

**Technology Stack:**

- Drools routing rules
- Priority queue (fraud > denial > low confidence)
- 28% case routing

**Business Use Cases:**

- Route 28% of cases (14K/day) to human review queue
- Prioritize fraud cases over low-confidence cases
- Assign to specialty-matched reviewer pool

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 5ms |

**Implementation & Flow Position:** DecisionAgent → HITLGateway → ReviewQueue or NotificationAgent.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DecisionAgent` | Route (28% Human) |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `DecisionAgent` (Route (28% Human)).

---

### Layer 2 — Document Gateways

#### `DocumentGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Tier 9 Data |
| **Role** | Gateway #45: Document OCR Processing |
| **Architecture Pattern** | OCR pipeline adapter |

**Technology Stack:**

- Azure Form Recognizer
- PDF/DICOM/TIFF support
- Handwriting recognition

**Business Use Cases:**

- Extract structured fields from PA form images for IntakeAgent
- Support 15 form templates with 98.5% accuracy
- Pre-process fax scans before GPT-4o Vision

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 50ms |

**Implementation & Flow Position:** IntakeAgent → DocumentGateway for OCR before LLM classification.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `IntakeAgent` | OCR Extract |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `IntakeAgent` (OCR Extract).

---

### Layer 2 — Governance Gateways

#### `AgentGovernanceGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Governance Gateways |
| **Role** | Permission check |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- RBAC

**Business Use Cases:**

- DecisionAgent permission validation.

**Implementation & Flow Position:** Component `AgentGovernanceGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DecisionAgent` | Permission Check |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `DecisionAgent` (Permission Check).

---

#### `AgentRegistryGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Governance Gateways |
| **Role** | Agent config |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL registry

**Business Use Cases:**

- Agent version and config loading.

**Implementation & Flow Position:** Component `AgentRegistryGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `IntakeAgent` | Agent Config |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `IntakeAgent` (Agent Config).

---

### Layer 2 — Risk Gateways

#### `RiskMgmtGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Risk Gateways |
| **Role** | Anomaly detection |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Custom ML

**Business Use Cases:**

- Fraud risk scoring algorithms.

**Implementation & Flow Position:** Component `RiskMgmtGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FraudAgent` | Anomaly Detection |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `FraudAgent` (Anomaly Detection).

---

### Layer 2 — Analytics Gateways

#### `UsageAnalyticsGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Analytics Gateways |
| **Role** | Behavior tracking |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Segment

**Business Use Cases:**

- User behavior analytics.

**Implementation & Flow Position:** Component `UsageAnalyticsGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `NotificationAgent` | Behavior Track |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `NotificationAgent` (Behavior Track).

---

### Layer 3 — Orchestration

*LangGraph DAG + Temporal durable execution. Pattern: **Supervisor Multi-Agent + Event Sourcing**.*

#### `StateManager`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 3 — Orchestration |
| **Role** | Workflow State Persistence |
| **Architecture Pattern** | Hot-cold tiering: Redis working memory (6h TTL) + PostgreSQL cold snapshots (90d) |

**Technology Stack:**

- Redis 7 Cluster (3 shards)
- PostgreSQL 15 JSONB
- Checkpoint every 30s
- PostgresSaver

**Business Use Cases:**

- Resume PA workflow from last checkpoint after failure (RPO 1 min, RTO 5 min)
- Store per-agent outputs and confidence scores for DecisionAgent aggregation
- Track workflow progress (4/7 agents complete = 57%) for portal status display
- Immutable checkpoint trail for CMS/state regulatory audit

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Ops Per Day | 500M |
| P50 Latency | <5ms |
| Checkpoint Interval | 30 sec |

**Implementation & Flow Position:** StateManagementGateway routes snapshots. Redis hot store 5 min; PostgreSQL cold store 90 days.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `StateManagementGateway` | Snapshots |
| 2 | `WorkflowEngine` | Checkpoint |
| 3 | `StateManagementGateway` | Snapshot Mgmt |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Redis` | Hot Store (5min) |
| 2 | `PostgreSQL` | Cold Store (90d) |

**Connection narrative:** receives from `StateManagementGateway` (Snapshots); receives from `WorkflowEngine` (Checkpoint); receives from `StateManagementGateway` (Snapshot Mgmt); sends to `Redis` (Hot Store (5min)); sends to `PostgreSQL` (Cold Store (90d)).

---

#### `Temporal`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 3 — Orchestration |
| **Role** | Durable Workflow Execution Engine |
| **Architecture Pattern** | Event sourcing + durable execution; workflow survives worker crashes; HITL pause/resume |

**Technology Stack:**

- Temporal.io 1.22
- TypeScript/Python workers
- PostgreSQL event store
- 100-worker task queue

**Business Use Cases:**

- Guarantee PA workflow completes even if ClinicalAgent worker crashes mid-8-min inference
- Pause workflow at HITL gate until human reviewer acts (hours/days)
- Auto-retry failed activities with exponential backoff (3 attempts)
- 90-day workflow history for regulatory audit and appeal reconstruction

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Retention | 90 days |
| Events Per Workflow | ~150 |
| Retry Success | 95% within 3 attempts |

**Implementation & Flow Position:** 11 Temporal activities map 1:1 to agents. OrchestrationGateway triggers durable runs.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `OrchestrationGateway` | Durable Exec |
| 2 | `WorkflowEngine` | Persist State |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Event History |

**Connection narrative:** receives from `OrchestrationGateway` (Durable Exec); receives from `WorkflowEngine` (Persist State); sends to `PostgreSQL` (Event History).

---

#### `WorkflowEngine`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 3 — Orchestration |
| **Role** | LangGraph Supervisor Workflow Engine |
| **Architecture Pattern** | Supervisor Multi-Agent DAG; 11-node graph with 8 conditional routing points; parallel Benefits+Fraud |

**Technology Stack:**

- LangGraph 0.2.15
- Python 3.11
- PostgresSaver checkpointing
- Redis state
- Kafka events

**Business Use Cases:**

- Orchestrate end-to-end PA pipeline: Intake → Eligibility → Benefits → Clinical → Policy → Fraud → Decision
- Conditional auto-deny on inactive eligibility; auto-approve when no PA required
- Parallel execution: Benefits + Fraud concurrent (20% time savings)
- Interrupt-before-decision for HITL gate (28% human review cases)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Daily Workflows | 50K |
| P50 Latency | 4.2 min |
| P95 | 12.8 min |
| Sla Compliance | 99.2% |

**Implementation & Flow Position:** Triggered by SecurityGateway (step ②). Persists to Temporal + StateManager. Publishes Kafka lifecycle events.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `SecurityGateway` | ② Token Valid (OAuth2) |
| 2 | `TokenMgmtGateway` | Quota OK (100/min) |
| 3 | `LiteLLMRouter` | Model Response |
| 4 | `AIFirewallGateway` | Security OK (Lakera) |
| 5 | `WorkflowGateway` | DAG Control |
| 6 | `Prometheus` | Metrics |
| 7 | `Jaeger` | Traces |
| 8 | `FHIRGateway` | Trigger PA |
| 9 | `X12Gateway` | Trigger PA |
| 10 | `SLAMonitorService` | Track SLA |
| 11 | `MultiTenantService` | Payer Config |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Temporal` | Persist State |
| 2 | `StateManager` | Checkpoint |
| 3 | `Kafka` | Event Stream |
| 4 | `IntakeAgent` | ③ Intake |
| 5 | `ExpeditedAgent` | Urgent Route |
| 6 | `RetrospectiveAgent` | Post-Service |

**Connection narrative:** receives from `SecurityGateway` (② Token Valid (OAuth2)); receives from `TokenMgmtGateway` (Quota OK (100/min)); receives from `LiteLLMRouter` (Model Response); sends to `Temporal` (Persist State); sends to `StateManager` (Checkpoint); sends to `Kafka` (Event Stream); + 8 more inbound; + 3 more outbound.

---

### Layer 4 — AI Agents (#1)

#### `IntakeAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#1) |
| **Role** | Document Processing & Classification Agent |
| **Architecture Pattern** | Vision-Language Agent; tool-calling via MCP (DocumentGateway, ContextGateway); schema-validated JSON output |

**Technology Stack:**

- GPT-4o Vision (gpt-4o-2024-05-13)
- Azure Form Recognizer
- LangSmith prompts
- JSON Schema validation

**Business Use Cases:**

- OCR and classify 15 PA form types (UB-04, CMS-1500, HCFA, custom payer forms)
- Extract patient, provider, diagnosis (ICD-10), procedure (CPT) fields with 97% accuracy
- Flag low-confidence extractions (<0.85) for HITL document review (12% of cases)
- Trigger RegistryAgent de-duplication before eligibility check

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency Avg | 2 min |
| Tokens In Out | 15K/2K |
| Cost | $0.285/exec |
| Accuracy | 97% |

**Implementation & Flow Position:** WorkflowEngine step ③. Calls DocumentGateway, BlobStorage, PostgreSQL, RegistryAgent, LiteLLMRouter.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `WorkflowEngine` | ③ Intake |
| 2 | `AgentRegistry` | Agent Config |
| 3 | `MCPRegistry` | Tools |
| 4 | `WorkingMemory` | Context |
| 5 | `Jaeger` | Agent Spans |
| 6 | `ePAService` | Transform PA |
| 7 | `CodeValidationService` | ICD/CPT Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `EligibilityAgent` | ④ Eligibility |
| 2 | `LiteLLMGW` | GPT-4o Vision |
| 3 | `BlobStorage` | Store PDF |
| 4 | `PostgreSQL` | Metadata |
| 5 | `LiteLLMRouter` | GPT-4o Vision (47K tokens) |
| 6 | `DocumentGateway` | OCR Extract |
| 7 | `AgentRegistryGateway` | Agent Config |
| 8 | `ContextGateway` | Init Context |
| 9 | `ObservabilityGateway` | Trace Start |
| 10 | `RegistryAgent` | De-dup Check |

**Connection narrative:** receives from `WorkflowEngine` (③ Intake); receives from `AgentRegistry` (Agent Config); receives from `MCPRegistry` (Tools); sends to `EligibilityAgent` (④ Eligibility); sends to `LiteLLMGW` (GPT-4o Vision); sends to `BlobStorage` (Store PDF); + 4 more inbound; + 7 more outbound.

---

### Layer 4 — AI Agents (#2)

#### `EligibilityAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#2) |
| **Role** | Member Eligibility Verification Agent |
| **Architecture Pattern** | Tool-augmented LLM; cache-first lookup (Redis 85% hit); rule-based validation with GPT-3.5 explanation |

**Technology Stack:**

- GPT-3.5 Turbo
- MemberService gRPC
- Redis cache-aside
- MCP member_lookup tool

**Business Use Cases:**

- Verify member ID exists and plan is active on service date
- Auto-deny inactive/termed members with structured denial reason
- Detect duplicate PA requests within 30-day window
- Confirm provider in-network status before benefits calculation

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 15 sec |
| Cache Hit | 85% |
| Accuracy | 99% |
| Cost | $0.003/exec |

**Implementation & Flow Position:** WorkflowEngine step ④. ToolGateway → MemberService. DataAccessGateway with Redis cache layer.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `IntakeAgent` | ④ Eligibility |
| 2 | `ToolExecutor` | Execute |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `BenefitsAgent` | ⑤ Benefits |
| 2 | `LiteLLMGW` | GPT-3.5 |
| 3 | `MemberService` | Member Lookup |
| 4 | `CacheGW` | Cache Hit |
| 5 | `LiteLLMRouter` | GPT-3.5 Turbo |
| 6 | `ToolGateway` | Member Lookup Tool |
| 7 | `DataAccessGateway` | Member DB (Cache Hit) |
| 8 | `MemoryGateway` | Episode Recall |
| 9 | `TokenMgmtGateway` | Token Count |

**Connection narrative:** receives from `IntakeAgent` (④ Eligibility); receives from `ToolExecutor` (Execute); sends to `BenefitsAgent` (⑤ Benefits); sends to `LiteLLMGW` (GPT-3.5); sends to `MemberService` (Member Lookup); + 6 more outbound.

---

### Layer 4 — AI Agents (#3)

#### `BenefitsAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#3) |
| **Role** | Benefit Tier & Network Validation Agent |
| **Architecture Pattern** | LLM + rules hybrid; OPA decision trees (12 trees) + FunctionCallingGateway tier calculator |

**Technology Stack:**

- GPT-4o
- OPA/Rego
- Neo4j plan ontology
- BenefitsConfigService
- NetworkService
- FormularyService

**Business Use Cases:**

- Determine if PA is required for requested service (auto-approve if not required)
- Calculate cost share: copay, coinsurance, deductible remaining
- Validate in-network vs out-of-network tier (affects approval criteria)
- Route drug PAs to StepTherapyAgent for protocol validation

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 20 sec |
| Decision Trees | 12 |
| Tier Accuracy | 95% |
| Cost | $0.300/exec |

**Implementation & Flow Position:** WorkflowEngine step ⑤. Parallel with FraudAgent possible. Triggers StepTherapyAgent for pharmacy PAs.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `EligibilityAgent` | ⑤ Benefits |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ClinicalAgent` | ⑥ Clinical |
| 2 | `LiteLLMGW` | GPT-4o |
| 3 | `PolicyService` | Policy Lookup |
| 4 | `BenefitsConfigService` | Tier Matching |
| 5 | `NetworkService` | Network Check |
| 6 | `LiteLLMRouter` | GPT-4o |
| 7 | `PolicyGateway` | Rule Evaluation |
| 8 | `FunctionCallingGateway` | Tier Calc |
| 9 | `KnowledgeGateway` | Plan Ontology |
| 10 | `CostMgmtGateway` | $$ Track |
| 11 | `StepTherapyAgent` | Drug PA |

**Connection narrative:** receives from `EligibilityAgent` (⑤ Benefits); sends to `ClinicalAgent` (⑥ Clinical); sends to `LiteLLMGW` (GPT-4o); sends to `PolicyService` (Policy Lookup); + 8 more outbound.

---

### Layer 4 — AI Agents (#4) ★ BOTTLENECK

*ClinicalAgent consumes 53% of pipeline time (8 min). Pattern: **RAG-Augmented LLM + Chain-of-Thought**.*

#### `ClinicalAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#4) ★ BOTTLENECK |
| **Role** | Medical Necessity Review Agent |
| **Architecture Pattern** | RAG-augmented LLM (Retrieval-Augmented Generation); hybrid search + graph RAG + episodic memory; chain-of-thought reasoning |

**Technology Stack:**

- GPT-4o
- Milvus HNSW (10M embeddings)
- Elasticsearch BM25
- Neo4j GraphRAG
- RRF k=60
- Guardrails AI
- text-embedding-3-large

**Business Use Cases:**

- Evaluate medical necessity against MCG, InterQual, CMS LCD/NCD, specialty society guidelines
- Determine if conservative therapy was attempted (step therapy clinical criteria)
- Generate explainable decision with guideline citations (96% accuracy, 4% overturn rate)
- Trigger DocRequestAgent when clinical documentation insufficient (25% pend rate)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency Avg | 8 min (53% of pipeline) |
| Rag Queries | 20/case |
| Llm Inference | 98.4% of time |
| Accuracy | 96% |
| Cost | $0.780/exec |

**Implementation & Flow Position:** WorkflowEngine step ⑥. RAGGateway + VectorSearch/HybridSearch/GraphRAG → RRF → ClinicalContentService → LiteLLMRouter.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BenefitsAgent` | ⑥ Clinical |
| 2 | `SafetyEval` | Validate |
| 3 | `SemanticMemory` | Knowledge |
| 4 | `Jaeger` | RAG Spans |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PolicyAgent` | ⑦ Policy |
| 2 | `LiteLLMRouter` | GPT-4o + RAG (8 min) |
| 3 | `RAGGateway` | Hybrid Retrieval (45ms) |
| 4 | `VectorDBGateway` | Milvus Search |
| 5 | `KnowledgeGateway` | Neo4j Cypher |
| 6 | `MemoryGateway` | Semantic Memory |
| 7 | `GuardrailGateway` | Hallucination Check |
| 8 | `ObservabilityGateway` | RAG Spans |
| 9 | `VectorSearch` | Semantic Search |
| 10 | `HybridSearch` | Keyword Search |
| 11 | `GraphRAG` | Relationship Query |
| 12 | `DocRequestAgent` | Pend Trigger |

**Connection narrative:** receives from `BenefitsAgent` (⑥ Clinical); receives from `SafetyEval` (Validate); receives from `SemanticMemory` (Knowledge); sends to `PolicyAgent` (⑦ Policy); sends to `LiteLLMRouter` (GPT-4o + RAG (8 min)); sends to `RAGGateway` (Hybrid Retrieval (45ms)); + 1 more inbound; + 9 more outbound.

---

### Layer 4 — AI Agents (#5)

#### `PolicyAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#5) |
| **Role** | Regulatory Compliance & Policy Rules Agent |
| **Architecture Pattern** | LLM policy interpreter + deterministic OPA engine; Claude 3.5 for 200K context policy documents |

**Technology Stack:**

- Claude 3.5 Sonnet
- OPA Rego (50+ rules)
- Drools
- PolicyService
- StateMandateService
- LangSmith A/B

**Business Use Cases:**

- Evaluate 6 policy types: medical, drug, administrative, regulatory, contract, internal
- Enforce HIPAA/SOC2/NCQA compliance before approval
- Apply 50-state mandate variations via StateMandateService
- Auto-deny on policy violation with citeable regulatory reference

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 2.5 min |
| Rules Evaluated | 50+ |
| Accuracy | 94% |
| Cost | $0.111/exec |

**Implementation & Flow Position:** WorkflowEngine step ⑦. PolicyGateway OPA evaluation <100ms. PromptMgmt supplies versioned templates.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ClinicalAgent` | ⑦ Policy |
| 2 | `PromptMgmt` | Prompt |
| 3 | `StateMandateService` | State Rules |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `FraudAgent` | ⑧ Fraud Check |
| 2 | `LiteLLMGW` | Claude 3.5 |
| 3 | `PolicyService` | Rule Lookup |
| 4 | `LiteLLMRouter` | Claude 3.5 Sonnet |
| 5 | `PolicyGateway` | OPA/Drools |
| 6 | `ComplianceGateway` | HIPAA Check |
| 7 | `PromptGateway` | LangSmith A/B |
| 8 | `EvaluationGateway` | Quality Metrics |
| 9 | `PolicyService` | — |

**Connection narrative:** receives from `ClinicalAgent` (⑦ Policy); receives from `PromptMgmt` (Prompt); receives from `StateMandateService` (State Rules); sends to `FraudAgent` (⑧ Fraud Check); sends to `LiteLLMGW` (Claude 3.5); sends to `PolicyService` (Rule Lookup); + 6 more outbound.

---

### Layer 4 — AI Agents (#6)

#### `FraudAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#6) |
| **Role** | Fraud Detection & Risk Scoring Agent |
| **Architecture Pattern** | Graph Neural Network (GNN) + LLM explanation; Neo4j pattern matching; GPU-accelerated inference |

**Technology Stack:**

- PyTorch Geometric GNN
- Neo4j 500K nodes
- NVIDIA T4 GPU
- ClaimsService
- RiskMgmtGateway
- SHAP explainability

**Business Use Cases:**

- Detect upcoding, unbundling, duplicate billing, kickback referral patterns
- Score fraud risk 0-100; >60 triggers mandatory HITL investigation
- Identify provider billing outliers (>3x peer average volume)
- Graph community detection for suspicious provider clusters

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 45 sec |
| Precision | 94% |
| Recall | 98% |
| F1 | 0.96 |
| Hitl Trigger | risk >60 |

**Implementation & Flow Position:** Can run parallel with BenefitsAgent. GPUGateway accelerates GNN. EpisodicMemory for historical patterns.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `PolicyAgent` | ⑧ Fraud Check |
| 2 | `EpisodicMemory` | History |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `DecisionAgent` | ⑨ Decision |
| 2 | `LiteLLMGW` | ML Scoring |
| 3 | `Neo4j` | Graph Patterns |
| 4 | `ClaimsService` | Claim History |
| 5 | `LiteLLMRouter` | Custom ML Model |
| 6 | `GPUGateway` | GPU Acceleration |
| 7 | `KnowledgeGateway` | Fraud Patterns |
| 8 | `RiskMgmtGateway` | Anomaly Detection |
| 9 | `DataGovernanceGateway` | PII Mask |
| 10 | `Neo4j` | — |

**Connection narrative:** receives from `PolicyAgent` (⑧ Fraud Check); receives from `EpisodicMemory` (History); sends to `DecisionAgent` (⑨ Decision); sends to `LiteLLMGW` (ML Scoring); sends to `Neo4j` (Graph Patterns); + 7 more outbound.

---

### Layer 4 — AI Agents (#7)

#### `DecisionAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#7) |
| **Role** | Final Decision Aggregation & HITL Routing Agent |
| **Architecture Pattern** | Aggregator agent with weighted confidence scoring; Drools HITL routing rules; interrupt-before pattern |

**Technology Stack:**

- GPT-4o
- Drools rules engine
- HITLGateway
- ApprovalGateway
- WorkingMemory
- QualityMeasureService

**Business Use Cases:**

- Aggregate confidence from all agents (Clinical 50%, Policy 30%, Fraud 20% weight)
- Auto-approve 72% of cases (confidence ≥0.85, fraud risk <30)
- Route 28% to HITL: low confidence, high fraud, all denials, high cost (>$50K)
- Capture HEDIS/Stars quality measures for NCQA reporting

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 30 sec |
| Auto Approve | 72% |
| Hitl Rate | 28% |
| Overturn Rate | 3% |
| Cost | $0.270/exec |

**Implementation & Flow Position:** WorkflowEngine step ⑨→⑩. HITLRouting branches to ReviewQueue (28%) or NotificationAgent (72%).

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FraudAgent` | ⑨ Decision |
| 2 | `QualityMeasureService` | HEDIS Track |
| 3 | `RootCauseService` | Denial Pattern |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMGW` | GPT-4o |
| 2 | `WorkingMemory` | Final Decision |
| 3 | `LiteLLMRouter` | GPT-4o Decision |
| 4 | `HITLGateway` | Route (28% Human) |
| 5 | `ApprovalGateway` | Workflow Trigger |
| 6 | `AgentGovernanceGateway` | Permission Check |
| 7 | `MemoryGateway` | Store Decision |
| 8 | `HITLRouting` | ⑩ Risk Assessment |
| 9 | `HITLRouting` | ⑩ Risk Assessment |
| 10 | `MedDirectorAgent` | P2P Request |

**Connection narrative:** receives from `FraudAgent` (⑨ Decision); receives from `QualityMeasureService` (HEDIS Track); receives from `RootCauseService` (Denial Pattern); sends to `LiteLLMGW` (GPT-4o); sends to `WorkingMemory` (Final Decision); sends to `LiteLLMRouter` (GPT-4o Decision); + 7 more outbound.

---

### Layer 4 — AI Agents (#8)

#### `NotificationAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#8) |
| **Role** | Multi-Channel Notification Agent |
| **Architecture Pattern** | Event-driven notification; channel selection via CommPreferenceService; async fire-and-forget |

**Technology Stack:**

- GPT-3.5 (message personalization)
- Kafka producer
- Slack/Teams webhooks
- SMS/Email APIs
- DLPService PHI scan

**Business Use Cases:**

- Send PA decision to provider and member (approve/deny/pend letters)
- Personalize notification tone per audience (clinical vs member-friendly language)
- Respect member communication preferences (email, SMS, portal, fax)
- Alert providers on DocRequestAgent pend requests within 15 minutes

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 1 min |
| Channels | Portal/Email/SMS/Slack |
| Delivery Rate | 99.5% |

**Implementation & Flow Position:** Async after DecisionAgent. SaaSConnectorGateway for Slack/Teams. DLPService scans outbound PHI.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `HITLRouting` | 72% Auto-Approve (36K/day) |
| 2 | `Kafka` | Consume |
| 3 | `DocRequestAgent` | Provider Alert |
| 4 | `DLPService` | PHI Scan |
| 5 | `CommPreferenceService` | Channel Select |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMGW` | GPT-3.5 |
| 2 | `Kafka` | Events |
| 3 | `LiteLLMRouter` | GPT-3.5 |
| 4 | `SaaSConnectorGateway` | Slack/Teams |
| 5 | `DataGateway` | Event Pub |
| 6 | `UsageAnalyticsGateway` | Behavior Track |

**Connection narrative:** receives from `HITLRouting` (72% Auto-Approve (36K/day)); receives from `Kafka` (Consume); receives from `DocRequestAgent` (Provider Alert); sends to `LiteLLMGW` (GPT-3.5); sends to `Kafka` (Events); sends to `LiteLLMRouter` (GPT-3.5); + 2 more inbound; + 3 more outbound.

---

### Layer 4 — AI Agents (#9)

#### `AuditAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#9) |
| **Role** | Compliance Audit Logging Agent |
| **Architecture Pattern** | Append-only audit pipeline; 100% coverage; async parallel with notification |

**Technology Stack:**

- GPT-4o (log summarization)
- PostgreSQL WORM tables
- Elasticsearch audit index
- AuditGateway immutable log

**Business Use Cases:**

- Log every agent input/output for HIPAA 6-year retention
- Create forensic trail for CMS/state regulatory audits
- Index audit events in Elasticsearch for RootCauseService analysis
- Generate compliance reports for SOC2/NCQA audits

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Coverage | 100% |
| Retention | 7 years |
| Index Latency | <15ms |

**Implementation & Flow Position:** Always executes async. ApprovalWorkflow triggers AuditAgent on human decisions.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ApprovalWorkflow` | Log |
| 2 | `DLPService` | Log Scan |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMGW` | GPT-4o Log |
| 2 | `PostgreSQL` | Compliance |
| 3 | `Elasticsearch` | Audit Index |
| 4 | `LiteLLMRouter` | GPT-4o Logging |
| 5 | `AuditGateway` | Immutable Log |
| 6 | `ComplianceGateway` | HIPAA/SOC2 |
| 7 | `DataGovernanceGateway` | Lineage Track |
| 8 | `ObservabilityGateway` | Audit Metrics |

**Connection narrative:** receives from `ApprovalWorkflow` (Log); receives from `DLPService` (Log Scan); sends to `LiteLLMGW` (GPT-4o Log); sends to `PostgreSQL` (Compliance); sends to `Elasticsearch` (Audit Index); + 5 more outbound.

---

### Layer 4 — AI Agents (#10)

#### `AppealsAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#10) |
| **Role** | Appeal Re-Evaluation Agent |
| **Architecture Pattern** | Conditional workflow branch; re-runs Clinical+Policy with new evidence; IRO escalation path |

**Technology Stack:**

- Claude 3.5 Sonnet
- RAG (new evidence)
- GrievanceTrackService
- Temporal sub-workflow

**Business Use Cases:**

- Re-evaluate denied PAs when provider submits new clinical evidence (2% of denials)
- Compare original vs new evidence; document changed criteria met
- Track appeal timeline per CMS 60-day requirement (GrievanceTrackService)
- Escalate to Independent Review Organization (IRO) if internal appeal denied

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 10 min |
| Appeal Volume | 1K/day |
| Overturn Rate | 35% |

**Implementation & Flow Position:** Conditional node in LangGraph DAG. Triggered on APPEALED state transition.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `GrievanceTrackService` | Appeal Track |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `GrievanceTrackService` (Appeal Track).

---

### Layer 4 — AI Agents (#11)

#### `COMAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — AI Agents (#11) |
| **Role** | Coordination of Benefits Agent |
| **Architecture Pattern** | Multi-payer sub-workflow; A2A agent messaging; async parallel branch |

**Technology Stack:**

- GPT-4o
- A2AGateway
- ProviderService
- WorkflowGateway sub-workflow
- Kafka COB events

**Business Use Cases:**

- Determine primary vs secondary payer when member has multiple coverage
- Coordinate PA decisions across Medicare/Medicaid/commercial payers
- Prevent duplicate payment across payer systems
- Apply COB rules per NAIC model regulation

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | async |
| Multi Payer Cases | 8% of volume |

**Implementation & Flow Position:** Conditional COMNode in DAG. A2AGateway for inter-agent coordination. Kafka COB events.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | GPT-4o COB |
| 2 | `ProviderService` | Network Lookup |
| 3 | `Kafka` | COB Events |
| 4 | `LiteLLMRouter` | GPT-4o COB |
| 5 | `A2AGateway` | Agent-to-Agent |
| 6 | `WorkflowGateway` | Sub-workflow |
| 7 | `ContextGateway` | Multi-Context |

**Connection narrative:** sends to `LiteLLMRouter` (GPT-4o COB); sends to `ProviderService` (Network Lookup); sends to `Kafka` (COB Events); + 4 more outbound.

---

### Layer 4 — PA Agents (#12)

#### `ExpeditedAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — PA Agents (#12) |
| **Role** | Urgent/Expedited PA Fast-Track Agent |
| **Architecture Pattern** | Priority queue + parallel agent execution; regulatory SLA enforcement (42 CFR 438.210) |

**Technology Stack:**

- GPT-4o Priority queue
- SLAMonitorService 72hr tracker
- Parallel LangGraph fan-out

**Business Use Cases:**

- Process CMS-mandated urgent PA within 72 hours (7,500/day, 15% volume)
- Detect urgent keywords: emergency, stat, life-threatening at intake
- Run all agents in parallel (save 10 min vs sequential)
- 24/7 on-call medical director escalation at 24-hour mark

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Sla | 72 hr regulatory |
| P50 | 1.5 hr |
| Auto Approve | 85% |
| Premium Cost | $0.92/request |

**Implementation & Flow Position:** WorkflowEngine urgent route. SLAMonitorService tracks deadline. Lower denial threshold vs standard.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `WorkflowEngine` | Urgent Route |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | GPT-4o Priority |
| 2 | `SLAMonitorService` | 72hr Track |

**Connection narrative:** receives from `WorkflowEngine` (Urgent Route); sends to `LiteLLMRouter` (GPT-4o Priority); sends to `SLAMonitorService` (72hr Track).

---

### Layer 4 — PA Agents (#13)

#### `StepTherapyAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — PA Agents (#13) |
| **Role** | Step Therapy Protocol Validation Agent |
| **Architecture Pattern** | Rules-first (OPA) + LLM for exception documentation; claims history lookup |

**Technology Stack:**

- GPT-4o + OPA
- ClaimsService NDC lookup
- DrugReferenceService
- FormularyService
- NCPDP SCRIPT

**Business Use Cases:**

- Validate member tried required lower-tier drugs before approving specialty Rx (20K drug PAs/day)
- Check 12-month claims history for prior NDC fills (30/60-day supply rules)
- Auto-approve exceptions: allergy, contraindication, prior trial documented
- Deny with step guidance when protocol not met (35% denial rate)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 30 sec |
| Accuracy | 96% |
| Cost Savings | $4.2M/month generic utilization |

**Implementation & Flow Position:** Triggered by BenefitsAgent on drug PA. ClaimsService + DrugReferenceService for NDC history.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BenefitsAgent` | Drug PA |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | GPT-4o |
| 2 | `ClaimsService` | Prior Fills |
| 3 | `DrugReferenceService` | NDC Lookup |

**Connection narrative:** receives from `BenefitsAgent` (Drug PA); sends to `LiteLLMRouter` (GPT-4o); sends to `ClaimsService` (Prior Fills); sends to `DrugReferenceService` (NDC Lookup).

---

### Layer 4 — PA Agents (#14)

#### `MedDirectorAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — PA Agents (#14) |
| **Role** | Medical Director Peer-to-Peer Agent |
| **Architecture Pattern** | Async human-in-loop coordinator; clinical summary generation + Calendly scheduling |

**Technology Stack:**

- GPT-4o summary
- Calendly API
- Microsoft Teams
- ProviderPortalService
- RAG similar cases

**Business Use Cases:**

- Generate 1-page clinical summary for medical director before P2P call (1,400/day)
- Match provider specialty to board-certified medical director
- Schedule P2P within 48 hours (95% success rate)
- Track overturn/upheld/partial outcomes; feed learning loop to ClinicalAgent

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Overturn Rate | 40% |
| Scheduling Success | 95% |
| Md Prep Savings | 15 min/call |

**Implementation & Flow Position:** DecisionAgent denial + provider P2P request. ProviderPortalService for scheduling.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DecisionAgent` | P2P Request |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | GPT-4o Summary |
| 2 | `ProviderPortalService` | Schedule P2P |

**Connection narrative:** receives from `DecisionAgent` (P2P Request); sends to `LiteLLMRouter` (GPT-4o Summary); sends to `ProviderPortalService` (Schedule P2P).

---

### Layer 4 — PA Agents (#15)

#### `RetrospectiveAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — PA Agents (#15) |
| **Role** | Post-Service Retrospective Review Agent |
| **Architecture Pattern** | Async claims-triggered workflow; same RAG stack as ClinicalAgent; 30-day SLA |

**Technology Stack:**

- GPT-4o + RAG
- ClaimsService UB-04/1500
- Temporal async workflow

**Business Use Cases:**

- Validate emergency services rendered before PA was obtained (2,500/day, 5% volume)
- Apply prudent layperson standard for ER necessity
- Evaluate 2-midnight rule for observation vs inpatient
- Recover inappropriate payments on retrospective denial

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 5-day avg |
| Sla | 30 days |
| Retrospective Denial Recovery | $2.1M/month |

**Implementation & Flow Position:** WorkflowEngine dashed post-service route. ClaimsService feeds UB-04/HCFA-1500 data.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `WorkflowEngine` | Post-Service |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | GPT-4o + RAG |
| 2 | `ClaimsService` | UB-04/1500 |

**Connection narrative:** receives from `WorkflowEngine` (Post-Service); sends to `LiteLLMRouter` (GPT-4o + RAG); sends to `ClaimsService` (UB-04/1500).

---

### Layer 4 — PA Agents (#16)

#### `RegistryAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — PA Agents (#16) |
| **Role** | PA De-Duplication & Registry Agent |
| **Architecture Pattern** | Cache-first dedup; Redis active PA index; fuzzy match on member+procedure |

**Technology Stack:**

- GPT-3.5 fuzzy match
- Redis active PA cache
- PostgreSQL PA history
- Bloom filter pre-check

**Business Use Cases:**

- Prevent duplicate PA submissions for same member+procedure (12% renewal detection)
- Return existing PA reference if active authorization found (<1 sec)
- Detect renewal vs new request for expedited processing
- Maintain payer PA registry for audit and reporting

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | <1 sec |
| Dedup Rate | 12% |
| False Positive | <0.5% |

**Implementation & Flow Position:** IntakeAgent triggers before EligibilityAgent. Redis cache + PostgreSQL history.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `IntakeAgent` | De-dup Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | GPT-3.5 |
| 2 | `Redis` | Active PA Cache |
| 3 | `PostgreSQL` | PA History |

**Connection narrative:** receives from `IntakeAgent` (De-dup Check); sends to `LiteLLMRouter` (GPT-3.5); sends to `Redis` (Active PA Cache); sends to `PostgreSQL` (PA History).

---

### Layer 4 — PA Agents (#17)

#### `DocRequestAgent`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 4 — PA Agents (#17) |
| **Role** | Clinical Documentation Request Agent |
| **Architecture Pattern** | Pend-and-request loop; GPT-4o generates specific doc request letter; provider notification |

**Technology Stack:**

- GPT-4o letter generation
- AttachmentService upload portal
- NotificationAgent alert
- Temporal pend state

**Business Use Cases:**

- Generate specific clinical documentation requests when ClinicalAgent confidence low (25% pend rate)
- List exactly what records needed (PT notes, lab results, imaging reports)
- Notify provider via portal/SMS within 2 minutes of pend
- Resume workflow when AttachmentService receives uploaded docs

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency | 2 min |
| Pend Rate | 25% |
| Doc Completion Rate | 78% within 48hr |

**Implementation & Flow Position:** ClinicalAgent pend trigger. AttachmentService for upload. NotificationAgent provider alert.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ClinicalAgent` | Pend Trigger |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `LiteLLMRouter` | GPT-4o Gen |
| 2 | `AttachmentService` | Doc Upload |
| 3 | `NotificationAgent` | Provider Alert |

**Connection narrative:** receives from `ClinicalAgent` (Pend Trigger); sends to `LiteLLMRouter` (GPT-4o Gen); sends to `AttachmentService` (Doc Upload); sends to `NotificationAgent` (Provider Alert).

---

### Layer 5 — Governance

#### `AgentRegistry`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 5 — Governance |
| **Role** | Agent Metadata & Version Registry |
| **Architecture Pattern** | Central registry; semantic versioning; config-driven agent deployment |

**Technology Stack:**

- PostgreSQL agent_registry table
- Semantic versioning
- AgentRegistryGateway API

**Business Use Cases:**

- Store 50+ agent definitions with version pins
- Feed IntakeAgent v2.1.0 config at runtime
- Track agent rollout canary percentages

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Agents Registered | 50+ |
| Config Fetch P95 | 10ms |

**Implementation & Flow Position:** AgentRegistryGateway → AgentRegistry → PostgreSQL. IntakeAgent loads config at workflow start.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Agent Metadata |
| 2 | `IntakeAgent` | Agent Config |

**Connection narrative:** sends to `PostgreSQL` (Agent Metadata); sends to `IntakeAgent` (Agent Config).

---

#### `PromptMgmt`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 5 — Governance |
| **Role** | Prompt versioning |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- Prompt templates for PolicyAgent.

**Implementation & Flow Position:** Component `PromptMgmt` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Prompt Versions |
| 2 | `PolicyAgent` | Prompt |

**Connection narrative:** sends to `PostgreSQL` (Prompt Versions); sends to `PolicyAgent` (Prompt).

---

#### `SafetyEval`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 5 — Governance |
| **Role** | Safety scoring |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Redis cache

**Business Use Cases:**

- ClinicalAgent output validation.

**Implementation & Flow Position:** Component `SafetyEval` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Redis` | Cache Scores |
| 2 | `ClinicalAgent` | Validate |

**Connection narrative:** sends to `Redis` (Cache Scores); sends to `ClinicalAgent` (Validate).

---

### Layer 6 — MCP

#### `MCPRegistry`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 6 — MCP |
| **Role** | MCP Tool Catalog & Permissions |
| **Architecture Pattern** | Tool registry pattern; MCP server discovery; permission-scoped tool access |

**Technology Stack:**

- PostgreSQL tool_registry SQL
- 20+ MCP servers
- RBAC tool permissions
- Vault credential refs

**Business Use Cases:**

- Catalog 50+ MCP tools (member_lookup, tier_calc, claims_search)
- Control which agents can invoke which tools
- Version tool schemas alongside agent updates

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Tools | 50+ |
| Mcp Servers | 20+ |

**Implementation & Flow Position:** MCPGateway → MCPRegistry. ToolExecutor reads permissions before sandbox run.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Tool Registry |
| 2 | `IntakeAgent` | Tools |

**Connection narrative:** sends to `PostgreSQL` (Tool Registry); sends to `IntakeAgent` (Tools).

---

#### `ToolExecutor`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 6 — MCP |
| **Role** | Tool execution |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Vault secrets

**Business Use Cases:**

- Executes tools for EligibilityAgent.

**Implementation & Flow Position:** Component `ToolExecutor` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Vault` | Secrets |
| 2 | `EligibilityAgent` | Execute |

**Connection narrative:** sends to `Vault` (Secrets); sends to `EligibilityAgent` (Execute).

---

### Layer 7 — Memory

#### `EpisodicMemory`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 7 — Memory |
| **Role** | Case history memory |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- FraudAgent historical pattern recall.

**Implementation & Flow Position:** Component `EpisodicMemory` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Storage |
| 2 | `FraudAgent` | History |

**Connection narrative:** sends to `PostgreSQL` (Storage); sends to `FraudAgent` (History).

---

#### `SemanticMemory`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 7 — Memory |
| **Role** | Vector Semantic Memory (Similar Cases) |
| **Architecture Pattern** | Vector memory store; embedding-based similar case retrieval |

**Technology Stack:**

- Milvus 10M vectors
- text-embedding-3-large
- Cosine similarity top-k

**Business Use Cases:**

- Retrieve similar approved PA cases for ClinicalAgent precedent
- Support episodic learning from historical decisions
- Reduce ClinicalAgent reasoning time on repeat procedure types

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Vectors | 10M |
| Retrieval P95 | 50ms |

**Implementation & Flow Position:** MemoryGateway → SemanticMemory → Milvus. ClinicalAgent semantic memory queries.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Milvus` | Vectors |
| 2 | `ClinicalAgent` | Knowledge |

**Connection narrative:** sends to `Milvus` (Vectors); sends to `ClinicalAgent` (Knowledge).

---

#### `WorkingMemory`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 7 — Memory |
| **Role** | Session Working Memory Store |
| **Architecture Pattern** | Cache-aside working memory; 6-hour session TTL; hash map workflow_id → state JSON |

**Technology Stack:**

- Redis 7 Hash structure
- 6-hour TTL
- JSON state blob

**Business Use Cases:**

- Hold in-flight agent outputs during 15-min PA pipeline
- Store DecisionAgent final decision for NotificationAgent
- Provide IntakeAgent session context to downstream agents

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Ttl | 6 hours |
| P50 | <5ms |

**Implementation & Flow Position:** MemoryGateway → WorkingMemory → Redis. DecisionAgent writes final decision.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DecisionAgent` | Final Decision |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Redis` | Cache |
| 2 | `IntakeAgent` | Context |

**Connection narrative:** receives from `DecisionAgent` (Final Decision); sends to `Redis` (Cache); sends to `IntakeAgent` (Context).

---

### Layer 8 — RAG

#### `GraphRAG`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 8 — RAG |
| **Role** | Knowledge Graph RAG Service |
| **Architecture Pattern** | Graph traversal RAG; Cypher pattern matching; relationship-aware retrieval |

**Technology Stack:**

- Neo4j 5 GDS
- 500K nodes
- 4 queries/case
- Cypher path finding

**Business Use Cases:**

- Traverse diagnosis→procedure→guideline relationships
- Find contraindication paths (drug interactions, comorbidities)
- Fraud pattern graph queries

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Queries Per Case | 4 |
| P95 | 120ms |
| Nodes | 500K |

**Implementation & Flow Position:** ClinicalAgent → GraphRAG → Neo4j → RRF relevance scores.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ClinicalAgent` | Relationship Query |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `RRF` | Relevance |
| 2 | `Neo4j` | Graph Traverse |
| 3 | `Neo4j` | — |

**Connection narrative:** receives from `ClinicalAgent` (Relationship Query); sends to `RRF` (Relevance); sends to `Neo4j` (Graph Traverse); sends to `Neo4j`.

---

#### `HybridSearch`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 8 — RAG |
| **Role** | BM25 Keyword Search Service |
| **Architecture Pattern** | Inverted index full-text search; ICD/CPT exact match boost |

**Technology Stack:**

- Elasticsearch 8 BM25
- 500K documents
- 6 queries/case

**Business Use Cases:**

- Exact ICD-10/CPT code matching in clinical policies
- Keyword search for drug names and procedure descriptions

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Queries Per Case | 6 |
| P95 | 85ms |

**Implementation & Flow Position:** ClinicalAgent → HybridSearch → Elasticsearch → RRF BM25 scores.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ClinicalAgent` | Keyword Search |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `RRF` | BM25 Scores |
| 2 | `Elasticsearch` | Index Scan |
| 3 | `Elasticsearch` | — |

**Connection narrative:** receives from `ClinicalAgent` (Keyword Search); sends to `RRF` (BM25 Scores); sends to `Elasticsearch` (Index Scan); sends to `Elasticsearch`.

---

#### `RRF`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 8 — RAG |
| **Role** | Reciprocal Rank Fusion Ranker |
| **Architecture Pattern** | Ensemble ranker; RRF k=60 fusion of heterogeneous retrieval scores |

**Technology Stack:**

- Python RRF implementation
- k=60 constant
- Top-10 output

**Business Use Cases:**

- Merge vector, BM25, and graph results into unified ranked list
- Prevent single retrieval method bias in clinical decisions
- Deliver top-10 chunks to ClinicalContentService

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Fusion Latency | 15ms |
| Top K | 10 |
| K Constant | 60 |

**Implementation & Flow Position:** VectorSearch + HybridSearch + GraphRAG → RRF → ClinicalContentService.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `VectorSearch` | Vector Scores |
| 2 | `HybridSearch` | BM25 Scores |
| 3 | `GraphRAG` | Relevance |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ClinicalContentService` | Top 10 Ranked Results |

**Connection narrative:** receives from `VectorSearch` (Vector Scores); receives from `HybridSearch` (BM25 Scores); receives from `GraphRAG` (Relevance); sends to `ClinicalContentService` (Top 10 Ranked Results).

---

#### `VectorSearch`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 8 — RAG |
| **Role** | Semantic Vector Search Service |
| **Architecture Pattern** | ANN search; HNSW index; embedding query pipeline |

**Technology Stack:**

- Milvus HNSW
- 1024-dim BGE-large
- 8 queries/case
- Cosine similarity

**Business Use Cases:**

- Find semantically similar clinical guidelines for diagnosis+procedure pair
- Support MCG/InterQual document retrieval by clinical concept

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Queries Per Case | 8 |
| P95 | 45ms |
| Embeddings | 10M |

**Implementation & Flow Position:** ClinicalAgent → VectorSearch → Milvus → RRF vector scores.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ClinicalAgent` | Semantic Search |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `RRF` | Vector Scores |
| 2 | `Milvus` | Vector Lookup |
| 3 | `Milvus` | — |

**Connection narrative:** receives from `ClinicalAgent` (Semantic Search); sends to `RRF` (Vector Scores); sends to `Milvus` (Vector Lookup); sends to `Milvus`.

---

### Layer 9 — Data Services

*gRPC-primary microservices (3.5M calls/day, 75% cache hit). Pattern: **Cache-Aside + Circuit Breaker**.*

#### `BenefitsConfigService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Benefit Tier Configuration API |
| **Architecture Pattern** | Configuration service; tier structure CRUD; cached reads |

**Technology Stack:**

- Spring Boot 3
- PostgreSQL
- Redis cache
- Bronze/Silver/Gold/Platinum schema

**Business Use Cases:**

- Serve tier structures for BenefitsAgent tier calculation
- Define PA requirements per plan tier
- Support annual open enrollment tier updates

**Key Metrics:**

| Metric | Value |
|--------|-------|
| P95 | 40ms |
| Cache Hit | 95% |

**Implementation & Flow Position:** BenefitsAgent → BenefitsConfigService → PostgreSQL.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BenefitsAgent` | Tier Matching |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Config DB |

**Connection narrative:** receives from `BenefitsAgent` (Tier Matching); sends to `PostgreSQL` (Config DB).

---

#### `ClaimsService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Historical Claims Data API |
| **Architecture Pattern** | Event-sourced claims store; Kafka change events; read-heavy optimization |

**Technology Stack:**

- Spring Boot 3
- PostgreSQL 150M claims
- Kafka events
- NDC/CPT indexes

**Business Use Cases:**

- Provide claim history for FraudAgent graph analysis
- Look up prior NDC fills for StepTherapyAgent (12-month window)
- Feed RetrospectiveAgent UB-04/HCFA-1500 post-service claims
- Support duplicate billing detection in FraudAgent

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 800K/day |
| Claims Stored | 150M |
| P95 | 100ms |

**Implementation & Flow Position:** FraudAgent, StepTherapyAgent, RetrospectiveAgent consumers. Kafka event publishing.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FraudAgent` | Claim History |
| 2 | `StepTherapyAgent` | Prior Fills |
| 3 | `RetrospectiveAgent` | UB-04/1500 |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Claims DB |
| 2 | `Kafka` | Events |

**Connection narrative:** receives from `FraudAgent` (Claim History); receives from `StepTherapyAgent` (Prior Fills); receives from `RetrospectiveAgent` (UB-04/1500); sends to `PostgreSQL` (Claims DB); sends to `Kafka` (Events).

---

#### `ClinicalContentService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Clinical Guideline Content Store |
| **Architecture Pattern** | Content delivery layer for RAG; Elasticsearch + PostgreSQL metadata |

**Technology Stack:**

- Elasticsearch 8 content index
- PostgreSQL metadata
- MCG/InterQual/CMS LCD corpus

**Business Use Cases:**

- Serve top-10 RRF-ranked guideline chunks to ClinicalAgent
- Store and retrieve full clinical policy text for citation
- Index 500K clinical documents for HybridSearch BM25
- Support AttachmentService clinical document indexing

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Documents | 500K |
| Rag Top K | 10 |
| P95 | 80ms |

**Implementation & Flow Position:** RRF → ClinicalContentService → ClinicalAgent context window. ES + PostgreSQL.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `RRF` | Top 10 Ranked Results |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Elasticsearch` | Content |
| 2 | `PostgreSQL` | Metadata |
| 3 | `Elasticsearch` | Content Index |
| 4 | `PostgreSQL` | Metadata |

**Connection narrative:** receives from `RRF` (Top 10 Ranked Results); sends to `Elasticsearch` (Content); sends to `PostgreSQL` (Metadata); sends to `Elasticsearch` (Content Index); + 1 more outbound.

---

#### `FormularyService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Drug Formulary & Tier API |
| **Architecture Pattern** | Formulary lookup; NDC→tier mapping; step therapy rules store |

**Technology Stack:**

- Spring Boot 3
- PostgreSQL formulary DB
- NDC/RxNorm indexes

**Business Use Cases:**

- Return drug tier for StepTherapyAgent (tiers 1-6)
- Support FHIRCDSService real-time formulary PA check
- Identify step therapy requirements per NDC

**Key Metrics:**

| Metric | Value |
|--------|-------|
| P95 | 50ms |
| Ndc Coverage | 98% |

**Implementation & Flow Position:** FHIRCDSService, StepTherapyAgent, BenefitsAgent consumers.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FHIRCDSService` | PA Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Formulary DB |

**Connection narrative:** receives from `FHIRCDSService` (PA Check); sends to `PostgreSQL` (Formulary DB).

---

#### `MemberService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Member Demographics & Eligibility API |
| **Architecture Pattern** | Microservice + cache-aside (Redis); gRPC primary, REST fallback; circuit breaker |

**Technology Stack:**

- Spring Boot 3
- gRPC + REST
- PostgreSQL 5M rows
- Redis 24h TTL
- Protobuf member.proto

**Business Use Cases:**

- Look up member by ID for EligibilityAgent verification (2M queries/day)
- Validate plan active on service date; return tier and effective dates
- Search members by name/DOB for provider portal lookup
- Support dependent and family coverage queries

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 2M/day |
| P95 | 50ms |
| Cache Hit | 75% |
| Availability | 99.95% |

**Implementation & Flow Position:** EligibilityAgent → ToolGateway → MemberService. PostgreSQL + Redis cache-aside.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `EligibilityAgent` | Member Lookup |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Member DB |
| 2 | `Redis` | Cache |

**Connection narrative:** receives from `EligibilityAgent` (Member Lookup); sends to `PostgreSQL` (Member DB); sends to `Redis` (Cache).

---

#### `NetworkService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Provider Network Validation API |
| **Architecture Pattern** | Network graph lookup; plan-provider affiliation matrix |

**Technology Stack:**

- Spring Boot 3
- PostgreSQL network tables
- Redis 24h cache

**Business Use Cases:**

- Validate provider in-network for member plan
- Return tier 1/2/OON status for BenefitsAgent
- Support narrow network plan PA rules

**Key Metrics:**

| Metric | Value |
|--------|-------|
| P95 | 60ms |
| Cache Hit | 90% |

**Implementation & Flow Position:** BenefitsAgent → NetworkService. ProviderService NPI cross-reference.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BenefitsAgent` | Network Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Network DB |

**Connection narrative:** receives from `BenefitsAgent` (Network Check); sends to `PostgreSQL` (Network DB).

---

#### `PolicyService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Medical & Drug Policy Document API |
| **Architecture Pattern** | Document store + OPA evaluation engine; Elasticsearch full-text search |

**Technology Stack:**

- Spring Boot 3
- PostgreSQL 100K policies
- Elasticsearch FTS
- OPA Rego embedded
- REST API

**Business Use Cases:**

- Retrieve policy documents for PolicyAgent evaluation (100K queries/day)
- Search policies by CPT/ICD-10/state combination
- Execute OPA Rego rule evaluation (<200ms for 50 rules)
- Serve FHIRCDSService real-time PA requirement checks

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 100K/day |
| P95 | 150ms |
| Cache Hit | 90% |

**Implementation & Flow Position:** PolicyAgent, BenefitsAgent, FHIRCDSService, StateMandateService consumers.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BenefitsAgent` | Policy Lookup |
| 2 | `PolicyAgent` | Rule Lookup |
| 3 | `PolicyAgent` | — |
| 4 | `FHIRCDSService` | Rules Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Policy DB |
| 2 | `Redis` | Cache |

**Connection narrative:** receives from `BenefitsAgent` (Policy Lookup); receives from `PolicyAgent` (Rule Lookup); receives from `PolicyAgent`; sends to `PostgreSQL` (Policy DB); sends to `Redis` (Cache); + 1 more inbound.

---

#### `ProviderService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services |
| **Role** | Provider Directory & Credentialing API |
| **Architecture Pattern** | Microservice + PostGIS geo-search; NPPES external sync |

**Technology Stack:**

- Spring Boot 3
- PostgreSQL 500K rows
- PostGIS spatial
- NPPES CMS API sync
- Redis 7-day TTL

**Business Use Cases:**

- Validate NPI and provider credentials for IntakeAgent (500K queries/day)
- Check in-network status for BenefitsAgent network validation
- Geo-search providers by specialty and zip code (25-mile radius)
- Support COMAgent multi-payer provider network lookup

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 500K/day |
| P95 | 75ms |
| Cache Hit | 80% |

**Implementation & Flow Position:** EligibilityAgent, BenefitsAgent, COMAgent, ProviderAnalyticsService consumers.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `COMAgent` | Network Lookup |
| 2 | `ProviderAnalyticsService` | Provider Score |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Provider DB |
| 2 | `Redis` | Cache |

**Connection narrative:** receives from `COMAgent` (Network Lookup); receives from `ProviderAnalyticsService` (Provider Score); sends to `PostgreSQL` (Provider DB); sends to `Redis` (Cache).

---

### Layer 9 — Data Services (new)

#### `AttachmentService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | Clinical Document Attachment Handler |
| **Architecture Pattern** | Blob store + search index; secure upload portal; virus scan pipeline |

**Technology Stack:**

- Azure Blob Storage
- Elasticsearch content index
- ClamAV scan
- DirectGateway S/MIME

**Business Use Cases:**

- Store supporting clinical documents for pended PAs
- Index document content for ClinicalAgent re-evaluation
- Receive Direct secure messages from providers

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Storage | 10TB |
| Upload P95 | 3 sec |

**Implementation & Flow Position:** DocRequestAgent, DirectGateway → AttachmentService → BlobStorage + Elasticsearch.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DirectGateway` | Secure Docs |
| 2 | `DocRequestAgent` | Doc Upload |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `BlobStorage` | Store Docs |
| 2 | `Elasticsearch` | Index Content |

**Connection narrative:** receives from `DirectGateway` (Secure Docs); receives from `DocRequestAgent` (Doc Upload); sends to `BlobStorage` (Store Docs); sends to `Elasticsearch` (Index Content).

---

#### `CodeValidationService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | ICD/CPT validation |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Redis code cache

**Business Use Cases:**

- IntakeAgent code validation.

**Implementation & Flow Position:** Component `CodeValidationService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `IntakeAgent` | ICD/CPT Check |
| 2 | `Redis` | Code Cache |

**Connection narrative:** sends to `IntakeAgent` (ICD/CPT Check); sends to `Redis` (Code Cache).

---

#### `DrugReferenceService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | NDC/RxNorm Drug Reference API |
| **Architecture Pattern** | Reference data service; 95% Redis cache; RxNorm crosswalk |

**Technology Stack:**

- PostgreSQL NDC/RxNorm tables
- Redis 95% cache
- FDA NDC Directory sync

**Business Use Cases:**

- NDC lookup for StepTherapyAgent drug identification
- RxNorm concept mapping for formulary tier lookup
- Generic/brand cross-reference for step therapy rules

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Cache Hit | 95% |
| P95 | 15ms |

**Implementation & Flow Position:** StepTherapyAgent → DrugReferenceService. Redis + PostgreSQL.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `StepTherapyAgent` | NDC Lookup |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Redis` | 95% Cache |
| 2 | `PostgreSQL` | NDC/RxNorm |

**Connection narrative:** receives from `StepTherapyAgent` (NDC Lookup); sends to `Redis` (95% Cache); sends to `PostgreSQL` (NDC/RxNorm).

---

#### `FHIRCDSService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | FHIR CDS Hooks Clinical Decision Support |
| **Architecture Pattern** | CDS Hooks 2.0 server; synchronous point-of-care PA check |

**Technology Stack:**

- FHIR R4
- CDS Hooks 2.0
- order-select hook
- FormularyService + PolicyService

**Business Use Cases:**

- Real-time PA requirement card in EHR at order entry
- Reduce unnecessary PA submissions (30% reduction)
- FHIR CRD (Coverage Requirements Discovery) compliance

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Latency P95 | <500ms |
| Hook Calls | 80K/day |

**Implementation & Flow Position:** FHIRGateway → FHIRCDSService → FormularyService + PolicyService.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FHIRGateway` | CDS Hooks |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `FormularyService` | PA Check |
| 2 | `PolicyService` | Rules Check |

**Connection narrative:** receives from `FHIRGateway` (CDS Hooks); sends to `FormularyService` (PA Check); sends to `PolicyService` (Rules Check).

---

#### `GrievanceTrackService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | Appeal timeline |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- AppealsAgent grievance tracking.

**Implementation & Flow Position:** Component `GrievanceTrackService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `AppealsAgent` | Appeal Track |
| 2 | `PostgreSQL` | Timeline Store |

**Connection narrative:** sends to `AppealsAgent` (Appeal Track); sends to `PostgreSQL` (Timeline Store).

---

#### `PayerExchangeService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | Inter-payer PA transfer |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- FHIR Bundle

**Business Use Cases:**

- ConsentMgmtService gated export.

**Implementation & Flow Position:** Component `PayerExchangeService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ConsentMgmtService` | Consent Check |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `FHIRGateway` | FHIR Export |
| 2 | `PostgreSQL` | PA Transfer |

**Connection narrative:** receives from `ConsentMgmtService` (Consent Check); sends to `FHIRGateway` (FHIR Export); sends to `PostgreSQL` (PA Transfer).

---

#### `ProviderPortalService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | Provider Portal GraphQL BFF API |
| **Architecture Pattern** | GraphQL BFF; aggregates PA status, scheduling, document upload |

**Technology Stack:**

- GraphQL Apollo Server
- PostgreSQL PA status
- ProviderPortal frontend

**Business Use Cases:**

- Serve PA status dashboard to ProviderPortal Angular app
- Schedule P2P calls for MedDirectorAgent
- Handle bulk CSV PA upload API

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Graphql P95 | 200ms |
| Providers | 85K |

**Implementation & Flow Position:** ProviderPortalService ↔ ProviderPortal. MedDirectorAgent P2P scheduling.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `MedDirectorAgent` | Schedule P2P |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ProviderPortal` | GraphQL API |
| 2 | `PostgreSQL` | PA Status |

**Connection narrative:** receives from `MedDirectorAgent` (Schedule P2P); sends to `ProviderPortal` (GraphQL API); sends to `PostgreSQL` (PA Status).

---

#### `QualityMeasureService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | HEDIS/Stars Quality Measure Tracking |
| **Architecture Pattern** | Quality event capture; NCQA measure calculation; Stars rating input |

**Technology Stack:**

- PostgreSQL Stars data
- HEDIS measure definitions
- Kafka quality events

**Business Use Cases:**

- Capture PA decision quality measures for NCQA HEDIS reporting
- Track timely PA decision rate for Medicare Stars rating
- Feed quality dashboards for payer compliance teams

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Measures Tracked | 45 HEDIS |
| Timely Pa Rate | 99.2% |

**Implementation & Flow Position:** DecisionAgent → QualityMeasureService → PostgreSQL.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `DecisionAgent` | HEDIS Track |
| 2 | `PostgreSQL` | Stars Data |

**Connection narrative:** sends to `DecisionAgent` (HEDIS Track); sends to `PostgreSQL` (Stars Data).

---

#### `SLAMonitorService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | PA SLA Deadline Tracking Service |
| **Architecture Pattern** | Deadline scheduler; event-driven SLA breach alerts |

**Technology Stack:**

- PostgreSQL deadline store
- Quartz scheduler
- Kafka SLA events
- PagerDuty integration

**Business Use Cases:**

- Track 30-minute standard PA SLA (99.2% compliance)
- Track 72-hour CMS expedited SLA for ExpeditedAgent
- Alert medical director at 24-hour mark on urgent cases
- Feed CapacityPlanningService historical SLA data

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Sla Compliance | 99.2% |
| Expedited Sla | 72 hr CMS |

**Implementation & Flow Position:** ExpeditedAgent → SLAMonitorService. WorkflowEngine SLA tracking loop.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ExpeditedAgent` | 72hr Track |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `WorkflowEngine` | Track SLA |
| 2 | `PostgreSQL` | Deadline Store |

**Connection narrative:** receives from `ExpeditedAgent` (72hr Track); sends to `WorkflowEngine` (Track SLA); sends to `PostgreSQL` (Deadline Store).

---

#### `ePAService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 9 — Data Services (new) |
| **Role** | Electronic Prior Authorization Transform Service |
| **Architecture Pattern** | Anti-corruption layer; X12/FHIR → canonical PA model |

**Technology Stack:**

- X12 parser
- FHIR R4 mapper
- PostgreSQL EDI log
- Spring Integration

**Business Use Cases:**

- Transform X12 278 and NCPDP SCRIPT to IntakeAgent input format
- Log all EDI transactions for regulatory audit
- Support bidirectional ePA response generation
- Enable standard-based PA without custom integration per provider

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Volume | 50K/day |
| Transform Success | 99.5% |

**Implementation & Flow Position:** X12Gateway/NCPDPGateway → ePAService → IntakeAgent. PostgreSQL EDI log.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `X12Gateway` | ePA Process |
| 2 | `NCPDPGateway` | Pharmacy PA |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `IntakeAgent` | Transform PA |
| 2 | `PostgreSQL` | EDI Log |

**Connection narrative:** receives from `X12Gateway` (ePA Process); receives from `NCPDPGateway` (Pharmacy PA); sends to `IntakeAgent` (Transform PA); sends to `PostgreSQL` (EDI Log).

---

### Compliance Layer

#### `BreachNotifyService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Compliance Layer |
| **Role** | Breach notification |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- DLP-triggered breach workflow.

**Implementation & Flow Position:** Component `BreachNotifyService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `DLPService` | Breach Detect |
| 2 | `PostgreSQL` | Breach Log |

**Connection narrative:** sends to `DLPService` (Breach Detect); sends to `PostgreSQL` (Breach Log).

---

#### `ConsentMgmtService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Compliance Layer |
| **Role** | Consent management |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- PayerExchange consent verification.

**Implementation & Flow Position:** Component `ConsentMgmtService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PayerExchangeService` | Consent Check |
| 2 | `PostgreSQL` | Consent DB |

**Connection narrative:** sends to `PayerExchangeService` (Consent Check); sends to `PostgreSQL` (Consent DB).

---

#### `DLPService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Compliance Layer |
| **Role** | Data Loss Prevention / PHI Scanner |
| **Architecture Pattern** | Inline DLP scan on outbound communications; breach detection trigger |

**Technology Stack:**

- Microsoft Purview DLP
- PHI pattern matching
- PostgreSQL incident log

**Business Use Cases:**

- Scan NotificationAgent outbound messages for PHI leakage
- Scan AuditAgent logs before external export
- Trigger BreachNotifyService on DLP violation

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Scan Coverage | 100% outbound |
| False Positive | <2% |

**Implementation & Flow Position:** Dashed upstream to NotificationAgent and AuditAgent. BreachNotifyService on detect.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `BreachNotifyService` | Breach Detect |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `NotificationAgent` | PHI Scan |
| 2 | `AuditAgent` | Log Scan |
| 3 | `PostgreSQL` | Incident Log |

**Connection narrative:** receives from `BreachNotifyService` (Breach Detect); sends to `NotificationAgent` (PHI Scan); sends to `AuditAgent` (Log Scan); sends to `PostgreSQL` (Incident Log).

---

#### `StateMandateService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Compliance Layer |
| **Role** | 50-state mandates |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- PolicyAgent state rule injection.

**Implementation & Flow Position:** Component `StateMandateService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PolicyAgent` | State Rules |
| 2 | `PostgreSQL` | 50-State DB |

**Connection narrative:** sends to `PolicyAgent` (State Rules); sends to `PostgreSQL` (50-State DB).

---

### Analytics Layer

#### `CapacityPlanningService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Analytics Layer |
| **Role** | HITL staffing |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- HITLRouting capacity planning.

**Implementation & Flow Position:** Component `CapacityPlanningService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `HITLRouting` | Staffing Plan |
| 2 | `PostgreSQL` | Historical Data |

**Connection narrative:** sends to `HITLRouting` (Staffing Plan); sends to `PostgreSQL` (Historical Data).

---

#### `CommPreferenceService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Analytics Layer |
| **Role** | Member comm prefs |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Redis + PostgreSQL

**Business Use Cases:**

- NotificationAgent channel selection.

**Implementation & Flow Position:** Component `CommPreferenceService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `NotificationAgent` | Channel Select |
| 2 | `Redis` | Pref Cache |
| 3 | `PostgreSQL` | Member Prefs |

**Connection narrative:** sends to `NotificationAgent` (Channel Select); sends to `Redis` (Pref Cache); sends to `PostgreSQL` (Member Prefs).

---

#### `MultiTenantService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Analytics Layer |
| **Role** | Multi-Payer Configuration Service |
| **Architecture Pattern** | Tenant config store; per-payer workflow rules and branding |

**Technology Stack:**

- MongoDB config documents
- Tenant ID routing
- Feature flags per payer

**Business Use Cases:**

- Configure per-payer PA rules (Medicare vs commercial vs Medicaid)
- Customize auto-approve thresholds by payer contract
- Enable/disable agents per payer plan type

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Tenants | 12 payers |
| Config Fetch | <20ms |

**Implementation & Flow Position:** MultiTenantService → WorkflowEngine payer config injection at workflow start.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `WorkflowEngine` | Payer Config |
| 2 | `MongoDB` | Config Store |

**Connection narrative:** sends to `WorkflowEngine` (Payer Config); sends to `MongoDB` (Config Store).

---

#### `ProviderAnalyticsService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Analytics Layer |
| **Role** | Provider scoring |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- PostgreSQL

**Business Use Cases:**

- ProviderService analytics enrichment.

**Implementation & Flow Position:** Component `ProviderAnalyticsService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ProviderService` | Provider Score |
| 2 | `PostgreSQL` | Analytics DB |

**Connection narrative:** sends to `ProviderService` (Provider Score); sends to `PostgreSQL` (Analytics DB).

---

#### `RootCauseService`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Analytics Layer |
| **Role** | Denial root cause |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Elasticsearch

**Business Use Cases:**

- DecisionAgent denial pattern analysis.

**Implementation & Flow Position:** Component `RootCauseService` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `DecisionAgent` | Denial Pattern |
| 2 | `Elasticsearch` | Log Analysis |

**Connection narrative:** sends to `DecisionAgent` (Denial Pattern); sends to `Elasticsearch` (Log Analysis).

---

### Layer 10 — HITL

*28% human review (14K/day). Pattern: **Interrupt-Before + Priority Queue**.*

#### `ApprovalWorkflow`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 10 — HITL |
| **Role** | Approval sub-workflow |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Temporal + Kafka

**Business Use Cases:**

- Human approve/deny; AuditAgent log.

**Implementation & Flow Position:** Component `ApprovalWorkflow` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ReviewQueue` | — |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `PostgreSQL` | Approval Log |
| 2 | `Kafka` | Event Stream |
| 3 | `AuditAgent` | Log |

**Connection narrative:** receives from `ReviewQueue`; sends to `PostgreSQL` (Approval Log); sends to `Kafka` (Event Stream); sends to `AuditAgent` (Log).

---

#### `HITLRouting`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 10 — HITL |
| **Role** | Human-in-the-Loop Risk Router |
| **Architecture Pattern** | Rules engine routing; weighted confidence aggregation; interrupt-before gate |

**Technology Stack:**

- Drools BRMS
- Confidence thresholds
- Fraud risk score input
- Priority queue assignment

**Business Use Cases:**

- Route 28% of cases (14K/day) to human clinical reviewers
- Prioritize fraud cases and all denials for human review
- Auto-approve 72% low-risk cases without human touch

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Hitl Rate | 28% |
| Auto Approve | 72% |
| Reviewers | 160 FTE equivalent |

**Implementation & Flow Position:** DecisionAgent step ⑩ → HITLRouting → ReviewQueue (28%) or NotificationAgent (72%).

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DecisionAgent` | ⑩ Risk Assessment |
| 2 | `DecisionAgent` | ⑩ Risk Assessment |
| 3 | `CapacityPlanningService` | Staffing Plan |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ReviewQueue` | 28% Human (14K/day) |
| 2 | `NotificationAgent` | 72% Auto-Approve (36K/day) |

**Connection narrative:** receives from `DecisionAgent` (⑩ Risk Assessment); receives from `DecisionAgent` (⑩ Risk Assessment); receives from `CapacityPlanningService` (Staffing Plan); sends to `ReviewQueue` (28% Human (14K/day)); sends to `NotificationAgent` (72% Auto-Approve (36K/day)).

---

#### `ReviewQueue`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 10 — HITL |
| **Role** | Human Review Work Queue |
| **Architecture Pattern** | Priority queue; specialty-matched assignment; SLA-tracked work items |

**Technology Stack:**

- PostgreSQL queue table
- Priority scoring
- Reviewer skill matching
- SLA timer

**Business Use Cases:**

- Queue 14K daily human reviews with <4hr SLA
- Assign cardiology PAs to cardiology-trained nurses
- Surface fraud-flagged cases at top of queue

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Daily Volume | 14K |
| Sla Avg | <4 hr |
| Sla P95 | <8 hr |

**Implementation & Flow Position:** HITLRouting → ReviewQueue → ApprovalWorkflow. CapacityPlanningService feeds staffing.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `HITLRouting` | 28% Human (14K/day) |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `ApprovalWorkflow` | — |

**Connection narrative:** receives from `HITLRouting` (28% Human (14K/day)); sends to `ApprovalWorkflow`.

---

### Database Layer

*Polyglot persistence: PostgreSQL (transactional), Redis (hot), Milvus (vectors), Neo4j (graph), ES (search).*

#### `BlobStorage`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Document blob store |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Azure Blob 10TB

**Business Use Cases:**

- PDF/DICOM/TIFF original documents.

**Implementation & Flow Position:** Component `BlobStorage` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `IntakeAgent` | Store PDF |
| 2 | `AttachmentService` | Store Docs |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `IntakeAgent` (Store PDF); receives from `AttachmentService` (Store Docs).

---

#### `Elasticsearch`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Full-text + audit index |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Elasticsearch 8

**Business Use Cases:**

- BM25 search; audit log index.

**Implementation & Flow Position:** Component `Elasticsearch` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `AuditAgent` | Audit Index |
| 2 | `HybridSearch` | Index Scan |
| 3 | `ClinicalContentService` | Content |
| 4 | `ClinicalContentService` | Content Index |
| 5 | `HybridSearch` | — |
| 6 | `Kafka` | Event Index |
| 7 | `AttachmentService` | Index Content |
| 8 | `RootCauseService` | Log Analysis |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `AuditAgent` (Audit Index); receives from `HybridSearch` (Index Scan); receives from `ClinicalContentService` (Content); + 5 more inbound.

---

#### `Milvus`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Vector embeddings |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Milvus 2.3

**Business Use Cases:**

- 10M clinical guideline embeddings.

**Implementation & Flow Position:** Component `Milvus` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `VectorSearch` | Vector Lookup |
| 2 | `VectorSearch` | — |
| 3 | `SemanticMemory` | Vectors |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `VectorSearch` (Vector Lookup); receives from `VectorSearch`; receives from `SemanticMemory` (Vectors).

---

#### `MongoDB`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Multi-tenant config |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- MongoDB 6

**Business Use Cases:**

- Per-payer workflow configuration.

**Implementation & Flow Position:** Component `MongoDB` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `MultiTenantService` | Config Store |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `MultiTenantService` (Config Store).

---

#### `Neo4j`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Knowledge graph |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Neo4j 5

**Business Use Cases:**

- 500K nodes; fraud + clinical relationships.

**Implementation & Flow Position:** Component `Neo4j` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FraudAgent` | Graph Patterns |
| 2 | `GraphRAG` | Graph Traverse |
| 3 | `FraudAgent` | — |
| 4 | `GraphRAG` | — |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `FraudAgent` (Graph Patterns); receives from `GraphRAG` (Graph Traverse); receives from `FraudAgent`; + 1 more inbound.

---

#### `PostgreSQL`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Primary Relational Database |
| **Architecture Pattern** | Primary-replica HA; JSONB for workflow state; B-tree + GIN indexes |

**Technology Stack:**

- PostgreSQL 15
- HA synchronous replica
- JSONB checkpoints
- pgvector extension

**Business Use Cases:**

- Store workflow checkpoints, member data, policies, audit logs
- Temporal event history backend
- 90-day workflow state cold storage

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Size | 12TB |
| Availability | 99.99% |
| Connections | 500 pooled |

**Implementation & Flow Position:** Written by StateManager, Temporal, all data services, AuditAgent, HITL layer.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `StateManager` | Cold Store (90d) |
| 2 | `Temporal` | Event History |
| 3 | `IntakeAgent` | Metadata |
| 4 | `AuditAgent` | Compliance |
| 5 | `ClinicalContentService` | Metadata |
| 6 | `MemberService` | Member DB |
| 7 | `ProviderService` | Provider DB |
| 8 | `PolicyService` | Policy DB |
| 9 | `ClaimsService` | Claims DB |
| 10 | `BenefitsConfigService` | Config DB |
| 11 | `NetworkService` | Network DB |
| 12 | `FormularyService` | Formulary DB |
| 13 | `ClinicalContentService` | Metadata |
| 14 | `AgentRegistry` | Agent Metadata |
| 15 | `PromptMgmt` | Prompt Versions |
| 16 | `MCPRegistry` | Tool Registry |
| 17 | `EpisodicMemory` | Storage |
| 18 | `ApprovalWorkflow` | Approval Log |
| 19 | `Prometheus` | Metrics |
| 20 | `Jaeger` | Store |
| 21 | `Keycloak` | User DB |
| 22 | `Kafka` | Event Log |
| 23 | `RegistryAgent` | PA History |
| 24 | `ePAService` | EDI Log |
| 25 | `DrugReferenceService` | NDC/RxNorm |
| 26 | `SLAMonitorService` | Deadline Store |
| 27 | `QualityMeasureService` | Stars Data |
| 28 | `PayerExchangeService` | PA Transfer |
| 29 | `ProviderPortalService` | PA Status |
| 30 | `GrievanceTrackService` | Timeline Store |
| 31 | `DLPService` | Incident Log |
| 32 | `ConsentMgmtService` | Consent DB |
| 33 | `BreachNotifyService` | Breach Log |
| 34 | `StateMandateService` | 50-State DB |
| 35 | `CapacityPlanningService` | Historical Data |
| 36 | `ProviderAnalyticsService` | Analytics DB |
| 37 | `CommPreferenceService` | Member Prefs |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `StateManager` (Cold Store (90d)); receives from `Temporal` (Event History); receives from `IntakeAgent` (Metadata); + 34 more inbound.

---

#### `Redis`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Hot Cache & Working Memory |
| **Architecture Pattern** | Redis Cluster; cache-aside; session store; rate limit counters |

**Technology Stack:**

- Redis 7 Cluster
- 3 shards 3 replicas
- Hash + String structures
- 6h session TTL

**Business Use Cases:**

- Cache member/provider lookups (75-85% hit rate)
- Store workflow working memory (6h TTL)
- Token bucket rate limiting (100 req/min)

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Ops Per Day | 500M |
| P50 | <5ms |
| Hit Rate | 75-85% |

**Implementation & Flow Position:** DataAccessGateway, MemoryGateway, TokenMgmtGateway, StateManager hot tier.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `DataAccessGateway` | Token Cache |
| 2 | `TokenMgmtGateway` | Rate State |
| 3 | `ContextGateway` | Session Context |
| 4 | `MemoryGateway` | Working Memory |
| 5 | `StateManager` | Hot Store (5min) |
| 6 | `MemberService` | Cache |
| 7 | `ProviderService` | Cache |
| 8 | `PolicyService` | Cache |
| 9 | `SafetyEval` | Cache Scores |
| 10 | `WorkingMemory` | Cache |
| 11 | `Grafana` | Dashboard Cache |
| 12 | `RegistryAgent` | Active PA Cache |
| 13 | `DrugReferenceService` | 95% Cache |
| 14 | `CodeValidationService` | Code Cache |
| 15 | `CommPreferenceService` | Pref Cache |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `DataAccessGateway` (Token Cache); receives from `TokenMgmtGateway` (Rate State); receives from `ContextGateway` (Session Context); + 12 more inbound.

---

#### `Vault`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Database Layer |
| **Role** | Secrets management |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- HashiCorp Vault

**Business Use Cases:**

- MCP tool credentials; API keys.

**Implementation & Flow Position:** Component `Vault` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `ToolExecutor` | Secrets |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `ToolExecutor` (Secrets).

---

### Infrastructure

*Azure AKS platform services. Pattern: **Sidecar Observability + Event-Driven Architecture**.*

#### `Grafana`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Infrastructure |
| **Role** | Dashboards |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Grafana 20+ dashboards

**Business Use Cases:**

- Queries Prometheus; Redis dashboard cache.

**Implementation & Flow Position:** Component `Grafana` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `Prometheus` | Query |
| 2 | `Redis` | Dashboard Cache |

**Connection narrative:** sends to `Prometheus` (Query); sends to `Redis` (Dashboard Cache).

---

#### `Jaeger`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Infrastructure |
| **Role** | Distributed tracing |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Jaeger adaptive sampling

**Business Use Cases:**

- 100% traces; ClinicalAgent RAG spans.

**Implementation & Flow Position:** Component `Jaeger` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `WorkflowEngine` | Traces |
| 2 | `IntakeAgent` | Agent Spans |
| 3 | `ClinicalAgent` | RAG Spans |
| 4 | `PostgreSQL` | Store |

**Connection narrative:** sends to `WorkflowEngine` (Traces); sends to `IntakeAgent` (Agent Spans); sends to `ClinicalAgent` (RAG Spans); + 1 more outbound.

---

#### `Kafka`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Infrastructure |
| **Role** | Enterprise Event Bus |
| **Architecture Pattern** | Event-driven architecture; pub/sub; event sourcing for audit trail |

**Technology Stack:**

- Kafka 6 brokers
- 200+ topics
- Avro schema registry
- 3x replication

**Business Use Cases:**

- Publish PA lifecycle events (submitted, approved, denied, appealed)
- Async NotificationAgent and AuditAgent triggering
- Feed Elasticsearch event index and PostgreSQL event log

**Key Metrics:**

| Metric | Value |
|--------|-------|
| Topics | 200+ |
| Throughput | 500K events/day |
| Retention | 7 days hot |

**Implementation & Flow Position:** WorkflowEngine, ApprovalWorkflow, NotificationAgent, ClaimsService publish/consume.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `WorkflowEngine` | Event Stream |
| 2 | `DataGateway` | Data Events |
| 3 | `NotificationAgent` | Events |
| 4 | `COMAgent` | COB Events |
| 5 | `ClaimsService` | Events |
| 6 | `ApprovalWorkflow` | Event Stream |
| 7 | `Prometheus` | Metrics |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `NotificationAgent` | Consume |
| 2 | `PostgreSQL` | Event Log |
| 3 | `Elasticsearch` | Event Index |

**Connection narrative:** receives from `WorkflowEngine` (Event Stream); receives from `DataGateway` (Data Events); receives from `NotificationAgent` (Events); sends to `NotificationAgent` (Consume); sends to `PostgreSQL` (Event Log); sends to `Elasticsearch` (Event Index); + 4 more inbound.

---

#### `Keycloak`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Infrastructure |
| **Role** | Identity provider |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Keycloak OIDC SSO+2FA

**Business Use Cases:**

- OAuth2/JWT; user DB in PostgreSQL.

**Implementation & Flow Position:** Component `Keycloak` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

*No inbound connections in diagram (entry point or external sink).*

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `AuthGW` | Auth Config |
| 2 | `PostgreSQL` | User DB |

**Connection narrative:** sends to `AuthGW` (Auth Config); sends to `PostgreSQL` (User DB).

---

#### `Prometheus`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Infrastructure |
| **Role** | Metrics |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Prometheus 15-day retention

**Business Use Cases:**

- 200+ metrics; WorkflowEngine/Kafka/PostgreSQL.

**Implementation & Flow Position:** Component `Prometheus` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `Grafana` | Query |

**Outbound connections** (what this component calls):

| # | To | Label |
|---|-----|-------|
| 1 | `WorkflowEngine` | Metrics |
| 2 | `Kafka` | Metrics |
| 3 | `PostgreSQL` | Metrics |

**Connection narrative:** receives from `Grafana` (Query); sends to `WorkflowEngine` (Metrics); sends to `Kafka` (Metrics); sends to `PostgreSQL` (Metrics).

---

### Layer 2 — Gateway Groups

#### `AgentCommGWs`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Groups |
| **Role** | Tier 2 group container |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- MCP/A2A/MultiAgent/Mesh

**Business Use Cases:**

- Logical grouping of agent communication gateways.

**Implementation & Flow Position:** Component `AgentCommGWs` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | Agent Mesh |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `KongHub` (Agent Mesh).

---

#### `CoreGWs`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Groups |
| **Role** | Tier 1 group container |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- API/AI/LLM/Agent gateways

**Business Use Cases:**

- Logical grouping: APIGateway, AIGateway, LLMGateway, AgentGateway.

**Implementation & Flow Position:** Component `CoreGWs` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | Core Routing |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `KongHub` (Core Routing).

---

#### `KnowledgeGWs`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Groups |
| **Role** | Tier 3 group container |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- RAG/Knowledge/Context/Memory/VectorDB

**Business Use Cases:**

- Logical grouping of knowledge gateways.

**Implementation & Flow Position:** Component `KnowledgeGWs` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `KongHub` | RAG Control |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `KongHub` (RAG Control).

---

#### `ModelGWs`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Gateway Groups |
| **Role** | Tier 5 group container |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Model/Inference/GPU/Serving/Registry

**Business Use Cases:**

- Logical grouping of model inference gateways.

**Implementation & Flow Position:** Component `ModelGWs` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `LiteLLMRouter` | Model Selection |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `LiteLLMRouter` (Model Selection).

---

### Layer 2 — Model & Inference

#### `GPUGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Model & Inference |
| **Role** | GPU acceleration |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- NVIDIA T4

**Business Use Cases:**

- Fraud GNN inference; 2ms device affinity.

**Implementation & Flow Position:** Component `GPUGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `FraudAgent` | GPU Acceleration |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `FraudAgent` (GPU Acceleration).

---

#### `InferenceGateway`

| Attribute | Detail |
|-----------|--------|
| **Layer** | Layer 2 — Model & Inference |
| **Role** | Batch+stream inference |
| **Architecture Pattern** | See platform architecture diagram 13 |

**Technology Stack:**

- Async queue + stream

**Business Use Cases:**

- Real-time and batch LLM inference routing.

**Implementation & Flow Position:** Component `InferenceGateway` in GenAI orchestration plane.

**Inbound connections** (who calls this component):

| # | From | Label |
|---|------|-------|
| 1 | `LiteLLMRouter` | Inference |

**Outbound connections** (what this component calls):

*No outbound connections in diagram (terminal/sink node).*

**Connection narrative:** receives from `LiteLLMRouter` (Inference).

---

---

## 10. Embedded Orchestration Specifications


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### ORCHESTRATION LAYER - WORKFLOW EXECUTION PATTERNS

LangGraph DAG | Temporal Workflows | State Machine | 50K Workflows/Day

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### 🎯 LANGGRAPH WORKFLOW ENGINE (v0.2.15)

  Architecture Pattern: Supervisor Multi-Agent DAG
  Topology: 11-node Directed Acyclic Graph (DAG)
  Daily Volume: 50,000 workflows (2,500 peak/hour)
  Execution Modes: Synchronous (72%) | Asynchronous HITL (28%)

  DAG Node Structure:
  1. IntakeNode (entry point) → validates input
  2. EligibilityNode → branches: [valid → continue | invalid → deny]
  3. BenefitsNode → branches: [pa_required → continue | no_pa → auto_approve]
  4. ClinicalNode (BOTTLENECK - 8 min)
  5. PolicyNode
  6. FraudNode (parallel with BenefitsNode - 20% time savings)
  7. DecisionNode → branches: [auto → NotificationNode | hitl → ReviewQueue]
  8. NotificationNode
  9. AuditNode (async, always executes)
  10. AppealsNode (conditional - only for appeals)
  11. COMNode (conditional - only for multi-payer cases)

  Conditional Routing (8 Decision Points):
  • Point 1: Intake confidence 60 → HITL mandatory investigation
  • Point 7: Decision confidence Parallel Execution Optimization:
  • Benefits + Fraud agents run concurrently (independent)
  • Notification + Audit agents run async (non-blocking)
  • Speedup: 20% faster than sequential execution

  Graph Configuration (Python):
  ```python
  from langgraph.graph import StateGraph
  from langgraph.checkpoint.postgres import PostgresSaver

  workflow = StateGraph(state_schema=PAState)

  # Add nodes
  workflow.add_node("intake", IntakeAgent)
  workflow.add_node("eligibility", EligibilityAgent)
  workflow.add_node("benefits", BenefitsAgent)
  # ... 8 more nodes

  # Define edges (DAG topology)
  workflow.add_edge("intake", "eligibility")
  workflow.add_conditional_edges(
      "eligibility",
      route_eligibility,  # function returns "continue" or "deny"
      {"continue": "benefits", "deny": END}
  )
  workflow.add_conditional_edges(
      "benefits",
      route_benefits,
      {"continue": "clinical", "auto_approve": "notification"}
  )
  # ... 5 more conditional edges

  # Parallel execution (fan-out + fan-in)
  workflow.add_edge("eligibility", ["benefits", "fraud"])  # parallel
  workflow.add_edge(["benefits", "fraud"], "decision")    # join

  # Compile with checkpointing
  app = workflow.compile(
      checkpointer=PostgresSaver(conn_string),
      interrupt_before=["decision"],  # HITL gate
  )
  ```

STATE MACHINE (10 States + 15 Transitions)
  State Diagram:

###   DRAFT → SUBMITTED → IN_REVIEW → {APPROVED | DENIED | PENDED} → NOTIFIED


  State Definitions:
  1. DRAFT: PA request created but not submitted
  2. SUBMITTED: PA submitted to workflow engine
  3. VALIDATING: IntakeAgent processing documents
  4. IN_REVIEW: Clinical/Policy agents evaluating
  5. PENDING_INFO: Waiting for additional information
  6. HITL_REVIEW: Human review queue (28% of cases)
  7. APPROVED: Auto-approved (72%) or human-approved
  8. DENIED: Auto-denied or human-denied
  9. PENDED: Awaiting provider response
  10. NOTIFIED: Final notification sent
  11. APPEALED: Appeal workflow initiated (2% of denials)

  State Transition Matrix:
  DRAFT → SUBMITTED (user action: submit)
  SUBMITTED → VALIDATING (auto: workflow start)
  VALIDATING → IN_REVIEW (auto: intake complete)
  IN_REVIEW → APPROVED (auto: all agents approve)
  IN_REVIEW → DENIED (auto: policy violation, fraud)
  IN_REVIEW → PENDED (auto: missing info)
  IN_REVIEW → HITL_REVIEW (auto: low confidence State Persistence:
  • Storage: PostgreSQL pa_workflow_state table
  • Schema: {workflow_id, state, prev_state, transition_reason, timestamp, user_id}
  • Indexing: B-tree on workflow_id + timestamp
  • Auditing: All state transitions logged (immutable)

TEMPORAL WORKFLOWS (Durable Execution)
  Framework: Temporal.io (v1.22)
  Workflow Type: PA_Request_Workflow
  Task Queue: pa-processing-queue (100 workers)

  Workflow Configuration:
  • Execution Timeout: 30 minutes (PA SLA)
  • Run Timeout: None (can run indefinitely for HITL)
  • Task Timeout: 5 minutes per activity
  • Retry Policy:
    - Initial Interval: 1 second
    - Backoff Coefficient: 2.0
    - Maximum Attempts: 3
    - Maximum Interval: 60 seconds
    - Non-retryable Errors: [ValidationError, PolicyViolation]

  Activities (11 total, map to agents):
  1. process_intake_activity
  2. check_eligibility_activity
  3. calculate_benefits_activity
  4. evaluate_clinical_activity (longest - 8 min)
  5. check_policy_activity
  6. detect_fraud_activity
  7. make_decision_activity
  8. send_notification_activity
  9. create_audit_log_activity
  10. process_appeal_activity
  11. coordinate_benefits_activity

  Workflow Definition (TypeScript):
  ```typescript
  import { proxyActivities, sleep } from '@temporalio/workflow';

  const activities = proxyActivities({
    startToCloseTimeout: '5 minutes',
    retry: { maximumAttempts: 3 }
  });

  export async function paRequestWorkflow(input: PARequest): Promise {
    // Sequential execution
    const intake = await activities.processIntake(input);
    const eligibility = await activities.checkEligibility(intake);

    if (!eligibility.is_eligible) {
      return { decision: 'denied', reason: 'not_eligible' };
    }

    // Parallel execution (fan-out)
    const [benefits, fraud] = await Promise.all([
      activities.calculateBenefits(eligibility),
      activities.detectFraud(eligibility)
    ]);

    if (fraud.risk_score > 60) {
      await activities.routeToHITL(fraud);
      // Workflow pauses here until human review
    }

    const clinical = await activities.evaluateClinical(benefits);
    const policy = await activities.checkPolicy(clinical);
    const decision = await activities.makeDecision({clinical, policy, fraud});

    // Async notification (fire and forget)
    await activities.sendNotification(decision);
    await activities.createAuditLog(decision);

    return decision;
  }
  ```

  Workflow History:
  • Retention: 90 days
  • Events: ~150 events per workflow (all state changes)
  • Size: ~50KB per workflow history
  • Storage: PostgreSQL + Cassandra (Temporal backend)

  Heartbeat Monitoring:
  • Interval: 30 seconds (long-running activities)
  • Purpose: Detect worker crashes, resume from checkpoint
  • Activities: ClinicalAgent (8 min), AppealsAgent (10 min)

STATE MANAGER (Redis + PostgreSQL)
  Working Memory (Redis 7.0):
  • Cluster: 3 shards, 3 replicas (HA)
  • Data Structure: Hash (workflow_id → state JSON)
  • TTL: 6 hours (session expiry)
  • Operations: 500M ops/day
  • Latency: P50 State Schema (JSON in Redis):
  ```json
  {
    "workflow_id": "WF-20240115-104523-456",
    "status": "in_review",
    "created_at": "2024-01-15T10:45:23Z",
    "updated_at": "2024-01-15T10:52:15Z",
    "current_agent": "ClinicalAgent",
    "progress": {"completed_agents": 4, "total_agents": 7, "percent": 57},
    "agent_outputs": {
      "IntakeAgent": {"confidence": 0.97, "extracted_fields": {...}},
      "EligibilityAgent": {"is_eligible": true, "plan": "Gold_PPO"},
      "BenefitsAgent": {"pa_required": true, "tier": "gold"},
      "ClinicalAgent": {"in_progress": true, "started_at": "2024-01-15T10:50:00Z"}
    },
    "decision": null,
    "hitl_required": false,
    "checkpoints": ["intake_complete", "eligibility_verified", "benefits_calculated"]
  }
  ```

  Persistent Checkpoints (PostgreSQL):
  • Table: pa_workflow_checkpoints
  • Frequency: Every 30 seconds (configurable)
  • Snapshot Strategy: Full state snapshot + delta
  • Purpose: Resume from failure, audit trail
  • RPO (Recovery Point Objective): 1 minute max data loss
  • RTO (Recovery Time Objective): 5 minutes to restore

  Checkpoint Schema (PostgreSQL):
  CREATE TABLE pa_workflow_checkpoints (
    checkpoint_id UUID PRIMARY KEY,
    workflow_id VARCHAR(50) NOT NULL,
    checkpoint_name VARCHAR(100),  -- e.g., "clinical_complete"
    state_snapshot JSONB NOT NULL,  -- full workflow state
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_workflow_checkpoints ON (workflow_id, created_at DESC)
  );


### EXECUTION METRICS & MONITORING

  Latency Distribution:
  • P50 (Median): 4.2 minutes (50% complete within 4.2 min)
  • P95: 12.8 minutes (95% complete within 12.8 min)
  • P99: 28.5 minutes (99% complete within 28.5 min)
  • SLA: 30 minutes (99.2% compliance)

  Throughput:
  • Daily Workflows: 50,000 (2,083/hour avg)
  • Peak Throughput: 2,500/hour (9-11 AM weekday peak)
  • Concurrency: 500 workflows in-flight simultaneously
  • Worker Pool: 100 workers × 5 concurrent tasks = 500 slots

  Success Metrics:
  • Success Rate: 96.2% (first-pass completion)
  • Retry Rate: 3.8% (automatic retries)
  • Human Intervention: 28% require HITL review
  • Failure Rate: Bottleneck Analysis:
  • ClinicalAgent: 8 min (53% of total time) ★ PRIMARY BOTTLENECK
  • PolicyAgent: 2.5 min (17%)
  • IntakeAgent: 2 min (13%)
  • All other agents: Optimization Strategies:
  1. Cache Frequent Guidelines: 40% RAG cache hit → save 3.2 min
  2. Parallel Execution: Benefits + Fraud → save 20%
  3. Speculative Execution: Start next agent on high confidence
  4. GPU Acceleration: Embedding generation 2x faster
  5. Workflow Batching: Batch similar PAs for efficiency


### ERROR RECOVERY & RESILIENCE

  Retry Policy (Exponential Backoff):
  • Attempt 1: Immediate retry (1-second delay)
  • Attempt 2: 2-second delay
  • Attempt 3: 4-second delay
  • Max Attempts: 3 total
  • Success Rate: 95% recover within 3 attempts

  Fallback Mechanisms:
  1. Agent Failure: Route to HITL review queue
  2. Database Timeout: Use cached data (Redis)
  3. External API Failure: Circuit breaker (stop calling)
  4. LLM Timeout: Retry with shorter context window
  5. Workflow Timeout: Auto-escalate to HITL (SLA breach)

  Circuit Breaker Pattern:
  • Failure Threshold: 5 consecutive failures
  • Open State: Stop calling failing service for 60 seconds
  • Half-Open State: Try 1 request to test recovery
  • Closed State: Resume normal operations

  Graceful Degradation:
  • RAG Unavailable: Use LLM without context (lower accuracy)
  • Fraud Agent Down: Skip fraud check (log warning)
  • Policy Service Down: Use cached policies (24-hour cache)
  • Redis Down: Fallback to PostgreSQL (slower)


### WORKFLOW OBSERVABILITY

  Distributed Tracing (Jaeger):
  • Trace ID: Unique per workflow (propagated through all services)
  • Spans: 50-100 spans per workflow (all agent calls)
  • Critical Path: Visualize bottlenecks in DAG
  • Flamegraph: Identify slow agents

  Metrics (Prometheus):
  • Workflow Duration: Histogram with percentiles
  • Agent Latency: Gauge per agent type
  • Workflow Throughput: Counter (workflows/sec)
  • Error Rate: Counter by error type
  • Queue Depth: Gauge (pending workflows)

  Alerting (PagerDuty):
  • P95 Latency >25 min: Warning (approaching SLA)
  • Success Rate 1000: Warning (scaling needed)
  • Workflow Failures >1%: Critical (systemic issue)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


---

## 11. Embedded Agent Specifications (All 17)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### 11 AI AGENTS - COMPLETE TECHNICAL SPECIFICATIONS

LangGraph Supervisor Pattern | Multi-Model Architecture | 385K Daily Executions

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### 🎯 AGENT ORCHESTRATION ARCHITECTURE

  LangGraph Supervisor Pattern (v0.2.15):
  • Topology: 11-node Directed Acyclic Graph (DAG)
  • Execution Mode: Sequential primary path + parallel branches
  • State Management: Global state (Redis) + per-agent checkpoints
  • Error Recovery: Automatic retry (3 attempts) + HITL escalation
  • Conditional Routing: 8 decision points based on confidence scores
  • Parallelization: Benefits + Fraud agents run concurrently (20% time savings)

  Agent Execution Pipeline:
  IntakeAgent (2 min) → EligibilityAgent (15 sec) → BenefitsAgent (20 sec) →
  ClinicalAgent (8 min ★ BOTTLENECK) → PolicyAgent (2.5 min) → FraudAgent (45 sec) →
  DecisionAgent (30 sec) → {72% Auto → NotificationAgent | 28% HITL → ReviewQueue}

  Performance Metrics:
  • Total Pipeline: 15 min average (30-min SLA, 99.2% compliance)
  • Success Rate: 96.2% first-pass | 3.8% require retry/HITL
  • Token Efficiency: 47,523 avg tokens/case ($1.04 cost)
  • Throughput: 50,000 requests/day (2,500 peak/hour)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


## AGENT 1: INTAKE AGENT - Document Processing & Classification

  Model: GPT-4o Vision (gpt-4o-2024-05-13)
  Primary Function: OCR extraction, document classification, field validation

  Token Usage:
  • Average Input: 15,000 tokens (includes image encoding)
  • Average Output: 2,000 tokens (structured JSON)
  • Cost per execution: $0.285 ($0.015/1K input + $0.060/1K output)

  Performance:
  • Average Latency: 2 minutes (120 seconds)
  • P95 Latency: 3.5 minutes
  • Accuracy: 97% field extraction accuracy
  • Document Types: 15 form templates (UB-04, CMS-1500, HCFA, custom)

  Tools & Integrations:
  • DocumentGateway: Azure Form Recognizer (98.5% OCR accuracy)
  • BlobStorage: Store original PDF/DICOM/TIFF (10TB storage)
  • PostgreSQL: Save extracted metadata (pa_documents table)
  • AgentRegistryGateway: Load agent configuration v2.1.0
  • ContextGateway: Initialize session context (6-hour TTL)

  Prompt Engineering:
  • Template Variants: 5 A/B tested templates
  • Current Winner: "medical_form_v2.3" (98% accuracy)
  • System Prompt: 2,500 tokens (includes examples, schema)
  • Few-shot Examples: 3 annotated examples per document type

  Error Handling:
  • Low Confidence (5 min): Auto-escalate to HITL queue
  • Field Validation: JSON schema validation + business rules

  Output Schema:
  {
    "document_type": "prior_auth_request",
    "patient": {"name": str, "dob": date, "member_id": str},
    "provider": {"npi": str, "name": str, "specialty": str},
    "diagnosis": {"icd10": [str], "description": str},
    "procedure": {"cpt": str, "description": str, "quantity": int},
    "confidence_scores": {"overall": float, "per_field": dict},
    "extracted_text": str
  }


## AGENT 2: ELIGIBILITY AGENT - Member Verification

  Model: GPT-3.5 Turbo (gpt-3.5-turbo-0125)
  Primary Function: Member lookup, plan verification, effective date validation

  Token Usage:
  • Average Input: 1,500 tokens
  • Average Output: 500 tokens
  • Cost per execution: $0.003 (very low cost, high volume)

  Performance:
  • Average Latency: 15 seconds
  • P95 Latency: 25 seconds
  • Accuracy: 99% (simple rule-based validation)
  • Cache Hit Rate: 85% (Redis cache)

  Tools & Integrations:
  • ToolGateway: member_lookup tool (gRPC to MemberService)
  • DataAccessGateway: PostgreSQL query with cache layer
  • MemoryGateway: Episodic memory for repeat members
  • TokenMgmtGateway: Track token usage (rate limiting)

  Validation Logic:
  1. Member ID exists in database (MemberService)
  2. Plan is active on service date
  3. Member has PA benefit (not all plans require PA)
  4. Provider is in-network (or out-of-network PA allowed)
  5. No duplicate PA request in last 30 days

  Cache Strategy:
  • Key: member_id + service_date
  • TTL: 24 hours (eligibility changes daily)
  • Invalidation: On member update events (Kafka trigger)
  • Hit Rate: 85% (significant cost savings)

  Error Scenarios:
  • Member Not Found: Auto-deny with notification
  • Inactive Plan: Check termination date, offer alternatives
  • No PA Benefit: Auto-approve (no PA required)
  • System Error: Fallback to manual lookup (HITL)


## AGENT 3: BENEFITS AGENT - Tier Determination & Network Validation

  Model: GPT-4o (gpt-4o-2024-05-13)
  Primary Function: Benefit tier calculation, network status, formulary lookup

  Token Usage:
  • Average Input: 8,000 tokens (complex benefit rules)
  • Average Output: 3,000 tokens (detailed breakdown)
  • Cost per execution: $0.300

  Performance:
  • Average Latency: 20 seconds
  • P95 Latency: 35 seconds
  • Accuracy: 95% tier determination
  • Complexity: 12 decision trees evaluated

  Tools & Integrations:
  • PolicyGateway: OPA rule evaluation (50+ rules)
  • FunctionCallingGateway: tier_calculator, cost_estimator
  • KnowledgeGateway: Plan ontology (Neo4j graph)
  • BenefitsConfigService: Tier structures (Bronze/Silver/Gold/Platinum)
  • NetworkService: In/out-of-network validation
  • FormularyService: Drug coverage tiers (if medication PA)

  Decision Trees:
  1. Plan Type (HMO, PPO, EPO, POS) → Different PA requirements
  2. Service Category (Medical, Pharmacy, DME, Home Health)
  3. Network Status (In-network Tier 1/2, Out-of-network)
  4. Cost Sharing (Copay, Coinsurance, Deductible)
  5. Benefit Limits (Annual max, visit limits)
  6. Prior Authorization Requirements (always, sometimes, never)
  7. Step Therapy (required prior treatments)
  8. Quantity Limits (days supply, dose restrictions)
  9. Age/Gender Restrictions
  10. Medical Necessity Criteria (clinical guidelines)
  11. Experimental/Investigational Exclusions
  12. Alternative Treatments Available

  Output Structure:
  {
    "tier": "gold",
    "network_status": "in_network_tier1",
    "cost_share": {"copay": 30, "coinsurance": 0.20, "deductible_remaining": 500},
    "pa_required": true,
    "pa_criteria": "medical_necessity",
    "alternative_options": [{"cpt": "99214", "lower_cost": true}],
    "confidence": 0.94
  }


## AGENT 4: CLINICAL AGENT - Medical Necessity Review ★ BOTTLENECK

  Model: GPT-4o + Hybrid RAG (gpt-4o-2024-05-13)
  Primary Function: Clinical guideline evaluation, medical necessity determination

  Token Usage:
  • Average Input: 20,000 tokens (RAG context + prompt)
  • Average Output: 8,000 tokens (detailed clinical reasoning)
  • Cost per execution: $0.780 (highest cost agent)

  Performance (BOTTLENECK - 53% of total time):
  • Average Latency: 8 minutes (480 seconds)
    ├─ RAG Retrieval: 20 queries × 135ms = 2.7 sec (0.6%)
    ├─ Context Preparation: 5 seconds (1%)
    └─ LLM Inference: 472 seconds (98.4%) ★ TRUE BOTTLENECK
  • P95 Latency: 12 minutes
  • P99 Latency: 18 minutes
  • Accuracy: 96% medical necessity determination
  • Overturn Rate: 4% by human clinical reviewers

  RAG Integration (20 retrieval queries per request):
  • RAGGateway: Hybrid retrieval orchestration (45ms)
  • VectorDBGateway: Milvus similarity search (10M embeddings)
  • KnowledgeGateway: Neo4j graph traversal (500K nodes)
  • MemoryGateway: Semantic memory (similar cases)
  • GuardrailGateway: Hallucination detection (99.9% safe)

  Clinical Guidelines Consulted:
  • MCG (Milliman Care Guidelines): 80% of cases
  • InterQual: 60% of cases (dual validation)
  • Hayes Technology Assessment: 15% of cases (new procedures)
  • CMS LCD/NCD: 25% of cases (Medicare policies)
  • Specialty Society Guidelines: 40% of cases (NCCN, AHA, etc.)
  • Internal Policies: 100% of cases (payer-specific)

  Evaluation Criteria:
  1. Diagnosis supports requested procedure (ICD-10 ↔ CPT mapping)
  2. Clinical guidelines recommend procedure for diagnosis
  3. Conservative treatments attempted first (step therapy)
  4. No contraindications present (drug interactions, comorbidities)
  5. Provider qualifications adequate (board certified, etc.)
  6. Appropriate setting of care (inpatient vs. outpatient)
  7. Quantity/frequency reasonable (evidence-based dosing)
  8. Expected outcomes justify risk/cost (benefit-risk analysis)

  RAG Query Types (20 queries):
  • 8 queries: Vector search ("diabetes management CPT 99213")
  • 6 queries: Keyword search ("ICD-10 E11.9 prior authorization")
  • 4 queries: Graph queries ("procedure → diagnosis relationships")
  • 2 queries: Similar case precedents (episodic memory)

  Guardrails & Safety:
  • Citation Required: All clinical claims must cite sources
  • Hallucination Detection: Guardrails AI validates medical facts
  • Confidence Threshold: Optimization Strategies (to reduce 8-min bottleneck):
  • Cache Frequent Guidelines: 40% hit rate (saves 3.2 min)
  • Parallel RAG Execution: Already implemented (async I/O)
  • GPT-4o Turbo: Testing 20% latency reduction
  • Streaming Responses: SSE for progressive results
  • Speculative Execution: Start DecisionAgent early on high confidence


## AGENT 5: POLICY AGENT - Regulatory Compliance & Rules Engine

  Model: Claude 3.5 Sonnet (claude-3-5-sonnet-20240620)
  Primary Function: Policy interpretation, compliance validation, rule evaluation

  Token Usage:
  • Average Input: 12,000 tokens (complex policy documents)
  • Average Output: 5,000 tokens (policy analysis)
  • Cost per execution: $0.111 (Claude cheaper than GPT-4o)

  Performance:
  • Average Latency: 2.5 minutes (150 seconds)
  • P95 Latency: 4 minutes
  • Accuracy: 94% policy interpretation
  • Rules Evaluated: 50+ policy rules per request

  Tools & Integrations:
  • PolicyGateway: OPA (Open Policy Agent) Rego language
  • ComplianceGateway: HIPAA/SOC2 validation
  • PromptGateway: LangSmith A/B testing (5 prompt variants)
  • EvaluationGateway: Quality metrics tracking
  • PolicyService: 100K+ policy documents (PostgreSQL)

  Policy Types Evaluated:
  1. Medical Policy: Clinical criteria, evidence requirements
  2. Drug Policy: Formulary tiers, step therapy, quantity limits
  3. Administrative Policy: Timely filing, claim edits
  4. Regulatory Policy: State mandates, federal requirements
  5. Contract Policy: Provider agreements, reimbursement rules
  6. Internal Policy: Payer-specific guidelines

  OPA Policy Engine (50+ Rules):
  • Rule Language: Rego (declarative policy language)
  • Evaluation Speed: Compliance Frameworks:
  • HIPAA: Protected Health Information (PHI) handling
  • SOC2: Security controls, audit logging
  • NCQA: Quality standards (HEDIS measures)
  • State Mandates: 50 state variations (e.g., NY prior auth reform)
  • CMS Requirements: Medicare/Medicaid policies

  Claude 3.5 Advantages:
  • Long Context: 200K tokens (vs. GPT-4o 128K)
  • Reasoning: Superior logical reasoning for complex policies
  • Cost: 5x cheaper than GPT-4o ($0.003 vs. $0.015 input)
  • Accuracy: 94% on policy interpretation tasks


## AGENT 6: FRAUD AGENT - Anomaly Detection & Risk Scoring

  Model: Custom Graph Neural Network (PyTorch)
  Primary Function: Fraud pattern detection, risk scoring, graph analysis

  Performance:
  • Average Latency: 45 seconds
  • P95 Latency: 75 seconds
  • Precision: 94% (low false positives)
  • Recall: 98% (catches most fraud)
  • F1 Score: 0.96 (balanced precision/recall)

  Tools & Integrations:
  • RiskMgmtGateway: Anomaly detection algorithms
  • GPUGateway: NVIDIA T4 GPU acceleration
  • KnowledgeGateway: Neo4j fraud pattern graphs
  • DataGovernanceGateway: PII masking, audit logging
  • ClaimsService: Historical claim data (150M claims)

  Graph Neural Network Architecture:
  • Framework: PyTorch Geometric (PyG)
  • Node Types: Patient, Provider, Procedure, Diagnosis, Facility
  • Edge Types: Treated_by, Diagnosed_with, Performed_at, Referred_by
  • Graph Size: 500K nodes, 2M edges
  • Embedding Dimension: 128-dim node embeddings
  • Layers: 3 Graph Convolutional (GCN) layers
  • Training: Supervised learning on 100K labeled fraud cases

  Fraud Patterns Detected:
  1. Billing Schemes:
     • Upcoding: Billing higher-level service than performed
     • Unbundling: Separating bundled procedures
     • Duplicate Billing: Same service billed multiple times
  2. Network Patterns:
     • Kickback Schemes: Suspicious referral patterns
     • Phantom Billing: Services never rendered
     • Patient Steering: Unusual patient clustering
  3. Statistical Anomalies:
     • Outlier Volumes: Provider billing 3x peer average
     • Unusual Patterns: Weekend surgeries, off-hours procedures
     • Geographic Anomalies: Patient travel >100 miles

  Risk Scoring (0-100 scale):
  • 0-30: Low Risk → Auto-approve (95% of cases)
  • 31-60: Medium Risk → Enhanced review (4% of cases)
  • 61-80: High Risk → HITL mandatory review (0.8% of cases)
  • 81-100: Critical Risk → Investigate + deny (0.2% of cases)

  Neo4j Graph Queries:
  • Pattern: MATCH (p:Provider)-[:TREATED]->(pat:Patient)-[:DIAGNOSED_WITH]->(d:Diagnosis)
  • Centrality: Calculate betweenness centrality for fraud hubs
  • Community Detection: Identify suspicious provider clusters
  • Path Finding: Shortest path between suspicious entities

  Model Monitoring:
  • Daily Retraining: Incremental learning on new fraud cases
  • Drift Detection: Monitor prediction distribution shifts
  • A/B Testing: Shadow mode for new model versions
  • Explainability: SHAP values for risk score attribution


## AGENT 7: DECISION AGENT - Final Aggregation & HITL Routing

  Model: GPT-4o (gpt-4o-2024-05-13)
  Primary Function: Aggregate all agent outputs, make final decision, route to HITL

  Token Usage:
  • Average Input: 10,000 tokens (all prior agent outputs)
  • Average Output: 2,000 tokens (final decision + reasoning)
  • Cost per execution: $0.270

  Performance:
  • Average Latency: 30 seconds
  • P95 Latency: 50 seconds
  • Accuracy: 96% decision correctness
  • Overturn Rate: 3% by human reviewers (very low)

  Decision Logic:
  1. Aggregate Confidence Scores:
     • IntakeAgent: Field extraction confidence
     • ClinicalAgent: Medical necessity confidence (weighted 50%)
     • PolicyAgent: Compliance confidence (weighted 30%)
     • FraudAgent: Risk score (weighted 20%)
  2. Apply Decision Rules:
     • All confidences >0.85 AND risk 30 → HITL review (28%)
     • Clinical confidence HITL Routing (28% of cases):
  • Low Confidence (30): 5% of HITL cases
  • All Denials: 10% of HITL cases (100% human review)
  • High Cost (>$50K): 3% of HITL cases
  • Complex Clinical: 12% of HITL cases
  • Appeal Cases: 2% of HITL cases
  • Random Sample: 10% of HITL cases (quality monitoring)
  • Policy Override: 3% of HITL cases

  Tools & Integrations:
  • HITLGateway: Queue routing logic (Drools rules)
  • ApprovalGateway: Workflow trigger (Temporal)
  • AgentGovernanceGateway: Permission checks (RBAC)
  • MemoryGateway: Store decision + reasoning (audit trail)

  Output Structure:
  {
    "decision": "approved",  // approved | denied | pended
    "confidence": 0.94,
    "reasoning": "Medical necessity supported by MCG guidelines...",
    "agent_scores": {
      "clinical": 0.96,
      "policy": 0.92,
      "fraud": 0.05
    },
    "hitl_required": false,
    "estimated_cost": 1250.00,
    "citations": ["MCG A-0123", "Policy MED-456"]
  }


## AGENT 8: NOTIFICATION AGENT - Multi-Channel Communication

  Model: GPT-3.5 Turbo (gpt-3.5-turbo-0125)
  Primary Function: Generate notifications, multi-channel dispatch

  Token Usage:
  • Average Input: 2,000 tokens (decision summary)
  • Average Output: 800 tokens (personalized message)
  • Cost per execution: $0.004 (very low cost)

  Performance:
  • Average Latency: 1 minute (60 seconds)
  • P95 Latency: 90 seconds
  • Delivery Rate: 99.5%
  • Multi-channel: Email (100%), SMS (80%), Portal (100%), Slack (20%)

  Tools & Integrations:
  • SaaSConnectorGateway: Slack, Microsoft Teams integration
  • DataGateway: Kafka event publishing
  • UsageAnalyticsGateway: Track notification engagement
  • BlobStorage: Store notification templates

  Notification Channels:
  1. Email: SendGrid API (primary channel)
     • Templates: 25 HTML templates
     • Personalization: Merge tags, dynamic content
     • Tracking: Open rate 65%, click rate 25%
  2. SMS: Twilio API (urgent notifications)
     • Character Limit: 160 chars (concise messaging)
     • Opt-in Required: TCPA compliance
     • Delivery: 99.9% within 10 seconds
  3. Portal Notification: In-app messages
     • Real-time: WebSocket push notifications
     • Persistent: Notification center (30-day retention)
     • Read Receipts: Track user engagement
  4. Slack/Teams: Provider notifications
     • Channels: #pa-approvals, #pa-denials, #pa-pending
     • Buttons: Quick actions (view details, appeal)
     • Mentions: @provider for urgent cases

  Message Templates (25 variants):
  • Approval: Simple, complex (with conditions)
  • Denial: With appeal instructions, alternative options
  • Pended: Request additional information
  • HITL: Under human review (SLA countdown)
  • Appeal Decision: Approval, denial, partial approval

  Personalization:
  • Recipient Name, Member Name, Provider Name
  • Service Details: CPT code, description, cost estimate
  • Decision Reasoning: Simplified for patient understanding
  • Next Steps: What to do next (appeal, schedule, etc.)
  • Contact Information: Help desk, appeals email


## AGENT 9: AUDIT AGENT - Compliance Logging & Forensics

  Model: GPT-4o (gpt-4o-2024-05-13)
  Primary Function: Generate audit logs, compliance reporting, lineage tracking

  Token Usage:
  • Average Input: 5,000 tokens (full PA workflow)
  • Average Output: 2,000 tokens (audit summary)
  • Cost per execution: $0.195

  Performance:
  • Latency: Real-time (async processing)
  • Processing: 50,000 events/day
  • Storage: 400GB Elasticsearch index
  • Retention: 7 years (HIPAA requirement)

  Tools & Integrations:
  • AuditGateway: Immutable append-only log
  • ComplianceGateway: HIPAA/SOC2 validation
  • DataGovernanceGateway: Data lineage tracking
  • ObservabilityGateway: Metrics, traces, logs
  • PostgreSQL: Structured audit records
  • Elasticsearch: Full-text search, analytics

  Audit Events Captured:
  1. User Actions:
     • Login/logout events
     • PA submission, modification, cancellation
     • Human review actions (approve, deny, pend)
     • Document access (PHI viewing)
  2. System Actions:
     • Agent executions (start, complete, error)
     • Decision changes (auto → manual override)
     • Data modifications (before/after snapshots)
     • API calls (external integrations)
  3. Security Events:
     • Failed authentication attempts
     • Unauthorized access attempts
     • Permission changes (role assignments)
     • Data exports (bulk downloads)

  Audit Log Structure:
  {
    "@timestamp": "2024-01-15T10:45:23.456Z",
    "event_id": "EVT-20240115-104523-456",
    "event_type": "pa_decision",
    "user": {"id": "U12345", "email": "user@example.com", "roles": ["pa_coordinator"]},
    "patient_id_hash": "sha256:abc123...",  // PII protected
    "action": "approve",
    "agent": "DecisionAgent",
    "confidence": 0.94,
    "before": {"status": "in_review"},
    "after": {"status": "approved"},
    "ip_address": "192.168.1.100",
    "compliance": ["HIPAA", "SOC2"],
    "retention_date": "2031-01-15"
  }

  Compliance Reporting:
  • HIPAA Audits: Quarterly reports to compliance officer
  • SOC2 Evidence: Continuous control monitoring
  • State Reporting: Prior auth metrics (denial rates, timeliness)
  • Internal Dashboards: Real-time KPI tracking


## AGENT 10: APPEALS AGENT - Denial Review & Reconsideration

  Model: GPT-4o (gpt-4o-2024-05-13)
  Primary Function: Process appeals, re-evaluate denials, track overturn rates

  Token Usage:
  • Average Input: 15,000 tokens (original PA + new evidence)
  • Average Output: 6,000 tokens (appeal determination)
  • Cost per execution: $0.585

  Performance:
  • Average Latency: 10 minutes (detailed review)
  • Appeal Volume: 2% of denials (1,000 appeals/day)
  • Overturn Rate: 40% of appeals approved
  • SLA: 30-day review window (95% compliance)

  Appeal Process:
  1. Intake: Receive appeal request + new clinical evidence
  2. Re-review: Re-run ClinicalAgent + PolicyAgent with new evidence
  3. Peer Review: Optional clinical peer-to-peer discussion
  4. Determination: Approve, partial approve, uphold denial
  5. Notification: Detailed explanation of appeal decision

  Tools & Integrations:
  • All original agent tools (full re-evaluation)
  • HITLGateway: Route complex appeals to medical director
  • ApprovalGateway: Multi-level approval for overturns
  • AuditGateway: Track all appeal decisions (compliance)

  Appeal Categories:
  • Clinical Appeals: New evidence (test results, specialist opinion)
  • Administrative Appeals: Timely filing, incorrect coding
  • Experimental Appeals: Request for coverage of investigational treatment
  • Network Appeals: Out-of-network provider necessity

  Overturn Analysis:
  • 40% Approved: New clinical evidence supported medical necessity
  • 30% Partial Approval: Reduced quantity or alternative approved
  • 30% Upheld Denial: Insufficient evidence or policy exclusion


## AGENT 11: COM AGENT - Coordination of Benefits

  Model: GPT-4o (gpt-4o-2024-05-13)
  Primary Function: Multi-payer coordination, primary/secondary insurance determination

  Token Usage:
  • Average Input: 18,000 tokens (multiple payer policies)
  • Average Output: 7,000 tokens (COB determination)
  • Cost per execution: $0.690 (complex multi-payer logic)

  Performance:
  • Average Latency: 5 minutes (external API calls)
  • COB Cases: 15% of all PA requests (7,500/day)
  • Accuracy: 92% (complex cross-payer logic)
  • External API Calls: 3-5 per case (other payers)

  Tools & Integrations:
  • A2AGateway: Communicate with other insurance agents
  • WorkflowGateway: Sub-workflow orchestration
  • ContextGateway: Multi-payer context management
  • ProviderService: Multi-payer network lookup
  • External APIs: Real-time eligibility checks (270/271 EDI)

  COB Scenarios:
  1. Medicare + Medicaid (dual eligible)
  2. Parent plans (dependent children covered by both)
  3. Spouse coverage (birthday rule determination)
  4. Auto insurance + health insurance (accident cases)
  5. Workers' compensation + health insurance

  Primary Payer Determination:
  • Birthday Rule: Parent with earlier birthday = primary
  • Active/Inactive: Active plan pays before retiree plan
  • Court Order: Divorce decree specifies primary
  • Medicare Secondary Payer: Medicare pays second if working

  External Integration:
  • Real-time Eligibility: 270/271 X12 transactions
  • API Timeout: 30 seconds per payer call
  • Fallback: Manual COB form if API fails
  • Caching: Store COB determination for 90 days


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### AGENT COLLABORATION PATTERNS

  Sequential Dependencies:
  • Intake → Eligibility → Benefits → Clinical → Policy → Fraud → Decision
  • Each agent builds on previous agent outputs
  • State passed via Redis global state + Temporal workflow

  Parallel Execution (20% time savings):
  • Benefits + Fraud agents run concurrently (independent)
  • Notification + Audit agents run async (non-blocking)

  Conditional Routing (8 decision points):
  1. Intake confidence 60 → HITL mandatory (investigate)
  7. Decision confidence Error Recovery:
  • Retry: 3 attempts with exponential backoff (1s, 2s, 4s)
  • Fallback: Route to HITL on persistent failures
  • Circuit Breaker: Stop calling failing external APIs
  • Graceful Degradation: Use cached data if DB unavailable


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### Agent Layer Summary Note

AI AGENT FABRIC LAYER - LAYER 4 (11 Specialized Agents)
  Execution Metrics:
  • Daily executions: 385,000 (7 agents/case avg)
  • Success rate: 96.2% | Failure: 3.8%
  • Avg response: 1.2s - 8.3s per agent
  • Avg tokens/case: 47,523 (31K in, 16K out)
  • Daily LLM cost: $52,000 (~$1.04/req)
  Model Distribution:
  • GPT-4o: Intake, Clinical, Decision (50%)
  • Claude 3.5 Sonnet: Policy, Appeals (25%)
  • GPT-3.5 Turbo: Eligibility, Benefits (20%)
  • Custom ML: Fraud Detection (5%)
  Key Features:
  • Confidence scoring: 0-1.0 scale
  • Tool calling: MCP integration
  • Safety guardrails: Hallucination detection
  • Error recovery: 3-attempt retry logic

### NewComponents_Complete


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### NEW PA-SPECIFIC AGENTS (6) - REGULATORY COMPLIANCE & INDUSTRY STANDARDS

Expedited | Step Therapy | Medical Director | Retrospective | Registry | Doc Request

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


🚨 AGENT 12: EXPEDITED/URGENT PA AGENT - Regulatory Fast-Track

  PURPOSE: CMS-mandated separate processing for urgent/expedited PA requests


###   TECHNICAL SPECIFICATIONS:

  ├─ Model: GPT-4o (same as standard, prioritized queue)
  ├─ Latency: Target 2 hours (vs. 15 min standard)
  ├─ Volume: 7,500 urgent PAs/day (15% of total 50K/day)
  ├─ SLA: 72 hours regulatory (42 CFR 438.210)
  ├─ Trigger Keywords: "emergency", "urgent", "stat", "life-threatening"
  └─ Auto-Escalation: 24-hour mark → medical director alert


###   WORKFLOW INTEGRATION:

  ├─ 1. Intake Detection: IntakeAgent flags urgent keywords in provider notes
  ├─ 2. Routing Logic: WorkflowEngine routes to ExpeditedAgent (priority queue)
  ├─ 3. Parallel Processing: Run all agents concurrently (vs. sequential)
  │  ├─ Eligibility + Benefits + Clinical run in parallel (save 10 min)
  │  └─ Policy + Fraud run during Clinical RAG latency (no added time)
  ├─ 4. Auto-Approval Bias: Lower denial threshold (85% vs. 72% auto-approve)
  ├─ 5. HITL Fast-Track: 24/7 on-call medical director (vs. 8am-6pm standard)
  └─ 6. Notification Priority: SMS + Email + Portal (vs. email-only)


###   REGULATORY REQUIREMENTS:

  ├─ Federal: 72-hour decision (42 CFR 438.210(d)(1))
  ├─ State Variance: California 24hr, Texas 24hr, New York 72hr
  ├─ Denial Process: Must offer expedited appeals (24-hour resolution)
  └─ Audit: State regulators track expedited processing compliance


###   KEY METRICS:

  ├─ Detection Accuracy: 98% keyword match (manual review on edge cases)
  ├─ Processing Time: P50 1.5hr | P95 4hr | P99 12hr (well under 72hr SLA)
  ├─ Auto-Approval Rate: 85% (vs. 72% standard, less conservative)
  ├─ Overturn Rate: 3% (vs. 4% standard, slightly higher risk tolerance)
  └─ Cost: $0.92/request (18% premium for expedited handling)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💊 AGENT 13: STEP THERAPY COMPLIANCE AGENT - Drug PA Protocols

  PURPOSE: Validate step therapy requirements (try cheaper drugs first)


###   TECHNICAL SPECIFICATIONS:

  ├─ Model: GPT-4o + Rule Engine (OPA for deterministic logic)
  ├─ Latency: 30 seconds (fast, mostly rule-based)
  ├─ Volume: 20,000 drug PAs/day (40% of total 50K/day)
  ├─ Tools: claims_lookup (check prior fills), formulary_check (tier validation)
  └─ Integration: NCPDP SCRIPT 10.6 (pharmacy PA standard)


###   STEP THERAPY LOGIC:

  ├─ 1. Identify Drug Request: Extract NDC code from PA (11-digit identifier)
  ├─ 2. Check Formulary Tier: Call FormularyService → identify tier (1-6)
  ├─ 3. Determine Step Requirements:
  │  ├─ Tier 1-2: No step therapy (generic/preferred brand)
  │  ├─ Tier 3: Require 1 prior drug (30-day supply)
  │  ├─ Tier 4-5: Require 2 prior drugs (60-day supply each)
  │  └─ Tier 6 (Specialty): Require 3 prior drugs + specialist consult
  ├─ 4. Claims History Check: Query last 12 months for NDC codes
  ├─ 5. Validate Compliance:
  │  ├─ Found prior fills → Check duration (30/60 days met?)
  │  ├─ Found failure documentation → Check "tried and failed" notes
  │  └─ Clinical exception criteria → Check contraindications, allergies
  └─ 6. Decision: Approve if compliant, Deny with required steps if not

  EXCEPTION CRITERIA (Auto-Approve without Step):
  ├─ • Prior authorization on file (within 365 days, same drug)
  ├─ • Allergy to step therapy drugs (documented in medical record)
  ├─ • Contraindication (drug interaction, comorbidity)
  ├─ • Previous trial documented (claims or provider notes)
  ├─ • Grandfathered patient (already on drug, changing formulary)
  └─ • Emergency/urgent situation (override step therapy)


###   KEY METRICS:

  ├─ Accuracy: 96% step therapy validation (vs. 92% manual)
  ├─ Auto-Approval: 55% (met step requirements or exception)
  ├─ Denial Rate: 35% (step therapy not met, provide guidance)
  ├─ Pend Rate: 10% (unclear claims history, manual review)
  ├─ Appeal Success: 30% of denials overturned (provider submits proof)
  └─ Cost Savings: $4.2M/month (generic utilization increased 12%)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍⚕️ AGENT 14: MEDICAL DIRECTOR REVIEW AGENT - Peer-to-Peer Coordination

  PURPOSE: Automate peer-to-peer review scheduling for complex denials


###   TECHNICAL SPECIFICATIONS:

  ├─ Model: GPT-4o (clinical summary generation)
  ├─ Latency: Async (2-day average turnaround)
  ├─ Volume: 1,400 peer-to-peer reviews/day (10% of 14K denials)
  ├─ Integration: Calendly API (scheduling), Microsoft Teams (video calls)
  └─ Trigger: DecisionAgent denial + provider requests peer-to-peer


###   WORKFLOW:

  ├─ 1. Trigger Detection: Provider clicks "Request Peer-to-Peer" in portal
  ├─ 2. Clinical Summary Generation:
  │  ├─ Extract key facts: diagnosis, requested procedure, denial reason
  │  ├─ RAG lookup: Find similar approved cases, guideline conflicts
  │  ├─ Generate 1-page summary (GPT-4o, 500 tokens)
  │  └─ Cite specific guideline sections (medical director prep)
  ├─ 3. Specialty Matching: Match provider specialty to medical director
  │  ├─ Cardiology → Dr. Smith (board-certified cardiologist)
  │  ├─ Oncology → Dr. Jones (oncology fellowship)
  │  └─ Fallback: General internal medicine (if no specialty match)
  ├─ 4. Scheduling: Calendly API → propose 3 time slots (48-hour window)
  ├─ 5. Call Coordination: Teams link sent to both parties, auto-record
  ├─ 6. Outcome Tracking:
  │  ├─ Overturn → Update PA decision, log reasoning
  │  ├─ Upheld → Provider can appeal to IRO (independent review)
  │  └─ Partial → Approve alternative procedure (e.g., MRI vs. PET scan)
  └─ 7. Learning Loop: Overturn cases fed to ClinicalAgent retraining


###   KEY METRICS:

  ├─ Scheduling Success: 95% scheduled within 48 hours
  ├─ Completion Rate: 88% calls completed (12% provider no-show)
  ├─ Overturn Rate: 40% denials overturned after peer-to-peer
  ├─ Partial Approval: 25% (alternative approved)
  ├─ Upheld: 35% denial confirmed
  ├─ Medical Director Time Savings: 15 min/call (vs. 45 min manual prep)
  └─ Provider Satisfaction: 4.2/5 stars (reduced friction)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏥 AGENT 15: RETROSPECTIVE REVIEW AGENT - Post-Service PA Validation

  PURPOSE: Validate medical necessity for emergency services rendered before PA


###   TECHNICAL SPECIFICATIONS:

  ├─ Model: GPT-4o + RAG (same as ClinicalAgent)
  ├─ Latency: Async (5-day average, 30-day SLA)
  ├─ Volume: 2,500 retrospective PAs/day (5% of total)
  ├─ Triggers: ER admissions, observation stays, urgent surgeries
  └─ Integration: Claims feed (UB-04, HCFA-1500 post-service claims)


###   VALIDATION CRITERIA:

  ├─ 1. Emergency Necessity: Was PA requirement waived appropriately?
  │  ├─ Life-threatening condition (MI, stroke, trauma)
  │  ├─ Severe pain (pain scale >7, intractable)
  │  ├─ Sudden symptom onset (Appropriate Setting: Could care be delivered outpatient?
  │  ├─ Observation vs. inpatient (2-midnight rule)
  │  ├─ Ambulatory surgery feasible? (same-day discharge)
  │  └─ Telemedicine alternative? (virtual urgent care)
  ├─ 3. Post-Stabilization: Ongoing stay medically necessary?
  │  ├─ Stabilized within 24 hours → discharge appropriate?
  │  ├─ Continued ICU stay justified?
  │  └─ Step-down to lower level of care (ICU → telemetry → floor)
  └─ 4. Billing Validation: DRG assignment correct? (Medicare severity)


###   OUTCOMES:

  ├─ Approved: 70% (emergency necessity confirmed)
  ├─ Partial Approval: 20% (e.g., 3 days approved, 2 days denied)
  ├─ Denied: 10% (non-emergency, should have sought PA first)
  └─ Provider Appeal: 30% of denials (high contention area)


###   KEY METRICS:

  ├─ Accuracy: 94% (validated against external medical review)
  ├─ Cost Recovery: $8.5M/month (inappropriate ER utilization denied)
  ├─ Appeal Overturn: 25% (aggressive denials, provider appeals)
  └─ Regulatory Risk: Medium (CMS audits retrospective denials closely)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 AGENT 16: PRIOR AUTHORIZATION REGISTRY AGENT - De-duplication & Renewals

  PURPOSE: Track PA history, detect duplicates, auto-approve renewals


###   TECHNICAL SPECIFICATIONS:

  ├─ Model: GPT-3.5 Turbo (lightweight, mostly database lookups)
  ├─ Latency: Volume: 50,000 checks/day (100% of PAs screened)
  ├─ Database: PostgreSQL (pa_registry table, 150M historical records)
  └─ Cache: Redis (active PAs, 90-day TTL)


###   DUPLICATE DETECTION LOGIC:

  ├─ 1. Exact Match: Same member + procedure + provider + date (100% duplicate)
  ├─ 2. Near Match: Same member + procedure + date ±7 days (98% duplicate)
  ├─ 3. Fuzzy Match: Similar diagnosis codes (same ICD-10 chapter) (85% duplicate)
  └─ 4. Action: Auto-reference original PA, no reprocessing


###   RENEWAL LOGIC:

  ├─ 1. Trigger: PA approaching expiration (30-day warning)
  ├─ 2. Eligibility Check: Member still enrolled? Plan still active?
  ├─ 3. Clinical Stability: No new diagnoses? Same treatment plan?
  ├─ 4. Auto-Renewal Criteria:
  │  ├─ Chronic condition management (diabetes, hypertension)
  │  ├─ Ongoing therapy (PT, infusion, DME)
  │  ├─ Maintenance medications (step therapy already met)
  │  └─ No utilization concerns (appropriate usage)
  └─ 5. Action: Auto-approve 90-day extension (no manual review)

  PA AUTHORIZATION PERIODS (Regulation):
  ├─ Acute Care: 30 days (surgery, imaging, diagnostic)
  ├─ Chronic Care: 90 days (ongoing treatment)
  ├─ Durable Medical Equipment: 12 months (wheelchairs, CPAP)
  └─ Specialty Drugs: Variable (30-365 days based on formulary)


###   KEY METRICS:

  ├─ Duplicate Detection: 12% of submissions are duplicates (6,000/day)
  ├─ Auto-Renewal Rate: 45% of chronic PAs auto-renewed
  ├─ Processing Time Savings: Cost Savings: $2.1M/month (reduced duplicate processing)
  └─ Provider Satisfaction: 4.5/5 (instant duplicate feedback)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 AGENT 17: CLINICAL DOCUMENTATION REQUEST AGENT - Pend Management

  PURPOSE: Auto-generate specific documentation requests, track submissions


###   TECHNICAL SPECIFICATIONS:

  ├─ Model: GPT-4o (generate precise clinical questions)
  ├─ Latency: 2 minutes (runs after initial review)
  ├─ Volume: 12,500 pends/day (25% of 50K PAs require additional info)
  ├─ Integration: AttachmentService (document upload), NotificationAgent (alerts)
  └─ Pend Resolution Time: 3-day average (48-hour provider response goal)

  PEND REASONS (Top 10):
  ├─ 1. Missing Lab Results: 35% (recent A1C, lipid panel, kidney function)
  ├─ 2. Incomplete Diagnosis: 20% (ICD-10 code too vague, need specificity)
  ├─ 3. No Prior Treatment History: 15% (step therapy validation)
  ├─ 4. Missing Imaging: 10% (X-ray, MRI reports to justify procedure)
  ├─ 5. Unclear Clinical Rationale: 8% (why this treatment vs. alternatives?)
  ├─ 6. Wrong Provider Specialty: 5% (specialist required, not PCP)
  ├─ 7. Outdated Information: 3% (records >12 months old)
  ├─ 8. Incomplete Form: 2% (required fields blank)
  ├─ 9. Illegible Handwriting: 1% (fax quality poor)
  └─ 10. Other: 1% (miscellaneous)


###   AUTO-GENERATED REQUEST EXAMPLES:

  ├─ Missing Lab: "Please provide A1C result from last 90 days (current A1C 8.5% is >6 months old)"
  ├─ Step Therapy: "Please document trial of metformin (generic) before approval of Ozempic (brand)"
  ├─ Imaging: "Please upload MRI report showing disk herniation to justify epidural injection"
  └─ Clinical Rationale: "Please explain why patient cannot tolerate CPAP before approving oral appliance"


###   WORKFLOW:

  ├─ 1. Detection: ClinicalAgent confidence Root Cause Analysis: Identify missing data (RAG context gaps)
  ├─ 3. Request Generation: GPT-4o generates specific questions (2-5 items)
  ├─ 4. Provider Notification: Email + Portal + Fax with checklist
  ├─ 5. Document Upload: Provider submits via portal (AttachmentService)
  ├─ 6. Re-trigger Workflow: IntakeAgent processes new docs → re-run agents
  └─ 7. Resolution: 85% approved after docs received, 15% still denied


###   KEY METRICS:

  ├─ Pend Rate: 25% (industry average 30%, below benchmark)
  ├─ Resolution Rate: 85% providers submit requested docs within 48 hours
  ├─ Auto-Approval Post-Docs: 80% approved once docs received
  ├─ Abandonment Rate: 15% providers never respond (auto-deny after 14 days)
  └─ Clarity Score: 4.3/5 provider rating (specific requests vs. generic)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### NEW DATA SERVICES (10) - INDUSTRY STANDARD INTEGRATIONS

ePA | FHIR CDS | Attachments | Drug Ref | Code Validation | SLA | Quality | Payer Exchange | Portal | Grievance

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


🔌 SERVICE 1: ELECTRONIC PRIOR AUTHORIZATION (ePA) SERVICE

  PURPOSE: Standards-based PA submission from EHR systems


###   PROTOCOLS SUPPORTED:

  ├─ Medical PA: X12 278 Health Care Services Review
  │  ├─ 278 Request (Provider → Payer)
  │  ├─ 278 Response (Payer → Provider: Approved/Denied/Pend)
  │  ├─ 278 Inquiry (Status check)
  │  └─ 278 Notification (Decision update)
  ├─ Pharmacy PA: NCPDP SCRIPT 10.6
  │  ├─ PARequest (Pharmacy → PBM)
  │  ├─ PAResponse (PBM → Pharmacy)
  │  ├─ PANotification (Status update)
  │  └─ PAAppealRequest (Denial appeal)
  └─ HL7 FHIR: Modern REST API alternative
     ├─ Task/$submit (PA submission)
     ├─ Task/$status (Status query)
     └─ Task/$update (Add information)


###   EHR INTEGRATIONS:

  ├─ Epic: 40% of volume (Epic Interconnect API)
  ├─ Cerner: 25% (Cerner Millennium API)
  ├─ Allscripts: 10% (Allscripts Open API)
  ├─ Athenahealth: 8% (MDP API)
  ├─ eClinicalWorks: 5% (eCW API)
  └─ Other: 12% (generic X12/SCRIPT)


###   WORKFLOW:

  ├─ 1. Receive ePA: X12 278 transaction via AS2/SFTP
  ├─ 2. Parse & Validate: EDI format validation (loop 2000E service line)
  ├─ 3. Transform to Internal: Map X12 fields → IntakeAgent JSON
  ├─ 4. Trigger Workflow: WorkflowEngine starts PA processing
  ├─ 5. Decision Mapping:
  │  ├─ Approved → X12 278 response (A1 = Approved)
  │  ├─ Denied → X12 278 response (A3 = Denied) + reason codes
  │  └─ Pend → X12 278 response (A2 = Modified/Pend) + doc request
  └─ 6. Response Transmission: Send 278 response via AS2 back to EHR


###   KEY METRICS:

  ├─ Volume: 30,000 ePA/day (60% of total 50K, growing 15%/year)
  ├─ Parsing Success: 99.5% (0.5% malformed X12 transactions rejected)
  ├─ Auto-Approval: 75% (higher than manual submissions, better data quality)
  ├─ Average Latency: 8 minutes (e2e from receive to response)
  ├─ Provider Satisfaction: 4.7/5 (integrated workflow, no portal login)
  └─ Cost: $0.15/transaction (EDI processing + transformation)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ SERVICE 2: FHIR CDS HOOKS SERVICE - Real-Time Clinical Decision Support

  PURPOSE: Alert providers at prescribing time if PA required


###   CDS HOOKS WORKFLOW:

  ├─ 1. EHR Event: Provider prescribes medication in Epic/Cerner
  ├─ 2. Hook Trigger: medication-prescribe hook fires
  ├─ 3. Context Sent: EHR sends patient data (FHIR R4 JSON)
  │  ├─ Patient demographics (age, gender, member ID)
  │  ├─ Active medications (MedicationRequest resources)
  │  ├─ Diagnoses (Condition resources, ICD-10 codes)
  │  └─ Current prescription (drug NDC, quantity, days supply)
  ├─ 4. PA Check: Call FormularyService + PolicyService
  │  ├─ Is drug covered? (on formulary?)
  │  ├─ PA required? (tier 3-6 drugs)
  │  ├─ Step therapy? (prior drugs required?)
  │  └─ Quantity limits? (max 30-day supply?)
  ├─ 5. CDS Card Response: Send alert to EHR
  │  ├─ Info Card: "PA required - Click to submit"
  │  ├─ Warning Card: "Step therapy needed - Try generic first"
  │  ├─ Suggestion Card: "Formulary alternative: Drug X (no PA)"
  │  └─ Link: Deep link to PA portal (pre-filled form)
  └─ 6. Provider Action: Click link → submit PA or change prescription


###   HOOK TYPES SUPPORTED:

  ├─ medication-prescribe: Drug PA alerts
  ├─ order-select: Procedure/imaging PA alerts
  ├─ patient-view: Show active PAs in chart
  └─ encounter-discharge: Post-acute PA requirements


###   KEY METRICS:

  ├─ Volume: 100,000 hooks/day (provider prescribing events)
  ├─ PA Detection: 35% of prescriptions require PA (35K alerts/day)
  ├─ Provider Response:
  │  ├─ 60% change to non-PA drug (formulary alternative)
  │  ├─ 25% submit PA immediately (integrated workflow)
  │  └─ 15% ignore (prescribe anyway, PA submitted later)
  ├─ Latency: ROI: 60% PA avoidance → $12M/year administrative savings
  └─ EHR Adoption: Epic (80%), Cerner (15%), Others (5%)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### 📎 SERVICE 3-10: CONDENSED SPECIFICATIONS



###   SERVICE 3: ATTACHMENT HANDLING SERVICE

  ├─ Purpose: Accept medical records (HL7 CDA, DICOM, PDF)
  ├─ Volume: 40,000 attachments/day (80% of PAs include documents)
  ├─ Processing: OCR (text extraction) → Index (Elasticsearch) → Link to PA
  ├─ Format Support: PDF, JPEG, TIFF, HL7 CDA, DICOM (imaging)
  └─ Storage: Azure Blob (10TB total, 2M objects)


###   SERVICE 4: DRUG REFERENCE DATA SERVICE

  ├─ Purpose: Comprehensive drug database (NDC, interactions, alternatives)
  ├─ Data Sources: FDA NDC Directory, RxNorm, FDB MedKnowledge
  ├─ Volume: 120,000 lookups/day (every drug PA)
  ├─ APIs: GET /drug/{ndc} → drug info, interactions, therapeutic equivalents
  └─ Cache: Redis 95% hit rate (frequently prescribed drugs)


###   SERVICE 5: ICD/CPT CODE VALIDATION SERVICE

  ├─ Purpose: Validate diagnosis/procedure codes before processing
  ├─ Volume: 50,000 validations/day (100% of PAs)
  ├─ Checks: ICD-10 valid? CPT valid? Appropriate pairing? (medical necessity)
  ├─ Rejection Rate: 5% invalid codes (auto-deny with correction request)
  └─ Data Sources: CMS ICD-10-CM, AMA CPT, NLM UMLS


###   SERVICE 6: SLA MONITORING & ESCALATION SERVICE

  ├─ Purpose: Track time remaining, escalate approaching breaches
  ├─ Volume: 50,000 PAs tracked/day
  ├─ SLA Tiers: Urgent 72hr, Standard 30 days, Appeals 60 days
  ├─ Escalation: 80% → P3 alert, 90% → P2 alert, 100% → Auto-approve (deemed)
  └─ Breach Rate: 2% (1,000/day, regulatory risk)


###   SERVICE 7: QUALITY MEASURE TRACKING SERVICE

  ├─ Purpose: Track HEDIS/NCQA quality measures (Stars rating)
  ├─ Volume: 10,000 measures/day
  ├─ Metrics: Diabetes care (A1C testing), Med adherence (PDC >80%)
  ├─ Impact: PA decisions affect quality scores (bonus $50M/year)
  └─ Reporting: NCQA annual submission, CMS Stars quarterly


###   SERVICE 8: PAYER-TO-PAYER DATA EXCHANGE SERVICE

  ├─ Purpose: Transfer PA approvals when member changes payers
  ├─ Protocol: FHIR R4 bulk data export (CMS Interoperability Rule 2022)
  ├─ Volume: 5,000 exchanges/day (10% member churn annually)
  ├─ Data: Active PAs, authorization periods, clinical notes
  └─ Compliance: Required by CMS for Medicare Advantage plans


###   SERVICE 9: PROVIDER SELF-SERVICE PORTAL BACKEND

  ├─ Purpose: Real-time PA status, form pre-fill, document upload
  ├─ Volume: 20,000 logins/day (70% provider preference vs. phone)
  ├─ Features: PA submission, status tracking, appeals, P2P scheduling
  ├─ Tech Stack: React (frontend), GraphQL (API), PostgreSQL (data)
  └─ Impact: 50% call center volume reduction


###   SERVICE 10: MEMBER GRIEVANCE & APPEAL TRACKING SERVICE

  ├─ Purpose: Track appeal timelines, IRO referrals, state reporting
  ├─ Volume: 2,000 grievances/day (4% of denials appealed)
  ├─ Timelines: Level 1 (30 days), Level 2 (60 days), IRO (180 days)
  ├─ Workflow: Temporal durable execution (SLA tracking)
  └─ Regulatory: State-mandated reporting (quarterly appeals metrics)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### INTEGRATION GATEWAY TIER (4) - HEALTHCARE INTEROPERABILITY STANDARDS

HL7 FHIR R4 | X12 278 EDI | NCPDP SCRIPT 10.6 | Direct Protocol

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


  GATEWAY 1: HL7 FHIR GATEWAY (Modern RESTful Standard)
  ├─ Protocol: HL7 FHIR R4 (Fast Healthcare Interoperability Resources)
  ├─ Endpoints: 15+ FHIR resources (Patient, Condition, MedicationRequest, Task, etc.)
  ├─ Use Cases: CDS Hooks, Payer-to-Payer Exchange, Mobile Apps
  ├─ Volume: 100,000 API calls/day
  ├─ Security: OAuth 2.0 + SMART on FHIR
  ├─ Compliance: CMS Interoperability Rule (42 CFR 431.60)
  └─ Response Time: P95 GATEWAY 2: X12 278 GATEWAY (Medical PA Standard)
  ├─ Protocol: ASC X12N 005010X217 (Health Care Services Review)
  ├─ Transaction Sets: 278 Request, 278 Response, 278 Inquiry, 278 Notification
  ├─ Transport: AS2 (secure file transfer), SFTP, VAN (value-added network)
  ├─ Volume: 30,000 transactions/day
  ├─ Validation: 999 Functional Acknowledgment, TA1 Interchange Acknowledgment
  ├─ Turnaround: Error Rate: 0.5% malformed transactions

  GATEWAY 3: NCPDP SCRIPT GATEWAY (Pharmacy PA Standard)
  ├─ Protocol: NCPDP SCRIPT 10.6 (Pharmacy Prior Authorization)
  ├─ Message Types: PARequest, PAResponse, PANotification, PAAppealRequest
  ├─ Transport: HTTPS (XML messages), NCPDP Mailbox
  ├─ Volume: 20,000 pharmacy PAs/day (40% of drug PAs)
  ├─ Integration: CVS Caremark, Express Scripts, OptumRx (PBMs)
  ├─ Response SLA: 24 hours (pharmacy pickup timeline)
  └─ Auto-Approval: 65% (formulary lookup + step therapy validation)

  GATEWAY 4: DIRECT PROTOCOL GATEWAY (Secure Document Exchange)
  ├─ Protocol: Direct Standard 1.1 (HISP - Health Information Service Provider)
  ├─ Use Cases: Secure fax alternative, medical record transfer
  ├─ Encryption: S/MIME (email encryption), XDR/XDM (document exchange)
  ├─ Volume: 5,000 messages/day
  ├─ Trust: DirectTrust accreditation (certificate validation)
  ├─ Message Size: Up to 50MB (large imaging studies)
  └─ Delivery Confirmation: MDN (Message Disposition Notification)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### COMPLIANCE & SECURITY LAYER (4) - REGULATORY CONTROLS

DLP | Consent Management | Breach Notification | State-Specific Mandates

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



###   SERVICE 1: DATA LOSS PREVENTION (DLP) SERVICE

  ├─ Technology: Microsoft Purview (formerly Azure Information Protection)
  ├─ Detection: Real-time PHI scanning (SSN, DOB, medical record numbers)
  ├─ Scope: Logs, emails, API responses, database exports
  ├─ Policies: 50+ DLP rules (regex patterns + ML classification)
  ├─ Actions: Block (prevent transmission), Redact (mask PHI), Alert (notify security)
  ├─ Incidents: 5 PHI leakage events/month (all blocked, no breaches)
  └─ Compliance: HIPAA Privacy Rule (45 CFR 164.308)


###   SERVICE 2: CONSENT MANAGEMENT SERVICE

  ├─ Technology: OneTrust Privacy Management Platform
  ├─ Purpose: Track HIPAA authorizations, patient consent for data sharing
  ├─ Use Cases: COB (coordination of benefits), payer exchange, marketing
  ├─ Consent Types: Treatment, Payment, Operations (TPO) + Marketing opt-in
  ├─ Storage: PostgreSQL (consent_records table, 7-year retention)
  ├─ Validation: Check consent before every external data share
  └─ Revocation: Patient can withdraw consent via portal (24-hour processing)


###   SERVICE 3: BREACH NOTIFICATION SERVICE

  ├─ Trigger: Automated breach detection (>500 records = reportable)
  ├─ Workflow:
  │  ├─ Detect breach (DLP alert, audit log anomaly)
  │  ├─ Risk assessment (severity scoring)
  │  ├─ Containment (revoke access, isolate affected data)
  │  ├─ Notification: HHS/OCR (72 hours), Affected members (60 days), Media (if >500)
  │  └─ Remediation (patch vulnerability, retraining)
  ├─ Regulatory: HIPAA Breach Notification Rule (45 CFR 164.404-414)
  ├─ Fines: $50K-$1.5M per breach (tiered penalties)
  └─ Incidents: 0 reportable breaches in 2025-2026


###   SERVICE 4: STATE-SPECIFIC MANDATE SERVICE

  ├─ Purpose: Apply 50-state PA regulation variations
  ├─ Variations:
  │  ├─ SLA Timelines: California 5 days, Texas 3 days, Federal 30 days
  │  ├─ External Review: New York mandates IRO for all denials
  │  ├─ Step Therapy: 15 states limit step therapy for certain conditions
  │  └─ Continuity of Care: Most states require ongoing treatment continuation
  ├─ Implementation: OPA policy engine (state-specific rule sets)
  ├─ Complexity: 500+ state-specific rules (vs. 100 federal rules)
  └─ Audit: State regulators conduct annual PA process audits


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### OPERATIONAL ANALYTICS LAYER (5) - PERFORMANCE & INSIGHTS

Capacity Planning | Root Cause Analysis | Provider Analytics | Member Preferences | Multi-Tenant Config

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



###   SERVICE 1: CAPACITY PLANNING SERVICE

  ├─ Purpose: Forecast HITL reviewer staffing needs, predict PA volume spikes
  ├─ ML Model: Prophet (Facebook time-series forecasting)
  ├─ Inputs: Historical volume, seasonality, holidays, payer enrollment trends
  ├─ Outputs: Daily staffing recommendations (200 FTE avg, ±30 range)
  ├─ Accuracy: 92% forecast accuracy (within 10% of actual volume)
  ├─ Cost Impact: $2.5M/year labor cost optimization (reduce overtime 40%)
  └─ Alerts: 7-day advance notice of volume spikes (flu season, enrollment)


###   SERVICE 2: ROOT CAUSE ANALYSIS SERVICE

  ├─ Purpose: Analyze denial patterns, identify systemic issues
  ├─ ML Model: K-means clustering (group similar denials)
  ├─ Insights:
  │  ├─ Top denial reason: Step therapy not met (35%)
  │  ├─ Agent accuracy dip: ClinicalAgent 96% → 93% (investigate prompt drift)
  │  ├─ Provider training opportunity: Dr. Smith 50% denial rate (outlier)
  │  └─ Data quality issue: 5% invalid ICD-10 codes (upstream fix needed)
  ├─ Actions: Auto-generate remediation tickets (Jira integration)
  ├─ Impact: Reduced denial rate 28% → 24% (4% improvement = $15M/year)
  └─ Reporting: Weekly executive dashboard (Power BI)


###   SERVICE 3: PROVIDER PERFORMANCE ANALYTICS SERVICE

  ├─ Purpose: Track provider PA success rates, identify training opportunities
  ├─ Metrics: Approval rate, pend rate, appeal rate, resubmission rate
  ├─ Segmentation: By provider, specialty, practice size, geography
  ├─ Outlier Detection: 10% of providers generate 40% of denials
  ├─ Intervention: Targeted education (webinars, 1:1 coaching)
  ├─ Impact: High-denial providers improved 15% after training
  └─ Provider Portal Integration: Providers see their own scorecard (gamification)


###   SERVICE 4: MEMBER COMMUNICATION PREFERENCE SERVICE

  ├─ Purpose: Track preferred contact method, language, accessibility needs
  ├─ Storage: Redis (fast lookup, 2M member preferences)
  ├─ Preferences: Email only, SMS only, Portal, Phone, Fax, No contact
  ├─ Accessibility: Large print, Braille, ASL video, 200+ languages
  ├─ Compliance: HIPAA requires respecting communication preferences
  ├─ Impact: 95% delivery success (vs. 70% without preferences)
  └─ Opt-out: CAN-SPAM (email), TCPA (SMS) compliance


###   SERVICE 5: MULTI-TENANT CONFIGURATION SERVICE

  ├─ Purpose: Per-payer customization (branding, workflows, approval thresholds)
  ├─ Database: MongoDB (flexible schema, payer_config collection)
  ├─ Configuration:
  │  ├─ Branding: Logo, colors, terminology (PA vs. authorization)
  │  ├─ Workflows: Custom approval steps (e.g., pharmacy director review)
  │  ├─ Thresholds: Auto-approve up to $5K (vs. $2K default)
  │  └─ Integrations: Custom EHR connections, reporting formats
  ├─ Payers: 5 payer organizations (10M members total)
  ├─ Isolation: Data segregation (row-level security in PostgreSQL)
  └─ SaaS Model: Platform shared, configuration isolated


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### Agent_Fallback_Security


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### AGENT FALLBACK, OPTIMIZATION, SECURITY & METRICS

Resilience Patterns | Performance Tuning | Zero Trust Security | SLA Monitoring

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


🛡️ AGENT 1: INTAKE AGENT - Fallback & Security

  PRIMARY EXECUTION PATH (Happy Path):
  ├─ 1. Document Upload → Azure Blob Storage (encrypted at rest)
  ├─ 2. OCR Processing → Azure Form Recognizer API (98.5% accuracy)
  ├─ 3. LLM Classification → GPT-4o Vision (97% field extraction)
  ├─ 4. Field Validation → JSON schema + business rules
  └─ 5. Store Metadata → PostgreSQL pa_documents table
     Success Rate: 88% complete without intervention | Latency: 2 min avg

  FALLBACK TIER 1: Token Limit Exceeded (>128K tokens)
  ├─ Trigger: PDF >100 pages or complex multi-form submission
  ├─ Strategy: Document chunking + progressive extraction
  │  ├─ Split PDF into 10-page chunks (overlap 1 page)
  │  ├─ Process each chunk separately (parallel execution)
  │  ├─ Merge results using deduplication logic
  │  └─ Confidence aggregation (weighted by chunk quality)
  ├─ Performance Impact: +45 seconds latency per 100 pages
  └─ Success Rate: 95% recover with chunking

  FALLBACK TIER 2: OCR Failure (Poor Image Quality)
  ├─ Trigger: OCR confidence Strategy: Progressive image preprocessing
  │  ├─ Attempt 1: Deskew + denoise (Pillow library)
  │  ├─ Attempt 2: Increase contrast + sharpen (OpenCV)
  │  ├─ Attempt 3: Tesseract OCR fallback (open-source)
  │  └─ Attempt 4: Route to HITL for manual data entry
  ├─ Retry Logic: 3 attempts × exponential backoff (1s, 2s, 4s)
  └─ Success Rate: 85% recover within 3 attempts | 15% → HITL

  FALLBACK TIER 3: GPT-4o Vision API Failure
  ├─ Trigger: HTTP 5xx errors, timeout (>5 min), rate limit (HTTP 429)
  ├─ Strategy: Model degradation cascade
  │  ├─ Primary: GPT-4o Vision (best accuracy, highest cost)
  │  ├─ Fallback 1: Claude 3.5 Sonnet Vision (comparable accuracy, 30% cheaper)
  │  ├─ Fallback 2: GPT-4 Turbo (no vision, OCR text only, 50% cheaper)
  │  ├─ Fallback 3: OCR + Rule-based extraction (regex patterns, 90% cheaper)
  │  └─ Emergency: Queue to HITL (manual review within 2 hours)
  ├─ Rate Limit Handling:
  │  ├─ Detect HTTP 429 → Extract Retry-After header
  │  ├─ Exponential backoff: 1s, 2s, 4s, 8s, 16s (max 30s)
  │  ├─ Circuit breaker: 5 consecutive failures → OPEN (60s cooldown)
  │  └─ Load shedding: Deprioritize low-value requests during peak
  └─ Success Rate: 96% recover within fallback chain

  DEGRADED MODE (Emergency Operations):
  ├─ Scenario: All LLM APIs unavailable (catastrophic failure)
  ├─ Action: Accept document uploads only (store for later processing)
  ├─ Notification: Email provider: "Delayed processing - expect 24-hour SLA"
  ├─ Batch Processing: Reprocess queue when services restored
  └─ Monitoring: PagerDuty alert → P1 incident (15-min response)


###   OPTIMIZATION STRATEGIES:


  1️⃣ Token Reduction Techniques:
     • Image Compression: Reduce resolution to 1024px max (70% token savings)
     • Selective Extraction: Extract only required form sections (vs. full document)
     • Template Matching: Pre-identify form type → use targeted prompts (40% tokens)
     • Batch Processing: Process multiple similar forms in single LLM call
     • Impact: Average token usage: 15K → 9K (40% reduction, $0.11 savings/request)

  2️⃣ Caching Strategy:
     • Cache Key: SHA-256 hash of document binary
     • Cache Storage: Redis (extracted metadata) + Blob (processed image)
     • TTL: 90 days (resubmission window per policy)
     • Hit Rate: 12% (duplicate/resubmission detection)
     • Savings: 12% × 50K requests/day × $0.285 = $1,710/day ($51K/month)

  3️⃣ Parallel Processing:
     • Multi-page Documents: Process pages in parallel (10 workers)
     • Multi-document Submissions: Process attachments concurrently
     • Speedup: 10-page PDF: 20 min sequential → 2.5 min parallel (8x faster)

  4️⃣ Speculative Execution:
     • Pre-warm EligibilityAgent: Start eligibility check on high-confidence OCR
     • Confidence Threshold: >0.95 OCR confidence → safe to proceed
     • Rollback: Abort downstream agents if final validation fails
     • Speedup: 15-30 seconds saved on 85% of requests

  5️⃣ Smart Retry Logic:
     • Idempotency: All operations idempotent (safe to retry)
     • Jitter: Random delay (0-500ms) to prevent thundering herd
     • Circuit Breaker: Fail-fast after 5 consecutive errors
     • Bulkhead Pattern: Isolate OCR failures from LLM failures


###   SECURITY CONTROLS:


  🔐 Authentication & Authorization:
  ├─ API Authentication: OAuth2 JWT tokens (1-hour expiry)
  ├─ Service Account: Managed Identity (Azure AD, no secrets in code)
  ├─ RBAC: Role-based access (pa_coordinator, pa_reviewer, admin)
  ├─ mTLS: Mutual TLS for service-to-service (Istio mesh)
  └─ Principle of Least Privilege: IntakeAgent has minimal permissions (read Blob, write PostgreSQL)

  🔒 Data Protection:
  ├─ Encryption at Rest: AES-256 (Azure Blob, PostgreSQL TDE)
  ├─ Encryption in Transit: TLS 1.3 (all API calls, database connections)
  ├─ PHI Masking: Redact SSN, DOB in logs (regex-based masking)
  ├─ PII Tokenization: Irreversible hash for audit logs (SHA-256)
  └─ Data Retention: Documents purged after 7 years (HIPAA requirement)

  🛡️ Input Validation:
  ├─ File Type Whitelist: PDF, JPEG, PNG, TIFF only (block executables)
  ├─ File Size Limit: 50MB max (prevent DoS via large uploads)
  ├─ Malware Scanning: ClamAV antivirus (scan before processing)
  ├─ Content Security: Validate PDF structure (prevent PDF bombs)
  └─ Rate Limiting: 100 uploads/hour per user (prevent abuse)

  🚨 Security Monitoring:
  ├─ Anomaly Detection: Alert on unusual upload patterns (volume spike, off-hours)
  ├─ Failed Auth Attempts: 5 failures → Account lockout (15 min)
  ├─ Data Exfiltration: Monitor bulk downloads (>1000 records/hour)
  ├─ Insider Threat: Privileged access review (quarterly)
  └─ Audit Logging: All PHI access logged (7-year retention)


###   METRICS & EVALUATION:


  📊 Performance Metrics:
  ├─ Latency Distribution:
  │  ├─ P50 (Median): 1.8 min (50% complete within 1.8 min)
  │  ├─ P95: 3.5 min (95% complete within 3.5 min)
  │  ├─ P99: 6.2 min (99% complete within 6.2 min)
  │  └─ SLA: 5 min (98.5% compliance)
  ├─ Throughput: 2,500 requests/hour peak (0.7 req/sec avg)
  ├─ Error Rate: 3.8% (retry + HITL recovery)
  └─ Availability: 99.95% uptime (4.38 hours downtime/year)

  📈 Accuracy Metrics:
  ├─ Field Extraction Accuracy: 97% (measured against HITL ground truth)
  │  ├─ Patient Demographics: 99% (name, DOB, member_id)
  │  ├─ Diagnosis Codes (ICD-10): 95% (complex medical terminology)
  │  ├─ Procedure Codes (CPT): 96% (standardized codes)
  │  └─ Provider Information: 98% (NPI, name, specialty)
  ├─ Document Classification: 99% (15 form types)
  ├─ Confidence Calibration: 92% (predicted confidence vs. actual accuracy)
  └─ Human Agreement: 94% (agent decision vs. expert reviewer)

  💰 Cost Metrics:
  ├─ Per Request Cost: $0.285 avg
  │  ├─ OCR (Azure Form Recognizer): $0.05
  │  ├─ LLM (GPT-4o Vision): $0.22
  │  ├─ Storage (Blob + PostgreSQL): $0.01
  │  └─ Compute (K8s pod hours): $0.005
  ├─ Daily Cost: 50K requests × $0.285 = $14,250/day
  ├─ Monthly Cost: $427,500/month
  └─ Cost per Successful Extraction: $0.296 (accounting for retries)

  🔐 Security Metrics:
  ├─ Failed Auth Attempts: 0.05% of requests (monitored for brute force)
  ├─ Malware Detected: 0.001% of uploads (blocked by ClamAV)
  ├─ PHI Leakage Events: 0 incidents in 2025 (DLP monitoring)
  ├─ Audit Coverage: 100% of PHI access logged
  ├─ Security Scan Results: 0 critical vulnerabilities (weekly Snyk scans)
  └─ Compliance Score: 98/100 (SOC2 Type II audit)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ AGENT 2: ELIGIBILITY AGENT - Fallback & Security


###   PRIMARY EXECUTION PATH:

  ├─ 1. Extract member_id from IntakeAgent output
  ├─ 2. Call member_lookup tool (MCP) → MemberService API
  ├─ 3. Validate plan status (active, terminated, pending)
  ├─ 4. Check effective dates (coverage start, end dates)
  └─ 5. Return eligibility determination
     Success Rate: 99% (simple rule-based logic) | Latency: 15 sec avg

  FALLBACK TIER 1: Cache Layer (Redis)
  ├─ Trigger: Primary database query
  ├─ Cache Strategy: Read-through cache (check cache first)
  ├─ Cache Key: member:{member_id}:{service_date}
  ├─ TTL: 24 hours (eligibility changes daily)
  ├─ Hit Rate: 85% (massive cost/latency savings)
  ├─ Cache Miss: Query PostgreSQL → populate cache
  └─ Performance: 5ms cache hit vs. 80ms database query

  FALLBACK TIER 2: Database Replica Failover
  ├─ Trigger: Primary PostgreSQL unavailable (connection timeout)
  ├─ Strategy: Auto-failover to read replica
  │  ├─ 5 read replicas (multi-AZ deployment)
  │  ├─ Health checks every 5 seconds
  │  ├─ Automatic DNS failover (Route 53)
  │  └─ Replication lag: Failover Time: Success Rate: 99.99% availability

  FALLBACK TIER 3: Stale Data Tolerance
  ├─ Trigger: All databases unavailable (catastrophic failure)
  ├─ Strategy: Use last known cached data (up to 24 hours old)
  ├─ Warning: Flag determination as "potentially stale - verify manually"
  ├─ Business Rule: Accept stale data for low-risk cases (Escalation: High-risk cases (>$10K) → HITL with fresh eligibility check
  └─ Recovery: Revalidate all "stale" determinations when database restored

  FALLBACK TIER 4: External Eligibility Verification
  ├─ Trigger: Member not found in internal database
  ├─ Strategy: Real-time eligibility check (270/271 EDI transaction)
  │  ├─ Call external payer API (if multi-payer case)
  │  ├─ SOAP/REST API to clearinghouse (Availity, Change Healthcare)
  │  ├─ Timeout: 30 seconds (API SLA)
  │  └─ Retry: 2 attempts with 5-second backoff
  ├─ Success Rate: 92% (some payers don't support real-time)
  └─ Fallback: Manual eligibility verification (HITL fax/phone)


###   OPTIMIZATION STRATEGIES:


  1️⃣ Cache Optimization:
     • Tiered Caching: L1 (in-memory) + L2 (Redis) + L3 (PostgreSQL)
     • Pre-warming: Cache frequent members during off-peak hours
     • Invalidation: Event-driven (Kafka member_updated event)
     • Compression: gzip compress large eligibility records (50% size reduction)
     • Impact: 85% hit rate saves 68 sec × 42.5K requests/day = 809 hours/day compute

  2️⃣ Query Optimization:
     • Index Strategy: B-tree on member_id + service_date (covering index)
     • Query Plan: Index-only scan (no table access required)
     • Connection Pooling: PgBouncer (1000 connections → 50 pool)
     • Prepared Statements: Reduce query planning overhead (5ms savings)
     • Impact: Query time: 150ms → 80ms (47% faster)

  3️⃣ Batch Processing:
     • Scenario: Bulk PA submissions (employer onboarding, annual reviews)
     • Strategy: Single SQL query with IN clause (vs. N queries)
     • Example: Check eligibility for 100 members in 1 query (500ms vs. 8 seconds)
     • Impact: 95% latency reduction for batch operations

  4️⃣ Result Prediction:
     • ML Model: Predict eligibility before database query (99% accuracy)
     • Features: Member age, plan type, historical eligibility, time since last update
     • Use Case: Skip database query if prediction confidence >99.5%
     • Impact: 20% of queries avoided (ultra-high confidence predictions)


###   SECURITY CONTROLS:


  🔐 Authentication:
  ├─ Service Account: Dedicated database user (eligibility_agent_read)
  ├─ Least Privilege: SELECT-only permissions (no INSERT/UPDATE/DELETE)
  ├─ Row-Level Security: PostgreSQL RLS (agent can only read active plans)
  ├─ Connection Security: SSL/TLS encrypted (verify-ca mode)
  └─ Credential Rotation: Automatic 90-day password rotation (Vault)

  🔒 Data Protection:
  ├─ PHI Minimization: Query only required fields (no unnecessary PHI)
  ├─ Audit Logging: Log all member lookups (who, when, member_id, purpose)
  ├─ Cache Encryption: Redis TLS + encryption at rest
  └─ Data Residency: Member data stays in US region (HIPAA compliance)


###   METRICS & EVALUATION:


  📊 Performance Metrics:
  ├─ Latency: P50 10ms (cache) | P95 85ms (DB) | P99 150ms
  ├─ Throughput: 10,000 req/sec (cache) | 500 req/sec (DB)
  ├─ Error Rate: 0.05% (database timeouts)
  └─ Cache Hit Rate: 85% (target: >80%)

  📈 Accuracy Metrics:
  ├─ Eligibility Determination: 99% accuracy (rule-based, deterministic)
  ├─ False Positives: 0.5% (incorrectly approved as eligible)
  ├─ False Negatives: 0.5% (incorrectly denied as ineligible)
  └─ Root Cause: 90% stale data, 10% incorrect member_id extraction

  💰 Cost Metrics:
  ├─ Per Request: $0.003 avg (very low cost)
  │  ├─ Cache hit: $0.0001 (Redis operation)
  │  ├─ Database query: $0.002 (compute + storage)
  │  └─ External API: $0.05 (rare, 3% of cases)
  ├─ Daily Cost: 50K × $0.003 = $150/day
  └─ Monthly Cost: $4,500/month (cheapest agent)

  🔐 Security Metrics:
  ├─ Audit Coverage: 100% member lookups logged
  ├─ Unauthorized Access Attempts: 0 (least privilege enforcement)
  └─ Data Leakage: 0 incidents (cache encryption, audit logging)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ AGENT 3: BENEFITS AGENT - Fallback & Security


###   PRIMARY EXECUTION PATH:

  ├─ 1. Retrieve member plan details (tier: Bronze/Silver/Gold/Platinum)
  ├─ 2. Check network status (in-network tier 1/2, out-of-network)
  ├─ 3. Evaluate OPA policy rules (50+ benefit rules)
  ├─ 4. Calculate cost sharing (copay, coinsurance, deductible)
  └─ 5. Determine PA requirement (always, conditional, never)
     Success Rate: 95% | Latency: 20 sec avg

  FALLBACK TIER 1: OPA Policy Engine Failure
  ├─ Trigger: OPA service unavailable (HTTP 5xx, timeout >2s)
  ├─ Strategy: Fallback to cached policy decisions
  │  ├─ Cache Key: plan_type + procedure_code + network_status
  │  ├─ Cache TTL: 24 hours (policies updated daily)
  │  ├─ Cache Hit Rate: 60% (common procedure/plan combinations)
  │  └─ Staleness Acceptable: Benefit policies change infrequently
  ├─ Circuit Breaker: After 5 OPA failures, use cache-only mode for 5 min
  └─ Success Rate: 60% recover from cache | 40% → HITL

  FALLBACK TIER 2: Complex Decision Tree Timeout
  ├─ Trigger: OPA evaluation >5 seconds (complex nested rules)
  ├─ Strategy: Progressive complexity reduction
  │  ├─ Attempt 1: Full rule evaluation (12 decision trees)
  │  ├─ Attempt 2: Simplified rules (8 core trees, skip edge cases)
  │  ├─ Attempt 3: Default benefit tier (conservative, Gold plan defaults)
  │  └─ Attempt 4: Route to HITL (manual benefit determination)
  ├─ Accuracy Trade-off: Simplified rules 92% accurate (vs. 95% full)
  └─ Success Rate: 90% resolve with simplified rules

  FALLBACK TIER 3: Network Service Unavailable
  ├─ Trigger: Network API timeout (provider NPI validation)
  ├─ Strategy: Assume in-network (more permissive)
  │  ├─ Risk: May over-approve out-of-network cases
  │  ├─ Mitigation: Flag for post-approval verification
  │  ├─ Business Rule: Accept for low-cost procedures ($5K) → HITL for network verification
  ├─ Recovery: Batch revalidation when network service restored
  └─ Impact: 2% over-approval rate (acceptable business risk)


###   OPTIMIZATION STRATEGIES:


  1️⃣ Policy Rule Caching:
     • Pre-compute Common Combinations: Top 100 plan+procedure pairs (covers 70%)
     • Materialized View: PostgreSQL view with cached OPA decisions
     • Refresh Strategy: Nightly batch update (policies change infrequently)
     • Impact: 70% of requests skip OPA entirely (15-sec savings)

  2️⃣ Decision Tree Pruning:
     • Early Termination: If PA not required, skip remaining 8 trees
     • Conditional Evaluation: Only evaluate relevant trees (medical vs. pharmacy)
     • Impact: Average trees evaluated: 12 → 6 (50% reduction)

  3️⃣ Parallel Tool Calls:
     • Concurrent Execution: Network check + Formulary check + Cost calculation
     • Promise.all: Wait for all results (vs. sequential)
     • Impact: 20s sequential → 8s parallel (60% faster)


###   SECURITY CONTROLS:


  🔐 Policy Integrity:
  ├─ Immutable Policies: OPA policies version-controlled (Git)
  ├─ Change Approval: 2-person review + compliance approval
  ├─ Audit Trail: All policy changes logged (who, when, diff)
  └─ Rollback: Instant rollback to previous policy version


###   METRICS & EVALUATION:


  📊 Performance: P50 18s | P95 35s | P99 60s
  📈 Accuracy: 95% tier determination | 5% require human adjustment
  💰 Cost: $0.30/request | $15K/day | $450K/month
  🔐 Security: 100% policy changes audited | 0 unauthorized policy modifications


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ AGENT 4: CLINICAL AGENT - Fallback & Security ★ CRITICAL BOTTLENECK


###   PRIMARY EXECUTION PATH (8-MINUTE BOTTLENECK):

  ├─ 1. RAG Retrieval (20 queries × 265ms) = 2.7 sec
  ├─ 2. Context Preparation (guidelines + similar cases) = 5 sec
  ├─ 3. GPT-4o Inference (medical necessity evaluation) = 472 sec ★ TRUE BOTTLENECK
  └─ 4. Confidence scoring + citation validation = 3 sec
     Success Rate: 96% | Latency: 8 min avg (480 sec)

  FALLBACK TIER 1: Context Window Overflow (>128K tokens)
  ├─ Trigger: RAG retrieves too many guidelines (complex multi-diagnosis case)
  ├─ Strategy: Intelligent context pruning
  │  ├─ Step 1: Rank guidelines by relevance score (vector similarity)
  │  ├─ Step 2: Keep top 10 guidelines (vs. all 20)
  │  ├─ Step 3: Summarize each guideline (GPT-4o-mini, 500 tokens → 100 tokens)
  │  ├─ Step 4: Fit within 100K token budget (leave 28K for response)
  │  └─ Trade-off: Slight accuracy loss (96% → 94%) vs. complete failure
  ├─ Token Budget:
  │  ├─ System Prompt: 2,500 tokens
  │  ├─ Guidelines (top 10): 15,000 tokens (1,500 each)
  │  ├─ Similar Cases: 3,000 tokens
  │  ├─ Current PA Details: 5,000 tokens
  │  ├─ Total Input: ~25,500 tokens (well under 128K limit)
  └─ Success Rate: 98% fit within limits after pruning

  FALLBACK TIER 2: RAG Service Unavailable
  ├─ Trigger: Milvus/Elasticsearch/Neo4j timeout or failure
  ├─ Strategy: LLM-only mode (zero-shot reasoning without RAG)
  │  ├─ Impact: Accuracy drops 96% → 78% (significant degradation)
  │  ├─ Mitigation: Flag all decisions as "low confidence" (Partial RAG Failure: If only 1 of 3 RAG sources fails
  │  ├─ Vector DB down: Use keyword + graph search (90% accuracy)
  │  ├─ Elasticsearch down: Use vector + graph search (92% accuracy)
  │  ├─ Neo4j down: Use vector + keyword search (94% accuracy)
  └─ Recovery: Retry RAG queries 3x with exponential backoff before degrading

  FALLBACK TIER 3: GPT-4o API Failure
  ├─ Trigger: HTTP 5xx errors, timeout (>10 min), rate limit (429)
  ├─ Strategy: Model cascade fallback
  │  ├─ Primary: GPT-4o (best medical reasoning, 96% accuracy)
  │  ├─ Fallback 1: Claude 3.5 Sonnet (comparable accuracy 94%, 5x cheaper)
  │  ├─ Fallback 2: GPT-4 Turbo (older model, 92% accuracy, 2x cheaper)
  │  ├─ Fallback 3: Med-PaLM 2 (Google, specialized medical model, 90% accuracy)
  │  └─ Emergency: Route to HITL (expert clinical reviewers)
  ├─ Rate Limit Handling (HTTP 429):
  │  ├─ Detect Retry-After header (e.g., "60 seconds")
  │  ├─ Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s, 60s
  │  ├─ Queue overflow: If wait >5 min, route to HITL
  │  └─ Load shedding: Deprioritize non-urgent PAs during rate limit
  └─ Success Rate: 94% recover within fallback chain

  FALLBACK TIER 4: LLM Hallucination Detection
  ├─ Trigger: Guardrails AI detects factual error (medical contradiction)
  ├─ Examples:
  │  ├─ Cites non-existent guideline ID
  │  ├─ Incorrect ICD-10 ↔ CPT mapping
  │  ├─ Drug interaction contradiction
  │  └─ Impossible clinical timeline (procedure before diagnosis)
  ├─ Strategy: Automatic re-generation with constrained prompt
  │  ├─ Add instruction: "Cite only provided guidelines, no external knowledge"
  │  ├─ Add validation: Cross-check citations against RAG results
  │  ├─ Retry: 2 attempts with stricter constraints
  │  └─ Escalation: If hallucination persists → HITL
  ├─ Guardrails Config:
  │  ├─ Detect contradictions (98% precision)
  │  ├─ Validate medical facts against UMLS ontology
  │  ├─ Check citation validity (all cited IDs exist in RAG results)
  │  └─ Response time: Hallucination Rate: 0.8% detected | 0.1% false positives

  DEGRADED MODE (Emergency Clinical Review):
  ├─ Scenario: All LLM APIs + RAG services unavailable (disaster scenario)
  ├─ Action: Queue ALL PA requests to HITL (100% human review)
  ├─ Staffing: Activate on-call clinical reviewers (24/7 coverage)
  ├─ SLA Extension: Automatic 30-min → 4-hour SLA for all cases
  ├─ Notification: Email all providers + members about delays
  └─ Recovery: Batch reprocess queued PAs when services restored

  OPTIMIZATION STRATEGIES (Critical for 8-min Bottleneck):

  1️⃣ RAG Caching (40% Hit Rate → Save 3.2 min):
     • Cache Key: diagnosis_codes + procedure_code + guideline_version
     • Cache Storage: Redis (guideline embeddings + retrieval results)
     • TTL: 30 days (guidelines update monthly)
     • Hit Rate: 40% (common diagnosis-procedure pairs)
     • Savings: Skip RAG retrieval (2.7s) + reduce context preparation (2s)
     • Impact: 40% × 50K requests/day × 4.7 sec = 261 hours/day compute saved

  2️⃣ Parallel RAG Execution (Already Implemented):
     • Sequential: Vector (45ms) → Keyword (85ms) → Graph (120ms) = 250ms
     • Parallel: Promise.all([vector, keyword, graph]) = 120ms (max latency)
     • Speedup: 2.1x faster (52% reduction)
     • Impact: 20 queries: 5 sec → 2.4 sec (2.6 sec savings per request)

  3️⃣ Streaming Responses (SSE - Server-Sent Events):
     • Traditional: Wait 8 min → receive complete response
     • Streaming: Receive tokens progressively (100 tokens/sec)
     • Benefit: Start parsing early decisions (approve/deny in first 10 sec)
     • Early Termination: If deny decision + reasoning in first 30 sec, stop generation
     • Impact: 15% of denials complete in 30 sec (vs. 8 min)

  4️⃣ GPT-4o Turbo Testing (20% Latency Reduction):
     • Hypothesis: GPT-4o Turbo faster than GPT-4o (same accuracy)
     • A/B Test: 10% traffic to Turbo, 90% to standard
     • Results (Jan 2026 test):
     │  ├─ Latency: 8 min → 6.4 min (20% faster) ✅
     │  ├─ Accuracy: 96% → 95.5% (0.5% drop) ⚠️
     │  ├─ Cost: $0.78 → $0.52 (33% cheaper) ✅
     │  └─ Decision: Gradual rollout to 100% (acceptable accuracy trade-off)
     • Expected Impact: 1.6 min × 50K/day = 1,333 hours/day saved

  5️⃣ Speculative Execution (Start DecisionAgent Early):
     • Scenario: ClinicalAgent generates high-confidence decision early (>0.95)
     • Strategy: Pre-warm DecisionAgent (load context, start inference)
     • Risk: If final decision changes, abort DecisionAgent (wasted compute)
     • Success Rate: 85% of high-confidence cases don't change
     • Impact: Save 20 sec on 85% × 72% auto-approved = 61% of requests

  6️⃣ Guideline Summarization (Reduce Token Count):
     • Problem: Full guidelines are verbose (2,000 tokens each)
     • Solution: Pre-summarize guidelines offline (GPT-4o-mini)
     │  ├─ Nightly batch job: Summarize all 5M guidelines
     │  ├─ Compression: 2,000 tokens → 500 tokens (75% reduction)
     │  ├─ Store: Milvus (embed summarized version)
     │  └─ Quality: Manual review of 1,000 summaries (98% retain key info)
     • Impact: Input tokens: 20K → 8K (60% reduction, $0.18 savings/request)

  7️⃣ Smart Retry with Reduced Context:
     • First Attempt: Full context (20 guidelines, 3 similar cases)
     • Retry 1: Reduced context (10 guidelines, 1 similar case) if timeout
     • Retry 2: Minimal context (5 guidelines, no cases) if timeout again
     • Retry 3: Zero-shot (no RAG, LLM knowledge only) → route to HITL
     • Impact: Graceful degradation vs. hard failure

  SECURITY CONTROLS (Highest Sensitivity - Medical Decisions):

  🔐 Authentication:
  ├─ Multi-Factor Auth: Clinical reviewers require MFA (TOTP)
  ├─ Role-Based Access: Only licensed clinicians can override agent
  ├─ Audit Logging: All clinical decisions logged (7-year retention)
  └─ Access Reviews: Quarterly review of clinical agent permissions

  🛡️ Data Protection:
  ├─ PHI Minimization: Only necessary clinical data in LLM prompts
  ├─ De-identification: Replace patient names with "Patient A" in prompts
  ├─ Prompt Injection Defense: Validate inputs (block malicious instructions)
  ├─ Response Filtering: Redact any accidentally generated PHI (regex scan)
  └─ Secure Prompts: System prompts version-controlled, change-controlled

  🚨 Guardrails & Safety:
  ├─ Hallucination Detection: Guardrails AI validates medical facts (99.9% safety)
  ├─ Citation Required: All clinical claims must cite sources (100% enforcement)
  ├─ Contradiction Detection: Flag conflicting medical statements
  ├─ Bias Detection: Monitor for demographic bias (race, gender, age)
  │  ├─ Approval Rate by Race: White 72%, Black 71%, Hispanic 73% (within 2% variance)
  │  ├─ Approval Rate by Gender: Male 72%, Female 72% (no bias detected)
  │  └─ Approval Rate by Age: Toxicity Filter: Block offensive/harmful language (0 incidents)

  🔬 Model Governance:
  ├─ Model Cards: Document GPT-4o training data, limitations, biases
  ├─ Version Control: Track GPT-4o version (gpt-4o-2024-05-13)
  ├─ A/B Testing: Test new models on 10% traffic before rollout
  ├─ Rollback Plan: Instant rollback to previous model if accuracy drops
  └─ Human Oversight: 28% HITL review rate (quality monitoring)

  METRICS & EVALUATION (Most Critical Agent):

  📊 Performance Metrics:
  ├─ Latency Distribution:
  │  ├─ P50: 7.2 min (median, 50% complete within 7.2 min)
  │  ├─ P75: 9.5 min (75% complete within 9.5 min)
  │  ├─ P95: 12 min (95% complete within 12 min)
  │  ├─ P99: 18 min (99% complete within 18 min)
  │  └─ SLA: 15 min (92% compliance, below 95% target ⚠️)
  ├─ Throughput: 100 requests/hour peak (0.027 req/sec)
  ├─ Bottleneck Impact: 53% of total PA processing time
  └─ Optimization Goal: Reduce to 5 min (target for Q2 2026)

  📈 Accuracy Metrics:
  ├─ Medical Necessity Determination: 96% accuracy
  │  ├─ True Positives: 94% (correctly approved medically necessary)
  │  ├─ True Negatives: 98% (correctly denied non-necessary)
  │  ├─ False Positives: 2% (incorrectly approved)
  │  ├─ False Negatives: 6% (incorrectly denied)
  │  └─ Ground Truth: Expert clinical reviewer consensus (3 reviewers)
  ├─ Overturn Rate: 4% by human reviewers
  │  ├─ Overturn Reasons: New evidence (40%), Clinical judgment (35%), Policy interpretation (25%)
  │  └─ Learning Loop: Overturn cases fed back to training data
  ├─ Confidence Calibration: 94% (predicted confidence vs. actual accuracy)
  │  ├─ High Confidence (>0.95): 98% accurate (well-calibrated)
  │  ├─ Medium Confidence (0.80-0.95): 92% accurate
  │  ├─ Low Confidence (Use: Low confidence → automatic HITL routing
  ├─ Citation Accuracy: 99% (cited guidelines exist and support claim)
  ├─ Hallucination Rate: 0.8% detected | 0.1% false positives
  └─ Inter-Rater Reliability: Cohen's Kappa 0.89 (strong agreement with humans)

  💰 Cost Metrics:
  ├─ Per Request Cost: $0.78 avg (highest cost agent)
  │  ├─ RAG Retrieval: $0.02 (Milvus + Elasticsearch + Neo4j compute)
  │  ├─ GPT-4o Inference: $0.72 (31K input + 16K output tokens)
  │  ├─ Guardrails Validation: $0.03 (hallucination detection)
  │  └─ Compute (K8s pods): $0.01
  ├─ Daily Cost: 50K × $0.78 = $39,000/day
  ├─ Monthly Cost: $1.17M/month (76% of total AI costs)
  ├─ Cost per Token: $0.015/1K input, $0.060/1K output (GPT-4o pricing)
  └─ Optimization Impact:
     ├─ RAG Caching (40% hit): Save $15,600/day ($468K/month)
     ├─ Token Reduction (60%): Save $14,040/day ($421K/month)
     ├─ GPT-4o Turbo (20% faster, 33% cheaper): Save $12,870/day ($386K/month)
     └─ Total Potential Savings: $42,510/day ($1.28M/month, 109% ROI)

  🔐 Security Metrics:
  ├─ Prompt Injection Attempts: 0.01% detected and blocked
  ├─ PHI Leakage: 0 incidents (response filtering 100% effective)
  ├─ Hallucination Detection: 0.8% flagged | 99% blocked before delivery
  ├─ Bias Audit: Quarterly review, Guardrails Uptime: 99.99% (critical safety system)
  └─ Clinical Oversight: 28% HITL review rate (quality monitoring)

  🎯 Business Impact Metrics:
  ├─ Time Savings: 8 min agent vs. 45 min human review (83% reduction)
  ├─ Cost Savings: $0.78 agent vs. $15 human labor (95% reduction)
  ├─ Scalability: 50K requests/day (vs. 1,200/day manual capacity)
  ├─ Consistency: 96% accuracy (vs. 92% human inter-rater reliability)
  └─ Annual ROI: $450M savings (automation of 72% of 50K daily PAs)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ AGENT 5: POLICY AGENT - Fallback & Security


###   PRIMARY EXECUTION PATH:

  ├─ 1. Load policy documents from PostgreSQL (100K+ policies)
  ├─ 2. Evaluate OPA rules (50+ Rego policy rules)
  ├─ 3. Claude 3.5 Sonnet interpretation (complex policy language)
  └─ 4. Compliance validation (HIPAA, state mandates)
     Success Rate: 94% | Latency: 2.5 min avg

  FALLBACK TIER 1: Claude 3.5 Sonnet Failure
  ├─ Trigger: HTTP 5xx, timeout (>5 min), rate limit (429)
  ├─ Strategy: Model cascade
  │  ├─ Primary: Claude 3.5 Sonnet (best policy reasoning, 200K context)
  │  ├─ Fallback 1: GPT-4o (comparable accuracy 93%, but 128K context limit)
  │  ├─ Fallback 2: GPT-4 Turbo (older, 92% accuracy)
  │  └─ Emergency: OPA rules only (no LLM, 85% accuracy, conservative)
  └─ Success Rate: 95% recover within cascade

  FALLBACK TIER 2: OPA Service Unavailable
  ├─ Trigger: OPA container crash, network timeout
  ├─ Strategy: Embedded OPA fallback
  │  ├─ Run OPA in-process (embedded mode, no external service)
  │  ├─ Load policy bundle from local cache (last successful bundle)
  │  ├─ Performance: Slower (100ms vs. 10ms) but functional
  │  └─ Staleness: Acceptable (policies update daily, Success Rate: 100% (always have local policy copy)


###   OPTIMIZATION STRATEGIES:


  1️⃣ Policy Caching:
     • Cache Key: policy_id + version + input_hash
     • TTL: 7 days (policies stable)
     • Hit Rate: 55% (common policy questions)
     • Savings: Skip Claude call (2.5 min → 0.1 sec)

  2️⃣ OPA Pre-computation:
     • Materialized Decisions: Pre-compute common policy scenarios
     • Example: "Is PA required for CPT 99213 under Gold PPO?" → cache answer
     • Coverage: Top 500 CPT codes × 20 plan types = 10K pre-computed
     • Impact: 50% of requests answered instantly (0.1 sec)


###   SECURITY CONTROLS:


  🔐 Policy Integrity:
  ├─ Git Versioning: All OPA policies in Git (semantic versioning)
  ├─ Code Review: 2-person approval + compliance officer sign-off
  ├─ Automated Testing: 500+ unit tests per policy release
  ├─ Immutable Audit: All policy changes logged (who, when, why, diff)
  └─ Rollback Capability: Instant rollback to previous policy version

  🛡️ Compliance Monitoring:
  ├─ HIPAA Validation: Ensure policies comply with HIPAA Privacy Rule
  ├─ State Mandate Tracking: 50-state policy variations
  ├─ Regulatory Updates: Automated alerts on CMS LCD/NCD changes
  └─ Annual Audit: External compliance audit (SOC2 Type II)


###   METRICS & EVALUATION:


  📊 Performance: P50 2.2 min | P95 4 min | P99 7 min
  📈 Accuracy: 94% policy interpretation | 6% require legal review
  💰 Cost: $0.111/request | $5,550/day | $167K/month
  🔐 Security: 100% policy changes audited | 0 unauthorized modifications


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### 🛡️ AGENTS 6-11: CONDENSED FALLBACK, OPTIMIZATION & SECURITY


  AGENT 6: FRAUD AGENT (Custom GNN)

  Fallback Strategies:
  ├─ Tier 1: GPU unavailable → CPU inference (10x slower, 45s → 7.5 min)
  ├─ Tier 2: Neo4j down → Rule-based fraud detection (70% accuracy vs. 96%)
  ├─ Tier 3: Model failure → Conservative scoring (flag all high-risk → HITL)
  └─ Degraded Mode: Accept low-cost (Optimizations:
  • Graph Caching: Cache fraud patterns (30-day TTL), 40% hit rate
  • Batch Inference: Process 100 requests in single GPU batch (5x faster)
  • Model Quantization: INT8 (vs. FP32), 4x smaller, 2x faster, 1% accuracy loss
  • Embeddings Pre-computation: Pre-compute provider/patient embeddings nightly

  Security:
  • Model Access: Only fraud investigation team can access GNN internals
  • Explainability: SHAP values for every fraud score (audit trail)
  • Bias Monitoring: No demographic correlation with fraud scores
  • False Positive Review: Weekly review of high-risk denials

  Metrics:
  📊 Latency: P50 40s | P95 75s | P99 120s
  📈 Accuracy: Precision 94%, Recall 98%, F1 0.96
  💰 Cost: $0.05/request (GPU compute)
  🔐 Security: 0 fraud score leaks | 100% explainability

  ──────────────────────────────────────────────────────────────────────────

  AGENT 7: DECISION AGENT (GPT-4o)

  Fallback Strategies:
  ├─ Tier 1: GPT-4o timeout → Use deterministic rules (if all confidences >0.90)
  ├─ Tier 2: Conflicting agent outputs → Conservative decision (deny or HITL)
  ├─ Tier 3: All agents failed → Automatic HITL routing (100% human review)
  └─ Degraded Mode: Simple approval logic (eligibility + no fraud → approve)

  Optimizations:
  • Early Decision: If all agents high confidence (>0.95), skip LLM (use rules)
  • Streaming: SSE streaming for faster reasoning display
  • Confidence Aggregation: Weighted ensemble (Clinical 50%, Policy 30%, Fraud 20%)
  • HITL Pre-warming: Load HITL queue context while DecisionAgent runs

  Security:
  • Decision Audit: 100% of decisions logged (immutable PostgreSQL)
  • Override Authorization: Only medical directors can override
  • Bias Detection: Monitor approval rates across demographics
  • Transparency: Full reasoning + citations in audit log

  Metrics:
  📊 Latency: P50 28s | P95 50s | P99 90s
  📈 Accuracy: 96% (3% overturn by human reviewers)
  💰 Cost: $0.27/request
  🔐 Security: 100% audit coverage | 0 unauthorized overrides

  ──────────────────────────────────────────────────────────────────────────

  AGENT 8: NOTIFICATION AGENT (GPT-3.5 Turbo)

  Fallback Strategies:
  ├─ Tier 1: SendGrid API down → Twilio SendGrid backup account
  ├─ Tier 2: SMS (Twilio) down → Email fallback (retry SMS later)
  ├─ Tier 3: LLM unavailable → Use pre-generated templates (no personalization)
  └─ Degraded Mode: Queue notifications, batch send when services restored

  Optimizations:
  • Template Caching: 25 pre-rendered HTML templates (instant load)
  • Batch Sending: SendGrid batch API (100 emails/request)
  • Async Processing: Kafka event-driven (non-blocking)
  • Smart Routing: Email only (vs. email+SMS+portal) if opt-in preferences

  Security:
  • PHI in Transit: TLS 1.3 encryption (email, SMS)
  • PII Redaction: Mask SSN, account numbers in notifications
  • Consent Management: Honor opt-out preferences (CAN-SPAM, TCPA)
  • Audit Logging: All notifications logged (delivery status, timestamps)

  Metrics:
  📊 Latency: P50 55s | P95 90s | P99 150s
  📈 Delivery Rate: 99.5% (email 99.8%, SMS 99.2%)
  💰 Cost: $0.004/request (very low)
  🔐 Security: 0 PHI leakage incidents | 100% consent compliance

  ──────────────────────────────────────────────────────────────────────────

  AGENT 9: AUDIT AGENT (GPT-4o)

  Fallback Strategies:
  ├─ Tier 1: Elasticsearch down → Write-through to PostgreSQL only
  ├─ Tier 2: LLM unavailable → Structured logging only (no summary generation)
  └─ Degraded Mode: Buffer logs in Kafka (24-hour retention), replay when restored

  Optimizations:
  • Async Processing: Non-blocking (doesn't affect PA workflow)
  • Batch Indexing: Elasticsearch bulk API (1000 events/batch)
  • Log Compression: gzip compress old logs (90% size reduction)
  • Tiered Storage: Hot (7 days SSD) → Warm (90 days HDD) → Cold (7 years S3)

  Security:
  • Immutable Logs: Append-only (no deletion or modification)
  • Encryption: AES-256 at rest, TLS 1.3 in transit
  • Access Control: Audit logs readable only by compliance team
  • Retention: 7-year HIPAA retention (automatic archival to S3 Glacier)

  Metrics:
  📊 Latency: Real-time (async, AGENT 10: APPEALS AGENT (GPT-4o)

  Fallback Strategies:
  ├─ Tier 1: GPT-4o unavailable → Claude 3.5 Sonnet fallback
  ├─ Tier 2: RAG down → Use original PA decision context only
  ├─ Tier 3: All services down → Queue to priority HITL (medical director review)
  └─ Degraded Mode: Extend SLA from 30 days to 60 days (regulatory allowed)

  Optimizations:
  • Delta Processing: Only re-evaluate changed evidence (vs. full re-review)
  • Historical Context: Load original PA decision from episodic memory
  • Peer-to-Peer Scheduling: Auto-schedule clinical peer discussions
  • Overturn Learning: Feed overturn decisions back to ClinicalAgent training

  Security:
  • Appeals Tracking: Separate database table (pa_appeals)
  • Multi-Level Approval: Overturns require medical director sign-off
  • External Review: 10% random sample to independent review organization
  • Reporting: State-mandated appeals metrics (quarterly reports)

  Metrics:
  📊 Latency: P50 8 min | P95 15 min | P99 30 min (SLA: 30 days)
  📈 Overturn Rate: 40% approved | 30% partial | 30% upheld
  💰 Cost: $0.585/request (similar to ClinicalAgent)
  🔐 Security: 100% appeals audited | 0 regulatory violations

  ──────────────────────────────────────────────────────────────────────────

  AGENT 11: COM AGENT (GPT-4o - Coordination of Benefits)

  Fallback Strategies:
  ├─ Tier 1: External payer API down → Use cached COB determination (90-day TTL)
  ├─ Tier 2: 270/271 EDI timeout → Manual COB form (fax/email to member)
  ├─ Tier 3: GPT-4o unavailable → Rule-based COB (birthday rule, active/inactive)
  └─ Degraded Mode: Assume single payer (process normally, flag for COB verification)

  Optimizations:
  • COB Caching: Cache primary payer determination (90-day TTL), 70% hit rate
  • Parallel API Calls: Query multiple payers concurrently (Promise.all)
  • Smart Timeout: 30s timeout per payer, fail-fast on slow APIs
  • Pre-determination: Pre-populate COB during eligibility check (speculative)

  Security:
  • Multi-Payer Privacy: Minimal data sharing with external payers
  • API Security: mTLS for payer-to-payer communication
  • Consent: Member consent required for COB data sharing
  • Audit: All external API calls logged (EDI transaction tracking)

  Metrics:
  📊 Latency: P50 4.5 min | P95 8 min | P99 15 min
  📈 Accuracy: 92% (complex cross-payer logic)
  💰 Cost: $0.69/request (external API fees)
  🔐 Security: 0 data leakage to external payers | 100% consent compliance


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### 🎯 CROSS-CUTTING CONCERNS (All 11 Agents)



###   RATE LIMITING & THROTTLING:


  🚦 Per-Agent Rate Limits:
  ├─ IntakeAgent: 100 uploads/min per user (prevent DoS)
  ├─ ClinicalAgent: 50 requests/min to GPT-4o (OpenAI limit: 10K TPM)
  ├─ FraudAgent: 200 inferences/min (GPU batch size limit)
  ├─ NotificationAgent: 1000 emails/min (SendGrid tier limit)
  └─ All Agents: 100 MCP tool calls/min per agent (gateway limit)

  🔄 Backpressure Handling:
  ├─ Queue Depth Monitoring: Alert when pending >1000 requests
  ├─ Load Shedding: Reject low-priority requests during peak (HTTP 503)
  ├─ Priority Queues: Urgent PAs (emergency procedures) bypass queue
  ├─ Autoscaling: HPA scales agent pods based on queue depth
  └─ Circuit Breaker: Open circuit after 5 consecutive failures (fail-fast)


###   OBSERVABILITY & MONITORING:


  📊 Distributed Tracing (Jaeger):
  ├─ Trace ID: Propagated through all 11 agents (W3C Trace Context)
  ├─ Spans: 50-100 spans per PA request (agent calls, tool calls, DB queries)
  ├─ Critical Path: Visualize bottleneck in DAG (ClinicalAgent 53% of time)
  ├─ Flamegraph: Identify slow operations (LLM inference vs. RAG retrieval)
  └─ Sampling: 100% of errors, 10% of successful requests (reduce volume)

  📈 Metrics (Prometheus + Grafana):
  ├─ Agent Latency: Histogram with P50/P95/P99 percentiles
  ├─ Agent Accuracy: Gauge (updated hourly from HITL feedback)
  ├─ Error Rate: Counter by error type (timeout, hallucination, validation)
  ├─ Token Usage: Counter (input + output tokens per agent)
  ├─ Cost Tracking: Gauge ($0.78/request ClinicalAgent, $0.003 EligibilityAgent)
  ├─ Queue Depth: Gauge (pending workflows per agent)
  └─ SLA Compliance: Gauge (99.2% within 30-min SLA, target 99.5%)

  🚨 Alerting (PagerDuty):
  ├─ P1 (Critical): Agent error rate >5%, all LLM APIs down, data loss
  ├─ P2 (High): P95 latency >25 min, SLA compliance P3 (Medium): Cache hit rate 500, cost spike >20%
  └─ P4 (Low): New agent version deployed, configuration change

  📝 Logging (Structured JSON):
  ├─ Format: {"timestamp", "level", "agent", "workflow_id", "message", "metadata"}
  ├─ Levels: ERROR (failures), WARN (degraded), INFO (normal), DEBUG (detailed)
  ├─ Storage: Elasticsearch (hot 7 days) → S3 (warm 90 days) → Glacier (7 years)
  ├─ Retention: ERROR logs 7 years (HIPAA), INFO logs 90 days
  └─ PII Masking: Regex-based redaction (SSN, DOB, account numbers)


###   COST MANAGEMENT & OPTIMIZATION:


  💰 Per-Agent Cost Breakdown (50K requests/day):
  ├─ IntakeAgent: $0.285 × 50K = $14,250/day ($427K/month)
  ├─ EligibilityAgent: $0.003 × 50K = $150/day ($4.5K/month)
  ├─ BenefitsAgent: $0.30 × 50K = $15,000/day ($450K/month)
  ├─ ClinicalAgent: $0.78 × 50K = $39,000/day ($1.17M/month) ★ HIGHEST
  ├─ PolicyAgent: $0.111 × 50K = $5,550/day ($167K/month)
  ├─ FraudAgent: $0.05 × 50K = $2,500/day ($75K/month)
  ├─ DecisionAgent: $0.27 × 50K = $13,500/day ($405K/month)
  ├─ NotificationAgent: $0.004 × 50K = $200/day ($6K/month)
  ├─ AuditAgent: $0.195 × 50K = $9,750/day ($293K/month)
  ├─ AppealsAgent: $0.585 × 1K = $585/day ($17.5K/month, 2% volume)
  ├─ COMAgent: $0.69 × 7.5K = $5,175/day ($155K/month, 15% volume)
  └─ TOTAL DAILY COST: $105,660/day ($3.17M/month)

  📉 Cost Optimization Strategies (Projected Savings):
  ├─ ClinicalAgent RAG Caching (40%): Save $15,600/day ($468K/month)
  ├─ ClinicalAgent Token Reduction (60%): Save $14,040/day ($421K/month)
  ├─ ClinicalAgent GPT-4o Turbo (33%): Save $12,870/day ($386K/month)
  ├─ EligibilityAgent Caching (85%): Save $128/day ($3.8K/month)
  ├─ BenefitsAgent Policy Pre-compute (70%): Save $10,500/day ($315K/month)
  ├─ FraudAgent Model Quantization (INT8): Save $1,250/day ($37.5K/month)
  └─ TOTAL POTENTIAL SAVINGS: $54,388/day ($1.63M/month, 51% reduction)
     Optimized Cost: $51,272/day ($1.54M/month)

  📊 ROI Calculation:
  ├─ Current AI Cost: $3.17M/month
  ├─ Optimized AI Cost: $1.54M/month (after optimizations)
  ├─ Manual Processing Cost: $10.5M/month (50K × $7/request human labor)
  ├─ Cost Savings: $10.5M - $1.54M = $8.96M/month
  ├─ Annual Savings: $107.5M/year
  └─ ROI: 693% (for every $1 spent on AI, save $6.93)


###   DISASTER RECOVERY & BUSINESS CONTINUITY:


  🔄 Multi-Region Deployment:
  ├─ Active-Active: 2 regions (US East, US West) load balanced
  ├─ Failover: Automatic DNS failover (Route 53 health checks)
  ├─ Data Replication: PostgreSQL streaming replication (cross-region)
  ├─ Cache Replication: Redis cluster replication (async, RTO: 5 min (Recovery Time Objective) | RPO: 1 min (Recovery Point Objective)

  🧪 Chaos Engineering (Litmus 3.0):
  ├─ Monthly Drills: Simulate agent failures, database outages, network partitions
  ├─ Scenarios: GPT-4o down, Redis crash, PostgreSQL failover, network split
  ├─ Success Criteria: Degraded mode activates, HITL routing works, no data loss
  └─ Learnings: Document failure modes, improve fallback logic

  🔐 Security Incident Response:
  ├─ Detection: Real-time anomaly detection (Datadog Security Monitoring)
  ├─ Response: 15-min P1 response (on-call security engineer)
  ├─ Containment: Isolate affected agents, revoke compromised credentials
  ├─ Investigation: Forensic analysis (audit logs, network traffic)
  ├─ Recovery: Restore from backup, patch vulnerability
  └─ Post-Mortem: Blameless review, update runbooks, improve defenses


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### Memory_MCP_Architecture


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### MEMORY MANAGEMENT & MCP TOOL CALLING ARCHITECTURE

Short-Term | Long-Term | Episodic | Semantic | MCP Client-Server | Tool Registry

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### 🧠 3-TIER MEMORY ARCHITECTURE


  TIER 1: SHORT-TERM MEMORY (Working Memory - Redis Cluster)

  Technology Stack:
  • Database: Redis 7.0 Cluster (3 shards, 3 replicas)
  • Capacity: 26GB total (8.6GB per shard)
  • TTL: 6 hours (session timeout)
  • Eviction Policy: LRU (Least Recently Used)
  • Operations: 500M ops/day (1M reads/sec, 100K writes/sec)
  • Latency: P50 Purpose: Active conversation context for ongoing PA requests

  Data Structures (Redis):
  1️⃣ Session Context (Hash):
     Key: session:{workflow_id}
     Fields: pa_request_id, member_id, current_agent, agent_outputs (JSON),
              progress (0-1), created_at, updated_at, ttl_expires_at
     TTL: 21,600 seconds (6 hours)
     Example: session:WF-20260608-104523 → {
                 "pa_request_id": "PA-20260608-104523",
                 "member_id": "M12345",
                 "current_agent": "ClinicalAgent",
                 "progress": 0.65,
                 "agent_outputs": {
                   "IntakeAgent": {"confidence": 0.97, "diagnosis": ["E11.9"], "procedure": ["99213"]},
                   "EligibilityAgent": {"is_eligible": true, "plan": "Gold_PPO"},
                   "BenefitsAgent": {"pa_required": true, "tier": "gold"}
                 },
                 "created_at": "2026-06-08T10:45:23Z",
                 "ttl_expires_at": "2026-06-08T16:45:23Z"
              }

  2️⃣ Conversation History (List):
     Key: conversation:{workflow_id}
     Value: [
       {"role": "user", "content": "Submit PA for procedure 99213", "timestamp": "..."},
       {"role": "assistant", "content": "Processing PA request...", "timestamp": "..."},
       {"role": "function", "name": "member_lookup", "result": {...}, "timestamp": "..."}
     ]
     TTL: 6 hours | Max Length: 100 messages (LTRIM to remove oldest)

  3️⃣ Agent State (Hash):
     Key: agent_state:{agent_name}:{workflow_id}
     Fields: status (in_progress|completed|failed), start_time, progress (0-1),
              current_step, steps_completed[], steps_remaining[], retry_count, last_error
     Example: agent_state:ClinicalAgent:WF-20260608-104523 → {
                 "status": "in_progress",
                 "start_time": "2026-06-08T10:50:00Z",
                 "progress": 0.65,
                 "current_step": "rag_retrieval",
                 "retry_count": 0
              }

  4️⃣ Tool Call Results Cache (Hash):
     Key: tool_result:{tool_name}:{call_id}
     Fields: tool, input (JSON), output (JSON), duration_ms, cached (bool), timestamp
     TTL: 300 seconds (5 minutes - short cache for tool results)
     Example: tool_result:member_lookup:abc123 → {
                 "tool": "member_lookup",
                 "input": {"member_id": "M12345"},
                 "output": {"name": "John Doe", "plan": "Gold_PPO", "status": "active"},
                 "duration_ms": 45,
                 "cached": false
              }

  Cache Patterns:
  • Write-Through: Update Redis cache on every state change
  • Cache-Aside: Read from cache first, populate on miss from PostgreSQL
  • Refresh-Ahead: Async refresh before TTL expiry (TTL Invalidation: Event-driven via Kafka events (claim update → invalidate cache)

  High Availability:
  • Replication: Synchronous to 2 replicas (quorum: 2/3 nodes must acknowledge)
  • Failover: Automatic via Redis Sentinel (3 instances), Persistence: RDB snapshots every 5 minutes + AOF append-only file
  • Backup: Daily snapshots to Azure Blob Storage (30-day retention, AES-256)

  ──────────────────────────────────────────────────────────────────────────

  TIER 2: EPISODIC MEMORY (Long-Term Event History - PostgreSQL)

  Technology Stack:
  • Database: PostgreSQL 15 (partitioned by month)
  • Storage: 6TB (SSD for hot data, HDD for warm data)
  • Records: 50M PA episodes, 550M agent executions (11 agents × 50M PA)
  • Retention: 7 years (HIPAA requirement)
  • Query Latency: P50 50ms | P95 200ms | P99 500ms
  • Access Pattern: Read-heavy 80% (5 read replicas)

  Purpose: Historical PA decisions, similar case precedents, audit trail

  Schema Design:

  1️⃣ pa_episodes Table (50M rows):
     Columns: episode_id (UUID PK), workflow_id (unique), member_id, provider_npi,
              diagnosis_codes (TEXT[]), procedure_codes (TEXT[]), clinical_summary,
              decision (approved|denied|pended), decision_reasoning, decision_confidence,
              agent_outputs (JSONB - all 11 agent outputs),
              hitl_required, auto_approved, appeal_filed, overturn,
              created_at, updated_at
     Partitioning: RANGE by created_at (monthly partitions)
     Indexes: idx_member (member_id, created_at DESC),
               idx_diagnosis (diagnosis_codes GIN), idx_procedure (procedure_codes GIN),
               idx_decision (decision, created_at DESC)
     Example Partition: pa_episodes_2026_06 FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')

  2️⃣ agent_execution_log Table (550M rows):
     Columns: execution_id (UUID PK), workflow_id, agent_name,
              model_name, input_tokens, output_tokens, total_tokens,
              latency_ms, confidence_score, input (JSONB), output (JSONB),
              error, retry_count, created_at
     Partitioning: RANGE by created_at (monthly partitions)
     Indexes: idx_workflow_agent (workflow_id, agent_name),
               idx_agent_created (agent_name, created_at DESC),
               idx_agent_latency (agent_name, latency_ms)
     Purpose: Performance monitoring, cost tracking, debugging

  3️⃣ similar_cases Materialized View (Fast Retrieval):
     Definition: SELECT diagnosis_codes, procedure_codes, decision,
                  AVG(decision_confidence) as avg_confidence, COUNT(*) as case_count,
                  array_agg(episode_id ORDER BY created_at DESC) as similar_episode_ids
              FROM pa_episodes WHERE decision IN ('approved', 'denied')
                AND created_at > NOW() - INTERVAL '2 years' AND decision_confidence > 0.90
              GROUP BY diagnosis_codes, procedure_codes, decision HAVING COUNT(*) >= 3
     Indexes: GIN on diagnosis_codes, GIN on procedure_codes, B-tree on case_count DESC
     Refresh: Daily (REFRESH MATERIALIZED VIEW CONCURRENTLY)

  Episodic Memory Retrieval Algorithm:
  1. Query by Similarity: Find cases with overlapping diagnosis + procedure codes
  2. Calculate Jaccard Similarity: |A ∩ B| / |A ∪ B| for diagnosis and procedure sets
  3. Temporal Decay: Weight recent cases higher (exponential decay, half-life 180 days)
  4. Outcome Filtering: Only retrieve successful (approved) cases with confidence >0.90
  5. Top-K Selection: Return top 5 most similar cases
  6. Context Injection: Inject into LLM prompt as few-shot examples

  Example Query (Similar Cases):
  ```sql
  SELECT episode_id, diagnosis_codes, procedure_codes, decision, decision_reasoning,
         -- Jaccard similarity for diagnosis codes
         (COUNT(*) FROM unnest(diagnosis_codes) WHERE d = ANY($1)) * 1.0 /
         (COUNT(DISTINCT d) FROM unnest(diagnosis_codes || $1)) AS diag_similarity,
         -- Temporal decay factor
         CASE WHEN created_at > NOW() - INTERVAL '3 months' THEN 1.0
              WHEN created_at > NOW() - INTERVAL '6 months' THEN 0.8
              WHEN created_at > NOW() - INTERVAL '1 year' THEN 0.6 ELSE 0.4 END AS recency_weight
  FROM pa_episodes
  WHERE diagnosis_codes && $1::TEXT[] AND procedure_codes && $2::TEXT[]
    AND decision = 'approved' AND decision_confidence > 0.90
    AND created_at > NOW() - INTERVAL '2 years'
  ORDER BY (diag_similarity + proc_similarity) * recency_weight DESC, created_at DESC
  LIMIT 5;
  ```

  Backup & Archival Strategy:
  • Hot Data (0-2 years): PostgreSQL on SSD, P95 Warm Data (2-5 years): PostgreSQL on HDD, P95 Cold Data (5-7 years): Azure Blob Storage (Parquet format, Snappy compression 60%)
  • PITR Backup: Point-in-time recovery every 5 minutes, 35-day retention

  ──────────────────────────────────────────────────────────────────────────

  TIER 3: SEMANTIC MEMORY (Learned Knowledge - Milvus Vector Store)

  Technology Stack:
  • Database: Milvus 2.3 (distributed vector database)
  • Storage: 1.2TB vectors (10M embeddings × 1024 dimensions × 4 bytes)
  • Index: HNSW (Hierarchical Navigable Small World)
  • Query Latency: P50 25ms | P95 45ms | P99 80ms
  • Access Pattern: Read-only (updated via batch jobs)
  • Embedding Model: BGE-large-en-v1.5 (1024-dimensional)

  Purpose: Conceptual knowledge, learned patterns, generalized insights

  Collections (3 total):

  1️⃣ case_embeddings (2M vectors):
     Content: PA case summaries (diagnosis + procedure + outcome + reasoning)
     Schema: id (INT64), episode_id (VARCHAR), embedding (FLOAT_VECTOR 1024),
              member_id, diagnosis, procedure, decision, confidence, created_at (INT64)
     Index: HNSW (M=16, efConstruction=200, metric=IP for cosine similarity)
     Update Frequency: Daily batch (new approved cases from last 24 hours)
     Purpose: Find similar historical cases via semantic search

  2️⃣ pattern_embeddings (500K vectors):
     Content: Discovered patterns from association rule mining
     Example: "Type 2 diabetes + BMI >30 + HbA1c >9% → insulin approved 95% (support: 2,500 cases)"
     Schema: id, pattern_id, embedding (FLOAT_VECTOR 1024), pattern_text,
              support_count (# cases), confidence (0-1), lift (vs baseline), discovered_at
     Index: HNSW (M=16, efConstruction=200)
     Update Frequency: Weekly (pattern mining job on last 7 days' approved cases)
     Algorithm: Apriori + FP-Growth (min_support=0.05, min_confidence=0.80)

  3️⃣ guideline_embeddings (5M vectors):
     Content: Clinical guidelines (MCG, InterQual, CMS LCD/NCD)
     Schema: id, guideline_id, embedding (FLOAT_VECTOR 1024), title,
              guideline_type (mcg|interqual|cms), version, effective_date, category
     Index: HNSW (M=16, efConstruction=200)
     Update Frequency: Monthly (guideline refresh from vendors)

  Semantic Search Implementation:
  1. Embed Query: Current PA description → BGE-large-en-v1.5 → 1024-dim vector
  2. HNSW Search: Find top 20 most similar embeddings (ef=64 for quality)
  3. Metadata Filter: decision='approved', created_at > 2024-01-01
  4. Rerank: Apply temporal decay factor (exponential, half-life 180 days)
  5. Top-K Selection: Return top 5-10 results
  6. Context Injection: Inject learned patterns/guidelines into LLM prompt

  HNSW Index Parameters (Tuning):
  • M (connections/node): 16 (balanced memory vs recall)
  • efConstruction (build quality): 200 (balanced build time vs recall)
  • ef (search quality): 64 (balanced latency vs recall)
  • Performance: 95% recall@10, P95 45ms, 2,000 QPS, 1.2TB index size

  Pattern Mining (Weekly Batch Job):
  • Input: Last 7 days' approved PA cases (3,500/week × 72% = 2,520 cases)
  • Algorithm: Association rule mining (Apriori, FP-Growth)
  • Output: Patterns like "diagnosis A + procedure B → approved (95% confidence, lift 1.8)"
  • Storage: Embed pattern text → store in pattern_embeddings collection
  • Usage: ClinicalAgent retrieves relevant patterns to guide decisions

  ──────────────────────────────────────────────────────────────────────────

  MEMORY INTEGRATION FLOW (3-Tier Query on Every PA Request)

  Scenario: ClinicalAgent processes PA request for Type 2 Diabetes + CGM device

  Step 1: Query Short-Term Memory (Redis)
  ├─ GET session:{workflow_id} → Retrieve current conversation context
  ├─ LRANGE conversation:{workflow_id} 0 -1 → Get message history
  ├─ HGETALL agent_state:ClinicalAgent:{workflow_id} → Get agent progress
  └─ Result: Current context (member_id, diagnosis, procedure, prior agent outputs)
     Latency: P95 Step 2: Query Episodic Memory (PostgreSQL)
  ├─ SQL query to find 5 similar historical cases (same diagnosis + procedure)
  ├─ Calculate Jaccard similarity + apply temporal decay
  └─ Result: 5 approved cases with reasoning (e.g., "Approved: Patient meets MCG criteria...")
     Latency: P95 Context Size: ~3,000 tokens

  Step 3: Query Semantic Memory (Milvus)
  ├─ Embed PA description → 1024-dim vector
  ├─ Search case_embeddings (top 10 similar cases)
  ├─ Search pattern_embeddings (top 5 relevant patterns)
  ├─ Search guideline_embeddings (top 10 clinical guidelines)
  └─ Result: Similar cases, learned patterns, relevant guidelines
     Latency: P95 Context Size: ~15,000 tokens (guidelines) + 2,000 tokens (patterns)

  Step 4: Call MCP Tools (see MCP section below)
  ├─ MCP Client → MCP Gateway → RAG MCP Server
  ├─ Hybrid RAG search (vector + keyword + graph + RRF)
  └─ Result: Top 10 RAG results with clinical guidelines
     Latency: ~280ms (cached: 20ms)
     Context Size: ~5,000 tokens

  Step 5: Synthesize Context for LLM
  ├─ Combine: Current context + Similar cases (episodic) + Patterns (semantic) + Guidelines (semantic + RAG)
  ├─ Total Context Size: ~25,000 tokens (within GPT-4o 128K limit)
  └─ Construct prompt: "You are a clinical PA reviewer. Based on these guidelines and similar cases..."

  Step 6: LLM Inference (GPT-4o)
  ├─ Call OpenAI API with enriched context
  ├─ Latency: ~8 minutes (GPT-4o inference)
  └─ Output: Decision (Approve/Deny) + Reasoning + Confidence score

  Step 7: Update Short-Term Memory (Redis)
  ├─ HSET session:{workflow_id} agent_outputs → Update with ClinicalAgent output
  ├─ HSET agent_state:ClinicalAgent:{workflow_id} status completed
  └─ Latency: Step 8: Persist to Episodic Memory (PostgreSQL - After PA Decision)
  ├─ INSERT INTO pa_episodes (...) → Store complete episode
  ├─ INSERT INTO agent_execution_log (...) × 11 → Store all agent executions
  ├─ Trigger: Nightly batch job → Embed case → Store in Milvus (semantic memory)
  └─ Latency: ~100ms (async, non-blocking)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### 🔧 MCP (MODEL CONTEXT PROTOCOL) TOOL CALLING ARCHITECTURE


  OVERVIEW: MCP enables AI agents to call external tools (APIs, databases, functions) in a standardized way
  Architecture: MCP Client (Agent) ↔ MCP Gateway ↔ MCP Server (Tool Provider)
  Protocol: JSON-RPC 2.0 over HTTP/WebSocket
  Security: OAuth2 tokens, mTLS (Istio), rate limiting, RBAC (OPA)

  ──────────────────────────────────────────────────────────────────────────

  COMPONENT 1: MCP CLIENT (Embedded in AI Agents)

  Location: Each of 11 agents has MCP client SDK embedded
  Technology: @modelcontextprotocol/sdk (TypeScript/Python)
  Purpose: Discover and call tools via MCP protocol

  Examples of Agent → Tool Mapping:
  • IntakeAgent: document_ocr, image_classify, handwriting_ocr
  • EligibilityAgent: member_lookup, eligibility_check, benefit_lookup
  • ClinicalAgent: rag_search, guideline_search, code_lookup, drug_interaction
  • PolicyAgent: policy_lookup, opa_evaluate, compliance_check
  • FraudAgent: fraud_score, risk_assessment, pattern_match
  • NotificationAgent: send_email, send_sms, send_slack

  MCP Client Workflow (TypeScript):

  1️⃣ Initialize & Connect:
     ```typescript
     import { Client } from '@modelcontextprotocol/sdk/client/index.js';
     const mcpClient = new Client({name: "ClinicalAgent", version: "2.1.0"},
                                  {capabilities: {tools: {}}});
     await mcpClient.connect(new StdioClientTransport({
       command: "mcp-gateway",
       args: ["--agent", "ClinicalAgent", "--endpoint", "http://mcp-gateway:8080"]
     }));
     ```

  2️⃣ Discover Tools:
     ```typescript
     const tools = await mcpClient.listTools();
     // Returns: [
     //   {name: "rag_search", description: "Hybrid RAG retrieval", inputSchema: {...}},
     //   {name: "member_lookup", description: "Get member details", inputSchema: {...}},
     //   ... 20+ more tools
     // ]
     ```

  3️⃣ Call Tool:
     ```typescript
     const result = await mcpClient.callTool({
       name: "rag_search",
       arguments: {
         query: "Type 2 diabetes prior authorization guidelines",
         top_k: 10,
         filters: {guideline_type: "mcg", effective_date: ">2024-01-01"}
       }
     });
     // Returns: {content: [{type: "text", text: JSON.stringify({results: [...], latency_ms: 265})}]}
     ```

  4️⃣ Process Result & Inject into LLM:
     ```typescript
     const ragData = JSON.parse(result.content[0].text);
     const guidelines = ragData.results.map(r => `${r.guideline_id}: ${r.title}`).join("\n");
     const llmPrompt = `Based on these guidelines:\n${guidelines}\n\nEvaluate PA request...`;
     const llmResponse = await openai.chat.completions.create({model: "gpt-4o", messages: [...]});
     ```

  MCP Client Configuration (per Agent):
  ```json
  {
    "mcpServers": {
      "rag-server": {
        "command": "mcp-gateway",
        "args": ["--server", "rag-server"],
        "env": {"RAG_ENDPOINT": "http://rag-mcp-server:8080", "TIMEOUT": "30000"}
      },
      "member-server": {
        "command": "mcp-gateway",
        "args": ["--server", "member-server"],
        "env": {"MEMBER_API": "http://member-service:9090", "CACHE_TTL": "3600"}
      }
    }
  }
  ```

  ──────────────────────────────────────────────────────────────────────────

  COMPONENT 2: MCP GATEWAY (Central Tool Router & Orchestrator)

  Deployment: Kubernetes deployment (pa-platform namespace)
  Replicas: 10 pods (HPA: auto-scale 3-50 based on CPU/QPS)
  Technology: Node.js + MCP SDK + Kong API Gateway + Redis cache
  Purpose: Route tool calls, load balancing, caching, rate limiting, circuit breaker

  Architecture:
  ```
  ┌─────────────────────────────────────────────────────────────────┐

###   │                      MCP GATEWAY                                │

  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
  │  │   Router    │  │    Cache    │  │ Rate Limiter│            │
  │  │  (Kong)     │  │   (Redis)   │  │  (100/min)  │            │
  │  └─────────────┘  └─────────────┘  └─────────────┘            │
  │         ↓                ↓                  ↓                   │
  │  ┌────────────────────────────────────────────────┐            │
  │  │       Tool Registry (PostgreSQL)               │            │
  │  │  tool_name | server_endpoint | input_schema    │            │
  │  └────────────────────────────────────────────────┘            │
  └─────────────────────────────────────────────────────────────────┘
           ↓                  ↓                  ↓
    ┌──────────┐       ┌──────────┐       ┌──────────┐

###     │  MCP     │       │  MCP     │       │  MCP     │

    │  Server  │       │  Server  │       │  Server  │
    │  (RAG)   │       │ (Member) │       │  (OCR)   │
    └──────────┘       └──────────┘       └──────────┘
  ```

  Gateway Features:

  1️⃣ Tool Registry (PostgreSQL):
     ```sql
     CREATE TABLE mcp_tool_registry (
       tool_name VARCHAR(100) UNIQUE NOT NULL,
       tool_description TEXT,
       server_endpoint VARCHAR(500) NOT NULL,
       input_schema JSONB NOT NULL,
       rate_limit INT DEFAULT 100,  -- Calls per minute
       enabled BOOLEAN DEFAULT true
     );
     ```
     Examples: rag_search, member_lookup, fraud_score, document_ocr (20+ tools total)

  2️⃣ Caching (Redis):
     Cache Key: tool_cache:{tool_name}:{hash(arguments)}
     TTL: 5 minutes (configurable per tool)
     Hit Rate: 35% (varies by tool: rag_search 30%, member_lookup 60%)
     Invalidation: Event-driven (Kafka events trigger cache clear)
     Example: Cache HIT → 20ms latency (vs 280ms for rag_search)

  3️⃣ Rate Limiting:
     Per Agent: 100 tool calls/minute per tool
     Global: 1,000 calls/minute per tool (total across all agents)
     Storage: Redis counters with 60-second expiry
     Response: HTTP 429 (Too Many Requests) if exceeded
     Algorithm: Token bucket (100 tokens/min refill rate)

  4️⃣ Circuit Breaker:
     Threshold: 5 consecutive failures → OPEN circuit for 60 seconds
     Purpose: Prevent cascading failures, fail-fast on broken servers
     States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED
     Metrics: Prometheus metrics for failure rate, circuit state

  5️⃣ Load Balancing:
     Strategy: Round-robin across MCP server replicas
     Health Checks: HTTP /healthz endpoint every 5 seconds
     Example: RAG MCP Server has 5 replicas → Gateway routes to healthy replicas only

  6️⃣ Observability:
     Tracing: Jaeger distributed tracing (trace tool call: Client → Gateway → Server)
     Metrics: Prometheus (tool_call_duration, tool_call_count, cache_hit_rate)
     Logging: Structured JSON logs (agent, tool, args, result, latency)
     Audit: PostgreSQL audit_log table (7-year retention for HIPAA)

  Gateway Implementation (Simplified TypeScript):
  ```typescript
  mcpGateway.setRequestHandler('tools/call', async (request) => {
    const { name, arguments: args } = request.params;

    // 1. Rate limiting check
    const rateLimitKey = `rate_limit:${name}:${agentName}`;
    if (await redis.incr(rateLimitKey) > 100) throw new Error("Rate limit exceeded");

    // 2. Check cache
    const cacheKey = `tool_cache:${name}:${hash(args)}`;
    const cached = await redis.get(cacheKey);
    if (cached) return { content: [{ type: "text", text: cached }] };

    // 3. Circuit breaker check
    if (await isCircuitOpen(name)) throw new Error("Circuit breaker OPEN");

    // 4. Route to MCP server
    const toolConfig = toolRegistry.get(name);
    const response = await axios.post(`${toolConfig.endpoint}/tools/${name}`, args);

    // 5. Cache result
    await redis.setex(cacheKey, 300, JSON.stringify(response.data));

    return { content: [{ type: "text", text: JSON.stringify(response.data) }] };
  });
  ```

  ──────────────────────────────────────────────────────────────────────────

  COMPONENT 3: MCP SERVERS (Tool Providers - 20+ Servers)

  Server Categories (8 categories, 20+ servers):

  1️⃣ RAG MCP Server: rag_search, vector_search, keyword_search, graph_search
     Replicas: 5 | Tech: Node.js + Milvus + Elasticsearch + Neo4j
     Endpoint: http://rag-mcp-server:8080
     Tools: rag_search (hybrid: vector + keyword + graph + RRF)

  2️⃣ Member MCP Server: member_lookup, eligibility_check, benefit_lookup
     Replicas: 10 | Tech: Python + PostgreSQL
     Endpoint: http://member-mcp-server:8080
     Tools: Query member service (5M members, P95 Provider MCP Server: provider_lookup, npi_validation, network_check
     Replicas: 5 | Tech: Python + PostgreSQL
     Endpoint: http://provider-mcp-server:8080
     Tools: Validate NPI, check network status (in/out of network)

  4️⃣ Policy MCP Server: policy_lookup, opa_evaluate, compliance_check
     Replicas: 8 | Tech: Go + Open Policy Agent
     Endpoint: http://policy-mcp-server:8080
     Tools: Evaluate policies (OPA Rego), HIPAA/NCQA compliance checks

  5️⃣ Clinical MCP Server: guideline_search, code_lookup, drug_interaction
     Replicas: 5 | Tech: Python + Milvus
     Endpoint: http://clinical-mcp-server:8080
     Tools: ICD-10/CPT code lookup, drug interaction checks

  6️⃣ OCR MCP Server: document_extract, image_classify, handwriting_ocr
     Replicas: 10 | Tech: Python + Azure Vision API
     Endpoint: http://ocr-mcp-server:8080
     Tools: Extract text from PDFs/images, OCR handwritten forms

  7️⃣ Notification MCP Server: send_email, send_sms, send_slack
     Replicas: 3 | Tech: Node.js + SendGrid + Twilio
     Endpoint: http://notification-mcp-server:8080
     Tools: Send notifications (email, SMS, Slack)

  8️⃣ Analytics MCP Server: fraud_score, risk_assessment, pattern_match
     Replicas: 5 | Tech: Python + scikit-learn + XGBoost
     Endpoint: http://analytics-mcp-server:8080
     Tools: ML models for fraud detection, risk scoring

  MCP Server Implementation Example (RAG Server - TypeScript):
  ```typescript
  ragServer.setRequestHandler('tools/call', async (request) => {
    const { name, arguments: args } = request.params;
    if (name !== "rag_search") throw new Error(`Unknown tool: ${name}`);

    const { query, top_k = 10, filters = {} } = args;
    const startTime = Date.now();

    // 1. Vector search (Milvus)
    const queryEmbedding = await embedModel.encode(query);
    const vectorResults = await milvus.search({
      collection_name: "guideline_embeddings", vector: queryEmbedding, limit: top_k
    });

    // 2. Keyword search (Elasticsearch)
    const keywordResults = await elasticsearch.search({
      index: "clinical_content", body: {query: {match: {content: query}}, size: top_k}
    });

    // 3. Graph search (Neo4j)
    const graphResults = await neo4jSession.run(
      "MATCH (g:Guideline)-[:SUPPORTS]->(p:Procedure) WHERE g.title CONTAINS $query RETURN g LIMIT $top_k",
      { query, top_k }
    );

    // 4. Reciprocal Rank Fusion (RRF)
    const fusedResults = performRRF([vectorResults, keywordResults, graphResults], k=60);

    return {
      content: [{
        type: "text",
        text: JSON.stringify({
          results: fusedResults.slice(0, top_k),
          latency_ms: Date.now() - startTime,
          sources: {vector: vectorResults.length, keyword: keywordResults.length, graph: graphResults.length}
        })
      }]
    };
  });
  ```

  Kubernetes Deployment (RAG MCP Server):
  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: rag-mcp-server
    namespace: pa-platform
  spec:
    replicas: 5
    selector:
      matchLabels:
        app: rag-mcp-server
    template:
      spec:
        containers:
        - name: rag-mcp-server
          image: acr.azurecr.io/rag-mcp-server:v2.1.0
          ports:
          - containerPort: 8080
          env:
          - name: MILVUS_ENDPOINT
            value: "milvus:19530"
          - name: ELASTICSEARCH_ENDPOINT
            value: "http://elasticsearch:9200"
          - name: NEO4J_URI
            value: "bolt://neo4j:7687"
          resources:
            requests: {cpu: 2000m, memory: 4Gi}
            limits: {cpu: 4000m, memory: 8Gi}
  ```

  ──────────────────────────────────────────────────────────────────────────

  COMPLETE MCP TOOL CALLING FLOW (End-to-End)

  Scenario: ClinicalAgent needs to search clinical guidelines

  Step 1: Agent Discovers Tools
  ├─ ClinicalAgent (MCP Client) → MCP Gateway
  ├─ Request: GET /tools/list
  ├─ Response: [{name: "rag_search", description: "...", inputSchema: {...}}, ...]
  └─ Latency: 10ms

  Step 2: Agent Calls Tool
  ├─ ClinicalAgent → MCP Gateway
  ├─ Request: POST /tools/call
  │  Body: {name: "rag_search", arguments: {query: "Type 2 diabetes insulin therapy", top_k: 10}}
  └─ Latency (Gateway processing): 5ms

  Step 3: Gateway Routes to MCP Server
  ├─ MCP Gateway checks:
  │  ├─ Tool exists in registry? ✓
  │  ├─ Rate limit OK? ✓ (45/100 calls in last minute)
  │  ├─ Cache hit? ✗ (cache miss)
  │  └─ Circuit breaker open? ✗ (closed, healthy)
  ├─ Load balance: Round-robin to RAG MCP Server replica 3/5
  ├─ Forward request: POST http://rag-mcp-server-3:8080/tools/rag_search
  └─ Latency (Gateway → Server): 10ms (K8s service mesh)

  Step 4: MCP Server Executes Tool
  ├─ RAG MCP Server:
  │  ├─ Embed query → 1024-dim vector (15ms)
  │  ├─ Vector search (Milvus) → 10 results (45ms)
  │  ├─ Keyword search (Elasticsearch) → 10 results (85ms)
  │  ├─ Graph search (Neo4j) → 10 results (120ms) [parallel execution]
  │  ├─ RRF fusion → Top 10 ranked (15ms)
  │  └─ Total: 280ms
  └─ Return: {results: [{guideline_id: "MCG-A0123", title: "Diabetes Management", relevance: 0.95}, ...]}

  Step 5: Gateway Caches Result
  ├─ MCP Gateway:
  │  ├─ Store in Redis: SET tool_cache:rag_search:hash "{results}" EX 300
  │  ├─ Record metrics: tool_call_duration{tool="rag_search"} = 280ms
  │  └─ Return to agent
  └─ Latency (Server → Gateway → Client): 20ms

  Step 6: Agent Processes Result
  ├─ ClinicalAgent:
  │  ├─ Extract guideline titles: "MCG-A0123: Diabetes Management", "MCG-A0456: Insulin Therapy", ...
  │  ├─ Inject into LLM prompt: "Based on these guidelines:\n- MCG-A0123...\n\nEvaluate PA request..."
  │  ├─ Call GPT-4o with enriched context
  │  └─ Receive decision + reasoning
  └─ Total Tool Call Latency: 315ms (cache HIT: 25ms)

  Performance Breakdown:
  • MCP Client → Gateway: 5ms
  • Gateway processing (rate limit, cache check): 5ms
  • Gateway → MCP Server: 10ms
  • Tool execution (RAG): 280ms
  • MCP Server → Gateway: 5ms
  • Gateway → MCP Client: 10ms
  • Total: 315ms (or 25ms if cached)

  ──────────────────────────────────────────────────────────────────────────


###   SECURITY & GOVERNANCE


  Authentication:
  • MCP Client: JWT token issued by Keycloak (expires in 1 hour)
  • MCP Gateway: Validates JWT signature + claims (sub, exp, aud)
  • MCP Server: mTLS via Istio service mesh (automatic certificate rotation)

  Authorization (RBAC):
  • Tool Permissions: Define which agents can call which tools (stored in OPA policy)
  • Example Policy (Rego):
    ```rego
    allow { input.agent_name == "ClinicalAgent"; input.tool_name == "rag_search" }
    allow { input.agent_name == "EligibilityAgent"; input.tool_name == "member_lookup" }
    ```
  • Enforcement: MCP Gateway calls OPA for authorization before routing

  Rate Limiting:
  • Per Agent: 100 calls/minute per tool
  • Global: 1,000 calls/minute per tool (total)
  • Response: HTTP 429 if exceeded
  • Monitoring: Alert if any agent approaches 80% of limit

  Audit Logging:
  ```sql
  CREATE TABLE tool_execution_log (
    execution_id UUID PRIMARY KEY,
    agent_name VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    arguments JSONB NOT NULL,
    result JSONB,
    execution_time_ms INT,
    success BOOLEAN NOT NULL,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW()
  );
  -- Retention: 7 years (HIPAA compliance)
  ```

  Cost Tracking:
  • Per Tool Call: $0.001 avg (compute + data transfer)
  • Daily Cost: 1M tool calls × $0.001 = $1,000/day
  • Monthly Cost: $30,000/month
  • Breakdown: rag_search (40%), member_lookup (25%), fraud_score (15%), others (20%)

  ──────────────────────────────────────────────────────────────────────────

  PERFORMANCE METRICS (Memory + MCP Combined)

  Memory System:
  • Redis (Short-Term): P50 PostgreSQL (Episodic): P50 50ms | P95 200ms | P99 500ms
  • Milvus (Semantic): P50 25ms | P95 45ms | P99 80ms

  MCP Tool Calls:
  • Total Latency: P50 150ms | P95 500ms (avg 315ms, cached 25ms)
  • Cache Hit Rate: 35% (varies: rag_search 30%, member_lookup 60%)
  • Daily Volume: 1M tool calls/day (11 agents × 50K PA × 2 tools avg)
  • Peak QPS: 2,000 calls/second (9-11 AM)

  End-to-End (Per PA Request):
  • Memory Query (3-tier): ~300ms total (parallel: Redis + PostgreSQL + Milvus)
  • MCP Tool Calls: ~315ms avg (2 tool calls per PA request)
  • LLM Inference: ~8 minutes (GPT-4o bottleneck)
  • Total PA Processing: ~8.5 minutes avg (15-min SLA, 99.2% compliance)

  Daily Stats:
  • PA Requests: 50,000/day
  • Agent Invocations: 385,000/day (7 agents avg per PA)
  • Memory Queries: 385,000/day (3-tier query per agent)
  • Tool Calls: 1M/day (2-3 tools per agent)
  • Cache Operations: 500M/day (Redis)
  • Vector Searches: 100K/day (Milvus)

  Cost Breakdown:
  • Memory Storage: $5K/month (Redis $2K, PostgreSQL $2K, Milvus $1K)
  • MCP Tools: $30K/month (compute + data transfer)
  • LLM Inference: $1.5M/month (GPT-4o: $52K/day)
  • Total: $1.535M/month


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


---

## 12. Embedded RAG / Data / Gateway Notes

### RAG_Complete


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### RAG RETRIEVAL LAYER - HYBRID SEARCH ALGORITHMS

Vector + Keyword + Graph | Reciprocal Rank Fusion | 250ms E2E Latency

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### 🎯 HYBRID RAG ARCHITECTURE

  Three-Source Retrieval Strategy:
  1. Vector Search (Semantic): Milvus HNSW → 45ms P95
  2. Keyword Search (Lexical): Elasticsearch BM25 → 85ms P95
  3. Graph Search (Relational): Neo4j Cypher → 120ms P95
  → Reciprocal Rank Fusion (RRF) → 15ms processing
  → Final Top-10 Results → 250ms total (parallel execution)

  Query Pattern (20 queries per PA request):
  • 8 Vector queries (40%): Semantic similarity
  • 6 Keyword queries (30%): Exact term matching
  • 4 Graph queries (20%): Relationship traversal
  • 2 Memory queries (10%): Case precedents

  Performance Metrics:
  • Daily Query Volume: 50K PA × 20 queries = 1M queries/day
  • Cache Hit Rate: 40% (saves 3.2 min per request)
  • Accuracy: 96% relevant results in top 10
  • Coverage: 99.5% queries return ≥1 result


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### COMPONENT 1: VECTOR SEARCH (MILVUS 2.3)

  Embedding Model:
  • Model: BGE-large-en-v1.5 (BAAI)
  • Dimension: 1024 dimensions
  • Max Input: 512 tokens (medical terminology optimized)
  • Inference: 15ms per embedding (batch 32)

  HNSW Index Parameters:
  • Index Type: HNSW (Hierarchical Navigable Small World)
  • M (connections per node): 16
  • ef_construction (build quality): 200
  • ef_search (runtime quality): 64
  • Distance Metric: Inner Product (IP) for normalized vectors

  Collections (3 total, 10M vectors):
  1. clinical_guidelines (5M vectors):
     • Content: MCG, InterQual, Hayes, specialty guidelines
     • Chunks: 512-token chunks with 50-token overlap
     • Metadata: guideline_id, version, effective_date, category
  2. policy_documents (3M vectors):
     • Content: Medical policies, drug policies, admin policies
     • Chunks: 256-token chunks (policies are more concise)
     • Metadata: policy_id, type, state, effective_date
  3. case_precedents (2M vectors):
     • Content: Historical PA decisions with outcomes
     • Chunks: Full case summaries (average 800 tokens)
     • Metadata: case_id, decision, diagnosis, procedure, date

  Search Algorithm:
  1. Embed query using BGE-large model (15ms)
  2. Normalize query vector (L2 norm)
  3. HNSW approximate nearest neighbor search:
     • Start at entry point (highest layer)
     • Greedily traverse to nearest neighbors
     • Descend layers until bottom (layer 0)
     • Expand search with ef=64 candidate list
  4. Re-rank top 100 candidates by exact distance
  5. Filter by metadata (effective date, category)
  6. Return top 20 results with scores

  Performance Tuning:
  • Latency P50: 25ms | P95: 45ms | P99: 80ms
  • Throughput: 2,000 QPS per collection
  • Memory: 1.2TB RAM (10M × 1024 × 4 bytes + index overhead)
  • Recall@10: 95% (vs. brute force)

  Optimization Strategies:
  • Partition by date: Reduce search space (recent guidelines more relevant)
  • GPU Acceleration: NVIDIA T4 for batch embedding
  • Load Balancing: 3 Milvus nodes (round-robin)
  • Cache: Redis cache for frequent queries (40% hit rate)


### COMPONENT 2: KEYWORD SEARCH (ELASTICSEARCH 8)

  BM25 Algorithm (Best Match 25):
  • Formula: score = IDF × (TF × (k1 + 1)) / (TF + k1 × (1 - b + b × (doc_len / avg_doc_len)))
  • k1 parameter: 1.2 (term frequency saturation)
  • b parameter: 0.75 (length normalization)
  • IDF: log((N - df + 0.5) / (df + 0.5)) (inverse document frequency)

  Index Configuration:
  • Shards: 5 primary shards
  • Replicas: 2 replicas per shard (HA)
  • Documents: 500K+ (clinical content, policies)
  • Index Size: 400GB (includes inverted index + doc values)
  • Refresh Interval: 30 seconds (near real-time)

  Analyzer Pipeline:
  1. Character Filters:
     • HTML Strip: Remove HTML tags from web-scraped content
     • Mapping: Normalize medical abbreviations (MI → myocardial infarction)
  2. Tokenizer:
     • Standard Tokenizer: Split on whitespace, punctuation
  3. Token Filters:
     • Lowercase: Normalize case
     • Stop Words: Remove common words (the, a, an, etc.)
     • Synonym: Expand medical synonyms (diabetes → DM, T2DM)
     • Stemmer: Porter stemmer for English (running → run)
     • Edge N-Gram: Support partial matching (diabet → diabetes)

  Field Boosting (Multi-field search):
  • title^3: Title field 3x weight (highest relevance)
  • summary^2: Summary field 2x weight
  • content^1: Full content field 1x weight (default)
  • metadata^0.5: Metadata field 0.5x weight (lower relevance)

  Fuzzy Matching:
  • Levenshtein Distance: ≤2 character edits allowed
  • Prefix Length: 3 (first 3 chars must match exactly)
  • Use Case: Typo tolerance (diabtes → diabetes)

  Highlighting:
  • Fragments: 3 fragments per document
  • Fragment Size: 150 characters
  • Pre/Post Tags:  for highlighting

  Performance:
  • Latency P50: 50ms | P95: 85ms | P99: 150ms
  • Throughput: 1,000 QPS (CPU-bound)
  • Cache: Query result cache (1-hour TTL, 30% hit rate)


### COMPONENT 3: GRAPH SEARCH (NEO4J 5.X)

  Graph Schema:
  • Nodes (500K total):
    - Patient (5M historical)
    - Provider (500K)
    - Diagnosis (70K ICD-10 codes)
    - Procedure (10K CPT codes)
    - Medication (100K NDC codes)
    - Policy (100K policies)
    - Guideline (50K clinical guidelines)
  • Relationships (2M total):
    - DIAGNOSED_WITH: Patient → Diagnosis
    - PERFORMED: Provider → Procedure
    - REQUIRES_PA: Procedure → Policy
    - CONTRAINDICATED_WITH: Medication → Diagnosis
    - SUPPORTS: Guideline → Procedure
    - STEP_THERAPY: Medication → Medication

  Cypher Query Templates (15 pre-compiled):
  1. Pattern Matching:
     MATCH (d:Diagnosis)-[:SUPPORTS]-(g:Guideline)-[:SUPPORTS]-(p:Procedure)
     WHERE d.icd10 = 'E11.9' AND p.cpt = '99213'
     RETURN g.title, g.recommendation, g.evidence_level
  2. Path Finding:
     MATCH path = shortestPath((start:Medication)-[*..4]-(end:Diagnosis))
     WHERE start.ndc = '12345' AND end.icd10 = 'E11.9'
     RETURN path, length(path)
  3. Centrality (Fraud Detection):
     CALL gds.betweenness.stream('fraud_graph')
     YIELD nodeId, score
     WHERE score > 1000
     RETURN gds.util.asNode(nodeId).name, score
     ORDER BY score DESC LIMIT 10

  Graph Algorithms (via GDS library):
  • Community Detection: Louvain algorithm (identify fraud rings)
  • Centrality: Betweenness, PageRank (find influential nodes)
  • Similarity: Node similarity (similar patient cohorts)
  • Path Finding: Dijkstra, A* (shortest path to approval)

  Performance Optimization:
  • Indexes: Composite indexes on frequently queried properties
  • Constraints: Unique constraints on node IDs
  • Traversal Depth: Limit to 4 hops (prevent exponential explosion)
  • Cache: Query result cache (Redis, 1-hour TTL)
  • Causal Cluster: 3-node HA cluster (read replicas)

  Query Performance:
  • Latency P50: 80ms | P95: 120ms | P99: 200ms
  • Throughput: 500 QPS (graph traversal CPU-intensive)
  • Memory: 200GB graph database


### COMPONENT 4: RECIPROCAL RANK FUSION (RRF)

  Algorithm:
  • Formula: RRF_score(d) = Σ (1 / (k + rank_i(d)))
    - d: document
    - k: constant (60 in our implementation)
    - rank_i(d): rank of document d in ranking i
    - Σ: sum over all rankings (vector, keyword, graph)

  Example Calculation:
  Document "MCG Diabetes Guideline":
  • Vector ranking: position 3 → 1/(60+3) = 0.0159
  • Keyword ranking: position 1 → 1/(60+1) = 0.0164
  • Graph ranking: position 5 → 1/(60+5) = 0.0154
  • RRF score: 0.0159 + 0.0164 + 0.0154 = 0.0477

  Normalization:
  • Min-Max Scaling: Scale all scores to [0, 1] range
  • Formula: normalized = (score - min) / (max - min)
  • Purpose: Ensure different sources are comparable

  Duplicate Removal:
  1. Exact Match: Same document ID from multiple sources
  2. Fuzzy Dedup: Cosine similarity >0.95 (near-duplicates)
  3. Keep Highest Score: Retain version with best combined score

  Final Ranking:
  • Sort by RRF score (descending)
  • Apply diversity: No more than 3 docs from same guideline
  • Return top 10 results
  • Include provenance: Which sources contributed to each result

  Processing Time:
  • RRF Calculation: 5ms (lightweight computation)
  • Deduplication: 8ms (similarity checks)
  • Sorting: 2ms
  • Total: 15ms


### RERANKING (OPTIONAL CROSS-ENCODER)

  Model: ms-marco-MiniLM-L-6-v2 (Microsoft)
  Purpose: Re-rank top 10 RRF results for final precision

  Algorithm:
  1. Take RRF top 10 results
  2. Concatenate query + document (cross-attention)
  3. Feed through cross-encoder model
  4. Get relevance score [0, 1]
  5. Re-sort by cross-encoder score

  Performance:
  • Latency: +50ms (inference for 10 docs)
  • Accuracy Improvement: +3% precision @10
  • Usage: Enabled for complex queries (>10 tokens)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### CACHING STRATEGY (40% HIT RATE → SAVES 3.2 MIN/REQUEST)

  Query Cache (Redis):
  • Key: hash(query_text + filters)
  • Value: Serialized top-10 results
  • TTL: 6 hours (guidelines don't change frequently)
  • Eviction: LRU (Least Recently Used)
  • Size: 10GB cache (stores ~1M queries)

  Guideline Cache:
  • Key: guideline_id
  • Value: Full guideline text + metadata
  • TTL: 24 hours
  • Invalidation: On guideline updates (monthly refresh)

  Cache Warming:
  • Pre-load: 1,000 most common queries on startup
  • Async Refresh: Refresh cache 1 hour before TTL expiry
  • Hit Rate Monitoring: Alert if ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### MONITORING & OBSERVABILITY

  Metrics (Prometheus):
  • Query Latency: P50, P95, P99 per source
  • Cache Hit Rate: Overall + per query type
  • Recall @10: Percentage of relevant results in top 10
  • Throughput: QPS per source
  • Error Rate: Failed queries, timeouts

  Distributed Tracing (Jaeger):
  • Span Hierarchy:
    - rag_query (parent span, 250ms)
      ├─ vector_search (child span, 45ms)
      ├─ keyword_search (child span, 85ms)
      ├─ graph_search (child span, 120ms)
      └─ rrf_fusion (child span, 15ms)

  Logging (Elasticsearch):
  • Query Logs: All queries logged with results
  • Slow Query Log: Queries >500ms (investigate)
  • Error Logs: Failed queries, empty results
  • Retention: 30 days


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### RAGLayer

RAG RETRIEVAL LAYER - LAYER 8 (Hybrid Search)
  Vector Search (Milvus 2.3):
  • Index: HNSW (Hierarchical Navigable Small World)
  • Embeddings: 10M+ vectors | Dimension: 1024
  • Latency: 45ms P95 | Top-K: 20
  • Database: Clinical guidelines, policies, case history
  Keyword Search (Elasticsearch 8):
  • Algorithm: BM25 (TF-IDF scoring)
  • Index size: 400 GB | Documents: 500K+
  • Latency: 85ms P95 | Top-K: 20
  • Features: Fuzzy matching, field boosting
  Knowledge Graph (Neo4j 5.x):
  • Nodes: 500K | Edges: 2M | Query: Cypher
  • Latency: 120ms P95 | Top-K: 10
  • Content: Disease ontology, drug interactions, provider networks
  Reciprocal Rank Fusion (RRF):
  • k-value: 60 | Score normalization
  • Duplicate removal: Deterministic
  • Latency: 15ms | Final results: Top 10
  ━━━
  Total RAG Pipeline: ~250ms (parallel execution)

### DataServices_Complete


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### DATA SERVICES LAYER - 8 MICROSERVICES API SPECS

gRPC Primary | REST Fallback | 3.5M API Calls/Day | 75% Cache Hit

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### 🎯 DATA SERVICES ARCHITECTURE OVERVIEW

  Service Mesh: Kong Enterprise (routing, rate limiting, auth)
  Protocol Stack: gRPC (primary, 70%) | REST (fallback, 30%)
  Total Daily Volume: 3.5M+ API calls (145K/hour avg)
  Response Time SLA: P95 Availability: 99.95% (multi-AZ deployment)

  Common API Patterns:
  • Authentication: OAuth 2.0 Bearer tokens (JWT)
  • Rate Limiting: 1000 req/min per service per client
  • Pagination: Cursor-based (for large datasets)
  • Versioning: URI versioning (v1, v2)
  • Error Handling: Standard HTTP status codes + error details
  • Idempotency: Idempotency-Key header for mutations

  Connection Pooling:
  • Pool Size: 50 connections per service
  • Max Idle: 10 connections
  • Connection Timeout: 30 seconds
  • Idle Timeout: 5 minutes


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SERVICE 1: MEMBER SERVICE (2M+ Members)
  Purpose: Member demographics, eligibility, enrollment
  Daily Volume: 2M queries (83K/hour)
  Protocol: gRPC + REST
  Latency: P50 25ms | P95 50ms
  Cache Hit Rate: 75% (Redis 24-hour TTL)

  gRPC API (member.proto):
  service MemberService {
    rpc GetMember(MemberRequest) returns (Member);
    rpc SearchMembers(SearchRequest) returns (MemberList);
    rpc ValidateEligibility(EligibilityRequest) returns (EligibilityResponse);
    rpc GetMemberPlans(MemberRequest) returns (PlanList);
    rpc UpdateMember(UpdateMemberRequest) returns (Member);
  }

  message Member {
    string member_id = 1;
    string first_name = 2;
    string last_name = 3;
    string dob = 4;  // ISO 8601 date
    string gender = 5;
    Address address = 6;
    repeated Plan plans = 7;
    string status = 8;  // active, inactive, termed
    google.protobuf.Timestamp effective_date = 9;
    google.protobuf.Timestamp term_date = 10;
  }

  REST API Endpoints (12 total):
  1. GET /v1/members/{member_id}
     • Description: Retrieve member details
     • Response: 200 OK + Member JSON | 404 Not Found
     • Cache: 24-hour TTL
     • Latency: P95 50ms

  2. POST /v1/members/search
     • Body: {"first_name": "John", "last_name": "Doe", "dob": "1980-01-01"}
     • Response: 200 OK + Array
     • Pagination: Cursor-based, 100 per page
     • Latency: P95 150ms

  3. GET /v1/members/{member_id}/eligibility?service_date=2024-01-15
     • Description: Check eligibility on specific date
     • Response: {"is_eligible": true, "plan": "Gold_PPO", "effective_date": "2023-01-01"}
     • Cache: 6-hour TTL
     • Latency: P95 75ms

  4. GET /v1/members/{member_id}/plans
  5. PUT /v1/members/{member_id}
  6. POST /v1/members (create new member)
  7. DELETE /v1/members/{member_id}
  8. GET /v1/members/{member_id}/dependents
  9. GET /v1/members/{member_id}/claims (delegates to ClaimsService)
  10. GET /v1/members/{member_id}/authorizations
  11. POST /v1/members/{member_id}/notes
  12. GET /v1/members/{member_id}/audit-log

  Database: PostgreSQL (members table, 5M rows)
  Indexes: member_id (PK), (last_name, first_name, dob), status
  Caching Strategy: Cache-aside pattern, Redis, 24-hour TTL
  Circuit Breaker: Fail after 5 consecutive errors, 60-sec timeout

SERVICE 2: PROVIDER SERVICE (500K+ Providers)
  Purpose: Provider directory, NPI lookup, credentialing
  Daily Volume: 500K queries (21K/hour)
  Protocol: gRPC + REST
  Latency: P50 30ms | P95 75ms
  Cache Hit Rate: 80% (providers rarely change)

  gRPC API (provider.proto):
  service ProviderService {
    rpc GetProvider(ProviderRequest) returns (Provider);
    rpc SearchProviders(SearchRequest) returns (ProviderList);
    rpc ValidateNPI(NPIRequest) returns (NPIValidationResponse);
    rpc GetProviderNetwork(NetworkRequest) returns (NetworkStatus);
    rpc SearchByGeo(GeoSearchRequest) returns (ProviderList);
  }

  message Provider {
    string provider_id = 1;
    string npi = 2;  // National Provider Identifier (10 digits)
    string first_name = 3;
    string last_name = 4;
    string organization_name = 5;
    string specialty = 6;
    repeated Address locations = 7;
    repeated string network_ids = 8;
    string credential_status = 9;  // active, inactive, suspended
    google.protobuf.Timestamp credential_expiry = 10;
  }

  REST API Endpoints (10 total):
  1. GET /v1/providers/{npi}
     • Description: Lookup provider by NPI
     • Response: 200 OK + Provider JSON
     • Cache: 7-day TTL
     • Latency: P95 75ms

  2. POST /v1/providers/search
     • Body: {"specialty": "Cardiology", "zip": "10001", "radius_miles": 25}
     • Response: Array (geo-sorted by distance)
     • Latency: P95 200ms (uses PostGIS spatial query)

  3. GET /v1/providers/{npi}/network?plan_id=GOLD_PPO
     • Description: Check if provider in-network for plan
     • Response: {"in_network": true, "tier": 1, "effective_date": "2023-01-01"}
     • Cache: 24-hour TTL

  4. POST /v1/providers/validate-npi
     • Body: {"npi": "1234567890"}
     • Response: {"valid": true, "name": "Dr. John Smith", "specialty": "Cardiology"}
     • External: Calls NPPES API (CMS registry)
     • Latency: P95 500ms (external API)

  5-10. Standard CRUD + credential management endpoints

  Database: PostgreSQL (providers table, 500K rows)
  Spatial Index: PostGIS for geo-search (lat/lon columns)
  External Integration: NPPES NPI Registry (daily sync)
  Rate Limiting: 1000 req/min per client

SERVICE 3: POLICY SERVICE (100K+ Policies)
  Purpose: Medical/drug policies, coverage rules, OPA evaluation
  Daily Volume: 100K queries (4K/hour)
  Protocol: REST (policy documents too large for gRPC)
  Latency: P50 50ms | P95 150ms
  Cache Hit Rate: 90% (policies change monthly)

  REST API Endpoints (8 total):
  1. GET /v1/policies/{policy_id}
     • Description: Get full policy document
     • Response: 200 OK + Policy JSON (average 50KB)
     • Cache: 24-hour TTL
     • Latency: P95 150ms

  2. POST /v1/policies/search
     • Body: {"cpt": "99213", "icd10": "E11.9", "state": "CA"}
     • Response: Array (matching policies)
     • Uses: Elasticsearch full-text search

  3. POST /v1/policies/evaluate
     • Body: {"policy_id": "MED-123", "input": {"age": 45, "diagnosis": "E11.9"}}
     • Response: {"decision": "approve", "reasons": [...], "rule_matches": [...]}
     • Backend: Open Policy Agent (OPA) Rego evaluation
     • Latency: P95 200ms (complex rule evaluation)

  4. GET /v1/policies/effective?date=2024-01-15&state=CA
     • Description: Get policies effective on date in state
     • Response: Array

  5. GET /v1/policies/{policy_id}/versions
  6. GET /v1/policies/{policy_id}/versions/{version_id}
  7. POST /v1/policies (admin - create new policy)
  8. PUT /v1/policies/{policy_id} (admin - update policy)

  Policy Document Structure (JSON):
  {
    "policy_id": "MED-123",
    "title": "Diabetes Management - Prior Authorization",
    "type": "medical",
    "state": "CA",
    "effective_date": "2024-01-01",
    "expiry_date": "2024-12-31",
    "version": "2.1",
    "coverage_criteria": {
      "diagnoses": ["E11.9", "E10.9"],
      "procedures": ["99213", "99214"],
      "age_range": {"min": 18, "max": 75},
      "required_trials": ["Metformin", "Sulfonylurea"]
    },
    "opa_policy": "package medical_policy.diabetes\n..."
  }

  OPA Integration:
  • Engine: Open Policy Agent (v0.58)
  • Policy Language: Rego
  • Evaluation: Database: PostgreSQL (policies table, 100K rows)
  Search Index: Elasticsearch (full-text search on policy content)
  Cache: Redis 24-hour TTL (policies rarely change intraday)

SERVICE 4: CLAIMS SERVICE (150M+ Claims)
  Purpose: Claims history, X12 EDI processing, fraud patterns
  Daily Volume: 400K queries (17K/hour)
  Protocol: REST + Batch Processing
  Latency: P50 100ms | P95 300ms (large dataset)
  Cache Hit Rate: 60% (recent claims cached)

  REST API Endpoints (15 total):
  1. GET /v1/claims/{claim_id}
     • Description: Retrieve single claim
     • Response: Claim JSON (average 10KB)
     • Latency: P95 100ms

  2. POST /v1/claims/search
     • Body: {"member_id": "M12345", "date_range": {"start": "2024-01-01", "end": "2024-01-31"}}
     • Response: Array (paginated)
     • Latency: P95 300ms

  3. GET /v1/claims/member/{member_id}?limit=100&cursor=xyz
     • Description: Get member's claims (cursor pagination)
     • Response: {"claims": [...], "next_cursor": "abc"}

  4. GET /v1/claims/provider/{npi}?start_date=2024-01-01
     • Description: Provider's claim history
     • Use Case: Fraud detection, billing patterns

  5. POST /v1/claims/validate-edi
     • Body: X12 EDI 837 transaction (healthcare claim)
     • Response: {"valid": true, "errors": []}
     • Validation: X12 schema compliance

  6. POST /v1/claims/submit
  7. PUT /v1/claims/{claim_id}/adjudicate
  8. GET /v1/claims/{claim_id}/audit-trail
  9. GET /v1/claims/fraud-score/{claim_id}
  10-15. Batch processing, status updates, reprocessing

  Claim Record Structure:
  {
    "claim_id": "CLM-20240115-104523",
    "member_id": "M12345",
    "provider_npi": "1234567890",
    "service_date": "2024-01-15",
    "submit_date": "2024-01-16",
    "diagnosis_codes": ["E11.9", "I10"],
    "procedure_codes": [{"cpt": "99213", "quantity": 1, "billed": 150.00}],
    "total_billed": 150.00,
    "total_allowed": 120.00,
    "total_paid": 96.00,
    "status": "paid",  // submitted, in_review, paid, denied
    "fraud_score": 15  // 0-100 scale
  }

  Database: PostgreSQL (claims table, 150M rows, partitioned by year)
  Partitioning: Range partition by service_date (yearly)
  Indexes: (member_id, service_date), (provider_npi, service_date), claim_id (PK)
  Data Retention: 7 years (HIPAA requirement)
  Archival: Move 5+ year data to Azure Blob cold storage

SERVICE 5: BENEFITS CONFIG SERVICE (Tier Structures)
  Purpose: Benefit plan configurations, tier structures, cost-sharing
  Daily Volume: 300K queries (12.5K/hour)
  Protocol: gRPC + REST
  Latency: P50 20ms | P95 50ms
  Cache Hit Rate: 95% (configs rarely change)

  REST API Endpoints (6 total):
  1. GET /v1/benefits/plans/{plan_id}
     • Description: Get plan configuration
     • Response: Plan JSON with tiers, copays, coinsurance, deductibles

  2. GET /v1/benefits/plans/{plan_id}/cost-share?cpt=99213&network=in
     • Description: Calculate cost sharing for procedure
     • Response: {"copay": 30, "coinsurance": 0.20, "patient_responsibility": 54}

  3. POST /v1/benefits/accumulator
     • Body: {"member_id": "M12345", "plan_id": "GOLD_PPO", "year": 2024}
     • Response: {"deductible_met": 500, "deductible_remaining": 1000, "oop_max_met": 2000, "oop_max_remaining": 4000}

  4-6. Standard CRUD for plan configurations

  Plan Structure:
  {
    "plan_id": "GOLD_PPO",
    "tier": "gold",
    "deductible": {"individual": 1500, "family": 3000},
    "oop_max": {"individual": 6000, "family": 12000},
    "coinsurance": 0.20,
    "copays": {"primary_care": 30, "specialist": 50, "er": 250},
    "network_tiers": {
      "tier1": {"coinsurance": 0.10, "providers": "preferred"},
      "tier2": {"coinsurance": 0.20, "providers": "standard"}
    }
  }

  Database: PostgreSQL (benefit_plans table, 5K rows)
  Cache: Redis 7-day TTL (plans change quarterly)

SERVICE 6: NETWORK SERVICE (In/Out-of-Network)
  Purpose: Network participation, tiering, adequacy analysis
  Daily Volume: 250K queries (10K/hour)
  Protocol: gRPC + REST
  Latency: P50 30ms | P95 80ms
  Cache Hit Rate: 85%

  REST API Endpoints (8 total):
  1. GET /v1/network/check?npi=1234567890&plan_id=GOLD_PPO
     • Description: Check if provider in-network
     • Response: {"in_network": true, "tier": 1, "effective_date": "2023-01-01"}

  2. POST /v1/network/search
     • Body: {"plan_id": "GOLD_PPO", "specialty": "Cardiology", "zip": "10001", "radius": 25}
     • Response: Array (in-network only, sorted by tier)

  3. GET /v1/network/adequacy?plan_id=GOLD_PPO&county=NY-NEW_YORK
     • Description: Network adequacy report (regulatory)
     • Response: {"specialty_coverage": {"cardiology": 95, "primary_care": 98}, "meets_standards": true}

  4-8. Network contracts, tier assignments, termination management

  Database: PostgreSQL (network_contracts table, 2M rows)
  Join Pattern: providers ⟗ network_contracts ⟗ plans
  Cache: Redis 24-hour TTL

SERVICE 7: FORMULARY SERVICE (Drug Coverage - 6 Tiers)
  Purpose: Drug coverage tiers, step therapy, quantity limits
  Daily Volume: 80K queries (3.3K/hour)
  Protocol: gRPC + REST
  Latency: P50 35ms | P95 90ms
  Cache Hit Rate: 92%

  REST API Endpoints (10 total):
  1. GET /v1/formulary/drug/{ndc}?plan_id=GOLD_PPO
     • Description: Get drug coverage details
     • Response: {"tier": 2, "covered": true, "pa_required": false, "step_therapy": [], "quantity_limit": "30 day supply"}

  2. POST /v1/formulary/search
     • Body: {"drug_name": "Metformin", "plan_id": "GOLD_PPO"}
     • Response: Array (brand + generics)

  3. GET /v1/formulary/alternatives/{ndc}?plan_id=GOLD_PPO
     • Description: Get lower-cost alternatives
     • Response: Array (sorted by tier, cost)

  4. GET /v1/formulary/step-therapy/{ndc}
     • Description: Check step therapy requirements
     • Response: {"required": true, "steps": ["Metformin", "Sulfonylurea"], "current_step": 1}

  5-10. Formulary management, exception requests, tier overrides

  Formulary Tiers (6 levels):
  • Tier 1: Generic ($10 copay)
  • Tier 2: Preferred Generic ($20 copay)
  • Tier 3: Preferred Brand ($50 copay)
  • Tier 4: Non-Preferred Brand ($100 copay)
  • Tier 5: Specialty ($250 copay or 25% coinsurance)
  • Tier 6: Experimental (not covered)

  Drug Record Structure:
  {
    "ndc": "12345-6789-01",  // National Drug Code
    "drug_name": "Metformin 500mg",
    "tier": 1,
    "covered": true,
    "pa_required": false,
    "step_therapy_required": false,
    "quantity_limit": "30 day supply",
    "age_restrictions": {"min": 18, "max": null},
    "alternatives": ["12345-6789-02", "67890-1234-01"]
  }

  Database: PostgreSQL (formulary table, 100K drugs × 1K plans = 100M rows)
  External Data: First Databank (FDB) drug database (weekly sync)
  Cache: Redis 7-day TTL

SERVICE 8: CLINICAL CONTENT SERVICE (MCG, InterQual)
  Purpose: Clinical guidelines, evidence-based criteria, coding reference
  Daily Volume: 50K queries (2K/hour)
  Protocol: REST (large documents)
  Latency: P50 100ms | P95 250ms
  Cache Hit Rate: 85%

  REST API Endpoints (12 total):
  1. GET /v1/clinical/guidelines/{guideline_id}
     • Description: Get full guideline document
     • Response: Guideline JSON (average 100KB)

  2. POST /v1/clinical/search
     • Body: {"cpt": "99213", "icd10": "E11.9", "guideline_type": "mcg"}
     • Response: Array

  3. GET /v1/clinical/mcg?code=A-0123
     • Description: Get MCG care guideline
     • Response: MCG guideline with evidence levels

  4. GET /v1/clinical/interqual?criteria=acute_inpatient&diagnosis=E11.9
     • Description: InterQual admission criteria

  5. GET /v1/clinical/codes/icd10/{code}
     • Description: ICD-10 code details
     • Response: {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"}

  6. GET /v1/clinical/codes/cpt/{code}
  7. GET /v1/clinical/codes/hcpcs/{code}
  8-12. Evidence-based medicine, specialty guidelines, CMS LCD/NCD

  Content Sources:
  • MCG (Milliman Care Guidelines): 5,000+ guidelines
  • InterQual: 2,000+ criteria sets
  • Hayes Technology Assessment: 500+ reports
  • CMS LCD/NCD: 1,000+ local/national coverage determinations
  • Specialty Societies: NCCN, AHA, ACC, etc.

  Update Frequency:
  • MCG/InterQual: Monthly updates
  • CMS LCD/NCD: Quarterly updates
  • ICD-10/CPT Codes: Annual (Oct 1)

  Database: PostgreSQL (clinical_guidelines table, 50K rows)
  Search: Elasticsearch (full-text + semantic search)
  Cache: Redis 30-day TTL (guidelines change monthly)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### CROSS-SERVICE INTEGRATION PATTERNS

  Service Choreography:
  • Pattern: Async event-driven (Kafka)
  • Events: member_updated, policy_changed, claim_submitted
  • Consumer Services: All services subscribe to relevant events

  Service Orchestration:
  • Orchestrator: Workflow Engine (LangGraph + Temporal)
  • Pattern: Saga pattern for distributed transactions
  • Compensation: Rollback on failure (e.g., undo PA approval)

  Data Consistency:
  • Pattern: Eventual consistency (via Kafka events)
  • Strong Consistency: Only within single service boundary
  • Idempotency: All write operations are idempotent

  API Gateway (Kong Enterprise):
  • Routing: 10 routes mapped to 8 services
  • Load Balancing: Round-robin across 3 instances per service
  • Rate Limiting: 1000 req/min per service per client
  • Authentication: OAuth 2.0 plugin
  • Caching: Response caching (configurable per route)
  • Monitoring: Request logging, latency tracking


### MONITORING & OBSERVABILITY

  Metrics (Prometheus):
  • Request Rate: Requests/sec per service
  • Latency: P50, P95, P99 per endpoint
  • Error Rate: 4xx/5xx errors per service
  • Cache Hit Rate: Per service
  • Connection Pool: Active/idle connections

  Distributed Tracing (Jaeger):
  • Trace Propagation: B3 headers (Zipkin compatible)
  • Span Hierarchy: Gateway → Service → Database
  • Sampling: 10% of requests (reduce overhead)

  Logging (ELK Stack):
  • Structured Logs: JSON format
  • Log Levels: DEBUG, INFO, WARN, ERROR
  • Correlation: trace_id in all logs
  • Retention: 30 days


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### DataServicesLayer

DATA SERVICES LAYER - LAYER 9 (8 Microservices)
  Core Data Services:
  • Member Service: 2M+ members | gRPC+REST | 2M queries/day
  • Provider Service: 500K+ providers | gRPC+REST | 500K queries/day
  • Policy Service: 100K+ policies | REST | 100K queries/day
  • Claims Service: 150M+ claims | REST+Batch | 400K queries/day
  Configuration Services:
  • Benefits Config: Tier structures | 300K queries/day
  • Network Service: In/out-of-network | 250K queries/day
  • Formulary Service: Drug coverage | 80K queries/day
  • Clinical Content Service: MCG, InterQual | 50K queries/day
  Performance Metrics:
  • Total daily API calls: 3.5M+
  • Average latency: 50-200ms (service dependent)
  • Cache hit rate: 75% average
  • Connection pool: 50 connections per service
  • Protocol: gRPC (primary, 2x faster) | REST (fallback)
  • Gateway: Kong Enterprise (10-gateway routing)

### DatabaseLayer

DATABASE LAYER - LAYER 9 (6 Systems, 18 TB Total)
  PostgreSQL 15 (6 TB | Primary ACID Store):
  • Databases: 6 dedicated | Tables: 30+ | Sharding: by tenant
  • Data: 5M members | 150M claims | 500K providers
  • Throughput: 10K trans/sec | Replication: synchronous
  • Backup: Daily snapshots | Retention: 35 days
  • HA: Zone-redundant | vCores: 32
  Redis 7.0 (26 GB | Cache & State Cluster):
  • Cluster: 3 shards | Replicas: 3 | 99.95% HA
  • Operations: 500M ops/day | Hit rate: 75%
  • TTL: 6-hour session, 5-min working memory
  • Data: Sessions, cache, workflow state, rate limits
  • Latency: P50: Milvus 2.3 (1.2 TB | Vector Database):
  • Vectors: 10M embeddings | Dimension: 1024
  • Index: HNSW (Hierarchical Navigable Small World)
  • Throughput: 50K searches/day | P95: 45ms
  • Collections: Clinical, Policy, Cases
  Neo4j 5.x (200 GB | Knowledge Graph):
  • Nodes: 500K | Edges: 2M relationships
  • Queries: Cypher language | Throughput: 10K/day
  • Graphs: Disease, drugs, providers, fraud patterns
  • Causal cluster: 3-node for HA
  Elasticsearch 8 (400 GB | Full-Text & Hybrid):
  • Documents: 500K+ | Shards: 5 | Replicas: 2
  • Algorithm: BM25 + Vector hybrid search
  • Throughput: 100K queries/day | P95: 85ms
  Azure Blob Storage (10 TB | Document Store):
  • Documents: PDF, DICOM, TIFF | Objects: 2M+
  • Throughput: 150K ops/day | Tier: Hot (frequent access)
  • Retention: Lifecycle policies (archive after 90 days)
  ━━━
  Per-Request Query Count: ~38 queries (5-10 per agent)

### HITLLayer

HUMAN-IN-THE-LOOP LAYER - LAYER 10 (28% of Cases)
  Routing Engine (Drools Rules):
  • Cases routed daily: 14,000 (28% of 50K)
  • Auto-approved: 36,000 (72%)
  • Rules: 50+ decision rules
  Routing Triggers:
  • Low confidence: 0.30 (5% of routed)
  • All denials: 100% review (10% of routed)
  • High-cost cases: 10% random sample (3% of routed)
  • Complex clinical: >3 agents consulted (12% of routed)
  Review Queue (React UI):
  • Queue type: Priority-based (fraud > denial > complex)
  • Assignment: Load-balanced to 50+ reviewers
  • SLA: Approval Workflow (Temporal):
  • Stages: Initial review → Escalation (if needed) → Final approval
  • Escalation: 5% of reviewed cases
  • Audit trail: 100% logged & searchable
  • Approval time: 10-120 minutes (avg: 45 min)
  • Callback: Notification via 3 channels

### GW60_Complete


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### 60-GATEWAY GENAI ORCHESTRATION ARCHITECTURE

Kong Enterprise Control Plane + LiteLLM Model Router Backbone

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



### 🎯 CONTROL PLANE HUB ARCHITECTURE

  Kong Enterprise Control Plane:
  • Central API Router: All 60 gateways managed centrally
  • Admin API: Dynamic plugin management & configuration
  • Rate Limiting Engine: Token bucket, 100 req/min per user
  • Load Balancing: Round-robin across gateway instances
  • Total Overhead: LiteLLM Model Router (Multi-Model Orchestration):
  • GPT-4o: 50% traffic (Intake, Clinical, Decision agents) - $0.015/1K input
  • Claude 3.5 Sonnet: 25% (Policy agent) - $0.003/1K input
  • GPT-3.5 Turbo: 20% (Eligibility, Benefits) - $0.001/1K input
  • Custom ML Models: 5% (Fraud detection) - Graph neural networks
  • Fallback Strategy: 3-tier automatic retry on model failure
  • Cost Optimization: Multi-model balancing achieves $52K/day ($1.04/request)
  • Routing Latency: 10ms model selection + dispatch


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIER 1: CORE GATEWAYS (4) - Foundation Layer
  1. API Gateway - REST/gRPC Router (5ms)
     ↳ Protocols: HTTP/2, gRPC, WebSocket
     ↳ Routing: Path-based, header-based, query parameter
     ↳ Load Balancing: Weighted round-robin, least connections

  2. AI Gateway - GenAI Controller (8ms)
     ↳ Orchestration: Multi-step prompt chains
     ↳ Context Management: Session persistence, state tracking
     ↳ Prompt Engineering: Template management, variable injection

  3. LLM Gateway - Model Selector (10ms)
     ↳ Model Routing: GPT-4o, Claude 3.5, GPT-3.5 selection
     ↳ Fallback Strategy: Primary → Secondary → Tertiary
     ↳ Cost Optimization: Automatic model downgrade for simple queries

  4. Agent Gateway - Multi-Agent Hub (12ms)
     ↳ Dispatch: 11 specialized agents (Intake → Decision)
     ↳ Pattern: Supervisor multi-agent (LangGraph 0.2.15)
     ↳ Coordination: Dynamic agent selection, parallel execution

TIER 2: AGENT COMMUNICATION (4) - Inter-Agent Mesh
  5. MCP Gateway - Model Context Protocol (8ms)
     ↳ Context Sharing: Cross-agent context propagation
     ↳ Tool Registry: Centralized function catalog (50+ tools)
     ↳ Resource Management: Memory, compute quotas per agent

  6. A2A Gateway - Agent-to-Agent Mesh (5ms)
     ↳ Direct Communication: Agent-to-agent message passing
     ↳ Routing: Point-to-point, broadcast, multicast
     ↳ Protocol: gRPC bidirectional streaming

  7. Multi-Agent Gateway - Supervisor Pattern (15ms)
     ↳ Coordination: Centralized workflow orchestration
     ↳ State Management: Global workflow state (Redis)
     ↳ Agent Selection: Dynamic based on confidence scores

  8. Agent Mesh Gateway - Service Mesh (3ms)
     ↳ Load Balancing: Agent instance auto-scaling
     ↳ Discovery: Service registry (Consul/Eureka)
     ↳ Health Checks: Automatic failover on agent failure

TIER 3: KNOWLEDGE & CONTEXT (5) - RAG & Memory
  9. RAG Gateway - Retrieval Orchestration (45ms) ★ CLINICAL BOTTLENECK
     ↳ Vector Search: Milvus HNSW (10M embeddings, 45ms P95)
     ↳ Hybrid Search: Elasticsearch BM25 (500K docs, 85ms P95)
     ↳ Graph RAG: Neo4j Cypher (500K nodes, 120ms P95)
     ↳ Fusion: Reciprocal Rank Fusion (k=60, top 10 results, 15ms)

  10. Knowledge Gateway - Semantic Layer (20ms)
      ↳ Knowledge Graph: Neo4j 500K nodes, 2M relationships
      ↳ Ontology: Disease taxonomy, drug interactions, procedure codes
      ↳ Query: Cypher traversal, path finding, pattern matching

  11. Context Gateway - State Management (5ms)
      ↳ Switching: Session-scoped context isolation
      ↳ Management: Context stack (push/pop operations)
      ↳ Persistence: Redis 6-hour TTL, PostgreSQL archival

  12. Memory Gateway - Memory Router (8ms)
      ↳ Episodic: 150M historical records (PostgreSQL)
      ↳ Semantic: 10M vector embeddings (Milvus)
      ↳ Working: Active session cache (Redis 5-min TTL)

  13. Vector DB Gateway - Vector Retrieval (50ms)
      ↳ Supported: Milvus, Pinecone, Weaviate, Qdrant
      ↳ Dimension: 1024-dim BGE-large embeddings
      ↳ Index: HNSW (M=16, ef_construction=200)

TIER 4: TOOL & INTEGRATION (4) - External Systems
  14. Tool Gateway - Tool Dispatcher (5ms)
      ↳ Registry: Function catalog (50+ tools)
      ↳ Invocation: Sandboxed execution (Docker containers)
      ↳ Limits: CPU 1 core, Memory 512MB, Timeout 30sec

  15. Function Calling Gateway - LLM Tool Execution (8ms)
      ↳ Binding: Automatic parameter extraction from LLM output
      ↳ Validation: JSON schema validation, type checking
      ↳ Execution: Synchronous + asynchronous execution modes

  16. Enterprise Integration Gateway - ERP/CRM APIs (25ms)
      ↳ SAP: RFC calls, BAPIs, OData services
      ↳ Oracle: PL/SQL stored procedures, REST APIs
      ↳ Salesforce: SOQL queries, Apex triggers, Streaming API

  17. SaaS Connector Gateway - Communication Platforms (15ms)
      ↳ Slack: Bot API, Events API, Interactive components
      ↳ Teams: Graph API, Activity feed, Adaptive cards
      ↳ Zendesk: Ticket API, User management, Custom fields

TIER 5: MODEL & INFERENCE (5) - ML Operations
  18. Model Gateway - Model Registry (Metadata)
      ↳ Version Control: Semantic versioning (v1.2.3)
      ↳ Metadata: Model lineage, training metrics, datasets
      ↳ Rollout: Canary deployment (10% → 50% → 100%)

  19. Inference Gateway - Batch+Stream (12ms)
      ↳ Async: Queue-based batch inference (RabbitMQ)
      ↳ Real-time: Streaming inference (Kafka Streams)
      ↳ Optimization: Dynamic batching (max 32 requests/batch)

  20. GPU Gateway - Acceleration (2ms)
      ↳ Device Affinity: GPU selection based on load
      ↳ Batching: Dynamic batch sizing (8-64 requests)
      ↳ Memory: VRAM management, model caching

  21. Model Serving Gateway - Load Balancing (5ms)
      ↳ Load Balancing: Weighted least connections
      ↳ A/B Testing: Traffic splitting (90/10, 50/50)
      ↳ Canary: Gradual rollout with automatic rollback

  22. Model Registry Gateway - MLflow Integration (10ms)
      ↳ MLflow: Experiment tracking, model registry
      ↳ Governance: Approval workflows, lineage tracking
      ↳ Lifecycle: Development → Staging → Production

TIER 6: GOVERNANCE & SECURITY (8) - Zero Trust
  23. Guardrail Gateway - Safety Enforcement (8ms)
      ↳ Hallucination Detection: Guardrails AI (99.9% safe)
      ↳ Content Filter: Toxic language, PII detection
      ↳ Output Validation: Fact-checking, source attribution

  24. AI Firewall - Prompt Injection (10ms)
      ↳ Lakera AI: Prompt injection, jailbreak detection
      ↳ Rebuff: Adversarial attack prevention
      ↳ Threat Database: 10K+ known attack patterns

  25. Agent Firewall - Agent Sandbox (5ms)
      ↳ Behavior Restrictions: API rate limits, allowed actions
      ↳ Resource Limits: CPU 80%, Memory 2GB, Disk 5GB
      ↳ Network Isolation: VPC isolation, egress filtering

  26. Security Gateway - OAuth2/JWT/mTLS (5ms)
      ↳ Authentication: Multi-factor (OAuth2 + TOTP)
      ↳ Certificate Management: Auto-renewal (Let's Encrypt)
      ↳ Token Validation: JWT signature verification, expiry

  27. Compliance Gateway - HIPAA/GDPR/SOC2 (8ms)
      ↳ Audit Enforcement: 100% request logging
      ↳ Data Residency: Geographic routing (US/EU regions)
      ↳ Retention Policies: HIPAA 6-year retention

  28. Policy Gateway - Rule Engine (10ms)
      ↳ OPA: Open Policy Agent (Rego language)
      ↳ Drools: Business rules engine (50+ rules)
      ↳ Decision Trees: Complex eligibility logic

  29. Risk Management Gateway - Anomaly Detection (12ms)
      ↳ Anomaly Detection: Statistical outlier analysis
      ↳ Risk Scoring: 0-100 scale (>30 triggers HITL)
      ↳ Fraud Patterns: Graph neural network detection

  30. Audit Gateway - Compliance Logging (15ms)
      ↳ Immutable Records: Append-only log (Elasticsearch)
      ↳ Forensic Trail: Request/response, user actions
      ↳ Retention: 7-year compliance archive

TIER 7: WORKFLOW & ORCHESTRATION (5) - Process Control
  31. Workflow Gateway - DAG Execution (8ms)
      ↳ DAG: Directed Acyclic Graph orchestration
      ↳ LangGraph: Integration (0.2.15)
      ↳ Execution: Sequential, parallel, conditional branches

  32. Orchestration Gateway - Durable Workflows (10ms)
      ↳ Temporal: Durable execution (1.22)
      ↳ Airflow: Batch workflows, scheduling
      ↳ Retry: Exponential backoff (3 attempts)

  33. HITL Gateway - Human Review (5ms)
      ↳ Routing: 28% of cases (14K/day)
      ↳ Queue Management: Priority-based (fraud > denial)
      ↳ SLA: Approval Gateway - Workflow Approvals (8ms)
      ↳ Multi-level: Manager → Director → VP chains
      ↳ Approval Chain: Sequential, parallel voting
      ↳ Escalation: 5% of cases escalated

  35. State Management Gateway - Checkpoints (5ms)
      ↳ Checkpoints: Every 30 seconds
      ↳ Snapshots: Recovery point objectives (RPO: 1 min)
      ↳ Recovery: Automatic from last checkpoint

TIER 8: OBSERVABILITY & OPERATIONS (5) - Monitoring
  36. Observability Gateway - Traces/Metrics/Logs (8ms)
      ↳ Traces: Jaeger (100% trace collection, 10-20 spans/request)
      ↳ Metrics: Prometheus (200+ metrics, 15-day retention)
      ↳ Logs: ELK Stack (centralized logging, 30-day retention)

  37. Monitoring Gateway - Real-time Dashboards (3ms)
      ↳ Prometheus: Metrics aggregation (15-second scrape)
      ↳ Grafana: 20+ dashboards, real-time visualization
      ↳ Alerts: 50+ alert rules (PagerDuty, Slack)

  38. Cost Management Gateway - $$ Tracking (5ms)
      ↳ Token Accounting: Per-request token counting
      ↳ Daily Cost: $52,000/day (~$1.04 per PA request)
      ↳ Optimization: Model downgrade recommendations

  39. Token Management Gateway - Usage Metering (8ms)
      ↳ Usage Metering: Per-user, per-agent tracking
      ↳ Rate Limiting: 100 requests/minute/user
      ↳ Quota Management: Monthly token quotas

  40. Usage Analytics Gateway - Behavior Tracking (10ms)
      ↳ Behavior Tracking: User journeys, agent patterns
      ↳ ROI Metrics: $667M annual savings
      ↳ Analytics: Mixpanel, Amplitude integration

TIER 9: DATA & ENTERPRISE (5) - Data Fabric
  41. Data Gateway - Data Router (12ms)
      ↳ SQL: PostgreSQL, MySQL, SQL Server
      ↳ NoSQL: MongoDB, DynamoDB, Cassandra
      ↳ GraphQL: Schema stitching, federation

  42. Data Access Gateway - Row-level Security (8ms)
      ↳ Databricks: Unity Catalog, column masking
      ↳ Snowflake: Row access policies, data sharing
      ↳ Access Control: Fine-grained permissions (RBAC)

  43. Data Governance Gateway - Lineage/Catalog (10ms)
      ↳ Lineage: Column-level lineage tracking
      ↳ Catalog: Data dictionary, metadata management
      ↳ PII Handling: Automatic detection, redaction

  44. Enterprise Data Gateway - Data Lake/Warehouse (15ms)
      ↳ Data Warehouse: Snowflake, Redshift, BigQuery
      ↳ Data Lake: S3, ADLS, Google Cloud Storage
      ↳ Federated Query: Cross-source SQL queries

  45. Document Gateway - Document Processing (50ms)
      ↳ OCR: Azure Form Recognizer (98.5% accuracy)
      ↳ Extract: Structured data from PDF/DICOM/TIFF
      ↳ Index: Elasticsearch full-text indexing

TIER 10: ENTERPRISE AGENT PLATFORM (8) - Agent Lifecycle
  46. Agent Registry Gateway - Agent Catalog
      ↳ Catalog: 50+ agents, semantic versioning
      ↳ Versioning: v1.2.3, backward compatibility
      ↳ Discovery: Agent search by capability

  47. Agent Discovery Gateway - Capability Matching
      ↳ Search: Natural language capability search
      ↳ Match: Skills-based agent recommendation
      ↳ Ranking: By accuracy, latency, cost

  48. Agent Marketplace Gateway - Publish/Deploy
      ↳ Publish: Agent submission, approval workflow
      ↳ Deploy: One-click deployment to production
      ↳ Monetization: Usage-based pricing

  49. Agent Lifecycle Gateway - Deploy/Monitor/Retire
      ↳ Deploy: Blue-green, canary deployment
      ↳ Monitor: Real-time health, performance metrics
      ↳ Retire: Deprecation warnings, migration paths

  50. Agent Certification Gateway - Quality/Security
      ↳ Quality Checks: Accuracy benchmarks (>95%)
      ↳ Security Validation: Penetration testing, vulnerability scans
      ↳ Compliance: HIPAA, GDPR certification

  51. Agent Trust Gateway - Reputation System
      ↳ Scoring: 96% average accuracy (monitored)
      ↳ Validation: Continuous evaluation (daily)
      ↳ Reputation: User feedback, peer reviews

  52. Agent Identity Gateway - Authentication/Keys
      ↳ Authentication: Multi-factor (mTLS + API key)
      ↳ Keys: Certificate management, rotation
      ↳ Federation: Cross-organization trust

  53. Agent Governance Gateway - Policies/Permissions
      ↳ Policies: RBAC + ABAC (attribute-based)
      ↳ Permissions: Fine-grained API access
      ↳ Role Management: Admin, Developer, User roles

TIER 11: SPECIALIZED ENTERPRISE (7) - Advanced AI
  54. Prompt Gateway - Prompt Management (8ms)
      ↳ Versioning: A/B testing (50/50, 90/10 splits)
      ↳ LangSmith: Prompt optimization, metrics
      ↳ Templates: Reusable prompt templates (100+)

  55. Evaluation Gateway - Model Evaluation (10ms)
      ↳ Metrics: HumanEval, MMLU, TruthfulQA
      ↳ Benchmarks: Custom healthcare benchmarks
      ↳ Continuous: Daily evaluation runs

  56. Testing Gateway - Test Orchestration
      ↳ Unit: Component-level tests (5,000+ tests)
      ↳ Integration: End-to-end workflows (500+ scenarios)
      ↳ Pipeline: CI/CD integration (GitHub Actions)

  57. Simulation Gateway - Scenario Testing (12ms)
      ↳ What-if Analysis: Counterfactual scenarios
      ↳ Monte Carlo: Statistical simulation (10K runs)
      ↳ Load Testing: Stress testing (50K concurrent)

  58. Digital Worker Gateway - RPA Integration (15ms)
      ↳ RPA: UiPath, Blue Prism, Automation Anywhere
      ↳ Automation: Workflow automation (1,000+ bots)
      ↳ Orchestration: Human + bot collaboration

  59. Autonomous System Gateway - Self-healing (10ms)
      ↳ Self-healing: Automatic error recovery
      ↳ Auto-scaling: Dynamic scaling (2-50 instances)
      ↳ Optimization: Continuous performance tuning

  60. Cognitive Services Gateway - Vision/Language/Speech (50ms)
      ↳ Vision: Azure Computer Vision, OCR
      ↳ Language: Text Analytics, Translation (90+ languages)
      ↳ Speech: Speech-to-Text, Text-to-Speech (24/7 IVR)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL DATA FLOW PATHS (Request Journey Through 60 Gateways)

## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


Typical PA Request Flow (15-minute journey):
  1. Entry: Web Portal (100K users) → Kong Hub → API Gateway (5ms)
  2. Security: Security Gateway (OAuth2, 5ms) → AI Firewall (prompt check, 10ms)
  3. Rate Limit: Token Mgmt Gateway (quota check, 8ms)
  4. AI Routing: AI Gateway → LiteLLM Router (model select, 10ms) → Agent Gateway
  5. Orchestration: Workflow Gateway → Temporal (persist, 10ms)
  6. Agent Pipeline:
     • Intake Agent (2 min): Document Gateway (OCR 50ms) + GPT-4o Vision
     • Eligibility Agent (15 sec): Data Access Gateway + Member Service
     • Benefits Agent (20 sec): Policy Gateway (rules) + Network Service
     • Clinical Agent (8 min - BOTTLENECK): RAG Gateway (45ms) + Vector/Hybrid/Graph
     • Policy Agent (2.5 min): Policy Gateway + Compliance Gateway
     • Fraud Agent (45 sec): Risk Mgmt Gateway + GPU Gateway
     • Decision Agent (30 sec): HITL Gateway (28% human routing)
  7. HITL Split:
     • 28% → HITL Gateway → Review Queue → Approval Gateway (45 min avg)
     • 72% → Auto-approve → Notification Agent
  8. Notification: SaaS Connector Gateway (Slack/Email) + Kafka events
  9. Audit: Audit Gateway (immutable log) + Compliance Gateway (HIPAA)
  10. Observability: Observability Gateway (traces) + Monitoring (metrics) + Cost Mgmt ($1.04)

Critical Bottleneck Analysis:
  • Clinical Agent RAG (53% of total time):
    - RAG Gateway: 45ms orchestration
    - Vector Search: 45ms (Milvus HNSW)
    - Hybrid Search: 85ms (Elasticsearch BM25)
    - Graph RAG: 120ms (Neo4j Cypher)
    - RRF Fusion: 15ms (k=60 ranking)
    - Total RAG: ~265ms per query × 20 queries = 5.3 sec
    - LLM Processing: 8 min (GPT-4o inference)


## ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


### PresentationLayer


### ENTRY POINTS - LAYER 1

  • Daily Volume: 50,000 PA requests
  • Channels: 5 (Web, Mobile, EDI, Fax, IVR)
  • Peak Load: 2,500 req/hour
  • Availability: 99.95% SLA
  • Auth: OAuth2/JWT (Keycloak)


---

## 13. Load Performance Metrics & Detailed Report

### 13.1 Target SLA Metrics

| Component | Metric | Target | Current | Status |
|---|---|---|---|---|
| **Kong Gateway** | p50 latency | < 50ms | 42ms | ✓ PASS |
| **Kong Gateway** | p95 latency | < 200ms | 185ms | ✓ PASS |
| **Kong Gateway** | p99 latency | < 500ms | 450ms | ✓ PASS |
| **OPA Engine** | Decision time (p95) | < 50ms | 48ms | ✓ PASS |
| **OPA Engine** | Decisions/sec | ≥ 200 | 225 | ✓ PASS |
| **Ollama GPU** | Inference latency (p95) | < 1200ms | 980ms | ✓ PASS |
| **Ollama GPU** | Tokens/sec | ≥ 80 | 95 | ✓ PASS |
| **Ollama GPU** | GPU Utilization | 60-80% | 72% | ✓ PASS |
| **Kafka** | Message latency | < 100ms | 85ms | ✓ PASS |
| **PostgreSQL** | Query latency (p95) | < 50ms | 42ms | ✓ PASS |
| **Redis** | Cache hit ratio | ≥ 75% | 78% | ✓ PASS |
| **End-to-End** | PA completion (avg) | < 15 min | 14.2 min | ✓ PASS |

### 13.2 Load Test Phases Summary

**Baseline Phase (5 min, 10 RPS):**
- Kong p95: 185ms
- OPA decision: 42ms
- Error rate: 0.0%
- GPU util: 15%
- Result: BASELINE ESTABLISHED

**Ramp-up Phase (10 min, 10→100 RPS):**
- Kong p95: 195ms (linear growth)
- OPA decision: 48ms
- Error rate: 0.05%
- GPU util: 45%
- Result: LINEAR SCALING CONFIRMED

**Sustained Load (15 min, 100 RPS):**
- Kong p95: 185ms (stable)
- OPA decision: 48ms (stable)
- Error rate: 0.08%
- GPU util: 72% (target range)
- Memory growth: 2.3%
- Result: STABILITY CONFIRMED

**Spike Test (5 min, 100→300 RPS):**
- Peak Kong p95: 420ms
- Recovery time: 45 seconds
- Peak GPU util: 92%
- Error rate: 0.3% (temporary)
- Result: PASSES - Recovers within SLA

**Endurance Test (30 min, 80 RPS):**
- Kong p95: 188ms (variance ±5%)
- OPA decision: 47ms (stable)
- Memory growth: 1.8% (no leak detected)
- Error rate: 0.07%
- Result: NO DEGRADATION - Production ready

---

## 14. OPA Decision Optimization

### 14.1 Current Bottleneck Analysis

**Issue:** OPA policy evaluation latency at **p95: 48ms** (Target: <50ms - ACCEPTABLE but room for optimization)

**Root Causes:**
1. Complex nested Rego policy with 15+ conditions per decision
2. No caching of authorization decisions
3. Policy bundle reload on config change (blocking reload)
4. N+1 external service calls (MemberService, PolicyService lookups inside OPA)

### 14.2 OPA Architecture (Current State)

```
Request Flow:
1. Kong → OPA (10ms network)
2. OPA Policy Evaluation (35ms)
   ├─ Parse input (2ms)
   ├─ Load policy rules (3ms)
   ├─ Evaluate RBAC rules (5ms)
   ├─ Evaluate ABAC rules (8ms)
   ├─ Check compliance flags (5ms)
   ├─ Evaluate cost policy (8ms)
   └─ Build decision output (4ms)
3. OPA → Kong (3ms network)
```

### 14.3 Optimization Strategy #1: Decision Caching

**Implementation:**
```rego
# Add to OPA policy - cache_key generation
package healthcare.cache

cache_key := sprintf(
  "%s:%s:%s:%s",
  [input.claims.sub, input.model, input.claims.environment, input.claims.country]
)

# Cache store (Redis backend)
http.send({
  "method": "GET",
  "url": sprintf("http://redis:6379/opa-cache:%s", [cache_key]),
  "timeout": "5ms"
})
```

**Benefits:**
- Reduces OPA evaluation from 35ms to 8ms on cache hit (77% reduction)
- Target cache hit rate: 85% → effective latency: 12ms average
- 5-minute TTL per decision

**Configuration:**
```yaml
opa_config:
  caching:
    enabled: true
    backend: redis
    ttl_seconds: 300
    max_cache_size: 100000
    invalidation_events:
      - member.updated
      - policy.changed
      - compliance_flag.toggled
```

### 14.4 Optimization Strategy #2: Policy Refactoring

**Current Complex Policy (48ms):**
```rego
# Monolithic 200-line policy evaluates ALL checks sequentially
allow {
  is_member_active
  has_correct_role
  is_within_country_allowlist
  is_within_environment_allowlist
  has_sufficient_budget
  passes_compliance_check
  passes_data_classification_check
  passes_fraud_score
  not in_denied_group
}
```

**Optimized Staged Policy (28ms):**
```rego
# Stage 1 (5ms) - Fast denial checks (95% hits)
fast_deny[reason] {
  in_denied_group
  reason := "group_denied"
}

fast_deny[reason] {
  input.claims.country not in allowed_countries
  reason := "country_denied"
}

# Stage 2 (8ms) - RBAC/ABAC checks only if fast_deny empty
allow {
  count(fast_deny) == 0
  has_correct_role
  is_within_environment_allowlist
}

# Stage 3 (15ms) - Expensive checks only if Stage 2 passes
allow {
  count(fast_deny) == 0
  has_correct_role
  passes_fraud_score  # Most expensive
  has_sufficient_budget
}
```

**Benefits:**
- Early exit on common denials (groups, countries) = 5ms decision
- 70% of decisions complete in Stage 1-2 (13ms total)
- Only 30% reach expensive Stage 3 (28ms)
- Average: 16ms (66% improvement)

### 14.5 Optimization Strategy #3: External Data Prefetch

**Current Issue:**
```
OPA calls MemberService inside policy evaluation:
→ 8ms network round-trip per request
```

**Solution - Prefetch & Cache:**
```yaml
# Kong → OPA Plugin configuration
opa:
  plugin:
    prefetch_data: true
    cache_ttl: 60
    prefetch_endpoints:
      - member_service: /api/member/{member_id}
      - policy_service: /api/policy/{policy_id}
      - risk_service: /api/risk/score/{member_id}
```

**Implementation:**
```
Request arrives at Kong:
1. Kong prefetches {member, policy, risk} data async
2. Kong enriches request with data in X-OPA-Context header
3. OPA receives enriched context (no N+1 calls)
4. OPA decision latency: 28ms → 18ms (36% improvement)
```

### 14.6 Optimization Checklist

- [ ] Enable OPA decision caching (Redis backend)
- [ ] Set cache TTL to 5 minutes
- [ ] Refactor policy into 3-stage pipeline
- [ ] Configure Kong prefetch for member/policy/risk data
- [ ] Add cache invalidation events for member/policy updates
- [ ] Monitor cache hit rate (target ≥85%)
- [ ] Set up OPA metrics in Prometheus
- [ ] Run A/B test: original vs. optimized (measure latency improvement)
- [ ] Validate no behavioral change (same allow/deny decisions)

### 14.7 Expected Post-Optimization Metrics

| Metric | Before | After | Improvement |
|---|---|---|---|
| p50 latency | 30ms | 12ms | 60% |
| p95 latency | 48ms | 18ms | 62% |
| p99 latency | 85ms | 35ms | 59% |
| Decisions/sec | 225 | 450+ | 100% |
| Cache hit ratio | 0% | 85% | N/A |

---

## 15. Ollama GPU Tuning

### 15.1 Current Bottleneck Analysis

**Issue:** Ollama inference latency at **p95: 980ms** (Target: <1200ms - ACCEPTABLE but can optimize)

**Current Hardware:**
- 2x NVIDIA L40S (48GB VRAM each)
- 96 total system cores
- 10Gb Ethernet

**Current Configuration Issues:**
1. Models loaded to CPU fallback during GPU shortage
2. No request batching for concurrent queries
3. Context window set too high (8K default)
4. No quantization for smaller models (qwen3, gemma)

### 15.2 Ollama Performance Tunin Parameters

**Current Configuration (Baseline):**
```yaml
ollama:
  models:
    llama3.3:
      context_length: 8192
      num_gpu: -1  # Auto
      num_thread: 96
      batch_size: 32
      quantization: none
    
    qwen3:
      context_length: 8192
      num_gpu: -1
      num_thread: 96
      batch_size: 32
      quantization: none
```

**Optimized Configuration (Proposed):**
```yaml
ollama:
  models:
    # Tier 1: Large models (highest priority)
    llama3.3:
      context_length: 4096        # Reduce from 8K (50% memory savings)
      num_gpu: 1                  # Force single GPU (L40S-0)
      num_thread: 32              # Reduce threads (GPU-bound)
      batch_size: 64              # Increase batch size (2x throughput)
      quantization: q5_k_m        # Quantize (30% memory reduction)
      cache_mode: layers_only     # Cache only attention layers
      priority: 1
    
    # Tier 2: Medium models
    qwen3:
      context_length: 2048        # Smaller context
      num_gpu: 1                  # Force single GPU (L40S-1)
      num_thread: 32
      batch_size: 128             # Higher batch (better for inference)
      quantization: q4_k_m        # More aggressive quantization
      cache_mode: layers_only
      priority: 2
    
    # Tier 3: Lightweight models
    gemma:
      context_length: 1024        # Minimal context
      num_gpu: 0.5                # Share GPU with lighter workloads
      num_thread: 16
      batch_size: 256
      quantization: q4_0          # Maximum quantization
      cache_mode: none            # Disable caching
      priority: 3
```

**Memory Impact:**
```
Before Optimization:
- llama3.3 (f32):    45GB GPU memory
- qwen3 (f32):       42GB GPU memory
- Total demand:      87GB (exceeds 96GB GPU capacity)
- Result:           CPU fallback, 3-4x slower

After Optimization:
- llama3.3 (q5_k_m): 15GB GPU memory
- qwen3 (q4_k_m):    12GB GPU memory
- gemma (q4_0):      3GB GPU memory
- Total demand:      30GB (fits comfortably in 48GB per GPU)
- Result:           Full GPU utilization, 2-3ms latency per token
```

### 15.3 Quantization Strategy

**Quantization Levels vs. Quality:**

| Level | Size Reduction | Quality Loss | Inference Speed | Use Case |
|---|---|---|---|---|
| **none (f32)** | 0% | 0% | Baseline | Compliance, audit, critical |
| **q8_0** | 75% | <1% | 1.1x faster | High accuracy needed |
| **q5_k_m** | 80% | ~2% | 1.3x faster | llama3.3 (clinical judgments) |
| **q4_k_m** | 85% | ~5% | 1.5x faster | qwen3 (eligibility checks) |
| **q4_0** | 87% | ~8% | 1.6x faster | gemma (routing, low-stakes) |
| **q3_k_m** | 90% | ~15% | 1.8x faster | Not recommended |

**Recommendation:**
- Tier 1 (llama3.3): q5_k_m (keep clinical accuracy, 80% reduction)
- Tier 2 (qwen3): q4_k_m (balance speed and accuracy, 85% reduction)
- Tier 3 (gemma): q4_0 (optimize for speed, low stakes, 87% reduction)

### 15.4 Batching & Request Queuing

**Current Issue:**
```
Each request processes individually:
Request 1: 980ms
Request 2: 980ms (arrives 500ms after Req1)
Request 3: 980ms (arrives 300ms after Req2)
Total 3 requests: 2940ms
```

**Optimized with Batching:**
```
Request Queue (100ms batch window):
Req1 (t=0ms)   ┐
Req2 (t=500ms) ├→ Batch 1: 1100ms (3 requests)
Req3 (t=800ms) ┘

Req4 (t=950ms) ┐
Req5 (t=1020ms)├→ Batch 2: 900ms (2 requests)
               ┘

Result:
- Req 1-3 complete at 1100ms (avg 366ms per request vs 980ms)
- Req 4-5 complete at 1900ms (avg 950ms per request)
- Overall throughput: 5 requests / 1900ms = 2.6 req/sec (vs 1 req/sec)
```

**Implementation:**
```yaml
ollama:
  batching:
    enabled: true
    max_batch_size: 8
    batch_timeout_ms: 100
    adaptive_batching: true
```

### 15.5 GPU Memory Management

**Layer Caching Strategy:**
```
Model: llama3.3 (80 layers)

Standard (All layers cached):
- First request: 4500ms (cold)
- Second request: 800ms (warm)
- GPU memory: 45GB

Optimized (Attention layers only):
- First request: 3200ms (cold)
- Second request: 600ms (warm)
- GPU memory: 18GB (60% reduction)
```

**Configuration:**
```yaml
ollama:
  gpu_memory:
    cache_layers: attention_only
    max_cached_models: 3
    eviction_policy: lru
    preload_models:
      - llama3.3      # Always in GPU
      - qwen3         # Always in GPU
      - gemma         # Load on demand
```

### 15.6 Production Deployment Steps

1. **Phase 1: Quantization (Week 1)**
   - Quantize models to q5_k_m, q4_k_m, q4_0
   - Run accuracy tests (compare outputs against f32 baseline)
   - Validate <5% accuracy loss (human review of samples)

2. **Phase 2: Batching (Week 2)**
   - Enable request batching with 100ms window
   - Load test with 100 concurrent users
   - Measure throughput improvement (target: 2-3x)

3. **Phase 3: Memory Tuning (Week 3)**
   - Reduce context windows (8K → 4K → 2K)
   - Enable attention-layer caching only
   - Monitor OOMKill events (target: zero)

4. **Phase 4: Validation (Week 4)**
   - Full regression testing
   - 48-hour endurance test
   - Monitoring and alerting

### 15.7 Expected Post-Optimization Metrics

| Metric | Before | After | Improvement |
|---|---|---|---|
| p50 latency | 650ms | 380ms | 42% |
| p95 latency | 980ms | 620ms | 37% |
| p99 latency | 1400ms | 950ms | 32% |
| Throughput | 1.5 req/sec | 3.8 req/sec | 153% |
| GPU util | 72% | 85% | +18% |
| GPU memory | 87GB (OOM) | 30GB | 66% savings |

---

## 16. Kong Worker Tuning

### 16.1 Current Bottleneck Analysis

**Issue:** Kong gateway latency stable at **p95: 185ms** (Target: <200ms - ACCEPTABLE but can reduce to <100ms)

**Current Hardware:**
- 2 Kong instances (8 core / 16GB RAM each)
- 16 worker processes per instance
- No request buffering
- OpenResty 1.21

**Current Configuration Issues:**
1. Worker processes: 16 (too high for 8 cores - context switching overhead)
2. Buffer pool: 4m (default - causes memory allocation latency)
3. No request pipelining (HTTP/1.1 sequential)
4. Lua code executed in master process (blocking)

### 16.2 Kong Configuration Optimization

**Current Configuration:**
```nginx
# /etc/kong/kong.conf (BASELINE)

# Worker processes
worker_processes = 16  # ← TOO HIGH (8 cores)
worker_connections = 1024
worker_rlimit_nofile = 65535

# Buffer sizes
client_body_buffer_size = 128k
client_header_buffer_size = 1k
large_client_header_buffers = 4 32k
proxy_buffer_size = 4k
proxy_buffers = 8 4k

# Timeouts
upstream_connect_timeout = 60000
upstream_send_timeout = 60000
upstream_read_timeout = 60000
```

**Optimized Configuration:**
```nginx
# /etc/kong/kong.conf (OPTIMIZED)

# Worker processes tuning
worker_processes = 8         # Match CPU cores (8 cores)
worker_connections = 2048    # Increase per-worker capacity (2x)
worker_rlimit_nofile = 65535

# Buffer pool optimization
buffer_pool_size = 8m        # Pre-allocate buffers (reduce allocation latency)
client_body_buffer_size = 256k  # Increase for PA document uploads
client_header_buffer_size = 4k
large_client_header_buffers = 8 64k
proxy_buffer_size = 16k
proxy_buffers = 16 16k       # Increase buffers for streaming

# Connection timeouts (reduce for fast path)
upstream_connect_timeout = 5000    # Reduce from 60s
upstream_send_timeout = 30000      # Reduce from 60s
upstream_read_timeout = 30000      # Reduce from 60s

# HTTP/2 for multiplexing
http2_max_header_table_size = 4096
http2_max_requests = 1000000

# Caching
proxy_cache_key = "$scheme$request_method$host$request_uri"
proxy_cache_valid = 200 5m
proxy_cache_use_stale = error timeout updating http_500 http_502 http_503 http_504

# Connection keepalive
keepalive_timeout = 65
keepalive_requests = 100
tcp_nopush = on
tcp_nodelay = on
```

### 16.3 Kong Plugins Optimization

**Plugin Load Order Impact on Latency:**

```
Request Processing Pipeline Latency Breakdown:

CURRENT (Sequential, 185ms):
1. http-log          (2ms)     - Logging plugin
2. cors               (3ms)     - CORS headers
3. key-auth           (5ms)     - API key validation
4. jwt                (8ms)     - JWT validation
5. acl                (10ms)    - Group ACL check
6. rate-limiting      (15ms)    - Token bucket
7. opa (custom)       (48ms)    - OPA policy decision ← BOTTLENECK
8. ai-proxy           (12ms)    - Model routing
9. proxy routing      (82ms)    - Upstream + network
────────────────────────────────
Total: 185ms
```

**Optimized (Parallel + Cache, 95ms):**
```
PHASE 1 (Parallel - 5ms):
├─ http-log (async)    (0ms)     - Non-blocking
├─ cors                (1ms)
└─ key-auth            (4ms)     ← Fallback to cache if slow

PHASE 2 (Cache/Fast-Path - 8ms):
├─ jwt (cached)        (2ms)     ← JWT cache hit
├─ acl (cached)        (3ms)     ← ACL cache hit
└─ rate-limiting       (3ms)     ← Token bucket in Redis

PHASE 3 (OPA + Routing - 40ms):
├─ opa (cached)        (8ms)     ← OPA cache hit (85%)
├─ ai-proxy            (12ms)
└─ proxy routing       (20ms)    ← Reduced upstream timeout

PHASE 4 (Parallel Response - 42ms):
└─ upstream response   (42ms)

────────────────────────────────
Total: 95ms (49% improvement)
```

### 16.4 Kong Plugin Configuration

**Recommended Plugin Order & Caching:**

```yaml
kong:
  plugins:
    # Phase 1: Async/Non-blocking
    - name: http-log
      config:
        http_endpoint: http://log-collector:5000
        batch_size: 100
        async: true

    # Phase 2: Fast-path with caching
    - name: key-auth
      config:
        cache_ttl: 3600
        hide_credentials: true
    
    - name: jwt
      config:
        cache_ttl: 900
        secret: "from-vault"
        algorithm: RS256
    
    - name: acl
      config:
        cache_ttl: 300
        whitelist: true
    
    - name: rate-limiting
      config:
        policy: redis
        redis_host: redis:6379
        minute: 200
        redis_timeout: 2000
    
    # Phase 3: Decision/Policy
    - name: opa
      config:
        host: http://opa:8181
        policy_path: /v1/data/healthcare/authz
        cache_ttl: 300
    
    - name: ai-proxy
      config:
        model_selection_timeout: 5000
```

### 16.5 Lua Code Optimization

**Avoid Blocking Lua in Master Process:**

**SLOW (8ms latency added):**
```lua
-- /etc/kong/plugins/custom-policy/handler.lua
function CustomPolicyHandler:access(conf)
  -- ❌ SLOW: Blocking lookup in master process
  local member = ngx.shared.DICT:get("member:" .. user_id)
  if not member then
    local res = ngx.location.capture("/internal/member/" .. user_id)
    member = cjson.decode(res.body)
    ngx.shared.DICT:set("member:" .. user_id, cjson.encode(member), 300)
  end
end
```

**FAST (2ms latency):**
```lua
-- /etc/kong/plugins/custom-policy/handler.lua
function CustomPolicyHandler:access(conf)
  -- ✓ FAST: Use Redis (async client)
  local redis = require "resty.redis"
  local red = redis:new()
  red:set_timeouts(100, 100, 100)
  
  local ok, err = red:connect("redis", 6379)
  local member, err = red:get("member:" .. user_id)
  
  if not member then
    -- Async queue lookup (non-blocking)
    ngx.var.trigger_async_fetch = 1
  end
end
```

### 16.6 Kong Metrics & Monitoring

**Add Prometheus Metrics:**

```yaml
kong:
  prometheus:
    enabled: true
    collect_endpoint: /metrics
    
  prometheus_metrics:
    - name: kong_request_latency
      help: "Request latency in milliseconds"
      buckets: [1, 5, 10, 50, 100, 500, 1000]
    
    - name: kong_upstream_latency
      help: "Upstream service latency"
      buckets: [1, 10, 50, 100, 500, 1000, 5000]
    
    - name: kong_plugin_latency
      help: "Per-plugin latency"
      labels: [plugin]
      
    - name: kong_worker_connections
      help: "Active worker connections"
      labels: [worker_id]
```

### 16.7 Deployment & Validation Steps

1. **Step 1: Configuration Update**
   ```bash
   # Update kong.conf with optimized settings
   sed -i 's/worker_processes = 16/worker_processes = 8/' /etc/kong/kong.conf
   sed -i 's/buffer_pool_size = 4m/buffer_pool_size = 8m/' /etc/kong/kong.conf
   
   # Validate syntax
   kong check /etc/kong/kong.conf
   
   # Apply without downtime (graceful reload)
   kong reload
   ```

2. **Step 2: Monitor Gradual Rollout**
   ```bash
   # Monitor in real-time
   watch 'curl -s http://localhost:8001/metrics | grep kong_request'
   ```

3. **Step 3: Load Test**
   ```bash
   # Run locust with optimized config
   locust -f locustfile.py -u 100 -r 10 --run-time=10m
   ```

4. **Step 4: Metric Validation**
   - p95 latency: < 100ms (vs 185ms baseline)
   - Throughput: > 300 req/sec (vs 150 req/sec baseline)
   - Error rate: < 0.1%

### 16.8 Expected Post-Optimization Metrics

| Metric | Before | After | Improvement |
|---|---|---|---|
| p50 latency | 42ms | 25ms | 40% |
| p95 latency | 185ms | 95ms | 49% |
| p99 latency | 450ms | 200ms | 56% |
| Throughput | 150 req/sec | 320 req/sec | 113% |
| CPU per core | 45% | 35% | 22% savings |
| Memory per worker | 250MB | 180MB | 28% savings |

---

*Generated by `scripts/generate_deep_reference.py` from PlantUML diagram 13.*
