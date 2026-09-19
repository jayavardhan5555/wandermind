"""Input Guardrails - powered by NeMo Guardrails"""


from __future__ import annotations
import re
from src.config import get_settings
from src.guardrails import GuardrailViolation
MAX_INPUT_CHARS = 400

_INJECTION_PATTERNS =(
    r"ignore (all | the | your ) ? (previous|prior|above) (instructions|guidelines|rules|context)",
    r"disregard (all | the | your ) ? (previous|prior|above) (instructions|guidelines|rules|context)",
    r"reveal (all | the | your ) ? (previous|prior|above) (instructions|guidelines|rules|context)",
    r"developer mode"
    r"bypass (all | the | your ) ? (previous|prior|above) (instructions|guidelines|rules|context)",
    r"you are now (a|an|no longer) (assistant|AI|bot|model|language model)",
)

_INJECTION_REGEX = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

def _rule_based(text: str) -> str | GuardrailViolation:
    stripped = text.strip()
    if not stripped:
        return GuardrailViolation("input","Input is empty or whitespace only.")
    if len(stripped) > MAX_INPUT_CHARS:
        return GuardrailViolation("input","Input exceeds maximum character limit.")
    if _INJECTION_REGEX.search(stripped):
        return GuardrailViolation("input","Input contains prompt injection patterns.")
    return stripped

def _nemo_check(text: str) -> str | GuardrailViolation:

    from nemoguardrails import LLMRails,RailsConfig

    rails = LLMRails(RailsConfig.from_path("config/nemo"))
    result = rails.generate(messages=[{"role":"user","content":text}])
    content = result.get("content","") if isinstance(result,dict) else result
    if isinstance(content, str) and ("can't" in content.lower() or "cannot" in content.lower()):
        return GuardrailViolation("input","Input violates NeMo Guardrails.")
    return text

def check_input(user_message: str) -> str | GuardrailViolation:
    """Check user input for guardrails violations."""
    text = _rule_based(user_message)
    if isinstance(text, GuardrailViolation):
        return text
    if get_settings().use_nemo:
        text = _nemo_check(text)
    return text