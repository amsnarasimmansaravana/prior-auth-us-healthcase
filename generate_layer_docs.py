#!/usr/bin/env python3
"""
Master Documentation Generator for Healthcare PA Platform
Generates comprehensive layer-by-layer documentation (.md + .puml)

Usage: python3 generate_layer_docs.py

Output: 18 files (9 .md + 9 .puml) for Layers 2-10
"""

import os
from pathlib import Path
from datetime import datetime

# Base directories
DOC_DIR = Path("doc")
PLANTUML_DIR = Path("plantuml")

# Ensure directories exist
DOC_DIR.mkdir(exist_ok=True)
PLANTUML_DIR.mkdir(exist_ok=True)

# ============================================================================
# LAYER DEFINITIONS
# ============================================================================

LAYERS = {
    2: {
        "name": "API Gateway Layer",
        "subtitle": "Kong Enterprise - 10 Gateway Types",
        "services": ["auth-gateway", "rate-limit-gateway", "llm-gateway", "vector-gateway", 
                    "graph-gateway", "cache-gateway", "firewall-gateway", "observability-gateway",
                    "data-gateway", "compliance-gateway"],
        "tech": "Kong Enterprise 3.4, Lua Plugins, Redis",
        "color": "#FFF8DC",
        "service_color": "#F39C12",
        "volume": "3.5M+ API calls/day",
        "latency": "<50ms total overhead",
    },
    3: {
        "name": "Orchestration Layer",
        "subtitle": "LangGraph + Temporal Workflow Engine",
        "services": ["workflow-engine-svc", "temporal-server", "state-manager-svc"],
        "tech": "LangGraph 0.2, Temporal.io 1.22, Python 3.11",
        "color": "#E6F7FF",
        "service_color": "#4A90E2",
        "volume": "50,000 workflows/day",
        "latency": "<5ms state operations",
    },
    4: {
        "name": "AI Agent Fabric Layer",
        "subtitle": "11 AI Agents with LLM Orchestration",
        "services": ["intake-agent", "eligibility-agent", "benefits-agent", "clinical-agent",
                    "policy-agent", "fraud-agent", "decision-agent", "appeals-agent",
                    "notification-agent", "audit-agent", "com-agent"],
        "tech": "GPT-4o, Claude 3.5, GPT-3.5 Turbo, LangGraph",
        "color": "#F5E6FF",
        "service_color": "#9B59B6",
        "volume": "385,000 agent executions/day",
        "latency": "1.2s - 8.3s per agent",
    },
    5: {
        "name": "Governance Layer",
        "subtitle": "Agent Registry, Prompt Management, Safety Evaluation",
        "services": ["agent-registry-svc", "prompt-mgmt-svc", "safety-eval-svc", "compliance-monitor-svc"],
        "tech": "FastAPI, LangSmith, Guardrails AI, PostgreSQL",
        "color": "#FFF5E6",
        "service_color": "#FFE4B5",
        "volume": "385,000 governance checks/day",
        "latency": "<100ms validation",
    },
    6: {
        "name": "MCP Layer",
        "subtitle": "Model Context Protocol - Tool Registry & Execution",
        "services": ["mcp-registry-svc", "tool-executor-svc"],
        "tech": "MCP SDK (Python), Docker Sandboxing, gRPC",
        "color": "#FFF5E6",
        "service_color": "#FFDAB9",
        "volume": "45+ tools, 200K+ invocations/day",
        "latency": "<200ms tool execution",
    },
    7: {
        "name": "Memory Layer",
        "subtitle": "Working, Episodic, Semantic & Procedural Memory",
        "services": ["working-memory-svc", "episodic-memory-svc", "semantic-memory-svc", "procedural-memory-svc"],
        "tech": "Redis, PostgreSQL, Milvus, FastAPI",
        "color": "#FFF5E6",
        "service_color": "#F5DEB3",
        "volume": "500M memory operations/day",
        "latency": "<10ms memory access",
    },
    8: {
        "name": "RAG Retrieval Layer",
        "subtitle": "Hybrid Retrieval - Vector, BM25 & Graph",
        "services": ["vector-search-svc", "hybrid-search-svc", "graph-rag-svc"],
        "tech": "Milvus 2.3, Elasticsearch 8, Neo4j 5.x, Python",
        "color": "#E8F5E9",
        "service_color": "#81C784",
        "volume": "50,000 searches/day",
        "latency": "45-120ms per search",
    },
    9: {
        "name": "Data Services Layer",
        "subtitle": "8 Domain Microservices with Database Access",
        "services": ["member-service", "provider-service", "policy-service", "claims-service",
                    "benefits-config-service", "network-service", "formulary-service", "clinical-content-service"],
        "tech": "FastAPI, gRPC, PostgreSQL, Redis Cache",
        "color": "#E3F2FD",
        "service_color": "#3498DB",
        "volume": "3.5M+ API calls/day",
        "latency": "25-120ms per query",
    },
    10: {
        "name": "HITL Layer",
        "subtitle": "Human-in-the-Loop Review & Approval",
        "services": ["hitl-routing-svc", "review-queue-svc", "approval-workflow-svc"],
        "tech": "Drools Rules Engine, React UI, Temporal, FastAPI",
        "color": "#FCE4EC",
        "service_color": "#F06292",
        "volume": "14,000 reviews/day (28% of cases)",
        "latency": "<4 hours review SLA",
    }
}

