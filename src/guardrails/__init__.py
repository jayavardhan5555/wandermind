"""Guardrails package: layered input , output and tool safety"""


from __future__ import annotations

class GuardrailViolation(Exception):
    """Raised when a guardrail blocks a request ,response or tool request"""

    def __init__(self, layer:str,reason:str) -> None:
        super().__init__(f"[{layer}]{reason}")
        self.layer = layer
        self.reason = reason