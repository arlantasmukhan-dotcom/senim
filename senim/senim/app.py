"""FastAPI server: streams check results to the web UI as Server-Sent Events."""

from __future__ import annotations

import hmac
import json
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException
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


def require_proxy_token(x_senim_token: str | None = Header(default=None)) -> None:
    """When SENIM_PROXY_TOKEN is set (public deployments), only the web app's server may call the API.
    Locally the variable is unset and the API stays open, as before."""
    expected = os.environ.get("SENIM_PROXY_TOKEN", "")
    if expected and not hmac.compare_digest(x_senim_token or "", expected):
        raise HTTPException(status_code=403, detail="forbidden")


def _mask(key: str) -> str | None:
    """A safe-to-log preview so a misconfigured key is visible without exposing it (e.g. in /api/health)."""
    return f"{key[:10]}…{key[-4:]}" if len(key) > 16 else None


@app.get("/api/health", dependencies=[Depends(require_proxy_token)])
async def health():
    return {
        "llm": settings.has_llm,
        "llm_key_preview": _mask(settings.openrouter_api_key),
        "search": "tavily" if settings.has_search else "wikipedia (fallback)",
        "models": {"main": settings.model_main, "fast": settings.model_fast, "witnesses": settings.witnesses},
        "author_models": AUTHOR_MODELS,
        "weights": scoring.load_weights()[1],
        "max_input_chars": settings.max_input_chars,
    }


def _sse(ev: dict) -> str:
    return f"event: {ev['event']}\ndata: {json.dumps(ev['data'], ensure_ascii=False)}\n\n"


@app.post("/api/check", dependencies=[Depends(require_proxy_token)])
async def check(req: CheckRequest):
    async def stream():
        async for ev in pipeline.check(req):
            yield _sse(ev)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
