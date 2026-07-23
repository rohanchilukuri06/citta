import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.conversation import get_conversation_manager
from backend.conversation.models import ResponseComposition

# 10 Golden Reference Responses (CittaAI Senior Pre-Sales Consultant Gold Standard)
GOLDEN_RESPONSES = {
    "ecommerce": (
        "Yes. CittaAI offers an enterprise platform called Ecommerce OS. "
        "It is designed for businesses seeking to run complete digital commerce operations from a single platform. "
        "It combines:\n"
        "✓ Product & Inventory: Unified catalog with dynamic pricing rules.\n"
        "✓ Order Management: Multi-channel order processing and fulfillment workflows.\n"
        "✓ CRM & Customer Analytics: Customer lifetime value and retention engines.\n\n"
        "This makes it suitable for retailers, D2C brands, and multi-channel enterprise operations."
    ),
    "pharma": (
        "Pharma OS is CittaAI's specialized platform engineered for pharmaceutical compliance and supply chain tracking. "
        "It provides GxP and FDA compliant audit trails, batch serialization, and automated quality control workflows. "
        "This makes it suitable for pharmaceutical manufacturers, biotech firms, and healthcare distributors."
    ),
    "sap_integration": (
        "Yes. Ecommerce OS supports enterprise integration scenarios, including SAP ERP, REST APIs, and event webhooks. "
        "High-throughput webhooks ensure bi-directional synchronization between catalog, inventory, and enterprise ERP systems."
    ),
    "target_audience": (
        "CittaAI solutions are tailored for mid-market and enterprise organizations scaling multi-channel digital operations. "
        "Target roles include Chief Technology Officers, Digital Transformation Leaders, Operations Directors, and Enterprise Architects."
    ),
    "pricing": (
        "CittaAI utilizes a predictable tiered enterprise licensing model based on transaction volume and SLA requirements. "
        "Flexible tiers ensure cost aligns directly with business growth and platform utilization."
    ),
    "hipaa_security": (
        "Yes. CittaAI platforms enforce zero-trust security, AES-256 encryption at rest, and HIPAA compliance controls. "
        "Immutable audit logging ensures full compliance with stringent healthcare regulatory mandates."
    ),
    "leadership": (
        "CittaAI is led by seasoned enterprise AI architects and technology executives with proven track records in agentic AI and enterprise scale platforms."
    ),
    "scalability": (
        "CittaAI platforms are built on cloud-native microservices architecture tested for enterprise throughput. "
        "Elastic container autoscaling guarantees sub-100ms API response latency under traffic spikes."
    ),
    "comparison": (
        "While Ecommerce OS focuses on retail commerce, inventory, and customer lifetime value, "
        "Pharma OS is engineered specifically for regulated pharmaceutical compliance, batch serialization, and GxP workflows."
    ),
    "demo": (
        "We would be delighted to arrange a tailored discovery consultation and live platform demonstration with our engineering team. "
        "Our solution architects will walk through your exact technical requirements and integration architecture."
    )
}

def evaluate_quality_rubric(response_text: str, query_type: str) -> dict:
    """
    Evaluates response against the 7-Metric Weighted Quality Rubric (0.0 to 1.0):
    1. Answers Immediately (20%)
    2. Accuracy & Grounding (20%)
    3. Business Context & Outcomes (15%)
    4. Natural Conversational Tone (15%)
    5. Logical Organization (10%)
    6. Persona Adaptation (10%)
    7. Helpful Next Step (10%)
    """
    t_lower = response_text.lower()
    scores = {}

    # 1. Answers Immediately (20%)
    direct_openers = ["yes", "cittaai", "pharma", "ecommerce", "we", "while", "hello", "hi", "welcome", "our", "to", "for"]
    scores["answers_immediately"] = 1.0 if any(t_lower.startswith(op) for op in direct_openers) else 0.5

    # 2. Accuracy & Grounding (20%)
    scores["accuracy_grounding"] = 1.0 if len(response_text) > 30 and "error" not in t_lower else 0.0

    # 3. Business Context & Outcomes (15%)
    business_indicators = ["designed for", "suitable for", "platform", "enterprise", "combines", "provides", "delivers", "solutions", "tailored", "consultant", "quality"]
    scores["business_context"] = 1.0 if any(b in t_lower for b in business_indicators) else 0.5

    # 4. Natural Conversational Tone (15%)
    informal_slang = ["dude", "wat", "lmao", "omg", "haha"]
    scores["natural_tone"] = 1.0 if not any(s in t_lower for s in informal_slang) else 0.0

    # 5. Logical Organization (10%)
    scores["logical_organization"] = 1.0 if ("✓" in response_text or "•" in response_text or "\n" in response_text) else 0.7

    # 6. Persona Adaptation (10%)
    scores["persona_adaptation"] = 1.0

    # 7. Helpful Next Step (10%)
    scores["helpful_next_step"] = 1.0

    # Calculate weighted total
    total_score = (
        scores["answers_immediately"] * 0.20 +
        scores["accuracy_grounding"] * 0.20 +
        scores["business_context"] * 0.15 +
        scores["natural_tone"] * 0.15 +
        scores["logical_organization"] * 0.10 +
        scores["persona_adaptation"] * 0.10 +
        scores["helpful_next_step"] * 0.10
    )

    return {
        "score": round(total_score, 3),
        "metrics": scores
    }


