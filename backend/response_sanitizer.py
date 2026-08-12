"""
Phase 5.5 Response Sanitizer Component.
Sanitizes outgoing chatbot responses to ensure NO internal validation messages,
debug tags, raw UUIDs, confidence scores, or implementation details ever reach the user.
"""
import re
import logging

logger = logging.getLogger(__name__)

class ResponseSanitizer:
    """
    Strips internal execution details and sanitizes outgoing responses.
    """
    def sanitize(self, text: str) -> str:
        if not text:
            return ""

        s = str(text)

        # 1. Remove validation header prefixes
        s = re.sub(r"\*Validation checks applied:\*\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"Validation checks applied:\s*", "", s, flags=re.IGNORECASE)

        # 2. Remove internal debug block tags
        s = re.sub(r"\[(?:DEBUG|EVIDENCE|METRICS|STRICT GROUNDING|UNAVAILABLE SECTIONS)\].*?\n", "", s, flags=re.IGNORECASE)

        # 3. Remove raw UUID strings (e.g. 4aca3b20-23a6-53b8-8155-bc69713f79a0)
        s = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "", s, flags=re.IGNORECASE)

        # 4. Remove internal registry metadata fields if present
        s = re.sub(r"\b(?:registry_id|entity_id|confidence_score|routing_path):\s*\S+", "", s, flags=re.IGNORECASE)

        # 5. Clean up redundant empty lines / extra whitespace
        s = re.sub(r"\n{3,}", "\n\n", s).strip()

        return s

_sanitizer_instance = None

def get_response_sanitizer() -> ResponseSanitizer:
    global _sanitizer_instance
    if _sanitizer_instance is None:
        _sanitizer_instance = ResponseSanitizer()
    return _sanitizer_instance
