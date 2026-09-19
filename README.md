---
title: WanderMind
emoji: "🌍"
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.27.0
python_version: "3.11"
app_file: app.py
pinned: false
---

# WanderMind

WanderMind is a multi-agent travel itinerary planner powered by Gradio and LangGraph.

## Deploy to Hugging Face Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space).
2. Select **Gradio** as the SDK and choose **Python 3.11**.
3. Create the Space, then push this repository to the Space's Git URL:

   ```powershell
   git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/<YOUR_SPACE_NAME>
   git push space main
   ```

4. In the Space, open **Settings > Variables and secrets** and add `OPENAI_API_KEY` as a secret.
5. Optionally add `GEMINI_API_KEY`, `OPENTRIPMAP_API_KEY`, `TRAVELPAYOUTS_API_KEY`, `TRAVELPAYOUTS_MARKER`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_SECRET_KEY`.
6. Keep `WANDERMIND_USE_MCP` unset or set it to `false`. The Space runs the travel tools in-process by default.

The Space will install `requirements.txt` and start `app.py` automatically. Open the Space URL after the build finishes.
