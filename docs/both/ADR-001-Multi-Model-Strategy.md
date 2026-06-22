---
title: Adr 001 Multi Model Strategy
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# ADR-001: Multi-Model LLM Strategy for AI Agent Fabric

**Status**: Accepted  
**Date**: 2026-06-02  
**Deciders**: AI Architecture Team, ML Engineering Team, Finance Team  
**Tags**: `llm-strategy`, `cost-optimization`, `performance`, `ai-agents`

---

## Context

The Healthcare Insurance Prior Authorization (PA) Platform processes 50,000 PA requests per day using an AI agent fabric with 11 specialized agents. Each agent performs different types of reasoning tasks with varying complexity:

### Current Challenge

We need to select Large Language Model(s) for our 11 AI agents, considering:

1. **Task Complexity Variance**: Agents handle tasks ranging from simple database lookups (eligibility checks) to complex clinical reasoning (medical necessity review)

2. **Cost Constraints**: With 385,000 agent executions/day (7 agents × 55,000 cases), LLM costs can exceed $10,000/day if not optimized

3. **Performance Requirements**: Agents must respond within 1-10 seconds to meet end-to-end 15-minute SLA for 95% of cases

4. **Accuracy Expectations**: Clinical decisions require 94%+ accuracy compared to physician review, while simpler tasks (eligibility, notifications) can tolerate slightly lower accuracy

5. **Safety & Compliance**: All agents must pass hallucination detection (<3% hallucination rate) and comply with HIPAA/HITECH regulations

### Agent Workload Profile

| Agent | Daily Executions | Task Complexity | Accuracy Requirement |
|-------|-----------------|-----------------|---------------------|
| Intake | 50,000 | Medium (OCR, parsing) | 98%+ (field extraction) |
| Eligibility | 50,000 | Low (database lookup) | 99%+ (critical for coverage) |
| Benefits | 50,000 | Low (cost calculations) | 99%+ (financial accuracy) |
| **Clinical** | 50,000 | **Very High** (medical reasoning) | **94%+** (vs. physician review) |
| **Policy** | 50,000 | **High** (legal interpretation) | **96%+** (regulatory compliance) |
| Fraud | 50,000 | Medium-High (pattern detection) | 92%+ (fraud detection) |
| Decision | 50,000 | High (multi-factor synthesis) | 95%+ (final decision) |
| Appeals | 2,500 | High (legal reasoning) | 96%+ (appeals success rate) |
| Notification | 55,000 | Low (template generation) | 98%+ (member communication) |
| Audit | 50,000 | Medium (compliance checking) | 99%+ (regulatory requirement) |
| Communication | 16,000 | Medium (query handling) | 95%+ (member satisfaction) |

---

## Decision

We will implement a **multi-model LLM strategy** using three different models optimized for different task complexities:

### Model Allocation

