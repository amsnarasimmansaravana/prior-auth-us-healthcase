---
title: 02 Provider Service
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Provider Service - Comprehensive Documentation

## Provider Network & Credentialing Service

**Version:** 2.8.0 | **Owner:** Provider Network Team | **Status:** Production

## Overview

### Business Purpose
Centralized provider data repository with NPI registry, credentialing status, network participation, specialty information, and quality metrics.

**Key Capabilities:**
- Provider lookup by NPI, name, TIN
- Network status verification (in-network vs out-of-network)
- Credentialing status validation
- Specialty & taxonomy codes
- Provider quality scores
- Network tier assignment

**Business Impact:**
- Provider Accuracy: 99.5%
- NPI Validation: 100% (against NPPES)
- Network Contract Tracking: 8,500 contracts
- API Response Time: <25ms P95

### Technical Architecture

**Technologies:**
- Database: PostgreSQL 15
- External: NPPES NPI Registry API
- Cache: Redis (24-hour TTL)
- API: REST + GraphQL
- Sync: Daily NPPES sync

---

## Database Schema

```sql
CREATE TABLE providers (
    npi VARCHAR(10) PRIMARY KEY,  -- National Provider Identifier
    entity_type INTEGER,  -- 1=Individual, 2=Organization
    first_name VARCHAR(100),  -- Individual providers
    middle_name VARCHAR(50),
    last_name VARCHAR(100),
    organization_name VARCHAR(255),  -- Organizational providers
    taxonomy_code VARCHAR(10),
    specialty VARCHAR(100),
    subspecialty VARCHAR(100),
    
    -- Contact Info
    address_line1 VARCHAR(255),
    city VARCHAR(100),
    state CHAR(2),
    zip_code VARCHAR(10),
    phone VARCHAR(20),
    fax VARCHAR(20),
    email VARCHAR(255),
    
    -- Credentialing
    credential_status VARCHAR(20),  -- ACTIVE, SUSPENDED, TERMINATED
    board_certified BOOLEAN,
    license_state CHAR(2),
    license_number VARCHAR(50),
    license_expiry DATE,
    dea_number VARCHAR(20),  -- DEA for prescribing
    
    -- Quality
    quality_score DECIMAL(3,2),  -- 0.00-5.00
    patient_satisfaction DECIMAL(3,2),  -- 0.00-5.00
    claims_denial_rate DECIMAL(5,2),  -- %
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_nppes_sync TIMESTAMP
);

CREATE TABLE network_contracts (
    contract_id SERIAL PRIMARY KEY,
    npi VARCHAR(10) REFERENCES providers(npi),
    plan_id VARCHAR(20),
    network_tier INTEGER,  -- 1=Preferred, 2=Standard, 3=Out-of-Network
    effective_date DATE,
    termination_date DATE,
    contract_status VARCHAR(20),  -- ACTIVE, TERMED, PENDING
    reimbursement_rate DECIMAL(5,2),  -- % of Medicare
    accepts_new_patients BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT chk_network_tier CHECK (network_tier IN (1, 2, 3))
);

CREATE TABLE provider_specialties (
    provider_npi VARCHAR(10) REFERENCES providers(npi),
    specialty_code VARCHAR(10),
    specialty_name VARCHAR(100),
    is_primary BOOLEAN DEFAULT FALSE,
    board_certified BOOLEAN DEFAULT FALSE,
    certification_date DATE,
    recertification_date DATE
);

-- Indexes
CREATE INDEX idx_provider_name ON providers(last_name, first_name);
CREATE INDEX idx_provider_specialty ON providers(specialty);
CREATE INDEX idx_network_active ON network_contracts(npi, effective_date, termination_date) 
    WHERE contract_status = 'ACTIVE';
```

---

## API Specifications

