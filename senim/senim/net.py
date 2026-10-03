"""Shared HTTP layer: one async client, a shared TTL cache, retries, and an SSRF-safe fetch."""

from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

from . import store
from .config import settings

_client: httpx.AsyncClient | None = None
_CACHE_TTL = 6 * 3600
WEEK = 7 * 86400   # for data that changes monthly or slower (Wikidata ids, monthly pageviews)


def client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=settings.http_timeout,
            follow_redirects=True,
            headers={"User-Agent": settings.user_agent},
        )
    return _client


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
    await store.close()


def _cache_key(key: str) -> str:
    return "senim:cache:" + hashlib.sha256(key.encode()).hexdigest()


async def cache_get(key: str):
    return await store.get(_cache_key(key))


async def cache_put(key: str, value: Any, ttl: int = _CACHE_TTL) -> None:
    await store.put(_cache_key(key), value, ttl)


def cache_clear() -> None:
    store.clear_memory()


class HTTPError(Exception):
    def __init__(self, status: int, url: str):
        super().__init__(f"HTTP {status} for {url}")
        self.status = status
        self.url = url


async def get_json(url: str, params: dict | None = None, *, retries: int = 2, cache: bool = True,
                   ok_statuses: tuple[int, ...] = (200,), cache_ttl: int = _CACHE_TTL) -> tuple[int, Any]:
    """GET a JSON API. Returns (status, json_or_None). 404-style statuses are returned, not raised."""
    key = f"GET {url} {sorted((params or {}).items())}"
    if not cache:
        return await _fetch_json(key, url, params, retries, False, ok_statuses, cache_ttl)
    if (hit := await cache_get(key)) is not None:
        return hit[0], hit[1]
    # Single flight: identical requests made at the same moment (two claims about the same entity)
    # share one network call instead of each paying for it.
    slot = (id(asyncio.get_running_loop()), key)
    task = _inflight.get(slot)
    if task is None:
        task = asyncio.ensure_future(_fetch_json(key, url, params, retries, True, ok_statuses, cache_ttl))
        _inflight[slot] = task
        task.add_done_callback(lambda _: _inflight.pop(slot, None))
    return await asyncio.shield(task)


_inflight: dict[tuple[int, str], asyncio.Future] = {}


async def _fetch_json(key: str, url: str, params: dict | None, retries: int, cache: bool,
                      ok_statuses: tuple[int, ...], cache_ttl: int) -> tuple[int, Any]:
    delay = 1.0
    for attempt in range(retries + 1):
        try:
            r = await client().get(url, params=params)
        except httpx.HTTPError:
            if attempt == retries:
                raise
            await asyncio.sleep(delay)
            delay *= 2
            continue
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries:
            await asyncio.sleep(float(r.headers.get("Retry-After", delay)) if r.headers.get("Retry-After", "").isdigit() else delay)
            delay *= 2
            continue
        data = None
        if r.status_code in ok_statuses:
            try:
                data = r.json()
            except ValueError:
                data = None
        result = (r.status_code, data)
        if cache and r.status_code in ok_statuses + (404,):
            await cache_put(key, list(result), cache_ttl)
        return result
    raise HTTPError(0, url)


def _is_public_host(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return True


class UnsafeURL(Exception):
    pass


async def safe_fetch(url: str, max_bytes: int = 2_000_000, max_hops: int = 5) -> tuple[int, str, str]:
    """Fetch a user-supplied URL without letting it reach internal networks (basic SSRF guard).

    Every redirect hop is re-validated. Returns (status, final_url, text);
    status 0 means the host does not resolve or could not be reached.
    """
    current = url
    for _ in range(max_hops + 1):
        parsed = urlparse(current)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise UnsafeURL(current)
        try:
            await asyncio.to_thread(socket.getaddrinfo, parsed.hostname, None)
        except socket.gaierror:
            return 0, current, ""
        if not await asyncio.to_thread(_is_public_host, parsed.hostname):
            raise UnsafeURL(current)
        try:
            r = await client().send(client().build_request("GET", current), stream=True, follow_redirects=False)
        except httpx.HTTPError:
            return 0, current, ""
        try:
            if r.is_redirect:
                current = str(r.url.join(r.headers.get("location", "")))
                continue
            body = b""
            async for chunk in r.aiter_bytes():
                body += chunk
                if len(body) > max_bytes:
                    break
            return r.status_code, str(r.url), body.decode(r.encoding or "utf-8", errors="replace")
        except httpx.HTTPError:
            return 0, current, ""
        finally:
            await r.aclose()
    return 0, current, ""


_TAGS = None


def html_to_text(html: str) -> str:
    """Very small HTML→text converter (good enough for Quote-Lock on citation pages)."""
    import html as html_lib
    import re

    global _TAGS
    if _TAGS is None:
        _TAGS = (
            re.compile(r"<(script|style|noscript|svg)[^>]*>.*?</\1>", re.S | re.I),
            re.compile(r"<br\s*/?>|</p>|</div>|</li>|</h\d>", re.I),
            re.compile(r"<[^>]+>"),
            re.compile(r"[ \t]+"),
        )
    blocks, breaks, tags, spaces = _TAGS
    text = blocks.sub(" ", html)
    text = breaks.sub("\n", text)
    text = tags.sub(" ", text)
    text = html_lib.unescape(text)
    return spaces.sub(" ", text).strip()
