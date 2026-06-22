# Clinical Content Service - Comprehensive Documentation

## Evidence-Based Clinical Guidelines Service

**Version:** 2.6.0 | **Owner:** Clinical Policy Team | **Status:** Production

## Overview

### Business Purpose
Centralized repository of evidence-based clinical guidelines (MCG, InterQual, CMS LCDs) supporting medical necessity determinations with versioned content and RAG retrieval.

**Key Capabilities:**
- Clinical guideline repository (MCG, InterQual)
- CMS Local Coverage Determinations (LCDs)
- Evidence-based literature database
- Guideline versioning and updates
- RAG-optimized vector embeddings

**Business Impact:**
- Clinical Guidelines: 8,500+ criteria sets
- Update Frequency: Monthly (MCG/InterQual)
- Clinical Accuracy: 96.2%
- RAG Retrieval Precision: 94.8%

### Technical Architecture

**Technologies:**
- Database: PostgreSQL 15 (metadata)
- Vector DB: Milvus (embeddings)
- Embedding Model: text-embedding-3-large
- Content Sources: MCG Health, InterQual, CMS

---

## Database Schema

```sql
CREATE TABLE clinical_guidelines (
    guideline_id SERIAL PRIMARY KEY,
    guideline_source VARCHAR(50),  -- MCG, INTERQUAL, CMS_LCD
    guideline_code VARCHAR(50),  -- e.g., MCG A-0527
    procedure_codes TEXT[],
    diagnosis_codes TEXT[],
    guideline_title VARCHAR(500),
    guideline_text TEXT,
    effective_date DATE,
    version VARCHAR(20),
    
    -- RAG Metadata
    vector_embedding_id VARCHAR(100),  -- Milvus collection ID
    chunk_count INTEGER,
    last_embedded_date TIMESTAMP
);

CREATE TABLE mcg_criteria (
    criteria_id SERIAL PRIMARY KEY,
    mcg_code VARCHAR(20),  -- e.g., A-0527
    procedure_category VARCHAR(100),
    clinical_indication TEXT,
    severity_criteria TEXT,
    conservative_therapy_requirements TEXT,
    contraindications TEXT,
    effective_date DATE,
    version VARCHAR(20)
);

CREATE TABLE cms_local_coverage (
    lcd_id VARCHAR(20) PRIMARY KEY,
    jurisdiction VARCHAR(10),  -- MAC jurisdiction (e.g., J15)
    procedure_codes TEXT[],
    diagnosis_codes TEXT[],  -- Covered diagnoses
    coverage_indications TEXT,
    limitations TEXT,
    effective_date DATE
);
```

---

## API Specifications

### GET /api/v1/clinical/guidelines/search
```json
Request:
POST /api/v1/clinical/guidelines/search
{
  "procedure_code": "27447",
  "diagnosis_code": "M17.11",
  "guideline_source": "MCG"
}

Response:
{
  "guidelines": [
    {
      "guideline_code": "A-0527",
      "source": "MCG",
      "title": "Total Knee Replacement",
      "criteria": {
        "clinical_indication": "Severe osteoarthritis...",
        "severity": "Grade 3-4 on X-ray...",
        "failed_conservative": "6-12 weeks PT..."
      },
      "version": "28th Edition",
      "effective_date": "2026-01-01"
    }
  ]
}
```

### GET /api/v1/clinical/rag-retrieve
```json
Request:
POST /api/v1/clinical/rag-retrieve
{
  "query": "MCG criteria for knee replacement M17.11",
  "top_k": 5
}

Response:
{
  "chunks": [
    {
      "guideline_code": "MCG A-0527",
      "chunk_text": "Total knee replacement is indicated when...",
      "relevance_score": 0.98,
      "source": "MCG 28th Edition"
    }
  ]
}
```

---

## Guideline Update Process

### Monthly MCG/InterQual Updates
```yaml
Process:
  1. Download latest MCG/InterQual content
  2. Parse XML/PDF guidelines
  3. Extract criteria sets
  4. Generate vector embeddings
  5. Load into Milvus vector DB
  6. Update PostgreSQL metadata
  7. Notify Clinical Agent of new version

Versioning:
  - Each guideline version archived
  - Historical decisions reference guideline version used
  - Audit trail tracks which version applied
```

---

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Guidelines Available | >8,000 | 8,500+ |
| RAG Retrieval Precision | >90% | 94.8% |
| Content Freshness | <30 days | 14 days avg |
| API Response Time | <100ms | 65ms P95 |

---

*Clinical Content Service v2.6.0 - 8,500+ Guidelines*
