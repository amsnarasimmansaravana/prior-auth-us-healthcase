---
title: 07 Decision Agent
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Decision Agent - Comprehensive Documentation

## Final Decision Aggregation & Routing Agent

**Version:** 2.4.0 | **Owner:** Decision Orchestration Team | **Status:** Production

## Overview

### Business Purpose
Aggregates inputs from all upstream agents (Intake, Eligibility, Benefits, Clinical, Policy, Fraud), synthesizes a final PA determination (Approve, Deny, Pend), and routes to appropriate downstream systems.

**Key Objectives:**
- Consolidate multi-agent outputs into single decision
- Apply business logic for final determination
- Route to HITL (Human-In-The-Loop) when needed
- Generate decision letters
- Maintain decision audit trail

**Business Impact:**
- Automation Rate: 78% (auto-adjudicated without human)
- Consistency: 99.2% decision consistency
- Turnaround Time: 3.5 minutes avg (auto) vs 2 hours (manual)
- HITL Rate: 22% (escalated to clinical reviewers)

### Technical Purpose
LangGraph supervisor pattern with state aggregation, confidence scoring, and intelligent HITL routing.

**Technologies:**
- Orchestrator: LangGraph (supervisor pattern)
- LLM: GPT-4o (decision synthesis, explanation generation)
- Database: PostgreSQL (decision_log table)
- Message Queue: Kafka (decision.complete topic)
- Workflow Engine: Temporal (durable workflows)

### Key Responsibilities

1. **Agent Output Aggregation**
   - Collect results from all upstream agents
   - Validate completeness
   - Handle timeout/failures
   - Maintain decision graph state

2. **Final Determination Logic**
   - Apply decision matrix
   - Resolve conflicting inputs
   - Calculate aggregate confidence score
   - Determine: APPROVE, DENY, PEND, NEEDS_REVIEW

3. **Human-In-The-Loop (HITL) Routing**
   - Route low-confidence decisions to clinical reviewers
   - Escalate policy conflicts
   - Flag fraud alerts for SIU
   - Assign to appropriate queue

4. **Decision Documentation**
   - Generate decision rationale
   - Cite supporting evidence
   - Create audit trail
   - Prepare decision letter content

5. **Downstream Notification**
   - Trigger notification workflows
   - Update case status
   - Publish to event streams
   - Integrate with claims system

---

## Business Rules

### Rule 1: Decision Matrix
```yaml
Rule ID: DEC-001
Description: Final determination logic based on agent outputs

Decision Table:
  Eligibility | Benefits | Clinical | Policy | Fraud | → Decision
  -----------|----------|----------|--------|-------|------------
  ELIGIBLE   | COVERED  | MET      | ALLOW  | PASS  | → APPROVE
  INELIGIBLE | *        | *        | *      | *     | → DENY (Eligibility)
  ELIGIBLE   | NOT_COV  | *        | *      | *     | → DENY (Not Covered)
  ELIGIBLE   | COVERED  | NOT_MET  | *      | *     | → DENY (Medical Necessity)
  ELIGIBLE   | COVERED  | MET      | DENY   | *     | → DENY (Policy)
  *          | *        | *        | *      | FAIL  | → DENY (Fraud/SIU Review)
  *          | *        | REVIEW   | *      | *     | → PEND (Clinical Review)
  
Priority (First blocking reason wins):
  1. Fraud → Immediate denial + SIU alert
  2. Eligibility → Deny (member not eligible)
  3. Benefits → Deny (service not covered)
  4. Clinical → Deny (not medically necessary)
  5. Policy → Deny (policy exclusion)
```

### Rule 2: Confidence-Based HITL Routing
```yaml
Rule ID: DEC-002
Description: Route to human review based on confidence scores

Confidence Calculation:
  aggregate_confidence = (
    eligibility.confidence * 0.30 +
    benefits.confidence * 0.20 +
    clinical.confidence * 0.40 +
    policy.confidence * 0.10
  )

HITL Thresholds:
  confidence >= 0.90 → AUTO_APPROVE/DENY
  0.70 <= confidence < 0.90 → SENIOR_REVIEWER
  confidence < 0.70 → MEDICAL_DIRECTOR

Additional HITL Triggers (override high confidence):
  - Clinical experimental procedure
  - Cost > $100,000
  - Member VIP status
  - Provider appeal
  - Regulatory flag
```

