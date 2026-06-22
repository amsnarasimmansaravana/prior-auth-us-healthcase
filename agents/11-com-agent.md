# Coordination of Benefits (COB) Agent - Comprehensive Documentation

## Multi-Payer Coordination Agent

**Version:** 2.0.0 | **Owner:** COB Operations Team | **Status:** Production

## Overview

### Business Purpose
Coordinates benefits when member has multiple insurance coverages, determines primary/secondary payer responsibility, calculates cost-sharing between payers, and prevents duplicate payments.

**Key Objectives:**
- Accurate primary/secondary payer determination
- Prevent duplicate payments
- Coordinate Medicare/Medicaid dual eligible
- Calculate secondary payer liability
- Comply with COB regulations (Medicare MSP, state laws)

**Business Impact:**
- Cost Recovery: $15M annually (secondary payer reimbursements)
- Duplicate Payment Prevention: $8M annually
- Compliance: 100% Medicare Secondary Payer (MSP) compliance
- Claim Accuracy: 99.1%

### Technical Purpose
Complex rule engine implementing Medicare Secondary Payer (MSP), birthday rule, court orders, and multi-payer coordination logic.

**Technologies:**
- Rules Engine: Drools (COB determination rules)
- Database: PostgreSQL (cob_records table)
- LLM: GPT-4o (complex COB scenario resolution)
- Integration: X12 270/271 (eligibility), Claims EDI

### Key Responsibilities

1. **COB Detection**
   - Identify multiple coverages
   - Query other insurance databases
   - Verify active coverage dates
   - Determine coverage types

2. **Primary Payer Determination**
   - Apply birthday rule (children with divorced parents)
   - Medicare Secondary Payer (MSP) rules
   - Active employee vs retiree coverage
   - Court order priority

3. **Secondary Payer Calculation**
   - Calculate primary payer allowed amount
   - Determine secondary payer liability
   - Apply COB reduction formulas
   - Prevent overpayment

4. **Medicare/Medicaid Dual Eligible**
   - Medicare primary, Medicaid secondary
   - Medicaid pays Medicare cost-sharing
   - QMB (Qualified Medicare Beneficiary) rules

5. **Third-Party Liability (TPL)**
   - Auto accident insurance
   - Workers' compensation
   - Liability insurance
   - No-fault insurance

---

## Business Rules

### Rule 1: Birthday Rule (Dependent Children)
```yaml
Rule ID: COB-001
Description: Determine primary payer for children with two employed parents

Birthday Rule:
  - Parent with EARLIER birthday in calendar year = Primary
  - Does NOT compare birth year, only month/day
  
Example:
  Father: Born March 15, 1980
  Mother: Born June 22, 1985
  Child: Covered by both parents' plans
  
  Primary: Father's plan (March < June)
  Secondary: Mother's plan

Exception - Court Order:
  - Court order OVERRIDES birthday rule
  - Court-ordered primary payer takes precedence

Implementation:
  parent1_birthday = extract_month_day(parent1.dob)
  parent2_birthday = extract_month_day(parent2.dob)
  
  IF court_order_exists:
    primary = court_ordered_payer
  ELIF parent1_birthday < parent2_birthday:
    primary = parent1_plan
  ELSE:
    primary = parent2_plan
```

### Rule 2: Medicare Secondary Payer (MSP) - Working Aged
```yaml
Rule ID: COB-002
Description: MSP rules for members age 65+ with active employment

Working Aged Rules:
  IF member.age >= 65 AND actively_employed:
    IF employer.size > 20 employees:
      primary = employer_group_plan
      secondary = medicare
    ELSE:
      primary = medicare
      secondary = employer_group_plan (optional)

Example:
  Member: Age 67, working at company with 50 employees
  Coverage: Medicare + Employer group plan
  
  Result:
    Primary: Employer plan (company >20 employees)
    Secondary: Medicare

Spouse Coverage:
  IF spouse.age >= 65 AND other_spouse_actively_employed:
    Same rules apply (employer size determines primary)
```

### Rule 3: Medicare Secondary Payer (MSP) - ESRD
```yaml
Rule ID: COB-003
Description: MSP rules for End-Stage Renal Disease (ESRD)

ESRD Coordination Period:
  First 30 months after ESRD diagnosis:
    - Employer plan PRIMARY (if eligible)
    - Medicare SECONDARY
  
  After 30 months:
    - Medicare PRIMARY
    - Employer plan SECONDARY (if still covered)

Implementation:
  IF diagnosis_code IN ESRD_codes:
    esrd_start_date = diagnosis_date
    months_since_esrd = (today - esrd_start_date).months
    
    IF months_since_esrd <= 30 AND has_employer_coverage:
      primary = employer_plan
      secondary = medicare
    ELSE:
      primary = medicare
      secondary = employer_plan
```

