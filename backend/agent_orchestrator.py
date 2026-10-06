import time
import asyncio
import logging
from typing import Dict, Any, List, Optional

from orchestration_context import OrchestrationContext
from agent_contracts import AgentID, AgentContext, AgentOutput
from specialized_agents import (
    BusinessSolutionsAgent,
    TechnicalArchitectureAgent,
    WorkflowAgent,
    MemoryAgent,
    ResearchAgent,
    ReviewerAgent
)
from agent_planner import get_agent_planner
from collaboration_planner import get_collaboration_planner
from consensus_builder import get_consensus_builder

from knowledge_tool_router import KnowledgeToolRouter
from sufficiency_gate import get_sufficiency_gate, MAX_KNOWLEDGE_OPERATIONS

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    def __init__(self):
        self.planner = get_agent_planner()
        self.collaboration_planner = get_collaboration_planner()
        self.consensus_builder = get_consensus_builder()
        self.tool_router = KnowledgeToolRouter()
        self.sufficiency_gate = get_sufficiency_gate()
        
        self.agents = {
            AgentID.BUSINESS_SOLUTIONS.value: BusinessSolutionsAgent(),
            AgentID.TECHNICAL_ARCHITECTURE.value: TechnicalArchitectureAgent(),
            AgentID.WORKFLOW.value: WorkflowAgent(),
            AgentID.MEMORY.value: MemoryAgent(),
            AgentID.RESEARCH.value: ResearchAgent(),
            AgentID.REVIEWER.value: ReviewerAgent()
        }

    async def execute_bounded_knowledge_query(
        self,
        query_intel: Dict[str, Any],
        query_text: str
    ) -> Dict[str, Any]:
        """
        Executes a bounded, schema-driven knowledge query using KnowledgeToolRouter
        and enforcing a hard limit of MAX_KNOWLEDGE_OPERATIONS = 3 via SufficiencyGate.
        """
        ops_count = 0
        collected_evidence = []
        op_history = []

        # 1. Resolve initial route plan
        route_plans = self.tool_router.route_query(query_intel)

        for plan in route_plans:
            if ops_count >= MAX_KNOWLEDGE_OPERATIONS:
                break

            ops_count += 1
            op_history.append(plan.operation_name)

            if plan.authoritative_source == "KnowledgeRegistry":
                from knowledge_registry import get_registry
                reg = get_registry()
                ent_id = plan.inputs.get("entity_id")
                sec = plan.inputs.get("section")
                
                if ent_id and hasattr(reg, "get_entity"):
                    ent = reg.get_entity(ent_id)
                    if ent:
                        collected_evidence.append({
                            "source": "KnowledgeRegistry",
                            "entity_id": ent_id,
                            "section": sec,
                            "text": str(ent)
                        })
            else:
                # VectorStore semantic search
                from vector_store import get_vector_store
                vstore = get_vector_store()
                if hasattr(vstore, "query_hybrid"):
                    chunks = vstore.query_hybrid(query_text=query_text, top_k=5)
                    for c in chunks:
                        collected_evidence.append({
                            "source": "VectorStore",
                            "text": c.get("text", "")
                        })

            # Check sufficiency after operation
            is_sufficient, reason, next_ops = self.sufficiency_gate.evaluate_sufficiency(
                query_intel=query_intel,
                collected_evidence=collected_evidence,
                ops_executed_count=ops_count
            )

            if is_sufficient:
                logger.info(f"[BoundedAgent] Evidence sufficient after {ops_count} ops. Reason: {reason}")
                break

        return {
            "evidence": collected_evidence,
            "ops_executed": ops_count,
            "op_history": op_history,
            "sufficiency_status": is_sufficient
        }

    async def orchestrate_collaboration(
        self,
        ctx: OrchestrationContext,
        simulate_failure_agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Agent Planning
        plan = self.planner.plan_agents(ctx)

        # 2. Collaboration Planning (Graph construction)
        graph = self.collaboration_planner.build_collaboration_graph(plan)

        # 3. Execution Context
        agent_outputs: List[AgentOutput] = []
        agent_outputs_by_id: Dict[str, AgentOutput] = {}

        # 4. Execute Steps in Graph Order
        for step in graph.execution_steps:
            aid = step.agent_id
            if aid not in self.agents:
                continue

            agent_obj = self.agents[aid]
            actx = AgentContext(
                agent_id=aid,
                task=ctx.original_query,
                objective=f"Execute multi-agent subtask for {aid}",
                inputs={"entity_name": ctx.resolved_entity_name or "Enterprise Solution"}
            )

            # Simulated Failure / Timeout Check
            if simulate_failure_agent_id and aid == simulate_failure_agent_id:
                logger.warning(f"Agent '{aid}' encountered simulated failure/timeout. Triggering fallback handler.")
                fallback_out = AgentOutput(
                    agent_id=aid,
                    task=ctx.original_query,
                    findings=[f"[{aid}] Fallback execution completed due to primary timeout."],
                    confidence=0.50,
                    status="FALLBACK"
                )
                agent_outputs.append(fallback_out)
                agent_outputs_by_id[aid] = fallback_out
                continue

            try:
                if aid == AgentID.REVIEWER.value:
                    # ReviewerAgent takes prior domain agent outputs for grounding validation
                    domain_outputs = [o for o in agent_outputs if o.agent_id != AgentID.REVIEWER.value]
                    out = await agent_obj.execute(actx, prior_outputs=domain_outputs)
                else:
                    out = await agent_obj.execute(actx)

                agent_outputs.append(out)
                agent_outputs_by_id[aid] = out

            except Exception as e:
                logger.error(f"Agent '{aid}' execution exception: {e}")
                err_out = AgentOutput(
                    agent_id=aid,
                    task=ctx.original_query,
                    findings=[f"[{aid}] Execution error: {e}"],
                    confidence=0.0,
                    status="FAILED"
                )
                agent_outputs.append(err_out)

        # 5. Consensus Building
        consensus = self.consensus_builder.build_consensus(agent_outputs, ctx.original_query)
        latency_ms = round((time.time() - start_time) * 1000.0, 2)

        # Update Context Metrics & Decision Trace
        ctx.response_text = consensus.summary_markdown
        ctx.metrics["participating_agents"] = consensus.participating_agents
        ctx.metrics["consensus_score"] = consensus.consensus_score
        ctx.metrics["total_findings"] = consensus.total_findings
        ctx.metrics["latency_ms"] = latency_ms

        ctx.add_trace(
            stage="AgentOrchestrator",
            result="SUCCESS",
            reason=f"Coordinated {len(consensus.participating_agents)} agents | Score: {consensus.consensus_score}"
        )

        return {
            "text": consensus.summary_markdown,
            "consensus_score": consensus.consensus_score,
            "participating_agents": consensus.participating_agents,
            "recommendations": consensus.unified_recommendations,
            "source": f"Enterprise Multi-Agent Collaboration ({len(consensus.participating_agents)} Agents)",
            "verified": True,
            "metrics": ctx.metrics
        }

_agent_orchestrator_instance = None

def get_agent_orchestrator() -> AgentOrchestrator:
    global _agent_orchestrator_instance
    if _agent_orchestrator_instance is None:
        _agent_orchestrator_instance = AgentOrchestrator()
    return _agent_orchestrator_instance
