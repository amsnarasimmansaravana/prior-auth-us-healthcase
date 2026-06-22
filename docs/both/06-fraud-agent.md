---
title: 06 Fraud Agent
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Fraud Detection Agent - Comprehensive Documentation

## Fraud, Waste, & Abuse Detection Agent

**Version:** 2.3.0 | **Owner:** SIU (Special Investigations Unit) | **Status:** Production

## Overview

### Business Purpose
Detects fraudulent PA requests, identifies patterns of abuse, and prevents improper payments through graph analytics, anomaly detection, and ML models.

**Key Objectives:**
- Detect provider fraud patterns (billing schemes, upcoding)
- Identify member collusion
- Prevent duplicate services
- Flag suspicious patterns
- Support SIU investigations

**Business Impact:**
- Fraud Prevention: $32M annually
- False Positive Rate: 2.1% (low)
- Investigative Leads: 1,200/year
- Prosecution Support: 85% conviction rate when prosecuted

### Technical Purpose
Graph database analytics with ML anomaly detection, identifying fraud rings and suspicious behavioral patterns.

**Technologies:**
- Graph Database: Neo4j (fraud network analysis)
- ML Models: Isolation Forest, LSTM (anomaly detection)
- LLM: GPT-4o (narrative analysis, pattern explanation)
- Time-Series DB: InfluxDB (billing pattern tracking)
- Alert System: PagerDuty (high-severity fraud alerts)

### Key Responsibilities

1. **Provider Fraud Detection**
   - Billing schemes (unbundling, upcoding)
   - Phantom billing (services not rendered)
   - Kickback relationships
   - License fraud (practicing without valid license)

2. **Member Collusion**
   - Identity theft
   - Shared member IDs
   - Fake injuries
   - Drug diversion schemes

3. **Network Analysis**
   - Fraud rings (connected providers/members)
   - Referral kickback networks
   - Shell corporations
   - Geographic clustering of fraud

4. **Anomaly Detection**
   - Statistical outliers (billing >3σ from mean)
   - Temporal patterns (billing spikes)
   - Behavioral changes
   - Duplicate services

5. **Regulatory Violations**
   - Stark Law violations (physician self-referral)
   - Anti-Kickback Statute
   - HIPAA violations
   - False Claims Act

---

## Business Rules

### Rule 1: Unbundling Detection
```yaml
Rule ID: FRD-001
Description: Detect unbundling of bundled procedures

Unbundling:
  Instead of billing bundled code 99213 (office visit)
  Provider bills:
    - 99211 (brief visit)
    - 36415 (venipuncture)
    - 93000 (EKG)
  Total: $150 vs $75 for bundled code

Detection:
  - Identify CPT codes billed separately on same date
  - Check CCI (Correct Coding Initiative) edits
  - Flag if separate billing > bundled rate by >20%

Action:
  IF unbundling_detected:
    fraud_score += 0.30
    alert_siu = True if fraud_score > 0.70
```

### Rule 2: Phantom Billing
```yaml
Rule ID: FRD-002
Description: Detect services billed but not rendered

Indicators:
  - Member claims they never saw provider
  - Service date when member was hospitalized elsewhere
  - Provider bills for deceased patient
  - Billing for >24 hours of service in one day

Verification:
  - Cross-check with claims database
  - Verify member was not admitted elsewhere on date
  - Check death records
  - Validate time-based codes (E/M levels)

Action:
  IF phantom_billing_suspected:
    fraud_score += 0.50
    require_medical_records = True
    investigate_provider_billing_history = True
```

### Rule 3: Fraud Network Detection (Graph)
```yaml
Rule ID: FRD-003
Description: Identify connected fraud rings using Neo4j

Graph Pattern:
  Provider A → refers to → Provider B → refers to → Provider C
  All billing for same diagnosis
  All for same patients
  Abnormally high referral rate

Detection Query (Cypher):
  MATCH (p1:Provider)-[:REFERS]->(p2:Provider)-[:REFERS]->(p3:Provider)
  WHERE p1.npi <> p3.npi
  AND count(DISTINCT patient) > 10
  AND p1.specialty <> p2.specialty
  RETURN p1, p2, p3, count(*) as referral_count
  HAVING referral_count > 20

Alert:
  IF circular_referral_pattern:
    fraud_score += 0.40
    flag_for_siu_investigation = True
```

### Rule 4: Geographic Clustering
```yaml
Rule ID: FRD-004
Description: Detect geographically impossible service patterns

Impossible Patterns:
  - Patient seen by providers in different cities on same day
  - Provider billing from multiple locations simultaneously
  - Member receiving services 500+ miles apart within hours

Example:
  10 AM: Service in Los Angeles
  2 PM: Service in San Francisco (400 miles away)
  
Action:
  IF geographic_anomaly:
    fraud_score += 0.35
    require_proof_of_service = True
    cross_check_provider_location = True
```

