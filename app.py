"""Gradio entry point , Hugging Face Space runs this fule"""

from __future__ import annotations
from src.config import get_settings

import gradio as gr

def _placeholder_respond(message:str,history:list) -> str:
    return(
        ""
    )

def build_ui()->gr.Blocks:
    with gr.Blocks(title="Wandermind") as demo:
        gr.Markdown("# WanderMind - multi agent travel planner")
        gr.ChatInterface(fn=_placeholder_respond)
    return demo

if __name__ =="__main__":
    _ = get_settings()
    build_ui().launch()