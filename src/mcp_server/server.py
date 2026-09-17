"""FastMCP server that exposes travel tools over MCP"""

from __future__ import annotations
from typing import Annotated,Literal

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from config import get_settings, Settings

from mcp_server import ToolError, providers

mcp = FastMCP("wandermind-travel")

_LOCAL_HOSTS = {"127.0.0.1","localhost","::1"}

@mcp.tool()
def resolve_location(
    query: Annotated[str, Field(description="Location name or IATA code, e.g 'New York' or 'JFK")],
    subtype: Annotated[Literal["city","airport","any"], Field(description="Type of location to resolve")]="any",
) -> dict:
    """Resolve a location name or IATA code to a normalized location"""
    settings:Settings = get_settings()
    try:
        return providers.resolve_location(query,subtype)
    except ToolError as exc:
        return {"error":str(exc)}

@mcp.tool()
def search_flights(
    origin: Annotated[str, Field(description="IATA code or City, e.g 'JFK")],
    destination: Annotated[str, Field(description="IATA code or City, e.g 'LAX")],
    depart_date: Annotated[str, Field(description="Date in YYYY-MM-DD format")],
    travelers: Annotated[int, Field(description="Number of travelers",ge=1,le=20)]=1,
) -> dict:
    """Search for flights for a route and date"""
    settings:Settings = get_settings()
    try:
        return providers.search_flights(origin,destination,depart_date,travelers)
    except ToolError as exc:
        return {"error":str(exc)}

@mcp.tool()
def search_places(
    city: Annotated[str, Field(description="City or location, e.g 'New York")],
    interest: Annotated[list[str], Field(description="Interest or category, e.g 'museums")],
    limit: Annotated[int, Field(description="Maximum number of results",ge=1,le=50)]=10,
) -> dict:
    """Search for places of interest in a city"""
    settings:Settings = get_settings()
    try:
        return providers.search_places(city, interest, limit)
    except ToolError as exc:
        return {"error":str(exc)}

@mcp.tool()
def search_hotels(
    location: Annotated[str, Field(description="City or location, e.g 'New York")],
    checkin_date: Annotated[str, Field(description="Check-in date in YYYY-MM-DD format")],
    nights: Annotated[int, Field(description="Number of nights",ge=1,le=20)]=1,
    travelers: Annotated[int, Field(description="Number of travelers",ge=1,le=20)]=1,
    max_price: Annotated[float, Field(description="Maximum price per night",ge=0.0)]=0.0,
) -> dict:
    """Search for hotels in a location for given dates"""
    settings:Settings = get_settings()
    try:
        return providers.search_hotels(location,checkin_date,nights,travelers,max_price)
    except ToolError as exc:
        return {"error":str(exc)}

@mcp.tool()
def get_weather(
    city: Annotated[str, Field(description="City or location, e.g 'New York")],
    start_date: Annotated[str, Field(description="Date in YYYY-MM-DD format")],
    days: Annotated[int, Field(description="Number of days for forecast",ge=1,le=7)]=1,
) -> dict:
    """Get weather forecast for a location and date"""
    settings:Settings = get_settings()
    try:
        return providers.get_weather(city,start_date,days)
    except ToolError as exc:
        return {"error":str(exc)}

@mcp.tool()
def convert_currency(
    amount: Annotated[float, Field(description="Amount to convert")],
    from_currency: Annotated[str, Field(description="Currency code to convert from, e.g 'USD")],
    to_currency: Annotated[str, Field(description="Currency code to convert to, e.g 'EUR")],
) -> dict:
    """Convert currency from one to another"""
    settings:Settings = get_settings()
    try:
        return providers.convert_currency(amount,from_currency,to_currency)
    except ToolError as exc:
        return {"error":str(exc)}   

def build_server() -> FastMCP:
    """Build and return the FastMCP server with all tools registered"""
    settings = get_settings()
    mcp.settings.host = settings.mcp_host
    mcp.settings.port = settings.mcp_port

    if settings.mcp_host not in _LOCAL_HOSTS:
        from mcp.server.transport_security import TransportSecuritySettings

        host_port = f"{settings.mcp_host}:{settings.mcp_port}"
        mcp.settings.transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=[host_port,f"localhost:{settings.mcp_port}"],
        )
    return mcp

if __name__ == "__main__":
    build_server().run(transport="streamable-http")