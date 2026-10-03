"""OpenRouter chat client (OpenAI-compatible API) with retries, concurrency limit and cost tracking."""

from __future__ import annotations

import asyncio
import contextlib
import contextvars
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable

import httpx

from .config import settings
from .net import client
from .text import parse_json_block

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(Exception):
    pass


class LLMUnavailable(LLMError):
    """No API key configured."""


@dataclass
class Usage:
    calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0

    def add(self, usage: dict | None) -> None:
        self.calls += 1
        if not usage:
            return
        self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
        self.completion_tokens += int(usage.get("completion_tokens") or 0)
        self.cost_usd += float(usage.get("cost") or 0.0)


current_usage: contextvars.ContextVar[Usage | None] = contextvars.ContextVar("current_usage", default=None)
# Set per check, so one big check queues behind its own calls instead of blocking everyone else's.
request_slots: contextvars.ContextVar[asyncio.Semaphore | None] = contextvars.ContextVar("request_slots", default=None)

# A test (or an offline demo) can replace the network call with a function
# (model, messages, temperature, max_tokens) -> reply text.
Backend = Callable[[str, list[dict], float, int], Awaitable[str]]
_backend: Backend | None = None
_semaphores: dict[int, asyncio.Semaphore] = {}


def set_backend(fn: Backend | None) -> None:
    global _backend
    _backend = fn


def available() -> bool:
    return _backend is not None or settings.has_llm


def _global_semaphore() -> asyncio.Semaphore:
    loop_id = id(asyncio.get_running_loop())
    if loop_id not in _semaphores:
        _semaphores[loop_id] = asyncio.Semaphore(settings.llm_global_concurrency)
    return _semaphores[loop_id]


def new_request_slots() -> asyncio.Semaphore:
    return asyncio.Semaphore(settings.llm_concurrency)


def _request(model: str, messages: list[dict], temperature: float, max_tokens: int,
             stream: bool = False) -> tuple[dict, dict]:
    if not settings.openrouter_api_key:
        raise LLMUnavailable("OPENROUTER_API_KEY is not set")
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "usage": {"include": True},
        # Keep hidden reasoning short and out of the reply: we only want the answer.
        "reasoning": {"effort": "low", "exclude": True},
    }
    if stream:
        payload["stream"] = True
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://github.com/yv7m8fchnb-dev/Wit-teens",
        "X-Title": "SENIM",
    }
    return payload, headers


async def _openrouter_stream(model: str, messages: list[dict], temperature: float, max_tokens: int,
                             usage_out: list) -> AsyncIterator[str]:
    """Yield the reply as it is generated. Retries only before the first token arrives."""
    payload, headers = _request(model, messages, temperature, max_tokens, stream=True)
    delay = 1.5
    for attempt in range(4):
        started = False
        try:
            async with client().stream("POST", OPENROUTER_URL, json=payload, headers=headers, timeout=90) as r:
                if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                if r.status_code != 200:
                    body = (await r.aread()).decode(errors="replace")[:300]
                    raise LLMError(f"{model}: HTTP {r.status_code} {body}".strip())
                async for line in r.aiter_lines():
                    if not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    try:
                        chunk = json.loads(line[6:])
                    except ValueError:
                        continue
                    if chunk.get("error"):
                        raise LLMError(f"{model}: {chunk['error'].get('message', 'stream error')}")
                    if chunk.get("usage"):
                        usage_out.append(chunk["usage"])
                    for choice in chunk.get("choices") or []:
                        text = (choice.get("delta") or {}).get("content") or ""
                        if text:
                            started = True
                            yield text
                return
        except httpx.HTTPError as e:
            if started or attempt == 3:
                raise LLMError(f"{model}: network error {e}") from e
            await asyncio.sleep(delay)
            delay *= 2
    raise LLMError(f"{model}: gave up after retries")


async def chat_stream(model: str, messages: list[dict], *, temperature: float = 0.0,
                      max_tokens: int = 1200) -> AsyncIterator[str]:
    """Like chat(), but yields the reply piece by piece so work can start before the model finishes."""
    usage: list = []
    async with request_slots.get() or contextlib.nullcontext():
        async with _global_semaphore():
            if _backend is not None:
                yield await _backend(model, messages, temperature, max_tokens)
            else:
                got_any = False
                async for piece in _openrouter_stream(model, messages, temperature, max_tokens, usage):
                    got_any = True
                    yield piece
                if not got_any:
                    raise LLMError(f"{model}: empty reply")
    u = current_usage.get()
    if u is not None:
        u.add(usage[-1] if usage else None)


async def _openrouter(model: str, messages: list[dict], temperature: float, max_tokens: int) -> tuple[str, dict | None]:
    payload, headers = _request(model, messages, temperature, max_tokens)
    delay = 1.5
    for attempt in range(4):
        try:
            r = await client().post(OPENROUTER_URL, json=payload, headers=headers, timeout=90)
        except httpx.HTTPError as e:
            if attempt == 3:
                raise LLMError(f"{model}: network error {e}") from e
            await asyncio.sleep(delay)
            delay *= 2
            continue
        if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
            await asyncio.sleep(delay)
            delay *= 2
            continue
        try:
            data = r.json()
        except ValueError as e:
            raise LLMError(f"{model}: HTTP {r.status_code}, non-JSON reply") from e
        if r.status_code != 200 or "error" in data:
            msg = (data.get("error") or {}).get("message", "") if isinstance(data, dict) else ""
            raise LLMError(f"{model}: HTTP {r.status_code} {msg}".strip())
        try:
            content = data["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError) as e:
            raise LLMError(f"{model}: malformed reply") from e
        if not content.strip():
            raise LLMError(f"{model}: empty reply")
        return content, data.get("usage")
    raise LLMError(f"{model}: gave up after retries")


async def chat(model: str, messages: list[dict], *, temperature: float = 0.0, max_tokens: int = 1200) -> str:
    # Take the check's own slot first, so a waiting check never holds a process-wide slot.
    async with request_slots.get() or contextlib.nullcontext():
        async with _global_semaphore():
            if _backend is not None:
                content, usage = await _backend(model, messages, temperature, max_tokens), None
            else:
                content, usage = await _openrouter(model, messages, temperature, max_tokens)
    u = current_usage.get()
    if u is not None:
        u.add(usage)
    return content


async def chat_json(model: str, messages: list[dict], *, temperature: float = 0.0, max_tokens: int = 2500) -> Any:
    """Chat and parse JSON from the reply; one repair retry if the model returns broken JSON."""
    reply = await chat(model, messages, temperature=temperature, max_tokens=max_tokens)
    try:
        return parse_json_block(reply)
    except ValueError:
        repair = messages + [
            {"role": "assistant", "content": reply},
            {"role": "user", "content": "Your reply was not valid JSON. Reply again with ONLY the JSON, nothing else."},
        ]
        reply = await chat(model, repair, temperature=0.0, max_tokens=max_tokens)
        try:
            return parse_json_block(reply)
        except ValueError as e:
            raise LLMError(f"{model}: could not parse JSON reply") from e
