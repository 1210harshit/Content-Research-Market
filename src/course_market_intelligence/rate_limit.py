"""Simple per-domain rate limiting and a guarded HTTP client.

Enforces a minimum interval between requests to the same host, request
timeouts, and a bounded number of retries with exponential backoff. No proxy
rotation, no fingerprint spoofing — this is a polite client, not an evasive one.
"""

from __future__ import annotations

import asyncio
import time
from urllib.parse import urlparse

import httpx

from .config import get_settings


class RateLimiter:
    """Token-bucket-ish minimum-interval limiter, keyed by host."""

    def __init__(self, default_interval: float | None = None) -> None:
        self.default_interval = (
            default_interval
            if default_interval is not None
            else get_settings().default_rate_limit_seconds
        )
        self._last: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _host(self, url: str) -> str:
        return urlparse(url).netloc or url

    async def acquire(self, url: str, interval: float | None = None) -> None:
        host = self._host(url)
        wait = interval if interval is not None else self.default_interval
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            last = self._last.get(host, 0.0)
            delta = now - last
            if delta < wait:
                await asyncio.sleep(wait - delta)
            self._last[host] = time.monotonic()


_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _limiter


async def guarded_get(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    auth: tuple[str, str] | None = None,
    interval: float | None = None,
) -> httpx.Response:
    """GET with rate limit, timeout and bounded retries (exponential backoff)."""
    settings = get_settings()
    await _limiter.acquire(url, interval)
    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        for attempt in range(settings.max_retries):
            try:
                resp = await client.get(url, params=params, headers=headers, auth=auth)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError(
                        f"retryable status {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                return resp
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == settings.max_retries - 1:
                    break
                await asyncio.sleep(2 ** attempt)
    assert last_exc is not None
    raise last_exc
