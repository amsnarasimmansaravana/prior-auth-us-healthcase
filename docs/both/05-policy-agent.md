---
title: 05 Policy Agent
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Policy Agent - Comprehensive Documentation

## Policy Retrieval & Rules Engine Agent

**Version:** 2.1.0 | **Owner:** Policy Management Team | **Status:** Production

## Overview

### Business Purpose
Retrieves and applies organizational policies, payer-specific rules, and regulatory requirements to prior authorization decisions. Ensures all determinations comply with plan documents, state/federal regulations, and contractual obligations.

**Key Objectives:**
- Retrieve accurate policy configurations
- Apply payer-specific rules consistently
- Ensure regulatory compliance (CMS, state DOI)
- Support policy version control
- Audit policy application

**Business Impact:**
- Compliance: 100% audit pass rate
- Policy Accuracy: 99.8% correct policy retrieval
- Version Control: Eliminates retroactive policy disputes
- Consistency: Standardized rule application across 50,000 PA/day

### Technical Purpose
Rule engine with versioned policy repository, supporting complex decision trees and regulatory compliance checks.

**Technologies:**
- Rules Engine: Drools (Java-based)
- Database: PostgreSQL (policy_configurations table)
- Cache: Redis (active policies, 24hr TTL)
- Version Control: Policy versions with effective dates
- LLM: GPT-4o (policy interpretation)

### Key Responsibilities

1. **Policy Retrieval**
   - Query policy repository for plan
   - Select correct policy version by effective date
   - Cache frequently accessed policies
   - Handle policy amendments

2. **Rules Application**
   - Execute Drools rule engine
   - Apply decision tree logic
   - Combine multiple policy sources
   - Document rule execution path

3. **Regulatory Compliance**
   - Apply CMS regulations (Medicare Advantage)
   - State Insurance Department mandates
   - ACA essential health benefits
   - Network adequacy requirements

4. **Contractual Obligations**
   - Employer group amendments
   - Provider contract terms
   - Carved-out benefits
   - Delegated authorization agreements

5. **Policy Version Control**
   - Track policy effective dates
   - Apply correct version for service date
   - Handle retroactive policy changes
   - Maintain audit trail

---

## Business Rules

### Rule 1: Policy Version Selection
```yaml
Rule ID: POL-001
Description: Select correct policy version for service date

Logic:
  SELECT policy_config 
  FROM policy_repository
  WHERE plan_id = {plan_id}
  AND effective_date <= {service_date}
  AND (termination_date IS NULL OR termination_date > {service_date})
  ORDER BY effective_date DESC
  LIMIT 1

Edge Cases:
  - Multiple versions on same date → Use latest version_number
  - Retroactive policy changes → Apply policy in effect on service date, NOT approval date
  - Future service dates → Use currently active policy (subject to change)
```

### Rule 2: CMS Medicare Advantage Requirements
```yaml
Rule ID: POL-002
Description: Apply CMS MA regulations

CMS Timelines (Medicare Advantage):
  - Standard PA: 14 calendar days
  - Expedited PA: 72 hours
  - Appeals: 30 days
  - Grievances: 30 days

Mandatory Coverage:
  - Emergency services (no PA required)
  - Urgently needed services
  - Out-of-network emergency (EMTALA)

Action:
  IF plan_type == "Medicare Advantage":
    Apply CMS timelines
    Waive PA for emergencies
    Expedite if clinical urgency
```

### Rule 3: State-Specific Mandates
```yaml
Rule ID: POL-003
Description: Apply state insurance mandates

Examples:
  California: Autism therapy coverage mandatory
  New York: IVF coverage required
  Massachusetts: Mental health parity
  
Logic:
  member_state = member.state_of_residence
  mandates = query_state_mandates(member_state)
  
  FOR EACH mandate in mandates:
    IF procedure in mandate.covered_services:
      override_plan_exclusion = True
      coverage_basis = "STATE_MANDATE"
```

### Rule 4: Employer Group Amendments
```yaml
Rule ID: POL-004
Description: Apply employer-specific policy modifications

Amendment Types:
  - Carved-in benefits (e.g., fertility coverage)
  - Enhanced limits (higher PT visit limits)
  - Reduced cost-sharing (lower copays)
  - Excluded services (e.g., bariatric surgery)

Priority:
  1. Employer amendment
  2. State mandate
  3. Base plan policy
  4. CMS regulation

Logic:
  IF employer_group HAS amendments:
    Apply amended policy
  ELSE:
    Apply base policy
```

### Rule 5: Network Adequacy Exceptions
```yaml
Rule ID: POL-005
Description: Grant out-of-network exceptions when network inadequate

Triggers:
  - No in-network provider within 30 miles
  - No in-network specialist for condition
  - Wait time >30 days for appointment
  - Provider doesn't accept new patients

Action:
  IF network_inadequate == True:
    status = "OUT_OF_NETWORK_EXCEPTION_APPROVED"
    reimbursement_rate = in_network_rate
    member_cost_sharing = in_network_cost_sharing
    
Documentation Required:
  - Member attempted to find in-network provider
  - Provider search results
  - Approval from Medical Director
```

