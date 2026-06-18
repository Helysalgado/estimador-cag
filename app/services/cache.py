from __future__ import annotations

import hashlib
import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError


def make_key(
    system_prompt: str,
    user_message: str,
    model: str,
    max_tokens: int,
    thinking_budget: int | None,
) -> str:
    """Build a deterministic, versioned cache key for estimation requests."""
    payload = json.dumps(
        {
            "system_prompt": system_prompt,
            "user_message": user_message,
            "model": model,
            "max_tokens": max_tokens,
            "thinking_budget": thinking_budget,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"estimation:v1:{digest}"


class RedisCache:
    """Redis-backed cache with JSON payload serialization."""

    def __init__(self, *, redis_url: str, default_ttl_seconds: int = 86400) -> None:
        """Initialize a Redis cache client from URL and default TTL."""
        self.default_ttl_seconds = default_ttl_seconds
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def get(self, key: str) -> Any | None:
        """Return a cached JSON value by key, or None when missing/unavailable."""
        try:
            raw = self._client.get(key)
        except RedisError:
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store value with TTL (seconds), using JSON serialization."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        payload = json.dumps(value, ensure_ascii=False)
        try:
            self._client.set(name=key, value=payload, ex=ttl)
        except RedisError:
            return


def build_cache(redis_url: str, cache_ttl_seconds: int) -> RedisCache:
    """Factory function to create the app cache backend."""
    return RedisCache(redis_url=redis_url, default_ttl_seconds=cache_ttl_seconds)
