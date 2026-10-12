"""
Spelling and chat-shorthand normalisation for visitor questions, applied before query understanding.

Visitors type "wat prodcts u hav", "where is ur ofice", "wats the prise of education os". Two steps make those
readable to the rule- and embedding-based engine without touching correctly spelled text:

  1. Shorthand: a fixed map of chat abbreviations ("u" -> "you", "hv" -> "have", "wats" -> "what is").
  2. Near-miss correction: a word the engine doesn't know (not in the registry's vocabulary, not a function word,
     not in PROTECTED) that is one edit away from a domain keyword is replaced by that keyword.

Only the engine's copy of the question is changed; the visitor's original text is what the answer model sees.
"""

import re
from typing import Iterable, Optional, Set

SHORTHAND = {
    "u": "you", "ur": "your", "yr": "your", "urs": "yours", "r": "are",
    "wat": "what", "wht": "what", "wut": "what", "wot": "what", "wats": "what is", "whats": "what is", "wts": "what is",
    "whos": "who is", "hows": "how is", "wheres": "where is", "hw": "how", "hv": "have", "hav": "have", "hve": "have",
    "abt": "about", "abot": "about", "bout": "about", "pls": "please", "plz": "please", "plzz": "please",
    "tel": "tell", "gv": "give", "giv": "give", "sel": "sell", "cn": "can", "cud": "could", "wud": "would", "shud": "should",
    "frm": "from", "wid": "with", "thru": "through", "ppl": "people", "bcoz": "because", "coz": "because", "bcz": "because",
    "im": "i am", "wanna": "want to", "wana": "want to", "gonna": "going to", "info": "information",
    "num": "number", "ph": "phone", "addr": "address", "loc": "location", "msg": "message", "biz": "business",
    "edu": "education", "mgmt": "management", "mktg": "marketing", "svc": "service", "svcs": "services", "ecom": "ecommerce",
    "busines": "business", "bussiness": "business", "buisness": "business", "bussines": "business", "compny": "company",
    "colege": "college", "collage": "college", "studnets": "students",
}

# Keywords the engine's rules look for. Unknown words one edit away from these are corrected to them.
KEYWORDS = {
    # catalog
    "services", "service", "products", "product", "solutions", "solution", "offerings", "industries", "industry",
    "catalog", "portfolio", "offer", "offers", "provide", "provides", "everything",
    # aspects
    "price", "prices", "pricing", "cost", "costs", "charge", "charges", "features", "feature", "benefits", "benefit",
    "capabilities", "workflow", "demo", "about", "studies",
    # company
    "contact", "address", "office", "location", "phone", "number", "email", "team", "members", "member", "founder",
    "founders", "leadership", "leaders", "management", "awards", "recognition", "clients", "client", "customers",
    "company", "partners",
    # offering names
    "education", "finance", "estate", "enterprise", "commerce", "ecommerce", "marketing", "whatsapp", "influencer",
}

# Real words that sit one edit from a keyword and must never be "corrected"
PROTECTED = {
    "serves", "served", "server", "servers", "serving", "servings", "servicing", "production", "productive", "produce",
    "producer", "producers", "produces", "produced", "solving", "solvent", "offering", "offset", "officer", "officers",
    "official", "prove", "proved", "proves", "proven", "provider", "providers", "providing", "provided",
    "contract", "contracts", "prize", "prizes", "pride", "prime", "prince", "princes", "coast", "coats", "change",
    "changes", "changed", "charger", "fiance", "fiancee", "pharmacy", "founded", "flounder", "fonder", "loaders",
    "ladders", "phony", "prone", "demon", "demons", "abort", "abut", "above", "commence", "influence", "influences",
    "influenced", "studio", "studios", "mail", "sale", "sales", "start", "started", "starts", "state", "states",
    "market", "markets", "manage", "manager", "managers", "managed", "lead", "leads", "leader", "local", "locate",
    "located", "counts", "order", "orders", "other", "others", "after", "often", "every",
}

_WORD = re.compile(r"[A-Za-z]+")


class SpellingNormaliser:
    def __init__(self, known_words: Optional[Iterable[str]] = None):
        # Words the engine already understands (registry vocabulary, function words, …) are left exactly as typed
        self.known: Set[str] = {w.lower() for w in (known_words or ())} | KEYWORDS | PROTECTED

    def _near_keyword(self, low: str) -> Optional[str]:
        try:
            from rapidfuzz import fuzz
            from rapidfuzz.distance import OSA
        except ImportError:
            return None
        # One slip (dropped, extra, swapped or wrong letter); two only in long words, where it can't reach another word
        budget = 2 if len(low) >= 9 else 1
        best, best_key = None, (0.0, 0)
        for kw in KEYWORDS:
            if kw[0] != low[0] or abs(len(kw) - len(low)) > budget:
                continue
            if len(low) == 4 and len(kw) < 5:   # "team" vs "term": four-letter words are too close to each other
                continue
            if OSA.distance(low, kw, score_cutoff=budget) > budget:
                continue
            key = (fuzz.ratio(low, kw), len(kw))
            if key > best_key:
                best, best_key = kw, key
        return best

    def _fix(self, m: "re.Match") -> str:
        word = m.group(0)
        low = word.lower()
        if low in SHORTHAND:
            return SHORTHAND[low]
        if len(low) < 4 or low in self.known or low.rstrip("s") in self.known or (low + "s") in self.known:
            return word
        return self._near_keyword(low) or word

    def normalise(self, text: str) -> str:
        return _WORD.sub(self._fix, text)
