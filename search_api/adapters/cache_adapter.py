import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


class CacheAdapter(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        raise NotImplementedError


@dataclass
class _Entry:
    value: Any
    expires_at: float


class InMemoryCacheAdapter(CacheAdapter):
    def __init__(self) -> None:
        self._store: Dict[str, _Entry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if entry.expires_at < time.time():
                self._store.pop(key, None)
                return None
            return entry.value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        async with self._lock:
            self._store[key] = _Entry(value=value, expires_at=time.time() + max(0, ttl_seconds))