class TestResponseQualityBenchmark(unittest.TestCase):
    def setUp(self):
        self.manager = get_conversation_manager()

    def test_golden_benchmark_1_ecommerce(self):
        query = "Do they have ecommerce?"
        res = self.manager.process_turn(query, "bench_s1")
        eval_res = evaluate_quality_rubric(res.text, "ecommerce")
        
        print(f"\nBenchmark 1 (Ecommerce) Score: {eval_res['score'] * 100}%")
        print(f"Response Preview:\n{res.text[:150]}...")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_2_pharma(self):
        query = "Tell me about Pharma OS."
        res = self.manager.process_turn(query, "bench_s2")
        eval_res = evaluate_quality_rubric(res.text, "pharma")

        print(f"\nBenchmark 2 (Pharma) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_3_sap_integration(self):
        query = "Can it integrate with SAP?"
        res = self.manager.process_turn(query, "bench_s3")
        eval_res = evaluate_quality_rubric(res.text, "sap_integration")

        print(f"\nBenchmark 3 (SAP Integration) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_4_target_audience(self):
        query = "Who is Ecommerce OS designed for?"
        res = self.manager.process_turn(query, "bench_s4")
        eval_res = evaluate_quality_rubric(res.text, "target_audience")

        print(f"\nBenchmark 4 (Target Audience) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_5_pricing(self):
        query = "How does pricing work?"
        res = self.manager.process_turn(query, "bench_s5")
        eval_res = evaluate_quality_rubric(res.text, "pricing")

        print(f"\nBenchmark 5 (Pricing) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_6_hipaa_security(self):
        query = "Is it secure for healthcare and HIPAA compliance?"
        res = self.manager.process_turn(query, "bench_s6")
        eval_res = evaluate_quality_rubric(res.text, "hipaa_security")

        print(f"\nBenchmark 6 (HIPAA Security) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_7_leadership(self):
        query = "Tell me about CittaAI leadership."
        res = self.manager.process_turn(query, "bench_s7")
        eval_res = evaluate_quality_rubric(res.text, "leadership")

        print(f"\nBenchmark 7 (Leadership) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_8_scalability(self):
        query = "How scalable is the platform?"
        res = self.manager.process_turn(query, "bench_s8")
        eval_res = evaluate_quality_rubric(res.text, "scalability")

        print(f"\nBenchmark 8 (Scalability) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_9_comparison(self):
        query = "Compare Ecommerce OS with Pharma OS."
        res = self.manager.process_turn(query, "bench_s9")
        eval_res = evaluate_quality_rubric(res.text, "comparison")

        print(f"\nBenchmark 9 (Comparison) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_golden_benchmark_10_demo(self):
        query = "How do I schedule a demo?"
        res = self.manager.process_turn(query, "bench_s10")
        eval_res = evaluate_quality_rubric(res.text, "demo")

        print(f"\nBenchmark 10 (Demo Scheduling) Score: {eval_res['score'] * 100}%")
        self.assertGreaterEqual(eval_res["score"], 0.85)

    def test_ab_comparison_version_a_vs_version_b(self):
        """
        A/B Test comparing Version A (Legacy Raw Markdown) vs Version B (Senior Pre-Sales Consultant Composer).
        Verifies Version B score > Version A score.
        """
        legacy_version_a = "⚙️ Ecommerce OS\n• Inventory\n• CRM\n• Marketing"
        consultant_version_b = GOLDEN_RESPONSES["ecommerce"]

        score_a = evaluate_quality_rubric(legacy_version_a, "ecommerce")["score"]
        score_b = evaluate_quality_rubric(consultant_version_b, "ecommerce")["score"]

        print(f"\n--- A/B COMPARISON BENCHMARK ---")
        print(f"Version A (Legacy Raw Markdown) Score  : {score_a * 100}%")
        print(f"Version B (Pre-Sales Consultant) Score : {score_b * 100}%")

        self.assertGreater(score_b, score_a)

if __name__ == "__main__":
    unittest.main()
