# PlantUML Architecture Diagrams
## Healthcare Insurance Multi-Agent AI Platform

This folder contains comprehensive PlantUML diagrams for the Healthcare Insurance Multi-Agent AI Platform, covering business workflows, technical architecture, and operational aspects.

---

## 📂 Diagram Inventory

### Business Architecture
| File | Description | Key Content |
|------|-------------|-------------|
| [01-business-pa-workflow.puml](01-business-pa-workflow.puml) | Prior Authorization business workflow | End-to-end PA process, stakeholders, decision points, SLA metrics |

### Technical Architecture
| File | Description | Key Content |
|------|-------------|-------------|
| [02-enterprise-10-layer-architecture.puml](02-enterprise-10-layer-architecture.puml) | Complete 10-layer enterprise architecture | Channel, API Gateway, Orchestration, Agent Fabric, Governance, MCP, Memory, RAG, Data Services, HITL layers |
| [03-multi-agent-orchestration-langgraph.puml](03-multi-agent-orchestration-langgraph.puml) | LangGraph supervisor pattern orchestration | State machine, conditional routing, parallel execution, agent nodes |
| [04-10-gateway-types-architecture.puml](04-10-gateway-types-architecture.puml) | 10 specialized gateway types | AI Gateway, Security Gateway (LLM Firewall), Agent Gateway, MCP Gateway, LLM Gateway, Human Approval Gateway, Data Gateway, Vector Gateway, Workflow Gateway, Observability Gateway |
| [07-rag-hybrid-retrieval-architecture.puml](07-rag-hybrid-retrieval-architecture.puml) | RAG hybrid retrieval system | Vector search (Milvus), BM25 keyword search, Knowledge Graph (Neo4j), Reciprocal Rank Fusion, Reranking, Context compression |
| [10-agent-to-agent-protocol.puml](10-agent-to-agent-protocol.puml) | A2A protocol specification | Message structure, authentication, schema validation, observability, error handling |
| [12-complete-microservice-architecture.puml](12-complete-microservice-architecture.puml) | Complete sequential flow diagram | End-to-end PA request flow with all 55+ services, 6 databases, 11 agents, 50-step detailed sequence |
| [13-microservice-workflow-architecture.puml](13-microservice-workflow-architecture.puml) | **Enterprise workflow component diagram (NEW)** | **Workflow-based visual architecture showing all layers, services, agents, databases with color-coded connections and metrics** |

### Security & Governance
| File | Description | Key Content |
|------|-------------|-------------|
| [05-zero-trust-security-architecture.puml](05-zero-trust-security-architecture.puml) | Zero Trust security implementation | 7 security layers, AAD, MFA, mTLS, OPA, PHI protection, SIEM |
| [11-iso-42001-governance-framework.puml](11-iso-42001-governance-framework.puml) | ISO 42001 AI governance framework | Certification process, AIMS components, agent lifecycle, AIIA template, compliance monitoring |

### Deployment & Operations
| File | Description | Key Content |
|------|-------------|-------------|
| [06-cicd-deployment-pipeline.puml](06-cicd-deployment-pipeline.puml) | CI/CD deployment pipeline | GitHub Actions, security scanning, testing, canary deployment, multi-region rollout, rollback |
| [09-multi-region-active-active-deployment.puml](09-multi-region-active-active-deployment.puml) | Multi-region deployment architecture | East US 2 (primary), West US 2 (secondary), Azure Front Door, Traffic Manager, HA configuration, DR strategy |

### Quality & Evaluation
| File | Description | Key Content |
|------|-------------|-------------|
| [08-15-level-evaluation-framework.puml](08-15-level-evaluation-framework.puml) | Comprehensive 15-level evaluation framework | Business KPIs, Agent performance, Tool calling, Multi-step reasoning, Multi-agent collaboration, RAG, Safety, Compliance, HITL, Operations, Cost, Reliability, Memory, Hallucination, LLMOps |

---

## 🎨 Rendering PlantUML Diagrams

### Option 1: VS Code Extension
1. Install **PlantUML** extension by jebbs
2. Install **Graphviz** (required): `brew install graphviz` (macOS) or `apt install graphviz` (Linux)
3. Open any `.puml` file
4. Press `Alt+D` or `Cmd+Option+P` to preview
5. Export to PNG/SVG: Right-click → Export Current Diagram

