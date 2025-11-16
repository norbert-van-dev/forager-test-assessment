from typing import Any, Dict, List, Optional

from search_api.adapters.index_adapter import IndexAdapter, MockIndexAdapter
from search_api.config.settings import get_settings
from search_api.models.schemas import SearchResponse


class SearchService:
    def __init__(self, index_adapter: Optional[IndexAdapter] = None) -> None:
        # Injected adapter allows swapping real index in production
        self.index_adapter = index_adapter or MockIndexAdapter()
        self.settings = get_settings()

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
        return response


