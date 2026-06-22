---
title: 04 Claims Service
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Claims Service - Comprehensive Documentation

## Claims Processing & Adjudication Service

**Version:** 4.2.0 | **Owner:** Claims Operations Team | **Status:** Production

## Overview

### Business Purpose
Processes medical claims, validates against PA authorizations, adjudicates payment amounts, and manages claim lifecycle from submission to payment.

**Key Capabilities:**
- Claim submission (X12 837)
- PA authorization validation
- Auto-adjudication (85% claims)
- Payment calculation
- EOB generation

**Business Impact:**
- Claims Processed: 150M annually
- Auto-Adjudication Rate: 85%
- Payment Accuracy: 99.4%
- Avg Processing Time: 2.3 days

### Technical Architecture

**Technologies:**
- Database: PostgreSQL 15 (claims)
- EDI: X12 837/835 processing
- Rules Engine: Payment adjudication logic
- Message Queue: Kafka (claim events)

---

## Database Schema

```sql
CREATE TABLE claims (
    claim_id VARCHAR(30) PRIMARY KEY,
    member_id VARCHAR(20),
    provider_npi VARCHAR(10),
    service_date DATE,
    submitted_date TIMESTAMP,
    claim_type VARCHAR(10),  -- PROFESSIONAL, INSTITUTIONAL, DENTAL, PHARMACY
    
    -- Financial
    billed_amount NUMERIC(10,2),
    allowed_amount NUMERIC(10,2),
    paid_amount NUMERIC(10,2),
    member_responsibility NUMERIC(10,2),
    
    -- PA Reference
    authorization_number VARCHAR(30),
    pa_case_id VARCHAR(30),
    
    -- Status
    claim_status VARCHAR(20),  -- RECEIVED, ADJUDICATED, PAID, DENIED, PENDED
    denial_reason VARCHAR(200),
    
    -- Processing
    adjudicated_date TIMESTAMP,
    paid_date TIMESTAMP,
    check_number VARCHAR(20),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE claim_lines (
    claim_line_id SERIAL PRIMARY KEY,
    claim_id VARCHAR(30) REFERENCES claims(claim_id),
    line_number INTEGER,
    procedure_code VARCHAR(10),  -- CPT/HCPCS
    diagnosis_codes TEXT[],  -- ICD-10
    units INTEGER,
    billed_amount NUMERIC(10,2),
    allowed_amount NUMERIC(10,2),
    paid_amount NUMERIC(10,2),
    denial_code VARCHAR(10)
);
```

---

## API Specifications

### POST /api/v1/claims/validate-authorization
```json
Request:
{
  "member_id": "M789456",
  "provider_npi": "1234567893",
  "service_date": "2026-07-15",
  "procedure_codes": ["27447"],
  "diagnosis_codes": ["M17.11"]
}

Response:
{
  "authorization_valid": true,
  "authorization_number": "AUTH-2026-987654",
  "approved_procedures": ["27447"],
  "valid_from": "2026-07-01",
  "valid_until": "2026-12-31",
  "remaining_units": 1,
  "estimated_payment": 18000.00,
  "member_responsibility": 2550.00
}
```

---

*Claims Service v4.2.0 - 150M Claims/Year*
