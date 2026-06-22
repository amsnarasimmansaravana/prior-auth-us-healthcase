# Clinical Agent - Comprehensive Documentation

## Medical Necessity Review & Clinical Decision Support Agent

**Version:** 2.5.0 | **Owner:** Clinical AI Team | **Status:** Production

## Overview

### Business Purpose
Determines medical necessity using evidence-based clinical guidelines (MCG, InterQual), analyzing patient clinical presentation against established criteria to approve/deny requested services.

**Key Objectives:**
- Evaluate medical necessity per clinical guidelines
- Ensure evidence-based decision making
- Maintain 96%+ clinical accuracy
- Reduce manual clinical review by 80%
- Provide explainable, auditable decisions

**Business Impact:**
- Cost Savings: $57.6M annually (800 FTEs → 160 FTEs)
- Clinical Accuracy: 96.2% (vs 88% manual)
- Override Rate: 4.2% (AI decisions overturned by humans)
- Turnaround Time: 3 minutes avg (vs 2 hours manual)

### Technical Purpose
LLM-powered clinical reasoning with RAG retrieval from evidence-based guidelines, supporting clinical decision making with full explainability.

**Technologies:**
- LLM: GPT-4o (clinical reasoning), Claude 3.5 Sonnet (backup)
- RAG: Milvus (vector DB), MCG/InterQual/CMS LCD embedded
- Embedding Model: text-embedding-3-large
- Clinical NLP: Azure Text Analytics for Health
- Knowledge Graph: Neo4j (drug interactions, contraindications)

### Key Responsibilities

1. **Clinical Guidelines Retrieval (RAG)**
   - Query MCG (Milliman Care Guidelines)
   - Query InterQual criteria
   - Query CMS LCDs (Local Coverage Determinations)
   - Retrieve relevant evidence-based literature

2. **Medical Necessity Determination**
   - Analyze clinical presentation
   - Match patient to guideline criteria
   - Evaluate severity/acuity
   - Assess failed conservative therapy
   - Check contraindications

3. **Clinical Reasoning (Chain-of-Thought)**
   - Step-by-step analysis
   - Criteria-by-criteria evaluation
   - Evidence synthesis
   - Confidence scoring
   - Alternative recommendations

4. **Safety Validation**
   - Drug interaction checks
   - Contraindication detection
   - Age/weight appropriateness
   - Allergy verification
   - Clinical red flags

5. **Decision Explainability**
   - Cite specific guidelines
   - Document clinical reasoning
   - Provide member-friendly explanation
   - Generate physician peer-to-peer talking points

---

## Business Rules

### Rule 1: Medical Necessity Criteria
```yaml
Rule ID: CLIN-001
Description: Evaluate medical necessity per MCG/InterQual

MCG Criteria Structure:
  1. Clinical Indication
     - Diagnosis confirmed
     - Severity documented
     
  2. Failed Conservative Therapy
     - Duration of conservative treatment
     - Lack of response to less invasive options
     
  3. Expected Benefit
     - Functional improvement expected
     - Evidence supports effectiveness
     
  4. No Contraindications
     - Patient can safely undergo procedure
     - No absolute contraindications present

Decision Logic:
  IF ALL criteria met → APPROVE
  IF ANY critical criterion not met → DENY
  IF borderline → REQUIRES_HUMAN_REVIEW
```

### Rule 2: Failed Conservative Therapy Requirements
```yaml
Rule ID: CLIN-002
Description: Validate adequate trial of conservative treatment

Orthopedic Surgery (e.g., Knee Replacement):
  Required:
    - Physical therapy: 6-12 weeks
    - NSAIDs: 3 months
    - Weight loss (if BMI >30): Documented attempt
    - Cortisone injections: At least 1 (temporary relief)
  
  Documentation Required:
    - PT notes showing compliance
    - Medication list with dates
    - Lack of improvement documented

Imaging Studies (MRI):
  Required:
    - X-ray performed first (unless contraindicated)
    - Clinical exam findings consistent
    - Management would change based on MRI results
```

