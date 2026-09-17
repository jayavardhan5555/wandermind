"""Input Guardrails - powered by NeMo Guardrails"""


from __future__ import annotations

from guardrails import GuardrailViolation

def check_input(user_message:str)-> str:
    """Check user input for guardrails violations."""
    raise NotImplementedError("Not implemented")