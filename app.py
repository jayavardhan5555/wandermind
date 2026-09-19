"""Gradio entry point , Hugging Face Space runs this fule"""

from __future__ import annotations
from src.config import get_settings
import threading
import uuid
from datetime import date
from langchain_core.messages import HumanMessage
from src.graph.builder import build_graph
from src.observability import flush,run_config
from src.schemas import BudgetSummary, Itinerary, ItineraryDay

import gradio as gr

_graph = None

def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

def _maybe_start_mcp():
    settings = get_settings()
    if not settings.use_mcp:
        return
    from src.mcp_server.server import build_server
    server = build_server()
    thread = threading.Thread(target=lambda: server.run(transport="streamable-http"),daemon=True)
    thread.start()
    print("MCP server started on port 8000")

def _render(itinerrary) -> str:
    if itinerrary is None:
        return "No itinerary yet."
    lines = [f'## {itinerrary.destination} ({len(itinerrary.days)} days)']
    if itinerrary.budget:
        lines.append(f"**Budget:** ${itinerrary.budget.total_usd:,.2f} ({'within budget' if itinerrary.budget.within_budget else 'over budget'})")
        lines.append("")
    for i,day in enumerate(itinerrary.days,1):
        lines.append(f"### {i}. {day.title}")
        lines.extend(f"{item}" for item in day.items)
        lines.append("")
    if itinerrary.disclaimers:
        for d in itinerrary.disclaimers:
            lines.append(f"*Disclaimer: {d}*")
    return "\n".join(lines)

def _demo_itinerary() -> Itinerary:
    return Itinerary(
        destination="Tokyo",
        summary="A compact five-day Tokyo sampler focused on food, history, and neighborhoods.",
        days=[
            ItineraryDay(
                day=date(2026, 4, 10),
                title="Asakusa and Ueno",
                items=["Senso-ji at sunrise", "Street-food crawl near Nakamise-dori", "Tokyo National Museum"],
                est_cost_usd=55,
            ),
            ItineraryDay(
                day=date(2026, 4, 11),
                title="Modern Tokyo",
                items=["Meiji Shrine", "Harajuku lunch", "Shibuya Sky at sunset"],
                est_cost_usd=70,
            ),
            ItineraryDay(
                day=date(2026, 4, 12),
                title="Markets and neighborhoods",
                items=["Tsukiji Outer Market breakfast", "Ginza walk", "Small izakaya dinner"],
                est_cost_usd=85,
            ),
            ItineraryDay(
                day=date(2026, 4, 13),
                title="A slower local day",
                items=["Yanaka neighborhood walk", "Tea and wagashi tasting", "Kappabashi kitchen street"],
                est_cost_usd=45,
            ),
            ItineraryDay(
                day=date(2026, 4, 14),
                title="Farewell Tokyo",
                items=["Coffee in Daikanyama", "TeamLab visit", "Last ramen dinner"],
                est_cost_usd=65,
            ),
        ],
        budget=BudgetSummary(
            flights_usd=0,
            lodging_usd=0,
            activities_usd=320,
            total_usd=320,
            within_budget=True,
        ),
        disclaimers=["This is a static demo itinerary; prices and availability are illustrative."],
    )

def demo():
    return gr.update(value=_render(_demo_itinerary())), gr.update(visible=False)

async def plan(message:str,thread_id:str|None):
    """Plan the travel itinerary for the given message"""
    if not(message or "").strip():
        return thread_id,gr.update(value="_Please describe your trip!_"),gr.update(visible=False)

    tid = thread_id or str(uuid.uuid4())
    config = run_config(tid)
    try:
        await _get_graph().ainvoke({"messages":[HumanMessage(content=message)]},config=config)
    except Exception as exc:
        print(f"Graph invocation failed: {exc}")
        return tid, gr.update(value=f"**Planning failed:** {exc}"),gr.update(visible=False)
    finally:
        flush()

    snapshot = _get_graph().get_state(config)
    state = snapshot.values
    if state.get("rejected"):
        reason = state.get("critic_feedback","request blocked by guardrails")
        return tid, gr.update(value=f"**Rejected**: {reason}"),gr.update(visible=False)

    awaiting = "confirm" in (snapshot.next or ())
    return tid, gr.update(value=_render(state.get("itinerary"))),gr.update(visible=awaiting)
    
async def confirm(thread_id: str | None):
    if not thread_id:
        return gr.update(), gr.update(visible=False)
    config = run_config(thread_id)
    try:
        await _get_graph().ainvoke(None,config)
        state = _get_graph().get_state(config=config).values
    finally:
        flush()
    return gr.update(value=_render(state.get("itinerary"))), gr.update(visible=False)

    

def build_ui()->gr.Blocks:
    with gr.Blocks(title="Wandermind") as demo:
        gr.Markdown("# WanderMind - multi agent travel planner")
        thread = gr.State(None)
        with gr.Row():
            msg = gr.Textbox(
                placeholder="Describe your trip ...",
                label="Plan a 5-day tokyo trip for 2 under $2500, love food & history",
                scale=4
            )
            send = gr.Button("Plan",variant="primary",scale=1)
            demo_btn = gr.Button("Try demo",scale=1)
        itinerary = gr.Markdown("_Your Itinernary will appare here_")
        confirm_btn = gr.Button("Confirm & Finalize",visible=False,variant="primary")

        send.click(plan,inputs=[msg,thread],outputs=[thread,itinerary,confirm_btn])
        demo_btn.click(demo,outputs=[itinerary,confirm_btn])
        confirm_btn.click(confirm,inputs=[thread],outputs=[itinerary,confirm_btn])
    return demo

if __name__ =="__main__":
    _maybe_start_mcp()
    build_ui().launch()