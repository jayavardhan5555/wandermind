""" Critic /reviewer agent
Validates the composed itinerary for feasibility, budget adherence, and quality.
Either approves it or writes `critic_feedback` and loops back to the supervisor
for a bounded number of revisions.
"""

from __future__ import annotations

from graph.state import WanderState

MAX_REVISIONS = 2

async def critic_node(state:WanderState) -> dict:
    """Approve or requesr a revision of the itinerary"""

    ## TODO 
    raise NotImplementedError("Not yet implemented")