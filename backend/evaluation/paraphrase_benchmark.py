import os
import sys
import json
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

import config
from query_intelligence_engine import QueryIntelligenceEngine
from knowledge_tool_router import KnowledgeToolRouter
from knowledge_registry import get_registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("paraphrase_benchmark")

EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = EVAL_DIR / "paraphrase_questions.json"
REPORT_PATH = EVAL_DIR / "paraphrase_matrix_report.md"


class ParaphraseBenchmarkRunner:
    def __init__(self):
        with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
            self.questions = json.load(f)
        self.qi_engine = QueryIntelligenceEngine()
        self.tool_router = KnowledgeToolRouter()
        self.registry = get_registry()

    def run_benchmark(self) -> Dict[str, Any]:
        logger.info("=== STARTING PARAPHRASE GENERALIZATION BENCHMARK ===")
        total_queries = len(self.questions)
        
        entity_correct = 0
        intent_correct = 0
        aspect_correct = 0
        scope_correct = 0
        catalog_leakage_count = 0
        level3_fallback_count = 0

        style_breakdown = {}
        failure_details = []

        for q_item in self.questions:
            qid = q_item["id"]
            query = q_item["question"]
            style = q_item.get("style", "Direct")
            exp_entity = q_item.get("expected_entity")
            exp_intent = q_item.get("expected_intent")
            exp_aspect = q_item.get("expected_aspect")
            exp_scope = q_item.get("expected_scope")

            if style not in style_breakdown:
                style_breakdown[style] = {"total": 0, "entity_correct": 0, "leakage": 0}
            style_breakdown[style]["total"] += 1

            interp = self.qi_engine.analyze_query(query)
            intel_dict = interp.to_dict()

            got_entity = interp.primary_entity_id
            got_intent = interp.primary_intent
            got_aspect = interp.primary_aspect
            got_scope = interp.answer_scope

            # Level 3 LLM fallback tracking
            if interp.llm_invoked:
                level3_fallback_count += 1

            # 1. Entity Match
            if exp_entity == got_entity or (exp_entity and got_entity and self.registry.get_entity(exp_entity) == self.registry.get_entity(got_entity)):
                entity_correct += 1
                style_breakdown[style]["entity_correct"] += 1
                ent_match = True
            elif exp_entity is None and got_entity is None:
                entity_correct += 1
                style_breakdown[style]["entity_correct"] += 1
                ent_match = True
            else:
                ent_match = False

            # 2. Intent Match
            if exp_intent == got_intent or (exp_intent in ["CAPABILITIES", "SOLUTIONS", "PRODUCTS"] and got_intent in ["CAPABILITIES", "SOLUTIONS", "PRODUCTS"]):
                intent_correct += 1
            elif exp_intent == "UNKNOWN" and got_intent == "UNKNOWN":
                intent_correct += 1

            # 3. Aspect Match
            if exp_aspect == got_aspect or (exp_aspect in ["OVERVIEW", "CAPABILITIES"] and got_aspect in ["OVERVIEW", "CAPABILITIES"]):
                aspect_correct += 1
            elif exp_aspect == "UNKNOWN" and got_aspect == "UNKNOWN":
                aspect_correct += 1

            # 4. Scope Match
            if exp_scope == got_scope:
                scope_correct += 1

            # Track Rules vs BGE Disagreements
            raw_ev = intel_dict.get("raw_evidence", {})
            r_ent_obj = raw_ev.get("rules", {}).get("entity") if isinstance(raw_ev.get("rules"), dict) else None
            b_ent_obj = raw_ev.get("bge", {}).get("entity") if isinstance(raw_ev.get("bge"), dict) else None

            rules_ent = getattr(r_ent_obj, "value", None) if r_ent_obj else (r_ent_obj.get("value") if isinstance(r_ent_obj, dict) else None)
            bge_ent = getattr(b_ent_obj, "value", None) if b_ent_obj else (b_ent_obj.get("value") if isinstance(b_ent_obj, dict) else None)
            
            disagreement = (rules_ent != bge_ent) and (rules_ent is not None or bge_ent is not None)

            # 5. Routing & Catalog Leakage Check
            plans = self.tool_router.route_query(intel_dict)
            selected_op = plans[0].operation_name if plans else "none"

            is_leakage = False
            if exp_entity is not None and selected_op in ["list_solutions", "list_products"] and not plans[0].inputs.get("entity_id"):
                is_leakage = True
                catalog_leakage_count += 1
                style_breakdown[style]["leakage"] += 1

            interp_desc = f"Intent: {got_intent}, Aspect: {got_aspect}, Scope: {got_scope}, Entity: {got_entity or 'NONE'} (Rules: {rules_ent}, BGE: {bge_ent})"

            if not ent_match or is_leakage or disagreement:
                failure_details.append({
                    "id": qid,
                    "query": query,
                    "style": style,
                    "expected_entity": exp_entity,
                    "got_entity": got_entity,
                    "rules_entity": rules_ent,
                    "bge_entity": bge_ent,
                    "disagreement": disagreement,
                    "selected_op": selected_op,
                    "is_leakage": is_leakage,
                    "interpretation": interp_desc
                })

        entity_acc = (entity_correct / total_queries) * 100
        intent_acc = (intent_correct / total_queries) * 100
        aspect_acc = (aspect_correct / total_queries) * 100
        scope_acc = (scope_correct / total_queries) * 100
        level3_fallback_rate = (level3_fallback_count / total_queries) * 100

        res = {
            "total_queries": total_queries,
            "entity_accuracy_pct": round(entity_acc, 1),
            "intent_accuracy_pct": round(intent_acc, 1),
            "aspect_accuracy_pct": round(aspect_acc, 1),
            "scope_accuracy_pct": round(scope_acc, 1),
            "catalog_leakage_count": catalog_leakage_count,
            "level3_fallback_rate_pct": round(level3_fallback_rate, 1),
            "style_breakdown": style_breakdown,
            "failures": failure_details
        }

        self._generate_report(res)
        return res

    def _generate_report(self, res: Dict[str, Any]):
        report = f"""# CittaAI Paraphrase Generalization Benchmark Report

**Generated At:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Evaluation Set:** `paraphrase_questions.json` ({res['total_queries']} Multi-Style Paraphrase Queries)

---

## 1. Summary Performance Metrics

| Metric | Target | Benchmark Result | Status |
| :--- | :---: | :---: | :---: |
| **Entity Resolution Accuracy** | ≥ 90.0% | **{res['entity_accuracy_pct']}%** | {'PASS' if res['entity_accuracy_pct'] >= 90.0 else 'FAIL'} |
| **Intent Classification Accuracy** | ≥ 85.0% | **{res['intent_accuracy_pct']}%** | {'PASS' if res['intent_accuracy_pct'] >= 85.0 else 'FAIL'} |
| **Semantic Aspect Accuracy** | ≥ 85.0% | **{res['aspect_accuracy_pct']}%** | {'PASS' if res['aspect_accuracy_pct'] >= 85.0 else 'FAIL'} |
| **Answer Scope Accuracy** | ≥ 85.0% | **{res['scope_accuracy_pct']}%** | {'PASS' if res['scope_accuracy_pct'] >= 85.0 else 'FAIL'} |
| **Catalog List Leakage Count** | **0** | **{res['catalog_leakage_count']}** | {'PASS' if res['catalog_leakage_count'] == 0 else 'HARD FAIL'} |
| **Level 3 LLM Fallback Rate** | < 15.0% | **{res['level3_fallback_rate_pct']}%** | {'PASS' if res['level3_fallback_rate_pct'] < 15.0 else 'FAIL'} |

---

## 2. Accuracy Breakdown by Paraphrase Formulation Style

| Formulation Style | Queries | Entity Accuracy | Leakage Count |
| :--- | :---: | :---: | :---: |
"""
        for style, data in res["style_breakdown"].items():
            acc = round((data["entity_correct"] / data["total"]) * 100, 1)
            report += f"| **{style}** | {data['total']} | **{acc}%** | **{data['leakage']}** |\n"

        report += f"""
---

## 3. Failure & Leakage Trace Details

```json
{json.dumps(res['failures'], indent=2)}
```

---
"""
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Paraphrase benchmark report written to {REPORT_PATH}")


if __name__ == "__main__":
    runner = ParaphraseBenchmarkRunner()
    res = runner.run_benchmark()
    print("\n=== PARAPHRASE BENCHMARK RESULTS ===")
    print(f"Entity Accuracy      : {res['entity_accuracy_pct']}%")
    print(f"Catalog Leakage Count: {res['catalog_leakage_count']}")
    print(f"LLM Fallback Rate    : {res['level3_fallback_rate_pct']}%")
    
    if res["catalog_leakage_count"] > 0:
        print("\n[HARD FAIL] Catalog list leakage detected on target entity queries!")
        sys.exit(1)
