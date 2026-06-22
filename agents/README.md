# Agent Documentation
## Healthcare Insurance Multi-Agent AI Platform - Agent Details

This folder contains **comprehensive, in-depth documentation** for all 11 specialized AI agents in the Healthcare Insurance Multi-Agent AI Platform.

---

## 📂 Agent Inventory

| # | Agent | Purpose | Complexity | Criticality |
|---|-------|---------|------------|-------------|
| 01 | [Intake Agent](01-intake-agent.md) | Document processing, OCR, entity extraction | High | Critical |
| 02 | [Eligibility Agent](02-eligibility-agent.md) | Member eligibility verification | Medium | Critical |
| 03 | [Benefits Agent](03-benefits-agent.md) | Coverage validation, network checks | High | Critical |
| 04 | [Clinical Agent](04-clinical-agent.md) | Medical necessity determination | Very High | Critical |
| 05 | [Policy Agent](05-policy-agent.md) | Policy compliance, rule engine | High | Critical |
| 06 | [Fraud Agent](06-fraud-agent.md) | Fraud detection, anomaly analysis | Very High | High |
| 07 | [Decision Agent](07-decision-agent.md) | Final determination, risk assessment | Very High | Critical |
| 08 | [Appeals Agent](08-appeals-agent.md) | Appeal processing, case law research | High | High |
| 09 | [Notification Agent](09-notification-agent.md) | Multi-channel communication | Medium | High |
| 10 | [Audit Agent](10-audit-agent.md) | Compliance logging, traceability | Medium | Critical |
| 11 | [COM Agent](11-com-agent.md) | Care coordination, case management | High | Medium |

---

## 📋 Documentation Structure

Each agent document contains:

### 1. Overview
- Business purpose
- Technical purpose
- Key responsibilities
- Success metrics

### 2. Business Rules
- Detailed business logic
- Decision criteria
- Edge cases
- Regulatory requirements

### 3. Technical Architecture
- Component design
- LLM configuration
- Tool integrations
- Memory management

### 4. Input/Output Specifications
- Input schema (JSON)
- Output schema (JSON)
- Validation rules
- Error codes

### 5. Processing Flow
- Step-by-step execution
- Decision points
- Error handling
- Performance metrics

### 6. Integration Points
- Upstream dependencies
- Downstream consumers
- External services
- Database interactions

### 7. Examples
- Real-world scenarios
- Code samples
- Expected outputs

---

## 🔄 Agent Orchestration Flow

```
User Request
    ↓
[Intake Agent] → Extract & Validate
    ↓
[Eligibility Agent] → Verify Member
    ↓
[Benefits Agent] → Check Coverage
    ↓
┌─────────────────────────────────┐
│     Parallel Processing          │
├─────────────┬──────────┬─────────┤
│  Clinical   │  Policy  │  Fraud  │
│    Agent    │  Agent   │  Agent  │
└─────────────┴──────────┴─────────┘
    ↓
[Decision Agent] → Aggregate & Decide
    ↓
[Notification Agent] → Send Result
    ↓
[Audit Agent] → Log & Trace
```

---

## 🎯 Agent Categories

### **Critical Path Agents** (Required for every PA)
- Intake Agent
- Eligibility Agent
- Benefits Agent
- Clinical Agent
- Decision Agent
- Notification Agent
- Audit Agent

### **Conditional Agents** (Triggered based on scenario)
- Policy Agent (complex cases)
- Fraud Agent (high-risk patterns)
- Appeals Agent (denied cases)
- COM Agent (chronic conditions)

---

## 📊 Agent Metrics

| Agent | Avg Latency | Success Rate | Daily Volume |
|-------|-------------|--------------|--------------|
| Intake | 120s | 98.5% | 50,000 |
| Eligibility | 15s | 99.8% | 50,000 |
| Benefits | 20s | 99.2% | 50,000 |
| Clinical | 180s | 96.2% | 50,000 |
| Policy | 60s | 98.1% | 35,000 |
| Fraud | 120s | 99.5% | 50,000 |
| Decision | 10s | 99.9% | 50,000 |
| Appeals | 600s | 94.5% | 2,500 |
| Notification | 30s | 99.9% | 50,000 |
| Audit | 5s | 100% | 50,000 |
| COM | 300s | 97.8% | 5,000 |

---

## 🔧 Technical Stack

### LLM Models Used
- **GPT-4o**: Clinical Agent, Intake Agent (OCR), Appeals Agent
- **GPT-4o-mini**: Benefits Agent, Policy Agent, Notification Agent
- **GPT-3.5 Turbo**: Eligibility Agent, Audit Agent
- **Claude 3.5 Sonnet**: COM Agent (complex care coordination)

### Frameworks
- **LangGraph**: Multi-agent orchestration (supervisor pattern)
- **LangChain**: Agent framework, tool calling, memory
- **Temporal**: Workflow durability, retries, compensation

### Tools & Integrations
- **RAG**: Milvus (vector search), Elasticsearch (keyword search), Neo4j (knowledge graph)
- **MCP**: Tool registry, capability routing, governance
- **Observability**: LangSmith, OpenTelemetry, Prometheus

---

## 🚀 Quick Start

### For Developers
1. Start with [Intake Agent](01-intake-agent.md) to understand data flow
2. Review [Clinical Agent](04-clinical-agent.md) for complex decision-making
3. Study [Decision Agent](07-decision-agent.md) for aggregation logic

### For Architects
1. Review agent orchestration in [LangGraph supervisor pattern](../doc/03-Agentic-AI-Platform-Architecture.md)
2. Understand A2A protocol in [Enterprise Architecture](../doc/02-Enterprise-Solution-Architecture.md)
3. See deployment in [Operations Runbook](../doc/05-Deployment-Operations-Runbook.md)

### For Business Analysts
1. Start with [Business Architecture](../doc/01-Business-Architecture.md)
2. Review each agent's business rules section
3. Understand decision criteria and regulatory compliance

---

## 📖 Related Documentation

- [Main README](../README.md)
- [Service Documentation](../services/README.md)
- [PlantUML Diagrams](../plantuml/README.md)
- [Core Architecture Docs](../doc/README.md)

---

*Last Updated: June 2, 2026*
