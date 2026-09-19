"""LLM gateway built on LiteLLM"""

from __future__ import annotations
from functools import lru_cache
from pydantic import SecretStr

from src.config import get_settings, Settings

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

def _fallback_model_list(settings:Settings) -> list[dict]:
    alt = [
        name
        for name, present in (
            ("gemini", settings.gemini_api_key),
        )
        if present
    ]
    if not alt:
        return []
    return [{"primary": alt}, {"heavy": alt}]

@lru_cache
def get_router():
    """Return a cached , process -wide LiteLLM router singleton"""
    settings = get_settings()
    import litellm
    from litellm import Router

    return Router(
        model_list=_model_list(settings),
        fallbacks=_fallback_model_list(settings),
        num_retries=2,
        cache_responses=True
    )
    
    raise NotImplementedError("LiteLLM router creation is not implemented yet. Please implement the router creation logic here.")

def get_chat_model(*,heavy:bool=False):

    from langchain_litellm import ChatLiteLLMRouter
    model_name = "heavy" if heavy else "primary"
    
    return ChatLiteLLMRouter(router=get_router(),model_name=model_name)