"""
Crawl https://cittaai.com and store its published content as chatbot knowledge.

The site is a React single-page app: every URL serves the same shell and all page text ships inside one
JS bundle. This script downloads the sitemap and the bundle, extracts the structured page data with
scripts/crawl_live_site.js (evaluated in an isolated Node vm, no site code runs), and normalises it into
knowledge/site/cittaai_live.json — one document per page section, each mapped to a registry entity with
its source URL. Nothing is generated; text is copied verbatim.

Usage: python scripts/sync_live_site.py
Then:  python build_index.py   (the site documents are indexed alongside the registry)
"""

import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "knowledge" / "site" / "cittaai_live.json"
SITE = "https://cittaai.com"
UA = {"User-Agent": "CittaAI-chatbot-knowledge-sync/1.0"}

SERVICE_ENTITY = {
    "data-engineering": ["data_engineering"],
    "enterprise-and-agentic-ai": ["enterprise_agentic_ai"],
    "ai-strategy-and-advisory": ["ai_strategy"],
    "ai-powered-martech": ["ai_powered_marketing"],
}
SUBSERVICE_EXTRA = {"branding-and-strategy": ["martech_360"]}  # MarTech 360 = the Branding & Strategy engine (site footer link)
INDUSTRY_ENTITY = {"agentic": ["enterprise_ai_os"], "lms": ["education_os"], "pharma": ["pharma_os"], "govtech": ["smart_cities_os"],
                   "marktech": ["ecommerce_os"]}
SOLUTION_LINK_ENTITY = {"/solutions/ecommerce": "ecommerce_os", "/solutions/real-estate": "real_estate_os",
                        "/solutions/pharma": "pharma_os", "/solutions/smart-cities": "smart_cities_os"}


def fetch_bundle(tmp: Path) -> tuple:
    home = httpx.get(SITE + "/", headers=UA, timeout=30, follow_redirects=True).text
    m = re.search(r'src="(/assets/index-[^"]+\.js)"', home)
    if not m:
        raise SystemExit("Could not find the site bundle in the homepage HTML")
    bundle_url = SITE + m.group(1)
    (tmp / "bundle.js").write_bytes(httpx.get(bundle_url, headers=UA, timeout=60).content)
    sitemap = httpx.get(SITE + "/sitemap.xml", headers=UA, timeout=30).text
    return bundle_url, re.findall(r"<loc>([^<]+)</loc>", sitemap)


def doc(entities, section, title, text, url, kind):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return {"entities": entities, "section": section, "title": title, "text": text, "url": url, "kind": kind} if text else None


