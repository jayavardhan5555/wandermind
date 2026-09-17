"""
Specialist agent nodes

Each Specialist calls its MCP backed tool(s) and writes structured findings into
state. They are intentionally narrow so the supervisor can compose them freely
"""

from __future__ import annotations

from graph.state import WanderState

async def flight_node(state:WanderState) -> dict:
    """Search flights and write `flights` to state (via MCP `search_flights`)."""
    raise NotImplementedError("Not implemeted")

async def hotel_node(state:WanderState) -> dict:
    """Search hotels and write `hotels` to state (via MCP `search_hotels`)."""
    raise NotImplementedError("Not implemeted")

async def activities_node(state:WanderState) -> dict:
    """Search activities and write `activities` to state (via MCP `search_places`)."""
    raise NotImplementedError("Not implemeted")

async def weather_node(state:WanderState) -> dict:
    """fetch forecast and write weather to state (via MCP `get_weather`)."""
    raise NotImplementedError("Not implemeted")

async def budget_node(state:WanderState) -> dict:
    """Reconsile totals vs. the user's budeget (via MCP `convert_currency`)."""
    raise NotImplementedError("Not implemeted")

async def composer_node(state:WanderState) -> dict:
    """Merge findings into a validated `Itinerary` (heavy model via gateway)."""
    raise NotImplementedError("Not implemeted")