"""Langfuse tracing setup"""

from __future__ import annotations

from src.config import get_settings

def get_callback_handler():

    settings = get_settings()
    if not settings.langfuse_enabled:
        return None
    raise NotImplementedError()