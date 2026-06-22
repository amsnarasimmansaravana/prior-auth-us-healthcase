---
title: 03 Benefits Agent
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Benefits Agent - Comprehensive Documentation

## Coverage Determination & Benefit Validation Agent

**Version:** 2.2.0 | **Owner:** Benefits Team | **Status:** Production

## Overview

### Business Purpose
Determines if requested service is covered under member's benefit plan, validates authorization requirements, calculates member cost-sharing (copay, coinsurance, deductible), and applies benefit limits.

**Key Objectives:**
- Verify procedure coverage under plan design
- Calculate accurate member cost-sharing
- Apply benefit limits (annual maximums, visit limits)
- Identify authorization requirements
- Detect experimental/investigational exclusions

**Business Impact:**
- Cost Avoidance: $18M annually preventing incorrect approvals
- Accuracy: 99.5% coverage determination accuracy
- Member Satisfaction: Transparent cost estimates upfront

### Technical Purpose
Real-time benefit configuration lookups with complex rule evaluation for multi-tiered benefit plans.

**Technologies:**
- LLM: GPT-4o (complex benefit interpretation)
- Database: PostgreSQL (benefit_configurations table)
- Cache: Redis (plan configurations, 24hr TTL)
- Rules Engine: Drools (benefit rules)

### Key Responsibilities

1. **Coverage Verification**
   - Query benefit configuration for plan
   - Match procedure code to covered benefits
   - Check exclusions list
   - Validate place of service

2. **Cost-Sharing Calculation**
   - Deductible application
   - Copay determination
   - Coinsurance calculation
   - Out-of-pocket maximum tracking

3. **Benefit Limits Application**
   - Annual visit limits (PT: 30 visits/year)
   - Lifetime maximums
   - Calendar year resets
   - Utilization tracking

4. **Prior Authorization Requirements**
   - Identify procedures requiring PA
   - Check if already approved
   - Validate authorization periods

5. **Network Status Impact**
   - In-network vs out-of-network benefits
   - Tier-based cost sharing
   - Balance billing protections

---

## Business Rules

### Rule 1: Coverage Determination Logic
```yaml
Rule ID: BEN-001
Description: Determine if procedure is covered

Logic:
  1. Query benefit_configuration WHERE plan_id = member.plan_id
  2. Check if procedure_code in covered_procedures
  3. Check if diagnosis supports procedure (medically necessary coverage)
  4. Verify place_of_service matches plan allowances
  5. Check exclusions list

Exclusions:
  - Cosmetic procedures
  - Experimental treatments
  - Non-FDA approved drugs
  - Services outside USA (except emergency)

Result:
  COVERED: Proceed to cost calculation
  NOT_COVERED: Deny with specific reason
  CONDITIONAL: Requires additional review
```

### Rule 2: Deductible Application
```yaml
Rule ID: BEN-002
Description: Apply deductible if not met

Deductible Types:
  Individual: $1,500/year
  Family: $3,000/year
  
Check:
  - Query claims database for YTD spending
  - Calculate remaining deductible
  - Determine if service applies to deductible

Services Exempt from Deductible:
  - Preventive care (ACA mandated)
  - Primary care visits (plan-specific)
  - Generic prescriptions (plan-specific)

Calculation:
  IF deductible_met == False:
    member_cost = min(service_cost, remaining_deductible)
  ELSE:
    member_cost = copay or coinsurance
```

### Rule 3: Network Tier Pricing
```yaml
Rule ID: BEN-003
Description: Different cost-sharing by network tier

Network Tiers:
  Tier 1 (Preferred): Copay $20, Coinsurance 10%
  Tier 2 (Standard): Copay $40, Coinsurance 20%
  Tier 3 (Out-of-Network): Copay $60, Coinsurance 40%

Action:
  - Determine provider network tier
  - Apply corresponding cost-sharing
  - Calculate estimated member responsibility
```

### Rule 4: Annual Benefit Maximums
```yaml
Rule ID: BEN-004
Description: Enforce annual visit/dollar limits

Examples:
  Physical Therapy: 30 visits/year
  Chiropractic: 20 visits/year
  DME: $5,000/year

Check:
  - Query utilization for current year
  - Calculate remaining benefits
  - Deny if limit exceeded

Reset: January 1st each year
```

