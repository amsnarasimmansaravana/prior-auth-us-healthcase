---
title: 01 Intake Agent
status: draft
owner: TODO
type: both
last_updated: 2026-06-22
version: 1.0.0
tags: []
---

# Intake Agent - Comprehensive Technical Documentation

## Document Classification & Information Extraction Agent

**Version:** 2.3.1  
**Last Updated:** June 1, 2026  
**Owner:** AI Platform Team  
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

The Intake Agent serves as the critical entry point for all Prior Authorization (PA) and Claims requests entering the Healthcare Insurance Multi-Agent AI Platform. It transforms unstructured, multi-format submissions (EDI, fax, portal, API) into standardized, machine-readable case records that downstream agents can process efficiently.

**Key Business Objectives:**
- **Reduce Manual Data Entry:** Eliminate 95% of manual intake processing
- **Improve Accuracy:** Achieve 98%+ data extraction accuracy (vs 85% manual)
- **Accelerate Processing:** Reduce intake time from 15 minutes to 30 seconds
- **Handle Multiple Formats:** Support EDI X12 278, fax, PDF, web forms, FHIR API
- **Enable Straight-Through Processing (STP):** Auto-route 80% of clean submissions

**Business Impact:**
- **Cost Savings:** $25.3M annually (450 FTEs → 50 FTEs)
- **Volume Capacity:** Handle 50,000+ PAs/day with auto-scaling
- **Provider Satisfaction:** Immediate acknowledgment vs 4-hour delay
- **Compliance:** 100% HIPAA audit trail from submission point

### Technical Purpose

The Intake Agent is a specialized AI agent powered by GPT-4o with vision capabilities, designed to:

1. **Document Classification:** Identify document type (PA request, claim, appeal, clinical notes)
2. **OCR Processing:** Extract text from scanned faxes and PDFs with 99% accuracy
3. **Entity Extraction:** Parse structured data (member ID, diagnosis codes, procedure codes, provider NPI)
4. **Validation:** Ensure completeness and correctness before case creation
5. **Normalization:** Convert diverse input formats into unified schema
6. **Case Creation:** Generate unique case ID and initialize workflow state

**Core Technologies:**
- **LLM:** GPT-4o (vision-enabled for OCR)
- **Embedding Model:** text-embedding-3-large
- **OCR Engine:** Azure Form Recognizer + GPT-4o Vision
- **Schema Validation:** Pydantic v2
- **Document Store:** Azure Blob Storage (Hot tier)
- **Metadata Store:** PostgreSQL (cases table)

### Key Responsibilities

#### Primary Responsibilities (Core Function)

1. **Multi-Channel Intake Processing**
   - EDI X12 278 (Prior Authorization Request/Response)
   - HL7 FHIR R4 API (CoverageEligibilityRequest)
   - Web Portal Submissions (React SPA)
   - Fax Server Integration (OCR required)
   - Email Attachments (auto-forwarded to intake queue)
   - IVR/Phone Submissions (speech-to-text transcripts)

2. **Document Classification & Routing**
   - Classify as: PA Request, Claim, Appeal, Grievance, Member Inquiry
   - Sub-classify PA urgency: URGENT (24h) vs STANDARD (72h)
   - Identify specialty: Cardiology, Oncology, Orthopedics, etc.
   - Route to appropriate workflow based on classification

3. **Intelligent Data Extraction**
   - **Member Information:** ID, Name, DOB, Address, Phone, Email
   - **Provider Information:** NPI, Name, TIN, Specialty, Contact
   - **Clinical Information:** Diagnosis codes (ICD-10), Procedure codes (CPT/HCPCS), Clinical summary
   - **Administrative Information:** Requested service date, Authorization period, Urgency flag
   - **Supporting Documents:** Clinical notes, imaging reports, lab results, physician letters

4. **Data Quality Validation**
   - Required fields present (member ID, diagnosis, procedure)
   - Format validation (NPI: 10 digits, DOB: YYYY-MM-DD, ICD-10 format)
   - Code validity (diagnosis/procedure codes exist in databases)
   - Referential integrity (member exists in enrollment DB)
   - Logical validation (service date in future, diagnosis matches procedure)

5. **Case Initialization**
   - Generate unique case ID (e.g., PA-2026-001234)
   - Set initial status: INTAKE_COMPLETE
   - Assign to queue based on urgency and specialty
   - Calculate SLA deadline (URGENT: 24h, STANDARD: 72h)
   - Trigger downstream agents (Eligibility, Fraud)

#### Secondary Responsibilities (Supporting Function)

