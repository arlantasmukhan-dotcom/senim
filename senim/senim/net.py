"""Shared HTTP layer: one async client, a small TTL cache, retries, and an SSRF-safe fetch."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import settings

_client: httpx.AsyncClient | None = None
_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 6 * 3600
_CACHE_MAX = 2000


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


def cache_get(key: str):
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < _CACHE_TTL:
        return hit[1]
    return None


def cache_put(key: str, value: Any) -> None:
    if len(_cache) >= _CACHE_MAX:
        for k in sorted(_cache, key=lambda k: _cache[k][0])[: _CACHE_MAX // 10]:
            _cache.pop(k, None)
    _cache[key] = (time.time(), value)


def cache_clear() -> None:
    _cache.clear()


class HTTPError(Exception):
    def __init__(self, status: int, url: str):
        super().__init__(f"HTTP {status} for {url}")
        self.status = status
        self.url = url


async def get_json(url: str, params: dict | None = None, *, retries: int = 2, cache: bool = True,
                   ok_statuses: tuple[int, ...] = (200,)) -> tuple[int, Any]:
    """GET a JSON API. Returns (status, json_or_None). 404-style statuses are returned, not raised."""
    key = f"GET {url} {sorted((params or {}).items())}"
    if cache and (hit := cache_get(key)) is not None:
        return hit
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
            cache_put(key, result)
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