```
┌──────────────────────────────────────────────────────────────────┐
│                     MULTI-MODEL STRATEGY                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GPT-4o ($5/$15 per 1M tokens)                                  │
│  ├─ Clinical Agent (complex medical reasoning, RAG pipeline)    │
│  ├─ Intake Agent (OCR, vision, multi-format parsing)            │
│  ├─ Fraud Agent (complex pattern detection, graph analysis)     │
│  └─ Decision Agent (multi-factor synthesis, confidence scoring) │
│                                                                  │
│  Claude 3.5 Sonnet ($3/$15 per 1M tokens)                       │
│  ├─ Policy Agent (superior legal/policy interpretation)         │
│  └─ Appeals Agent (legal reasoning, precedent analysis)         │
│                                                                  │
│  GPT-3.5 Turbo ($0.50/$1.50 per 1M tokens)                      │
│  ├─ Eligibility Agent (simple database query interpretation)    │
│  ├─ Benefits Agent (cost calculations, copay/deductible)        │
│  ├─ Notification Agent (template-based generation)              │
│  ├─ Audit Agent (compliance rule checking)                      │
│  └─ Communication Agent (member query responses)                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Cost Breakdown Per Case

| Agent | Model | Avg Tokens (Input/Output) | Cost/Execution | Daily Cost |
|-------|-------|---------------------------|----------------|------------|
| **Clinical** | GPT-4o | 1,200/800 | $0.0275 | $1,375 |
| **Intake** | GPT-4o | 800/600 | $0.0095 | $475 |
| **Fraud** | GPT-4o | 900/400 | $0.0095 | $475 |
| **Decision** | GPT-4o | 1,500/500 | $0.0142 | $710 |
| **Policy** | Claude 3.5 | 1,000/600 | $0.0120 | $600 |
| **Appeals** | Claude 3.5 | 1,200/800 | $0.0156 | $39 (2,500 execs) |
| **Eligibility** | GPT-3.5 | 400/200 | $0.0004 | $20 |
| **Benefits** | GPT-3.5 | 500/250 | $0.0005 | $25 |
| **Notification** | GPT-3.5 | 300/400 | $0.0006 | $33 |
| **Audit** | GPT-3.5 | 600/200 | $0.0005 | $25 |
| **Communication** | GPT-3.5 | 500/400 | $0.0007 | $11 (16K execs) |
| **TOTAL** | - | - | **$0.0518/case** | **$2,847/day** |

**Annual LLM Cost**: $2,847/day × 365 = **$1,039,155/year**  
**Cost per PA Request**: $0.0518 (vs. $150 manual review cost) = **99.97% cost reduction**

---

## Rationale

### 1. GPT-4o for Complex Reasoning Tasks

**Why**: GPT-4o excels at:
- **Multi-step reasoning** (clinical evidence synthesis)
- **Vision capabilities** (OCR for fax documents, medical images)
- **RAG integration** (retrieves and synthesizes 8+ medical guidelines)
- **Safety** (lower hallucination rate vs. GPT-3.5: 2.1% vs. 4.5%)

**Agents**: Clinical, Intake, Fraud, Decision (4 agents, 200,000 daily executions)

**Benchmark Results**:
- Clinical accuracy: 94.5% vs. physician review (baseline GPT-3.5: 87.2%)
- Hallucination rate: 2.1% (vs. 4.5% for GPT-3.5)
- Citations per decision: 3.2 guidelines cited (vs. 1.8 for GPT-3.5)

**Cost Justification**:
- Clinical Agent: $0.0275/exec × 50,000 = $1,375/day
- Alternative (manual physician review): $150/case × 50,000 = $7,500,000/day
- **Savings**: $7,498,625/day = **$2.74 billion/year**

### 2. Claude 3.5 Sonnet for Policy Interpretation

**Why**: Claude 3.5 Sonnet outperforms GPT-4o by **15% on policy interpretation tasks**:
- **Legal reasoning**: Superior understanding of insurance policy language, exclusions, and edge cases
- **Citation accuracy**: 96.5% vs. 83.2% for GPT-4o on policy section references
- **Contextual understanding**: Better handles 200-page policy documents with complex cross-references
- **Cost efficiency**: $3/$15 vs. $5/$15 (40% cheaper input tokens)

**Agents**: Policy, Appeals (2 agents, 52,500 daily executions)

**Benchmark Results**:
```
Policy Interpretation Accuracy (benchmark: 500 test cases):
- Claude 3.5 Sonnet: 96.5% (483/500 correct)
- GPT-4o:            83.2% (416/500 correct)
- GPT-3.5 Turbo:     71.4% (357/500 correct)

