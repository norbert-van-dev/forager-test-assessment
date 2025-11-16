from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, HttpUrl


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class FacetCount(BaseModel):
    value: str
    count: int


class Facet(BaseModel):
    name: str
    counts: List[FacetCount]


class SearchResult(BaseModel):
    doc_id: str
    url: HttpUrl
    title: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None
    language: Optional[str] = None
    last_crawled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    page: int
    size: int
    total: int
    results: List[SearchResult]
    facets: Optional[List[Facet]] = None
    request_id: Optional[str] = None


Priority = Literal["low", "normal", "high", "critical"]
JobStatus = Literal["queued", "running", "succeeded", "failed", "expired"]


class RecrawlRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., min_length=1, max_length=100)
    priority: Priority = "normal"
    reason: Optional[str] = None
    callback_url: Optional[HttpUrl] = None


class RecrawlJob(BaseModel):
    job_id: str
    url: HttpUrl
    status: JobStatus = "queued"
    priority: Priority = "normal"
    created_at: datetime
    updated_at: datetime
    estimated_start_time: Optional[datetime] = None
    sla_deadline: datetime
    result: Optional[Dict[str, Any]] = None


class RecrawlGroupResponse(BaseModel):
    job_group_id: str
    jobs: List[RecrawlJob]
    request_id: Optional[str] = None


class RecrawlStatusResponse(BaseModel):
    job_id: str
    url: HttpUrl
    status: JobStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    estimated_start_time: Optional[datetime] = None
    sla_deadline: datetime
    result: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


