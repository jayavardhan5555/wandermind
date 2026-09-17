"""LLM gateway built on LiteLLM"""

from __future__ import annotations
from functools import lru_cache

from config import get_settings, Settings

def _model_list(settings:Settings) -> list[dict]:

    models:list[dict] = [
        {
            "model_name": "primary",
            "litellm_params":{
                "model": f"openai/{settings.primary_model}",
                "api_key": settings.openai_api_key
            }
        },
        {
            "model_name": "heavy",
            "litellm_params":{
                "model": f"openai/{settings.heavy_model}",
                "api_key": settings.openai_api_key
            }
        },
        {
            "model_name": "gemini",
            "litellm_params":{
                "model": "gemini/gemini-1.5-turbo",
                "api_key": settings.gemini_api_key
            }
        },
        {
            "model_name": "groq",
            "litellm_params":{
                "model": "groq/groq-1.0",
                "api_key": settings.groq_api_key
            }

        }
    ]
    return models

@lru_cache
def get_router():
    """Return a cached , process -wide LiteLLM router singleton"""
    settings = get_settings()
    raise NotImplementedError("LiteLLM router creation is not implemented yet. Please implement the router creation logic here.")