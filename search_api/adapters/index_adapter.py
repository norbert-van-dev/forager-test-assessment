import asyncio
import math
import random
import string
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import HttpUrl

from search_api.models.schemas import Facet, FacetCount, SearchResponse, SearchResult


class IndexAdapter(ABC):
    @abstractmethod
    async def search(
        self,
        query: str,
        page: int,
        size: int,
        sort: str = "relevance",
        language: Optional[str] = None,
        site: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
    ) -> SearchResponse:
        raise NotImplementedError


class MockIndexAdapter(IndexAdapter):
    async def search(
        self,
        query: str,
        page: int,
        size: int,
        sort: str = "relevance",
        language: Optional[str] = None,
        site: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
    ) -> SearchResponse:
        # Simulate async latency typical of shard fanout + aggregation
        await asyncio.sleep(0.005)
        total = 12345
        start_index = (page - 1) * size
        end_index = min(start_index + size, total)
        now = datetime.now(timezone.utc)

        def fake_url(i: int) -> str:
            base = site if site else "https://example.com"
            return f"{base}/doc/{i}-{self._rand_suffix(6)}"

        results: List[SearchResult] = []
        for i in range(start_index, end_index):
            results.append(
                SearchResult(
                    doc_id=f"doc-{i}",
                    url=fake_url(i),  # type: ignore[arg-type]
                    title=f"Result {i} for '{query}'",
                    snippet=f"... snippet for {query} (doc {i}) ...",
                    score=round(100.0 - math.log2(i + 2), 4),
                    language=language or "en",
                    last_crawled_at=now - timedelta(days=(i % 365)),
                    metadata={"site": site or "example.com", "rank_features": {"bm25": 12.3}},
                )
            )

        facets = [
            Facet(name="language", counts=[FacetCount(value="en", count=100), FacetCount(value="fr", count=50)])
        ]

        return SearchResponse(
            query=query,
            page=page,
            size=size,
            total=total,
            results=results,
            facets=facets,
        )

    def _rand_suffix(self, n: int) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


