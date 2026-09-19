"""Langfuse tracing setup"""

from __future__ import annotations
import os

from src.config import Settings, get_settings


def _export_env(settings: Settings) -> None:
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)


def _initialize_langfuse(settings: Settings) -> bool:
    """Create the singleton Langfuse client when credentials are available."""
    if not settings.langfuse_enabled:
        return False

    _export_env(settings)
    try:
        from langfuse import Langfuse, get_client

        try:
            if get_client() is not None:
                return True
        except Exception:
            pass

        Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        return True
    except Exception as exc:
        print(f"Langfuse initialization failed: {exc}")
        return False


def get_callback_handler():
    settings = get_settings()
    if not settings.langfuse_enabled:
        return None

    if not _initialize_langfuse(settings):
        return None

    from langfuse.langchain import CallbackHandler

    return CallbackHandler(public_key=settings.langfuse_public_key)


def run_config(thread_id: str, extra_callbacks: list | None = None) -> dict:
    callbacks: list = []
    handler = get_callback_handler()
    if handler is not None:
        callbacks.append(handler)
    if extra_callbacks:
        callbacks.extend(extra_callbacks)
    return {"configurable": {"thread_id": thread_id}, "callbacks": callbacks}


def flush() -> None:
    settings = get_settings()
    if not settings.langfuse_enabled:
        return

    try:
        from langfuse import get_client

        client = get_client()
        if client is not None:
            client.flush()
    except Exception:
        pass
