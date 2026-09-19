---
title: WanderMind
emoji: "🌍"
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.27.0
python_version: "3.12"
app_file: app.py
pinned: false
---

# WanderMind

WanderMind is a multi-agent travel itinerary planner powered by Gradio and LangGraph.

## Deploy to Hugging Face Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space).
2. Select **Gradio** as the SDK and choose **Python 3.12**.
3. Create the Space, then push this repository to the Space's Git URL:

   ```powershell
   git remote add space https://huggingface.co/spaces/<YOUR_USERNAME>/<YOUR_SPACE_NAME>
   git push space main
   ```

4. In **Settings > Hardware**, select **ZeroGPU**. Free personal accounts can host up to two ZeroGPU Spaces if the account is verified and at least 30 days old.
5. Open the Space URL and click **Try demo**. This static itinerary works without any API keys.
6. For live planning, add `GEMINI_API_KEY` under **Settings > Variables and secrets**. When no OpenAI key is present, WanderMind uses Gemini automatically.
7. Optionally add `OPENAI_API_KEY`, `OPENTRIPMAP_API_KEY`, `TRAVELPAYOUTS_API_KEY`, `TRAVELPAYOUTS_MARKER`, `LANGFUSE_PUBLIC_KEY`, and `LANGFUSE_SECRET_KEY`.
8. Keep `WANDERMIND_USE_MCP` unset or set it to `false`. The Space runs the travel tools in-process by default.

The CPU Basic runtime has no hourly cost, but new Gradio Spaces generally require a paid Hugging Face plan. ZeroGPU is the current free hosting option for eligible personal accounts. The Space will install `requirements.txt` and start `app.py` automatically.
