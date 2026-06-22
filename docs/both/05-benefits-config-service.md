---
title: 05 Benefits Config Service
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Benefits Configuration Service - Comprehensive Documentation

## Plan Benefit Design & Configuration Service

**Version:** 2.7.0 | **Owner:** Benefits Design Team | **Status:** Production

## Overview

### Business Purpose
Manages benefit plan designs including deductibles, copays, coinsurance, out-of-pocket maximums, coverage limits, and cost-sharing structures for all plan types.

**Key Capabilities:**
- Benefit plan configuration
- Cost-sharing calculation parameters
- Coverage tier definitions
- Network tier pricing
- Benefit limit management

**Business Impact:**
- Active Benefit Plans: 1,200+
- Calculation Accuracy: 99.6%
- API Response Time: <20ms P95
- Configuration Changes: 3,500+ annually

### Technical Architecture

**Technologies:**
- Database: PostgreSQL 15
- Cache: Redis (plan configurations)
- API: REST + GraphQL
- Version Control: Git-backed benefit definitions

---

## Database Schema

```sql
CREATE TABLE benefit_plans (
    plan_id VARCHAR(20) PRIMARY KEY,
    plan_name VARCHAR(100),
    plan_type VARCHAR(20),  -- HMO, PPO, EPO, POS, HDHP
    metal_tier VARCHAR(20),  -- BRONZE, SILVER, GOLD, PLATINUM
    effective_date DATE,
    termination_date DATE,
    
    -- Deductibles
    individual_deductible NUMERIC(10,2),
    family_deductible NUMERIC(10,2),
    individual_oop_max NUMERIC(10,2),
    family_oop_max NUMERIC(10,2),
    
    -- Configuration
    benefit_configuration JSONB,
    cost_sharing_config JSONB,
    network_tiers JSONB
);

CREATE TABLE benefit_categories (
    category_id SERIAL PRIMARY KEY,
    plan_id VARCHAR(20) REFERENCES benefit_plans(plan_id),
    category_name VARCHAR(100),  -- PRIMARY_CARE, SPECIALIST, SURGERY, etc.
    
    -- In-Network Cost-Sharing
    in_network_copay NUMERIC(10,2),
    in_network_coinsurance NUMERIC(5,4),  -- 0.20 = 20%
    
    -- Out-of-Network Cost-Sharing
    out_network_copay NUMERIC(10,2),
    out_network_coinsurance NUMERIC(5,4),
    
    -- Limits
    annual_visit_limit INTEGER,
    annual_dollar_limit NUMERIC(10,2),
    lifetime_limit NUMERIC(10,2)
);
```

---

## API Specifications

### GET /api/v1/benefits/{plan_id}
```json
Response:
{
  "plan_id": "PLN-12345",
  "plan_name": "PPO Gold Plus",
  "deductible": {
    "individual": 1500.00,
    "family": 3000.00
  },
  "oop_max": {
    "individual": 6000.00,
    "family": 12000.00
  },
  "cost_sharing": {
    "primary_care": {
      "in_network_copay": 20.00,
      "out_network_copay": 60.00
    },
    "specialist": {
      "in_network_copay": 40.00,
      "out_network_copay": 80.00
    },
    "surgery": {
      "in_network_coinsurance": 0.10,
      "out_network_coinsurance": 0.40
    }
  }
}
```

---

*Benefits Config Service v2.7.0 - 1,200+ Plans*
