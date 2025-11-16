import asyncio
from datetime import datetime, timezone
from typing import Optional

from search_api.adapters.queue_adapter import InMemoryPriorityQueueAdapter, Priority
from search_api.services.recrawl_service import RecrawlService


async def recrawl_worker(queue: InMemoryPriorityQueueAdapter, service: RecrawlService, capacity: int = 100) -> None:
    """
    A representative async worker consuming recrawl jobs and marking them complete.
    In production, this would fetch, parse, dedupe, and trigger index updates.
    """
    semaphore = asyncio.Semaphore(capacity)
    async for job_id, url, priority in queue.consume():
        await semaphore.acquire()
        asyncio.create_task(_process_job(semaphore, service, job_id, url, priority))


async def _process_job(
    semaphore: asyncio.Semaphore, service: RecrawlService, job_id: str, url: str, priority: Priority
) -> None:
    try:
        await service.mark_running(job_id)
        # Simulate network + processing time; SLA-aware prioritization can modulate this
        await asyncio.sleep(0.1)
        # Mark success and attach a simple result payload
        await service.mark_finished(
            job_id, success=True, result={"last_crawled_at": datetime.now(timezone.utc).isoformat()}
        )
    finally:
        semaphore.release()


async def main() -> None:
    queue = InMemoryPriorityQueueAdapter()
    service = RecrawlService(queue_adapter=queue)
    await recrawl_worker(queue, service, capacity=100)


if __name__ == "__main__":
    asyncio.run(main())


