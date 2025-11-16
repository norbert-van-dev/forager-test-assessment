from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from search_api.config.settings import RequestContext, get_settings
from search_api.models.schemas import ErrorResponse, SearchResponse
from search_api.services.search_service import SearchService
from search_api.dependencies.context import get_context

router = APIRouter(tags=["search"])


@router.get(
    "/search",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def search(
    q: str = Query(min_length=1, description="Query string"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=lambda: get_settings().default_page_size, ge=1),
    sort: str = Query(default="relevance", pattern="^(relevance|freshness)$"),
    lang: Optional[str] = Query(default=None, description="ISO language hint"),
    site: Optional[str] = Query(default=None, description="Restrict to site or host"),
    filters: Optional[str] = Query(default=None, description="JSON-encoded filters"),
    fields: Optional[str] = Query(default=None, description="Comma-separated fields to return"),
    ctx: RequestContext = Depends(get_context),
) -> SearchResponse:
    service = SearchService()
    parsed_filters: Optional[Dict[str, Any]] = None
    if filters:
        # Parsing omitted for brevity; validate shape before use
        parsed_filters = {}
    parsed_fields: Optional[List[str]] = [s.strip() for s in fields.split(",")] if fields else None
    response = await service.search(
        query=q,
        page=page,
        size=size,
        sort=sort,
        language=lang,
        site=site,
        filters=parsed_filters,
        fields=parsed_fields,
    )
    response.request_id = ctx.request_id
    return response