# ============================================================================
# MARKDOWN GENERATOR
# ============================================================================

def generate_markdown(layer_num, layer_info):
    """Generate comprehensive markdown documentation for a layer"""
    
    md_content = f"""# Layer {layer_num}: {layer_info['name']}
## {layer_info['subtitle']} - Healthcare Insurance PA Platform

**Layer Purpose**: {get_layer_purpose(layer_num)}  
**Services**: {len(layer_info['services'])} services  
**Technology Stack**: {layer_info['tech']}  
**Daily Volume**: {layer_info['volume']}  
**Performance**: {layer_info['latency']}

---

## Table of Contents
1. [Layer Overview](#layer-overview)
2. [Service Architecture](#service-architecture)
3. [Technical Implementation](#technical-implementation)
4. [API Specifications](#api-specifications)
5. [Data Flow](#data-flow)
6. [Database Connectivity](#database-connectivity)
7. [Performance & Scaling](#performance--scaling)
8. [Security & Compliance](#security--compliance)
9. [Monitoring & Operations](#monitoring--operations)

---

## Layer Overview

### Purpose
{get_layer_description(layer_num)}

### Architecture Principles
{get_architecture_principles(layer_num)}

---

## Service Architecture

### Service Inventory ({len(layer_info['services'])} Services)

{get_service_details(layer_num, layer_info)}

---

## Technical Implementation

### Deployment Architecture

```yaml
Kubernetes Namespace: {get_namespace(layer_num)}

{get_deployment_config(layer_num, layer_info)}

Ingress:
  Controller: nginx-ingress
  TLS: Let's Encrypt (cert-manager)
```

### Technology Stack

{get_tech_stack_details(layer_num)}

---

## API Specifications

{get_api_specs(layer_num)}

---

## Data Flow

{get_data_flow(layer_num)}

---

## Database Connectivity

{get_database_connectivity(layer_num)}

---

## Performance & Scaling

### Auto-Scaling Configuration

{get_scaling_config(layer_num)}

### Performance Metrics

{get_performance_metrics(layer_num)}

---

## Security & Compliance

{get_security_details(layer_num)}

---

## Monitoring & Operations

### Observability Stack

**Metrics**: Prometheus + Grafana
```yaml
Dashboards:
  - Layer {layer_num} Overview
    * Request rate per service
    * Error rate (4xx, 5xx)
    * Latency percentiles (P50, P95, P99)
    * Pod CPU/memory usage
```

**Logging**: Azure Log Analytics  
**Tracing**: Jaeger (OpenTelemetry)

### Alerting

{get_alerting_config(layer_num)}

---

## Summary

The **{layer_info['name']}** processes **{layer_info['volume']}** with **{layer_info['latency']}** latency. It provides critical {get_layer_summary(layer_num)} functionality for the PA platform.

**Key Metrics**:
- **{len(layer_info['services'])} services** deployed on AKS
- **{get_uptime_sla(layer_num)}** uptime SLA
- **{layer_info['latency']}** response times
- **HIPAA compliant** with end-to-end encryption

---

*Generated: {datetime.now().strftime("%B %d, %Y")} | Version: 1.0*
"""
    
    return md_content

# ============================================================================
# PLANTUML GENERATOR
# ============================================================================

