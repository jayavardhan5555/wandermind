"""Tool Call Guardrails - custom, app specific layer
-- tool allowlist
-- argument validation / bounds
-- timeouts and ratelimits
"""

from __future__ import annotations

from guardrails import GuardrailViolation

ALLOWED_TOOLS = frozenset(
    {"search_flights","search_hotles","search_places","get_weather","convert_currency"}
)

def guard_tool_call(name: str, args: dict)-> dict:
    """Validate a tool call; return args or raise"""
    raise NotImplementedError("Not implemented")