def normalise(arrays: list) -> list:
    docs = []
    for arr in arrays:
        items = arr["items"]
        keys = set().union(*[set(i) for i in items if isinstance(i, dict)])
        # 1. Service categories with sub-service pages
        if {"id", "title", "items"} <= keys and all(i.get("id") in SERVICE_ENTITY for i in items):
            for cat in items:
                for s in cat.get("items") or []:
                    ents = SERVICE_ENTITY[cat["id"]] + SUBSERVICE_EXTRA.get(s.get("id"), [])
                    url = f"{SITE}/services/{cat['id']}/{s.get('id')}"
                    name = f"{cat['title']} — {s.get('title')}"
                    docs.append(doc(ents, "overview", name, f"{s.get('title')}: {s.get('shortDescription', '')}. {s.get('fullDescription', '')}", url, "service_page"))
                    if s.get("features"):
                        docs.append(doc(ents, "capabilities", name, f"{s.get('title')} features: " + "; ".join(map(str, s["features"])), url, "service_page"))
                    if s.get("benefits"):
                        docs.append(doc(ents, "benefits", name, f"{s.get('title')} benefits: " + "; ".join(map(str, s["benefits"])), url, "service_page"))
                    if s.get("process"):
                        docs.append(doc(ents, "workflows", name, f"{s.get('title')} process: " + " ".join(
                            f"{i + 1}. {p.get('title')}: {p.get('description')}" for i, p in enumerate(s["process"])), url, "service_page"))
                    for f in s.get("faq") or []:
                        docs.append(doc(ents, "faq", name, f"Q: {f.get('question')} A: {f.get('answer')}", url, "service_page"))
                    for c in s.get("caseStudies") or []:
                        docs.append(doc(ents, "case_studies", name, f"{s.get('title')} case study — {c.get('title')}: "
                                        + "; ".join(map(str, c.get("points") or [])) + f". Result: {c.get('result', '')}", url, "service_page"))
        # 2. Industry operating-system pages (hero, metrics, features)
        elif {"heroDescription", "features"} <= keys:
            for p in items:
                ents = INDUSTRY_ENTITY.get(p.get("id"), [])
                if not ents:
                    continue
                url = f"{SITE}/solutions"
                docs.append(doc(ents, "overview", p.get("title"), f"{p.get('title')} ({p.get('heroSubtitle')}): {p.get('heroDescription')}", url, "industry_page"))
                if p.get("metrics"):
                    docs.append(doc(ents, "benefits", p.get("title"), f"{p.get('title')} results: " + "; ".join(
                        f"{m.get('value')} {m.get('label')}" for m in p["metrics"] if isinstance(m, dict)), url, "industry_page"))
                for f in p.get("features") or []:
                    if isinstance(f, dict):
                        docs.append(doc(ents, "capabilities", p.get("title"), f"{f.get('title')} ({f.get('subtitle', '')}): {f.get('description', '')} "
                                        + "; ".join(map(str, f.get("points") or [])), url, "industry_page"))
        # 3. Solutions list with links
        elif {"link", "features"} <= keys:
            for s in items:
                ent = SOLUTION_LINK_ENTITY.get(s.get("link"))
                if ent:
                    docs.append(doc([ent], "overview", s.get("title"), f"{s.get('title')}: {s.get('description')} " + "; ".join(
                        f.get("title", "") + " " + f.get("description", "") if isinstance(f, dict) else str(f) for f in s.get("features") or [])
                        + " " + str(s.get("footer") or ""), SITE + s["link"], "solutions_list"))
        # 4. Q&A lists (SEO page FAQ)
        elif keys >= {"question", "answer"}:
            for q in items:
                docs.append(doc(["ai_powered_marketing"], "faq", "SEO — FAQ", f"Q: {q.get('question')} A: {q.get('answer')}",
                                f"{SITE}/services/ai-powered-martech/seo", "seo_page"))
        # 5. Team
        elif keys >= {"name", "role"}:
            for p in items:
                docs.append(doc(["leadership_info"], "leadership", "Leadership", f"{p.get('name')} — {p.get('role')}. {p.get('bio', '')}",
                                f"{SITE}/about", "about_page"))
        # 6. Generic title/description cards (why CittaAI, challenges, capability stack, SEO page cards)
        elif keys >= {"title", "description"}:
            text = " ".join(f"{i.get('title')}: {i.get('description')}" + (f" (solution: {i['solution']})" if i.get("solution") else "")
                            for i in items if isinstance(i, dict))
            seo = any("SEO" in str(i.get("title")) or "search" in str(i.get("description", "")).lower() for i in items)
            docs.append(doc(["ai_powered_marketing"] if seo else ["company_info"], "capabilities" if seo else "overview",
                            "SEO services" if seo else "Why CittaAI", text,
                            f"{SITE}/services/ai-powered-martech/seo" if seo else SITE + "/", "site_cards"))
    return [d for d in docs if d]


def main():
    tmp = ROOT / "data" / "site_crawl"
    tmp.mkdir(parents=True, exist_ok=True)
    bundle_url, pages = fetch_bundle(tmp)
    subprocess.run(["node", str(ROOT / "scripts" / "crawl_live_site.js"), str(tmp / "bundle.js"), str(tmp / "arrays.json")], check=True)
    docs = normalise(json.loads((tmp / "arrays.json").read_text(encoding="utf-8")))
    team = [d["text"] for d in docs if d["section"] == "leadership"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": SITE, "bundle": bundle_url, "crawled": str(date.today()), "sitemap_pages": pages,
                               "documents": docs}, indent=1, ensure_ascii=False), encoding="utf-8")
    by = {}
    for d in docs:
        for e in d["entities"]:
            by[e] = by.get(e, 0) + 1
    print(f"{len(docs)} documents from {bundle_url} ({len(pages)} sitemap pages) -> {OUT}")
    print("per entity:", dict(sorted(by.items())))
    print("team on the live site:", team)


if __name__ == "__main__":
    main()