def generate_plantuml(layer_num, layer_info):
    """Generate comprehensive PlantUML diagram for a layer"""
    
    puml_content = f"""@startuml layer-{layer_num:02d}-{layer_info['name'].lower().replace(' ', '-')}
!theme aws-orange
skinparam componentStyle rectangle
skinparam linetype ortho
skinparam nodesep 100
skinparam ranksep 80
skinparam backgroundColor #FAFAFA
skinparam shadowing false
skinparam defaultFontSize 11
skinparam componentFontSize 10

title <size:18><b>Layer {layer_num}: {layer_info['name']}</b></size>\\n<size:14>{layer_info['subtitle']} | {layer_info['volume']}</size>\\n\\n

{get_plantuml_components(layer_num, layer_info)}

{get_plantuml_connections(layer_num)}

{get_plantuml_notes(layer_num, layer_info)}

{get_plantuml_legend(layer_num, layer_info)}

@enduml
"""
    
    return puml_content

# ============================================================================
# HELPER FUNCTIONS - CONTENT GENERATORS
# ============================================================================

def get_layer_purpose(layer_num):
    purposes = {
        2: "API Gateway management, authentication, rate limiting, security, and LLM request routing",
        3: "Multi-agent workflow orchestration, state management, and durable execution",
        4: "AI-powered decision automation with 11 specialized LLM agents",
        5: "Agent lifecycle management, prompt optimization, and safety validation",
        6: "Tool discovery, registration, and sandboxed execution via Model Context Protocol",
        7: "Multi-tier memory system for agent context, history, and knowledge",
        8: "Hybrid retrieval combining vector search, BM25, and knowledge graphs",
        9: "Domain-specific data access services with caching and query optimization",
        10: "Risk-based human review routing and approval workflows"
    }
    return purposes.get(layer_num, "Layer functionality")