### Rule 5: Outlier Detection (Statistical)
```yaml
Rule ID: FRD-005
Description: Identify statistical outliers in billing patterns

Metrics:
  - Billing per member per month (PMPM)
  - Services per patient
  - Cost per service
  - Approval rate

Outlier Detection:
  Mean PMPM for specialty: $250
  StdDev: $50
  Provider X PMPM: $450 (4σ above mean)

Action:
  IF billing > (mean + 3*stddev):
    fraud_score += 0.25
    require_peer_comparison = True
    audit_sample_of_claims = True
```

---

## Technical Architecture

### Neo4j Graph Schema

```cypher
// Nodes
CREATE (p:Provider {
    npi: "1234567893",
    name: "Dr. Smith",
    specialty: "Orthopedic Surgery",
    license_state: "CA",
    license_expiry: "2027-12-31",
    fraud_score: 0.0
})

CREATE (m:Member {
    member_id: "M789456",
    dob: "1975-03-15",
    address: "123 Main St, LA, CA"
})

CREATE (c:Claim {
    claim_id: "CLM-001",
    service_date: "2026-06-01",
    procedure_codes: ["27447"],
    billed_amount: 25000.00,
    allowed_amount: 18000.00
})

// Relationships
CREATE (p)-[:TREATED {service_date: "2026-06-01"}]->(m)
CREATE (p)-[:BILLED]->(c)
CREATE (p1:Provider)-[:REFERS {referral_count: 25}]->(p2:Provider)

// Fraud Ring Detection Query
MATCH (p1:Provider)-[r:REFERS]->(p2:Provider)
WHERE r.referral_count > 20
AND p1.specialty <> p2.specialty
MATCH (p1)-[:TREATED]->(m:Member)<-[:TREATED]-(p2)
WHERE m.total_services > 50  // High utilization
RETURN p1, p2, count(m) as shared_patients, sum(m.total_cost) as total_cost
ORDER BY total_cost DESC
```

### ML Anomaly Detection

```python
from sklearn.ensemble import IsolationForest
import numpy as np

class FraudAnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.05,  # Expect 5% fraud rate
            random_state=42
        )
    
    def detect_anomalies(self, provider_metrics):
        """
        Detect anomalous providers using Isolation Forest
        
        Features:
        - billing_pmpm: Billing per member per month
        - approval_rate: % of PA requests approved
        - services_per_patient: Avg services per patient
        - cost_per_service: Avg cost per service
        - referral_rate: % of patients referred out
        """
        
        features = np.array([
            [p['billing_pmpm'], 
             p['approval_rate'],
             p['services_per_patient'],
             p['cost_per_service'],
             p['referral_rate']]
            for p in provider_metrics
        ])
        
        # Train model
        self.model.fit(features)
        
        # Predict anomalies (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(features)
        
        # Calculate anomaly scores
        anomaly_scores = self.model.score_samples(features)
        
        anomalies = []
        for i, (pred, score) in enumerate(zip(predictions, anomaly_scores)):
            if pred == -1:  # Anomaly detected
                anomalies.append({
                    'provider_npi': provider_metrics[i]['npi'],
                    'anomaly_score': abs(score),  # Lower score = more anomalous
                    'reason': self._explain_anomaly(provider_metrics[i])
                })
        
        return sorted(anomalies, key=lambda x: x['anomaly_score'])
    
    def _explain_anomaly(self, provider):
        """Generate human-readable explanation"""
        reasons = []
        
        if provider['billing_pmpm'] > 500:
            reasons.append(f"High billing PMPM: ${provider['billing_pmpm']}")
        
        if provider['approval_rate'] > 0.95:
            reasons.append(f"Suspiciously high approval rate: {provider['approval_rate']*100}%")
        
        if provider['services_per_patient'] > 20:
            reasons.append(f"High services per patient: {provider['services_per_patient']}")
        
        return "; ".join(reasons)
```

---

## Input/Output Specifications

### Input
```json
{
  "case_id": "PA-2026-001234",
  "provider_npi": "1234567893",
  "member_id": "M789456",
  "service_date": "2026-07-15",
  "procedure_codes": ["27447"],
  "diagnosis_codes": ["M17.11"],
  "billed_amount": 25000.00
}
```

### Output
```json
{
  "case_id": "PA-2026-001234",
  "fraud_risk_score": 0.15,
  "risk_level": "LOW",
  "fraud_indicators": [],
  "network_analysis": {
    "fraud_ring_detected": false,
    "connected_providers": 0,
    "suspicious_referral_patterns": false
  },
  "anomaly_detection": {
    "provider_anomaly_score": 0.05,
    "member_anomaly_score": 0.02,
    "outlier_status": "NORMAL"
  },
  "recommendations": [],
  "siu_alert_required": false,
  "processing_time_ms": 450
}
```

---

## Integration Points

- **Graph DB:** Neo4j (fraud networks)
- **ML Platform:** Azure ML (anomaly models)
- **Alert System:** PagerDuty (SIU alerts)
- **Upstream:** All agents (fraud check on every case)
- **Downstream:** Decision Agent, SIU case management system

---

## Monitoring

- Fraud detection rate: 2.8% of cases flagged
- False positive rate: 2.1%
- SIU conversion rate: 35% (flagged cases → investigations)
- Prevented fraud: $32M/year

---

*Fraud Agent v2.3.0 - Protecting $32M Annually*