### GET /api/v1/providers/{npi}
```json
Request:
GET /api/v1/providers/1234567893

Response:
{
  "npi": "1234567893",
  "entity_type": 1,
  "name": "Smith, John MD",
  "first_name": "John",
  "last_name": "Smith",
  "specialty": "Orthopedic Surgery",
  "taxonomy_code": "207X00000X",
  "address": {
    "line1": "456 Medical Plaza",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90024"
  },
  "phone": "+1-555-987-6543",
  "fax": "+1-555-987-6544",
  "credentialing": {
    "status": "ACTIVE",
    "board_certified": true,
    "license": {
      "state": "CA",
      "number": "A123456",
      "expiry": "2027-12-31"
    }
  },
  "quality": {
    "quality_score": 4.5,
    "patient_satisfaction": 4.7,
    "claims_denial_rate": 2.3
  }
}
```

### GET /api/v1/providers/{npi}/network-status
```json
Request:
GET /api/v1/providers/1234567893/network-status?plan_id=PLN-12345&service_date=2026-07-15

Response:
{
  "npi": "1234567893",
  "plan_id": "PLN-12345",
  "network_status": "IN_NETWORK",
  "network_tier": 1,
  "tier_name": "Preferred Provider",
  "effective_date": "2024-01-01",
  "termination_date": null,
  "accepts_new_patients": true,
  "member_cost_sharing": {
    "copay": 20.00,
    "coinsurance_rate": 0.10
  }
}
```

### POST /api/v1/providers/search
```json
Request:
{
  "specialty": "Orthopedic Surgery",
  "city": "Los Angeles",
  "state": "CA",
  "network_tier": 1,
  "accepts_new_patients": true,
  "within_miles": 10
}

Response:
{
  "results": [
    {
      "npi": "1234567893",
      "name": "Smith, John MD",
      "specialty": "Orthopedic Surgery",
      "distance_miles": 2.3,
      "quality_score": 4.5,
      "accepts_new_patients": true
    },
    ...
  ],
  "total_count": 15
}
```

---

## Business Rules

### Rule 1: NPPES NPI Validation
```yaml
Daily Sync:
  - Query NPPES NPI Registry API
  - Update provider demographic data
  - Flag deactivated NPIs
  - Validate license expiry dates

Validation:
  - Luhn algorithm checksum for NPI
  - Cross-check against NPPES
  - Alert if NPI not found in NPPES
```

### Rule 2: Network Tier Assignment
```yaml
Tier 1 (Preferred):
  - Cost-sharing: Lowest (copay $20, 10% coinsurance)
  - Quality score ≥4.0
  - Accepts new patients
  - Contracted reimbursement: 110% of Medicare

Tier 2 (Standard):
  - Cost-sharing: Medium (copay $40, 20% coinsurance)
  - Quality score ≥3.0
  - Contracted reimbursement: 100% of Medicare

Tier 3 (Out-of-Network):
  - Cost-sharing: Highest (copay $60, 40% coinsurance)
  - No contract
  - Reimbursement: 80% of Medicare (or billed charges)
```

### Rule 3: Credentialing Monitoring
```yaml
Alerts:
  - License expiring within 90 days → Provider notice
  - License expired → Suspend from network
  - Board certification lapsed → Downgrade to Tier 2
  - Quality score <3.0 → Performance improvement plan

Quarterly Review:
  - Verify active licenses
  - Check malpractice insurance
  - Review quality metrics
  - Update credentialing status
```

---

## Integration Points

- **External:** NPPES NPI Registry, state medical boards
- **Downstream:** All PA agents (Clinical, Benefits, etc.)
- **Upstream:** Contracting team (network updates)
- **Event Stream:** Kafka topic: provider.contract.updated

---

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| NPI Validation Accuracy | 100% | 100% |
| Network Status Accuracy | >99% | 99.5% |
| API Response Time (P95) | <50ms | 25ms |
| NPPES Sync Success Rate | >99% | 99.8% |

---

*Provider Service v2.8.0 - 8,500 Network Contracts*
