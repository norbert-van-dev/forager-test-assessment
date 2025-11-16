import hashlib
import json
from typing import Any, Dict, List, Optional

from search_api.adapters.index_adapter import IndexAdapter, MockIndexAdapter
from search_api.adapters.cache_adapter import CacheAdapter, InMemoryCacheAdapter
from search_api.config.settings import get_settings
from search_api.models.schemas import SearchResponse


class SearchService:
    def __init__(
        self,
        index_adapter: Optional[IndexAdapter] = None,
        cache_adapter: Optional[CacheAdapter] = None,
    ) -> None:
        # Injected adapter allows swapping real index in production
        self.index_adapter = index_adapter or MockIndexAdapter()
        self.settings = get_settings()
        self.cache = cache_adapter or InMemoryCacheAdapter()

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
        bounded_size = min(max(size, 1), self.settings.max_page_size)
        bounded_page = max(page, 1)

        cache_key = self._make_cache_key(
            query=query,
            page=bounded_page,
            size=bounded_size,
            sort=sort,
            language=language,
            site=site,
            filters=filters,
            fields=fields,
        )
        if self.settings.enable_result_cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        response = await self.index_adapter.search(
            query=query,
            page=bounded_page,
            size=bounded_size,
            sort=sort,
            language=language,
            site=site,
            filters=filters,
            fields=fields,
        )
        if self.settings.enable_result_cache:
            await self.cache.set(cache_key, response, ttl_seconds=self.settings.result_cache_ttl_seconds)
        return response

    def _make_cache_key(
        self,
        query: str,
        page: int,
        size: int,
        sort: str,
        language: Optional[str],
        site: Optional[str],
        filters: Optional[Dict[str, Any]],
        fields: Optional[List[str]],
    ) -> str:
        payload = {
            "q": query,
            "p": page,
            "s": size,
            "o": sort,
            "l": language,
            "site": site,
            "f": filters or {},
            "fields": fields or [],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