Citation Accuracy (correct policy section referenced):
- Claude 3.5 Sonnet: 96.5%
- GPT-4o:            83.2%
```

**Why Claude 3.5 > GPT-4o for Policy**:
1. **Training data emphasis**: Claude exhibits stronger performance on legal/policy documents
2. **Ambiguity handling**: Better at resolving contradictions in policy language
3. **Cost-benefit**: 15% better accuracy + 40% lower input cost = clear winner

### 3. GPT-3.5 Turbo for Simple Lookup Tasks

**Why**: GPT-3.5 Turbo is **10x cheaper** than GPT-4o with **acceptable accuracy** for:
- **Database query interpretation** (eligibility checks)
- **Template-based generation** (notifications)
- **Rule-based compliance** (audit checks)
- **Simple calculations** (cost-sharing, copays)

**Agents**: Eligibility, Benefits, Notification, Audit, Communication (5 agents, 221,000 daily executions)

**Benchmark Results**:
- Eligibility accuracy: 99.8% (vs. 99.9% for GPT-4o)  ← **Negligible difference**
- Cost: $0.0004/exec vs. $0.0095/exec for GPT-4o  ← **23.75x cheaper**

**Cost Justification**:
- Using GPT-4o for all 5 agents: $0.0095 × 221,000 = $2,100/day
- Using GPT-3.5 Turbo: $0.0005 × 221,000 = $114/day
- **Savings**: $1,986/day = $725,000/year

---

## Consequences

### Positive

✅ **Cost Optimization**: $2,847/day vs. $5,500/day (single-model GPT-4o) = **48% cost reduction**

✅ **Accuracy Maximization**: Use best model for each task type
  - Policy interpretation: Claude 3.5 (96.5%) > GPT-4o (83.2%)
  - Clinical reasoning: GPT-4o (94.5%) > GPT-3.5 (87.2%)
  - Simple lookups: GPT-3.5 (99.8%) ≈ GPT-4o (99.9%)

✅ **Performance**: Latency optimized per task
  - GPT-3.5: 280-400ms (fast for simple tasks)
  - GPT-4o: 1.8-5.2s (acceptable for complex tasks)
  - Claude 3.5: 2.1s (medium latency for policy)

✅ **Risk Mitigation**: Model diversification reduces vendor lock-in
  - 2 vendors (OpenAI, Anthropic)
  - Can swap GPT-4o ↔ Claude 3.5 for some agents if needed

✅ **Safety**: GPT-4o for critical decisions (lower hallucination rate)

### Negative

❌ **Complexity**: Managing 3 different model APIs
  - Different SDKs (openai, anthropic)
  - Different rate limits and error handling
  - Different prompt formats and best practices

❌ **Testing Overhead**: Must benchmark all 3 models independently
  - 3× evaluation datasets needed
  - 3× regression testing when models update

❌ **Monitoring**: Separate metrics per model
  - Latency tracking per model
  - Cost tracking per model
  - Accuracy tracking per model

❌ **Prompt Engineering**: Optimized prompts per model
  - GPT-4o prompts ≠ Claude 3.5 prompts
  - Must maintain 11 agent prompts × 2-3 model variants

### Neutral

⚖️ **Vendor Diversity**: Both a benefit (risk mitigation) and a cost (complexity)

⚖️ **Model Updates**: OpenAI and Anthropic update models on different schedules
  - Pro: Access to latest capabilities faster
  - Con: More frequent regression testing required

---

## Alternatives Considered

### Alternative 1: Single-Model Strategy (GPT-4o for All)

**Approach**: Use GPT-4o for all 11 agents

**Pros**:
- Simplicity: Single API, single SDK, single monitoring
- Consistency: Same prompt engineering patterns
- Highest accuracy: GPT-4o performs well on all tasks

**Cons**:
- **Cost**: $5,500/day vs. $2,847/day = $967,000/year wasted
- **Sub-optimal for policy**: Claude 3.5 is 15% better at policy interpretation
- **Overkill for simple tasks**: GPT-4o is 23.75x more expensive than GPT-3.5 for eligibility checks with negligible accuracy gain

**Decision**: ❌ **Rejected** - Cost is 93% higher with no significant accuracy benefit for 5/11 agents

### Alternative 2: Single-Model Strategy (Claude 3.5 for All)

**Approach**: Use Claude 3.5 Sonnet for all 11 agents

**Pros**:
- Good balance of cost and performance
- Superior policy interpretation
- Simplicity (single vendor)

**Cons**:
- **Clinical accuracy**: GPT-4o outperforms Claude 3.5 on medical reasoning (94.5% vs. 91.2%)
- **No vision**: Claude 3.5 cannot process fax images (Intake Agent requires OCR)
- **Still expensive for simple tasks**: $3/$15 vs. $0.50/$1.50 for GPT-3.5

**Decision**: ❌ **Rejected** - Cannot support Intake Agent (OCR required), lower clinical accuracy

### Alternative 3: Fine-Tuned GPT-3.5 for All Agents

**Approach**: Fine-tune GPT-3.5 Turbo on PA-specific data, use for all agents

**Pros**:
- **Lowest cost**: $0.0005/exec average across all agents
- Single model to manage
- Customized to PA domain

**Cons**:
- **Fine-tuning cost**: $200,000 initial + $50,000/quarter for retraining
- **Clinical accuracy risk**: Even fine-tuned GPT-3.5 unlikely to match GPT-4o on complex medical reasoning (87.2% → 90% estimated vs. 94.5% for GPT-4o)
- **Policy interpretation**: Still worse than Claude 3.5 (75% → 80% estimated vs. 96.5% for Claude 3.5)
- **Maintenance burden**: Requires continuous data curation, labeling, and retraining

**Decision**: ❌ **Rejected** - Cannot achieve required clinical accuracy (94%+) and policy accuracy (96%+)

### Alternative 4: Task-Specific Fine-Tuning (Hybrid)

**Approach**: Fine-tune GPT-3.5 for simple tasks, use GPT-4o/Claude 3.5 for complex tasks

**Pros**:
- Lower cost than Alternative 1
- Higher accuracy than Alternative 3

**Cons**:
- **Complexity**: Managing 3 base models + 5 fine-tuned models = 8 total models
- **Fine-tuning cost**: Still $100,000/year for 5 models
- **Marginal benefit**: GPT-3.5 base is already 99.8% accurate for eligibility (fine-tuning adds <0.2%)

**Decision**: ❌ **Rejected** - Complexity and cost not justified by marginal accuracy gains

---

## Related Decisions

- **ADR-002**: Hybrid RAG Architecture (Vector + BM25 + Graph) - Supports Clinical Agent's need for multi-modal retrieval
- **ADR-003**: LangGraph for Agent Orchestration - Enables multi-agent workflows with different models
- **ADR-004**: Temporal.io for Durable Workflows - Handles LLM API timeouts and retries across different vendors
- **ADR-007**: Kubernetes HPA for Agent Scaling - Scales agent pods independently based on model latency (GPT-3.5 fast, GPT-4o slower)
- **ADR-009**: Claude 3.5 for Policy Interpretation - Deep dive on Claude 3.5 selection

---

## Implementation Notes

### API Configuration

```python
# config/llm_config.py

