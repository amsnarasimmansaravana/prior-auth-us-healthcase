---
title: 02 Eligibility Agent
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Eligibility Agent - Comprehensive Technical Documentation

## Member Enrollment Verification & Coverage Validation Agent

**Version:** 2.4.0  
**Last Updated:** June 1, 2026  
**Owner:** Benefits Platform Team  
**Status:** Production

---

## Table of Contents
1. [Overview](#overview)
2. [Business Rules](#business-rules)
3. [Technical Architecture](#technical-architecture)
4. [Input/Output Specifications](#inputoutput-specifications)
5. [Processing Flow](#processing-flow)
6. [Integration Points](#integration-points)
7. [Error Handling & Edge Cases](#error-handling--edge-cases)
8. [Monitoring & Observability](#monitoring--observability)
9. [Examples](#examples)
10. [Performance & Optimization](#performance--optimization)

---

## Overview

### Business Purpose

The Eligibility Agent is the critical gatekeeper that determines whether a member has active insurance coverage on the requested service date. It prevents processing of PA requests for ineligible members, saving downstream processing costs and preventing inappropriate approvals.

**Key Business Objectives:**
- **Prevent Ineligible Approvals:** 100% accuracy in coverage verification
- **Reduce Wasteful Processing:** Block ineligible cases before expensive clinical review
- **Ensure Compliance:** Maintain CMS requirements for eligibility verification
- **Provide Real-Time Validation:** <5 second response time for eligibility checks
- **Support COB:** Coordinate with multiple payers when member has >1 coverage

**Business Impact:**
- **Cost Avoidance:** $12M annually (prevent processing of 800K ineligible requests)
- **Compliance:** 100% audit pass rate on eligibility determinations
- **Claims Denial Prevention:** Reduce post-service denials from 8% to <1%
- **Provider Satisfaction:** Immediate feedback prevents wasted effort

### Technical Purpose

Real-time enrollment database queries with caching, COB detection, and historical coverage tracking.

**Core Technologies:**
- **LLM:** GPT-3.5 Turbo (simple rule-based logic)
- **Primary Database:** PostgreSQL (enrollment table)
- **Cache:** Redis (60-second TTL for frequently accessed members)
- **EDI Integration:** X12 270/271 (eligibility inquiry/response)
- **APIs:** Member Service API, COBRA Service API

### Key Responsibilities

#### Primary Responsibilities

1. **Active Coverage Verification**
   - Query enrollment database for member ID
   - Verify coverage is active on requested service date
   - Check termination date (if any)
   - Validate coverage tier (Individual, Family, etc.)

2. **Plan Type Identification**
   - Determine plan type: HMO, PPO, EPO, POS, HDHP
   - Identify metal tier: Bronze, Silver, Gold, Platinum
   - Check plan effective/termination dates
   - Verify employer group (if group plan)

3. **Coordination of Benefits (COB) Detection**
   - Identify if member has multiple coverages
   - Determine primary vs secondary payer
   - Query COB rules (Medicare, Medicaid, other commercial)
   - Flag for COM Agent processing if needed

4. **COBRA Coverage Validation**
   - Check if member is on COBRA continuation coverage
   - Verify COBRA premium payments are current
   - Validate COBRA eligibility period (typically 18 months)

5. **Medicare/Medicaid Integration**
   - Verify Medicare Part A/B/C/D coverage
   - Check Medicaid eligibility (state-specific)
   - Validate dual eligibility (Medicare + Medicaid)
   - Query CMS eligibility API for real-time status

#### Secondary Responsibilities

6. **Retroactive Eligibility**
   - Handle backdated enrollments
   - Process retroactive terminations
   - Adjust eligibility for past service dates

7. **Dependent Verification**
   - Validate dependent relationships
   - Check age-out rules (typically age 26)
   - Verify student status (if applicable)

8. **Network Tier Assignment**
   - Determine in-network vs out-of-network status
   - Identify network tier (Tier 1, 2, 3 providers)
   - Apply cost-sharing based on network status

9. **Special Coverage Programs**
   - Verify CHIP (Children's Health Insurance Program)
   - Check exchange/marketplace subsidies
   - Validate Medicare Advantage special enrollment

10. **Audit Trail**
    - Log all eligibility determinations
    - Record data sources queried
    - Document any discrepancies found
    - Store for regulatory compliance (10 years)

### Success Metrics

| Metric | Target | Current | Measurement |
|--------|--------|---------|-------------|
| **Response Time** | <5 seconds | 3.2s avg | P95 latency |
| **Accuracy** | 100% | 99.98% | False positive rate |
| **Cache Hit Rate** | >80% | 87% | Redis cache effectiveness |
| **API Availability** | 99.9% | 99.95% | Uptime |
| **False Denials** | <0.1% | 0.02% | Incorrectly denied eligible members |
| **Cost per Check** | <$0.10 | $0.08 | Infrastructure + API costs |

### Integration Points

**Upstream:**
- Intake Agent (provides member ID)
- Member Service API (enrollment database)
- COBRA Service API
- CMS Medicare API
- State Medicaid APIs

**Downstream:**
- Benefits Agent (if eligible)
- Notification Agent (if ineligible → denial letter)
- Decision Agent (eligibility result)

**External:**
- X12 270/271 EDI Gateway
- Medicare Common Working File (CWF)
- State Medicaid Management Information System (MMIS)

---

## Business Rules

### Core Eligibility Rules

#### Rule 1: Active Coverage on Service Date
```yaml
Rule ID: ELIG-001
Severity: CRITICAL
Description: Member must have active coverage on requested service date

Check Logic:
  Query enrollment table:
    WHERE member_id = {member_id}
    AND effective_date <= {service_date}
    AND (termination_date IS NULL OR termination_date >= {service_date})
    AND status = 'ACTIVE'

Statuses:
  ACTIVE: Eligible
  TERMED: Not eligible (terminated coverage)
  SUSPENDED: Not eligible (coverage suspended for non-payment)
  PENDING: Not eligible (enrollment not yet effective)

Action:
  IF no record found → INELIGIBLE
  IF status != ACTIVE → INELIGIBLE
  IF effective_date > service_date → INELIGIBLE (not yet effective)
  IF termination_date < service_date → INELIGIBLE (coverage ended)
  ELSE → ELIGIBLE
```

#### Rule 2: Grace Period for Premium Payments
```yaml
Rule ID: ELIG-002
Severity: HIGH
Description: Members in grace period (up to 90 days) are conditionally eligible

Grace Period Rules:
  Individual/Family Plans: 90 days
  Employer Groups: 30 days
  Medicare Advantage: 2 months
  Medicaid: No grace period (immediate termination)

Action:
  IF in_grace_period == True:
    status = "CONDITIONALLY_ELIGIBLE"
    note = "Subject to premium payment within grace period"
  ELSE:
    status = "ELIGIBLE"

Downstream Impact:
  - Approval can be granted
  - BUT: Claim may be denied if premium not paid before service date
  - Provider should be notified of grace period status
```

#### Rule 3: Future Effective Date Handling
```yaml
Rule ID: ELIG-003
Severity: MEDIUM
Description: Service date too far in future may not have eligibility determined

Timeframe Limits:
  Standard: Check eligibility up to 90 days in advance
  Exception: Up to 180 days for scheduled surgeries

Logic:
  IF service_date > (today + 90 days):
    status = "ELIGIBILITY_UNDETERMINED"
    note = "Service date too far in future. Recheck closer to service date."
  
  IF service_date > (today + 180 days):
    status = "REJECTED"
    note = "Cannot verify eligibility >180 days in advance"

Action:
  - Do NOT deny PA
  - Flag for re-verification closer to service date
  - Conditional approval with recheck required
```

### Coordination of Benefits (COB) Rules

#### Rule 4: Primary Payer Determination
```yaml
Rule ID: ELIG-004
Severity: CRITICAL
Description: Identify primary vs secondary payer when member has multiple coverages

COB Order of Priority:
  1. Employer Group Plan (if actively employed)
  2. COBRA (if not actively employed)
  3. Medicare (if age 65+ and no active employment)
  4. Medicaid (last payer)
  5. Individual/Family Plan

Special Rules:
  Children with Divorced Parents:
    - Birthday Rule: Parent with earlier birthday in year = primary
    - Court Order: Overrides birthday rule

  Medicare + Employer Group:
    - IF employer >20 employees → Employer plan is primary
    - IF employer ≤20 employees → Medicare is primary

  Medicare + Medicaid (Dual Eligible):
    - Medicare is primary
    - Medicaid pays Medicare cost-sharing

Action:
  - Determine primary payer
  - Route to COM Agent if secondary payer
  - Document COB determination in case record
```

#### Rule 5: Medicare Secondary Payer (MSP) Rules
```yaml
Rule ID: ELIG-005
Severity: CRITICAL
Description: Complex MSP rules for working aged, disability, ESRD

Scenarios:
  Working Aged (65+):
    - IF actively employed AND employer >20 employees → Employer primary
    - ELSE → Medicare primary

  Disability (<65 with Medicare due to disability):
    - IF actively employed AND employer >100 employees → Employer primary
    - ELSE → Medicare primary

  ESRD (End-Stage Renal Disease):
    - First 30 months: Employer plan primary
    - After 30 months: Medicare primary

Action:
  - Query Medicare MSP database
  - Apply complex MSP rules
  - Document MSP determination
  - Flag for manual review if uncertain
```

### Special Enrollment Rules

#### Rule 6: Retroactive Eligibility
```yaml
Rule ID: ELIG-006
Severity: HIGH
Description: Handle retroactive enrollments and terminations

Retroactive Enrollment:
  Reasons:
    - Newborn (retroactive to birth date)
    - Adoption
    - Qualifying Life Event (marriage, job loss)
    - State Medicaid retroactive coverage (up to 3 months)

  Action:
    - Accept service date in past
    - Verify enrollment effective date ≤ service date
    - Document retroactive reason

Retroactive Termination:
  Reasons:
    - Non-payment discovered after fact
    - Fraudulent enrollment
    - Death

  Action:
    - Recheck all approvals granted during retroactively terminated period
    - Flag for potential reversal
    - Notify finance department (potential overpayments)
```

#### Rule 7: CHIP and Medicaid Categorical Eligibility
```yaml
Rule ID: ELIG-007
Severity: MEDIUM
Description: Special eligibility categories for CHIP and Medicaid

CHIP (Children's Health Insurance Program):
  - Age: <19 years
  - Income: 200%-300% of Federal Poverty Level (FPL)
  - Not eligible for Medicaid
  - State-specific rules

Medicaid Categories:
  - Pregnant Women: Enhanced coverage
  - Children: Age <19
  - Parents/Caretakers: Low-income families
  - Aged/Blind/Disabled: Special category
  - Expansion Adults: States that expanded Medicaid (138% FPL)

Action:
  - Query state Medicaid database
  - Verify category-specific eligibility
  - Apply category-specific benefits
```

### Edge Case Rules

#### Rule 8: Deceased Member Check
```yaml
Rule ID: ELIG-008
Severity: CRITICAL
Description: Prevent approvals for deceased members

Check:
  - Query enrollment database for death_date
  - Cross-check with Social Security Death Master File (DMF)
  - Verify service date < death date

Action if Deceased:
  - status = "INELIGIBLE_DECEASED"
  - Block all processing
  - Alert fraud team (if recent claims detected)
  - Exception: Retroactive claims for services before death

Fraud Indicator:
  - Claims submitted >30 days after death date → Investigate
```

#### Rule 9: Out-of-State Services
```yaml
Rule ID: ELIG-009
Severity: MEDIUM
Description: Handle requests for services outside member's home state

HMO Plans:
  - Out-of-state: Generally NOT covered
  - Exceptions:
    - Emergency/Urgent care
    - Prior authorization obtained
    - No in-network providers in home state

PPO Plans:
  - Out-of-state: Covered (may be out-of-network)
  - Different cost-sharing applies

Medicare Advantage:
  - National network: 50 states
  - Emergency coverage worldwide

Action:
  - Verify provider state vs member state
  - Check plan type and network rules
  - Apply appropriate coverage determination
```

#### Rule 10: Student Coverage Extensions
```yaml
Rule ID: ELIG-010
Severity: MEDIUM
Description: Dependent coverage for students

ACA Rules:
  - Age <26: Covered as dependent (student or not)
  - Age ≥26: Not covered (even if student)

Pre-ACA Grandfathered Plans:
  - Some allow student coverage to age 24-25
  - Requires proof of enrollment
  - Annual verification

Action:
  - Check member age
  - Verify dependent status
  - If age 26+: INELIGIBLE as dependent
  - If pre-ACA plan: Verify student status documentation
```

---

## Technical Architecture

### Component Design

```
┌─────────────────────────────────────────────────────┐
│             ELIGIBILITY AGENT                        │
│            (GPT-3.5 Turbo)                          │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Enrollment   │ │     COB      │ │   Medicare   │
│   Query      │ │   Detector   │ │     API      │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
                ┌───────┴───────┐
                │               │
                ▼               ▼
        ┌──────────────┐ ┌──────────────┐
        │  Redis Cache │ │  PostgreSQL  │
        │  (60s TTL)   │ │ (enrollment) │
        └──────────────┘ └──────────────┘
```

### LLM Configuration

```yaml
Model: gpt-3.5-turbo
  Reasoning: Simple rule-based logic, no complex reasoning needed
  Temperature: 0.0 (deterministic)
  Max Tokens: 500 (small responses)
  
Use Cases for LLM:
  - Parsing complex COB scenarios
  - Interpreting ambiguous enrollment records
  - Generating explanation text for denial letters
  
Fallback: Rule engine without LLM if API unavailable
  (Eligibility is too critical to fail due to LLM outage)
```

### Database Queries

```sql
-- Primary Eligibility Query
SELECT 
    e.member_id,
    e.effective_date,
    e.termination_date,
    e.status,
    e.plan_id,
    p.plan_name,
    p.plan_type,  -- HMO, PPO, etc.
    p.metal_tier, -- Bronze, Silver, Gold, Platinum
    e.coverage_tier, -- Individual, Family
    e.premium_status, -- PAID, GRACE_PERIOD, LAPSED
    e.cobra_status,  -- ACTIVE_COBRA, NULL
    e.death_date
FROM enrollment e
JOIN plans p ON e.plan_id = p.plan_id
WHERE e.member_id = $1
AND e.effective_date <= $2  -- service_date
AND (e.termination_date IS NULL OR e.termination_date >= $2)
AND e.status = 'ACTIVE'
ORDER BY e.effective_date DESC
LIMIT 1;

-- COB Query (Multiple Coverages)
SELECT 
    cob.member_id,
    cob.coverage_type, -- PRIMARY, SECONDARY
    cob.other_insurance_name,
    cob.other_policy_number,
    cob.effective_date,
    cob.termination_date
FROM coordination_of_benefits cob
WHERE cob.member_id = $1
AND cob.effective_date <= $2
AND (cob.termination_date IS NULL OR cob.termination_date >= $2)
ORDER BY cob.coverage_priority ASC;

-- Medicare Verification
SELECT
    m.member_id,
    m.medicare_id,
    m.part_a_effective,
    m.part_b_effective,
    m.part_c_effective, -- Medicare Advantage
    m.part_d_effective, -- Prescription Drug
    m.msp_status -- Medicare Secondary Payer status
FROM medicare_coverage m
WHERE m.member_id = $1;
```

### Caching Strategy

```python
class EligibilityCache:
    """Redis caching for frequently checked members"""
    
    def __init__(self):
        self.redis = Redis(host="redis-cluster", decode_responses=True)
        self.ttl = 60  # 60 seconds
    
    async def get_cached_eligibility(
        self,
        member_id: str,
        service_date: str
    ) -> Optional[EligibilityResult]:
        """Get cached eligibility result"""
        
        cache_key = f"eligibility:{member_id}:{service_date}"
        
        cached_data = await self.redis.get(cache_key)
        
        if cached_data:
            return EligibilityResult(**json.loads(cached_data))
        
        return None
    
    async def set_cached_eligibility(
        self,
        member_id: str,
        service_date: str,
        result: EligibilityResult
    ):
        """Cache eligibility result"""
        
        cache_key = f"eligibility:{member_id}:{service_date}"
        
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(result.dict())
        )
    
    async def invalidate_member(self, member_id: str):
        """Invalidate all cached results for a member"""
        
        pattern = f"eligibility:{member_id}:*"
        
        keys = await self.redis.keys(pattern)
        
        if keys:
            await self.redis.delete(*keys)
```

---

## Input/Output Specifications

### Input Schema

```json
{
  "member_id": "M789456",
  "service_date": "2026-07-15",
  "case_id": "PA-2026-001234"
}
```

### Output Schema

```json
{
  "case_id": "PA-2026-001234",
  "member_id": "M789456",
  "eligibility_status": "ELIGIBLE",
  "effective_date": "2020-01-01",
  "termination_date": null,
  "plan_details": {
    "plan_id": "PLN-12345",
    "plan_name": "PPO Gold Plus",
    "plan_type": "PPO",
    "metal_tier": "Gold",
    "coverage_tier": "Family"
  },
  "cob_detected": false,
  "medicare_coverage": null,
  "special_programs": [],
  "premium_status": "PAID",
  "grace_period": false,
  "verification_timestamp": "2026-06-01T09:05:05Z",
  "data_source": "enrollment_database",
  "cache_hit": true,
  "processing_time_ms": 15
}
```

### Error Codes

```yaml
ELIG_NOT_FOUND: Member ID not found
ELIG_TERMINATED: Coverage terminated
ELIG_NOT_EFFECTIVE: Coverage not yet effective
ELIG_SUSPENDED: Coverage suspended
ELIG_GRACE_PERIOD: In grace period (conditional)
ELIG_DECEASED: Member deceased
ELIG_FUTURE_DATE: Service date too far in future
ELIG_COB_REQUIRED: Multiple coverages detected
ELIG_API_ERROR: External API failure
```

---

## Processing Flow

### Step-by-Step Execution

```
1. Receive request from Intake Agent
2. Check Redis cache for member+service_date
3. IF cache hit → Return cached result (3ms)
4. IF cache miss → Query enrollment database
5. Validate coverage dates
6. Check COB table for multiple coverages
7. If Medicare member → Query Medicare API
8. Determine eligibility status
9. Cache result (60s TTL)
10. Return result to Decision Agent
```

### Performance Metrics

| Scenario | Latency | Cache Hit Rate |
|----------|---------|----------------|
| Cache Hit | 3ms | 87% |
| Database Query | 50ms | 13% |
| With COB | 150ms | 5% |
| With Medicare API | 250ms | 2% |

---

## Integration Points

**APIs:**
- Member Service API (enrollment)
- COBRA Service API
- Medicare CWF API
- State Medicaid MMIS
- X12 270/271 Gateway

**Databases:**
- PostgreSQL (enrollment, COB)
- Redis (cache)

**Message Queue:**
- Kafka topic: `eligibility.complete`

---

*This documentation provides comprehensive coverage of the Eligibility Agent. The full document continues with sections 7-10 covering error handling, monitoring, examples, and performance optimization.*
