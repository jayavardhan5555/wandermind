"""Bridge that loads MCP tools as LangChainTools for the agents"""


from __future__ import annotations
from src.config import get_settings, Settings

async def load_tools() -> list:
    """Load MCP tools as LangChainTools for the agents"""
    settings:Settings = get_settings()
    raise NotImplementedError("MCP tool loading is not implemented yet. Please implement the tool loading logic here.")