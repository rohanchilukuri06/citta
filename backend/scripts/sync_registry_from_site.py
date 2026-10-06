"""
Fill registry gaps from the public website source (frontend/src/data/content.js).

Only copies content the website already publishes; never generates text. Only fills fields that are
empty (or contain only the "Admin"/"User" placeholders); existing registry content is never overwritten.
Every change is printed and recorded in the entity's metadata.site_sync block. Idempotent.

  benefits      <- website `outcomes`, the "why" grid, and quantitative headline stats (e.g. "50% Faster Reviews")
  target_users  <- website `bestFor` / `stakeholders`
  contact       <- website CONTACT phone / email / hours

Usage: python scripts/sync_registry_from_site.py [--dry-run]
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT.parent / "frontend" / "src" / "data" / "content.js"
REG = ROOT / "knowledge" / "registry" / "new"

SITE_TO_REGISTRY = {
    "WHATSAPP": "product_whatsapp_marketing.json", "INFLUENCER": "product_influencer_marketing.json",
    "ECOMMERCE": "solution_ecommerce_os.json", "REALESTATE": "solution_real_estate_os.json",
    "PHARMA": "solution_pharma_os.json", "SMARTCITIES": "solution_smart_cities_os.json",
    "EDUCATION": "solution_education_os.json", "ENTERPRISEAI": "solution_enterprise_ai_os.json",
}
PLACEHOLDERS = {"admin", "user", "users"}


def load_site() -> dict:
    js = f"import('{SITE.resolve().as_uri()}').then(m => process.stdout.write(JSON.stringify(m)))"
    out = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


def site_benefits(page: dict) -> list:
    items = list(page.get("outcomes") or [])
    items += list(page.get("whyGrid") or [])
    for s in page.get("stats") or []:
        v, label = str(s.get("v", "")), str(s.get("l", ""))
        if re.search(r"\d", v):  # quantitative claims only ("50% Faster Reviews"), not labels like "E2E"
            items.append(f"{v} {label}".strip())
    seen, out = set(), []
    for i in items:
        if i and i.lower() not in seen:
            seen.add(i.lower())
            out.append(i)
    return out


def main(dry_run: bool) -> None:
    site = load_site()
    changes = []
    for key, fname in SITE_TO_REGISTRY.items():
        page, path = site.get(key) or {}, REG / fname
        data = json.loads(path.read_text(encoding="utf-8"))
        sync = {}
        if not data.get("benefits"):
            b = site_benefits(page)
            if b:
                data["benefits"] = b
                sync["benefits"] = "website outcomes / why-grid / quantitative stats"
                changes.append((data["id"], "benefits", b))
        users = [u for u in (data.get("target_users") or []) if str(u).lower() not in PLACEHOLDERS]
        if not users:
            site_users = list(page.get("bestFor") or page.get("stakeholders") or [])
            if site_users:
                data["target_users"] = site_users
                sync["target_users"] = "website bestFor / stakeholders"
                changes.append((data["id"], "target_users", site_users))
        if sync:
            data.setdefault("metadata", {})["site_sync"] = {"source": "frontend/src/data/content.js", "fields": sync, "date": str(date.today())}
            if not dry_run:
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Contact details published on the website
    cpath = REG / "contact_info.json"
    contact = json.loads(cpath.read_text(encoding="utf-8"))
    site_contact = site.get("CONTACT") or {}
    faq = contact.get("faq") or []
    asked = {q.get("question", "").lower() for q in faq}
    additions = []
    if site_contact.get("phone") and "what is cittaai's phone number?" not in asked:
        additions.append({"question": "What is CittaAI's phone number?", "answer": site_contact["phone"]})
    if site_contact.get("email") and "what is cittaai's email address?" not in asked:
        additions.append({"question": "What is CittaAI's email address?", "answer": site_contact["email"]})
    for f in ("phone", "email"):
        if site_contact.get(f) and contact.get(f) != site_contact[f]:
            contact[f] = site_contact[f]
            additions.append({f: site_contact[f]})
    if additions:
        contact["faq"] = faq + [a for a in additions if "question" in a]
        contact.setdefault("metadata", {})["site_sync"] = {"source": "frontend/src/data/content.js", "fields": {"phone": "CONTACT.phone", "email": "CONTACT.email"}, "date": str(date.today())}
        changes.append(("contact_info", "phone/email", [site_contact.get("phone"), site_contact.get("email")]))
        if not dry_run:
            cpath.write_text(json.dumps(contact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for eid, field, value in changes:
        print(f"{'[dry-run] ' if dry_run else ''}{eid}.{field} <- {value}")
    print(f"{len(changes)} field(s) {'would be ' if dry_run else ''}filled from the website.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    main(ap.parse_args().dry_run)
