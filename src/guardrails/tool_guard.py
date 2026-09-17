"""Tool Call Guardrails - custom, app specific layer
-- tool allowlist
-- argument validation / bounds
-- timeouts and ratelimits
"""

from __future__ import annotations


ALLOWED_TOOLS = frozenset(
    {"resolve_location","search_flights","search_hotels","search_places","get_weather","convert_currency"}
)

def guard_tool_call(name: str, args: dict)-> dict:
    """Validate a tool call; return args or raise"""
    raise NotImplementedError("Not implemented")