---
title: 01 Member Service
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Member Service - Comprehensive Documentation

## Member Enrollment & Demographics Service

**Version:** 3.1.0 | **Owner:** Member Data Team | **Status:** Production

## Overview

### Business Purpose
Centralized member enrollment database providing real-time member demographics, eligibility status, coverage details, and enrollment history for all PA processing.

**Key Capabilities:**
- Member lookup by ID, SSN, name+DOB
- Enrollment status verification
- Demographic data retrieval
- Dependent relationship validation
- Coverage tier management
- Enrollment history tracking

**Business Impact:**
- Data Accuracy: 99.97%
- API Availability: 99.98%
- Response Time: <20ms P95
- Daily Queries: 2M+ lookups

### Technical Architecture

**Technologies:**
- Database: PostgreSQL 15 (primary)
- Read Replicas: 3x for high availability
- Cache: Redis (60-second TTL)
- API: GraphQL + REST
- Authentication: OAuth 2.0 + mTLS

---

## Database Schema

```sql
CREATE TABLE members (
    member_id VARCHAR(20) PRIMARY KEY,
    ssn VARCHAR(11) ENCRYPTED,  -- AES-256 encrypted
    first_name VARCHAR(100),
    middle_name VARCHAR(50),
    last_name VARCHAR(100),
    dob DATE,
    sex CHAR(1),  -- M, F, X
    email VARCHAR(255),
    phone VARCHAR(20),
    preferred_language VARCHAR(10) DEFAULT 'EN',
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state CHAR(2),
    zip_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT chk_sex CHECK (sex IN ('M', 'F', 'X'))
);

CREATE TABLE enrollment (
    enrollment_id SERIAL PRIMARY KEY,
    member_id VARCHAR(20) REFERENCES members(member_id),
    plan_id VARCHAR(20) REFERENCES plans(plan_id),
    effective_date DATE NOT NULL,
    termination_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE, TERMED, SUSPENDED, GRACE_PERIOD
    coverage_tier VARCHAR(20),  -- INDIVIDUAL, FAMILY, EMPLOYEE_SPOUSE, EMPLOYEE_CHILDREN
    premium_status VARCHAR(20) DEFAULT 'PAID',  -- PAID, GRACE_PERIOD, LAPSED
    cobra_status VARCHAR(20),  -- ACTIVE_COBRA, NULL
    employer_group_id VARCHAR(20),
    subscriber_id VARCHAR(20),  -- If dependent, pointer to subscriber
    relationship VARCHAR(20),  -- SELF, SPOUSE, CHILD, PARTNER
    death_date DATE,
    CONSTRAINT chk_status CHECK (status IN ('ACTIVE', 'TERMED', 'SUSPENDED', 'GRACE_PERIOD', 'PENDING'))
);

CREATE TABLE dependents (
    dependent_id SERIAL PRIMARY KEY,
    subscriber_member_id VARCHAR(20) REFERENCES members(member_id),
    dependent_member_id VARCHAR(20) REFERENCES members(member_id),
    relationship VARCHAR(20),  -- SPOUSE, CHILD, PARTNER, OTHER
    effective_date DATE,
    termination_date DATE,
    student_status BOOLEAN DEFAULT FALSE,
    disabled_status BOOLEAN DEFAULT FALSE
);

-- Indexes for performance
CREATE INDEX idx_enrollment_member ON enrollment(member_id, effective_date, termination_date);
CREATE INDEX idx_enrollment_status ON enrollment(status) WHERE status = 'ACTIVE';
CREATE INDEX idx_members_dob ON members(last_name, first_name, dob);  -- Search by name+DOB
```

---

## API Specifications

### REST Endpoints

#### GET /api/v1/members/{member_id}
```json
Request:
GET /api/v1/members/M789456
Authorization: Bearer {token}

Response:
{
  "member_id": "M789456",
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1975-03-15",
  "sex": "M",
  "email": "john.doe@email.com",
  "phone": "+1-555-123-4567",
  "preferred_language": "EN",
  "address": {
    "line1": "123 Main St",
    "city": "Los Angeles",
    "state": "CA",
    "zip": "90001"
  },
  "enrollment": {
    "plan_id": "PLN-12345",
    "plan_name": "PPO Gold Plus",
    "effective_date": "2020-01-01",
    "status": "ACTIVE",
    "coverage_tier": "FAMILY"
  }
}
```

#### GET /api/v1/members/{member_id}/eligibility
```json
Request:
GET /api/v1/members/M789456/eligibility?service_date=2026-07-15

Response:
{
  "member_id": "M789456",
  "service_date": "2026-07-15",
  "eligible": true,
  "plan_id": "PLN-12345",
  "effective_date": "2020-01-01",
  "termination_date": null,
  "status": "ACTIVE",
  "premium_status": "PAID",
  "grace_period": false,
  "coverage_tier": "FAMILY"
}
```

#### GET /api/v1/members/{member_id}/dependents
```json
Response:
{
  "subscriber": "M789456",
  "dependents": [
    {
      "member_id": "M789457",
      "name": "Jane Doe",
      "relationship": "SPOUSE",
      "dob": "1977-08-22",
      "eligible": true
    },
    {
      "member_id": "M789458",
      "name": "Jimmy Doe",
      "relationship": "CHILD",
      "dob": "2010-05-10",
      "eligible": true,
      "student_status": true
    }
  ]
}
```

### GraphQL API

```graphql
query GetMemberDetails {
  member(memberId: "M789456") {
    memberId
    firstName
    lastName
    dob
    enrollment {
      planId
      planName
      effectiveDate
      status
    }
    dependents {
      memberId
      firstName
      relationship
    }
    cob {
      otherInsurance
      primaryPayer
      secondaryPayer
    }
  }
}
```

---

## Business Rules

### Rule 1: Member Lookup Priority
```yaml
Priority Order:
  1. member_id (exact match, fastest)
  2. SSN (unique, encrypted lookup)
  3. last_name + first_name + DOB (fuzzy match allowed)
  4. email (if unique)

Fuzzy Matching:
  - Soundex algorithm for name variations
  - Levenshtein distance ≤2 for typos
  - Return multiple matches if ambiguous
```

### Rule 2: Data Privacy (HIPAA)
```yaml
Access Controls:
  - PII fields encrypted at rest (SSN, address)
  - Audit all member lookups
  - PHI access requires authorized user
  - Redact SSN in logs (show last 4 digits only)

Encryption:
  - AES-256 for SSN
  - Column-level encryption in PostgreSQL
  - TLS 1.3 for data in transit
```

### Rule 3: Data Freshness
```yaml
Update Sources:
  - Real-time: Enrollment changes (new hires, terminations)
  - Daily batch: Demographic updates from HR feeds
  - Monthly: Audit reconciliation with employer groups

Caching:
  - Redis: 60-second TTL (eligibility lookups)
  - CDN: Static demographic data (name, DOB)
  - Invalidate cache on enrollment change
```

---

## Integration Points

- **Upstream:** Employer HR systems (EDI 834)
- **Downstream:** All PA agents (Eligibility, Benefits, etc.)
- **External:** Medicare CWF, State Medicaid MMIS
- **Event Stream:** Kafka topic: member.enrollment.changed

---

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| API Response Time (P95) | <50ms | 18ms |
| Availability | 99.9% | 99.98% |
| Data Accuracy | >99.9% | 99.97% |
| Cache Hit Rate | >80% | 87% |

---

*Member Service v3.1.0 - 2M+ Daily Lookups*
