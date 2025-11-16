from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, Response, status

from search_api.config.settings import RequestContext, get_settings
from search_api.services.rate_limit_service import RateLimitService


def get_context(
    request: Request,
    response: Response,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    x_request_id: Optional[str] = Header(default=None, alias="X-Request-Id"),
) -> RequestContext:
    settings = get_settings()
    # AuthN (API Key)
    if settings.api_keys:
        if not x_api_key or x_api_key not in settings.api_keys:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    # Rate limiting
    rl = RateLimitService()
    principal = x_api_key or "anonymous"
    decision = rl.check(key=principal, limit_per_minute=settings.rate_limit_per_minute)
    response.headers["X-RateLimit-Limit"] = str(decision.limit)
    response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
    if not decision.allowed:
        response.headers["Retry-After"] = str(decision.reset_seconds)
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    ctx = RequestContext(
        request_id=x_request_id or getattr(request.state, "request_id", None),
        api_key=x_api_key,
        user_id=None,
        tenant_id=None,
    )
    return ctx


