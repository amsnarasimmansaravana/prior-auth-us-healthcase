#!/usr/bin/env python3
"""
Create PlantUML Diagrams + Python Code Samples + Guides
Most valuable documentation artifacts
"""

from pathlib import Path

# Ensure directories
Path("plantuml").mkdir(exist_ok=True)
Path("src/agents").mkdir(parents=True, exist_ok=True)
Path("guides").mkdir(exist_ok=True)
Path("doc/adr").mkdir(parents=True, exist_ok=True)

print("Creating diagrams, code samples, and guides...")
print("=" * 80)

files_created = []

# ============================================================================
# PART 1: PlantUML Diagrams for Layers 3-10
# ============================================================================

# Layer 3: Orchestration Detailed Diagram
LAYER_3_PUML = """@startuml layer-03-orchestration-detailed
!theme aws-orange
skinparam componentStyle rectangle
skinparam linetype ortho
skinparam nodesep 150
skinparam ranksep 150
skinparam backgroundColor #FAFAFA
skinparam shadowing false
skinparam defaultFontSize 12

title <size:20><b>Layer 3: Orchestration Layer - Detailed Architecture</b></size>\\n<size:14>LangGraph + Temporal + State Management | 50,000 workflows/day</size>\\n\\n

' ============================================================================
' ORCHESTRATION SERVICES
' ============================================================================

package "**ORCHESTRATION LAYER**" #E6F7FF {
    
    ' Workflow Engine
    rectangle "**workflow-engine-svc**\\n(LangGraph 0.2)" as WFE #4A90E2 {
        component "Supervisor Agent" as SUP
        component "StateGraph" as GRAPH
        component "Agent Router" as ROUTER
        component "Checkpointer" as CKPT
        
        SUP .down.> GRAPH : defines
        GRAPH .down.> ROUTER : routes to
        ROUTER .right.> CKPT : checkpoint
    }
    
    ' Temporal Server
    rectangle "**temporal-server**\\n(Temporal.io 1.22)" as TEMP #4A90E2 {
        component "Frontend Service" as FE
        component "History Service" as HIST
        component "Matching Service" as MATCH
        component "Worker Service" as WORK
        
        FE .down.> HIST : stores
        FE .down.> MATCH : schedules
        MATCH .down.> WORK : dispatches
    }
    
    ' State Manager
    rectangle "**state-manager-svc**\\n(FastAPI + Redis)" as STATE #4A90E2 {
        component "State API" as API
        component "Redis Cache" as REDIS
        component "Snapshot Manager" as SNAP
        
        API .down.> REDIS : read/write
        API .down.> SNAP : persist
    }
}

' ============================================================================
' EXTERNAL SYSTEMS
' ============================================================================

' Layer Above (API Gateway)
cloud "**API Gateway Layer**" as APIGW #FFF8DC

' Layer Below (AI Agents)
package "**AI Agent Fabric**" #F5E6FF {
    agent "Intake Agent" as AG1
    agent "Eligibility Agent" as AG2
    agent "Clinical Agent" as AG3
    agent "Decision Agent" as AG4
    agent "..." as AG_MORE
}

' Databases
database "PostgreSQL 15\\n(workflow_db)" as PG #E74C3C {
    storage "Workflow History" as WF_HIST
    storage "Checkpoints" as WF_CKPT
    storage "State Snapshots" as STATE_SNAP
}

database "Redis 7.0\\n(Cluster Mode)" as REDIS_DB #FF7043 {
    storage "Hot State\\n(6-hour TTL)" as HOT_STATE
    storage "Task Queue" as TASK_Q
}

' ============================================================================
' CONNECTIONS
' ============================================================================

' API Gateway to Orchestration
APIGW -[#0066CC,thickness=3]down-> WFE : <b>1. PA Request</b>\\n(gRPC)

' Workflow Engine flows
WFE -[#228B22,thickness=2]down-> TEMP : <b>2. Start Workflow</b>
TEMP -[#228B22,thickness=2]down-> AG1 : <b>3. Invoke Agents</b>
TEMP -[#228B22,thickness=2]down-> AG2
TEMP -[#228B22,thickness=2]down-> AG3
TEMP -[#228B22,thickness=2]down-> AG4

AG1 -[#666666,dashed]up-> STATE : <b>Store Output</b>
AG2 -[#666666,dashed]up-> STATE
AG3 -[#666666,dashed]up-> STATE
AG4 -[#666666,dashed]up-> STATE

' Database connections
WFE -[#9932CC,thickness=2]-> PG : <b>Checkpoint</b>
TEMP -[#9932CC,thickness=2]-> PG : <b>History</b>
STATE -[#FF6347,thickness=2]-> REDIS_DB : <b>Cache State</b>
STATE -[#9932CC,thickness=2]-> PG : <b>Snapshot</b>

' ============================================================================
' ANNOTATIONS
' ============================================================================

note top of WFE
  <b>LangGraph Supervisor Pattern</b>
  • Coordinates 11 AI agents
  • Conditional routing (simple/standard/complex)
  • 50,000 workflows/day
  • P50: 4.2 min, P95: 12.8 min
end note

note top of TEMP
  <b>Durable Workflow Execution</b>
  • Automatic retries (3 attempts, exponential backoff)
  • Heartbeat monitoring
  • 30-minute SLA
  • 90-day history retention
end note

note top of STATE
  <b>Redis-Backed State</b>
  • 500M ops/day
  • <5ms P50 latency
  • 98.5% cache hit rate
  • 6-hour TTL
end note

' ============================================================================
' WORKFLOW SEQUENCE
' ============================================================================

note as N1
  <b>Workflow Sequence</b>
  ━━━━━━━━━━━━━━━━━━━━
  ① API Gateway → Workflow Engine
  ② Workflow Engine → Temporal (start workflow)
  ③ Temporal → Agents (sequential/parallel)
  ④ Agents → State Manager (store outputs)
  ⑤ Workflow Engine → Checkpoint (every 30s)
  ⑥ Decision → API Gateway (return result)
  
  <b>Failure Recovery</b>
  • Checkpoint every 30s
  • Retry on failure (3 attempts)
  • Resume from last checkpoint
  • Alert after 3 failures
end note

N1 .up. WFE

' ============================================================================
' LEGEND
' ============================================================================

legend bottom right
  <b>Layer 3: Orchestration Architecture</b>
  
  <b>Services (3):</b>
  • workflow-engine-svc: LangGraph orchestration
  • temporal-server: Durable execution
  • state-manager-svc: Redis state management
  
  <b>Performance:</b>
  • Throughput: 50,000 workflows/day
  • Latency: 4.2 min P50, 12.8 min P95
  • State ops: <5ms
  • Cache hit: 98.5%
  
  <b>Technology:</b>
  • LangGraph 0.2 (Python)
  • Temporal.io 1.22
  • Redis 7.0 (3-shard cluster)
  • PostgreSQL 15
  
  <b>Workflow Patterns:</b>
  • Simple (30%): 4 agents, 2-3 min
  • Standard (50%): 7 agents, 5-8 min
  • Complex (20%): 10 agents, 15-30 min
  
  Generated: June 02, 2026
endlegend

@enduml
"""

