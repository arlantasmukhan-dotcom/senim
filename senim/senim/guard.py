"""Abuse protection: every check costs real money (dozens of paid model calls), so cap checks per
client IP per hour and the server's total model spend per day. Counters live in the shared store."""

from __future__ import annotations

import ipaddress
import time
from datetime import datetime, timezone

from . import store
from .config import settings

_HOUR = 3600
_DAY = 86400


def _budget_key() -> str:
    return "senim:spend:" + datetime.now(timezone.utc).strftime("%Y-%m-%d")


def is_local(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False


async def admit(client_ip: str) -> str | None:
    """None if the check may run, else the error code to show the user."""
    if settings.daily_budget_usd > 0 and await store.read_counter(_budget_key()) >= settings.daily_budget_usd:
        return "budget_exceeded"
    if settings.rate_limit_per_hour > 0 and client_ip and not is_local(client_ip):
        window = int(time.time() // _HOUR)
        count = await store.incr(f"senim:rate:{client_ip}:{window}", 1, _HOUR)
        if count > settings.rate_limit_per_hour:
            return "rate_limited"
    return None


async def record_spend(usd: float) -> None:
    if usd > 0:
        await store.incr(_budget_key(), usd, _DAY + _HOUR)
