"""
Supervisor agent

Parses the raw user message into a validated TripRequest, then on each turn decides which specialist should act next (or that planning ic omplete
returns `next_agent` in state; the graph's conditional edges route on it.
"""

from __future__ import annotations
from typing import cast
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import WanderState
from llm import get_chat_model
from schemas import TripRequest
from src.guardrails import GuardrailViolation
from guardrails.input_guard import check_input

_PARSE_SYSTEM =(
    "You extract structured trip details from a traveler's request."
    "Infer sensible values where the traveler implies them; leave truly unknown"
    "fields null. Dates must be ISO (YYYY-MM-DD)"
)

def _latest_user_text(state:WanderState)-> str:
    for msg in reversed(state.get("messages") or []):
        if getattr(msg,"type",None) == "human":
            return msg.content
        if isinstance(msg,dict) and msg.get("role") == "user":
            return msg.get("content", "")
    return ""

def _parse_request(text: str) -> TripRequest:
    model = get_chat_model().with_structured_output(TripRequest)
    return cast(
        TripRequest,
        model.invoke(
            [
                SystemMessage(content=_PARSE_SYSTEM),
                HumanMessage(content=text),
            ]
        ),
    )

def _route(state:WanderState) -> str:
    if "flights"not in state:
        return "flight"
    if "hotels" not in state:
        return "hotel" 
    if "activities" not in state:
        return "activity"
    if "weather" not in state:
        return "weather"
    if "budget" not in state:
        return "budget"
    if state.get("itinerary") is None:
        return "compose"
    return "done"

async def supervisor_node(state:WanderState) -> dict:
    update:dict = {}
    if not state.get("request"):
        try:
            text = cast(str, check_input(_latest_user_text(state)))
        except GuardrailViolation as ex:
            return {"rejected": True,"critic_feedback": ex.reason,"next_agent":"done"}
        update["request"] = _parse_request(text)
        state = cast(WanderState, {**state, **update})
    update["next_agent"] = _route(state)
    return update

def route_from_supervisor(state:WanderState) -> str:
    return state.get("next_agent","done")