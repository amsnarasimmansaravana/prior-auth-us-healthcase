"""
Clinical Review Agent - Production Implementation
Healthcare Insurance PA Platform

Agent: clinical-agent
Model: GPT-4o with RAG pipeline
Purpose: Assess medical necessity using clinical guidelines
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import openai
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
import logging

# ============================================================================
# CONFIGURATION
# ============================================================================

AGENT_CONFIG = {
    "name": "clinical_agent",
    "model": "gpt-4o",
    "temperature": 0.3,
    "max_tokens": 4096,
    "timeout_seconds": 300,
    "retry_attempts": 3
}

# ============================================================================
# DATA MODELS
# ============================================================================

class ClinicalInput(BaseModel):
    """Input schema for clinical review agent"""
    request_id: str = Field(..., description="Unique PA request ID")
    patient_age: int = Field(..., ge=0, le=150)
    patient_gender: str = Field(..., regex="^(M|F|O)$")
    icd10_codes: List[str] = Field(..., min_items=1, description="Diagnosis codes")
    cpt_codes: List[str] = Field(..., min_items=1, description="Requested treatment codes")
    clinical_notes: str = Field(..., min_length=10, description="Clinical justification")
    supporting_docs: List[str] = Field(default=[], description="URLs to lab results, imaging")
    urgency_level: str = Field(default="standard", regex="^(standard|urgent|emergency)$")
    
    # Context from previous agents
    previous_outputs: Dict[str, Any] = Field(default={})

class ClinicalOutput(BaseModel):
    """Output schema for clinical review agent"""
    agent_name: str = "clinical_agent"
    medical_necessity: str = Field(..., regex="^(APPROVED|DENIED|NEED_MORE_INFO)$")
    clinical_rationale: str = Field(..., min_length=50)
    cited_guidelines: List[Dict[str, str]] = Field(default=[])
    alternative_treatments: List[str] = Field(default=[])
    contraindications: List[str] = Field(default=[])
    safety_concerns: List[str] = Field(default=[])
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Execution metadata
    execution_time_ms: int
    token_usage: Dict[str, int]
    rag_sources_used: int
    rag_retrieval_time_ms: int
    tools_used: List[str]

# ============================================================================
# RAG PIPELINE
# ============================================================================

class HybridRAGPipeline:
    """
    Hybrid retrieval combining Vector Search, BM25, and Graph RAG
    """
    
    def __init__(self):
        self.milvus_client = self._init_milvus()
        self.elasticsearch_client = self._init_elasticsearch()
        self.neo4j_driver = self._init_neo4j()
        self.embedding_model = self._init_embeddings()
        self.reranker = self._init_reranker()
    
    def search(self, query: str, diagnosis: str, treatment: str, top_k: int = 10) -> List[Dict]:
        """
        Perform hybrid search and return top-k results
        
        Pipeline:
        1. Vector search (Milvus) - 45ms
        2. BM25 search (Elasticsearch) - 120ms
        3. Graph RAG (Neo4j) - 85ms
        4. Reciprocal Rank Fusion (RRF, k=60)
        5. Reranking (cross-encoder) - 180ms
        
        Total: ~430ms
        """
        import time
        start_time = time.time()
        
        # 1. Vector Search
        vector_start = time.time()
        query_vector = self.embedding_model.embed_query(
            f"{diagnosis} {treatment} medical necessity"
        )
        vector_results = self.milvus_client.search(
            collection_name="clinical_guidelines",
            data=[query_vector],
            limit=20,
            output_fields=["guideline_id", "title", "content", "source"]
        )
        vector_time = (time.time() - vector_start) * 1000
        
        # 2. BM25 Lexical Search
        bm25_start = time.time()
        bm25_results = self.elasticsearch_client.search(
            index="clinical_content",
            body={
                "query": {
                    "bool": {
                        "should": [
                            {"match": {"diagnosis": diagnosis}},
                            {"match": {"treatment": treatment}},
                            {"match": {"content": query}}
                        ]
                    }
                },
                "size": 20
            }
        )
        bm25_time = (time.time() - bm25_start) * 1000
        
        # 3. Graph RAG (Neo4j)
        graph_start = time.time()
        graph_results = self.neo4j_driver.execute_query(
            """
            MATCH (d:Diagnosis {code: $diagnosis})-[r:INDICATES]->(t:Treatment)
            WHERE t.code IN $treatment_codes
            MATCH (t)-[:SUPPORTED_BY]->(g:Guideline)
            RETURN g.guideline_id, g.title, g.content, g.evidence_level
            LIMIT 20
            """,
            diagnosis=diagnosis,
            treatment_codes=treatment.split(",")
        )
        graph_time = (time.time() - graph_start) * 1000
        
        # 4. Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(
            [
                vector_results,
                bm25_results["hits"]["hits"],
                graph_results
            ],
            k=60
        )
        
        # 5. Reranking
        rerank_start = time.time()
        reranked_results = self.reranker.rerank(
            query=query,
            documents=[r["content"] for r in fused_results[:30]],
            top_k=top_k
        )
        rerank_time = (time.time() - rerank_start) * 1000
        
        total_time = (time.time() - start_time) * 1000
        
        logging.info(f"RAG Pipeline: {total_time:.0f}ms total | Vector: {vector_time:.0f}ms | BM25: {bm25_time:.0f}ms | Graph: {graph_time:.0f}ms | Rerank: {rerank_time:.0f}ms")
        
        return reranked_results
    
    def _reciprocal_rank_fusion(self, result_lists: List[List], k: int = 60) -> List:
        """
        RRF algorithm to merge multiple ranked lists
        
        Score(d) = Σ 1/(k + rank(d))
        """
        scores = {}
        
        for results in result_lists:
            for rank, doc in enumerate(results, start=1):
                doc_id = doc.get("guideline_id") or doc.get("_id")
                scores[doc_id] = scores.get(doc_id, 0) + (1.0 / (k + rank))
        
        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked
    
    def _init_milvus(self):
        from pymilvus import connections, Collection
        connections.connect(alias="default", host="milvus", port="19530")
        return Collection("clinical_guidelines")
    
    def _init_elasticsearch(self):
        from elasticsearch import Elasticsearch
        return Elasticsearch(["http://elasticsearch:9200"])
    
    def _init_neo4j(self):
        from neo4j import GraphDatabase
        return GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "password"))
    
    def _init_embeddings(self):
        from langchain.embeddings import OpenAIEmbeddings
        return OpenAIEmbeddings(model="text-embedding-ada-002")
    
    def _init_reranker(self):
        from sentence_transformers import CrossEncoder
        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")

# ============================================================================
# MCP TOOLS
# ============================================================================

def create_clinical_tools(rag_pipeline: HybridRAGPipeline) -> List[Tool]:
    """Create MCP tools for clinical agent"""
    
    tools = [
        Tool(
            name="rag_search_clinical",
            description="Search clinical guidelines using hybrid RAG (vector + BM25 + graph)",
            func=lambda query: rag_pipeline.search(query, "", "", top_k=5)
        ),
        Tool(
            name="get_clinical_guideline",
            description="Retrieve specific clinical guideline by ID",
            func=lambda guideline_id: _get_guideline_by_id(guideline_id)
        ),
        Tool(
            name="check_drug_interactions",
            description="Check for drug-drug interactions using FDA database",
            func=lambda drugs: _check_drug_interactions(drugs)
        ),
        Tool(
            name="get_treatment_alternatives",
            description="Find alternative treatments for given diagnosis",
            func=lambda diagnosis: _get_alternatives(diagnosis)
        ),
        Tool(
            name="assess_urgency",
            description="Triage urgency level based on clinical presentation",
            func=lambda symptoms: _assess_urgency(symptoms)
        )
    ]
    
    return tools

def _get_guideline_by_id(guideline_id: str) -> Dict:
    """Retrieve guideline from database"""
    # Implementation would query PostgreSQL/Elasticsearch
    return {"guideline_id": guideline_id, "content": "..."}

def _check_drug_interactions(drugs: List[str]) -> Dict:
    """Check FDA drug interaction database"""
    # Implementation would call FDA API
    return {"interactions": [], "severity": "none"}

def _get_alternatives(diagnosis: str) -> List[str]:
    """Get alternative treatments"""
    # Implementation would query clinical database
    return ["Alternative 1", "Alternative 2"]

def _assess_urgency(symptoms: str) -> str:
    """Triage urgency"""
    # Implementation would use medical triage rules
    return "standard"

# ============================================================================
# CLINICAL REVIEW AGENT
# ============================================================================

class ClinicalReviewAgent:
    """
    Clinical Review Agent - Assess medical necessity using GPT-4o + RAG
    """
    
    def __init__(self):
        self.config = AGENT_CONFIG
        self.rag_pipeline = HybridRAGPipeline()
        self.tools = create_clinical_tools(self.rag_pipeline)
        self.executor = self._create_executor()
    
    def _create_executor(self) -> AgentExecutor:
        """Create LangChain agent executor"""
        
        # System prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a clinical review agent for medical necessity determination in a health insurance PA system.

Your task: Assess if the requested treatment is medically necessary based on evidence-based clinical guidelines.

Process:
1. Review the diagnosis (ICD-10 codes) and requested treatment (CPT codes)
2. Use the rag_search_clinical tool to retrieve relevant clinical guidelines
3. Compare the requested treatment against evidence-based criteria
4. Check for contraindications and safety concerns using check_drug_interactions
5. Consider alternative treatments if requested treatment not indicated
6. Assess urgency level

Decision Criteria:
- APPROVED: Treatment meets clinical guidelines and is medically necessary
- DENIED: Treatment not indicated, alternatives available, or contraindicated
- NEED_MORE_INFO: Insufficient clinical documentation to make determination

CRITICAL: Provide detailed clinical rationale citing specific guidelines (include guideline name, section, and evidence level). Your decision impacts patient care.

Output format:
{{
  "medical_necessity": "APPROVED|DENIED|NEED_MORE_INFO",
  "clinical_rationale": "Detailed explanation citing specific guidelines",
  "cited_guidelines": [
    {{"guideline": "Name", "section": "X.Y", "evidence_level": "A"}}
  ],
  "alternative_treatments": ["alt1", "alt2"],
  "contraindications": [],
  "safety_concerns": []
}}
"""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_openai_functions_agent(
            llm=openai.ChatOpenAI(
                model=self.config["model"],
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            ),
            tools=self.tools,
            prompt=prompt
        )
        
        # Create executor
        executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=True
        )
        
        return executor
    
    def process(self, input_data: ClinicalInput) -> ClinicalOutput:
        """
        Process clinical review request
        """
        import time
        start_time = time.time()
        
        # Format input for LLM
        input_text = f"""
Patient Information:
- Age: {input_data.patient_age}
- Gender: {input_data.patient_gender}
- Urgency: {input_data.urgency_level}

Diagnosis (ICD-10):
{', '.join(input_data.icd10_codes)}

Requested Treatment (CPT):
{', '.join(input_data.cpt_codes)}

Clinical Justification:
{input_data.clinical_notes}

Supporting Documents:
{', '.join(input_data.supporting_docs) if input_data.supporting_docs else 'None'}

Previous Agent Outputs:
{input_data.previous_outputs}

Task: Determine if this treatment is medically necessary. Use RAG to search clinical guidelines.
"""
        
        # Invoke agent
        result = self.executor.invoke({"input": input_text})
        
        # Parse output
        output_data = self._parse_output(result)
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Create output
        output = ClinicalOutput(
            medical_necessity=output_data.get("medical_necessity", "NEED_MORE_INFO"),
            clinical_rationale=output_data.get("clinical_rationale", ""),
            cited_guidelines=output_data.get("cited_guidelines", []),
            alternative_treatments=output_data.get("alternative_treatments", []),
            contraindications=output_data.get("contraindications", []),
            safety_concerns=output_data.get("safety_concerns", []),
            confidence=self._calculate_confidence(output_data),
            execution_time_ms=execution_time_ms,
            token_usage=self._get_token_usage(result),
            rag_sources_used=len(output_data.get("cited_guidelines", [])),
            rag_retrieval_time_ms=0,  # Would track separately
            tools_used=[step[0].tool for step in result.get("intermediate_steps", [])]
        )
        
        return output
    
    def _parse_output(self, result: Dict) -> Dict:
        """Parse agent output"""
        import json
        try:
            return json.loads(result["output"])
        except:
            # Fallback parsing
            return {"medical_necessity": "NEED_MORE_INFO", "clinical_rationale": result.get("output", "")}
    
    def _calculate_confidence(self, output_data: Dict) -> float:
        """Calculate confidence score based on output quality"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence if guidelines cited
        if len(output_data.get("cited_guidelines", [])) > 0:
            confidence += 0.2
        
        # Increase if detailed rationale
        if len(output_data.get("clinical_rationale", "")) > 100:
            confidence += 0.15
        
        # Decrease if alternatives suggested (uncertainty)
        if len(output_data.get("alternative_treatments", [])) > 0:
            confidence -= 0.1
        
        return min(max(confidence, 0.0), 1.0)
    
    def _get_token_usage(self, result: Dict) -> Dict[str, int]:
        """Extract token usage from result"""
        # Would extract from LLM metadata
        return {"prompt_tokens": 3500, "completion_tokens": 1500, "total_tokens": 5000}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Example usage
    agent = ClinicalReviewAgent()
    
    # Sample input
    sample_input = ClinicalInput(
        request_id="PA-2026-123456",
        patient_age=55,
        patient_gender="M",
        icd10_codes=["I63.9"],  # Cerebral infarction
        cpt_codes=["97110"],    # Therapeutic exercise
        clinical_notes="Patient with recent stroke (3 weeks ago), requesting physical therapy for motor recovery. Right-sided weakness, ambulatory with assistance.",
        urgency_level="standard"
    )
    
    # Process
    output = agent.process(sample_input)
    
    # Display result
    print("=" * 80)
    print("CLINICAL REVIEW RESULT")
    print("=" * 80)
    print(f"Decision: {output.medical_necessity}")
    print(f"Confidence: {output.confidence:.2%}")
    print(f"Rationale: {output.clinical_rationale}")
    print(f"Guidelines Cited: {len(output.cited_guidelines)}")
    print(f"Execution Time: {output.execution_time_ms}ms")
    print(f"Tools Used: {', '.join(output.tools_used)}")
