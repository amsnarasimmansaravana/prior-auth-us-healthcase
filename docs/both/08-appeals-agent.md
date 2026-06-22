# Appeals Agent - Comprehensive Documentation

## Member & Provider Appeals Processing Agent

**Version:** 2.0.0 | **Owner:** Appeals & Grievances Team | **Status:** Production

## Overview

### Business Purpose
Processes member and provider appeals of denied PA requests, coordinates Internal Review, External Review (IRO), and ensures regulatory compliance with appeal timelines and processes.

**Key Objectives:**
- Process appeals within regulatory timelines
- Coordinate Independent Review Organization (IRO)
- Track appeal status through lifecycle
- Ensure compliance with CMS/state regulations
- Provide transparent appeal process

**Business Impact:**
- Overturn Rate: 18% (appeals that reverse original denial)
- IRO Agreement Rate: 92% (IRO upholds internal decision)
- Compliance: 100% regulatory timeline adherence
- Member Satisfaction: 4.2/5.0 for appeal process transparency

### Technical Purpose
Workflow orchestration for multi-stage appeal process with document management, deadline tracking, and IRO integration.

**Technologies:**
- Workflow Engine: Temporal (durable workflows with SLA enforcement)
- LLM: GPT-4o (appeal letter analysis, decision drafting)
- Document Management: Azure Blob Storage
- Database: PostgreSQL (appeals tracking)
- Notification: Automated appeal status updates

### Key Responsibilities

1. **Appeal Intake & Classification**
   - Receive appeal requests (member, provider, authorized rep)
   - Validate timeliness (180 days for standard, 60 days for expedited)
   - Classify appeal type (Internal, External, Grievance)
   - Extract appeal rationale

2. **Internal Review (Level 1)**
   - Assign to different clinical reviewer (not original decision maker)
   - Full de novo review (fresh look at all evidence)
   - Consider new clinical information
   - Issue decision within timeline (30 days standard, 72 hours expedited)

3. **External Review / IRO Coordination**
   - Submit to Independent Review Organization
   - Provide all case documentation
   - Track IRO review timeline (45 days)
   - Accept IRO decision as binding

4. **Appeal Decision Communication**
   - Generate appeal decision letters
   - Explain decision rationale
   - Provide next-level appeal rights
   - Send to member and provider

5. **Regulatory Compliance**
   - Enforce appeal timelines (CMS, state mandates)
   - Maintain appeal logs
   - Report to regulators
   - Support appeals audits

---

## Business Rules

### Rule 1: Appeal Timeliness
```yaml
Rule ID: APP-001
Description: Validate appeal filed within regulatory timeframe

Timeframes:
  Standard Appeal: 180 days from denial notice
  Expedited Appeal: 60 days from denial notice
  Medicare Advantage: 60 days
  
Validation:
  denial_date = original_denial_timestamp
  appeal_date = appeal_received_timestamp
  days_elapsed = (appeal_date - denial_date).days
  
  IF days_elapsed > 180:
    status = "REJECTED_UNTIMELY"
    reason = "Appeal filed beyond 180-day deadline"
    send_untimely_notice = True
  ELSE:
    status = "ACCEPTED"
    proceed_to_review = True
```

### Rule 2: Appeal Review Timelines
```yaml
Rule ID: APP-002
Description: Process appeal within regulatory deadlines

CMS Medicare Advantage Timelines:
  Standard Appeal: 30 calendar days
  Expedited Appeal: 72 hours
  
State Timelines (varies):
  California: 30 days standard, 3 days expedited
  New York: 30 days standard, 72 hours expedited

Expedited Criteria:
  - Provider certifies delay could seriously jeopardize life/health
  - Member requests expedited AND clinical urgency present
  
Auto-Approve on Breach:
  IF elapsed_time > deadline:
    decision = "APPROVED_BY_DEFAULT"
    reason = "Regulatory timeline exceeded"
    notify_compliance = True
```

### Rule 3: Different Reviewer Requirement
```yaml
Rule ID: APP-003
Description: Appeal must be reviewed by different clinical reviewer

Validation:
  original_reviewer = get_original_decision_reviewer(case_id)
  appeal_reviewer = get_appeal_reviewer_assignment()
  
  IF appeal_reviewer == original_reviewer:
    status = "ERROR_SAME_REVIEWER"
    reassign = True
    select_different_reviewer = True
    
Peer-to-Peer Requirement:
  - Same/similar specialty as ordering provider
  - Board-certified in relevant specialty
  - Not involved in original decision
```

### Rule 4: New Evidence Consideration
```yaml
Rule ID: APP-004
Description: Must consider new clinical information submitted with appeal

New Evidence Types:
  - Additional diagnostic test results
  - Specialist consultation notes
  - Peer-reviewed literature supporting treatment
  - Updated clinical guidelines
  - Patient progress notes

Processing:
  IF new_clinical_evidence_submitted:
    attach_to_case_record = True
    send_to_clinical_agent_for_reanalysis = True
    update_medical_necessity_determination = True
    
De Novo Review:
  - Review ALL evidence (original + new)
  - Fresh clinical analysis (not just review new evidence)
  - May overturn, uphold, or partially approve
```

### Rule 5: IRO External Review Triggers
```yaml
Rule ID: APP-005
Description: Route to Independent Review Organization when required

IRO Triggers:
  - Member requests external review after internal denial
  - Experimental/investigational determination disputed
  - Medical necessity disagreement
  - Regulatory requirement (MA, state mandates)

IRO Process:
  1. Submit all case documentation to IRO
  2. IRO conducts independent clinical review
  3. IRO issues binding decision (45 days)
  4. Health plan must accept IRO decision
  
IRO Selection:
  - State-approved IRO list
  - Specialty-matched reviewers
  - No financial interest in outcome
  - Certified/accredited organizations
```

