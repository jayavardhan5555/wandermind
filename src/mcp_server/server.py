"""FastMCP server that exposes travel tools over MCP"""

from __future__ import annotations
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from config import get_settings, Settings

mcp = FastMCP("wandermind-travel")

@mcp.tool()
def search_flights(
    origin: Annotated[str, Field(description="IATA code or City, e.g 'JFK")],
    destination: Annotated[str, Field(description="IATA code or City, e.g 'LAX")],
    depart_date: Annotated[str, Field(description="Date in YYYY-MM-DD format")],
    travelers: Annotated[int, Field(description="Number of travelers",ge=1,le=20)]=1,
) -> dict:
    """Search for flights for a route and date"""
    settings:Settings = get_settings()
    raise NotImplementedError("Flight search is not implemented yet. Please implement the flight search logic here.")

@mcp.tool()
def search_hotels(
    location: Annotated[str, Field(description="City or location, e.g 'New York")],
    checkin_date: Annotated[str, Field(description="Check-in date in YYYY-MM-DD format")],
    checkout_date: Annotated[str, Field(description="Check-out date in YYYY-MM-DD format")],
    guests: Annotated[int, Field(description="Number of guests",ge=1,le=20)]=1,
) -> dict:
    """Search for hotels in a location for given dates"""
    settings:Settings = get_settings()
    raise NotImplementedError("Hotel search is not implemented yet. Please implement the hotel search logic here.")

@mcp.tool()
def get_weather(
    location: Annotated[str, Field(description="City or location, e.g 'New York")],
    date: Annotated[str, Field(description="Date in YYYY-MM-DD format")],
) -> dict:
    """Get weather forecast for a location and date"""
    settings:Settings = get_settings()
    raise NotImplementedError("Weather forecast is not implemented yet. Please implement the weather forecast logic here.")

@mcp.tool()
def convert_currency(
    amount: Annotated[float, Field(description="Amount to convert")],
    from_currency: Annotated[str, Field(description="Currency code to convert from, e.g 'USD")],
    to_currency: Annotated[str, Field(description="Currency code to convert to, e.g 'EUR")],
) -> dict:
    """Convert currency from one to another"""
    settings:Settings = get_settings()
    raise NotImplementedError("Currency conversion is not implemented yet. Please implement the currency conversion logic here.")

def build_server() -> FastMCP:
    """Build and return the FastMCP server with all tools registered"""
    settings = get_settings()
    mcp.settings.host = settings.mcp_host
    mcp.settings.port = settings.mcp_port
    return mcp

if __name__ == "__main__":
    build_server().run(transport="streamable-http")