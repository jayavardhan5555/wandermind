"""MCP server package: exposes travel tools over MCP"""

from __future__ import annotations

class ToolError(Exception):
    """A travel tool failed"""

class MissingCredentials(ToolError):
    """A required api is not configured"""

    def __init__(self, provider:str) -> None:
        super().__init__(f"Missing creds for {provider}")
        self.provider = provider

__all__ = ["ToolError","MissingCredentials"]