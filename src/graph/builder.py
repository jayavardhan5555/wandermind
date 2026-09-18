"""
Graph assembly : wires agent nodes and conditional edges

The supervisor routes to specialists, results converge on the budget node, the compose
builds the itinerary, and the critic either loops back for a revision or approvers
"""

from __future__ import annotations
from langgraph.graph import START,END, StateGraph

from agents.critic import critic_node,route_from_crictic
from graph.state import WanderState
from agents.supervisor import supervisor_node,route_from_supervisor
from agents.specialist import (
   activities_node,flight_node,hotel_node,weather_node,composer_node,budget_node
)
from langgraph.checkpoint.memory import MemorySaver
_SPECIALISTS ={
   "flight":flight_node,
   "hotel": hotel_node,
   "activities":activities_node,
   "weather":weather_node,
   "budget":budget_node
}


def build_graph():

   graph = StateGraph(WanderState)

   #Add nodes
   graph.add_node("supervisor",supervisor_node)
   for name,node in _SPECIALISTS.items():
      graph.add_node(name,node)
   graph.add_node("compose",composer_node)
   graph.add_node("critic",critic_node)

   graph.add_edge(START,"supervisor")
   graph.add_conditional_edges("supervisor",route_from_supervisor,{
      "flight":"flight",
        "hotel":"hotel",
        "activities":"activities",
        "weather":"weather",
        "budget":"budget",
        "compose":"compose",
        "done":END
   })
   for name in _SPECIALISTS.keys():
        graph.add_edge(name,"supervisor")
   graph.add_edge("compose","critic")
   graph.add_conditional_edges("critic",route_from_crictic,{
        "supervisor":"supervisor",
        "done":END
    })

   return graph.compile(checkpointer=MemorySaver())