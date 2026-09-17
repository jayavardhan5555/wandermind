"""Output Guardrails - powered by Guardrails AI"""


from __future__ import annotations

from guardrails import GuardrailViolation
from schemas import Itinerary

def check_output(itinerary:Itinerary)-> Itinerary:
    """Check itinerary for guardrails violations."""
    raise NotImplementedError("Not implemented")