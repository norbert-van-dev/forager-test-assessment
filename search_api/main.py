from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from search_api.config.settings import get_settings
from search_api.routes.search import router as search_router
from search_api.routes.recrawl import router as recrawl_router
from search_api.middleware.request_id import RequestIdMiddleware
from search_api.middleware.errors import add_exception_handlers


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.api_name,
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIdMiddleware)
    add_exception_handlers(app)

    @app.get("/healthz", tags=["health"])
    async def health() -> dict:
        return {"status": "ok"}

    app.include_router(search_router, prefix="/v1")
    app.include_router(recrawl_router, prefix="/v1")
    return app


app = create_app()


