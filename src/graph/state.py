"""Shared graph state passed between agent nodes

Langgraph merges updates each node return into this TypeDict.
The Specialists write their findings;
The Supervsior reads them to decide routing;
The Composer and Critic read everything to produce and validate the final itinerary
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages

from schemas import (
    Activity,
    AgentName,
    CriticVerdict,
    FlightOption,
    HotelOption,
    Itinerary,
    ItineraryDay,
    TripRequest,
    WeatherDay,
    BudgetSummary
)

class WanderState(TypedDict,total=False):

    messages: Annotated[list,add_messages]
    request: TripRequest
    flights: list[FlightOption]
    hotels: list[HotelOption]
    activities: list[Activity]
    weather: list[WeatherDay]
    budget: BudgetSummary
    itinerary: Itinerary

    # Composer output and critic control
    verdict: CriticVerdict
    critic_feedback:str
    revisions:int

    # Routing + Human in the loop
    next_agent:AgentName
    awaiting_confirmation:bool
