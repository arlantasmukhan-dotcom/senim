"""FastAPI server: streams check results to the web UI as Server-Sent Events."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import net, pipeline, scoring
from .config import PROJECT_ROOT, settings
from .models import CheckRequest

STATIC = PROJECT_ROOT / "static"

# Models the user can pick as "the AI that wrote this answer" (used by the Phantom Twin sensor).
AUTHOR_MODELS = [
    {"id": "openai/gpt-6-luna", "label": "ChatGPT"},
    {"id": "google/gemini-3.5-flash-lite", "label": "Gemini"},
    {"id": "anthropic/claude-haiku-4.5", "label": "Claude"},
    {"id": "deepseek/deepseek-v4-flash", "label": "DeepSeek"},
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await net.close()


app = FastAPI(title="SENIM", version="0.1", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/health")
async def health():
    return {
        "llm": settings.has_llm,
        "search": "tavily" if settings.has_search else "wikipedia (fallback)",
        "models": {"main": settings.model_main, "fast": settings.model_fast, "witnesses": settings.witnesses},
        "author_models": AUTHOR_MODELS,
        "weights": scoring.load_weights()[1],
        "max_input_chars": settings.max_input_chars,
    }


def _sse(ev: dict) -> str:
    return f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"


@app.post("/api/check")
async def check(req: CheckRequest):
    async def stream():
        async for ev in pipeline.check(req):
            yield _sse(ev)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
