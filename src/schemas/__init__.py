"""Pydantic data models: the domain schemas shared across agents and tools
Keeping these strict means agent outputs are always validated structured data, which itself an out put guardrail."""


from __future__ import annotations

from datetime import date
from tkinter import N
from pydantic import BaseModel,Field
from typing import Literal

class LocationMatch(BaseModel):
    name:str
    iata_code:str | None = None
    subtype:str | None = None
    country:str | None = None
    lat:float | None = None
    lon:float | None = None

class TripRequest(BaseModel):
    """Normalized user request produced by the supervisor after intent parsing"""

    destination: str
    origin: str | None = None
    start_date : date | None = None
    end_date: date | None = None
    travelers: int = Field(default=1,ge=1,le=20)
    budget_usd: float | None = Field(default=None,ge=0)
    interests: list[str] = Field(default_factory=list)
    notes: str | None = None

class FlightOption(BaseModel):
    airline:str
    price_usd:float = Field(ge=0)
    depart:str
    arrive:str
    stops:int = Field(default=0,ge=0)

class HotelOption(BaseModel):
    name:str
    price_per_night_usd: float = Field(ge=0)
    rating:float | None = Field(default=None,ge=0,le=5)
    area:str | None = None

class Activity(BaseModel):
    name:str
    category:str | None = None
    est_cost_usd:float = Field(default=0,ge=0)
    lat:float | None = None
    lon:float | None = None

class WeatherDay(BaseModel):
    day:date
    summary:str
    high_c:float | None = None
    low_c:float | None = None

class BudgetSummary(BaseModel):
    flights_usd:float=Field(default=0,ge=0)
    lodging_usd:float=Field(default=0,ge=0)
    activities_usd:float=Field(default=0,ge=0)
    total_usd:float=Field(default=0,ge=0)
    within_budget:bool = True

class ItineraryDay(BaseModel):
    day:date | None = None
    title:str
    items: list[str] = Field(default_factory=list)
    est_cost_usd:float = Field(default=0,ge=0)

class Itinerary(BaseModel):
    """The final validated output returned to the user"""
    destination:str
    summary:str
    days:list[ItineraryDay] = Field(default_factory=list)
    budget: BudgetSummary | None = None
    disclaimers:list[str]= Field(default_factory=list)

class AgentName: Literal[
    "flight",
    "hotel",
    "activities",
    "weather",
    "budget",
    "compose",
    "done"
]

class RouteDecision(BaseModel):
    """structured supervisor output : the next hop and on the first turn"""

    next_agent: AgentName
    request: TripRequest
    reason: str | None = None

class CriticVerdict(BaseModel):
    approved: bool
    score: float | None = Field(default=None,ge=0,le=10)
    feedback:str | None = None

__all__ =[
    "LocationMatch",
    "TripRequest",
    "FlightOption",
    "AgentName",
    "HotelOption",
    "Activity",
    "WeatherDay",
    "BudgetSummary",
    "ItineraryDay",
    "Itinerary",
    "RouteDecision",
    "CriticVerdict"
]
