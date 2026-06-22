# Service Documentation
## Healthcare Insurance Multi-Agent AI Platform - Data Services Layer

This folder contains **comprehensive, in-depth documentation** for all 8 enterprise data services that power the Healthcare Insurance Multi-Agent AI Platform.

---

## 📂 Service Inventory

| # | Service | Purpose | API Type | Daily Volume |
|---|---------|---------|----------|--------------|
| 01 | [Member Service](01-member-service.md) | Enrollment database, eligibility verification | REST, gRPC | 2M+ lookups |
| 02 | [Provider Service](02-provider-service.md) | NPI registry, network status, credentialing | REST, gRPC | 500K+ lookups |
| 03 | [Policy Service](03-policy-service.md) | Plan policies, coverage rules, version control | REST | 100K+ queries |
| 04 | [Claims Service](04-claims-service.md) | Claims processing, payment history, analytics | REST, Batch | 150M/year |
| 05 | [Benefits Config Service](05-benefits-config-service.md) | Plan design, cost-sharing, service limits | REST | 300K+ queries |
| 06 | [Network Service](06-network-service.md) | Network contracts, adequacy, tier management | REST | 250K+ lookups |
| 07 | [Formulary Service](07-formulary-service.md) | Drug coverage, tier placement, PA requirements | REST | 80K+ lookups |
| 08 | [Clinical Content Service](08-clinical-content-service.md) | MCG/InterQual guidelines, RAG embeddings | REST, Vector | 50K+ queries |

---

## 📋 Documentation Structure

Each service document contains:

### 1. Service Overview
- Business purpose
- Technical architecture
- API specifications (REST, gRPC)
- Database schema
- Performance SLAs

### 2. Data Model
- Entity schemas (tables, columns, indexes)
- Relationships (foreign keys, joins)
- Data volumes
- Retention policies
- Archival strategies

### 3. API Endpoints
- Complete REST API specification
- gRPC service definitions
- Request/response schemas
- Authentication (OAuth2, API keys)
- Rate limiting

### 4. Business Logic
- Service rules
- Data validation
- Business constraints
- Regulatory compliance
- Error handling

### 5. Integration Points
- Upstream data sources
- Downstream consumers (agents)
- External systems (EDI, HL7)
- Event publishing (Kafka)

### 6. Caching Strategy
- Cache layers (Redis)
- TTL policies
- Cache invalidation
- Hit rate targets

### 7. Security & Compliance
- Access control (RBAC)
- Data encryption
- PHI protection
- Audit logging
- HIPAA compliance

### 8. Monitoring & SLAs
- Performance metrics
- Availability targets
- Error rates
- Alerting rules

---

## 🔄 Service Architecture

```
┌─────────────────────────────────────────────────┐
│              Agent Layer                         │
│  Intake | Eligibility | Benefits | Clinical     │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│           Data Services Layer                    │
├─────────────┬─────────────┬─────────────┬───────┤
│   Member    │  Provider   │   Policy    │Claims│
│   Service   │   Service   │   Service   │ Svc  │
├─────────────┼─────────────┼─────────────┼───────┤
│  Benefits   │  Network    │ Formulary   │Clinic│
│   Config    │  Service    │  Service    │ Cont │
└─────────────┴─────────────┴─────────────┴───────┘
                    ↓
┌─────────────────────────────────────────────────┐
│            Database Layer                        │
│  PostgreSQL | Redis | Neo4j | Elasticsearch     │
└─────────────────────────────────────────────────┘
```

---

## 🎯 Service Categories

### **Core Member Services** (Identity & Enrollment)
- Member Service: Demographics, enrollment history
- Provider Service: NPI, credentials, network status

### **Coverage Services** (Benefits & Plans)
- Policy Service: Plan documents, coverage rules
- Benefits Config Service: Copays, deductibles, limits
- Network Service: Tier placement, contracts
- Formulary Service: Drug coverage, tiers

### **Transaction Services** (Claims & History)
- Claims Service: Payment history, adjudication

### **Clinical Services** (Medical Guidelines)
- Clinical Content Service: MCG, InterQual, evidence-based medicine

---

## 📊 Service Metrics

| Service | Latency (P95) | Throughput | Cache Hit | Availability |
|---------|---------------|------------|-----------|--------------|
| Member | 25ms | 2,000 req/s | 85% | 99.99% |
| Provider | 30ms | 800 req/s | 75% | 99.95% |
| Policy | 50ms | 200 req/s | 90% | 99.9% |
| Claims | 100ms | 500 req/s | 60% | 99.95% |
| Benefits Config | 40ms | 500 req/s | 80% | 99.9% |
| Network | 35ms | 400 req/s | 70% | 99.9% |
| Formulary | 45ms | 150 req/s | 85% | 99.9% |
| Clinical Content | 120ms | 100 req/s | 50% | 99.95% |