---

## Technical Architecture

### Database Schema
```sql
CREATE TABLE benefit_configurations (
    plan_id VARCHAR(20) PRIMARY KEY,
    plan_name VARCHAR(100),
    coverage_rules JSONB,  -- Flexible benefit rules
    cost_sharing JSONB,    -- Copay/coinsurance
    limits JSONB,          -- Annual/lifetime limits
    exclusions TEXT[],     -- Excluded procedures
    network_tiers JSONB,   -- Tier-based pricing
    effective_date DATE,
    termination_date DATE
);

CREATE TABLE member_utilization (
    member_id VARCHAR(20),
    plan_id VARCHAR(20),
    year INTEGER,
    deductible_ytd NUMERIC(10,2),
    oop_max_ytd NUMERIC(10,2),
    pt_visits_ytd INTEGER,
    PRIMARY KEY (member_id, year)
);
```

### LLM Configuration
```yaml
Model: gpt-4o
Temperature: 0.2
Max Tokens: 2000

Use Cases:
  - Interpret ambiguous benefit language
  - Match procedure to benefit category
  - Explain coverage determination to member
```

---

## Input/Output Specifications

### Input
```json
{
  "case_id": "PA-2026-001234",
  "member_id": "M789456",
  "plan_id": "PLN-12345",
  "procedure_codes": ["27447"],
  "diagnosis_codes": ["M17.11"],
  "provider_npi": "1234567893",
  "service_date": "2026-07-15",
  "estimated_cost": 25000.00
}
```

### Output
```json
{
  "case_id": "PA-2026-001234",
  "coverage_status": "COVERED",
  "pa_required": true,
  "member_cost_sharing": {
    "deductible_remaining": 500.00,
    "deductible_applies": true,
    "copay": 0.00,
    "coinsurance_rate": 0.10,
    "estimated_member_cost": 2550.00,
    "oop_max_remaining": 4500.00
  },
  "benefit_details": {
    "plan_name": "PPO Gold Plus",
    "network_status": "IN_NETWORK",
    "network_tier": "TIER_1",
    "benefit_category": "Surgical Services",
    "annual_limit": null,
    "ytd_utilization": 0
  },
  "authorization_required": true,
  "processing_time_ms": 45
}
```

---

## Processing Flow

1. Receive request from Eligibility Agent
2. Query benefit_configurations for plan
3. Check Redis cache for plan rules
4. Match procedure to benefit category
5. Query member YTD utilization
6. Calculate deductible/OOP status
7. Determine network tier
8. Calculate member cost-sharing
9. Check PA requirements
10. Return coverage determination

**Performance:** P95 latency <50ms

---

## Integration Points

- **Upstream:** Eligibility Agent
- **Database:** PostgreSQL (benefits, utilization)
- **Cache:** Redis (plan configurations)
- **Downstream:** Clinical Agent, Decision Agent
- **External:** Network Management System, Claims Database

---

## Error Handling

| Error Code | Description | Action |
|------------|-------------|--------|
| BEN_PLAN_NOT_FOUND | Plan configuration missing | Route to manual review |
| BEN_PROCEDURE_NOT_MAPPED | Procedure not in benefit catalog | Clinical review required |
| BEN_COST_CALC_ERROR | Cost calculation failure | Default to member-favorable |
| BEN_LIMIT_EXCEEDED | Annual limit exceeded | Deny with appeal rights |

---

## Monitoring Metrics

- Coverage determination accuracy: >99.5%
- Cost calculation variance: <2% from actual claims
- Cache hit rate: >90%
- Response time P95: <50ms

---

## Examples

### Example 1: Covered Service with Deductible
```
Input: Knee replacement, member has $500 deductible remaining
Output: COVERED, member pays $500 (deductible) + $2,050 (10% coinsurance)
```

### Example 2: Excluded Service
```
Input: Cosmetic rhinoplasty
Output: NOT_COVERED (cosmetic exclusion)
```

### Example 3: Benefit Limit Reached
```
Input: Request for 31st PT visit (limit: 30/year)
Output: NOT_COVERED (annual limit exceeded)
```

---

*Benefits Agent documentation v2.2.0 - Production Ready*