def get_layer_description(layer_num):
    descriptions = {
        2: """The **API Gateway Layer** serves as the single entry point for all API traffic, providing:
- **Authentication & Authorization**: OAuth2, JWT validation, RBAC
- **Rate Limiting**: Token bucket algorithm with Redis-backed counters
- **LLM Request Routing**: Intelligent routing to GPT-4o, Claude, GPT-3.5
- **Security**: WAF, prompt injection detection, jailbreak prevention
- **Observability**: Request tracing, metrics collection, logging
- **Caching**: Response caching with TTL-based invalidation

Kong Enterprise manages **10 specialized gateway types**, each handling specific concerns while maintaining a unified API surface.""",
        
        3: """The **Orchestration Layer** coordinates multi-agent workflows using:
- **LangGraph Supervisor Pattern**: Coordinates 11 AI agents in a directed graph
- **Temporal Durable Execution**: Ensures workflow reliability with automatic retries
- **State Management**: Redis for hot state, PostgreSQL for persistence
- **Checkpointing**: Workflow recovery from any point of failure
- **Timeout Management**: 30-minute SLA with automatic escalation
- **Conditional Routing**: Dynamic agent selection based on case complexity

This layer processes **50,000 PA workflows daily**, orchestrating an average of **7 agents per case**.""",
        
        4: """The **AI Agent Fabric** provides specialized AI decision-making with:
- **11 Specialized Agents**: Each agent handles a specific PA workflow step
- **Multi-Model Strategy**: GPT-4o (clinical), Claude 3.5 (policy), GPT-3.5 (eligibility)
- **RAG Integration**: Clinical agent uses hybrid retrieval for medical guidelines
- **Confidence Scoring**: Each agent returns decisions with confidence metrics
- **Tool Calling**: Agents invoke MCP tools for data access and calculations
- **Safety Guardrails**: Hallucination detection and toxicity filtering

Agents execute **385,000 times daily** (7 agents × 55,000 cases) with **96.2% success rate**.""",
        
        5: """The **Governance Layer** ensures AI safety and compliance through:
- **Agent Registry**: Metadata, versioning, capabilities catalog
- **Prompt Management**: Template versioning, A/B testing, optimization
- **Safety Evaluation**: Hallucination detection, bias checking, PII redaction
- **Compliance Monitoring**: ISO 42001 AIMS, audit trails, certification
- **Performance Tracking**: Agent execution metrics, token usage, costs
- **Quality Assurance**: Automated testing, regression detection

This layer validates **every agent execution** (385,000/day) in real-time.""",
        
        6: """The **MCP (Model Context Protocol) Layer** enables tool integration:
- **Tool Registry**: Catalog of 45+ tools (database queries, API calls, calculations)
- **Dynamic Discovery**: Agents discover tools at runtime based on capabilities
- **Sandboxed Execution**: Docker containers for secure tool execution
- **Protocol Compliance**: Full MCP specification implementation
- **Error Handling**: Graceful degradation when tools fail
- **Versioning**: Tool schema versioning with backward compatibility

Tools are invoked **200,000+ times daily** across all agent executions.""",
        
        7: """The **Memory Layer** provides multi-tier memory for agents:
- **Working Memory** (Redis, 5-min TTL): Agent scratchpad during workflow
- **Episodic Memory** (PostgreSQL, 90-day): Case history and conversation threads
- **Semantic Memory** (Milvus, permanent): Embeddings for similar case retrieval
- **Procedural Memory** (PostgreSQL, permanent): Workflow templates and best practices

This layer handles **500M memory operations daily** with sub-10ms latency.""",
        
        8: """The **RAG Retrieval Layer** powers clinical decision-making through:
- **Vector Search** (Milvus): Dense retrieval with HNSW index (10M embeddings)
- **Hybrid Search** (Elasticsearch): BM25 lexical + semantic search
- **Graph RAG** (Neo4j): Knowledge graph traversal for clinical pathways
- **Reciprocal Rank Fusion**: Merges results from all 3 sources (k=60)
- **Reranking**: Cross-encoder reranking for top 10 results

RAG pipeline processes **50,000 clinical searches daily** with **45-250ms latency**.""",
        
        9: """The **Data Services Layer** provides domain-specific data access:
- **8 Microservices**: Member, Provider, Policy, Claims, Benefits, Network, Formulary, Clinical
- **API Protocols**: gRPC (primary), REST (fallback)
- **Caching Strategy**: Cache-aside pattern with Redis (75% hit rate)
- **Query Optimization**: Connection pooling, prepared statements, indexes
- **Data Validation**: Pydantic models, schema validation
- **Multi-Database**: Routes to PostgreSQL, Elasticsearch, Neo4j as needed

Services handle **3.5M+ API calls daily** with **25-120ms latency**.""",
        
        10: """The **HITL (Human-in-the-Loop) Layer** manages human review:
- **Risk-Based Routing**: Drools rules engine routes 28% of cases to human review
- **Review Queue**: React-based UI for medical reviewers
- **Approval Workflows**: Multi-level approvals with Temporal orchestration
- **SLA Tracking**: 4-hour review turnaround target
- **Workload Distribution**: Skills-based routing to specialized reviewers
- **Audit Trail**: Complete review history for compliance

This layer routes **14,000 cases daily** to human reviewers (28% of total volume)."""
    }
    return descriptions.get(layer_num, "Layer description not available")

def get_architecture_principles(layer_num):
    principles = {
        2: """- **Single Entry Point**: All API traffic flows through Kong
- **Zero Trust**: Every request authenticated and authorized
- **Defense in Depth**: Multiple security layers (WAF, firewall, rate limit)
- **Observability First**: Every request traced and metered
- **High Availability**: 5 Kong nodes in active-active configuration""",
        
        3: """- **Reliability**: Durable execution with automatic retries
- **Scalability**: Horizontal scaling of workflow workers
- **Visibility**: Complete workflow state visibility
- **Fault Tolerance**: Checkpoint-based recovery
- **Performance**: Sub-5ms state operations with Redis""",
        
        4: """- **Specialization**: Each agent has a single responsibility
- **Composability**: Agents combine via LangGraph orchestration
- **Reliability**: Retry logic with exponential backoff
- **Safety**: Guardrails on every agent execution
- **Multi-Model**: Use best LLM for each task (GPT-4o, Claude, GPT-3.5)""",
        
        5: """- **Centralized Governance**: Single source of truth for agent metadata
- **Version Control**: Track all prompt and agent changes
- **Safety First**: Validate every agent response
- **Compliance**: ISO 42001 AIMS framework
- **Auditability**: Complete execution history""",
        
        6: """- **Protocol Compliance**: Full MCP specification adherence
- **Sandboxing**: Isolate tool execution in containers
- **Discoverability**: Dynamic tool catalog
- **Versioning**: Semantic versioning for tools
- **Error Handling**: Graceful degradation""",
        
        7: """- **Tiered Storage**: Hot (Redis), warm (PostgreSQL), cold (Milvus)
- **TTL-Based Expiry**: Automatic cleanup of stale data
- **Fast Access**: Sub-10ms memory retrieval
- **Persistence**: Critical data persisted to PostgreSQL
- **Scalability**: Distributed memory stores""",
        
        8: """- **Hybrid Approach**: Combine vector, lexical, and graph retrieval
- **Quality**: Reciprocal Rank Fusion for best results
- **Performance**: Parallel search execution
- **Accuracy**: 96% relevance for top 10 results
- **Scalability**: HNSW index for 10M+ vectors""",
        
        9: """- **Domain Isolation**: Each service owns its domain data
- **API-First**: Well-defined REST/gRPC interfaces
- **Caching**: 75% cache hit rate reduces database load
- **Connection Pooling**: Efficient database connections
- **Observability**: Full request tracing""",
        
        10: """- **Risk-Based**: Only route uncertain cases to humans
- **Efficiency**: Minimize human review burden
- **SLA Compliance**: Track and enforce 4-hour SLA
- **Skills-Based Routing**: Match cases to reviewer expertise
- **Audit Trail**: Complete review history"""
    }
    return principles.get(layer_num, "Architecture principles")

