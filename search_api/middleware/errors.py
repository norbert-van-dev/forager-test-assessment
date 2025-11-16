from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from search_api.models.schemas import ErrorBody, ErrorResponse


def add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:  # type: ignore[override]
        request_id: Optional[str] = getattr(request.state, "request_id", None)
        body = ErrorResponse(
            error=ErrorBody(
                code=str(exc.status_code),
                message=exc.detail if isinstance(exc.detail, str) else "HTTP error",
                details=None,
                request_id=request_id,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
        request_id: Optional[str] = getattr(request.state, "request_id", None)
        body = ErrorResponse(
            error=ErrorBody(code="internal_error", message="Unexpected error", details=None, request_id=request_id)
        )
        return JSONResponse(status_code=500, content=body.model_dump())


