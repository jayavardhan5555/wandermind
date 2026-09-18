"""Tool Call Guardrails - custom, app specific layer
-- tool allowlist
-- argument validation / bounds
-- timeouts and ratelimits
"""

from __future__ import annotations
from src.guardrails import GuardrailViolation

ALLOWED_TOOLS = frozenset(
    {"resolve_location","search_flights","search_hotels","search_places","get_weather","convert_currency"}
)

_IN_BOUNDS ={
    "travelers":(1,20),
    "nights":(1,60),
    "limit":(1,50),
    "days":(1,16)
}

def guard_tool_call(name: str, args: dict)-> dict:
    """Validate a tool call; return args or raise"""
    if name not in ALLOWED_TOOLS:
        raise GuardrailViolation("tool",f"tool not allowed :{name}")

    safe = dict(args)
    for key,(low,high) in _IN_BOUNDS.items():
        if safe.get(key) is None:
            continue
        try:
            value = int(safe[key])
        except (TypeError,ValueError) as ex:
            raise GuardrailViolation("tool",f"{key} must be in") from ex
        safe[key] = max(low,min(value,high))

    price = safe.get("max_price_usd")
    if price is not None and price < 0:
        raise GuardrailViolation("tool","max_price_usd must be plus")

    return safe