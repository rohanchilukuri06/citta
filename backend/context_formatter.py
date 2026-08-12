"""
Generic Context Formatter for CittaAI Knowledge Registry Entities.

Converts raw registry entity dictionaries or Pydantic models into compact, 
semantically rich text blocks suitable for LLM prompts, stripping raw JSON 
overhead (search indexes, UUIDs, metadata) while preserving all factual company information.
"""

from typing import Dict, Any, List, Union


def format_compact_entity_context(entity_data: Union[Dict[str, Any], Any]) -> str:
    """
    Transforms a raw registry entity dictionary or object into a compact text block.
    Works generically across products, services, solutions, company info, leadership, etc.
    """
    if not entity_data:
        return ""

    # Convert Pydantic models or custom objects to dict if needed
    if hasattr(entity_data, "model_dump"):
        data = entity_data.model_dump()
    elif hasattr(entity_data, "dict"):
        data = entity_data.dict()
    elif isinstance(entity_data, dict):
        data = entity_data
    else:
        return str(entity_data)

    lines: List[str] = []

    # 1. Header Information
    name = data.get("name") or data.get("title") or data.get("id", "Entity")
    entity_type = data.get("type", "")
    if hasattr(entity_type, "value"):
        entity_type = entity_type.value
    entity_type = str(entity_type).upper() if entity_type else ""

    title = data.get("title")
    tagline = data.get("tagline")

    lines.append(f"Entity: {name}" + (f" ({entity_type})" if entity_type else ""))
    if title and title != name:
        lines.append(f"Title: {title}")
    if tagline:
        lines.append(f"Tagline: {tagline}")

    # 2. Overview / Description
    overview = data.get("overview") or data.get("description")
    if overview:
        lines.append(f"\nOverview:\n{str(overview).strip()}")

    # 3. Target Users / Audience
    target_users = data.get("target_users") or data.get("best_for")
    if target_users:
        if isinstance(target_users, list):
            lines.append(f"\nTarget Audience: {', '.join(str(u) for u in target_users)}")
        elif isinstance(target_users, str):
            lines.append(f"\nTarget Audience: {target_users}")

    # 4. Capabilities & Features
    capabilities = data.get("capabilities", [])
    if capabilities and isinstance(capabilities, list):
        lines.append("\nCapabilities:")
        for cap in capabilities:
            if hasattr(cap, "model_dump"):
                cap = cap.model_dump()
            elif hasattr(cap, "dict"):
                cap = cap.dict()

            if isinstance(cap, dict):
                cap_title = cap.get("title", "")
                cap_sub = cap.get("subtitle", "")
                cap_desc = cap.get("description", "")

                header_parts = [cap_title]
                if cap_sub and cap_sub != cap_title:
                    header_parts.append(f"({cap_sub})")

                lines.append(f"- {' '.join(header_parts)}")
                if cap_desc and cap_desc != cap_title:
                    lines.append(f"  {cap_desc}")

                features = cap.get("features", [])
                if features and isinstance(features, list):
                    for feat in features:
                        if hasattr(feat, "model_dump"):
                            feat = feat.model_dump()
                        elif hasattr(feat, "dict"):
                            feat = feat.dict()

                        if isinstance(feat, dict):
                            f_title = feat.get("title") or feat.get("description", "")
                            lines.append(f"  * Feature: {f_title}")
                        elif isinstance(feat, str):
                            lines.append(f"  * Feature: {feat}")
            elif isinstance(cap, str):
                lines.append(f"- {cap}")

    # 5. Workflows / Implementation Steps
    workflows = data.get("workflows") or (
        data.get("how_it_works", {}).get("steps")
        if isinstance(data.get("how_it_works"), dict)
        else None
    )
    if workflows and isinstance(workflows, list):
        lines.append("\nImplementation Workflows:")
        for step in workflows:
            if hasattr(step, "model_dump"):
                step = step.model_dump()
            elif hasattr(step, "dict"):
                step = step.dict()

            if isinstance(step, dict):
                s_num = step.get("step", "")
                s_title = step.get("title", "")
                s_desc = step.get("description", "")
                prefix = f"{s_num}. " if s_num else "- "
                step_str = f"{prefix}{s_title}"
                if s_desc and s_desc != s_title:
                    step_str += f": {s_desc}"
                lines.append(step_str)
            elif isinstance(step, str):
                lines.append(f"- {step}")

    # 6. Benefits & Key Metrics
    benefits = data.get("benefits", [])
    if benefits and isinstance(benefits, list):
        lines.append("\nBenefits & Results:")
        for b in benefits:
            lines.append(f"- {b}")

    # 7. Use Cases
    use_cases = data.get("use_cases", [])
    if use_cases and isinstance(use_cases, list):
        lines.append("\nUse Cases:")
        for uc in use_cases:
            lines.append(f"- {uc}")

    # 8. FAQs
    faqs = data.get("faq", [])
    if faqs and isinstance(faqs, list):
        lines.append("\nFrequently Asked Questions:")
        for f in faqs:
            if hasattr(f, "model_dump"):
                f = f.model_dump()
            elif hasattr(f, "dict"):
                f = f.dict()

            if isinstance(f, dict):
                q = f.get("question", "")
                a = f.get("answer", "")
                lines.append(f"Q: {q}\nA: {a}")

    # 9. Company / Special Entity Handling
    if data.get("founder"):
        lines.append(f"\nFounder: {data.get('founder')}")
    if data.get("vision"):
        lines.append(f"Vision: {data.get('vision')}")
    if data.get("mission"):
        lines.append(f"Mission: {data.get('mission')}")

    # Contact Info
    if data.get("email") or data.get("phone"):
        lines.append("\nContact Info:")
        if data.get("email"):
            lines.append(f"- Email: {data.get('email')}")
        if data.get("phone"):
            lines.append(f"- Phone: {data.get('phone')}")
        if data.get("business_hours"):
            lines.append(f"- Hours: {data.get('business_hours')}")

    return "\n".join(lines)
