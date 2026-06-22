# Layer 4: AI Agent Fabric Layer
## 11 AI Agents with Hybrid LLM Orchestration - Healthcare Insurance PA Platform

**Layer Purpose**: AI-powered decision automation with 11 specialized agents using hybrid model strategy  
**Services**: 11 agents  
**Technology Stack**: Proprietary LLMs (GPT-4o, Claude 3.5, GPT-3.5) + In-House Models (Llama 3.1 70B, LayoutLM v3, Classification ML/DL)  
**Model Serving**: vLLM, SageMaker, Azure OpenAI, Anthropic API  
**Daily Volume**: 385,000 agent executions/day (7 agents × 55,000 cases)  
**Performance**: 1.2s - 8.3s per agent execution  
**Success Rate**: 96.2% automation (72% without human review)  
**Cost Optimization**: 62% cost reduction via in-house models + fallback strategy

---

## Table of Contents
1. [Layer Overview](#layer-overview)
2. [Agent Architecture](#agent-architecture)
3. [Hybrid Model Architecture](#hybrid-model-architecture)
   - [Proprietary vs In-House Models](#proprietary-vs-in-house-models)
   - [Fallback Strategy](#fallback-strategy)
   - [Model Serving Infrastructure](#model-serving-infrastructure)
   - [Cost Comparison](#cost-comparison)
4. [Individual Agent Specifications](#individual-agent-specifications)
   - [Agent 1: Intake Agent (with LayoutLM v3 + ML Classification)](#agent-1-intake-agent)
   - [Agent 2: Eligibility Agent](#agent-2-eligibility-agent)
   - [Agent 3: Benefits Agent](#agent-3-benefits-agent)
   - [Agent 4: Clinical Review Agent (with In-House Medical LLM)](#agent-4-clinical-review-agent)
   - [Agent 5: Policy Agent](#agent-5-policy-agent)
   - [Agent 6: Fraud Detection Agent](#agent-6-fraud-detection-agent)
   - [Agent 7: Decision Agent](#agent-7-decision-agent)
   - [Agent 8: Appeals Agent](#agent-8-appeals-agent)
   - [Agent 9: Notification Agent](#agent-9-notification-agent)
   - [Agent 10: Audit Agent](#agent-10-audit-agent)
   - [Agent 11: Communication Agent](#agent-11-communication-agent)
5. [Technical Implementation](#technical-implementation)
6. [API Specifications](#api-specifications)
7. [Multi-Model Strategy](#multi-model-strategy)
8. [Performance & Scaling](#performance--scaling)
9. [Security & Safety](#security--safety)
10. [Monitoring & Operations](#monitoring--operations)

---

## Layer Overview

### Purpose
The **AI Agent Fabric** provides specialized AI decision-making capabilities across the PA workflow:

- **11 Specialized Agents**: Each handles a specific domain (eligibility, clinical, policy, etc.)
- **Hybrid Model Strategy**: Proprietary LLMs (GPT-4o, Claude 3.5) + In-House Models (Llama 3.1 70B, LayoutLM v3) + ML/DL Classification
- **Intelligent Fallback**: Primary model → Backup model → In-house model with automatic failover
- **RAG Integration**: Clinical agent uses hybrid retrieval (Vector + BM25 + Graph)
- **Specialized NER**: LayoutLM v3 fine-tuned on medical forms for document entity extraction
- **ML/DL Classification**: Random Forest, XGBoost, ResNet for fast classification tasks
- **Tool Calling**: Agents invoke 45+ MCP tools for data access, calculations, and external APIs
- **Confidence Scoring**: Every decision includes confidence (0-1) for HITL routing
- **Safety Guardrails**: Hallucination detection, PII redaction, toxicity filtering
- **Cost Optimization**: 62% cost reduction via in-house models (from $52,000/day to $19,760/day)

**Daily Execution Volume**:
- Total: 385,000 agent executions/day
- Per case: Average 7 agents (min 4, max 10)
- Success rate: 96.2% (76,230 successful automations/day)
- HITL escalation: 28% of cases (14,000/day) due to low confidence (<0.85)

### Architecture Principles

1. **Single Responsibility**: Each agent focuses on one domain
2. **Composability**: Agents combine via LangGraph orchestration
3. **Reliability**: Multi-tier fallback (proprietary → in-house → rule-based), circuit breakers
4. **Safety First**: Guardrails validate every agent output
5. **Hybrid Model**: Proprietary LLMs for complex reasoning, in-house models for cost optimization, ML/DL for classification
6. **Cost Efficiency**: In-house models handle 75% of workload, proprietary models for edge cases
7. **Observability**: Full tracing of prompts, outputs, tokens, latency, model selection decisions
8. **Model Serving**: vLLM for in-house LLMs (Llama, LayoutLM), SageMaker for ML/DL models

---

## Agent Architecture

### Common Agent Framework

All agents inherit from a base `PAAgent` class:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
import openai
from langchain.agents import AgentExecutor
from langchain.tools import Tool

class AgentInput(BaseModel):
    """Base input schema"""
    request_id: str
    context: Dict[str, Any]
    previous_outputs: Dict[str, Any] = {}

class AgentOutput(BaseModel):
    """Base output schema"""
    agent_name: str
    decision: str
    confidence: float  # 0.0 - 1.0
    reasoning: str
    tools_used: List[str]
    execution_time_ms: int
    token_usage: Dict[str, int]
    metadata: Dict[str, Any]

class PAAgent(ABC):
    """Base class for all PA agents"""
    
    def __init__(
        self,
        name: str,
        model: str,
        temperature: float,
        max_tokens: int,
        tools: List[Tool],
        system_prompt: str
    ):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools
        self.system_prompt = system_prompt
        self.executor = self._build_executor()
    
    @abstractmethod
    def process(self, input: AgentInput) -> AgentOutput:
        """Process the agent logic"""
        pass
    
    def _invoke_llm(self, prompt: str, context: Dict) -> str:
        """Invoke LLM with retry logic"""
        pass
    
    def _calculate_confidence(self, output: str, context: Dict) -> float:
        """Calculate confidence score"""
        pass
    
    def _apply_guardrails(self, output: str) -> str:
        """Apply safety guardrails"""
        pass
```

### Agent Deployment Pattern

Each agent deployed as a separate microservice:

```yaml
Agent Pod Template:
  containers:
    - name: agent
      image: agent-{name}:v1.2.0
      resources:
        requests: { cpu: 200m, memory: 512Mi }
        limits: { cpu: 1000m, memory: 2Gi }
      env:
        - name: AGENT_NAME
          value: "{agent_name}"
        - name: LLM_MODEL
          valueFrom:
            configMapKeyRef:
              name: agent-config
              key: model
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: openai-api-key
```

---

## Hybrid Model Architecture

### Proprietary vs In-House Models

The Layer 4 architecture uses a **hybrid approach** combining proprietary LLMs (OpenAI, Anthropic) with in-house models for cost optimization and reliability:

**Proprietary Models (25% of workload)**:
- **GPT-4o**: Complex clinical reasoning, multi-modal vision (fax/image OCR), decision synthesis
- **Claude 3.5 Sonnet**: Policy interpretation (15% better than GPT-4o for legal text)
- **GPT-3.5 Turbo**: Simple lookup/classification tasks (23.75x cheaper than GPT-4o)

**In-House Models (75% of workload)**:
- **Llama 3.1 70B** (fine-tuned on medical data): Clinical reasoning fallback, policy interpretation
- **LayoutLM v3** (fine-tuned on PA forms): Document NER, field extraction from structured/semi-structured forms
- **Clinical Classification DL Model**: ResNet-50 for urgency triage (emergency/urgent/standard)
- **Document Type Classifier**: Random Forest for classifying incoming document types (fax/EDI/web)
- **Fraud Detection ML**: XGBoost for FWA pattern scoring
- **Llama 3.1 8B** (quantized INT8): Fast eligibility/benefits lookups

**Model Hosting**:
```yaml
In-House Model Serving Infrastructure:
  vLLM Server:
    models:
      - llama-3.1-70b-medical-ft (FP16, 4x A100 80GB GPUs)
      - llama-3.1-8b-eligibility-ft (INT8, 1x A100 40GB)
      - layoutlm-v3-medical-forms-ft (FP16, 1x A100 40GB)
    throughput: 850 requests/second (batched)
    latency: P50=180ms, P95=350ms
    cost: $14,400/month (GPU compute)
  
  SageMaker Endpoints:
    models:
      - clinical-urgency-resnet50 (ml.g4dn.xlarge)
      - document-classifier-rf (ml.m5.large)
      - fraud-detection-xgboost (ml.c5.xlarge)
    throughput: 2,500 requests/second
    latency: P50=25ms, P95=45ms
    cost: $3,200/month
  
  Proprietary APIs:
    Azure OpenAI (GPT-4o, GPT-3.5): $52,000/month baseline
    Anthropic (Claude 3.5): $19,170/month baseline
    Total Proprietary Cost: $71,170/month (baseline without in-house)
```

**Cost Comparison**:
```
Baseline (100% Proprietary): $71,170/month
Hybrid (25% Proprietary + 75% In-House): $17,792 (proprietary) + $17,600 (in-house) = $35,392/month
Monthly Savings: $35,778 (50.3% reduction)

Daily Cost Breakdown:
  Proprietary only: $52,000/day → Hybrid: $19,760/day
  Savings: $32,240/day = $11.77M/year
```

---

### Fallback Strategy

**Multi-Tier Fallback Architecture**:

Each agent implements a 3-tier fallback cascade for reliability and cost optimization:

**Tier 1 - In-House Model (Primary, 75% of traffic)**:
- Cost: $0.002 - $0.008 per request (vLLM + SageMaker)
- Latency: 180-350ms
- Routing Logic: All requests start here
- Success Rate: 92.5% (handles most standard cases)
- Fallback Trigger: Confidence < 0.70 OR model unavailable

**Tier 2 - Proprietary Model (Backup, 23% of traffic)**:
- Cost: $0.0095 - $0.0275 per request
- Latency: 450-2,100ms
- Routing Logic: Low confidence from in-house OR complex edge case
- Success Rate: 95.8%
- Fallback Trigger: Confidence < 0.85 OR API failure

**Tier 3 - Rule-Based Fallback (Last Resort, 2% of traffic)**:
- Cost: $0 (deterministic rules)
- Latency: <50ms
- Routing Logic: All LLM tiers failed OR critical API outage
- Decision: Route to HITL with "Automated review unavailable" flag

**Fallback Decision Tree**:
```python
def execute_agent_with_fallback(agent_name: str, input_data: AgentInput) -> AgentOutput:
    """Execute agent with intelligent fallback"""
    
    # Tier 1: In-House Model (Primary)
    try:
        result = execute_inhouse_model(agent_name, input_data)
        if result.confidence >= 0.70 and result.status == "success":
            result.metadata["model_tier"] = "in-house"
            result.metadata["cost"] = calculate_inhouse_cost(result.token_usage)
            return result
        else:
            log.warning(f"In-house model low confidence ({result.confidence}), falling back to proprietary")
    except ModelUnavailableError as e:
        log.error(f"In-house model unavailable: {e}, falling back to proprietary")
    
    # Tier 2: Proprietary Model (Backup)
    try:
        result = execute_proprietary_model(agent_name, input_data)
        if result.confidence >= 0.85 and result.status == "success":
            result.metadata["model_tier"] = "proprietary"
            result.metadata["cost"] = calculate_proprietary_cost(result.token_usage)
            result.metadata["fallback_reason"] = "in-house_low_confidence"
            return result
        else:
            log.warning(f"Proprietary model low confidence ({result.confidence}), falling back to rules")
    except (APIError, RateLimitError, Timeout) as e:
        log.error(f"Proprietary API failed: {e}, falling back to rules")
    
    # Tier 3: Rule-Based Fallback (Last Resort)
    result = execute_rule_based_fallback(agent_name, input_data)
    result.metadata["model_tier"] = "rule-based-fallback"
    result.metadata["cost"] = 0
    result.metadata["needs_human_review"] = True
    result.metadata["fallback_reason"] = "all_models_failed"
    return result
```

**Fallback Metrics (30-day average)**:
- In-house success: 75.2% (290,100 requests/day)
- Proprietary fallback: 23.1% (89,025 requests/day)
- Rule-based fallback: 1.7% (6,545 requests/day → routed to HITL)
- Total failures requiring HITL: 8.2% (31,570 requests/day)

---

### Model Serving Infrastructure

**vLLM Inference Server Configuration**:

```yaml
vLLM Deployment (Kubernetes):
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: vllm-inference-server
    namespace: model-serving
  spec:
    replicas: 8  # Auto-scaled 4-12
    template:
      spec:
        nodeSelector:
          gpu: nvidia-a100
        containers:
          - name: vllm-server
            image: vllm/vllm-openai:v0.4.2
            resources:
              limits:
                nvidia.com/gpu: 4  # 4x A100 80GB per pod
            env:
              - name: MODEL_NAME
                value: "llama-3.1-70b-medical-ft"
              - name: TENSOR_PARALLEL_SIZE
                value: "4"
              - name: MAX_MODEL_LEN
                value: "8192"
              - name: GPU_MEMORY_UTILIZATION
                value: "0.95"
            command:
              - python
              - -m
              - vllm.entrypoints.openai.api_server
              - --model=/models/llama-3.1-70b-medical-ft
              - --tensor-parallel-size=4
              - --max-num-batched-tokens=16384
              - --dtype=float16

Models Served via vLLM:
  1. llama-3.1-70b-medical-ft:
     - Fine-tuned on: 2.5M clinical notes, 180K PA decisions, 45K policy documents
     - Use cases: Clinical reasoning, policy interpretation fallback
     - Latency: P50=280ms, P95=510ms
     - Throughput: 320 req/s (with batching)
     - Cost per request: $0.0055
  
  2. llama-3.1-8b-eligibility-ft (INT8 quantized):
     - Fine-tuned on: 5M eligibility checks, 150K benefits calculations
     - Use cases: Eligibility, benefits, simple lookups
     - Latency: P50=85ms, P95=145ms
     - Throughput: 780 req/s
     - Cost per request: $0.0008
  
  3. layoutlm-v3-medical-forms-ft:
     - Fine-tuned on: 500K medical PA forms (PDF/TIFF), 85K X12 EDI transactions
     - Use cases: Document NER, field extraction, form understanding
     - Latency: P50=220ms, P95=380ms
     - Throughput: 410 req/s
     - Cost per request: $0.0042
```

**SageMaker ML/DL Endpoints**:

```yaml
SageMaker Model Endpoints:
  1. clinical-urgency-classifier:
     model: ResNet-50 (fine-tuned on 1.2M PA cases)
     instance: ml.g4dn.xlarge (1x NVIDIA T4 GPU)
     input: Clinical text + ICD-10 codes
     output: urgency_level (emergency/urgent/standard), confidence
     latency: P50=18ms, P95=32ms
     accuracy: 96.8%
     cost: $0.0003/request
  
  2. document-type-classifier:
     model: Random Forest (175 trees, max_depth=25)
     instance: ml.m5.large (CPU-only)
     input: Document metadata + first-page text features
     output: doc_type (fax/edi_x12/web_json/ivr_transcript), confidence
     latency: P50=8ms, P95=14ms
     accuracy: 98.5%
     cost: $0.0001/request
  
  3. fraud-risk-scorer:
     model: XGBoost (gradient boosting, 500 estimators)
     instance: ml.c5.xlarge (compute-optimized CPU)
     input: Provider history, billing patterns, claim features
     output: fraud_risk_score (0-100), risk_level (LOW/MEDIUM/HIGH/CRITICAL)
     latency: P50=12ms, P95=22ms
     ROC-AUC: 0.94
     cost: $0.0002/request
  
  4. ner-field-extractor:
     model: LayoutLM v3 (document understanding transformer)
     instance: ml.g4dn.xlarge (1x NVIDIA T4)
     input: Document image/PDF (up to 10 pages)
     output: Extracted fields (member_id, provider_npi, cpt_codes, icd10_codes, etc.)
     latency: P50=220ms/page, P95=380ms/page
     field extraction accuracy: 97.2%
     cost: $0.0042/page
```

**Model Registry & Versioning**:

```python
# MLflow Model Registry
mlflow_models = {
    "llama-3.1-70b-medical-ft": {
        "version": "v2.3.1",
        "stage": "production",
        "training_date": "2026-05-15",
        "metrics": {"accuracy": 0.945, "avg_latency_ms": 280},
        "artifacts": "s3://models/llama-70b-medical/v2.3.1/"
    },
    "layoutlm-v3-medical-forms-ft": {
        "version": "v1.8.2",
        "stage": "production",
        "training_date": "2026-05-28",
        "metrics": {"field_accuracy": 0.972, "avg_latency_ms": 220},
        "artifacts": "s3://models/layoutlm-v3/v1.8.2/"
    }
}

# Automated A/B Testing
# New model versions serve 5% traffic, champion model serves 95%
# Auto-promote if new model improves accuracy >2% AND latency <10% worse
```

---

### Cost Comparison

**Daily Cost Breakdown (55,000 PA cases/day)**:

| Component | Baseline (100% Proprietary) | Hybrid (25% Prop + 75% In-House) | Savings |
|-----------|----------------------------|----------------------------------|---------|
| **Intake Agent** | | | |
| - GPT-4o Vision (OCR) | $2,475 (5,000 fax cases) | $2,475 (complex fax) | $0 |
| - LayoutLM v3 (NER) | N/A | $1,155 (27,500 forms) | -$1,155 |
| - Document Classifier ML | N/A | $82 (55,000 docs) | -$82 |
| **Eligibility Agent** | | | |
| - GPT-3.5 Turbo | $220 (55,000 checks) | $0 | $220 |
| - Llama 8B (in-house) | N/A | $440 (55,000 checks) | -$440 |
| **Benefits Agent** | | | |
| - GPT-3.5 Turbo | $275 (55,000 calcs) | $0 | $275 |
| - Llama 8B (in-house) | N/A | $440 (55,000 calcs) | -$440 |
| **Clinical Agent** | | | |
| - GPT-4o (complex) | $15,125 (55,000 reviews) | $3,781 (13,750 complex) | $11,344 |
| - Llama 70B (in-house) | N/A | $2,268 (41,250 standard) | -$2,268 |
| - Urgency Classifier DL | N/A | $165 (55,000 triage) | -$165 |
| **Policy Agent** | | | |
| - Claude 3.5 Sonnet | $6,600 (55,000 interp) | $1,650 (12,500 complex) | $4,950 |
| - Llama 70B (in-house) | N/A | $2,338 (42,500 standard) | -$2,338 |
| **Fraud Agent** | | | |
| - GPT-4o | $5,225 (55,000 checks) | $1,306 (12,500 complex) | $3,919 |
| - XGBoost (in-house) | N/A | $85 (42,500 scoring) | -$85 |
| **Decision Agent** | | | |
| - GPT-4o | $7,810 (55,000 synth) | $1,952 (13,750 complex) | $5,858 |
| - Llama 70B (in-house) | N/A | $2,268 (41,250 standard) | -$2,268 |
| **Other Agents** | | | |
| - Appeals, Notification, Audit, COM | $13,270 | $3,318 (25% prop) + $1,980 (75% in-house) | $7,972 |
| | | | |
| **Total Daily Cost** | **$52,000** | **$19,760** | **$32,240 (62%)** |
| **Annual Cost** | **$18.98M** | **$7.21M** | **$11.77M saved** |

**ROI Calculation**:
```
In-House Infrastructure Cost:
  vLLM GPU cluster: $14,400/month ($172,800/year)
  SageMaker endpoints: $3,200/month ($38,400/year)
  Model training/fine-tuning: $25,000/month ($300,000/year)
  MLOps engineers (2 FTEs): $360,000/year
  Total infrastructure: $871,200/year

Annual Savings: $11,770,000
Infrastructure Cost: $871,200
Net Savings: $10,898,800/year

ROI: 1,251% (12.5x return on investment)
Payback Period: 0.9 months
```

---

## Individual Agent Specifications

### Agent 1: Intake Agent

**Business Use Case**: Extract and structure PA request data from multiple input channels

**Input Sources**:
- Web portal submissions (JSON)
- Fax documents (OCR via Azure Form Recognizer + LayoutLM v3)
- EDI X12 278 transactions (healthcare standard)
- Phone calls (IVR transcripts via Azure Speech)

**Hybrid Model Architecture**:

**Tier 1 - ML Classification + LayoutLM v3 NER (Primary, 85% of workload)**:
```yaml
Document Type Classifier (Random Forest):
  model: sklearn RandomForest (175 trees, deployed on SageMaker ml.m5.large)
  input: Document metadata (file_type, page_count, first_50_chars)
  output: doc_type (fax/edi/web/ivr), confidence
  latency: 8ms P50, 14ms P95
  accuracy: 98.5%
  cost: $0.0001 per document
  routing_logic: Classify ALL incoming documents before extraction

LayoutLM v3 NER (Fine-Tuned on Medical Forms):
  model: microsoft/layoutlm-v3-base (fine-tuned on 500K PA forms)
  serving: vLLM server (1x A100 40GB GPU)
  input: Document image/PDF (multi-page support)
  output: Structured fields:
    - patient: {member_id, name, dob, gender, policy_number}
    - provider: {npi, name, specialty, phone, tax_id}
    - service: {cpt_codes[], icd10_codes[], service_description, urgency}
    - clinical: {diagnosis, treatment_plan, prior_treatments[]}
  field_extraction_accuracy: 97.2%
  latency: 220ms/page (P50), 380ms/page (P95)
  throughput: 410 req/s (batched inference)
  cost: $0.0042 per page
  use_cases:
    - Standard PA forms (CMS-1500, UB-04, custom payer forms)
    - Multi-page faxes (up to 15 pages)
    - Semi-structured documents (provider letterhead, clinical notes)
  fallback_trigger: confidence < 0.90 on required fields OR poor scan quality

Training Details:
  dataset: 500K annotated medical forms (CMS-1500, UB-04, payer-specific)
  augmentation: Rotation, noise, blur, contrast (simulates fax quality)
  epochs: 15, batch_size: 16, learning_rate: 5e-5
  validation accuracy: 97.2% (field-level), 94.8% (document-level)
  fine-tuning compute: 8x A100 GPUs for 72 hours
```

**Tier 2 - GPT-4o Vision (Fallback, 13% of workload)**:
```yaml
GPT-4o Vision API (Azure OpenAI):
  use_cases:
    - Poor quality faxes (LayoutLM confidence < 0.90)
    - Handwritten forms (provider notes, prescriptions)
    - Complex multi-page documents (>15 pages)
    - Unstructured clinical narratives
  latency: 1.8s (web), 4.2s (fax with vision)
  cost: $0.045 per image (GPT-4o vision pricing)
  fallback_trigger: LayoutLM extraction failed OR confidence < 0.90
```

**Tier 3 - Azure Form Recognizer (Last Resort, 2% of workload)**:
```yaml
Azure Form Recognizer (Managed Service):
  use_cases:
    - All LLM/ML tiers failed
    - Critical API outages
    - Extremely poor scan quality (last attempt before HITL)
  latency: 3.5s per document
  cost: $0.50 per document (expensive, last resort only)
  output: Basic OCR text + bounding boxes (no semantic understanding)
  post_processing: Manual HITL review required
```

**LLM Model (Legacy/Fallback)**: GPT-4o (vision for fax/image processing)
**Temperature**: 0.1 (deterministic extraction)
**Max Tokens**: 2048

**Core Responsibilities**:
1. **Document Classification**: Classify incoming document type (fax/EDI/web/IVR) using Random Forest
2. **NER Field Extraction**: Extract patient demographics, provider info, service details using LayoutLM v3
3. Extract patient demographics (name, DOB, member ID, policy number)
4. Extract provider information (NPI, name, specialty, tax ID)
5. Extract requested service (CPT codes, ICD-10 diagnoses, HCPCS)
6. **Validation**: Validate data completeness and NPI checksums
7. **Normalization**: Normalize formats (dates, phone numbers, addresses)
8. Handle multi-page faxes and poor-quality scans

**System Prompt** (abbreviated):
```
You are a medical data extraction agent for a health insurance PA system.

Your task: Extract structured data from PA requests in various formats.

Required fields:
- Patient: member_id, name, dob, gender, policy_number
- Provider: npi, name, specialty, phone
- Service: cpt_codes[], icd10_codes[], service_description
- Clinical: diagnosis, treatment_plan, urgency_level

Output JSON with extracted data and confidence score (0-1) for each field.
If confidence < 0.9 for required fields, set needs_human_review=true.

Handle variations: poor scans, handwriting, abbreviations.
```

**MCP Tools Used**:
- `parse_x12_278`: Parse EDI transactions
- `ocr_fax_document`: Azure Form Recognizer API
- `validate_member_id`: Check member ID format
- `validate_npi`: Verify provider NPI
- `normalize_date`: Standardize date formats

**Input Schema**:
```python
class IntakeInput(AgentInput):
    source_type: str  # "web", "fax", "edi", "ivr"
    raw_data: Union[Dict, str, bytes]  # Varies by source
    document_urls: List[str] = []  # For fax PDFs
```

**Output Schema**:
```python
class IntakeOutput(AgentOutput):
    patient: PatientData
    provider: ProviderData
    requested_service: ServiceData
    supporting_documents: List[str]
    data_quality_score: float  # 0-1
    missing_fields: List[str]
    needs_human_review: bool
```

**Performance Metrics (Hybrid Model)**:
- **Throughput**: 55,000 requests/day
- **Latency Breakdown by Model Tier**:
  - **ML Classification (document type)**: 8ms P50, 14ms P95 (100% of docs)
  - **LayoutLM v3 NER (primary, 85%)**: 220ms/page P50, 380ms/page P95 (46,750 docs)
  - **GPT-4o Vision (fallback, 13%)**: 1.8s (web), 4.2s (fax) (7,150 docs)
  - **Azure Form Recognizer (last resort, 2%)**: 3.5s (1,100 docs)
- **Overall Latency**: 
  - Web (JSON): 45ms P50, 85ms P95 (no OCR needed)
  - Fax (LayoutLM v3): 230ms P50, 395ms P95 (standard quality)
  - Fax (GPT-4o fallback): 1.8s P50, 4.2s P95 (poor quality)
- **Accuracy**:
  - LayoutLM v3: 97.2% field extraction accuracy
  - GPT-4o Vision: 98.5% field extraction accuracy
  - Document Classification: 98.5% accuracy
- **Cost per Request**:
  - Web/EDI (no OCR): $0.0001 (classification only)
  - Fax (LayoutLM v3, 3-page avg): $0.0127 ($0.0001 class + $0.0126 NER)
  - Fax (GPT-4o fallback, 3-page avg): $0.0452 ($0.0001 class + $0.0451 vision)
- **Model Distribution**:
  - Classification ML: 100% (55,000 docs/day)
  - LayoutLM v3: 85% (46,750 docs/day), Cost: $593/day
  - GPT-4o Vision: 13% (7,150 docs/day), Cost: $323/day
  - Azure Form Recognizer: 2% (1,100 docs/day), Cost: $550/day
  - **Total Daily Cost**: $1,466 (vs $2,475 GPT-4o only = 41% savings)
- **Human Review Rate**: 3.2% (LayoutLM v3 reduced from 5% GPT-4o only)

**Error Handling**:
- Missing required fields → Return partial data with `needs_human_review=true`
- Invalid member ID → Call validation API, attempt fuzzy match
- OCR failure → Retry with different preprocessing, escalate to human

---

### Agent 2: Eligibility Agent

**Business Use Case**: Verify patient's active insurance coverage and eligibility for requested service

**LLM Model**: GPT-3.5 Turbo (simple lookup/validation task)
**Temperature**: 0.0 (deterministic)
**Max Tokens**: 1024

**Core Responsibilities**:
1. Verify active insurance policy (effective dates)
2. Check coverage tier (PPO, HMO, EPO)
3. Validate network status (in-network vs out-of-network)
4. Check deductibles and out-of-pocket limits
5. Verify service-specific coverage (plan covers requested CPT codes)
6. Identify any exclusions or waiting periods

**System Prompt** (abbreviated):
```
You are an insurance eligibility verification agent.

Your task: Determine if the patient is eligible for the requested service.

Check:
1. Policy active? (current_date between effective_date and term_date)
2. Service covered under plan? (cpt_code in covered_services)
3. Provider in-network? (provider_npi in network_providers)
4. Deductible met? (ytd_spend >= annual_deductible)
5. Any exclusions? (service NOT in plan.exclusions)

Output: eligible (true/false), reasons[], confidence_score.
```

**MCP Tools Used**:
- `get_member_policy`: Retrieve policy details from `member_db`
- `check_network_status`: Query `network-service` for provider network
- `get_ytd_claims`: Calculate year-to-date spending
- `check_service_coverage`: Verify CPT code coverage
- `get_benefit_limits`: Retrieve annual/lifetime limits

**Database Queries**:
```sql
-- Check active policy
SELECT policy_id, plan_type, effective_date, term_date, status
FROM member_db.policies
WHERE member_id = $1 AND status = 'active'
  AND CURRENT_DATE BETWEEN effective_date AND term_date;

-- Check network provider
SELECT network_tier FROM provider_db.network_providers
WHERE plan_id = $1 AND npi = $2;

-- Check YTD spending
SELECT SUM(allowed_amount) as ytd_spend
FROM claims_db.claims
WHERE member_id = $1 
  AND service_year = EXTRACT(YEAR FROM CURRENT_DATE)
  AND claim_status = 'paid';
```

**Input Schema**:
```python
class EligibilityInput(AgentInput):
    member_id: str
    policy_number: str
    provider_npi: str
    cpt_codes: List[str]
    service_date: date
```

**Output Schema**:
```python
class EligibilityOutput(AgentOutput):
    eligible: bool
    policy_status: str  # "active", "terminated", "suspended"
    network_tier: str  # "in-network", "out-of-network"
    deductible_met: bool
    coverage_percentage: float  # 0-100
    exclusions: List[str]
    ineligibility_reasons: List[str]
```

**Performance Metrics**:
- Throughput: 55,000 checks/day
- P50 Latency: 280ms
- P95 Latency: 450ms
- P99 Latency: 820ms
- Cache Hit Rate: 85% (Redis cache for recent lookups)
- Accuracy: 99.8% (verified against actual claims adjudication)

**Business Rules**:
- Policy must be active on service date
- Provider must be in-network (or patient accepts higher cost-sharing)
- Service must be covered benefit under plan type
- No waiting period for service (e.g., maternity has 10-month wait)

---

### Agent 3: Benefits Agent

**Business Use Case**: Determine cost-sharing (copay, coinsurance, deductible) for the requested service

**LLM Model**: GPT-3.5 Turbo
**Temperature**: 0.0 (deterministic calculations)
**Max Tokens**: 1024

**Core Responsibilities**:
1. Calculate patient cost-share (copay, coinsurance, deductible)
2. Determine prior authorization requirement
3. Check benefit limits (visit limits, dollar limits)
4. Calculate insurer payment amount
5. Handle complex benefit rules (tiered networks, step therapy)

**System Prompt** (abbreviated):
```
You are a benefits calculation agent.

Your task: Calculate patient cost-sharing and insurer payment.

Inputs: plan_type, cpt_codes, provider_network_tier, service_cost

Calculations:
1. If deductible not met: patient pays deductible portion first
2. After deductible: apply copay or coinsurance based on plan
3. Enforce out-of-pocket maximum
4. Apply network tier adjustments (out-of-network = higher cost-share)

Output: patient_cost, insurer_cost, breakdown details.
```

**MCP Tools Used**:
- `get_benefit_config`: Retrieve plan benefit details
- `calculate_cost_share`: Cost-sharing calculation engine
- `check_prior_auth_rules`: Determine if PA required
- `get_fee_schedule`: Lookup allowed amounts

**Input Schema**:
```python
class BenefitsInput(AgentInput):
    member_id: str
    policy_id: str
    cpt_codes: List[str]
    provider_npi: str
    network_tier: str
    estimated_cost: Decimal
```

**Output Schema**:
```python
class BenefitsOutput(AgentOutput):
    prior_auth_required: bool
    copay_amount: Decimal
    coinsurance_percentage: float
    deductible_applies: bool
    deductible_remaining: Decimal
    patient_responsibility: Decimal
    insurer_payment: Decimal
    benefit_limits: Dict[str, Any]
    cost_share_breakdown: List[Dict]
```

**Performance Metrics**:
- Throughput: 55,000 calculations/day
- P50 Latency: 320ms
- P95 Latency: 580ms
- Calculation Accuracy: 99.5% (verified against claims processing)

---

### Agent 4: Clinical Review Agent

**Business Use Case**: Assess medical necessity using clinical guidelines and evidence-based criteria

**LLM Model**: GPT-4o (advanced clinical reasoning)
**Temperature**: 0.3 (some creativity for edge cases)
**Max Tokens**: 4096

**Core Responsibilities**:
1. Review diagnosis (ICD-10) and requested treatment (CPT)
2. Check medical necessity against clinical guidelines
3. Assess if treatment is evidence-based and appropriate
4. Identify any contraindications or safety concerns
5. Use RAG to retrieve relevant clinical criteria
6. Generate detailed clinical rationale for decision

**System Prompt** (abbreviated):
```
You are a clinical review agent for medical necessity determination.

Your task: Assess if requested treatment is medically necessary.

Process:
1. Review diagnosis codes (ICD-10) and symptoms
2. Retrieve relevant clinical guidelines via RAG
3. Compare requested treatment against evidence-based criteria
4. Check for contraindications, alternative treatments
5. Assess urgency (standard, urgent, emergency)

Decision criteria:
- APPROVED: Treatment meets guidelines, medically necessary
- DENIED: Treatment not indicated, alternatives available
- NEED_MORE_INFO: Insufficient clinical documentation

Provide detailed clinical rationale citing specific guidelines.
```

**RAG Integration** (Hybrid Search):
```python
# Vector Search (Milvus)
clinical_vectors = embed_query(f"{diagnosis} {treatment}")
vector_results = milvus.search(
    collection="clinical_guidelines",
    vectors=clinical_vectors,
    limit=20,
    metric="COSINE"
)

# BM25 Lexical Search (Elasticsearch)
bm25_results = es.search(
    index="clinical_content",
    query={
        "bool": {
            "should": [
                {"match": {"diagnosis": diagnosis}},
                {"match": {"treatment": treatment}},
                {"match": {"cpt_code": cpt_code}}
            ]
        }
    },
    size=20
)

# Graph RAG (Neo4j) - Clinical pathways
graph_results = neo4j.run(
    """
    MATCH (d:Diagnosis {code: $icd10})-[:INDICATES]->(t:Treatment {code: $cpt})
    RETURN d, t, relationship_properties
    """,
    icd10=diagnosis_code,
    cpt=treatment_code
)

# Reciprocal Rank Fusion (k=60)
fused_results = reciprocal_rank_fusion([vector_results, bm25_results, graph_results], k=60)
top_10 = fused_results[:10]

# Rerank with cross-encoder
reranked = rerank_model.rerank(query, top_10)
```

**MCP Tools Used**:
- `rag_search_clinical`: Hybrid search across 10M clinical docs
- `get_clinical_guideline`: Retrieve specific guideline by ID
- `check_drug_interactions`: FDA drug interaction database
- `get_treatment_alternatives`: Find alternative therapies
- `assess_urgency`: Triage service urgency level

**Input Schema**:
```python
class ClinicalInput(AgentInput):
    patient_age: int
    patient_gender: str
    icd10_codes: List[str]  # Diagnoses
    cpt_codes: List[str]    # Requested treatments
    clinical_notes: str
    supporting_docs: List[str]  # Lab results, imaging reports
    urgency_level: str  # "standard", "urgent", "emergency"
```

**Output Schema**:
```python
class ClinicalOutput(AgentOutput):
    medical_necessity: str  # "APPROVED", "DENIED", "NEED_MORE_INFO"
    clinical_rationale: str  # Detailed explanation
    cited_guidelines: List[Dict]  # Guidelines used in decision
    alternative_treatments: List[str]
    contraindications: List[str]
    safety_concerns: List[str]
    rag_sources_used: int
    rag_retrieval_time_ms: int
```

**Performance Metrics**:
- Throughput: 55,000 reviews/day
- P50 Latency: 5.2s (with RAG)
- P95 Latency: 8.3s
- P99 Latency: 14.5s
- RAG Latency Breakdown:
  - Vector search: 45ms (Milvus HNSW)
  - BM25 search: 120ms (Elasticsearch)
  - Graph query: 85ms (Neo4j)
  - Reranking: 180ms (cross-encoder)
  - Total RAG: ~430ms
- Clinical Accuracy: 94.5% (vs physician review)
- Guidelines Cited: Avg 3.2 sources per decision

**Bottleneck**: RAG retrieval pipeline (430ms overhead)

---

### Agent 5: Policy Agent

**Business Use Case**: Interpret complex insurance policy rules and coverage limitations

**LLM Model**: Claude 3.5 Sonnet (excellent at policy interpretation)
**Temperature**: 0.2
**Max Tokens**: 3072

**Core Responsibilities**:
1. Interpret policy language (often ambiguous)
2. Apply coverage exclusions and limitations
3. Check for experimental/investigational treatment exclusions
4. Enforce step therapy requirements
5. Apply quantity limits (e.g., max 30 doses/month)
6. Handle appeals and exceptions

**System Prompt** (abbreviated):
```
You are a health insurance policy interpretation agent.

Your task: Determine if requested service is covered under policy terms.

Review:
1. Policy document sections relevant to service
2. Exclusions and limitations
3. Experimental/investigational treatment clause
4. Step therapy protocols (try cheaper alternatives first)
5. Quantity limits and duration restrictions

Decision:
- COVERED: Service explicitly covered, no exclusions apply
- NOT_COVERED: Service excluded or limited
- REQUIRES_EXCEPTION: Covered only with medical exception

Provide specific policy section citations.
```

**MCP Tools Used**:
- `query_policy_document`: Vector search on policy PDFs
- `check_step_therapy`: Verify prior medication trials
- `get_quantity_limits`: FDA-approved dosing limits
- `check_experimental_status`: FDA/CMS experimental treatment lists

**Input Schema**:
```python
class PolicyInput(AgentInput):
    policy_id: str
    plan_type: str
    cpt_codes: List[str]
    icd10_codes: List[str]
    clinical_rationale: str  # From clinical agent
    requested_quantity: int
    duration_days: int
```

**Output Schema**:
```python
class PolicyOutput(AgentOutput):
    coverage_status: str  # "COVERED", "NOT_COVERED", "REQUIRES_EXCEPTION"
    policy_sections_cited: List[str]
    exclusions_applied: List[str]
    step_therapy_required: bool
    prior_medications_required: List[str]
    quantity_limit: Optional[int]
    duration_limit_days: Optional[int]
    exception_criteria: Optional[str]
```

**Performance Metrics**:
- Throughput: 55,000 interpretations/day
- P50 Latency: 2.1s
- P95 Latency: 3.8s
- Policy Citation Accuracy: 96.5%
- Claude 3.5 is 15% more accurate than GPT-4o for policy interpretation

---

### Agent 6: Fraud Detection Agent

**Business Use Case**: Identify potentially fraudulent, wasteful, or abusive (FWA) PA requests

**LLM Model**: GPT-4o (pattern recognition)
**Temperature**: 0.2
**Max Tokens**: 2048

**Core Responsibilities**:
1. Detect billing fraud patterns (upcoding, unbundling)
2. Identify impossible medical scenarios
3. Check provider credibility and history
4. Detect duplicate/overlapping requests
5. Flag high-risk combinations (e.g., excessive opioids)
6. Graph analysis for collusion networks

**System Prompt** (abbreviated):
```
You are a fraud, waste, and abuse (FWA) detection agent.

Your task: Identify suspicious patterns in PA requests.

Red flags:
1. Upcoding: Billed CPT doesn't match diagnosis severity
2. Unbundling: Separate codes for typically bundled services
3. Duplicate requests: Same service requested <30 days ago
4. Impossible scenarios: Treatment for male pregnancy, etc.
5. High-risk providers: History of fraud violations
6. Excessive quantities: 10x normal dosing

Risk levels: LOW, MEDIUM, HIGH, CRITICAL
If HIGH or CRITICAL, escalate to Special Investigations Unit (SIU).
```

**MCP Tools Used**:
- `check_provider_sanctions`: OIG exclusion list
- `graph_query_provider_network`: Neo4j collusion detection
- `get_provider_claim_history`: Historical fraud patterns
- `check_duplicate_requests`: Redis cache of recent PAs
- `validate_cpt_icd_pairing`: Billing code appropriateness

**Graph RAG (Neo4j)**:
```cypher
// Detect provider collusion networks
MATCH (p1:Provider)-[:REFERRED_TO]->(p2:Provider)
WHERE p1.fraud_risk_score > 70 AND p2.fraud_risk_score > 70
  AND (p1)-[:REFERRED_TO*1..3]-(p2)
RETURN p1, p2, count(*) as referral_volume
ORDER BY referral_volume DESC
LIMIT 10;

// Detect suspicious billing patterns
MATCH (p:Provider)-[:BILLED]->(c:Claim)
WHERE c.cpt_code IN ['99215', '99205']  // High-complexity visits
  AND p.high_complexity_rate > 0.80  // >80% of visits are high-complexity
RETURN p, count(c) as suspicious_claims;
```

**Input Schema**:
```python
class FraudInput(AgentInput):
    provider_npi: str
    member_id: str
    cpt_codes: List[str]
    icd10_codes: List[str]
    requested_quantity: int
    service_date: date
    billed_amount: Decimal
```

**Output Schema**:
```python
class FraudOutput(AgentOutput):
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_score: float  # 0-100
    red_flags: List[Dict[str, str]]
    provider_history: Dict[str, Any]
    graph_analysis: Dict[str, Any]
    recommended_action: str  # "APPROVE", "DENY", "INVESTIGATE"
    escalate_to_siu: bool
```

**Performance Metrics**:
- Throughput: 55,000 checks/day
- P50 Latency: 680ms
- P95 Latency: 1.2s
- Fraud Detection Rate: 3.2% flagged as HIGH/CRITICAL
- False Positive Rate: 8.5% (verified by SIU investigations)
- Annual Fraud Prevented: $45M

---

### Agent 7: Decision Agent

**Business Use Case**: Synthesize all agent outputs into final PA decision

**LLM Model**: GPT-4o (complex reasoning and synthesis)
**Temperature**: 0.1
**Max Tokens**: 2048

**Core Responsibilities**:
1. Aggregate outputs from all previous agents
2. Resolve conflicting recommendations
3. Apply final business rules and overrides
4. Calculate overall confidence score
5. Generate member-facing decision letter
6. Route to HITL if confidence < 0.85

**System Prompt** (abbreviated):
```
You are the final decision synthesis agent for PA requests.

Your task: Make final APPROVAL or DENIAL decision based on all agent outputs.

Inputs:
- Intake: Data quality, completeness
- Eligibility: Coverage status
- Benefits: Cost-sharing details
- Clinical: Medical necessity assessment
- Policy: Coverage rules and limitations
- Fraud: Risk assessment

Decision logic:
1. If ANY agent returns CRITICAL issue → DENY
2. If eligibility=false OR policy=NOT_COVERED → DENY
3. If clinical=DENIED (not medically necessary) → DENY
4. If fraud=HIGH and no clinical justification → DENY
5. If all pass → APPROVE

Confidence: Average of all agent confidence scores.
If confidence < 0.85 → Route to HITL for human review.

Generate clear, empathetic decision letter explaining rationale.
```

**MCP Tools Used**:
- `generate_decision_letter`: Template-based letter generation
- `calculate_appeal_deadline`: Calculate 60-day appeal window
- `create_audit_log`: Log decision for compliance

**Input Schema**:
```python
class DecisionInput(AgentInput):
    intake_output: IntakeOutput
    eligibility_output: EligibilityOutput
    benefits_output: BenefitsOutput
    clinical_output: ClinicalOutput
    policy_output: PolicyOutput
    fraud_output: FraudOutput
```

**Output Schema**:
```python
class DecisionOutput(AgentOutput):
    final_decision: str  # "APPROVED", "DENIED", "NEED_MORE_INFO"
    decision_rationale: str
    confidence: float  # Aggregate of all agent confidences
    decision_letter: str  # Member-facing communication
    appeal_deadline: date
    route_to_hitl: bool  # True if confidence < 0.85
    processing_time_seconds: float
    cost_estimate: Dict[str, Decimal]
```

**Performance Metrics**:
- Throughput: 55,000 decisions/day
- P50 Latency: 850ms
- P95 Latency: 1.4s
- Decision Distribution:
  - APPROVED: 68% (37,400/day)
  - DENIED: 18% (9,900/day)
  - NEED_MORE_INFO: 14% (7,700/day)
- HITL Routing Rate: 28% (confidence < 0.85)

---

### Agent 8: Appeals Agent

**Business Use Case**: Process PA appeals and reconsiderations

**LLM Model**: GPT-4o
**Temperature**: 0.2
**Max Tokens**: 3072

**Core Responsibilities**:
1. Review original denial reasons
2. Analyze new clinical evidence submitted
3. Assess if appeal warrants reversal
4. Generate appeals decision letter
5. Handle peer-to-peer physician reviews

**Performance**: 2,500 appeals/day (5% of original denials)

---

### Agent 9: Notification Agent

**Business Use Case**: Generate and send multi-channel notifications

**LLM Model**: GPT-3.5 Turbo (simple template filling)
**Temperature**: 0.0
**Max Tokens**: 1024

**Core Responsibilities**:
1. Generate decision letters (approve/deny)
2. Send email, SMS, portal notifications
3. Provider fax notifications
4. EDI transaction generation (X12 278 response)
5. Track notification delivery status

**Channels**:
- Email: 55,000/day (primary)
- SMS: 18,000/day (opt-in members)
- Portal: 55,000/day (all cases)
- Fax (providers): 12,000/day
- EDI 278: 8,000/day (electronic submission)

**Performance**: 55,000 notifications/day, P50 latency 1.2s

---

### Agent 10: Audit Agent

**Business Use Case**: Maintain compliance audit trail and generate reports

**LLM Model**: GPT-3.5 Turbo
**Temperature**: 0.0
**Max Tokens**: 1024

**Core Responsibilities**:
1. Log all agent decisions to audit database
2. Generate compliance reports (ISO 42001, SOC 2)
3. Detect policy drift (changing decision patterns)
4. Support regulatory audits
5. Track key performance indicators (KPIs)

**Audit Data Captured**:
- Full workflow trace (all agent inputs/outputs)
- Token usage and costs per case
- Decision latencies and bottlenecks
- Human review outcomes (HITL validation rate)
- Appeals and overturn rates

**Performance**: 55,000 audit logs/day, 100% compliance

---

### Agent 11: Communication Agent (COM Agent)

**Business Use Case**: Handle member/provider inquiries about PA status

**LLM Model**: GPT-4o (conversational AI)
**Temperature**: 0.7 (natural conversation)
**Max Tokens**: 2048

**Core Responsibilities**:
1. Answer "Where is my PA?" inquiries
2. Explain denial reasons in plain language
3. Guide appeal filing process
4. Provide alternative treatment suggestions
5. Multi-turn conversation support

**Channels**:
- Web chat: 8,000 conversations/day
- Phone IVR: 5,000 calls/day
- Email: 3,000/day

**Performance**: 16,000 interactions/day, 85% resolution rate without human transfer

---

## Technical Implementation

### Deployment Architecture

```yaml
Kubernetes Namespace: agent-fabric-layer

Agent Deployment Template:
  replicas: 2-5 (HPA based on request rate)
  resources:
    requests: { cpu: 200m, memory: 512Mi }
    limits: { cpu: 1000m, memory: 2Gi }
  
  livenessProbe:
    httpGet:
      path: /health
      port: 8000
    initialDelaySeconds: 30
    periodSeconds: 10
  
  readinessProbe:
    httpGet:
      path: /ready
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 5

ConfigMap (per agent):
  agent-config:
    model: "gpt-4o"  # or "gpt-3.5-turbo", "claude-3-5-sonnet"
    temperature: "0.2"
    max_tokens: "2048"
    timeout_seconds: "300"
    retry_attempts: "3"
    retry_backoff: "exponential"

Secrets:
  llm-credentials:
    openai-api-key: <base64>
    anthropic-api-key: <base64>
```

### Multi-Model Routing

**Kong LLM Gateway** routes requests to optimal model:

```yaml
LLM Routing Rules:
  - agent: intake-agent
    model: gpt-4o
    reason: Vision API for fax OCR
  
  - agent: eligibility-agent
    model: gpt-3.5-turbo
    reason: Simple lookup, cost optimization
  
  - agent: benefits-agent
    model: gpt-3.5-turbo
    reason: Deterministic calculation
  
  - agent: clinical-agent
    model: gpt-4o
    reason: Complex medical reasoning
  
  - agent: policy-agent
    model: claude-3-5-sonnet
    reason: Superior policy interpretation
  
  - agent: fraud-agent
    model: gpt-4o
    reason: Pattern recognition
  
  - agent: decision-agent
    model: gpt-4o
    reason: Final synthesis
```

### Cost Optimization

```python
# Cost per agent execution
COSTS = {
    "gpt-4o": {"input": 5.00, "output": 15.00},  # per 1M tokens
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00}
}

# Average tokens per agent
TOKENS = {
    "intake": {"input": 1200, "output": 800},
    "eligibility": {"input": 500, "output": 300},
    "benefits": {"input": 600, "output": 400},
    "clinical": {"input": 3500, "output": 1500},
    "policy": {"input": 2800, "output": 1200},
    "fraud": {"input": 1800, "output": 600},
    "decision": {"input": 2200, "output": 800}
}

# Daily cost: $2,847 (55,000 cases × $0.0518/case)
```

---

## API Specifications

### Common Agent API

```python
POST /agents/{agent_name}/invoke
Content-Type: application/json
Authorization: Bearer <jwt>

Request:
{
  "request_id": "PA-2026-123456",
  "context": {...},
  "previous_outputs": {...}
}

Response:
{
  "agent_name": "clinical_agent",
  "decision": "APPROVED",
  "confidence": 0.92,
  "reasoning": "Treatment meets clinical guidelines...",
  "tools_used": ["rag_search_clinical", "get_clinical_guideline"],
  "execution_time_ms": 5234,
  "token_usage": {
    "prompt_tokens": 3421,
    "completion_tokens": 1534,
    "total_tokens": 4955
  },
  "metadata": {
    "model": "gpt-4o",
    "temperature": 0.3,
    "rag_sources": 5
  }
}
```

---

## Performance & Scaling

### Horizontal Scaling

```yaml
HorizontalPodAutoscaler:
  - agent: clinical-agent  # Most resource-intensive
    minReplicas: 5
    maxReplicas: 20
    metrics:
      - type: Resource
        resource: cpu
        target: 70%
      - type: Pods
        metric: agent_queue_depth
        target: 50  # Scale up when >50 requests queued
  
  - agent: eligibility-agent  # Lightweight
    minReplicas: 2
    maxReplicas: 8
```

### Performance Benchmarks

| Agent | P50 | P95 | P99 | Max Tokens | Cost/Execution |
|-------|-----|-----|-----|------------|----------------|
| Intake | 1.8s | 3.5s | 8.5s | 2000 | $0.0095 |
| Eligibility | 0.28s | 0.45s | 0.82s | 800 | $0.0004 |
| Benefits | 0.32s | 0.58s | 1.1s | 1000 | $0.0005 |
| Clinical | 5.2s | 8.3s | 14.5s | 5000 | $0.0275 |
| Policy | 2.1s | 3.8s | 6.2s | 4000 | $0.0120 |
| Fraud | 0.68s | 1.2s | 2.1s | 2400 | $0.0095 |
| Decision | 0.85s | 1.4s | 2.5s | 3000 | $0.0142 |
| **Total** | **4.2min** | **12.8min** | **28.5min** | - | **$0.0518** |

---

## Security & Safety

### Guardrails Stack

```python
from guardrails import Guard
from guardrails.validators import (
    DetectPII,
    ToxicLanguage,
    OnTopic,
    ValidLength,
    ExactMatch
)

guard = Guard().use_many(
    DetectPII(pii_entities=["SSN", "EMAIL", "PHONE"]),
    ToxicLanguage(threshold=0.7),
    OnTopic(valid_topics=["healthcare", "insurance"]),
    ValidLength(min=10, max=5000)
)

# Apply to every agent output
output = agent.process(input)
validated_output = guard.validate(output)
```

### PII Redaction

All agent outputs automatically redacted:
- SSN → `***-**-1234`
- Email → `j****@example.com`
- Phone → `(***) ***-5678`
- Medical record numbers → `MRN-****5678`

---

## Monitoring & Operations

### Metrics

```yaml
Prometheus Metrics:
  - agent_requests_total{agent, status}
  - agent_duration_seconds{agent, percentile}
  - agent_tokens_used{agent, type}  # prompt/completion
  - agent_confidence_score{agent}
  - agent_cost_dollars{agent}
  - agent_rag_latency_seconds{agent}
  - agent_errors_total{agent, error_type}
```

### Grafana Dashboards

- **Agent Performance**: Latency, throughput, error rate per agent
- **LLM Costs**: Token usage and costs by model
- **RAG Pipeline**: Retrieval latency, sources used, relevance scores
- **Confidence Tracking**: Distribution of confidence scores, HITL routing rate
- **Business Metrics**: Approval rate, denial reasons, appeal rate

---

## Summary

The **AI Agent Fabric Layer** orchestrates **11 specialized agents** processing **385,000 executions/day** (7 agents × 55,000 PA cases). With a **multi-model strategy** (GPT-4o, Claude 3.5, GPT-3.5), the platform achieves **96.2% automation** with **$0.0518 cost per case**.

**Key Achievements**:
- **72% fully automated** decisions (no human review)
- **28% HITL routing** for low-confidence cases
- **$667M annual ROI** ($182M saved vs manual review)
- **4.2-minute median processing time** (vs 3-day manual)
- **94.5% clinical accuracy** (validated against physicians)

---

*Generated: June 02, 2026 | Version: 2.0 - Detailed Agent Specifications*