### Rule 3: Conflicting Agent Resolution
```yaml
Rule ID: DEC-003
Description: Handle conflicting agent outputs

Scenario 1: Clinical says APPROVE, Policy says DENY
  Resolution: Policy wins (regulatory compliance)
  Action: DENY + appeal rights notice

Scenario 2: Benefits says COVERED, Fraud says HIGH_RISK
  Resolution: Fraud wins (prevent improper payment)
  Action: PEND for SIU investigation

Scenario 3: Multiple "REQUIRES_REVIEW" flags
  Resolution: Route to highest-level reviewer
  Action: PEND + assign to Medical Director queue

Conflict Priority:
  1. Fraud (safety/compliance)
  2. Policy (regulatory)
  3. Eligibility (contractual)
  4. Clinical (medical necessity)
  5. Benefits (coverage)
```

### Rule 4: Urgency-Based SLA Enforcement
```yaml
Rule ID: DEC-004
Description: Enforce decision timelines based on urgency

Urgency Levels:
  EMERGENT: 1 hour
  URGENT: 24 hours
  STANDARD: 14 days (CMS requirement for MA)
  RETROSPECTIVE: 30 days

Auto-Approve on SLA Breach:
  IF elapsed_time > sla_deadline:
    decision = "APPROVED_BY_DEFAULT"
    reason = "SLA breach (CMS timely filing)"
    notify_compliance_team = True

Grace Period:
  - 85% of SLA → Escalate to supervisor
  - 95% of SLA → Auto-approve trigger armed
```

### Rule 5: Decision Reversibility
```yaml
Rule ID: DEC-005
Description: Handle decision reversals and amendments

Reversible Scenarios:
  - New clinical information submitted
  - Eligibility corrected retroactively
  - Policy interpretation clarified
  - Fraud investigation exonerated provider

Process:
  1. Original decision marked as "REVERSED"
  2. Create new decision with reversal_reason
  3. Notify all affected parties
  4. Adjust claims if service already rendered
  5. Document in audit trail

Audit Trail:
  - Original decision timestamp
  - Reversal timestamp
  - Reason for reversal
  - Approving authority
  - Member/provider notifications sent
```

---

## Technical Architecture

### LangGraph Supervisor Pattern

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class PADecisionState(TypedDict):
    """Shared state across all agents"""
    case_id: str
    member_id: str
    
    # Agent outputs
    intake_result: dict
    eligibility_result: dict
    benefits_result: dict
    clinical_result: dict
    policy_result: dict
    fraud_result: dict
    
    # Aggregated decision
    final_decision: str  # APPROVE, DENY, PEND
    decision_rationale: str
    confidence_score: float
    hitl_required: bool
    
    # Metadata
    processing_start: str
    processing_end: str
    agents_completed: Annotated[list, operator.add]
    
# Define Decision Graph
decision_graph = StateGraph(PADecisionState)

# Add agent nodes
decision_graph.add_node("intake_agent", run_intake_agent)
decision_graph.add_node("eligibility_agent", run_eligibility_agent)
decision_graph.add_node("benefits_agent", run_benefits_agent)
decision_graph.add_node("clinical_agent", run_clinical_agent)
decision_graph.add_node("policy_agent", run_policy_agent)
decision_graph.add_node("fraud_agent", run_fraud_agent)
decision_graph.add_node("decision_aggregator", aggregate_decision)

# Define execution flow
decision_graph.set_entry_point("intake_agent")

decision_graph.add_edge("intake_agent", "eligibility_agent")
decision_graph.add_conditional_edges(
    "eligibility_agent",
    lambda state: "benefits_agent" if state["eligibility_result"]["status"] == "ELIGIBLE" else "decision_aggregator"
)
decision_graph.add_edge("benefits_agent", "clinical_agent")
decision_graph.add_edge("clinical_agent", "policy_agent")
decision_graph.add_edge("policy_agent", "fraud_agent")
decision_graph.add_edge("fraud_agent", "decision_aggregator")

decision_graph.add_conditional_edges(
    "decision_aggregator",
    lambda state: "hitl_routing" if state["hitl_required"] else END
)

app = decision_graph.compile()

