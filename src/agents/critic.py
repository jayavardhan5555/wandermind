""" Critic /reviewer agent
Validates the composed itinerary for feasibility, budget adherence, and quality.
Either approves it or writes `critic_feedback` and loops back to the supervisor
for a bounded number of revisions.
"""

from __future__ import annotations
from langchain_core.messages import HumanMessage, SystemMessage
from llm import get_chat_model
from graph.state import WanderState
from pydantic import BaseModel
MAX_REVISIONS = 2

_CRITIC_SYSTEM = (
    "You are a travel critic. You review the itinerary and provide feedback."
    "If the itinerary is feasible, within budget, and of high quality, approve it."
    "Otherwise, provide constructive feedback for improvement."
    "You may request revisions up to a maximum of 2 times."
)

class _Review(BaseModel):
    approved: bool
    feedback: str =""

async def critic_node(state:WanderState) -> dict:
    revisions = state.get("revisions",0)
    model = get_chat_model(heavy=True).with_structured_output(_Review)
    itinerary = state.get("itinerary")
    if itinerary is None:
        return {"critic_feedback": "No itinerary is available for review."}
    review = _Review.model_validate(model.invoke(
        [
            SystemMessage(content=_CRITIC_SYSTEM),
            HumanMessage(content=itinerary.model_dump_json()),
        ]
    ))
    if review.approved or revisions < MAX_REVISIONS:
        return {
            "crictic_feedback": review.feedback,
            "awaiting_confirmation": True,
            "next_agent":"done"
        }
    return {
        "itinerary": None,
        "critic_feedback": review.feedback,
        "revisions": revisions + 1,
        "next_agent": "supervisor"
    }

def route_from_crictic(state:WanderState) -> str:
    return state.get("next_agent","done")