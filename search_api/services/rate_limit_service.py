import time
from dataclasses import dataclass
from threading import Lock
from typing import Dict, Optional, Tuple

from search_api.config.settings import get_settings


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_seconds: int


class TokenBucket:
    def __init__(self, capacity: int, refill_per_sec: float) -> None:
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = capacity
        self.last = time.monotonic()
        self.lock = Lock()

    def try_take(self, n: int = 1) -> Tuple[bool, int, int]:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last
            self.last = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
            allowed = self.tokens >= n
            if allowed:
                self.tokens -= n
            remaining = max(0, int(self.tokens))
            reset_seconds = 0 if self.tokens >= 1 else int((1 - self.tokens) / self.refill_per_sec) + 1
            return allowed, remaining, reset_seconds


class RateLimitService:
    """
    Simple in-memory token-bucket rate limiter keyed by api_key or tenant.
    Replace with Redis/Elasticache or gateway-based limiting for production.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = Lock()

    def check(self, key: str, limit_per_minute: Optional[int] = None) -> RateLimitDecision:
        limit = limit_per_minute or self.settings.rate_limit_per_minute
        refill = limit / 60.0
        with self._lock:
            bucket = self._buckets.get(key)
            if not bucket:
                bucket = TokenBucket(capacity=limit, refill_per_sec=refill)
                self._buckets[key] = bucket
        allowed, remaining, reset_seconds = bucket.try_take(1)
        return RateLimitDecision(allowed=allowed, limit=limit, remaining=remaining, reset_seconds=reset_seconds)