---

## Technical Architecture

### Drools Rule Engine Example

```drl
package com.healthplan.authorization.rules;

import com.healthplan.model.*;

rule "Emergency Service - No PA Required"
    when
        $case : PACase(
            placeOfService == PlaceOfService.EMERGENCY_ROOM
        )
    then
        $case.setAuthorizationRequired(false);
        $case.addPolicyNote("Emergency services do not require PA per CMS regulations");
        $case.setPolicyBasis("CMS_EMTALA");
end

rule "Medicare Advantage - Expedited Timeline"
    when
        $case : PACase(
            planType == PlanType.MEDICARE_ADVANTAGE,
            urgency == Urgency.EXPEDITED
        )
    then
        $case.setDeadline(72, TimeUnit.HOURS);
        $case.addPolicyNote("CMS requires 72-hour decision for expedited MA requests");
end

rule "State Mandate - Autism Therapy (California)"
    when
        $case : PACase(
            memberState == "CA",
            diagnosisCode in ("F84.0", "F84.5"),  // Autism spectrum
            procedureCode in ("97153", "97155")   // ABA therapy
        )
    then
        $case.setCoverageStatus(CoverageStatus.COVERED);
        $case.addPolicyNote("Covered per California autism mandate AB 88");
        $case.setPolicyBasis("STATE_MANDATE_CA_AB88");
end
```

### Policy Repository Schema

```sql
CREATE TABLE policy_configurations (
    policy_id SERIAL PRIMARY KEY,
    plan_id VARCHAR(20),
    policy_version INTEGER,
    effective_date DATE,
    termination_date DATE,
    policy_rules JSONB,  -- Drools rule definitions
    regulatory_basis VARCHAR(100), -- CMS, STATE, CONTRACT
    created_at TIMESTAMP,
    created_by VARCHAR(50),
    approved_by VARCHAR(50)
);

CREATE TABLE employer_amendments (
    amendment_id SERIAL PRIMARY KEY,
    employer_group_id VARCHAR(20),
    plan_id VARCHAR(20),
    amendment_type VARCHAR(50),
    amendment_details JSONB,
    effective_date DATE,
    termination_date DATE
);

CREATE TABLE state_mandates (
    mandate_id SERIAL PRIMARY KEY,
    state_code CHAR(2),
    mandate_name VARCHAR(200),
    statute_reference VARCHAR(50),
    covered_services TEXT[],
    effective_date DATE
);
```

---

## Input/Output Specifications

### Input
```json
{
  "case_id": "PA-2026-001234",
  "plan_id": "PLN-12345",
  "member_state": "CA",
  "employer_group_id": "EMP-987",
  "service_date": "2026-07-15",
  "procedure_code": "97153",
  "diagnosis_code": "F84.0",
  "place_of_service": "11", // Office
  "urgency": "STANDARD"
}
```

### Output
```json
{
  "case_id": "PA-2026-001234",
  "policy_version": "PLN-12345-v3",
  "policy_effective_date": "2026-01-01",
  "rules_applied": [
    {
      "rule_id": "STATE_MANDATE_CA_AB88",
      "rule_description": "California autism therapy mandate",
      "outcome": "COVERAGE_REQUIRED",
      "priority": 1
    },
    {
      "rule_id": "PA_REQUIRED_ABA",
      "rule_description": "ABA therapy requires PA",
      "outcome": "PA_REQUIRED",
      "priority": 2
    }
  ],
  "employer_amendments": [],
  "state_mandates": [
    {
      "state": "CA",
      "mandate": "AB 88 - Autism Coverage",
      "impact": "Must cover ABA therapy"
    }
  ],
  "regulatory_compliance": {
    "cms_compliant": true,
    "state_compliant": true,
    "aca_compliant": true
  },
  "policy_notes": [
    "Covered per CA autism mandate",
    "PA required for visit limits >40/year"
  ],
  "processing_time_ms": 25
}
```

---

## Processing Flow

1. Receive case from Benefits Agent
2. Query policy_configurations for plan
3. Check Redis cache for cached policy
4. Select correct policy version by service date
5. Load Drools rules from policy
6. Execute rule engine
7. Apply employer amendments
8. Apply state mandates
9. Check CMS/regulatory requirements
10. Return policy determination

**Performance:** <30ms P95 latency

---

## Integration Points

- **Upstream:** Benefits Agent
- **Database:** PostgreSQL (policies, amendments, mandates)
- **Cache:** Redis (active policies)
- **Rules Engine:** Drools
- **Downstream:** Clinical Agent, Decision Agent
- **External:** State DOI databases, CMS policy updates

---

## Monitoring

- Policy retrieval accuracy: 99.8%
- Rule execution time: <30ms P95
- Policy version conflicts: <0.1%
- Regulatory compliance violations: 0%

---

*Policy Agent v2.1.0 - Ensuring 100% Compliance*
