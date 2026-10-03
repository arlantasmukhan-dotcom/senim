"""Shared key-value store for the cache, rate limits and the daily budget.

With UPSTASH_REDIS_REST_URL/TOKEN (or Vercel KV's KV_REST_API_URL/TOKEN) set, everything lives in
Redis and is shared by all server instances. Without them the store is this process's memory.
A Redis failure never breaks a check: reads miss, counters fall back to memory.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

import httpx

log = logging.getLogger("senim.store")

_MEM_MAX = 2000
_REDIS_MAX_VALUE = 512_000
_mem: dict[str, tuple[float, Any]] = {}
_client: httpx.AsyncClient | None = None


def _redis_conf() -> tuple[str, str] | None:
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL") or ""
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN") or ""
    return (url.rstrip("/"), token) if url and token else None


def shared() -> bool:
    return _redis_conf() is not None


async def _redis(*commands: list) -> list[Any]:
    global _client
    url, token = _redis_conf()  # type: ignore[misc]
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=3.0)
    r = await _client.post(f"{url}/pipeline", json=list(commands), headers={"Authorization": f"Bearer {token}"})
    r.raise_for_status()
    out = []
    for item in r.json():
        if "error" in item:
            raise RuntimeError(item["error"])
        out.append(item.get("result"))
    return out


def _mem_get(key: str) -> Any:
    hit = _mem.get(key)
    if hit and hit[0] > time.time():
        return hit[1]
    return None


def _mem_put(key: str, value: Any, ttl: int) -> None:
    if len(_mem) >= _MEM_MAX:
        for k in sorted(_mem, key=lambda k: _mem[k][0])[: _MEM_MAX // 10]:
            _mem.pop(k, None)
    _mem[key] = (time.time() + ttl, value)


async def get(key: str) -> Any:
    if (hit := _mem_get(key)) is not None:
        return hit
    if not shared():
        return None
    try:
        raw = (await _redis(["GET", key]))[0]
    except Exception as e:
        log.warning("redis GET failed: %s", e)
        return None
    if raw is None:
        return None
    value = json.loads(raw)
    _mem_put(key, value, 600)
    return value


async def put(key: str, value: Any, ttl: int) -> None:
    _mem_put(key, value, ttl)
    if not shared():
        return
    raw = json.dumps(value, ensure_ascii=False)
    if len(raw) > _REDIS_MAX_VALUE:
        return
    try:
        await _redis(["SET", key, raw, "EX", ttl])
    except Exception as e:
        log.warning("redis SET failed: %s", e)


async def incr(key: str, amount: float, ttl: int) -> float:
    """Add to a counter that expires `ttl` seconds after its last change; returns the new total.
    Callers put the time window (hour, day) in the key, so a refreshed expiry never merges windows."""
    if shared():
        try:
            total, _ = await _redis(["INCRBYFLOAT", key, str(amount)], ["EXPIRE", key, ttl])
            return float(total)
        except Exception as e:
            log.warning("redis INCR failed, counting in memory: %s", e)
    hit = _mem.get(key)
    expires, total = hit if hit and hit[0] > time.time() else (time.time() + ttl, 0.0)
    _mem[key] = (expires, total + amount)
    return total + amount


async def read_counter(key: str) -> float:
    if shared():
        try:
            raw = (await _redis(["GET", key]))[0]
            return float(raw or 0)
        except Exception as e:
            log.warning("redis GET failed, reading memory: %s", e)
    hit = _mem.get(key)
    return float(hit[1]) if hit and hit[0] > time.time() else 0.0


def clear_memory() -> None:
    _mem.clear()


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
