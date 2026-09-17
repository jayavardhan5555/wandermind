"""
Supervisor agent

Parses the raw user message into a validated TripRequest, then on each turn decides which specialist should act next (or that planning ic omplete
returns `next_agent` in state; the graph's conditional edges route on it.
"""

from __future__ import annotations

from graph.state import WanderState

async def supervisor_node(state:WanderState) -> dict:
    """route the workflow and normalize the request
    TODO:

    call the LLM gateway with a routing prompt + the current state summary;
    parse intent into TriRequest in the first turn;
    set `next_agent` to one of the specialists or compose/done

    """
    raise NotImplementedError("Not implemeted")