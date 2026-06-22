# Formulary Service - Comprehensive Documentation

## Prescription Drug Formulary Service

**Version:** 2.3.0 | **Owner:** Pharmacy Benefits Team | **Status:** Production

## Overview

### Business Purpose
Manages prescription drug formularies including tier assignments, prior authorization requirements, step therapy protocols, and quantity limits for all pharmacy benefits.

**Key Capabilities:**
- Drug formulary management
- Tier assignment (Generic, Preferred Brand, Non-Preferred)
- PA requirements for specialty drugs
- Step therapy protocols
- Quantity limit enforcement

**Business Impact:**
- Formulary Drugs: 12,000+ NDC codes
- Generic Utilization Rate: 87%
- Specialty Drug Cost Savings: $42M annually
- PA Compliance: 99.5%

### Technical Architecture

**Technologies:**
- Database: PostgreSQL 15
- Drug Database: First Databank (FDB)
- API: REST + NCPDP SCRIPT
- Update Frequency: Monthly

---

## Database Schema

```sql
CREATE TABLE formulary (
    formulary_id SERIAL PRIMARY KEY,
    plan_id VARCHAR(20),
    ndc_code VARCHAR(11),  -- National Drug Code
    drug_name VARCHAR(200),
    formulary_tier INTEGER,  -- 1=Generic, 2=Preferred Brand, 3=Non-Preferred
    pa_required BOOLEAN DEFAULT FALSE,
    step_therapy_required BOOLEAN DEFAULT FALSE,
    quantity_limit INTEGER,
    days_supply_limit INTEGER DEFAULT 30,
    effective_date DATE,
    termination_date DATE
);

CREATE TABLE step_therapy_protocols (
    protocol_id SERIAL PRIMARY KEY,
    drug_ndc VARCHAR(11),
    required_trials TEXT[],  -- List of drugs to try first
    trial_duration_days INTEGER,
    failure_criteria TEXT
);
```

---

## API Specifications

### GET /api/v1/formulary/{plan_id}/drug
```json
Request:
GET /api/v1/formulary/PLN-12345/drug?ndc=00002-3227-01

Response:
{
  "plan_id": "PLN-12345",
  "ndc": "00002-3227-01",
  "drug_name": "Humira 40mg/0.8mL",
  "formulary_status": "COVERED",
  "tier": 3,
  "tier_name": "Specialty",
  "pa_required": true,
  "step_therapy": false,
  "quantity_limit": 2,
  "days_supply_limit": 30,
  "member_cost_sharing": {
    "copay": 150.00
  }
}
```

---

*Formulary Service v2.3.0 - 12,000+ Drugs*
