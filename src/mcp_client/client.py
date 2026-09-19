"""Bridge that loads MCP tools as LangChainTools for the agents"""


from __future__ import annotations
from src.config import get_settings, Settings
import functools
from src.guardrails.tool_guard import guard_tool_call
import json
import asyncio
from src.mcp_server import ToolError
from src.mcp_server import providers

_tool_cache:dict | None = None

@functools.lru_cache
def get_mcp_client():
    """return a cached MultiServer MCP Client poined at the WanderMind Server"""
    from langchain_mcp_adapters.client import MultiServerMCPClient
    settings = Settings()
    return MultiServerMCPClient(
        {
            "wandermind":{
                "url":settings.mcp_url,
                "transport":"streamable_http",
                "headers":{"X-WanderMind-Token":settings.mcp_auth_token}
            }
        }
    )
async def _tool_map() -> dict:
    global _tool_cache
    if _tool_cache is None:
        _tool_cache = {t.name: t for t in await load_tools()}
    return _tool_cache

def _coerce(result)->dict:
    if isinstance(result,dict):
        return result
    if isinstance(result,str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"result":result}
    return {"result": result}

async def _call_via_mcp(name:str,args:dict) -> dict:
    tool = (await _tool_map()).get(name)
    if tool is None:
        raise ToolError(f"MCP tool not found: {name}")
    return _coerce(await tool.ainvoke(args)
                   )

def _call_inline(name:str,args:dict)-> dict:
    func = getattr(providers,name,None)
    if func is None:
        raise ToolError(f"unknown tool: {name}")
    return func(**args)




async def load_tools() -> list:
    """Load MCP tools as LangChainTools for the agents"""
    settings:Settings = get_settings()
    return await get_mcp_client().get_tools()


async def call_tool(name:str,**args) -> dict:
    """Invoke a travel tool by name, through MCP or in-process per Settings.use_mcp"""
    args = guard_tool_call(name,args)
    if get_settings().use_mcp:
        return await _call_via_mcp(name,args)
    return await asyncio.to_thread(functools.partial(_call_inline, name, args))