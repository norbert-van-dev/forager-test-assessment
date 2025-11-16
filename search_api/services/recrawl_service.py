import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from search_api.adapters.queue_adapter import InMemoryPriorityQueueAdapter, Priority, QueueAdapter
from search_api.config.settings import get_settings
from search_api.models.schemas import RecrawlGroupResponse, RecrawlJob, RecrawlStatusResponse


class RecrawlService:
    def __init__(self, queue_adapter: Optional[QueueAdapter] = None) -> None:
        self.queue: QueueAdapter = queue_adapter or InMemoryPriorityQueueAdapter()
        self.settings = get_settings()
        # In-memory job state, replace with durable store in production
        self._jobs: Dict[str, RecrawlJob] = {}
        # Idempotency registry: (tenant_id or "", key) -> job_group_id
        self._idem: Dict[Tuple[str, str], str] = {}

    async def enqueue_recrawl(
        self,
        urls: List[str],
        priority: Priority,
        reason: Optional[str],
        callback_url: Optional[str],
        tenant_id: Optional[str] = None,
        not_before: Optional[datetime] = None,
        idempotency_key: Optional[str] = None,
    ) -> RecrawlGroupResponse:
        now = datetime.now(timezone.utc)
        tenant = tenant_id or ""
        if idempotency_key:
            key = (tenant, idempotency_key)
            if key in self._idem:
                # Duplicate submission by design returns conflict by spec
                raise ValueError("duplicate_idempotency_key")
        job_group_id = str(uuid.uuid4())
        sla_deadline = now + timedelta(minutes=self.settings.recrawl_sla_minutes)

        job_ids = await self.queue.enqueue(
            urls=urls, priority=priority, group_id=job_group_id, tenant_id=tenant_id, not_before=not_before
        )

        jobs: List[RecrawlJob] = []
        for url, job_id in zip(urls, job_ids):
            job = RecrawlJob(
                job_id=job_id,
                url=url,  # type: ignore[arg-type]
                status="queued",
                priority=priority,
                created_at=now,
                updated_at=now,
                estimated_start_time=now + timedelta(minutes=3),
                sla_deadline=sla_deadline,
                result=None,
            )
            self._jobs[job_id] = job
            jobs.append(job)
        if idempotency_key:
            self._idem[(tenant, idempotency_key)] = job_group_id
        return RecrawlGroupResponse(job_group_id=job_group_id, jobs=jobs)

    async def get_status(self, job_id: str) -> Optional[RecrawlStatusResponse]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        return RecrawlStatusResponse(
            job_id=job.job_id,
            url=job.url,
            status=job.status,
            priority=job.priority,
            created_at=job.created_at,
            updated_at=job.updated_at,
            estimated_start_time=job.estimated_start_time,
            sla_deadline=job.sla_deadline,
            result=job.result,
        )

    # For demonstration: update job status (would be done by workers)
    async def mark_running(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "running"
            job.updated_at = datetime.now(timezone.utc)

    async def mark_finished(self, job_id: str, success: bool, result: Optional[dict] = None) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = "succeeded" if success else "failed"
            job.updated_at = datetime.now(timezone.utc)
            job.result = result


