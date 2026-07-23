import re
from typing import Any, List, Optional

def clean_val(val: Any) -> str:
    """Sanitizes text fields to ensure None, null, or empty string literals are never rendered."""
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ["none", "null", "empty", "unknown", "none.", "null."]:
        return ""
    return s

def sanitize_conversational_text(text: str) -> str:
    """
    Transforms website-style markdown responses into clean, conversational chat responses optimized for desktop and mobile.
    Strips markdown links, internal URLs, arrows, webpage heading artifacts, and broken CTA buttons.
    """
    if not text:
        return ""

    t = text

    # 1. Strip markdown links with internal URLs or action text: e.g. [View Solution →](/solutions/ecommerce-os)
    action_phrases = ["explore", "view", "learn more", "read more", "get started", "consult ai", "click here", "show"]
    
    def replace_md_link(match):
        label = match.group(1).strip()
        url = match.group(2).strip()
        label_clean = re.sub(r"[→\->=>]", "", label).strip()
        
        # Check if it's an action CTA phrase
        if any(p in label_clean.lower() for p in action_phrases):
            return ""
        # Return clean label without link syntax or arrow
        return label_clean

    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_md_link, t)

    # 2. Remove any remaining raw internal URLs or route paths (e.g., /products/..., /solutions/..., /services/..., /about, /contact)
    t = re.sub(r"/(?:products|services|solutions|case-studies|about|contact|recognition)[^\s\)]*", "", t)
    t = re.sub(r"https?://[^\s\)]*", "", t)

    # 3. Remove arrows and broken link symbols
    t = re.sub(r"[→\->=>]\s*", "", t)
    t = re.sub(r"\[\s*\]|\(\s*\)", "", t)

    # 4. Transform webpage headers (### Heading) into conversational bold headers
    t = re.sub(r"###\s*Overview\b", "**Overview**:", t, flags=re.IGNORECASE)
    t = re.sub(r"###\s*Summary\b", "**Summary**:", t, flags=re.IGNORECASE)
    t = re.sub(r"###\s*(Core Capabilities|Capabilities & Methodology|System Modules & Capabilities)\b", "**Key Highlights**:", t, flags=re.IGNORECASE)
    t = re.sub(r"###\s*(Key Benefits|Service Outcomes|Strategic Value|Client Benefits)\b", "**Core Value**:", t, flags=re.IGNORECASE)
    t = re.sub(r"###\s*(Implementation Workflow|System Architecture & Workflow)\b", "How It Works (Workflow):", t, flags=re.IGNORECASE)
    t = re.sub(r"###\s*(Ideal Use Cases|Target Audience)\b", "**Target Audience**:", t, flags=re.IGNORECASE)
    t = re.sub(r"###\s*", "**", t)

    # 5. Normalize bullet points to clean '• '
    t = re.sub(r"^\s*[\-\*]\s+", "• ", t, flags=re.MULTILINE)

    # 6. Remove literal "None", "null", "undefined", "Unknown"
    t = re.sub(r"\b(None|null|undefined|Unknown)\b", "", t)

    # 7. Clean up empty lines and trailing spaces
    lines = [line.strip() for line in t.split("\n")]
    cleaned_lines = []
    prev_blank = False
    for line in lines:
        if not line:
            if not prev_blank:
                cleaned_lines.append("")
                prev_blank = True
        else:
            cleaned_lines.append(line)
            prev_blank = False

    return "\n".join(cleaned_lines).strip()

def render_product(obj) -> str:
    """Renders a Product object to conversational pre-sales consultant format."""
    parts = []
    title = clean_val(obj.title or obj.name)
    tagline = clean_val(obj.tagline)
    overview = clean_val(obj.overview or obj.description)
    
    parts.append(f"Yes.\n\nCittaAI provides **{title}**.")
    if tagline:
        parts.append(f"*{tagline}*\n")
    if overview:
        parts.append(f"{overview}\n")
    
    if obj.capabilities:
        parts.append("Key Platform Capabilities:")
        for cap in obj.capabilities[:5]:
            cap_title = clean_val(cap.title)
            cap_desc = clean_val(cap.description)
            parts.append(f"✓ **{cap_title}**: {cap_desc}" if cap_desc else f"✓ **{cap_title}**")
        parts.append("")
        
    if obj.benefits:
        bens = [clean_val(b) for b in obj.benefits if clean_val(b)]
        if bens:
            parts.append("Business Value & Strategic Outcomes:")
            for benefit in bens[:4]:
                parts.append(f"• {benefit}")
            parts.append("")
            
    if obj.target_users:
        users = [clean_val(u) for u in obj.target_users if clean_val(u)]
        if users:
            parts.append(f"This makes it suitable for {', '.join(users)}.")
            
    return sanitize_conversational_text("\n".join(parts))

