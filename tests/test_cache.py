import pytest

from search_api.services.search_service import SearchService
from search_api.adapters.index_adapter import IndexAdapter
from search_api.adapters.cache_adapter import InMemoryCacheAdapter
from search_api.models.schemas import SearchResponse


class CountingIndex(IndexAdapter):
    def __init__(self) -> None:
        self.calls = 0

    async def search(self, **kwargs) -> SearchResponse:  # type: ignore[override]
        from search_api.adapters.index_adapter import MockIndexAdapter

        self.calls += 1
        return await MockIndexAdapter().search(**kwargs)


@pytest.mark.anyio
async def test_search_cache_hits():
    idx = CountingIndex()
    cache = InMemoryCacheAdapter()
    svc = SearchService(index_adapter=idx, cache_adapter=cache)
    r1 = await svc.search(query="cache me", page=1, size=5)
    r2 = await svc.search(query="cache me", page=1, size=5)
    assert idx.calls == 1  # second call served from cache
    assert r1.total == r2.total