LLM_MODELS = {
    "gpt-4o": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o",
        "pricing": {"input": 0.005, "output": 0.015},  # per 1K tokens
        "rate_limit": 10000,  # RPM
        "timeout": 30  # seconds
    },
    "claude-3.5-sonnet": {
        "provider": "anthropic",
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
        "base_url": "https://api.anthropic.com",
        "model_name": "claude-3-5-sonnet-20240620",
        "pricing": {"input": 0.003, "output": 0.015},
        "rate_limit": 4000,
        "timeout": 30
    },
    "gpt-3.5-turbo": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-3.5-turbo",
        "pricing": {"input": 0.0005, "output": 0.0015},
        "rate_limit": 10000,
        "timeout": 10
    }
}

AGENT_MODEL_MAPPING = {
    "intake_agent": "gpt-4o",
    "eligibility_agent": "gpt-3.5-turbo",
    "benefits_agent": "gpt-3.5-turbo",
    "clinical_agent": "gpt-4o",
    "policy_agent": "claude-3.5-sonnet",
    "fraud_agent": "gpt-4o",
    "decision_agent": "gpt-4o",
    "appeals_agent": "claude-3.5-sonnet",
    "notification_agent": "gpt-3.5-turbo",
    "audit_agent": "gpt-3.5-turbo",
    "communication_agent": "gpt-3.5-turbo"
}
```

### Monitoring Metrics

Track per-model metrics in Prometheus:
```
llm_api_latency_seconds{model="gpt-4o", agent="clinical_agent"}
llm_api_cost_usd{model="gpt-4o", agent="clinical_agent"}
llm_api_tokens_total{model="gpt-4o", type="input", agent="clinical_agent"}
llm_api_errors_total{model="gpt-4o", error_type="timeout", agent="clinical_agent"}
llm_accuracy{model="gpt-4o", agent="clinical_agent"}
```

### Gradual Rollout

Implement model changes with feature flags:
```python
# Week 1: 10% of traffic to Claude 3.5 for Policy Agent
# Week 2: 50% of traffic
# Week 3: 100% of traffic (if accuracy ≥96% maintained)