def get_service_details(layer_num, layer_info):
    # This would be extensive - simplified version here
    services_list = "\n".join([f"- **{svc}**: {get_service_description(layer_num, svc)}" for svc in layer_info['services']])
    return f"""
The {layer_info['name']} consists of **{len(layer_info['services'])} services**:

{services_list}

**Deployment**: Azure Kubernetes Service (AKS)  
**Scaling**: Horizontal Pod Autoscaler (HPA)  
**High Availability**: Multi-zone deployment
"""

def get_service_description(layer_num, service_name):
    # Simplified - would have detailed descriptions
    return f"Core {layer_num} layer component"

def get_namespace(layer_num):
    namespaces = {
        2: "api-gateway-layer",
        3: "orchestration-layer",
        4: "agent-fabric-layer",
        5: "governance-layer",
        6: "mcp-layer",
        7: "memory-layer",
        8: "rag-layer",
        9: "data-services-layer",
        10: "hitl-layer"
    }
    return namespaces.get(layer_num, f"layer-{layer_num}")

def get_deployment_config(layer_num, layer_info):
    services_config = "\n".join([f"""  - {svc}:
      replicas: 2-5 (HPA)
      resources:
        requests: {{ cpu: 200m, memory: 512Mi }}
        limits: {{ cpu: 1000m, memory: 2Gi }}""" for svc in layer_info['services'][:2]])
    
    return f"""Services:
{services_config}
  # ... ({len(layer_info['services'])} total services)
"""

def get_tech_stack_details(layer_num):
    return """
**Primary Technologies**: See service details above  
**Container Runtime**: containerd 1.7  
**Orchestration**: Kubernetes 1.28  
**Service Mesh**: Istio 1.20 (optional)
"""

def get_api_specs(layer_num):
    return """
### Common API Patterns

**Authentication**: JWT Bearer tokens  
**Rate Limiting**: 100 requests/minute per client  
**Error Responses**: RFC 7807 Problem Details
"""

def get_data_flow(layer_num):
    return f"""
### Request Flow

1. Request enters Layer {layer_num}
2. Service processes request
3. Data persisted/retrieved as needed
4. Response returned to caller
"""

def get_database_connectivity(layer_num):
    return """
### Database Access Patterns

**PostgreSQL**: Transactional data  
**Redis**: Caching and state  
**Connection Pooling**: 50 connections per service
"""

def get_scaling_config(layer_num):
    return """
```yaml
HorizontalPodAutoscaler:
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: 70%
```
"""

def get_performance_metrics(layer_num):
    return """
| Service | P50 | P95 | P99 | Throughput |
|---------|-----|-----|-----|------------|
| Primary | 50ms | 120ms | 350ms | 1000 req/s |
"""

def get_security_details(layer_num):
    return """
**Encryption**: TLS 1.3 (transit), AES-256 (rest)  
**Authentication**: OAuth 2.0 + JWT  
**Authorization**: RBAC with OPA policies  
**Compliance**: HIPAA, SOC 2, ISO 27001
"""

def get_alerting_config(layer_num):
    return """
```yaml
Alerts:
  - name: HighErrorRate
    condition: error_rate > 5% for 5 minutes
    severity: critical
  - name: SlowResponseTime
    condition: p95_latency > 2s for 10 minutes
    severity: warning
```
"""

