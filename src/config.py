from __future__ import annotations
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_prefix="",
        extra="ignore",
        case_sensitive=False
    )

    # --- LLM Provider --
    openai_api_key:str = Field(default="",alias="OPENAI_API_KEY")
    primary_model:str = Field(default="gpt-4o-mini",alias="WANDERMIND_PRIMARY_MODEL")
    heavy_model:str = Field(default="gpt-4o",alias="WANDERMIND_HEAVY_MODEL")

    # -- fallbck model for when the primary model is unavailable
    gemini_api_key:str = Field(default="",alias="GEMINI_API_KEY")
    groq_api_key:str = Field(default="",alias="GROQ_API_KEY")

    # -- Travel tool APIs
   
    travelpayouts_api_key:str = Field(default="",alias="TRAVELPAYOUTS_API_KEY")
    travelpayouts_marker:str = Field(default="",alias="TRAVELPAYOUTS_MARKER")
    opentripmap_api_key:str = Field(default="",alias="OPENTRIPMAP_API_KEY")

    # --Langfuse
    langfuse_public_key:str = Field(default="",alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key:str = Field(default="",alias="LANGFUSE_SECRET_KEY")
    langfuse_host:str = Field(default="https://cloud.langfuse.com",alias="LANGFUSE_HOST")

    # -- MCP Server
    mcp_host:str = Field(default="http://localhost:8000",alias="WANDERMIND_MCP_HOST")
    mcp_port:int = Field(default=8000,alias="WANDERMIND_MCP_PORT")
    mcp_auth_token:str = Field(default="",alias="WANDERMIND_MCP_AUTH_TOKEN")
    use_mcp:bool= Field(default=False,alias="WANDERMIND_USE_MCP")

    # -- RUN TIME
    env:str = Field(default="development",alias="WANDERMIND_ENV")
    log_level:str = Field(default="INFO",alias="WANDERMIND_LOG_LEVEL")
    max_usd_per_request:float = Field(default=0.5,alias="WANDERMIND_MAX_USE_PER_REQUEST")

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def mcp_url(self) -> str:
        return f"http://{self.mcp_host}:{self.mcp_port}/mcp"

@lru_cache
def get_settings() -> Settings:
    """Return a cached , process -wide Settings singleton"""
    return Settings()