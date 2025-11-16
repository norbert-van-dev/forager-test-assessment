import anyio
import pytest

from search_api.services.search_service import SearchService


@pytest.mark.anyio
async def test_search_service_returns_results():
    svc = SearchService()
    resp = await svc.search(query="test", page=1, size=5)
    assert resp.query == "test"
    assert resp.page == 1
    assert resp.size == 5
    assert len(resp.results) == 5
    assert resp.total >= 5