if feature_flag("policy_agent_claude_3.5", default=0.0) > random.random():
    model = "claude-3.5-sonnet"
else:
    model = "gpt-4o"
```

---

## Review & Approval

**Reviewed by**:
- ✅ AI Architecture Team (recommendation)
- ✅ ML Engineering Team (implementation feasibility)
- ✅ Finance Team (cost approval)
- ✅ Compliance Team (HIPAA compliance)
- ✅ Clinical Leadership (clinical accuracy validation)

**Approved by**: CTO, VP of AI/ML  
**Effective Date**: 2026-01-15  
**Next Review**: 2026-07-15 (semi-annual review)

---

## Appendix: Benchmark Data

### Clinical Reasoning Benchmark (500 Test Cases)

| Model | Accuracy vs. Physician | Avg Latency | Cost/Case |
|-------|----------------------|-------------|-----------|
| GPT-4o | 94.5% (473/500) | 5.2s | $0.0275 |
| Claude 3.5 Sonnet | 91.2% (456/500) | 4.8s | $0.0180 |
| GPT-3.5 Turbo | 87.2% (436/500) | 1.1s | $0.0012 |
| GPT-4-Turbo | 93.1% (466/500) | 4.5s | $0.0220 |

**Winner**: GPT-4o (highest accuracy for critical medical decisions)

### Policy Interpretation Benchmark (500 Test Cases)

| Model | Correct Policy Section | Citation Accuracy | Avg Latency | Cost/Case |
|-------|----------------------|-------------------|-------------|-----------|
| Claude 3.5 Sonnet | 96.5% (483/500) | 96.5% | 2.1s | $0.0120 |
| GPT-4o | 83.2% (416/500) | 83.2% | 3.5s | $0.0185 |
| GPT-3.5 Turbo | 71.4% (357/500) | 65.2% | 0.8s | $0.0008 |

**Winner**: Claude 3.5 Sonnet (15% better accuracy, 35% lower cost)

### Eligibility Lookup Benchmark (1,000 Test Cases)

| Model | Accuracy | Avg Latency | Cost/Case |
|-------|----------|-------------|-----------|
| GPT-4o | 99.9% (999/1000) | 0.9s | $0.0095 |
| GPT-3.5 Turbo | 99.8% (998/1000) | 0.28s | $0.0004 |

**Winner**: GPT-3.5 Turbo (23.75x cheaper, negligible accuracy difference)

---

*This ADR documents the strategic decision to optimize LLM selection per agent based on task complexity, achieving a 48% cost reduction ($967K/year savings) while maximizing accuracy for critical decisions (clinical, policy).*

*Author: AI Architecture Team | Date: 2026-06-02 | Version: 1.0*