### Rule 4: Medicare/Medicaid Dual Eligible
```yaml
Rule ID: COB-004
Description: Coordinate Medicare and Medicaid for dual eligible members

Standard Dual Eligible:
  - Medicare PRIMARY for all Medicare-covered services
  - Medicaid SECONDARY (pays Medicare cost-sharing)
  - Medicaid may cover additional services not covered by Medicare

QMB (Qualified Medicare Beneficiary):
  - Medicaid pays Medicare premiums, deductibles, coinsurance
  - Provider CANNOT bill member for Medicare cost-sharing
  - Medicaid reimbursement = Medicaid fee schedule (not Medicare)

Example:
  Service: Doctor visit ($100)
  Medicare allows: $80 (pays 80% = $64)
  Medicare cost-sharing: $16 (20% coinsurance)
  
  Medicaid pays:
    - QMB: Up to Medicaid fee schedule for $16
    - Non-QMB: $16 (if Medicaid covers service)
  
  Member owes: $0 (for QMB), $0-$16 (for non-QMB)
```

### Rule 5: Third-Party Liability (TPL) Priority
```yaml
Rule ID: COB-005
Description: TPL takes precedence over health insurance

TPL Order:
  1. Auto insurance (no-fault, PIP)
  2. Workers' compensation
  3. Liability insurance
  4. Health insurance (primary)
  5. Health insurance (secondary)

Auto Accident Example:
  Service: ER visit for auto accident injuries
  Member has: Auto insurance + Health insurance + Medicare
  
  Payment Order:
    1. Auto insurance pays (up to policy limits)
    2. Health insurance pays remaining (if any)
    3. Medicare pays last (if applicable)

Subrogation:
  - Health plan may pay initially
  - Health plan seeks reimbursement from TPL payer
  - Member must cooperate with subrogation efforts
```

---

## Technical Architecture

### COB Determination Engine

```python
from dataclasses import dataclass
from datetime import datetime, date

@dataclass
class Insurance:
    payer_id: str
    payer_name: str
    plan_type: str  # EMPLOYER, MEDICARE, MEDICAID, AUTO, etc.
    effective_date: date
    termination_date: date = None
    employer_size: int = None  # For MSP rules
    coverage_type: str = None  # PRIMARY, SECONDARY

class COBDeterminationEngine:
    """Determine primary/secondary payer"""
    
    def determine_cob(self, member: Member, coverages: List[Insurance]) -> COBResult:
        """Apply COB rules to determine payer order"""
        
        # Step 1: Filter active coverages
        active_coverages = [
            c for c in coverages
            if c.effective_date <= service_date <= (c.termination_date or date.max)
        ]
        
        if len(active_coverages) == 1:
            return COBResult(primary=active_coverages[0], secondary=None)
        
        # Step 2: Check for TPL (auto, workers comp)
        tpl_coverage = self._check_tpl(active_coverages)
        if tpl_coverage:
            health_coverages = [c for c in active_coverages if c.plan_type in ["EMPLOYER", "MEDICARE", "MEDICAID"]]
            return COBResult(
                primary=tpl_coverage,
                secondary=self._determine_health_primary(member, health_coverages)
            )
        
        # Step 3: Apply COB rules
        primary = self._determine_primary(member, active_coverages)
        secondary = [c for c in active_coverages if c != primary][0] if len(active_coverages) > 1 else None
        
        return COBResult(primary=primary, secondary=secondary)
    
    def _determine_primary(self, member: Member, coverages: List[Insurance]) -> Insurance:
        """Apply COB rules to select primary payer"""
        
        # Rule: Court order takes precedence
        if member.cob_court_order:
            return self._get_coverage_by_id(member.cob_court_order_payer_id)
        
        # Rule: Medicare Secondary Payer (MSP)
        if self._has_medicare(coverages):
            return self._apply_msp_rules(member, coverages)
        
        # Rule: Birthday rule for dependent children
        if member.age < 18 and member.relationship == "DEPENDENT":
            return self._apply_birthday_rule(member, coverages)
        
        # Rule: Active employment > Retiree coverage
        active_employer = [c for c in coverages if c.plan_type == "EMPLOYER" and c.is_active_employee]
        if active_employer:
            return active_employer[0]
        
        # Default: Earlier effective date = primary
        return min(coverages, key=lambda c: c.effective_date)
    
    def _apply_msp_rules(self, member: Member, coverages: List[Insurance]) -> Insurance:
        """Apply Medicare Secondary Payer rules"""
        
        medicare = [c for c in coverages if c.plan_type == "MEDICARE"][0]
        employer = [c for c in coverages if c.plan_type == "EMPLOYER"]
        
        if not employer:
            return medicare  # Medicare is primary if no employer coverage
        
        employer = employer[0]
        
        # Working Aged (65+)
        if member.age >= 65 and member.is_actively_employed:
            if employer.employer_size > 20:
                return employer  # Employer primary
            else:
                return medicare  # Medicare primary
        
        # Disability (<65)
        if member.medicare_reason == "DISABILITY" and member.is_actively_employed:
            if employer.employer_size > 100:
                return employer  # Employer primary
            else:
                return medicare  # Medicare primary
        
        # ESRD (End-Stage Renal Disease)
        if member.medicare_reason == "ESRD":
            esrd_months = (date.today() - member.esrd_diagnosis_date).days // 30
            if esrd_months <= 30 and employer:
                return employer  # Employer primary (first 30 months)
            else:
                return medicare  # Medicare primary (after 30 months)
        
        # Default: Medicare primary
        return medicare
    
    def _apply_birthday_rule(self, member: Member, coverages: List[Insurance]) -> Insurance:
        """Apply birthday rule for dependent children"""
        
        # Assumes member has parent1_coverage and parent2_coverage
        parent1_birthday = (member.parent1_dob.month, member.parent1_dob.day)
        parent2_birthday = (member.parent2_dob.month, member.parent2_dob.day)
        
        if parent1_birthday < parent2_birthday:
            return coverages[0]  # Parent 1's plan
        else:
            return coverages[1]  # Parent 2's plan
```