def aggregate_decision(state: PADecisionState) -> PADecisionState:
    """Final decision aggregation logic"""
    
    # Extract agent results
    eligibility = state["eligibility_result"]["status"]
    benefits = state["benefits_result"]["coverage_status"]
    clinical = state["clinical_result"]["determination"]
    policy = state["policy_result"]["policy_decision"]
    fraud = state["fraud_result"]["risk_level"]
    
    # Apply decision matrix
    if fraud == "HIGH":
        decision = "DENY"
        rationale = f"High fraud risk detected: {state['fraud_result']['fraud_indicators']}"
        hitl = True  # SIU review required
        
    elif eligibility == "INELIGIBLE":
        decision = "DENY"
        rationale = "Member not eligible for coverage on service date"
        hitl = False
        
    elif benefits == "NOT_COVERED":
        decision = "DENY"
        rationale = "Service not covered under member's benefit plan"
        hitl = False
        
    elif clinical == "DENY":
        decision = "DENY"
        rationale = state["clinical_result"]["detailed_rationale"]
        hitl = state["clinical_result"]["requires_human_review"]
        
    elif policy == "DENY":
        decision = "DENY"
        rationale = "Denied per policy exclusion"
        hitl = False
        
    elif clinical == "APPROVE" and policy == "APPROVE":
        decision = "APPROVE"
        rationale = "Medical necessity met and all eligibility/coverage checks passed"
        hitl = False
        
    else:
        decision = "PEND"
        rationale = "Requires additional review"
        hitl = True
    
    # Calculate aggregate confidence
    confidence = calculate_aggregate_confidence(state)
    
    # Override HITL if low confidence
    if confidence < 0.70:
        hitl = True
    
    state["final_decision"] = decision
    state["decision_rationale"] = rationale
    state["confidence_score"] = confidence
    state["hitl_required"] = hitl
    
    return state

def calculate_aggregate_confidence(state: PADecisionState) -> float:
    """Weighted average of agent confidence scores"""
    
    weights = {
        "eligibility": 0.30,
        "benefits": 0.20,
        "clinical": 0.40,
        "policy": 0.10
    }
    
    confidence = (
        state["eligibility_result"]["confidence"] * weights["eligibility"] +
        state["benefits_result"]["confidence"] * weights["benefits"] +
        state["clinical_result"]["confidence"] * weights["clinical"] +
        state["policy_result"]["confidence"] * weights["policy"]
    )
    
    return round(confidence, 2)
```

---

## Input/Output Specifications

### Input (Aggregated Agent Outputs)
```json
{
  "case_id": "PA-2026-001234",
  "intake_result": {...},
  "eligibility_result": {"status": "ELIGIBLE", "confidence": 1.0},
  "benefits_result": {"coverage_status": "COVERED", "confidence": 0.98},
  "clinical_result": {"determination": "APPROVE", "confidence": 0.96},
  "policy_result": {"policy_decision": "APPROVE", "confidence": 1.0},
  "fraud_result": {"risk_level": "LOW", "fraud_risk_score": 0.15}
}
```

### Output
```json
{
  "case_id": "PA-2026-001234",
  "final_decision": "APPROVE",
  "decision_rationale": "Medical necessity met per MCG A-0527. Failed conservative therapy documented. All eligibility/coverage checks passed.",
  "confidence_score": 0.96,
  "decision_timestamp": "2026-06-01T09:08:30Z",
  "processing_time_total_ms": 3500,
  "hitl_required": false,
  "approval_details": {
    "authorization_number": "AUTH-2026-987654",
    "approved_procedures": ["27447"],
    "approved_diagnoses": ["M17.11"],
    "valid_from": "2026-07-01",
    "valid_until": "2026-12-31",
    "number_of_services": 1,
    "estimated_cost": 25000.00,
    "member_cost_sharing": 2550.00
  },
  "agent_summary": {
    "eligibility": "PASS",
    "benefits": "PASS",
    "clinical": "PASS",
    "policy": "PASS",
    "fraud": "PASS"
  },
  "next_steps": [
    "Notification Agent → Send approval letter to member",
    "Notification Agent → Send approval to provider",
    "Claims System → Create authorization record",
    "Audit Agent → Log decision in compliance database"
  ]
}
```

---

## Processing Flow

1. Receive all agent outputs
2. Validate completeness (all agents responded)
3. Apply decision matrix
4. Calculate aggregate confidence
5. Determine HITL routing need
6. Generate decision rationale
7. Create authorization record (if approved)
8. Publish to Kafka (decision.complete topic)
9. Trigger downstream workflows
10. Log to audit trail

**Performance:**
- Total processing time: 3.5 minutes avg
- Automation rate: 78%
- Decision consistency: 99.2%

---

## Integration Points

- **Upstream:** All 6 agents (Intake, Eligibility, Benefits, Clinical, Policy, Fraud)
- **Downstream:** Notification Agent, Audit Agent, Claims System
- **HITL Platform:** Clinical Reviewer UI, SIU Portal
- **Event Stream:** Kafka (decision.complete)
- **Workflow:** Temporal (durable execution)

---

## Monitoring

- Automation rate: Target >75%, Current 78%
- HITL rate: Target <25%, Current 22%
- Decision accuracy: 99.2%
- SLA compliance: 98.5%
- Average processing time: 3.5 min

---

*Decision Agent v2.4.0 - Orchestrating 50,000 PA/Day*