6. **Missing Information Detection**
   - Identify incomplete submissions
   - Generate deficiency letter (what's missing)
   - Auto-request additional info from provider via portal/fax
   - Set case status: PENDING_MORE_INFO
   - Track response timeline (7-day deadline)

7. **Duplicate Detection**
   - Check for duplicate submissions (same member + procedure + date)
   - Link to existing case if found
   - Prevent duplicate processing and billing
   - Alert provider of existing case

8. **Audit Trail Creation**
   - Log submission timestamp and channel
   - Capture original documents (immutable copy)
   - Record all extracted entities with confidence scores
   - Document validation results (pass/fail per field)
   - Store for 10 years (regulatory requirement)

9. **Real-Time Provider Feedback**
   - Immediate acknowledgment with case ID
   - Validation errors returned instantly
   - Expected completion time provided
   - Portal link to track status

10. **Analytics & Reporting**
    - Track submission volume by channel
    - Monitor extraction accuracy by document type
    - Identify common data quality issues
    - Report provider-specific patterns (frequent errors)

### Success Metrics

#### Operational Metrics

| Metric | Target | Current | Measurement |
|--------|--------|---------|-------------|
| **Processing Time** | <30 seconds | 25 seconds avg | P95 latency |
| **Extraction Accuracy** | >98% | 98.7% | Human validation sample |
| **OCR Accuracy** | >99% | 99.2% | Character-level accuracy |
| **Completeness Rate** | >85% | 87% | % with all required fields |
| **Straight-Through Processing** | >80% | 82% | % auto-approved intake |
| **Manual Review Rate** | <20% | 18% | % requiring human touch |

#### Business Metrics

| Metric | Target | Current | Annual Impact |
|--------|--------|---------|---------------|
| **Cost per Case** | $1.50 | $1.40 | $54.8M savings |
| **FTE Reduction** | 89% | 89% | 400 FTEs eliminated |
| **Provider Satisfaction** | >85% | 88% | NPS improvement +15 |
| **Intake Errors** | <2% | 1.8% | 98.2% accuracy |

#### Quality Metrics

| Metric | Target | Current | Measurement |
|--------|--------|---------|-------------|
| **False Positives** | <1% | 0.8% | Incorrectly extracted data |
| **False Negatives** | <2% | 1.5% | Missed required fields |
| **Confidence Score** | >0.95 | 0.96 | Average across extractions |
| **Human Override Rate** | <5% | 4.2% | Manual corrections needed |

#### AI Performance Metrics

| Metric | Target | Current | Measurement |
|--------|--------|---------|-------------|
| **Hallucination Rate** | <1% | 0.3% | Fabricated data detected |
| **Grounding Score** | >0.95 | 0.97 | Evidence-based extraction |
| **Token Usage** | <3000/case | 2800/case | Cost optimization |
| **Model Drift** | <0.05 KL | 0.03 KL | Distribution stability |

### Integration Points

**Upstream Dependencies:**
- Provider Portal (React + Next.js)
- EDI Gateway (X12 Parser)
- Fax Server (Azure Communication Services)
- FHIR API Gateway (HAPI FHIR)
- Email Server (Exchange/O365)

**Downstream Consumers:**
- Eligibility Agent
- Fraud Agent
- Audit Agent
- SLA Engine
- Case Management System

**External Integrations:**
- Azure Form Recognizer (OCR)
- OpenAI API (GPT-4o)
- Azure Blob Storage (Document Store)
- PostgreSQL (Case Database)
- Redis (Working Memory)
- Kafka (Event Bus)

---

## Business Rules

### Document Acceptance Rules

#### Rule 1: Required Fields for PA Request
```yaml
Rule ID: INTAKE-001
Severity: CRITICAL
Description: All PA requests must contain minimum required fields

Required Fields:
  Member Information:
    - Member ID (must exist in enrollment DB)
    - Member Name (First + Last)
    - Date of Birth (format: YYYY-MM-DD)
  
  Provider Information:
    - Provider NPI (10-digit number)
    - Provider Name
    - Provider Specialty
  
  Clinical Information:
    - At least 1 Diagnosis Code (ICD-10 format)
    - At least 1 Procedure Code (CPT/HCPCS format)
    - Clinical Justification (text, min 20 characters)
  
  Administrative:
    - Requested Service Date (must be future date or <30 days past)
    - Authorization Period (days, must be >0)

Action if Missing:
  - Status: INCOMPLETE
  - Generate: Deficiency Letter
  - Send to: Provider Portal + Email + Fax
  - Deadline: 7 days to respond
  - Auto-Deny if: No response after 14 days
```

#### Rule 2: Urgency Classification
```yaml
Rule ID: INTAKE-002
Severity: HIGH
Description: Classify PA urgency based on clinical indicators

URGENT Classification (24-hour SLA):
  Keywords in Clinical Notes:
    - "emergency"
    - "urgent"
    - "stat"
    - "life-threatening"
    - "acute"
    - "immediately"
  
  Diagnosis Codes:
    - I21.* (Acute myocardial infarction)
    - I60-I62 (Intracranial hemorrhage)
    - C00-C97 (Malignant neoplasms - if treatment delay >1 week)
    - T36-T50 (Poisoning)
  
  Procedure Codes:
    - 33510-33536 (CABG - Coronary artery bypass)
    - 01967 (Neuroangiography)
    - 99281-99285 (Emergency department visits)

STANDARD Classification (72-hour SLA):
  - All other requests not meeting URGENT criteria

Action:
  - Set SLA Deadline based on classification
  - Priority Queue assignment (URGENT gets top priority)
  - Notification: URGENT cases alert on-call clinical reviewer
```

#### Rule 3: Document Quality Thresholds
```yaml
Rule ID: INTAKE-003
Severity: MEDIUM
Description: Accept/reject documents based on quality

Minimum OCR Confidence: 85%
  - If <85%: Route to manual review
  - If <60%: Reject and request re-submission

Minimum Page Clarity:
  - Resolution: ≥200 DPI
  - If <200 DPI: Request higher quality scan

Maximum Document Size: 50 MB
  - If >50 MB: Reject with error message

Supported Formats:
  - PDF, JPG, PNG, TIFF
  - Unsupported: BMP, GIF, RAW

Action on Rejection:
  - Immediate feedback to provider
  - Specific reason for rejection
  - Instructions to re-submit
```

### Validation Business Rules

#### Rule 4: Member Eligibility Pre-Check
```yaml
Rule ID: INTAKE-004
Severity: CRITICAL
Description: Basic eligibility check during intake

Checks:
  1. Member ID exists in enrollment database
  2. Member has active coverage on requested service date
  3. Member is not deceased
  4. Member is not termed (terminated coverage)

Action if Failed:
  - Status: REJECTED_INELIGIBLE
  - Do Not Create Case
  - Immediate notification to provider
  - Reason: "Member not eligible for benefits"

Exception:
  - If service date is >90 days in future: Skip check (eligibility may change)
```

#### Rule 5: Diagnosis-Procedure Alignment
```yaml
Rule ID: INTAKE-005
Severity: MEDIUM
Description: Ensure diagnosis supports requested procedure

Examples of Valid Alignments:
  - Diagnosis: M17.11 (Knee osteoarthritis) → Procedure: 27447 (Knee replacement) ✓
  - Diagnosis: I25.10 (Coronary artery disease) → Procedure: 33533 (CABG) ✓
  - Diagnosis: C50.911 (Breast cancer) → Procedure: 19307 (Mastectomy) ✓

Examples of Invalid Alignments:
  - Diagnosis: J45.909 (Asthma) → Procedure: 27447 (Knee replacement) ✗
  - Diagnosis: E11.9 (Type 2 diabetes) → Procedure: 19307 (Mastectomy) ✗

Detection Method:
  - Clinical Knowledge Graph lookup
  - ICD-10 → CPT mapping database
  - LLM clinical reasoning (GPT-4o)

Action if Misaligned:
  - Confidence Score <0.7: Flag for clinical review
  - Status: PENDING_CLINICAL_VALIDATION
  - Request: Clarification from provider
```

#### Rule 6: Duplicate Detection Logic
```yaml
Rule ID: INTAKE-006
Severity: HIGH
Description: Prevent duplicate case creation

Duplicate Criteria (ALL must match):
  - Same Member ID
  - Same Procedure Code
  - Same Service Date (±3 days)
  - Submitted within last 90 days

Action on Duplicate Detected:
  - Do NOT create new case
  - Link to existing case ID
  - Notification: "Duplicate submission - Case ID: PA-2026-XXXXXX"
  - Log: Duplicate attempt in audit trail

Exception:
  - If previous case status = DENIED, allow re-submission (appeal)
  - If previous case status = EXPIRED, allow re-submission (renewal)
```

### Data Quality Rules

#### Rule 7: NPI Validation
```yaml
Rule ID: INTAKE-007
Severity: CRITICAL
Description: Validate provider NPI

Validation Steps:
  1. Format: Exactly 10 numeric digits
  2. Luhn Algorithm Check (checksum validation)
  3. NPI Registry Lookup (NPPES database)
  4. Active status in registry
  5. Specialty matches request type

Action if Invalid:
  - Status: INVALID_PROVIDER
  - Request: Valid NPI from provider
  - Auto-Suggest: NPI based on provider name lookup

Example:
  Valid NPI: 1234567893 (passes Luhn check)
  Invalid NPI: 1234567890 (fails Luhn check)
```

#### Rule 8: Date Logic Validation
```yaml
Rule ID: INTAKE-008
Severity: HIGH
Description: Validate all dates for logical consistency

Checks:
  1. Service Date:
     - Must be ≥ Today OR ≤ 30 days in past
     - Cannot be >365 days in future
     - If past date: Must have clinical justification

  2. Date of Birth:
     - Must be in past
     - Member age must be ≥0 and ≤120 years
     - Pediatric procedures: Age <18
     - Geriatric procedures: Age >65

  3. Authorization Period:
     - Must be >0 days
     - Cannot exceed 365 days
     - Standard: 30-90 days typical

Action on Validation Failure:
  - Flag specific date field
  - Request correction from provider
  - Do not auto-proceed
```

### Edge Case Handling Rules

#### Rule 9: Handwritten Documents
```yaml
Rule ID: INTAKE-009
Severity: MEDIUM
Description: Special handling for handwritten clinical notes

Detection:
  - OCR confidence <70% for >50% of document
  - Presence of cursive writing
  - Irregular character spacing

Action:
  - Route to manual review queue
  - Assign to trained medical records specialist
  - Request typed summary from provider
  - SLA: 4 hours for manual processing

Optimization:
  - GPT-4o Vision model handles handwriting better than traditional OCR
  - Use hybrid approach: Azure Form Recognizer + GPT-4o
```

#### Rule 10: Missing Clinical Notes
```yaml
Rule ID: INTAKE-010
Severity: HIGH
Description: Handle cases with no clinical justification

Scenario: PA request submitted with codes but no clinical notes

Action Path 1 (Low-Risk Procedures):
  - Procedure in "Auto-Approve List" (routine preventive care)
  - Proceed without clinical notes
  - Example: Annual physical (99396)

Action Path 2 (High-Risk/Expensive Procedures):
  - Status: PENDING_CLINICAL_DOCUMENTATION
  - Request: Clinical notes from provider
  - Deadline: 48 hours
  - Auto-Deny if: No response

High-Risk Indicators:
  - Cost >$10,000
  - Surgical procedures (CPT 10000-69999)
  - Experimental/investigational
  - Off-label drug use
```

#### Rule 11: Multiple Procedures in Single Request
```yaml
Rule ID: INTAKE-011
Severity: MEDIUM
Description: Handle requests with >1 procedure code

Scenarios:
  1. Related Procedures (same session):
     - Example: Colonoscopy + Biopsy + Polypectomy
     - Action: Group as single case
     - Evaluate: All procedures together

  2. Unrelated Procedures (separate sessions):
     - Example: Knee MRI + Sleep Study
     - Action: Split into 2 separate cases
     - Each gets own PA number

Detection Logic:
  - Clinical Knowledge Graph: Related procedures
  - Same anatomic site
  - Same specialty
  - Bundled billing codes

Action:
  - LLM determines: Related or unrelated
  - Create 1 case (related) or N cases (unrelated)
  - Link cases in database if split
```

#### Rule 12: Prior Authorization vs Prior Notification
```yaml
Rule ID: INTAKE-012
Severity: HIGH
Description: Distinguish PA (approval required) from Prior Notification (FYI only)

Prior Authorization (PA):
  - Insurance approval REQUIRED before service
  - Examples: Surgeries, high-cost imaging, specialty drugs
  - Process: Full PA workflow (eligibility → benefits → clinical → decision)
  - SLA: 24-72 hours

Prior Notification (PN):
  - Informational only, no approval needed
  - Examples: Generic prescriptions, routine labs
  - Process: Acknowledge receipt only
  - SLA: Immediate acknowledgment

Detection:
  - Benefit plan configuration lookup
  - Procedure code in "PA Required" list
  - Override: Provider can escalate PN to PA if needed

Action:
  - PA: Full workflow
  - PN: Auto-acknowledge and close case
```

#### Rule 13: Experimental/Investigational Procedures
```yaml
Rule ID: INTAKE-013
Severity: CRITICAL
Description: Flag experimental procedures for special review

Detection Criteria:
  1. Procedure Code:
     - CPT Category III codes (0001T-0999T) - experimental
     - HCPCS C codes (C1000-C9999) - temporary codes

  2. Drug Administration:
     - FDA approval status check
     - Clinical trial participation

  3. Off-Label Use:
     - Drug prescribed for non-FDA approved indication

  4. Medical Device:
     - Investigational Device Exemption (IDE) status

Action on Detection:
  - Status: EXPERIMENTAL_REVIEW_REQUIRED
  - Route to: Medical Director (physician review)
  - Research: Clinical trial data, peer-reviewed literature
  - Decision Authority: Medical Director only (no AI auto-approval)
  - Timeline: Extended to 5 business days

Documentation Required:
  - Peer-reviewed studies supporting efficacy
  - FDA approval status
  - Clinical trial enrollment documentation
  - Letter of medical necessity from treating physician
```

#### Rule 14: Retroactive Authorization Requests
```yaml
Rule ID: INTAKE-014
Severity: HIGH
Description: Handle requests submitted after service was rendered

Definition:
  - Retroactive = Service date is in the past
  - Timeframe: Service occurred >3 days ago

Business Policy:
  - Generally NOT allowed (encourages prior submission)
  - Exceptions: Emergency situations, technical issues

Exception Criteria (ALL must be met):
  - Emergency/Urgent service (life-threatening)
  - Provider documented why PA not obtained beforehand
  - Submitted within 30 days of service
  - Member was eligible on date of service

Action on Retroactive Request:
  Path 1 (Meets Exception Criteria):
    - Accept and process
    - Flag: RETROACTIVE for audit
    - Review: Escalate to supervisor

  Path 2 (Does NOT Meet Exception):
    - Status: REJECTED_RETROACTIVE
    - Reason: "PA must be obtained prior to service"
    - Inform: Provider is financially responsible

Regulatory Compliance:
  - CMS requires: "Prior authorization means PRIOR to service"
  - State regulations: Some states allow 24-hour grace period
  - Document: Reason for retroactive submission for audit
```

#### Rule 15: Cross-State Coverage Requests
```yaml
Rule ID: INTAKE-015
Severity: MEDIUM
Description: Handle PA requests for services in different states

Scenarios:
  1. Member lives in State A, seeks care in State B
  2. Snowbird/seasonal residents
  3. Emergency care while traveling

Validation Logic:
  - Provider State: Extract from NPI
  - Member State: Extract from address
  - Plan Type: HMO vs PPO (HMO more restrictive)

Business Rules:
  HMO Plans:
    - Out-of-state ONLY if:
      a) Emergency/Urgent care
      b) Prior approval obtained
      c) No in-network provider available in state
    - Otherwise: DENIED

  PPO Plans:
    - Out-of-state allowed
    - May have different benefit levels
    - Check: Network status in provider state

  Medicare Advantage:
    - National coverage (50 states)
    - Emergency coverage worldwide

Action:
  - Flag: OUT_OF_STATE
  - Verify: Network adequacy in member state
  - Check: Emergency/urgent justification
  - Route to: Benefits agent for coverage determination
```

#### Rule 16: Interpreter/Translation Needs
```yaml
Rule ID: INTAKE-016
Severity: LOW
Description: Detect non-English submissions and handle appropriately

Detection:
  - Language identification (LangDetect library)
  - Common languages: Spanish, Chinese, Vietnamese, Korean, Russian

Action on Non-English:
  - OCR with language parameter (Azure Form Recognizer supports 164 languages)
  - Translation to English (Azure Translator)
  - Store: Both original and translated versions
  - Flag: TRANSLATION_USED for audit

Member Communication:
  - If member preferred language != English:
    - Decision letter in both English + preferred language
    - Phone support with interpreter

Regulatory Compliance:
  - Civil Rights Act: Language access required
  - Medicare: Top 15 languages must be supported
  - NCQA: Interpreter services documented
```

#### Rule 17: Partial Approvals
```yaml
Rule ID: INTAKE-017
Severity: MEDIUM
Description: Handle requests that may be partially approved

Examples:
  - Request: 30 physical therapy sessions
  - Approval: 12 sessions initially (can request more later)

  - Request: Brand-name drug
  - Approval: Generic equivalent approved instead

Intake Detection:
  - Quantity > typical coverage limits
  - Brand when generic available
  - Duration > plan maximum

Action:
  - Do NOT reject at intake
  - Flag: POTENTIAL_PARTIAL_APPROVAL
  - Route to: Clinical agent for determination
  - Inform: Provider that partial approval possible
```

#### Rule 18: Appeals vs New Requests
```yaml
Rule ID: INTAKE-018
Severity: CRITICAL
Description: Distinguish appeal from new PA request

Appeal Indicators:
  - Document states: "Appeal", "Reconsideration", "Grievance"
  - References existing case ID
  - Submitted after previous denial
  - Member/Provider explicitly states "appealing denial"

Validation:
  - Lookup: Original case ID
  - Verify: Previous decision was DENIAL
  - Check: Appeal filed within timeframe (typically 180 days)

Action on Appeal:
  - Do NOT create new PA case
  - Route to: Appeals Agent (different workflow)
  - Link to: Original case
  - SLA: Different (30-60 days for appeals vs 24-72h for PA)
  - Regulatory: Appeal rights must be preserved

Action on New Request:
  - Create: New case with new case ID
  - Link reference: To previous case for historical context
```

#### Rule 19: Coordination of Benefits (COB)
```yaml
Rule ID: INTAKE-019
Severity: HIGH
Description: Detect members with multiple insurance coverage

Detection:
  - Member has >1 active insurance plan
  - Medicare + Medigap
  - Primary + Secondary insurance

Data Requirements:
  - Other insurance information
  - Which plan is primary vs secondary
  - Explanation of Benefits (EOB) from primary if service already rendered

Business Logic:
  - Primary pays first
  - Secondary pays remainder (if applicable)
  - PA required: Depends on primary plan decision

Action at Intake:
  - Flag: COB_DETECTED
  - Route to: COM Agent (Coordination of Benefits Agent)
  - Request: Primary plan information
  - Hold: Until primary plan determination received (if applicable)
```

#### Rule 20: Bundled Services Detection
```yaml
Rule ID: INTAKE-020
Severity: MEDIUM
Description: Identify procedures that should be bundled vs billed separately

CCI Edits (Correct Coding Initiative):
  - NCCI edits define which procedures can be billed together
  - Example: Colonoscopy includes anesthesia (cannot bill separately)

Detection:
  - Multiple procedure codes submitted
  - Check against NCCI edit tables
  - Identify: Bundled vs separately billable

Action:
  - Inform provider: "Codes X and Y are bundled"
  - Request: Correction or justification for separate billing
  - Clinical Review: If modifier justifies separate billing
  - Prevent: Inappropriate unbundling (fraud indicator)

Integration:
  - Send flag to Fraud Agent if pattern detected
  - Audit trail: Document bundling decisions
```

---

## Technical Architecture

### Component Design

```
┌─────────────────────────────────────────────────────────────┐
│                     INTAKE AGENT                             │
│                    (GPT-4o Vision)                           │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Document     │    │     OCR      │    │   Entity     │
│ Classifier   │    │   Engine     │    │  Extractor   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
        ┌──────────────┐          ┌──────────────┐
        │  Validator   │          │     Case     │
        │    Engine    │          │   Creator    │
        └──────────────┘          └──────────────┘
                │                           │
                └─────────────┬─────────────┘
                              │
                              ▼
                     ┌──────────────┐
                     │   Working    │
                     │    Memory    │
                     │   (Redis)    │
                     └──────────────┘
```

### LLM Configuration

```yaml
Model Configuration:
  Primary Model: gpt-4o-2024-08-06
  Capabilities:
    - Vision: Yes (OCR from images)
    - Structured Output: Yes (JSON mode)
    - Function Calling: Yes
    - Max Context: 128K tokens
    - Max Output: 16K tokens

  Temperature: 0.1
    Reasoning: Low temperature for consistent, deterministic extraction

  Top-P: 0.95
    Reasoning: Slight randomness for creative problem-solving

  Frequency Penalty: 0.0
    Reasoning: No penalty needed for extraction tasks

  Presence Penalty: 0.0
    Reasoning: No penalty needed

  Token Limits:
    Max Input: 10,000 tokens (per request)
    Max Output: 3,000 tokens (per request)
    Average Usage: 2,800 tokens/request

Fallback Model: gpt-4-turbo
  Trigger: If gpt-4o unavailable or error rate >5%
  Auto-Failover: Yes
  Notification: PagerDuty alert

Cost Optimization:
  Model Selection Logic:
    - Simple forms (no OCR needed): gpt-3.5-turbo ($0.001/1K tokens)
    - OCR required: gpt-4o ($0.01/1K tokens)
    - Complex extraction: gpt-4o

  Average Cost per Request:
    - Simple: $0.003
    - Medium: $0.028
    - Complex: $0.042
    - Blended Average: $0.020
```

### Tool Integrations

#### Tool 1: OCR Tool (Azure Form Recognizer + GPT-4o Vision)

```python
class OCRTool:
    """
    Hybrid OCR: Azure Form Recognizer for structured forms,
    GPT-4o Vision for handwritten notes and complex layouts
    """
    
    def __init__(self):
        self.azure_ocr = AzureFormRecognizer()
        self.gpt4o_vision = OpenAI(model="gpt-4o")
    
    async def extract_text(
        self,
        document: bytes,
        document_type: str
    ) -> OCRResult:
        """Extract text from document"""
        
        # Step 1: Classify extraction strategy
        if document_type in ["structured_form", "edi_837", "fhir_bundle"]:
            # Use Azure Form Recognizer (optimized for forms)
            result = await self.azure_ocr.analyze_document(
                document=document,
                model="prebuilt-healthInsuranceCard.us"
            )
            
            return OCRResult(
                text=result.content,
                confidence=result.confidence,
                fields=result.fields,
                method="azure_form_recognizer"
            )
        
        else:
            # Use GPT-4o Vision (better for handwriting, complex layouts)
            image_data = self.convert_to_image(document)
            
            prompt = """
            You are a medical document OCR specialist.
            
            Extract ALL text from this document.
            Preserve formatting, line breaks, and structure.
            
            If handwriting is illegible, indicate [ILLEGIBLE].
            If unsure about a word, indicate [UNCLEAR: <best guess>].
            
            Return extracted text exactly as it appears.
            """
            
            response = await self.gpt4o_vision.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000
            )
            
            extracted_text = response.choices[0].message.content
            
            # Calculate confidence based on [ILLEGIBLE] and [UNCLEAR] tags
            confidence = self.calculate_confidence(extracted_text)
            
            return OCRResult(
                text=extracted_text,
                confidence=confidence,
                fields=None,
                method="gpt4o_vision"
            )
    
    def calculate_confidence(self, text: str) -> float:
        """Calculate confidence based on uncertainty markers"""
        illegible_count = text.count("[ILLEGIBLE]")
        unclear_count = text.count("[UNCLEAR:")
        total_words = len(text.split())
        
        uncertainty_score = (illegible_count + unclear_count) / total_words
        confidence = max(0.0, 1.0 - (uncertainty_score * 2))
        
        return round(confidence, 2)
```

#### Tool 2: Entity Extraction Tool

```python
class EntityExtractionTool:
    """Extract structured entities using GPT-4o with schema enforcement"""
    
    def __init__(self, prompt_registry: PromptRegistry):
        self.llm = OpenAI(model="gpt-4o")
        self.prompt_registry = prompt_registry
    
    async def extract_entities(
        self,
        text: str,
        document_type: str
    ) -> EntityResult:
        """Extract entities from text using structured output"""
        
        # Get versioned prompt template
        prompt_template = self.prompt_registry.get_prompt(
            agent_id="intake_agent",
            prompt_name="extract_entities",
            version="v2.3.1"
        )
        
        # Build prompt with context
        prompt = prompt_template.format(
            document_type=document_type,
            text=text
        )
        
        # Define output schema (enforces structure)
        schema = {
            "type": "object",
            "properties": {
                "member": {
                    "type": "object",
                    "properties": {
                        "member_id": {"type": "string"},
                        "name": {"type": "string"},
                        "dob": {"type": "string", "format": "date"},
                        "address": {"type": "string"},
                        "phone": {"type": "string"},
                        "email": {"type": "string", "format": "email"}
                    },
                    "required": ["member_id", "name", "dob"]
                },
                "provider": {
                    "type": "object",
                    "properties": {
                        "npi": {"type": "string", "pattern": "^[0-9]{10}$"},
                        "name": {"type": "string"},
                        "specialty": {"type": "string"},
                        "phone": {"type": "string"},
                        "fax": {"type": "string"}
                    },
                    "required": ["npi", "name"]
                },
                "clinical": {
                    "type": "object",
                    "properties": {
                        "diagnosis_codes": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "procedure_codes": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "clinical_summary": {"type": "string"}
                    },
                    "required": ["diagnosis_codes", "procedure_codes"]
                },
                "administrative": {
                    "type": "object",
                    "properties": {
                        "urgency": {
                            "type": "string",
                            "enum": ["URGENT", "STANDARD"]
                        },
                        "service_date": {"type": "string", "format": "date"},
                        "authorization_period_days": {"type": "integer"}
                    },
                    "required": ["service_date"]
                }
            },
            "required": ["member", "provider", "clinical", "administrative"]
        }
        
        # Call LLM with schema enforcement
        response = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a healthcare data extraction specialist."},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "pa_entities",
                    "schema": schema,
                    "strict": True
                }
            },
            temperature=0.1
        )
        
        # Parse response
        entities = json.loads(response.choices[0].message.content)
        
        # Add confidence scores
        entities_with_confidence = await self.add_confidence_scores(entities, text)
        
        return EntityResult(
            entities=entities_with_confidence,
            model_used="gpt-4o",
            tokens_used=response.usage.total_tokens,
            extraction_time_ms=response.response_ms
        )
    
    async def add_confidence_scores(
        self,
        entities: dict,
        source_text: str
    ) -> dict:
        """Add confidence scores to extracted entities"""
        
        # For each entity, check if value appears in source text
        for category, fields in entities.items():
            if isinstance(fields, dict):
                for field_name, field_value in fields.items():
                    if isinstance(field_value, str):
                        # Check if value appears in source
                        appears_in_source = field_value.lower() in source_text.lower()
                        
                        fields[f"{field_name}_confidence"] = 0.95 if appears_in_source else 0.60
        
        return entities
```

#### Tool 3: Validation Tool

```python
class ValidationTool:
    """Validate extracted entities against business rules and databases"""
    
    def __init__(
        self,
        member_service: MemberService,
        provider_service: ProviderService,
        code_validator: CodeValidator
    ):
        self.member_service = member_service
        self.provider_service = provider_service
        self.code_validator = code_validator
    
    async def validate_entities(
        self,
        entities: dict
    ) -> ValidationResult:
        """Comprehensive validation of extracted entities"""
        
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "field_validations": {}
        }
        
        # 1. Member Validation
        member_validation = await self.validate_member(entities["member"])
        validation_results["field_validations"]["member"] = member_validation
        
        if not member_validation["is_valid"]:
            validation_results["is_valid"] = False
            validation_results["errors"].extend(member_validation["errors"])
        
        # 2. Provider Validation
        provider_validation = await self.validate_provider(entities["provider"])
        validation_results["field_validations"]["provider"] = provider_validation
        
        if not provider_validation["is_valid"]:
            validation_results["is_valid"] = False
            validation_results["errors"].extend(provider_validation["errors"])
        
        # 3. Clinical Validation
        clinical_validation = await self.validate_clinical(entities["clinical"])
        validation_results["field_validations"]["clinical"] = clinical_validation
        
        if not clinical_validation["is_valid"]:
            validation_results["is_valid"] = False
            validation_results["errors"].extend(clinical_validation["errors"])
        
        # 4. Administrative Validation
        admin_validation = await self.validate_administrative(entities["administrative"])
        validation_results["field_validations"]["administrative"] = admin_validation
        
        if not admin_validation["is_valid"]:
            validation_results["is_valid"] = False
            validation_results["errors"].extend(admin_validation["errors"])
        
        return ValidationResult(**validation_results)
    
    async def validate_member(self, member: dict) -> dict:
        """Validate member information"""
        
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["member_id", "name", "dob"]
        for field in required_fields:
            if not member.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Member ID format
        member_id = member.get("member_id")
        if member_id and not re.match(r"^[A-Z0-9]{6,12}$", member_id):
            errors.append(f"Invalid member ID format: {member_id}")
        
        # Member exists in database
        if member_id:
            member_record = await self.member_service.get_member(member_id)
            if not member_record:
                errors.append(f"Member ID not found in enrollment database: {member_id}")
            elif member_record.status != "ACTIVE":
                errors.append(f"Member is not active: {member_record.status}")
        
        # DOB validation
        dob = member.get("dob")
        if dob:
            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
                age = (datetime.now().date() - dob_date).days // 365
                
                if age < 0 or age > 120:
                    errors.append(f"Invalid date of birth (age {age})")
            except ValueError:
                errors.append(f"Invalid DOB format: {dob} (expected YYYY-MM-DD)")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def validate_provider(self, provider: dict) -> dict:
        """Validate provider information"""
        
        errors = []
        warnings = []
        
        # NPI required
        npi = provider.get("npi")
        if not npi:
            errors.append("Missing required field: NPI")
            return {"is_valid": False, "errors": errors, "warnings": warnings}
        
        # NPI format (10 digits)
        if not re.match(r"^[0-9]{10}$", npi):
            errors.append(f"Invalid NPI format: {npi} (must be 10 digits)")
        
        # Luhn algorithm check
        if not self.validate_luhn(npi):
            errors.append(f"NPI failed checksum validation: {npi}")
        
        # NPI registry lookup
        provider_record = await self.provider_service.get_provider_by_npi(npi)
        if not provider_record:
            errors.append(f"NPI not found in NPPES registry: {npi}")
        elif provider_record.status != "ACTIVE":
            warnings.append(f"Provider NPI is not active: {provider_record.status}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def validate_clinical(self, clinical: dict) -> dict:
        """Validate clinical codes"""
        
        errors = []
        warnings = []
        
        # Diagnosis codes
        diagnosis_codes = clinical.get("diagnosis_codes", [])
        if not diagnosis_codes:
            errors.append("At least one diagnosis code required")
        
        for dx_code in diagnosis_codes:
            is_valid = await self.code_validator.validate_icd10(dx_code)
            if not is_valid:
                errors.append(f"Invalid ICD-10 code: {dx_code}")
        
        # Procedure codes
        procedure_codes = clinical.get("procedure_codes", [])
        if not procedure_codes:
            errors.append("At least one procedure code required")
        
        for proc_code in procedure_codes:
            is_valid = await self.code_validator.validate_cpt(proc_code)
            if not is_valid:
                errors.append(f"Invalid CPT/HCPCS code: {proc_code}")
        
        # Clinical summary
        clinical_summary = clinical.get("clinical_summary", "")
        if len(clinical_summary) < 20:
            warnings.append("Clinical summary is very brief (<20 characters)")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    async def validate_administrative(self, administrative: dict) -> dict:
        """Validate administrative fields"""
        
        errors = []
        warnings = []
        
        # Service date
        service_date = administrative.get("service_date")
        if not service_date:
            errors.append("Service date is required")
        else:
            try:
                svc_date = datetime.strptime(service_date, "%Y-%m-%d").date()
                days_diff = (svc_date - datetime.now().date()).days
                
                # Future date check
                if days_diff > 365:
                    warnings.append(f"Service date is >365 days in future: {service_date}")
                
                # Past date check
                if days_diff < -30:
                    warnings.append(f"Service date is >30 days in past (retroactive): {service_date}")
                
            except ValueError:
                errors.append(f"Invalid service date format: {service_date}")
        
        # Urgency
        urgency = administrative.get("urgency")
        if urgency and urgency not in ["URGENT", "STANDARD"]:
            errors.append(f"Invalid urgency value: {urgency}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def validate_luhn(self, npi: str) -> bool:
        """Luhn algorithm for NPI checksum validation"""
        digits = [int(d) for d in npi]
        checksum = 0
        
        for i, digit in enumerate(reversed(digits)):
            if i % 2 == 1:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        
        return checksum % 10 == 0
```

### Memory Management

```yaml
Working Memory (Redis):
  Purpose: Store intermediate processing results
  
  Key Pattern: "intake:case:{case_id}"
  
  Data Stored:
    - Original request (JSON)
    - OCR results (text + confidence)
    - Extracted entities (JSON)
    - Validation results
    - Processing timestamps
    - Agent execution trace
  
  TTL: 7 days (auto-expire after 7 days)
  
  Example:
    Key: "intake:case:PA-2026-001234"
    Value:
      {
        "case_id": "PA-2026-001234",
        "created_at": "2026-06-01T09:00:00Z",
        "request_channel": "fax",
        "ocr_result": {
          "text": "...",
          "confidence": 0.98,
          "method": "gpt4o_vision"
        },
        "entities": {
          "member": {...},
          "provider": {...},
          "clinical": {...},
          "administrative": {...}
        },
        "validation": {
          "is_valid": true,
          "errors": [],
          "warnings": ["Service date >30 days past"]
        },
        "processing_time_ms": 25000
      }

Episodic Memory (PostgreSQL):
  Purpose: Long-term storage of case history
  
  Table: cases
  Columns:
    - case_id (PK)
    - member_id
    - provider_npi
    - diagnosis_codes (JSONB)
    - procedure_codes (JSONB)
    - status
    - created_at
    - updated_at
    - deleted_at (soft delete)
  
  Indexes:
    - member_id (for member lookup)
    - provider_npi (for provider lookup)
    - created_at (for time-range queries)
    - status (for queue filtering)
  
  Retention: 10 years (regulatory requirement)
```

### Prompt Templates

#### Prompt Version: v2.3.1

```text
SYSTEM PROMPT:
You are a healthcare intake specialist with expertise in medical coding,
insurance terminology, and data extraction.

Your task is to extract structured information from prior authorization requests.

CRITICAL RULES:
1. Extract ONLY information explicitly stated in the document
2. Do NOT invent or guess information
3. If information is unclear, mark as [UNCLEAR: <best guess>]
4. If information is missing, leave field empty (do NOT fill with placeholders)
5. Preserve exact medical codes (do not modify diagnosis/procedure codes)
6. Use standard date format: YYYY-MM-DD

───────────────────────────────────────────────────────────────

USER PROMPT:
Extract the following entities from this prior authorization request:

DOCUMENT TYPE: {document_type}
DOCUMENT TEXT:
{text}

───────────────────────────────────────────────────────────────

EXTRACTION REQUIREMENTS:

MEMBER INFORMATION:
  - Member ID (insurance ID number)
  - Member Name (First Last)
  - Date of Birth (YYYY-MM-DD format)
  - Address (full address)
  - Phone Number
  - Email Address

PROVIDER INFORMATION:
  - NPI (10-digit number)
  - Provider Name
  - Provider Specialty
  - Phone Number
  - Fax Number
  - Address

CLINICAL INFORMATION:
  - Diagnosis Codes (ICD-10 format, e.g., M17.11)
  - Procedure Codes (CPT or HCPCS format, e.g., 27447)
  - Clinical Summary (why procedure is needed)
  - Clinical Findings (symptoms, test results, etc.)

ADMINISTRATIVE INFORMATION:
  - Urgency (URGENT or STANDARD)
  - Requested Service Date (YYYY-MM-DD)
  - Authorization Period (number of days)

───────────────────────────────────────────────────────────────

OUTPUT FORMAT:
Return a JSON object with the following structure:

{
  "member": {
    "member_id": "string",
    "name": "string",
    "dob": "YYYY-MM-DD",
    "address": "string",
    "phone": "string",
    "email": "string"
  },
  "provider": {
    "npi": "string (10 digits)",
    "name": "string",
    "specialty": "string",
    "phone": "string",
    "fax": "string",
    "address": "string"
  },
  "clinical": {
    "diagnosis_codes": ["string"],
    "procedure_codes": ["string"],
    "clinical_summary": "string",
    "clinical_findings": "string"
  },
  "administrative": {
    "urgency": "URGENT | STANDARD",
    "service_date": "YYYY-MM-DD",
    "authorization_period_days": integer
  }
}

EXAMPLE OUTPUT:
{
  "member": {
    "member_id": "M789456",
    "name": "John Smith",
    "dob": "1975-06-15",
    "address": "123 Main St, Chicago, IL 60601",
    "phone": "312-555-1234",
    "email": "john.smith@email.com"
  },
  "provider": {
    "npi": "1234567893",
    "name": "Dr. Sarah Johnson",
    "specialty": "Orthopedic Surgery",
    "phone": "312-555-5678",
    "fax": "312-555-5679",
    "address": "456 Medical Plaza, Chicago, IL 60602"
  },
  "clinical": {
    "diagnosis_codes": ["M17.11"],
    "procedure_codes": ["27447"],
    "clinical_summary": "Patient has severe right knee osteoarthritis with failed conservative management (8 weeks PT, NSAIDs). X-ray shows Grade 4 arthritis with bone-on-bone contact.",
    "clinical_findings": "Pain 8/10, limited ROM, antalgic gait, failed PT and medications"
  },
  "administrative": {
    "urgency": "STANDARD",
    "service_date": "2026-07-15",
    "authorization_period_days": 30
  }
}
```

### RAG Pipeline

**Not Applicable:** The Intake Agent does not use RAG (Retrieval-Augmented Generation) because it performs data extraction from provided documents rather than knowledge retrieval.

However, it does use:
- **Document Store (Azure Blob Storage):** Store original faxes, PDFs, emails
- **Code Validation Databases:** ICD-10, CPT, HCPCS code lookups
- **NPI Registry:** NPPES database for provider validation

---

## Input/Output Specifications

### Input Schema

```json
{
  "title": "PA Request Input",
  "type": "object",
  "properties": {
    "request_id": {
      "type": "string",
      "description": "Unique request ID from submission channel"
    },
    "channel": {
      "type": "string",
      "enum": ["portal", "fax", "edi", "fhir", "email", "ivr"],
      "description": "Submission channel"
    },
    "submitted_at": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp of submission (ISO 8601)"
    },
    "submitter": {
      "type": "object",
      "properties": {
        "type": {"type": "string", "enum": ["provider", "member", "facility"]},
        "id": {"type": "string"},
        "name": {"type": "string"},
        "contact_phone": {"type": "string"},
        "contact_email": {"type": "string"}
      },
      "required": ["type", "id", "name"]
    },
    "documents": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "document_id": {"type": "string"},
          "document_type": {
            "type": "string",
            "enum": ["pa_form", "clinical_notes", "lab_report", "imaging_report", "prescription", "other"]
          },
          "file_name": {"type": "string"},
          "file_size_bytes": {"type": "integer"},
          "mime_type": {"type": "string"},
          "storage_url": {"type": "string", "format": "uri"},
          "page_count": {"type": "integer"}
        },
        "required": ["document_id", "document_type", "storage_url"]
      },
      "minItems": 1
    },
    "structured_data": {
      "type": "object",
      "description": "Pre-extracted data if available (e.g., from portal form)",
      "properties": {
        "member_id": {"type": "string"},
        "diagnosis_codes": {
          "type": "array",
          "items": {"type": "string"}
        },
        "procedure_codes": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "priority": {
      "type": "string",
      "enum": ["URGENT", "STANDARD", "ROUTINE"],
      "description": "Submitter-indicated priority"
    },
    "metadata": {
      "type": "object",
      "description": "Additional metadata",
      "properties": {
        "submission_ip": {"type": "string"},
        "user_agent": {"type": "string"},
        "session_id": {"type": "string"}
      }
    }
  },
  "required": ["request_id", "channel", "submitted_at", "documents"]
}
```

### Output Schema

```json
{
  "title": "Intake Agent Output",
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "pattern": "^PA-[0-9]{4}-[0-9]{6}$",
      "description": "Generated case ID (e.g., PA-2026-001234)",
      "examples": ["PA-2026-001234"]
    },
    "status": {
      "type": "string",
      "enum": [
        "INTAKE_COMPLETE",
        "INCOMPLETE",
        "INVALID",
        "DUPLICATE",
        "REJECTED"
      ],
      "description": "Intake processing status"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Case creation timestamp"
    },
    "sla_deadline": {
      "type": "string",
      "format": "date-time",
      "description": "SLA deadline based on urgency"
    },
    "extracted_entities": {
      "type": "object",
      "properties": {
        "member": {
          "type": "object",
          "properties": {
            "member_id": {"type": "string"},
            "name": {"type": "string"},
            "dob": {"type": "string", "format": "date"},
            "address": {"type": "string"},
            "phone": {"type": "string"},
            "email": {"type": "string", "format": "email"}
          },
          "required": ["member_id", "name", "dob"]
        },
        "provider": {
          "type": "object",
          "properties": {
            "npi": {"type": "string", "pattern": "^[0-9]{10}$"},
            "name": {"type": "string"},
            "specialty": {"type": "string"},
            "tin": {"type": "string"},
            "phone": {"type": "string"},
            "fax": {"type": "string"},
            "address": {"type": "string"}
          },
          "required": ["npi", "name"]
        },
        "clinical": {
          "type": "object",
          "properties": {
            "diagnosis_codes": {
              "type": "array",
              "items": {"type": "string"},
              "minItems": 1
            },
            "procedure_codes": {
              "type": "array",
              "items": {"type": "string"},
              "minItems": 1
            },
            "clinical_summary": {"type": "string"},
            "clinical_findings": {"type": "string"},
            "supporting_documentation": {
              "type": "array",
              "items": {"type": "string"}
            }
          },
          "required": ["diagnosis_codes", "procedure_codes"]
        },
        "administrative": {
          "type": "object",
          "properties": {
            "urgency": {
              "type": "string",
              "enum": ["URGENT", "STANDARD"]
            },
            "service_date": {"type": "string", "format": "date"},
            "authorization_period_days": {"type": "integer"},
            "specialty": {"type": "string"},
            "place_of_service": {"type": "string"}
          },
          "required": ["service_date", "urgency"]
        }
      },
      "required": ["member", "provider", "clinical", "administrative"]
    },
    "validation_results": {
      "type": "object",
      "properties": {
        "is_complete": {"type": "boolean"},
        "is_valid": {"type": "boolean"},
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "field": {"type": "string"},
              "error_code": {"type": "string"},
              "message": {"type": "string"}
            }
          }
        },
        "warnings": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "field": {"type": "string"},
              "warning_code": {"type": "string"},
              "message": {"type": "string"}
            }
          }
        },
        "field_confidence_scores": {
          "type": "object",
          "description": "Confidence score (0-1) for each extracted field"
        }
      },
      "required": ["is_complete", "is_valid", "errors", "warnings"]
    },
    "processing_metadata": {
      "type": "object",
      "properties": {
        "agent_version": {"type": "string"},
        "model_used": {"type": "string"},
        "tokens_consumed": {"type": "integer"},
        "processing_time_ms": {"type": "integer"},
        "ocr_method": {"type": "string"},
        "extraction_confidence": {"type": "number"}
      }
    },
    "next_steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "agent": {"type": "string"},
          "action": {"type": "string"},
          "scheduled_at": {"type": "string", "format": "date-time"}
        }
      }
    }
  },
  "required": [
    "case_id",
    "status",
    "created_at",
    "sla_deadline",
    "extracted_entities",
    "validation_results"
  ]
}
```

### Validation Rules

**Field-Level Validation:**

| Field | Rule | Error Code | Message |
|-------|------|------------|---------|
| member_id | Required, alphanumeric, 6-12 chars | ERR_MEMBER_ID_INVALID | Invalid member ID format |
| member_id | Must exist in enrollment DB | ERR_MEMBER_NOT_FOUND | Member ID not found |
| dob | Required, YYYY-MM-DD, age 0-120 | ERR_DOB_INVALID | Invalid date of birth |
| npi | Required, 10 digits, Luhn check | ERR_NPI_INVALID | Invalid NPI format or checksum |
| npi | Must exist in NPPES registry | ERR_NPI_NOT_FOUND | NPI not found in registry |
| diagnosis_codes | Required, ≥1 code, ICD-10 format | ERR_DX_MISSING | At least one diagnosis code required |
| diagnosis_codes | Each code must be valid ICD-10 | ERR_DX_INVALID | Invalid ICD-10 code: {code} |
| procedure_codes | Required, ≥1 code, CPT/HCPCS | ERR_PROC_MISSING | At least one procedure code required |
| procedure_codes | Each code must be valid CPT | ERR_PROC_INVALID | Invalid CPT/HCPCS code: {code} |
| service_date | Required, YYYY-MM-DD, <365 days future | ERR_SVC_DATE_INVALID | Invalid service date |
| urgency | Required, URGENT or STANDARD | ERR_URGENCY_INVALID | Invalid urgency value |

### Error Codes

```yaml
Error Code Categories:

ERR_MEMBER_* (1000-1099):
  ERR_MEMBER_ID_INVALID: 1001
  ERR_MEMBER_NOT_FOUND: 1002
  ERR_MEMBER_NOT_ACTIVE: 1003
  ERR_MEMBER_TERMED: 1004
  ERR_DOB_INVALID: 1010
  ERR_DOB_MISMATCH: 1011

ERR_PROVIDER_* (2000-2099):
  ERR_NPI_INVALID: 2001
  ERR_NPI_NOT_FOUND: 2002
  ERR_NPI_NOT_ACTIVE: 2003
  ERR_PROVIDER_NAME_MISSING: 2010

ERR_CLINICAL_* (3000-3099):
  ERR_DX_MISSING: 3001
  ERR_DX_INVALID: 3002
  ERR_PROC_MISSING: 3010
  ERR_PROC_INVALID: 3011
  ERR_CLINICAL_SUMMARY_MISSING: 3020

ERR_ADMIN_* (4000-4099):
  ERR_SVC_DATE_MISSING: 4001
  ERR_SVC_DATE_INVALID: 4002
  ERR_SVC_DATE_PAST: 4003
  ERR_URGENCY_INVALID: 4010

ERR_DOCUMENT_* (5000-5099):
  ERR_DOCUMENT_MISSING: 5001
  ERR_DOCUMENT_FORMAT_UNSUPPORTED: 5002
  ERR_DOCUMENT_SIZE_EXCEEDED: 5003
  ERR_OCR_FAILED: 5010
  ERR_OCR_LOW_CONFIDENCE: 5011

ERR_VALIDATION_* (6000-6099):
  ERR_VALIDATION_FAILED: 6001
  ERR_REQUIRED_FIELD_MISSING: 6002
  ERR_DUPLICATE_CASE: 6010

ERR_SYSTEM_* (9000-9099):
  ERR_SYSTEM_ERROR: 9001
  ERR_DATABASE_ERROR: 9002
  ERR_LLM_ERROR: 9003
  ERR_TIMEOUT: 9004
```

### Example Payloads

#### Example 1: Valid Complete PA Request

**Input:**
```json
{
  "request_id": "REQ-2026-00542891",
  "channel": "portal",
  "submitted_at": "2026-06-01T09:00:00Z",
  "submitter": {
    "type": "provider",
    "id": "NPI-1234567893",
    "name": "Dr. Sarah Johnson",
    "contact_phone": "312-555-5678",
    "contact_email": "sjohnson@medical.com"
  },
  "documents": [
    {
      "document_id": "DOC-001",
      "document_type": "pa_form",
      "file_name": "pa_request.pdf",
      "file_size_bytes": 245678,
      "mime_type": "application/pdf",
      "storage_url": "https://storage.azure.com/pa-docs/DOC-001.pdf",
      "page_count": 3
    },
    {
      "document_id": "DOC-002",
      "document_type": "clinical_notes",
      "file_name": "clinical_notes.pdf",
      "file_size_bytes": 512000,
      "mime_type": "application/pdf",
      "storage_url": "https://storage.azure.com/pa-docs/DOC-002.pdf",
      "page_count": 8
    }
  ],
  "structured_data": {
    "member_id": "M789456",
    "diagnosis_codes": ["M17.11"],
    "procedure_codes": ["27447"]
  },
  "priority": "STANDARD"
}
```

**Output:**
```json
{
  "case_id": "PA-2026-001234",
  "status": "INTAKE_COMPLETE",
  "created_at": "2026-06-01T09:05:00Z",
  "sla_deadline": "2026-06-04T09:05:00Z",
  "extracted_entities": {
    "member": {
      "member_id": "M789456",
      "name": "John Smith",
      "dob": "1975-06-15",
      "address": "123 Main St, Chicago, IL 60601",
      "phone": "312-555-1234",
      "email": "john.smith@email.com"
    },
    "provider": {
      "npi": "1234567893",
      "name": "Dr. Sarah Johnson",
      "specialty": "Orthopedic Surgery",
      "tin": "12-3456789",
      "phone": "312-555-5678",
      "fax": "312-555-5679",
      "address": "456 Medical Plaza, Chicago, IL 60602"
    },
    "clinical": {
      "diagnosis_codes": ["M17.11"],
      "procedure_codes": ["27447"],
      "clinical_summary": "Patient has severe right knee osteoarthritis with failed conservative management (8 weeks PT, NSAIDs, injections). X-ray shows Grade 4 arthritis with bone-on-bone contact. Significant functional impairment.",
      "clinical_findings": "Pain 8/10, limited ROM (flexion 90°, extension -10°), antalgic gait, failed PT and medications, cortisone injection provided temporary relief (2 weeks)",
      "supporting_documentation": [
        "X-ray report: Severe joint space narrowing, osteophytes",
        "PT notes: 8 weeks, minimal improvement",
        "Medication list: Ibuprofen 800mg TID, Tramadol PRN"
      ]
    },
    "administrative": {
      "urgency": "STANDARD",
      "service_date": "2026-07-15",
      "authorization_period_days": 30,
      "specialty": "Orthopedic Surgery",
      "place_of_service": "Hospital Outpatient"
    }
  },
  "validation_results": {
    "is_complete": true,
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "field_confidence_scores": {
      "member.member_id": 1.0,
      "member.name": 0.98,
      "member.dob": 0.99,
      "provider.npi": 1.0,
      "provider.name": 1.0,
      "clinical.diagnosis_codes": 1.0,
      "clinical.procedure_codes": 1.0,
      "clinical.clinical_summary": 0.96
    }
  },
  "processing_metadata": {
    "agent_version": "v2.3.1",
    "model_used": "gpt-4o-2024-08-06",
    "tokens_consumed": 2845,
    "processing_time_ms": 25123,
    "ocr_method": "azure_form_recognizer",
    "extraction_confidence": 0.98
  },
  "next_steps": [
    {
      "agent": "eligibility_agent",
      "action": "verify_coverage",
      "scheduled_at": "2026-06-01T09:05:01Z"
    },
    {
      "agent": "fraud_agent",
      "action": "risk_assessment",
      "scheduled_at": "2026-06-01T09:05:01Z"
    }
  ]
}
```

---

*This documentation continues with sections 5-10. Due to length constraints, I'm providing the first 4 comprehensive sections. Would you like me to continue with the remaining sections (Processing Flow, Integration Points, Error Handling, Monitoring, Examples, Performance)?*