### Option 2: Online Renderer
1. Visit [PlantUML Online Server](http://www.plantuml.com/plantuml/)
2. Copy & paste `.puml` file content
3. Click "Submit" to render
4. Download as PNG/SVG

### Option 3: Command Line
```bash
# Install PlantUML
brew install plantuml  # macOS
# or
apt install plantuml   # Linux

# Render all diagrams to PNG
plantuml plantuml/*.puml

# Render to SVG (better for documentation)
plantuml -tsvg plantuml/*.puml

# Render specific file
plantuml plantuml/02-enterprise-10-layer-architecture.puml
```

### Option 4: Docker
```bash
# Render all diagrams using Docker
docker run --rm -v $(pwd)/plantuml:/data plantuml/plantuml:latest -tpng "/data/*.puml"

# Render to SVG
docker run --rm -v $(pwd)/plantuml:/data plantuml/plantuml:latest -tsvg "/data/*.puml"
```

---

## 📊 Diagram Statistics

| Category | Diagrams | Lines of Code | Complexity |
|----------|----------|---------------|------------|
| **Business** | 1 | ~400 | Medium |
| **Architecture** | 5 | ~3,000 | High |
| **Security** | 2 | ~800 | High |
| **Deployment** | 2 | ~1,200 | High |
| **Evaluation** | 1 | ~600 | Medium |
| **TOTAL** | **11** | **~6,000** | **Enterprise** |

---

## 🔑 Key Diagram Features

### ✅ Comprehensive Coverage
- **Business flows**: PA workflow with decision points, SLA metrics
- **Technical architecture**: 10-layer stack, all components detailed
- **Multi-agent orchestration**: LangGraph state machine with all nodes
- **10 Gateway types**: Complete taxonomy with responsibilities
- **RAG system**: Hybrid retrieval with vector + keyword + graph
- **Security**: Zero Trust architecture with 7 layers
- **Governance**: ISO 42001 certification framework
- **Deployment**: Multi-region active-active with DR
- **CI/CD**: Full pipeline from commit to production
- **Evaluation**: 15-level comprehensive framework
- **A2A Protocol**: Complete message lifecycle

### ✅ Enterprise Quality
- **Detailed annotations**: Every component explained
- **Metrics included**: Latency, throughput, costs, SLAs
- **Real-world data**: 50K PAs/day, 99.9% uptime, $80M savings
- **Production-ready**: Actual configurations, not theoretical
- **Compliance-focused**: HIPAA, CMS, ISO 27001/42001

### ✅ Professional Design
- **Consistent styling**: Color-coded by layer/concern
- **Clear flow**: Left-to-right or top-to-bottom logic
- **Component hierarchy**: C4 model influence
- **Notes & legends**: Extensive documentation inline
- **Metrics callouts**: Performance data visible

---

## 🎯 Use Cases

### For Executives
- **01-business-pa-workflow.puml**: Understand business value and ROI
- **08-15-level-evaluation-framework.puml**: See quality assurance framework
- **11-iso-42001-governance-framework.puml**: Understand governance & compliance

### For Architects
- **02-enterprise-10-layer-architecture.puml**: Full system architecture
- **04-10-gateway-types-architecture.puml**: Gateway design patterns
- **07-rag-hybrid-retrieval-architecture.puml**: RAG implementation
- **09-multi-region-active-active-deployment.puml**: Infrastructure design

### For Developers
- **03-multi-agent-orchestration-langgraph.puml**: Agent coordination logic
- **10-agent-to-agent-protocol.puml**: A2A communication protocol
- **06-cicd-deployment-pipeline.puml**: Deployment process

### For Security Teams
- **05-zero-trust-security-architecture.puml**: Complete security model
- **11-iso-42001-governance-framework.puml**: AI governance controls

### For Operations
- **09-multi-region-active-active-deployment.puml**: Infrastructure topology
- **06-cicd-deployment-pipeline.puml**: Release process
- **08-15-level-evaluation-framework.puml**: Monitoring & metrics

---

## 📖 Documentation Alignment

These PlantUML diagrams are generated from the comprehensive documentation in `/doc`:

1. **[01-Business-Architecture.md](../doc/01-Business-Architecture.md)** (3,494 lines)
   - Source for: 01-business-pa-workflow.puml

2. **[02-Enterprise-Solution-Architecture.md](../doc/02-Enterprise-Solution-Architecture.md)** (5,658 lines)
   - Source for: 02-enterprise-10-layer-architecture.puml, 04-10-gateway-types-architecture.puml, 10-agent-to-agent-protocol.puml

3. **[03-Agentic-AI-Platform-Architecture.md](../doc/03-Agentic-AI-Platform-Architecture.md)** (4,027 lines)
   - Source for: 03-multi-agent-orchestration-langgraph.puml, 07-rag-hybrid-retrieval-architecture.puml

4. **[04-Enterprise-Security-Governance-Compliance.md](../doc/04-Enterprise-Security-Governance-Compliance.md)** (3,967 lines)
   - Source for: 05-zero-trust-security-architecture.puml, 11-iso-42001-governance-framework.puml

5. **[05-Deployment-Operations-Runbook.md](../doc/05-Deployment-Operations-Runbook.md)** (4,028 lines)
   - Source for: 06-cicd-deployment-pipeline.puml, 09-multi-region-active-active-deployment.puml, 08-15-level-evaluation-framework.puml

**Total Documentation**: 21,174 lines → **11 comprehensive PlantUML diagrams**

---

## 🚀 Quick Start

### Render All Diagrams (PNG)
```bash
cd plantuml
plantuml *.puml
```

This creates PNG files for all diagrams in the same folder.

### Render All Diagrams (SVG - Recommended)
```bash
cd plantuml
plantuml -tsvg *.puml
```

SVG format is better for:
- Scalability (vector graphics)
- Web embedding
- Documentation
- Presentations

### Export to Confluence/Wiki
1. Render to SVG: `plantuml -tsvg *.puml`
2. Upload SVG files to Confluence attachments
3. Embed in pages using `!image.svg!` macro

### Export to PowerPoint/Keynote
1. Render to PNG at high DPI: `plantuml -tpng -Sdpi=300 *.puml`
2. Import PNG files into slides
3. Or convert PNG → PDF → insert in slides

---

## 🛠️ Customization

### Change Color Scheme
Edit `skinparam` at the top of each file:
```plantuml
skinparam backgroundColor #FFFFFF  ' White background
skinparam defaultFontName Arial   ' Font
skinparam defaultFontSize 11      ' Size
```

### Export Different Formats
```bash
# PNG (default)
plantuml diagram.puml

# SVG (vector)
plantuml -tsvg diagram.puml

# PDF
plantuml -tpdf diagram.puml

# ASCII art (terminal)
plantuml -ttxt diagram.puml

# LaTeX
plantuml -tlatex diagram.puml
```

### High-Resolution Export
```bash
# 300 DPI (print quality)
plantuml -Sdpi=300 -tpng diagram.puml

# 600 DPI (professional print)
plantuml -Sdpi=600 -tpng diagram.puml
```

---

## 📝 Maintenance

### Updating Diagrams
When documentation in `/doc` changes:

1. **Identify affected diagrams** (see Documentation Alignment above)
2. **Edit `.puml` files** with new information
3. **Re-render** to verify changes
4. **Commit** updated `.puml` files (not rendered images)
5. **Document changes** in commit message

### Version Control
- **Commit**: `.puml` source files (text-based, diff-friendly)
- **Ignore**: Rendered `.png`, `.svg` files (binary, large)
- **Exception**: Can commit final rendered images for releases

### Quality Checks
Before committing:
- ✅ Render successfully (no syntax errors)
- ✅ All text readable
- ✅ Metrics/numbers accurate
- ✅ Consistent with documentation
- ✅ Notes/annotations complete

---

## 🔗 Related Documentation

- [Main README](../README.md) - Project overview
- [Documentation Folder](../doc/) - Comprehensive architecture docs
- [Tracking Folder](../tracking/) - Progress and enhancement maps
- [ALIGNMENT_PROGRESS.md](../tracking/ALIGNMENT_PROGRESS.md) - Documentation status

---

## 📞 Support

For diagram issues or questions:
- Review PlantUML documentation: https://plantuml.com/
- Check C4 model syntax: https://github.com/plantuml-stdlib/C4-PlantUML
- Internal: Contact Architecture Team

---

**Generated from**: 21,174 lines of comprehensive documentation  
**Diagram Count**: 11 enterprise-grade diagrams  
**Coverage**: Business, Architecture, Security, Deployment, Evaluation  
**Quality**: Production-ready, metrics-driven, compliance-focused  

---

*Last Updated: June 1, 2026*