def render_service(obj) -> str:
    """Renders a Service object to conversational pre-sales consultant format."""
    parts = []
    title = clean_val(obj.title or obj.name)
    tagline = clean_val(obj.tagline)
    overview = clean_val(obj.overview or obj.description)

    parts.append(f"CittaAI delivers specialized enterprise services through **{title}**.")
    if tagline:
        parts.append(f"*{tagline}*\n")
    if overview:
        parts.append(f"{overview}\n")
    
    if obj.capabilities:
        parts.append("Service Highlights:")
        for cap in obj.capabilities[:5]:
            c_title = clean_val(cap.title)
            c_desc = clean_val(cap.description)
            parts.append(f"✓ **{c_title}**: {c_desc}" if c_desc else f"✓ **{c_title}**")
        parts.append("")
        
    if obj.benefits:
        bens = [clean_val(b) for b in obj.benefits if clean_val(b)]
        if bens:
            parts.append("Business Impact:")
            for benefit in bens[:4]:
                parts.append(f"• {benefit}")
            parts.append("")
            
    return sanitize_conversational_text("\n".join(parts))

def render_solution(obj) -> str:
    """Renders a Solution object to conversational pre-sales consultant format."""
    parts = []
    title = clean_val(obj.title or obj.name)
    tagline = clean_val(obj.tagline)
    overview = clean_val(obj.overview or obj.description)

    parts.append(f"Yes. CittaAI offers an enterprise platform called **{title}**.")
    if tagline:
        parts.append(f"\n*{tagline}*")
    if overview:
        parts.append(f"\nIt is designed for businesses seeking to {overview.lower() if len(overview)>0 and overview[0].isupper() else overview}.")
    
    if obj.capabilities:
        parts.append("\nIt combines:")
        for cap in obj.capabilities[:5]:
            c_title = clean_val(cap.title)
            c_desc = clean_val(cap.description)
            parts.append(f"✓ **{c_title}**: {c_desc}" if c_desc else f"✓ **{c_title}**")
        
    if obj.workflows:
        parts.append("\nOperational Workflow:")
        for step in obj.workflows[:4]:
            s_title = clean_val(step.title)
            s_desc = clean_val(step.description)
            parts.append(f"{step.step}. **{s_title}**: {s_desc}" if s_desc else f"{step.step}. **{s_title}**")

    if hasattr(obj, "target_users") and obj.target_users:
        users = [clean_val(u) for u in obj.target_users if clean_val(u)]
        if users:
            parts.append(f"\nThis makes it suitable for {', '.join(users)}.")

    return sanitize_conversational_text("\n".join(parts))

def render_company(obj) -> str:
    """Renders Company Info object into clean conversational chat response."""
    title = clean_val(obj.title or obj.name)

    parts = []
    parts.append(f"🏢 **{title}** is an Enterprise AI consultancy that helps organizations build secure, scalable, and production-ready AI solutions.")
    parts.append("")
    parts.append("Here is a quick overview:")
    parts.append("• Founded in 2022")
    parts.append("• Serves 50+ enterprise clients")
    parts.append("• Serves 100,000+ active enterprise users")
    parts.append("• Delivers ₹3.5 Cr+ measurable client ROI")
    parts.append("• Specializes in Enterprise AI, Data Engineering, and Industry-specific AI platforms")
    parts.append("")
    parts.append("**Mission**: To empower enterprise transformation through autonomous, transparent, and scalable AI solutions.")
    parts.append("**Vision**: To be the global benchmark for trusted Enterprise AI architecture.")
    parts.append("")
    parts.append("You can also ask about our leadership team, products, services, or case studies.")
    return "\n".join(parts)

def render_case_study(obj) -> str:
    """Renders Case Study object to conversational chat format."""
    parts = []
    title = clean_val(obj.title or obj.name)
    tagline = clean_val(obj.tagline)
    overview = clean_val(obj.overview or obj.description)

    parts.append(f"📈 **Case Study: {title}**")
    if tagline:
        parts.append(f"*{tagline}*\n")
    if overview:
        parts.append(f"{overview}\n")
        
    if obj.capabilities:
        parts.append("Key Highlights:")
        for cap in obj.capabilities[:4]:
            c_title = clean_val(cap.title)
            c_desc = clean_val(cap.description)
            if c_title and c_desc:
                parts.append(f"• **{c_title}**: {c_desc}")
        parts.append("")
                
    if obj.benefits:
        bens = [clean_val(b) for b in obj.benefits if clean_val(b)]
        if bens:
            parts.append("Core Value:")
            for b in bens[:4]:
                parts.append(f"• {b}")
            parts.append("")
            
    return sanitize_conversational_text("\n".join(parts))

def render_award(obj) -> str:
    """Renders Award object."""
    title = clean_val(obj.title or obj.name)
    desc = clean_val(obj.description or obj.overview)
    return f"🏆 **{title}**\n\n{desc}"

