import asyncio
import heapq
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator, Dict, List, Literal, Optional, Tuple

Priority = Literal["low", "normal", "high", "critical"]


@dataclass(order=True)
class _PrioritizedItem:
    sort_index: int
    enqueue_ts: float
    job_id: str = field(compare=False)
    url: str = field(compare=False)
    priority: Priority = field(compare=False)
    group_id: Optional[str] = field(compare=False, default=None)
    tenant_id: Optional[str] = field(compare=False, default=None)
    not_before: Optional[datetime] = field(compare=False, default=None)


class QueueAdapter(ABC):
    @abstractmethod
    async def enqueue(
        self,
        urls: List[str],
        priority: Priority,
        group_id: str,
        tenant_id: Optional[str] = None,
        not_before: Optional[datetime] = None,
    ) -> List[str]:
        raise NotImplementedError

    @abstractmethod
    async def consume(self) -> AsyncIterator[Tuple[str, str, Priority]]:
        raise NotImplementedError


class InMemoryPriorityQueueAdapter(QueueAdapter):
    def __init__(self) -> None:
        self._heap: List[_PrioritizedItem] = []
        self._cv = asyncio.Condition()
        self._closed = False

    async def enqueue(
        self,
        urls: List[str],
        priority: Priority,
        group_id: str,
        tenant_id: Optional[str] = None,
        not_before: Optional[datetime] = None,
    ) -> List[str]:
        job_ids: List[str] = []
        priority_rank = self._priority_to_rank(priority)
        now = time.time()
        async with self._cv:
            for url in urls:
                job_id = str(uuid.uuid4())
                job_ids.append(job_id)
                item = _PrioritizedItem(
                    sort_index=priority_rank,
                    enqueue_ts=now,
                    job_id=job_id,
                    url=url,
                    priority=priority,
                    group_id=group_id,
                    tenant_id=tenant_id,
                    not_before=not_before,
                )
                heapq.heappush(self._heap, item)
            self._cv.notify_all()
        return job_ids

    async def consume(self) -> AsyncIterator[Tuple[str, str, Priority]]:
        while not self._closed:
            async with self._cv:
                while not self._heap:
                    await self._cv.wait()
                item = heapq.heappop(self._heap)
            if item.not_before and datetime.now(timezone.utc) < item.not_before:
                # Not ready yet; re-enqueue with a small delay
                await asyncio.sleep(0.1)
                async with self._cv:
                    heapq.heappush(self._heap, item)
                    continue
            yield (item.job_id, item.url, item.priority)

    def close(self) -> None:
        self._closed = True
        # Wake consumers
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(lambda: None)
        except RuntimeError:
            pass

    def _priority_to_rank(self, p: Priority) -> int:
        return {"critical": 0, "high": 1, "normal": 2, "low": 3}[p]