### Rule 3: Severity Thresholds
```yaml
Rule ID: CLIN-003
Description: Evaluate severity/acuity level

Pain Scale (Orthopedic):
  - Pain >7/10 at rest
  - Functional impairment (unable to work/ADLs)
  - Failed multiple conservative therapies

Cardiac (CABG Surgery):
  - Significant coronary stenosis >70%
  - Failed medical management
  - Angina despite optimal therapy
  - Left main disease or 3-vessel disease

Cancer (Oncology):
  - Biopsy-confirmed malignancy
  - Staging appropriate for treatment
  - Evidence-based treatment regimen
```

### Rule 4: Experimental/Investigational Exclusion
```yaml
Rule ID: CLIN-004
Description: Detect experimental procedures requiring special review

Detection:
  - CPT Category III codes (0001T-0999T)
  - HCPCS C codes (temporary codes)
  - Off-label drug use (FDA non-approved indication)
  - Phase I/II clinical trials
  - No peer-reviewed evidence

Action:
  - status = "EXPERIMENTAL"
  - Route to Medical Director
  - Require: Clinical trial data, peer-reviewed studies
  - Extended review timeline (5 business days)
```

### Rule 5: Age/Weight Appropriateness
```yaml
Rule ID: CLIN-005
Description: Validate procedure appropriate for patient demographics

Pediatric Considerations:
  - Age <18: Pediatric dosing calculations
  - Growth plate considerations (orthopedics)
  - Parental consent requirements

Geriatric Considerations:
  - Age >75: Increased surgical risk assessment
  - Comorbidity review
  - Functional status evaluation

Weight-Based:
  - BMI >40: Bariatric surgery safety considerations
  - BMI >50: Some procedures contraindicated
  - Weight-based medication dosing
```

---

## Technical Architecture

### RAG Pipeline Architecture

```
User Query: "MCG criteria for knee replacement, M17.11"
    ↓
┌──────────────────────────────────────────────┐
│ STEP 1: Query Embedding                      │
│ Model: text-embedding-3-large                │
│ Output: 3072-dimension vector                │
└──────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────┐
│ STEP 2: Vector Search (Milvus)              │
│ Collections: mcg_guidelines, interqual,      │
│              cms_lcd, peer_reviewed_lit      │
│ Top-K: 10 chunks                             │
│ Filters: diagnosis=M17.11, procedure=27447   │
└──────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────┐
│ STEP 3: Retrieved Context                   │
│ Chunk 1: MCG A-0527 Knee Replacement        │
│ Chunk 2: InterQual Criteria                 │
│ Chunk 3: CMS LCD for Total Joint            │
│ ... (7 more chunks)                          │
└──────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────┐
│ STEP 4: Re-Ranking (Cross-Encoder)          │
│ Model: cross-encoder/ms-marco-MiniLM-L-12   │
│ Re-rank top 10 → Top 5 most relevant        │
└──────────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────────┐
│ STEP 5: LLM Analysis (GPT-4o)               │
│ Prompt: Clinical reasoning with guidelines  │
│ Context: Top 5 chunks + patient data        │
│ Output: Medical necessity determination     │
└──────────────────────────────────────────────┘
```

### LLM Configuration

```yaml
Model: gpt-4o-2024-08-06
Temperature: 0.1  # Low for clinical consistency
Max Tokens: 4000
Top-P: 0.95

Prompt Structure:
  System: "You are a board-certified clinical reviewer..."
  Context: Retrieved guidelines + patient clinical data
  Task: Chain-of-thought medical necessity evaluation
  Output: Structured JSON with determination, rationale, citations

Safety Guardrails:
  - Hallucination detection (verify all facts cited in context)
  - Clinical safety validator (check for unsafe recommendations)
  - PHI leakage prevention
```

