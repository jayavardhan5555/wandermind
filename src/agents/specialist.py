"""
Specialist agent nodes

Each Specialist calls its MCP backed tool(s) and writes structured findings into
state. They are intentionally narrow so the supervisor can compose them freely
"""

from __future__ import annotations
from langchain_core.messages import HumanMessage, SystemMessage
from llm import get_chat_model
from mcp_server import ToolError,providers
from schemas import (
    Activity,
    FlightOption,
    HotelOption,
    Itinerary,
    ItineraryDay,   
    BudgetSummary,
    WeatherDay,
    TripRequest
    )

_COMPOSE_SYSTEM = (
    "You are a travel itinerary composer. You merge the findings from the flight, "
    "hotel, activities, weather, and budget specialists into a coherent and feasible itinerary.    "
    "Ensure that the itinerary is within budget, considers the weather forecast,"
    " and provides a balanced experience for the traveler.    "
    "If any specialist's findings are missing or incomplete, make reasonable assumptions to fill in the gaps.    "
    "The final output should be a structured Itinerary object, including a summary, daily breakdown, and budget summary.    "
    "If you cannot produce a valid itinerary, return an empty Itinerary object.")

from graph.state import WanderState

def _iata(query:str,kind:str)-> str | None:
    try:
        result = providers.resolve_location(query,kind)
    except ToolError as e:
        print(f"Error resolving {kind} for {query}: {e}")
        return None
    for loc in result.get("locations",[]):
        if loc.get("iata_code"):
            return loc["iata_code"]
    return None

def flight_node(state:WanderState) -> dict:
    if "request" not in state:
        return {}
    req: TripRequest = state["request"]
    if not (req.origin and req.destination and req.start_date):
        return {"flights": []}
    origin = _iata(req.origin,"airport") or req.origin.upper()
    destination = _iata(req.destination,"airport") or req.destination.upper()
    try:
        data = providers.search_flights(
            origin,
            destination,
            req.start_date.isoformat(),
            req.travelers)
    except ToolError as e:
        print(f"Error searching flights: {e}")
        return {"flights": []}
    return {"flights": [FlightOption.model_validate(f) for f in data.get("flights",[])]}
    

async def hotel_node(state:WanderState) -> dict:
    """Search hotels and write `hotels` to state (via MCP `search_hotels`)."""
    req = state.get("request")
    if req is None or not req.destination or not req.start_date:
        return {"hotels": []}

    try:
        data = providers.search_hotels(
            req.destination,
            req.start_date.isoformat(),
            _nights(req),
            req.travelers,
        )
    except ToolError as e:
        print(f"Error searching hotels: {e}")
        return {"hotels": []}
    return {"hotels": [HotelOption.model_validate(h) for h in data.get("hotels", [])]}

async def activities_node(state:WanderState) -> dict:
    """Search activities and write `activities` to state (via MCP `search_places`)."""
    req = state.get("request")
    if req is None or not req.destination:
        return {"activities": []}

    try:
        data = providers.search_places(req.destination, req.interests)
    except ToolError as e:
        print(f"Error searching activities: {e}")
        return {"activities": []}
    return {"activities": [Activity.model_validate(a) for a in data.get("places", [])]}

async def weather_node(state:WanderState) -> dict:
    """fetch forecast and write weather to state (via MCP `get_weather`)."""
    req = state.get("request")
    if req is None or not req.destination or not req.start_date:
        return {"weather": []}

    try:
        data = providers.get_weather(
            req.destination,
            req.start_date.isoformat(),
            min(_nights(req), 7),
        )
    except ToolError as e:
        print(f"Error fetching weather: {e}")
        return {"weather": []}
    return {"weather": [WeatherDay.model_validate(day) for day in data.get("days", [])]}
def _nights(req:TripRequest)-> int:
    if req.start_date and req.end_date:
        return (req.end_date - req.start_date).days
    return 1

async def budget_node(state:WanderState) -> dict:
    req = state.get("request")
    if req is None:
        return {"budget": None}
    flights: list[FlightOption] = state.get("flights",[])
    hotels: list[HotelOption] = state.get("hotels",[])
    activities: list[Activity] = state.get("activities",[])
    nights = _nights(req)

    flights_usd = sum(f.price_usd for f in flights)
    lodging_usd = sum(h.price_per_night_usd * nights for h in hotels)
    activities_usd = sum(a.est_cost_usd for a in activities)
    total_usd = flights_usd + lodging_usd + activities_usd
    within_budget = req.budget_usd is None or total_usd <= req.budget_usd
    return {
        "budget": BudgetSummary(
            flights_usd=flights_usd,
            lodging_usd=lodging_usd,
            activities_usd=activities_usd,
            total_usd=total_usd,
            within_budget=within_budget
        )}

def _compose_context(state:WanderState) -> str:
    """Produce a JSON string of the current state for the composer prompt"""
    def dump(objs)-> list:
        return [o.model_dump_json() for o in objs] if objs else []
    context = {
        "request": state.get("request"),
        "flights": state.get("flights"),
        "hotels": state.get("hotels"),
        "activities": state.get("activities"),
        "weather": state.get("weather"),
        "budget": state.get("budget"),
        "revision_feedback": state.get("critic_feedback")
    }
    return Itinerary.model_validate(context).model_dump_json()

async def composer_node(state:WanderState) -> dict:
    model = get_chat_model(heavy=True).with_structured_output(Itinerary)
    itinerary = model.invoke(
        [
            SystemMessage(content=_COMPOSE_SYSTEM),
            HumanMessage(content=_compose_context(state)),
        ]
    )
    return {"itinerary": itinerary}