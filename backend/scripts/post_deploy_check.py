"""
Post-deploy check: run after every deployment to confirm the live chatbot really works.

    python scripts/post_deploy_check.py https://<backend-host> [https://<website-host>]

It checks, against the running service (nothing is mocked):
  1. /api/health is Healthy, with no configuration errors (answer-model key, email key and sender verified)
  2. the website's origin is allowed by CORS, and the website's build points at this backend
  3. real questions get real answers: misspelled ones, the complete team list, contact details, pricing,
     out-of-scope questions, and the meeting agent's first steps (cancelled, so nothing is saved or emailed)

Every check here is a failure that reached production once. Exit code 0 = all passed, 1 = something is wrong.
"""

import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

FALLBACK_MARK = "I can't compose a full answer right now"
results: List[Tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> bool:
    results.append((bool(ok), name, detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + (f"\n          {detail}" if detail and not ok else ""))
    return bool(ok)


def ask(client: httpx.Client, base: str, origin: str, session: str, message: str) -> Tuple[str, Dict[str, Any]]:
    text, done = "", {}
    with client.stream("POST", f"{base}/api/chat", json={"session_id": session, "message": message},
                       headers={"Origin": origin}) as r:
        if r.status_code != 200:
            return f"HTTP {r.status_code}", {}
        for line in r.iter_lines():
            if line.startswith("data: "):
                event = json.loads(line[6:])
                if event.get("done"):
                    done = event
                else:
                    text += event.get("text", "")
    return text, done.get("metrics", {})


def team_names() -> List[str]:
    """CittaAI's own team from the registry (people whose title is a role at another company are excluded)."""
    path = Path(__file__).resolve().parents[1] / "knowledge" / "registry" / "new" / "leadership_info.json"
    people = json.loads(path.read_text(encoding="utf-8")).get("capabilities", [])
    return [p["title"] for p in people if " of " not in str(p.get("subtitle", "")).lower()]


def main(base: str, site: Optional[str]) -> int:
    base = base.rstrip("/")
    origin = (site or "https://cittaai.com").rstrip("/")
    with httpx.Client(timeout=90, follow_redirects=True) as client:
        print(f"\n1. Health — {base}")
        try:
            health = client.get(f"{base}/api/health").json()
        except (httpx.HTTPError, ValueError) as e:
            check(False, "backend is reachable", f"{type(e).__name__}: {e}")
            return 1
        check(health.get("status") == "Healthy", "status is Healthy", json.dumps(health)[:400])
        issues = health.get("config_issues", [])
        check(not [i for i in issues if i.startswith("ERROR")], "no configuration errors", "\n          ".join(issues))
        for warning in (i for i in issues if i.startswith("WARNING")):
            print(f"  note  {warning}")
        check(health.get("llm_provider", {}).get("status") == "Configured", "answer model key works",
              str(health.get("llm_provider")))
        email = health.get("email", {})
        check(email.get("status") in ("Verified", "Configured") and email.get("transport") != "none",
              "email sending is configured", str(email))
        check(health.get("vector_index", {}).get("fresh") is True, "knowledge index is fresh", str(health.get("vector_index")))

        print(f"\n2. Website connection — {origin}")
        pre = client.options(f"{base}/api/chat", headers={"Origin": origin, "Access-Control-Request-Method": "POST",
                                                          "Access-Control-Request-Headers": "content-type"})
        check(pre.headers.get("access-control-allow-origin") == origin, "website origin is allowed (CORS)",
              f"HTTP {pre.status_code}, allow-origin={pre.headers.get('access-control-allow-origin')}")
        if site:
            try:
                page = client.get(origin)
                scripts = re.findall(r'src="(/static/js/main\.[^"]+\.js)"', page.text)
                bundle = client.get(origin + scripts[0]).text if scripts else ""
                host = re.sub(r"^https?://", "", base)
                check(page.status_code == 200 and host in bundle, "website build points at this backend",
                      "REACT_APP_BACKEND_URL in the website's build does not match this backend — set it in Vercel and redeploy")
            except httpx.HTTPError as e:
                check(False, "website is reachable", f"{type(e).__name__}: {e}")

        print("\n3. Real questions")
        sid = "deploy-check-" + uuid.uuid4().hex[:8]

        def question(q: str, name: str, operation: Optional[str] = None, contains: Tuple[str, ...] = ()) -> None:
            text, m = ask(client, base, origin, sid + uuid.uuid4().hex[:4], q)
            problems = []
            if FALLBACK_MARK in text:
                problems.append("answer model did not respond (fallback text served)")
            if operation and m.get("operation") != operation:
                problems.append(f"routed to {m.get('operation')}, expected {operation}")
            missing = [c for c in contains if c.lower() not in text.lower()]
            if missing:
                problems.append("answer is missing: " + ", ".join(missing))
            check(not problems, f"{name}  ({q!r})", "; ".join(problems) + f" | answer: {text[:200]!r}")

        question("Who os the ceo", "typo in a simple question", "get_leadership", ("Akhil Reddy",))
        question("who are the citta team members", "team list is complete", "get_leadership", tuple(team_names()))
        question("wat servics do u ofer", "misspelled catalog question", "list_services")
        question("wat prodcts u hav", "misspelled products question", "list_products")
        question("where is ur ofice", "misspelled contact question", "get_contact", ("Hyderabad",))
        question("tell me about your company", "'your company' means CittaAI", "get_company_info")
        question("wats the prise of education os", "misspelled pricing question", "get_pricing")
        question("whats the wether today", "out-of-scope question is declined", "decline_out_of_domain")

        meeting = sid + "-meeting"
        t1, _ = ask(client, base, origin, meeting, "I want to book a meeting")
        t2, _ = ask(client, base, origin, meeting, "Deploy Check")
        t3, _ = ask(client, base, origin, meeting, "cancel")
        check("name" in t1.lower() and "company or organisation" in t2.lower() and "cancelled" in t3.lower(),
              "meeting agent asks for name, then company, and cancels cleanly", f"{t1[:120]!r} / {t2[:120]!r} / {t3[:120]!r}")

    failed = [name for ok, name, _ in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed." + (" FAILED: " + "; ".join(failed) if failed else " All good."))
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