### Clinical Reasoning Prompt (Chain-of-Thought)

```text
SYSTEM PROMPT:
You are a board-certified clinical reviewer specializing in {specialty}.

Your task is to determine medical necessity for the requested procedure.

CRITICAL RULES:
1. Base decisions ONLY on evidence-based guidelines provided
2. Do NOT fabricate clinical information
3. Cite specific guideline sections for all claims
4. Use chain-of-thought reasoning (show your work)
5. If uncertain, mark for human review

────────────────────────────────────────────────────────

USER PROMPT:
Evaluate medical necessity for the following case:

PATIENT DATA:
{patient_clinical_summary}

DIAGNOSIS: {diagnosis_codes}
PROCEDURE REQUESTED: {procedure_codes}

CLINICAL GUIDELINES (Retrieved via RAG):
{retrieved_guidelines}

────────────────────────────────────────────────────────

ANALYSIS FRAMEWORK:

Step 1: Clinical Presentation
- Analyze symptoms, severity, duration
- Review diagnostic test results
- Assess functional impairment

Step 2: Guideline Criteria Review
- Identify applicable guidelines
- List each criterion
- Evaluate if patient meets each criterion

Step 3: Conservative Therapy Evaluation
- Review treatments already attempted
- Assess duration and response
- Determine if adequate trial completed

Step 4: Medical Necessity Determination
- Synthesize findings
- Determine: APPROVE, DENY, or REQUIRES_REVIEW
- Provide confidence score (0.0-1.0)

Step 5: Clinical Rationale
- Detailed explanation
- Cite specific guidelines (with section numbers)
- Address any borderline criteria

────────────────────────────────────────────────────────

OUTPUT FORMAT (JSON):
{
  "determination": "APPROVE | DENY | REQUIRES_REVIEW",
  "confidence": 0.96,
  "clinical_summary": "Brief summary",
  "detailed_rationale": "Full explanation",
  "criteria_evaluation": [
    {
      "criterion": "Failed conservative therapy",
      "met": true,
      "evidence": "8 weeks PT completed, NSAIDs x 3 months"
    }
  ],
  "guidelines_cited": [
    {
      "source": "MCG",
      "guideline": "A-0527",
      "section": "Knee Replacement Criteria",
      "text": "Patient must have failed 6-12 weeks PT..."
    }
  ],
  "alternative_options": [],
  "red_flags": [],
  "requires_human_review": false
}
```

### Knowledge Graph Integration

```cypher
// Neo4j Query: Drug Interaction Check
MATCH (drug1:Drug {name: $medication1})-[:INTERACTS_WITH]->(drug2:Drug {name: $medication2})
RETURN drug1.name, drug2.name, interaction.severity, interaction.mechanism

// Example: Check contraindications
MATCH (procedure:Procedure {code: $cpt_code})-[:CONTRAINDICATED_WITH]->(condition:Condition)
WHERE condition.icd10_code IN $patient_diagnoses
RETURN condition.name, contraindication.severity, contraindication.reason
```

---

## Input/Output Specifications

### Input Schema
```json
{
  "case_id": "PA-2026-001234",
  "member": {
    "member_id": "M789456",
    "age": 51,
    "sex": "M",
    "allergies": ["Penicillin"],
    "current_medications": ["Lisinopril", "Atorvastatin"],
    "comorbidities": ["Hypertension", "Hyperlipidemia"]
  },
  "clinical_data": {
    "diagnosis_codes": ["M17.11"],
    "procedure_codes": ["27447"],
    "clinical_summary": "Severe right knee OA, failed 8wks PT, pain 8/10",
    "labs": [],
    "imaging": [
      {
        "type": "X-ray",
        "date": "2026-05-15",
        "findings": "Grade 4 OA, bone-on-bone"
      }
    ],
    "prior_treatments": [
      "Physical therapy: 8 weeks",
      "NSAIDs: 3 months",
      "Cortisone injection: 1 (temporary relief)"
    ]
  },
  "provider": {
    "npi": "1234567893",
    "specialty": "Orthopedic Surgery"
  }
}
```