def get_layer_summary(layer_num):
    summaries = {
        2: "API gateway, security, and routing",
        3: "workflow orchestration and state management",
        4: "AI-powered decision automation",
        5: "governance, safety, and compliance",
        6: "tool discovery and execution",
        7: "memory and context management",
        8: "hybrid RAG retrieval",
        9: "data access and caching",
        10: "human review and approval"
    }
    return summaries.get(layer_num, "core platform")

def get_uptime_sla(layer_num):
    return "99.95%"

def get_plantuml_components(layer_num, layer_info):
    components_list = "\n".join([f'    component "{svc}\\n({layer_info["tech"].split(",")[0]})" as {svc.replace("-", "_")} {layer_info["service_color"]}' for svc in layer_info['services'][:4]])
    
    return f"""rectangle "**LAYER {layer_num}: {layer_info['name'].upper()}**" as Layer{layer_num} {layer_info['color']} {{
    
{components_list}
    
    note right
      <b>{len(layer_info['services'])} Services</b>
      {layer_info['volume']}
      {layer_info['latency']}
    end note
}}

database "PostgreSQL" as DB #E74C3C
database "Redis" as Cache #FF7043"""

def get_plantuml_connections(layer_num):
    return f"""' Connections
Layer{layer_num} -[#0066CC,thickness=2]down-> DB : <b>Data Access</b>
Layer{layer_num} -[#666666,dashed]down-> Cache : <b>Caching</b>"""

def get_plantuml_notes(layer_num, layer_info):
    return f"""note top of Layer{layer_num}
  <b>LAYER {layer_num} METRICS</b>
  • Services: {len(layer_info['services'])}
  • Volume: {layer_info['volume']}
  • Latency: {layer_info['latency']}
  • Tech: {layer_info['tech']}
end note"""

def get_plantuml_legend(layer_num, layer_info):
    return f"""legend bottom right
  <b>Layer {layer_num}: {layer_info['name']}</b>
  
  Services: {len(layer_info['services'])}
  Technology: {layer_info['tech']}
  Volume: {layer_info['volume']}
  Performance: {layer_info['latency']}
  
  Generated: {datetime.now().strftime("%B %d, %Y")}
endlegend"""

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Generate all layer documentation files"""
    
    print("=" * 70)
    print("Healthcare PA Platform - Layer Documentation Generator")
    print("=" * 70)
    print(f"Generating documentation for Layers 2-10...")
    print(f"Output: 18 files (9 .md + 9 .puml)\n")
    
    total_files = 0
    total_lines = 0
    
    for layer_num in range(2, 11):
        layer_info = LAYERS[layer_num]
        
        # Generate markdown
        md_file = DOC_DIR / f"layer-{layer_num:02d}-{layer_info['name'].lower().replace(' ', '-').replace('layer', '').strip()}.md"
        md_content = generate_markdown(layer_num, layer_info)
        
        with open(md_file, 'w') as f:
            f.write(md_content)
        
        md_lines = len(md_content.split('\n'))
        total_lines += md_lines
        total_files += 1
        
        print(f"✓ Created {md_file.name} ({md_lines} lines)")
        
        # Generate PlantUML
        puml_file = PLANTUML_DIR / f"layer-{layer_num:02d}-{layer_info['name'].lower().replace(' ', '-').replace('layer', '').strip()}.puml"
        puml_content = generate_plantuml(layer_num, layer_info)
        
        with open(puml_file, 'w') as f:
            f.write(puml_content)
        
        puml_lines = len(puml_content.split('\n'))
        total_lines += puml_lines
        total_files += 1
        
        print(f"✓ Created {puml_file.name} ({puml_lines} lines)")
        print()
    
    print("=" * 70)
    print(f"✅ SUCCESS! Generated {total_files} files ({total_lines:,} total lines)")
    print("=" * 70)
    print("\nFiles created:")
    print(f"  • Markdown docs: doc/layer-02-*.md through layer-10-*.md")
    print(f"  • PlantUML diagrams: plantuml/layer-02-*.puml through layer-10-*.puml")
    print("\nNext steps:")
    print("  1. Review generated documentation in doc/ folder")
    print("  2. Render PlantUML diagrams (VS Code PlantUML extension or plantuml command)")
    print("  3. Customize content as needed for your specific requirements")
    print()

if __name__ == "__main__":
    main()