---

## 🔧 Technical Stack

### Databases
- **PostgreSQL**: Transactional data (member, claims, benefits)
  - Version: 15
  - HA: Zone-redundant with read replicas
  - Backup: Daily with 35-day retention
  
- **Redis**: Caching layer
  - Version: 7.0
  - Tier: Premium P4 (26GB)
  - HA: Cluster mode with zone redundancy
  
- **Neo4j**: Graph database (provider networks, fraud detection)
  - Version: 5.x
  - Mode: Causal cluster
  - Size: 500K nodes, 2M edges
  
- **Elasticsearch**: Full-text search, hybrid retrieval
  - Version: 8.x
  - Cluster: 6 nodes
  - Indices: Clinical content, policies

### API Layer
- **REST**: FastAPI (Python), OpenAPI 3.0 spec
- **gRPC**: High-performance binary protocol
- **GraphQL**: Flexible queries (selected services)
- **Authentication**: OAuth2, JWT, API keys
- **Rate Limiting**: Kong API Gateway (1000 req/min per client)

### Integration Patterns
- **Synchronous**: REST, gRPC (< 100ms latency)
- **Asynchronous**: Kafka events (audit, notifications)
- **Batch**: ETL jobs (nightly, weekly)
- **Real-time**: Change Data Capture (CDC) for critical updates

---

## 🚀 Quick Start

### For Developers
1. Review API specifications in each service document
2. See [Member Service](01-member-service.md) for database patterns
3. Study [Clinical Content Service](08-clinical-content-service.md) for RAG integration

### For Architects
1. Understand data model relationships
2. Review caching strategies across services
3. Study integration patterns and event flows

### For DevOps
1. Review SLA targets and monitoring
2. Understand deployment configurations
3. Study backup and disaster recovery strategies

---

## 📖 Related Documentation

- [Agent Documentation](../agents/README.md) - Consumers of these services
- [Main README](../README.md) - Project overview
- [Enterprise Architecture](../doc/02-Enterprise-Solution-Architecture.md) - Full system design
- [PlantUML Diagrams](../plantuml/README.md) - Visual architecture

---

## 🔐 Security & Compliance

### Data Classification
- **PHI (Protected Health Information)**: Member demographics, claims, clinical notes
- **PII (Personally Identifiable Information)**: SSN, DOB, addresses
- **Business Confidential**: Provider contracts, pricing, policies

### Security Controls
- **Encryption at Rest**: AES-256 (all databases)
- **Encryption in Transit**: TLS 1.3 (all APIs)
- **Access Control**: RBAC with OPA policies
- **Audit Logging**: 100% API calls logged (7-year retention)
- **PHI Protection**: Presidio PII detection, dynamic masking

### Compliance
- **HIPAA**: BAA with all vendors, breach notification procedures
- **CMS**: Medicare/Medicaid compliance, audit trail requirements
- **SOC 2 Type II**: Annual certification
- **ISO 27001**: Information security management

---

## 📊 Data Volumes

| Service | Records | Daily Growth | Retention |
|---------|---------|--------------|-----------|
| Member | 5M members | +10K/day | Active: Forever, Terminated: 10 years |
| Provider | 1.2M NPIs | +500/day | Active: Forever, Retired: 7 years |
| Policy | 1,200 plans | +50/year | Active: 3 years, Historical: 10 years |
| Claims | 150M/year | 400K/day | 7 years (regulatory) |
| Benefits Config | 1,200 plans | +50/year | 3 years active |
| Network | 8,500 contracts | +100/month | Active: Forever, Expired: 7 years |
| Formulary | 12,000 drugs | +500/year | Active: 3 years |
| Clinical Content | 50K guidelines | +2K/year | Active: 5 years, Archived: Forever |

**Total Database Size**: ~8 TB (production)  
**Daily Backup Size**: ~50 GB  
**Monthly Growth**: ~1.2 TB

---

## 🔄 Service Dependencies

### Critical Dependencies (Required for PA Workflow)
1. Member Service → Eligibility Agent
2. Benefits Config Service → Benefits Agent
3. Clinical Content Service → Clinical Agent
4. Policy Service → Policy Agent

### Optional Dependencies (Conditional)
- Claims Service → Fraud Agent (pattern analysis)
- Network Service → Benefits Agent (tier validation)
- Formulary Service → Clinical Agent (drug PA)
- Provider Service → All agents (NPI validation)

---

*Last Updated: June 2, 2026*
