#!/usr/bin/env bash
set -euo pipefail
echo 'Starting apply_moves...'

echo 'SKIP: original not found: DELIVERY-SUMMARY.md'
echo 'SKIP: original not found: DOCUMENTATION_SUMMARY.md'
echo 'SKIP: original not found: INDEX.md'
echo 'SKIP: original not found: INTEGRATION-SUMMARY.md'
echo 'SKIP: original not found: INTERVIEW_GUIDE.md'
echo 'SKIP: original not found: MASTER_ARCHITECTURE_REFERENCE.md'
echo 'SKIP: original not found: README-PERFORMANCE-UPDATE.md'
echo 'SKIP: original not found: README.md'
echo 'SKIP: original not found: adr/ADR-001-Multi-Model-Strategy.md'
echo 'SKIP: original not found: agents/01-intake-agent.md'
echo 'SKIP: original not found: agents/02-eligibility-agent.md'
echo 'SKIP: original not found: agents/03-benefits-agent.md'
echo 'SKIP: original not found: agents/04-clinical-agent.md'
echo 'SKIP: original not found: agents/05-policy-agent.md'
echo 'SKIP: original not found: agents/06-fraud-agent.md'
echo 'SKIP: original not found: agents/07-decision-agent.md'
echo 'SKIP: original not found: agents/08-appeals-agent.md'
echo 'SKIP: original not found: agents/09-notification-agent.md'
echo 'SKIP: original not found: agents/10-audit-agent.md'
echo 'SKIP: original not found: agents/11-com-agent.md'
echo 'SKIP: destination already exists: docs/both/README.md'
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/01-Business-Architecture.md" "docs/both/01-Business-Architecture.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/02-Enterprise-Solution-Architecture.md" "docs/both/02-Enterprise-Solution-Architecture.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/03-Agentic-AI-Platform-Architecture.md" "docs/both/03-Agentic-AI-Platform-Architecture.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/04-Enterprise-Security-Governance-Compliance.md" "docs/both/04-Enterprise-Security-Governance-Compliance.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/05-Deployment-Operations-Runbook.md" "docs/both/05-Deployment-Operations-Runbook.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/06-Complete-Microservice-Architecture.md" "docs/both/06-Complete-Microservice-Architecture.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/13-Complete-Platform-Component-Reference.md" "docs/both/13-Complete-Platform-Component-Reference.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/13-Deep-Component-Connection-Reference.md" "docs/both/13-Deep-Component-Connection-Reference.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/PERFORMANCE-VISUALIZATION-SUMMARY.md" "docs/both/PERFORMANCE-VISUALIZATION-SUMMARY.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/layer-01-presentation.md" "docs/both/layer-01-presentation.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-02-api-gateway-.md" "docs/technical/layer-02-api-gateway-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-03-orchestration-.md" "docs/technical/layer-03-orchestration-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-04-ai-agent-fabric-.md" "docs/technical/layer-04-ai-agent-fabric-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/layer-04-ai-agent-fabric-DETAILED.md" "docs/both/layer-04-ai-agent-fabric-DETAILED.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-05-governance-.md" "docs/technical/layer-05-governance-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/layer-05-governance-DETAILED.md" "docs/both/layer-05-governance-DETAILED.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-06-mcp-.md" "docs/technical/layer-06-mcp-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-06-mcp-DETAILED.md" "docs/technical/layer-06-mcp-DETAILED.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-07-memory-.md" "docs/technical/layer-07-memory-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-07-memory-DETAILED.md" "docs/technical/layer-07-memory-DETAILED.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "doc/layer-08-rag-DETAILED.md" "docs/both/layer-08-rag-DETAILED.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-08-rag-retrieval-.md" "docs/technical/layer-08-rag-retrieval-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-09-data-services-.md" "docs/technical/layer-09-data-services-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-09-data-services-DETAILED.md" "docs/technical/layer-09-data-services-DETAILED.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-10-hitl-.md" "docs/technical/layer-10-hitl-.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/technical"
git mv "doc/layer-10-hitl-DETAILED.md" "docs/technical/layer-10-hitl-DETAILED.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "plantuml/60-Gateway-GenAI-Orchestration-Architecture.md" "docs/both/60-Gateway-GenAI-Orchestration-Architecture.md"
echo 'SKIP: destination already exists: docs/both/README.md'
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/01-member-service.md" "docs/both/01-member-service.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/02-provider-service.md" "docs/both/02-provider-service.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/03-policy-service.md" "docs/both/03-policy-service.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/04-claims-service.md" "docs/both/04-claims-service.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/05-benefits-config-service.md" "docs/both/05-benefits-config-service.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/06-network-service.md" "docs/both/06-network-service.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/07-formulary-service.md" "docs/both/07-formulary-service.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "services/08-clinical-content-service.md" "docs/both/08-clinical-content-service.md"
echo 'SKIP: destination already exists: docs/both/README.md'
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "tracking/ALIGNMENT_PROGRESS.md" "docs/both/ALIGNMENT_PROGRESS.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "tracking/CONTENT_ENHANCEMENT_MAP.md" "docs/both/CONTENT_ENHANCEMENT_MAP.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "tracking/LATEST_SESSION_REPORT.md" "docs/both/LATEST_SESSION_REPORT.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "tracking/ORGANIZATION_SUMMARY.md" "docs/both/ORGANIZATION_SUMMARY.md"
echo 'SKIP: destination already exists: docs/both/README.md'
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "tracking/archive/ALIGNMENT_SUMMARY.md" "docs/both/ALIGNMENT_SUMMARY.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "tracking/archive/SESSION_COMPLETION_REPORT.md" "docs/both/SESSION_COMPLETION_REPORT.md"
mkdir -p "/Users/narasimman.saravana/Documents/personal/study/PA_Healthcare_Use_Case/docs/both"
git mv "tracking/archive/VERIFICATION_REPORT.md" "docs/both/VERIFICATION_REPORT.md"
echo 'Done apply_moves'