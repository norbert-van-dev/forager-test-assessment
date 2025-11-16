from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_name: str = "Scalable Search API"
    api_version: str = "1.0.0"
    api_keys: List[str] = []
    default_page_size: int = 10
    max_page_size: int = 100
    rate_limit_per_minute: int = 60000
    enable_vector_blend: bool = True
    recrawl_sla_minutes: int = 60

    class Config:
        env_prefix = "SEARCH_"
        extra = "ignore"


class RequestContext(BaseModel):
    request_id: Optional[str] = None
    api_key: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