### Output Schema
```json
{
  "case_id": "PA-2026-001234",
  "determination": "APPROVE",
  "confidence": 0.96,
  "medical_necessity": "MET",
  "clinical_summary": "51yo male with severe right knee OA...",
  "detailed_rationale": "Patient meets MCG A-0527 criteria for total knee replacement. Failed conservative therapy (8wks PT, NSAIDs x3mo, injection). X-ray confirms Grade 4 OA. No contraindications.",
  "criteria_evaluation": [
    {
      "criterion": "Diagnosis confirmed",
      "met": true,
      "evidence": "X-ray: Grade 4 OA"
    },
    {
      "criterion": "Failed conservative therapy",
      "met": true,
      "evidence": "PT 8wks, NSAIDs 3mo, injection"
    },
    {
      "criterion": "Functional impairment",
      "met": true,
      "evidence": "Pain 8/10, limited ROM"
    }
  ],
  "guidelines_cited": [
    {
      "source": "MCG",
      "guideline": "A-0527",
      "section": "2.1 Knee Replacement Indications",
      "relevance_score": 0.98
    }
  ],
  "contraindications_checked": [],
  "drug_interactions_checked": "None detected",
  "alternative_options": [],
  "requires_human_review": false,
  "processing_metadata": {
    "model_used": "gpt-4o",
    "tokens_consumed": 8500,
    "rag_chunks_retrieved": 10,
    "processing_time_ms": 3200
  }
}
```

---

## Processing Flow

1. **Receive case** from Decision Agent
2. **Extract clinical entities** (diagnosis, procedures, clinical notes)
3. **RAG retrieval**: Query Milvus for relevant guidelines
4. **Knowledge graph check**: Drug interactions, contraindications
5. **LLM clinical reasoning**: Chain-of-thought analysis
6. **Safety validation**: Verify recommendations are clinically safe
7. **Confidence scoring**: Calculate decision confidence
8. **HITL routing**: If confidence <0.85 → human review
9. **Return determination** with full rationale

**Performance Metrics:**
- P95 Latency: 3.2 seconds
- Clinical Accuracy: 96.2%
- Hallucination Rate: 0.3%
- Override Rate: 4.2%

---

## Integration Points

- **RAG Stack:** Milvus (vectors), PostgreSQL (metadata)
- **Knowledge Graph:** Neo4j (drug interactions)
- **External APIs:** MCG API, InterQual API
- **Upstream:** Benefits Agent
- **Downstream:** Decision Agent
- **HITL:** Clinical Reviewer UI

---

## Error Handling

| Scenario | Action |
|----------|--------|
| RAG retrieval fails | Use fallback cached guidelines |
| LLM timeout | Retry 3x, then route to human |
| Low confidence (<0.70) | Automatic human escalation |
| Guideline not found | Medical Director review |
| Contraindication detected | Auto-deny with safety alert |

---

## Examples

### Example 1: Knee Replacement (Approve)
```
Input: M17.11, 27447, 8wks PT failed
Output: APPROVE (MCG A-0527 criteria met)
Confidence: 0.96
```

### Example 2: Experimental Procedure (Escalate)
```
Input: 0999T (Category III experimental code)
Output: REQUIRES_MEDICAL_DIRECTOR_REVIEW
Reason: Experimental procedure, needs clinical trial data
```

### Example 3: Contraindication (Deny)
```
Input: Procedure X requested, patient has allergy to required anesthesia
Output: DENY
Reason: Absolute contraindication detected
Safety Alert: Severe allergic reaction risk
```

---

*Clinical Agent v2.5.0 - Achieving 96.2% Clinical Accuracy*