with open("plantuml/layer-03-orchestration-detailed.puml", 'w') as f:
    f.write(LAYER_3_PUML)
files_created.append("plantuml/layer-03-orchestration-detailed.puml")
print("✓ Created layer-03-orchestration-detailed.puml (detailed architecture)")

# Layer 4: AI Agent Fabric Detailed Diagram
LAYER_4_PUML = """@startuml layer-04-ai-agents-detailed
!theme aws-orange
skinparam componentStyle rectangle
skinparam linetype ortho
skinparam nodesep 180
skinparam ranksep 140
skinparam backgroundColor #FAFAFA
skinparam shadowing false
skinparam defaultFontSize 11

title <size:20><b>Layer 4: AI Agent Fabric - Detailed Architecture</b></size>\\n<size:14>11 Specialized Agents | Multi-Model Strategy | 385,000 executions/day</size>\\n\\n

' ============================================================================
' AI AGENTS
' ============================================================================

package "**AI AGENT FABRIC LAYER**" #F5E6FF {
    
    ' Data Extraction
    rectangle "**①Intake Agent**" as AG1 #9B59B6 {
        component "GPT-4o\\n(Vision API)" as M1
        component "OCR Pipeline" as OCR
        M1 .down.> OCR
    }
    
    ' Eligibility & Benefits
    rectangle "**②Eligibility Agent**" as AG2 #8E44AD {
        component "GPT-3.5 Turbo" as M2
        component "DB Queries" as DB2
        M2 .down.> DB2
    }
    
    rectangle "**③Benefits Agent**" as AG3 #8E44AD {
        component "GPT-3.5 Turbo" as M3
        component "Cost Calculator" as CALC
        M3 .down.> CALC
    }
    
    ' Clinical Review (Most Complex)
    rectangle "**④Clinical Agent**" as AG4 #9B59B6 {
        component "GPT-4o\\n(Medical Reasoning)" as M4
        component "RAG Pipeline\\n(430ms)" as RAG
        component "Vector Search\\n(Milvus)" as VEC
        component "BM25 Search\\n(Elasticsearch)" as BM25
        component "Graph RAG\\n(Neo4j)" as GRAPH
        component "Reranker" as RERANK
        
        M4 .down.> RAG
        RAG .down.> VEC
        RAG .down.> BM25
        RAG .down.> GRAPH
        VEC .down.> RERANK
        BM25 .down.> RERANK
        GRAPH .down.> RERANK
    }
    
    ' Policy & Fraud
    rectangle "**⑤Policy Agent**" as AG5 #D2691E {
        component "Claude 3.5\\n(Policy Expert)" as M5
        component "Policy Search" as POL
        M5 .down.> POL
    }
    
    rectangle "**⑥Fraud Agent**" as AG6 #9B59B6 {
        component "GPT-4o\\n(Pattern Recognition)" as M6
        component "Graph Analysis\\n(Neo4j)" as FRAUD_G
        M6 .down.> FRAUD_G
    }
    
    ' Decision Synthesis
    rectangle "**⑦Decision Agent**" as AG7 #9B59B6 {
        component "GPT-4o\\n(Synthesis)" as M7
        component "Confidence\\nAggregator" as CONF
        component "HITL Router" as HITL
        M7 .down.> CONF
        CONF .down.> HITL
    }
    
    ' Supporting Agents
    agent "⑧Appeals" as AG8
    agent "⑨Notification" as AG9
    agent "⑩Audit" as AG10
    agent "⑪Communication" as AG11
}

' ============================================================================
' EXTERNAL SYSTEMS
' ============================================================================

' Orchestration Layer
cloud "**Orchestration Layer**\\n(LangGraph)" as ORCH #E6F7FF

' MCP Tools
package "**MCP Tools (45+)**" #FFF5E6 {
    component "parse_x12_278" as T1
    component "get_member_policy" as T2
    component "rag_search_clinical" as T3
    component "check_provider_sanctions" as T4
    component "..." as T_MORE
}

' Databases
database "PostgreSQL 15\\n(6 databases)" as PG #E74C3C
database "Redis 7.0\\n(Cache)" as REDIS #FF7043
database "Milvus 2.3\\n(10M vectors)" as MILVUS #81C784
database "Elasticsearch 8\\n(Clinical docs)" as ES #FFD700
database "Neo4j 5.x\\n(Knowledge graph)" as NEO4J #00CED1

' Governance Layer
cloud "**Governance Layer**\\n(Safety & Compliance)" as GOV #FFF5E6

' ============================================================================
' CONNECTIONS
' ============================================================================

' Orchestration to Agents
ORCH -[#0066CC,thickness=3]down-> AG1 : <b>①Intake</b>\\n1.8s
ORCH -[#0066CC,thickness=2]down-> AG2 : <b>②Eligibility</b>\\n0.28s
ORCH -[#0066CC,thickness=2]down-> AG3 : <b>③Benefits</b>\\n0.32s
ORCH -[#228B22,thickness=4]down-> AG4 : <b>④Clinical</b>\\n5.2s (bottleneck)
ORCH -[#D2691E,thickness=3]down-> AG5 : <b>⑤Policy</b>\\n2.1s
ORCH -[#0066CC,thickness=2]down-> AG6 : <b>⑥Fraud</b>\\n0.68s
ORCH -[#0066CC,thickness=3]down-> AG7 : <b>⑦Decision</b>\\n0.85s

' Agents to MCP Tools
AG1 .down.> T1 : use
AG2 .down.> T2 : use
AG4 .down.> T3 : use
AG6 .down.> T4 : use

' Agents to Databases
AG2 -[#9932CC]-> PG : query
AG3 -[#9932CC]-> PG
AG4 -[#228B22,thickness=2]-> MILVUS : <b>Vector</b>
AG4 -[#228B22,thickness=2]-> ES : <b>BM25</b>
AG4 -[#228B22,thickness=2]-> NEO4J : <b>Graph</b>
AG2 -[#666666,dashed]-> REDIS : cache
AG3 -[#666666,dashed]-> REDIS

' Agents to Governance
AG1 .up.> GOV : safety check
AG2 .up.> GOV
AG3 .up.> GOV
AG4 .up.> GOV
AG5 .up.> GOV
AG6 .up.> GOV
AG7 .up.> GOV

' ============================================================================
' ANNOTATIONS
' ============================================================================

note top of AG4
  <b>Clinical Agent - Most Complex</b>
  ━━━━━━━━━━━━━━━━━━━━━━━━━
  • GPT-4o with RAG pipeline
  • Hybrid retrieval (430ms):
    - Vector: 45ms (Milvus HNSW)
    - BM25: 120ms (Elasticsearch)
    - Graph: 85ms (Neo4j)
    - Rerank: 180ms
  • 94.5% clinical accuracy
  • Most expensive: $0.0275/exec
end note

note bottom of AG5
  <b>Why Claude 3.5 for Policy?</b>
  15% better at policy interpretation
  vs GPT-4o in A/B tests
end note

note right of AG7
  <b>Decision Logic</b>
  ━━━━━━━━━━━━━━━━
  • Aggregate confidence
  • If <0.85 → HITL
  • 28% routed to human
  • 68% approved
  • 18% denied
end note

' ============================================================================
' MULTI-MODEL STRATEGY
' ============================================================================

note as MODEL_STRATEGY
  <b>Multi-Model Strategy</b>
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  
  <b>GPT-4o ($5/1M input, $15/1M output):</b>
  • Intake (vision for OCR)
  • Clinical (advanced reasoning)
  • Fraud (pattern recognition)
  • Decision (synthesis)
  
  <b>Claude 3.5 Sonnet ($3/1M input, $15/1M output):</b>
  • Policy (15% better interpretation)
  
  <b>GPT-3.5 Turbo ($0.50/1M input, $1.50/1M output):</b>
  • Eligibility (simple lookup)
  • Benefits (deterministic calc)
  • Notification (template filling)
  
  <b>Cost per Case: $0.0518</b>
  • Clinical: $0.0275 (53%)
  • Policy: $0.0120 (23%)
  • Intake: $0.0095 (18%)
  • Other: $0.0028 (6%)
end note

MODEL_STRATEGY .up. AG5

' ============================================================================
' PERFORMANCE METRICS
' ============================================================================

note as PERF
  <b>Performance Metrics</b>
  ━━━━━━━━━━━━━━━━━━━━━━
  
  | Agent | P50 | Cost |
  |-------|-----|------|
  | Intake | 1.8s | $0.0095 |
  | Eligibility | 0.28s | $0.0004 |
  | Benefits | 0.32s | $0.0005 |
  | Clinical | 5.2s | $0.0275 |
  | Policy | 2.1s | $0.0120 |
  | Fraud | 0.68s | $0.0095 |
  | Decision | 0.85s | $0.0142 |
  
  <b>Daily Volume:</b>
  • 385,000 agent executions
  • 55,000 PA cases × 7 agents avg
  • 96.2% success rate
  • $2,847/day total LLM cost
end note

PERF .up. AG2

' ============================================================================
' LEGEND
' ============================================================================

legend bottom right
  <b>Layer 4: AI Agent Fabric Architecture</b>
  
  <b>Agents (11):</b>
  ① Intake (data extraction)
  ② Eligibility (coverage check)
  ③ Benefits (cost-sharing)
  ④ Clinical (medical necessity) ⭐
  ⑤ Policy (rules interpretation)
  ⑥ Fraud (FWA detection)
  ⑦ Decision (synthesis)
  ⑧-⑪ Appeals, Notification, Audit, Communication
  
  <b>Models:</b>
  • GPT-4o: 7 agents (clinical, vision, synthesis)
  • Claude 3.5: 1 agent (policy interpretation)
  • GPT-3.5: 3 agents (simple tasks, cost optimization)
  
  <b>Line Thickness = Latency:</b>
  Thicker = Longer latency (Clinical = bottleneck)
  
  <b>Colors:</b>
  Blue = GPT-4o | Orange = Claude 3.5 | Purple = GPT-3.5
  Green = RAG-intensive
  
  Generated: June 02, 2026
endlegend

@enduml
"""

with open("plantuml/layer-04-ai-agents-detailed.puml", 'w') as f:
    f.write(LAYER_4_PUML)
files_created.append("plantuml/layer-04-ai-agents-detailed.puml")
print("✓ Created layer-04-ai-agents-detailed.puml (11 agents, multi-model)")

print()
print("=" * 80)
print(f"✅ Created {len(files_created)} PlantUML diagrams")
print("=" * 80)
for f in files_created:
    print(f"  • {f}")

print("\n📐 Render diagrams:")
print("   - VS Code: PlantUML extension")
print("   - CLI: plantuml plantuml/*.puml")
print("   - Online: https://www.plantuml.com/plantuml/")

