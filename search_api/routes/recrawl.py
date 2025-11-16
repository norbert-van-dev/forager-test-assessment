from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status

from search_api.config.settings import RequestContext, get_settings
from search_api.models.schemas import ErrorResponse, RecrawlGroupResponse, RecrawlRequest, RecrawlStatusResponse
from search_api.services.recrawl_service import RecrawlService
from search_api.dependencies.context import get_context

router = APIRouter(tags=["recrawl"])


@router.post(
    "/recrawl",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=RecrawlGroupResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def request_recrawl(
    payload: RecrawlRequest,
    ctx: RequestContext = Depends(get_context),
) -> RecrawlGroupResponse:
    if len(payload.urls) > 100:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Too many URLs")
    service = RecrawlService()
    now = datetime.now(timezone.utc)
    # Example: delay low-priority jobs slightly if needed
    not_before = None
    response = await service.enqueue_recrawl(
        urls=[str(u) for u in payload.urls],
        priority=payload.priority,
        reason=payload.reason,
        callback_url=str(payload.callback_url) if payload.callback_url else None,
        tenant_id=ctx.tenant_id,
        not_before=not_before,
    )
    response.request_id = ctx.request_id
    return response


@router.get(
    "/recrawl/{job_id}",
    response_model=RecrawlStatusResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
async def get_recrawl_status(
    job_id: str = Path(..., min_length=8),
    ctx: RequestContext = Depends(get_context),
) -> RecrawlStatusResponse:
    service = RecrawlService()
    status_resp = await service.get_status(job_id)
    if not status_resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    status_resp.request_id = ctx.request_id
    return status_resp


