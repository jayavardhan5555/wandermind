"""Output Guardrails - powered by Guardrails AI"""

from __future__ import annotations

import importlib
import re
import sys
from functools import lru_cache
from pathlib import Path

from src.config import get_settings
from src.schemas import Itinerary
from src.guardrails import GuardrailViolation

_REDACT = ["REDACTED"]
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")


@lru_cache(maxsize=1)
def _guardrails_guard():
    """Create a Guardrails AI guard without importing this package recursively."""
    local_package = sys.modules.pop("guardrails", None)
    source_root = Path(__file__).resolve().parents[1]
    removed_paths = [
        path for path in sys.path
        if Path(path or ".").resolve() == source_root
    ]
    sys.path[:] = [path for path in sys.path if path not in removed_paths]
    try:
        guardrails_ai = importlib.import_module("guardrails")
        return guardrails_ai.Guard.for_pydantic(output_class=Itinerary)
    finally:
        sys.path[:0] = removed_paths
        if local_package is not None:
            sys.modules["guardrails"] = local_package


def _text_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for field in value.values():
            yield from _text_values(field)
    elif isinstance(value, list):
        for item in value:
            yield from _text_values(item)


def _check_sensitive_content(itinerary: Itinerary) -> None:
    for value in _text_values(itinerary.model_dump(mode="python")):
        if _EMAIL.search(value):
            raise GuardrailViolation("output", "Itinerary contains an email address.")
        if any(marker.lower() in value.lower() for marker in _REDACT):
            raise GuardrailViolation("output", "Itinerary contains redacted content.")


def check_output(itinerary: Itinerary) -> Itinerary:
    """Validate and return an itinerary, raising on unsafe or invalid output."""
    normalized = Itinerary.model_validate(itinerary)
    _check_sensitive_content(normalized)

    if not get_settings().use_guardrails_ai:
        return normalized

    outcome = _guardrails_guard().validate(normalized.model_dump_json())
    if not outcome.validation_passed or outcome.validated_output is None:
        reason = "Guardrails AI rejected the itinerary."
        if outcome.reask and outcome.reask.fail_results:
            reason = outcome.reask.fail_results[0].error_message
        raise GuardrailViolation("output", reason)

    validated = Itinerary.model_validate(outcome.validated_output)
    _check_sensitive_content(validated)
    return validated