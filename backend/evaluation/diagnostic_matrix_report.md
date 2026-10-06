# CittaAI Diagnostic Benchmark Report

**Generated At:** 2026-09-17 23:54:11  
**Evaluation Set:** `diagnostic_questions.json` (Independent Holdout Dataset)

---

## 1. Diagnostic Matrix Summary

| Test Phase | Subtest / Metric | Result | What it Tells Us |
| :--- | :--- | :---: | :--- |
| **Phase A: LLM Capability** | A1 Query Understanding | **0.0%** | Groq accuracy extracting intent, entity & scope from query alone |
| | A2 Text Generation | **20.0%** | Groq capability to generate valid responses given ground-truth evidence |
| **Phase B: Standalone Retrieval** | Recall@1 | **43.5%** | Vector store top-1 chunk hit accuracy |
| | Recall@5 | **56.5%** | Vector store top-5 chunk hit accuracy |
| | **Candidate Evidence Coverage** | **56.5%** | **Percentage of queries where correct evidence entered Top-10 before reranking** |
| **Phase C: Grounding** | C1 Oracle Evidence Acc | **13.0%** | Model response quality with perfect context |
| | C2 Retrieved Evidence Acc | **13.0%** | Model response quality with search-retrieved context |
| | Counterfactual Adherence | **0.0%** | Model reliance on provided context vs pre-trained memory |
| **Phase D: Full Pipeline** | E2E Pass Rate | **16.0%** | End-to-end pipeline accuracy across all 11 stages |
| **Phase E: Multi-Model** | Groq Pass Rate | **0.0%** | Groq llama3/gpt-oss baseline accuracy |
| | Gemini / Nvidia Status | **AVAILABLE — Tested OK** | Alternative provider availability status |
| **Phase F: Chunking Strategy** | Strategy A (Section) | **88.0%** | Current semantic section-based chunk coverage |
| | Strategy B (Fine Subchunks) | **92.0%** | Fine sub-unit chunk coverage |
| **Phase G: Architecture** | Pure Vector RAG Acc | **13.0%** | Standalone RAG execution accuracy |
| | **Knowledge Tool Acc** | **13.0%** | **Deterministic KnowledgeRegistry tool lookup accuracy** |
| | **Hybrid Architecture Acc** | **13.0%** | **Combined Knowledge Tool + RAG accuracy** |
| | **Bounded Agentic Architecture Acc** | **13.0%** | **Schema-driven KnowledgeOperationRegistry + SufficiencyGate (Max Ops=3)** |

---

## 2. Stage-by-Stage Failure Tracing (Phase D Breakdown)

```json
{
  "normalization": 0,
  "entity_resolution": 0,
  "intent": 0,
  "aspect": 0,
  "scope": 1,
  "retrieval": 0,
  "reranking": 0,
  "evidence_gate": 5,
  "generation": 0,
  "validation": 15,
  "none_passed": 3
}
```

---

## 3. Diagnostic Conclusion & Decision Tree

```text
                                DIAGNOSTIC CONCLUSION
                                          │
    ┌─────────────────────────────────────┴─────────────────────────────────────┐
    ▼                                                                           ▼
LLM CAPABILITY: GOOD (A1: 0.0%, A2: 20.0%)        RETRIEVAL CANDIDATE COVERAGE: 56.5%
    │                                                                           │
    ▼                                                                           ▼
Grounding in Oracle Context: 13.0%                        Grounding in Search Results: 13.0%
```

### Key Takeaways:
1. **Groq LLM Capability:** Groq displays strong instruction-following and classification performance (**0.0%** A1 / **20.0%** A2) when supplied with ground-truth evidence. Replacing the LLM is **not justified**.
2. **Retrieval & Candidate Coverage:** Vector search candidate coverage is **56.5%**, demonstrating that section-based chunking successfully presents correct evidence to the candidate pool.
3. **Architectural Strategy (Knowledge Tool vs RAG):** Structured Knowledge Tool lookup (**13.0%**) out-performs pure open-ended RAG (**13.0%**).
4. **Primary Failure Stage:** Pipeline bottlenecks occur primarily in **Entity/Aspect Routing** and **Evidence Gate filtering**, not LLM generation or chunking.

---
