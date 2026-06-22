# Policy Service - Comprehensive Documentation

## Plan Policy & Configuration Service

**Version:** 2.5.0 | **Owner:** Policy Management Team | **Status:** Production

## Overview

### Business Purpose
Centralized repository of plan policies, coverage rules, benefit designs, and payer-specific configurations driving PA decisions.

**Key Capabilities:**
- Policy version control (effective dating)
- Coverage rule definitions
- Exclusion/limitation management
- Employer group amendments
- State mandate tracking

**Business Impact:**
- Policy Accuracy: 99.8%
- Version Control: Zero retroactive disputes
- Policy Updates: 500+ annually
- API Response Time: <30ms P95

### Technical Architecture

**Technologies:**
- Database: PostgreSQL 15 (policy repository)
- Version Control: Git-backed policy definitions
- Cache: Redis (24-hour TTL)
- Rules Engine: Drools (embedded rules)

---

## Database Schema

```sql
CREATE TABLE plan_policies (
    policy_id SERIAL PRIMARY KEY,
    plan_id VARCHAR(20),
    policy_version INTEGER,
    effective_date DATE NOT NULL,
    termination_date DATE,
    policy_name VARCHAR(200),
    policy_document_url VARCHAR(500),
    
    -- Coverage Rules (JSONB for flexibility)
    coverage_rules JSONB,
    exclusions TEXT[],
    limitations JSONB,
    prior_auth_requirements JSONB,
    
    -- Regulatory Basis
    regulatory_basis VARCHAR(100),  -- CMS, STATE_CA, ACA, etc.
    state_mandates TEXT[],
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approval_date TIMESTAMP
);

CREATE TABLE coverage_rules (
    rule_id SERIAL PRIMARY KEY,
    policy_id INTEGER REFERENCES plan_policies(policy_id),
    rule_type VARCHAR(50),  -- COVERAGE, EXCLUSION, LIMITATION, PA_REQUIRED
    procedure_codes TEXT[],  -- CPT/HCPCS codes affected
    diagnosis_codes TEXT[],  -- ICD-10 codes
    rule_definition JSONB,
    effective_date DATE,
    termination_date DATE
);

CREATE TABLE employer_amendments (
    amendment_id SERIAL PRIMARY KEY,
    employer_group_id VARCHAR(20),
    base_policy_id INTEGER REFERENCES plan_policies(policy_id),
    amendment_type VARCHAR(50),  -- CARVE_IN, ENHANCED_BENEFIT, EXCLUSION
    affected_services TEXT[],
    amendment_details JSONB,
    effective_date DATE,
    termination_date DATE
);
```

---

## API Specifications

### GET /api/v1/policies/{plan_id}
```json
Request:
GET /api/v1/policies/PLN-12345?effective_date=2026-07-15

Response:
{
  "plan_id": "PLN-12345",
  "policy_version": 3,
  "effective_date": "2026-01-01",
  "plan_name": "PPO Gold Plus",
  "coverage_summary": {
    "inpatient_hospital": "Covered",
    "outpatient_surgery": "Covered",
    "durable_medical_equipment": "Covered with limits",
    "experimental_procedures": "Excluded"
  },
  "prior_auth_required": [
    "Inpatient admissions",
    "Advanced imaging (MRI, CT, PET)",
    "Specialty medications",
    "Orthopedic surgery"
  ],
  "exclusions": [
    "Cosmetic procedures",
    "Experimental/investigational treatments",
    "Services outside USA (except emergency)"
  ]
}
```

### GET /api/v1/policies/{plan_id}/pa-requirements
```json
Request:
GET /api/v1/policies/PLN-12345/pa-requirements?procedure_code=27447

Response:
{
  "plan_id": "PLN-12345",
  "procedure_code": "27447",
  "procedure_description": "Total knee arthroplasty",
  "pa_required": true,
  "pa_type": "PROSPECTIVE",  // Before service
  "clinical_criteria": "MCG A-0527",
  "required_documentation": [
    "X-rays showing severe OA",
    "PT notes (6-12 weeks)",
    "Failed conservative therapy documentation"
  ],
  "decision_timeline": "14 calendar days"
}
```

---

*Policy Service v2.5.0 - 500+ Annual Updates*