---

## Technical Architecture

### Temporal Workflow (Durable Appeal Process)

```python
from temporalio import workflow, activity
from datetime import timedelta

@workflow.defn
class AppealWorkflow:
    """Durable appeal workflow with SLA enforcement"""
    
    @workflow.run
    async def run(self, appeal_request: AppealRequest) -> AppealDecision:
        """Execute appeal process with automatic deadline enforcement"""
        
        # Step 1: Validate appeal timeliness
        validation = await workflow.execute_activity(
            validate_appeal_timeliness,
            appeal_request,
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        if not validation.is_timely:
            return AppealDecision(
                status="REJECTED_UNTIMELY",
                reason="Appeal filed beyond 180-day deadline"
            )
        
        # Step 2: Classify appeal urgency
        urgency = await workflow.execute_activity(
            classify_appeal_urgency,
            appeal_request,
            start_to_close_timeout=timedelta(seconds=10)
        )
        
        # Set deadline based on urgency
        if urgency == "EXPEDITED":
            deadline = timedelta(hours=72)
        else:
            deadline = timedelta(days=30)
        
        # Step 3: Assign to clinical reviewer (different from original)
        reviewer = await workflow.execute_activity(
            assign_appeal_reviewer,
            appeal_request,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 4: Conduct clinical review with deadline
        try:
            review_result = await workflow.execute_activity(
                conduct_appeal_review,
                appeal_request,
                schedule_to_close_timeout=deadline
            )
        except TimeoutError:
            # Auto-approve if deadline exceeded
            return AppealDecision(
                status="APPROVED_BY_DEFAULT",
                reason="Regulatory timeline exceeded",
                compliance_alert=True
            )
        
        # Step 5: Generate appeal decision letter
        decision_letter = await workflow.execute_activity(
            generate_appeal_decision_letter,
            review_result,
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        # Step 6: Send notifications
        await workflow.execute_activity(
            send_appeal_decision_notifications,
            decision_letter,
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        # Step 7: Check if IRO external review requested
        if review_result.decision == "UPHOLD_DENIAL" and appeal_request.iro_requested:
            iro_result = await workflow.execute_activity(
                submit_to_iro,
                appeal_request,
                schedule_to_close_timeout=timedelta(days=45)
            )
            return iro_result
        
        return review_result

@activity.defn
async def conduct_appeal_review(appeal_request: AppealRequest) -> AppealDecision:
    """Conduct de novo clinical review of appeal"""
    
    # Fetch original case
    original_case = await fetch_original_case(appeal_request.original_case_id)
    
    # Fetch new evidence submitted with appeal
    new_evidence = await fetch_appeal_evidence(appeal_request.appeal_id)
    
    # Re-run Clinical Agent with ALL evidence (original + new)
    clinical_reanalysis = await clinical_agent.analyze(
        case_data=original_case,
        additional_evidence=new_evidence,
        review_type="DE_NOVO_APPEAL"
    )
    
    # Generate appeal decision
    if clinical_reanalysis.determination == "APPROVE":
        decision = "OVERTURN_DENIAL"
        rationale = f"Appeal approved. New evidence supports medical necessity: {clinical_reanalysis.rationale}"
    else:
        decision = "UPHOLD_DENIAL"
        rationale = f"Appeal denied. Medical necessity still not met: {clinical_reanalysis.rationale}"
    
    return AppealDecision(
        appeal_id=appeal_request.appeal_id,
        decision=decision,
        rationale=rationale,
        reviewer_npi=appeal_request.reviewer_npi,
        decision_timestamp=datetime.utcnow()
    )
```

---

## Input/Output Specifications

### Input
```json
{
  "appeal_id": "APL-2026-00123",
  "original_case_id": "PA-2026-001234",
  "appeal_type": "INTERNAL_REVIEW",
  "urgency": "STANDARD",
  "appellant": "MEMBER",
  "appeal_received_date": "2026-06-15",
  "original_denial_date": "2026-05-01",
  "appeal_rationale": "New MRI shows progressive worsening, supports medical necessity for surgery",
  "new_evidence": [
    {
      "type": "MRI",
      "date": "2026-06-10",
      "findings": "Significant progression of OA since initial X-ray"
    }
  ],
  "iro_requested": false
}
```

### Output
```json
{
  "appeal_id": "APL-2026-00123",
  "appeal_decision": "OVERTURN_DENIAL",
  "original_decision": "DENY",
  "final_decision": "APPROVE",
  "decision_rationale": "New MRI evidence demonstrates progression of condition. Medical necessity now met per MCG guidelines.",
  "reviewer_name": "Dr. Jane Smith, MD",
  "reviewer_npi": "9876543210",
  "review_date": "2026-06-20",
  "processing_time_days": 5,
  "sla_met": true,
  "iro_required": false,
  "decision_letter_sent": true,
  "authorization_number": "AUTH-2026-987655"
}
```

---

## Processing Flow

1. Receive appeal request
2. Validate timeliness (180 days)
3. Classify urgency (standard vs expedited)
4. Assign to different clinical reviewer
5. Conduct de novo review (all evidence)
6. Generate appeal decision
7. Send decision letter
8. If denied + IRO requested → External review
9. Log appeal in compliance database

**Performance:**
- Standard appeals: 8 days avg (30-day SLA)
- Expedited appeals: 48 hours avg (72-hour SLA)
- Overturn rate: 18%
- SLA compliance: 100%

---

*Appeals Agent v2.0.0 - Ensuring Fair & Compliant Appeals*