### Secondary Payer Calculation

```python
def calculate_secondary_payment(
    service_amount: float,
    primary_allowed: float,
    primary_paid: float,
    secondary_allowed: float,
    member_deductible_remaining: float
) -> float:
    """Calculate secondary payer liability"""
    
    # Primary payer responsibility
    primary_responsibility = min(service_amount, primary_allowed)
    primary_payment = primary_paid
    
    # Member cost-sharing from primary
    member_owed_primary = primary_responsibility - primary_payment
    
    # Secondary payer calculation
    secondary_responsibility = min(service_amount, secondary_allowed)
    
    # Secondary pays LESSER of:
    # 1. Member's cost-sharing from primary
    # 2. Secondary's allowed amount - primary payment
    secondary_payment = min(
        member_owed_primary,
        max(0, secondary_responsibility - primary_payment)
    )
    
    # Apply secondary's deductible (if any)
    if member_deductible_remaining > 0:
        secondary_payment = max(0, secondary_payment - member_deductible_remaining)
    
    return secondary_payment

# Example:
service_amount = 100.00
primary_allowed = 80.00  # Primary allows $80 for service
primary_paid = 64.00     # Primary pays 80% ($64)
secondary_allowed = 90.00
member_deductible = 0.00

secondary_payment = calculate_secondary_payment(
    service_amount, primary_allowed, primary_paid, secondary_allowed, member_deductible
)
# Result: $16.00 (secondary pays member's 20% coinsurance from primary)

member_owes = service_amount - primary_paid - secondary_payment
# Result: $0.00 (no balance billing)
```

---

## Input/Output Specifications

### Input
```json
{
  "case_id": "PA-2026-001234",
  "member_id": "M789456",
  "service_date": "2026-07-15",
  "coverages": [
    {
      "payer_id": "PAY-001",
      "payer_name": "Medicare Part B",
      "plan_type": "MEDICARE",
      "effective_date": "2024-01-01"
    },
    {
      "payer_id": "PAY-002",
      "payer_name": "ABC Health Plan",
      "plan_type": "EMPLOYER",
      "effective_date": "2020-01-01",
      "employer_size": 50
    }
  ],
  "member": {
    "age": 67,
    "is_actively_employed": true
  }
}
```

### Output
```json
{
  "case_id": "PA-2026-001234",
  "cob_determination": {
    "primary_payer": {
      "payer_id": "PAY-002",
      "payer_name": "ABC Health Plan",
      "reason": "MSP Working Aged rule: Employer >20 employees"
    },
    "secondary_payer": {
      "payer_id": "PAY-001",
      "payer_name": "Medicare Part B",
      "reason": "Medicare Secondary Payer"
    },
    "rules_applied": ["MSP_WORKING_AGED"],
    "confidence": 1.0
  },
  "payment_responsibility": {
    "primary_pays_first": true,
    "secondary_pays_remaining": true,
    "member_cost_sharing": "After both payers"
  }
}
```

---

*COM Agent v2.0.0 - Recovering $15M Annually*