def render_faq(obj) -> str:
    """Renders FAQ object."""
    parts = []
    parts.append(f"❓ **{clean_val(obj.title or obj.name)}**\n")
    if obj.faq:
        for item in obj.faq[:5]:
            q = clean_val(item.question)
            a = clean_val(item.answer)
            if q and a:
                parts.append(f"**Q: {q}**\n*A: {a}*\n")
    return "\n".join(parts).strip()

def render_contact(obj) -> str:
    """Renders Contact object."""
    title = clean_val(obj.title or obj.name)
    overview = clean_val(obj.overview or obj.description)
    return f"📞 **{title}**\n\n{overview}\n\n**Address**: HITEC City, Hyderabad, Telangana, India"

def render_capability(cap_entry: dict) -> str:
    """Renders a single Capability object with context of parent entity."""
    cap = cap_entry["capability"]
    parent = cap_entry["parent"]
    
    c_title = clean_val(cap.title)
    c_desc = clean_val(cap.description)
    p_title = clean_val(parent.title)
    
    parts = []
    parts.append(f"⚡ **{c_title}**")
    parts.append(f"Part of **{p_title}** ({parent.type.value.title()})\n")
    parts.append(f"{c_desc}\n")
    
    if cap.features:
        parts.append("Key Features Included:")
        for feat in cap.features[:4]:
            f_title = clean_val(feat.title)
            f_desc = clean_val(feat.description)
            parts.append(f"• **{f_title}**: {f_desc}" if f_desc else f"• **{f_title}**")
        parts.append("")
        
    return sanitize_conversational_text("\n".join(parts))

def render_feature(feat_entry: dict) -> str:
    """Renders a single Feature object with context of capability and parent."""
    feat = feat_entry["feature"]
    cap = feat_entry["capability"]
    parent = feat_entry["parent"]
    
    f_title = clean_val(feat.title)
    f_desc = clean_val(feat.description)
    c_title = clean_val(cap.title)
    p_title = clean_val(parent.title)
    
    parts = []
    parts.append(f"✨ **{f_title}**")
    parts.append(f"Capability: **{c_title}** (Part of **{p_title}**)\n")
    parts.append(f"{f_desc}\n")
    
    return sanitize_conversational_text("\n".join(parts))

def render_target_users(obj: Any) -> str:
    """Renders target audience / intended users for any object."""
    title = clean_val(getattr(obj, "title", None) or getattr(obj, "name", None) or "CittaAI")
    users = getattr(obj, "target_users", None)
    if not users and isinstance(obj, dict):
        users = obj.get("target_users")
    if users and isinstance(users, list):
        user_str = ", ".join([clean_val(u) for u in users if clean_val(u)])
        return f"🎯 **Target Audience for {title}**:\n\n{title} is designed for **{user_str}**."
    return f"🎯 **Target Audience for {title}**:\n\n{title} is designed for Enterprises, Technical Leaders, and Decision Makers seeking production-ready AI solutions."

def render_section(obj: Any, section: str) -> str:
    """Renders specific section for an object."""
    sec = (section or "").lower().strip()
    if sec in ["best_for", "target", "audience"]:
        return render_target_users(obj)
    if sec in ["how_it_works", "workflow", "workflows"]:
        workflows = getattr(obj, "workflows", [])
        if not workflows and isinstance(obj, dict):
            workflows = obj.get("workflows", [])
        if workflows:
            title = clean_val(getattr(obj, "title", None) or getattr(obj, "name", None) or "CittaAI")
            steps = []
            for step in workflows:
                if hasattr(step, "step"):
                    steps.append(f"{step.step}. **{clean_val(step.title)}**: {clean_val(step.description)}")
                else:
                    steps.append(f"{step.get('step', '')}. **{clean_val(step.get('title'))}**: {clean_val(step.get('description'))}")
            wf_str = "\n".join(steps)
            return sanitize_conversational_text(f"### How {title} Works\n\n{wf_str}")
    if sec in ["benefits", "benefit", "advantages"]:
        benefits = getattr(obj, "benefits", [])
        if not benefits and isinstance(obj, dict):
            benefits = obj.get("benefits", [])
        if benefits:
            title = clean_val(getattr(obj, "title", None) or getattr(obj, "name", None) or "CittaAI")
            ben_bullets = "\n".join([f"• {clean_val(b)}" for b in benefits if clean_val(b)])
            return sanitize_conversational_text(f"### Key Benefits of {title}\n\n{ben_bullets}")
    return render_by_type(obj)

def render_by_type(obj: Any) -> str:
    """Helper dispatcher to render any schema object by KnowledgeType."""
    t = obj.type.value
    if t == "product":
        return render_product(obj)
    elif t == "service":
        return render_service(obj)
    elif t == "solution":
        return render_solution(obj)
    elif t == "company":
        return render_company(obj)
    elif t == "case_study":
        return render_case_study(obj)
    elif t == "award":
        return render_award(obj)
    elif t == "faq":
        return render_faq(obj)
    elif t == "contact":
        return render_contact(obj)
    else:
        return f"**{clean_val(obj.title)}**\n{clean_val(obj.description)}"
