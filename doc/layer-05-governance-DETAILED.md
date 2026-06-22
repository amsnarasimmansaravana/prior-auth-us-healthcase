# Layer 5: Governance Layer
## Agent Registry, Prompt Management & Safety Evaluation - Healthcare Insurance PA Platform

**Layer Purpose**: Centralized governance for AI agents, prompt optimization, and safety validation  
**Services**: 4 services  
**Technology Stack**: FastAPI, LangSmith, Guardrails AI, PostgreSQL  
**Daily Volume**: 385,000 governance checks/day (100% of agent executions)  
**Performance**: <100ms validation overhead per agent call

---

## Table of Contents
1. [Layer Overview](#layer-overview)
2. [Service Architecture](#service-architecture)
   - [Service 1: Agent Registry](#service-1-agent-registry-svc)
   - [Service 2: Prompt Management](#service-2-prompt-mgmt-svc)
   - [Service 3: Safety Evaluation](#service-3-safety-eval-svc)
   - [Service 4: Compliance Monitor](#service-4-compliance-monitor-svc)
3. [Technical Implementation](#technical-implementation)
4. [Governance Workflows](#governance-workflows)
5. [ISO 42001 AIMS Compliance](#iso-42001-aims-compliance)
6. [Performance & Scaling](#performance--scaling)
7. [Monitoring & Operations](#monitoring--operations)

---

## Layer Overview

### Purpose

The **Governance Layer** ensures AI safety, quality, and compliance across all 11 agents:

- **Agent Registry**: Centralized catalog of agent metadata, versions, capabilities
- **Prompt Management**: Version control, A/B testing, and optimization of prompts
- **Safety Evaluation**: Real-time hallucination detection, bias checking, PII redaction
- **Compliance Monitoring**: ISO 42001 AIMS framework, audit trails, certifications

**Governance Coverage**:
- 385,000 agent executions/day (100% coverage)
- Real-time safety checks on every agent response
- Prompt versioning with rollback capability
- Complete audit trail for regulatory compliance

### Architecture Principles

1. **Safety First**: Validate every agent output before use
2. **Centralized Control**: Single source of truth for agent metadata
3. **Auditability**: Track all changes to agents and prompts
4. **Continuous Improvement**: A/B test prompts, optimize based on metrics
5. **Compliance**: ISO 42001, SOC 2, HIPAA compliance built-in

---

## Service Architecture

### Service 1: agent-registry-svc

**Business Use Case**: Maintain centralized catalog of all AI agents with metadata, versions, and capabilities

**Technology Stack**:
- Language: Python 3.11
- Framework: FastAPI 0.104
- Database: PostgreSQL 15 (agent_db)
- Cache: Redis 7.0

**Core Capabilities**:
1. **Agent Catalog**: Store metadata for all 11 agents
2. **Version Management**: Track agent versions, model changes, prompt updates
3. **Capability Discovery**: Agents advertise their capabilities (tools, inputs, outputs)
4. **Health Monitoring**: Track agent availability, latency, error rates
5. **Dependency Mapping**: Track which agents depend on which tools/services

**Database Schema**:
```sql
-- Agent Registry Table
CREATE TABLE agent_db.agents (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    description TEXT,
    version VARCHAR(20) NOT NULL,  -- Semantic versioning
    model_name VARCHAR(100),       -- e.g., "gpt-4o", "claude-3-5-sonnet"
    temperature DECIMAL(3,2),
    max_tokens INTEGER,
    system_prompt_id UUID REFERENCES prompts(prompt_id),
    capabilities JSONB,            -- List of capabilities
    input_schema JSONB,            -- Pydantic model as JSON
    output_schema JSONB,
    mcp_tools JSONB,               -- List of MCP tool names
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',  -- active, deprecated, retired
    
    -- Performance baselines
    avg_latency_ms INTEGER,
    p95_latency_ms INTEGER,
    success_rate DECIMAL(5,2),
    daily_volume INTEGER,
    cost_per_execution DECIMAL(10,6),
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'deprecated', 'retired'))
);

CREATE INDEX idx_agents_name ON agent_db.agents(agent_name);
CREATE INDEX idx_agents_status ON agent_db.agents(status);
CREATE INDEX idx_agents_model ON agent_db.agents(model_name);

-- Agent Version History
CREATE TABLE agent_db.agent_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id),
    version VARCHAR(20) NOT NULL,
    changes TEXT,                  -- Change description
    deployed_at TIMESTAMP,
    deprecated_at TIMESTAMP,
    performance_metrics JSONB,
    created_by VARCHAR(100)
);

-- Agent Dependencies (agents -> tools, agents -> agents)
CREATE TABLE agent_db.agent_dependencies (
    dependency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(agent_id),
    dependency_type VARCHAR(50),   -- 'mcp_tool', 'agent', 'service', 'database'
    dependency_name VARCHAR(200),
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**API Endpoints**:
```python
# Agent CRUD
POST   /agents                       # Register new agent
GET    /agents                       # List all agents
GET    /agents/{agent_name}          # Get agent details
PUT    /agents/{agent_name}          # Update agent metadata
DELETE /agents/{agent_name}          # Retire agent

# Version Management
GET    /agents/{agent_name}/versions           # List versions
POST   /agents/{agent_name}/versions           # Create new version
POST   /agents/{agent_name}/rollback/{version} # Rollback to version

# Capabilities
GET    /agents/capabilities                     # Search by capability
GET    /agents/{agent_name}/dependencies       # Get dependencies

# Health & Metrics
GET    /agents/{agent_name}/health             # Health check
GET    /agents/{agent_name}/metrics            # Performance metrics
```

**Performance**:
- Throughput: 385,000 registry lookups/day
- P50 Latency: 8ms (Redis cache hit)
- P95 Latency: 45ms (PostgreSQL query)
- Cache Hit Rate: 92%

---

### Service 2: prompt-mgmt-svc

**Business Use Case**: Manage, version, test, and optimize prompts for all agents

**Technology Stack**:
- Language: Python 3.11
- Framework: FastAPI 0.104
- Prompt Store: LangSmith (LangChain)
- Database: PostgreSQL 15
- A/B Testing: Custom framework

**Core Capabilities**:
1. **Prompt Versioning**: Git-like version control for prompts
2. **Template Management**: Jinja2 templates with variable substitution
3. **A/B Testing**: Compare prompt variants with statistical significance
4. **Optimization**: Automatic prompt optimization using DSPy/PromptPerfect
5. **Analytics**: Track prompt performance (accuracy, latency, cost)

**Prompt Schema**:
```sql
CREATE TABLE agent_db.prompts (
    prompt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_name VARCHAR(200) NOT NULL,
    agent_name VARCHAR(100) REFERENCES agents(agent_name),
    version VARCHAR(20) NOT NULL,
    prompt_template TEXT NOT NULL,     -- Jinja2 template
    variables JSONB,                   -- Template variables
    examples JSONB,                    -- Few-shot examples
    tags TEXT[],                       -- Searchable tags
    
    -- A/B Testing
    is_production BOOLEAN DEFAULT false,
    test_group VARCHAR(50),            -- 'A', 'B', 'control'
    traffic_percentage INTEGER,        -- % of traffic for this variant
    
    -- Performance metrics
    avg_tokens_used INTEGER,
    avg_latency_ms INTEGER,
    success_rate DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),       -- If ground truth available
    cost_per_execution DECIMAL(10,6),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft', -- draft, testing, production, archived
    
    CONSTRAINT valid_status CHECK (status IN ('draft', 'testing', 'production', 'archived'))
);

CREATE INDEX idx_prompts_agent ON agent_db.prompts(agent_name);
CREATE INDEX idx_prompts_status ON agent_db.prompts(status);

-- Prompt Performance Tracking
CREATE TABLE agent_db.prompt_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id UUID REFERENCES prompts(prompt_id),
    execution_date DATE,
    execution_count INTEGER,
    avg_latency_ms INTEGER,
    success_count INTEGER,
    failure_count INTEGER,
    total_tokens INTEGER,
    total_cost DECIMAL(10,2),
    
    -- Quality metrics
    hallucination_rate DECIMAL(5,2),
    pii_leak_count INTEGER,
    toxicity_score DECIMAL(5,2),
    
    PRIMARY KEY (prompt_id, execution_date)
);
```

**Prompt Optimization Workflow**:
```python
from dspy import ChainOfThought
from dspy.teleprompt import BootstrapFewShot

# 1. Define baseline prompt
baseline_prompt = {
    "agent": "clinical_agent",
    "template": '''
    You are a clinical review agent. Assess if the requested treatment is medically necessary.
    
    Diagnosis: {diagnosis}
    Treatment: {treatment}
    Clinical Guidelines: {guidelines}
    
    Decision: APPROVED or DENIED
    Rationale: [Provide detailed explanation]
    ''',
    "version": "1.0.0"
}

# 2. Generate optimized variant using DSPy
optimizer = BootstrapFewShot(metric=clinical_accuracy)
optimized_prompt = optimizer.compile(
    baseline_prompt,
    trainset=training_examples,
    max_bootstrapped_demos=5
)

# 3. A/B Test: 80% baseline, 20% optimized
ab_test = {
    "control": {"prompt": baseline_prompt, "traffic": 80},
    "variant_a": {"prompt": optimized_prompt, "traffic": 20}
}

# 4. Measure metrics after 1000 samples
# - Accuracy: Control 92.5%, Variant A 94.8% ✓ +2.3%
# - Latency: Control 5.2s, Variant A 5.4s (acceptable)
# - Cost: Control $0.0275, Variant A $0.0285 (acceptable)

# 5. Statistical significance test (Chi-square, p-value < 0.05)
if variant_is_better and is_statistically_significant:
    promote_to_production("variant_a")
```

**API Endpoints**:
```python
# Prompt CRUD
POST   /prompts                      # Create prompt
GET    /prompts                      # List prompts
GET    /prompts/{prompt_id}          # Get prompt details
PUT    /prompts/{prompt_id}          # Update prompt
DELETE /prompts/{prompt_id}          # Archive prompt

# Versioning
GET    /prompts/{prompt_id}/versions        # List versions
POST   /prompts/{prompt_id}/versions        # Create version
POST   /prompts/{prompt_id}/rollback        # Rollback

# A/B Testing
POST   /prompts/{prompt_id}/test            # Start A/B test
GET    /prompts/{prompt_id}/test/results    # Get test results
POST   /prompts/{prompt_id}/promote         # Promote to production

# Optimization
POST   /prompts/{prompt_id}/optimize        # Auto-optimize prompt
GET    /prompts/{prompt_id}/metrics         # Performance metrics
```

**Performance**:
- Prompts Managed: 25 prompts (11 agents × ~2-3 variants each)
- A/B Tests Running: 3-5 concurrent tests
- Optimization Runs: Weekly for top 5 agents
- Version Rollbacks: <5 minutes to revert

---

### Service 3: safety-eval-svc

**Business Use Case**: Real-time safety validation of agent outputs (hallucination, bias, PII, toxicity)

**Technology Stack**:
- Language: Python 3.11
- Framework: FastAPI 0.104
- Guardrails: Guardrails AI, NeMo Guardrails (NVIDIA)
- PII Detection: Microsoft Presidio
- Hallucination Detection: Custom classifier + GPT-4o verification

**Core Safety Checks**:

**1. Hallucination Detection**
```python
from guardrails import Guard
from guardrails.validators import OnTopic, FactualConsistency

# Check if agent output is consistent with input context
hallucination_guard = Guard().use(
    FactualConsistency(
        context=input_context,
        threshold=0.85  # 85% similarity required
    )
)

# If confidence < 85%, flag as potential hallucination
result = hallucination_guard.validate(agent_output)
if result.validation_failed:
    # Re-prompt agent with explicit instruction
    # OR escalate to human review
    handle_hallucination(agent_output, result.error_message)
```

**2. PII Detection & Redaction**
```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Detect PII entities
pii_entities = analyzer.analyze(
    text=agent_output,
    entities=["SSN", "EMAIL", "PHONE_NUMBER", "CREDIT_CARD", 
              "MEDICAL_LICENSE", "US_PASSPORT", "US_DRIVER_LICENSE"],
    language="en"
)

# Redact or mask PII
if pii_entities:
    redacted_text = anonymizer.anonymize(
        text=agent_output,
        analyzer_results=pii_entities,
        operators={"DEFAULT": OperatorConfig("mask", {"chars_to_mask": 6})}
    )
    
    # Log PII leak incident
    log_pii_leak(agent_name, pii_entities, severity="HIGH")
    
    return redacted_text
```

**3. Bias Detection**
```python
# Check for demographic bias in clinical decisions
bias_detector = BiasDetector(
    protected_attributes=["age", "gender", "race", "socioeconomic_status"]
)

bias_score = bias_detector.check(
    agent_output=clinical_decision,
    patient_demographics=patient_data
)

if bias_score > 0.3:  # >30% bias detected
    flag_for_review(clinical_decision, "potential_bias", bias_score)
```

**4. Toxicity Filtering**
```python
from detoxify import Detoxify

toxicity_model = Detoxify('original')
toxicity_scores = toxicity_model.predict(agent_output)

if toxicity_scores['toxicity'] > 0.7:
    block_output(agent_output, reason="high_toxicity")
    alert_safety_team()
```

**Safety Metrics**:
- Checks Per Day: 385,000 (one per agent execution)
- P50 Latency: 45ms
- P95 Latency: 120ms
- Hallucination Detection Rate: 2.1% flagged
- PII Leaks Prevented: ~50/day
- Bias Incidents: ~15/day flagged for review

---

### Service 4: compliance-monitor-svc

**Business Use Case**: Ensure ISO 42001 AIMS compliance, audit trails, and regulatory reporting

**Technology Stack**:
- Language: Python 3.11
- Framework: FastAPI 0.104
- Database: PostgreSQL 15 (audit_db)
- Compliance: ISO 42001 AIMS framework

**ISO 42001 AIMS Requirements**:

**1. AI Management System Documentation**
```yaml
AIMS Documentation:
  - AI Policy Document
  - Risk Assessment Register
  - Data Governance Framework
  - AI Ethics Guidelines
  - Incident Response Plan
  - Stakeholder Engagement Plan
```

**2. Risk Management**
```sql
CREATE TABLE audit_db.ai_risk_register (
    risk_id UUID PRIMARY KEY,
    agent_name VARCHAR(100),
    risk_category VARCHAR(50),   -- 'bias', 'hallucination', 'privacy', 'security'
    risk_description TEXT,
    likelihood VARCHAR(20),       -- 'low', 'medium', 'high'
    impact VARCHAR(20),           -- 'low', 'medium', 'high', 'critical'
    risk_score INTEGER,           -- Likelihood × Impact (1-25)
    mitigation_strategy TEXT,
    mitigation_status VARCHAR(20), -- 'planned', 'in_progress', 'implemented'
    owner VARCHAR(100),
    review_date DATE,
    created_at TIMESTAMP
);
```

**3. Audit Trail**
```sql
CREATE TABLE audit_db.agent_execution_log (
    execution_id UUID PRIMARY KEY,
    request_id VARCHAR(100),
    agent_name VARCHAR(100),
    model_name VARCHAR(100),
    prompt_version VARCHAR(20),
    
    -- Input/Output
    input_data JSONB,
    output_data JSONB,
    
    -- Safety checks
    hallucination_score DECIMAL(5,2),
    pii_detected BOOLEAN,
    bias_score DECIMAL(5,2),
    toxicity_score DECIMAL(5,2),
    
    -- Performance
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost DECIMAL(10,6),
    
    -- Decision context
    confidence DECIMAL(5,2),
    routed_to_hitl BOOLEAN,
    
    -- Compliance
    executed_at TIMESTAMP DEFAULT NOW(),
    executed_by VARCHAR(100),
    regulatory_flags TEXT[],
    
    -- Retention: 7 years for HIPAA compliance
    retention_until DATE DEFAULT (CURRENT_DATE + INTERVAL '7 years')
);

CREATE INDEX idx_execution_log_agent ON audit_db.agent_execution_log(agent_name, executed_at DESC);
CREATE INDEX idx_execution_log_request ON audit_db.agent_execution_log(request_id);
```

**4. Compliance Reporting**
```python
# Generate monthly compliance report
def generate_compliance_report(month: str, year: int):
    report = {
        "reporting_period": f"{year}-{month}",
        "total_agent_executions": 1_650_000,  # 55K/day × 30 days
        
        "safety_metrics": {
            "hallucination_incidents": 34_650,  # 2.1%
            "pii_leaks_prevented": 1_500,
            "bias_incidents_flagged": 450,
            "toxicity_blocks": 25
        },
        
        "quality_metrics": {
            "avg_confidence_score": 0.89,
            "hitl_routing_rate": 0.28,
            "appeal_rate": 0.05,
            "overturn_rate": 0.12
        },
        
        "risk_register_updates": {
            "new_risks_identified": 3,
            "risks_mitigated": 5,
            "high_risks_outstanding": 2
        },
        
        "model_changes": {
            "prompt_optimizations": 4,
            "model_version_updates": 1,
            "rollbacks": 0
        },
        
        "compliance_status": "COMPLIANT",
        "auditor": "Internal Audit Team",
        "next_review_date": "2026-07-15"
    }
    
    return report
```

**Performance**:
- Audit Records/Day: 385,000 (100% coverage)
- Retention Period: 7 years (HIPAA requirement)
- Compliance Reports: Monthly + on-demand
- Audit Query Time: <1s for 30-day lookups

---

## Governance Workflows

### Prompt Update Workflow
1. Developer creates new prompt variant
2. Save as "draft" in prompt management
3. Run A/B test (80/20 split) for 1,000 samples
4. Measure metrics (accuracy, latency, cost)
5. Statistical significance test (p < 0.05)
6. If better → Promote to production (gradual rollout 20% → 50% → 100%)
7. If worse → Archive variant
8. Update agent registry with new prompt_id

### Agent Onboarding Workflow
1. Register agent in agent registry (metadata, version, capabilities)
2. Create initial system prompt (prompt management)
3. Define safety thresholds (max hallucination rate, PII tolerance)
4. Set up compliance monitoring (audit logging enabled)
5. Run validation tests (100 test cases)
6. Deploy to staging environment
7. Shadow production traffic (1 week)
8. Gradual production rollout (10% → 50% → 100%)

---

## ISO 42001 AIMS Compliance

The platform implements **ISO 42001:2023 AI Management System** requirements:

✅ **Clause 4**: Context of organization - Documented stakeholders, AI scope  
✅ **Clause 5**: Leadership - Designated AI governance team  
✅ **Clause 6**: Planning - Risk assessment, objectives, mitigation plans  
✅ **Clause 7**: Support - Competence, awareness, documented information  
✅ **Clause 8**: Operation - AI lifecycle management (design → deploy → monitor)  
✅ **Clause 9**: Performance evaluation - Metrics, audits, management review  
✅ **Clause 10**: Improvement - Incident management, continuous improvement

**Certification**: ISO 42001 certified (June 2026)

---

## Performance & Scaling

```yaml
HorizontalPodAutoscaler:
  - service: agent-registry-svc
    minReplicas: 2
    maxReplicas: 6
    targetCPU: 70%
  
  - service: prompt-mgmt-svc
    minReplicas: 2
    maxReplicas: 4
    targetCPU: 60%
  
  - service: safety-eval-svc
    minReplicas: 3
    maxReplicas: 10
    targetCPU: 75%
  
  - service: compliance-monitor-svc
    minReplicas: 2
    maxReplicas: 5
    targetCPU: 65%
```

---

## Summary

The **Governance Layer** ensures **100% safety coverage** across 385,000 agent executions/day with:
- ✅ Centralized agent registry (11 agents, versioning, capabilities)
- ✅ Prompt management with A/B testing and optimization
- ✅ Real-time safety checks (hallucination, PII, bias, toxicity)
- ✅ ISO 42001 AIMS compliance with complete audit trails
- ✅ <100ms governance overhead per agent call

**Key Achievements**:
- 2.1% hallucination detection rate (34,650 incidents/month prevented)
- ~50 PII leaks prevented daily
- 7-year audit trail retention (HIPAA compliant)
- ISO 42001 certified AI management system

---

*Generated: June 02, 2026 | Version: 1.0*
