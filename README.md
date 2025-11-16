Scalable Search Engine System
=============================

This repository contains a high-level yet production-lean scaffold of a web‑scale search engine system capable of:
- Crawling ~4B pages/month (~1.5K pages/sec average)
- Serving ~100B queries/month (~38.5K QPS average; plan for 5–10× peak)
- Handling on-demand re-crawl requests with a 1-hour SLA

What’s included
---------------
- docs/system-diagram.md: High-level architecture diagram (Mermaid) and component map
- docs/architecture.md: Detailed service descriptions and scaling strategies
- docs/api-spec.md: REST API specification for search and re-crawl
- search_api/: FastAPI app demonstrating routes, services, adapters, tasks
- tests/: Representative tests for routes/services
- requirements.txt: Minimal dependencies

Quick start (local)
-------------------
1) Create and activate a virtual environment (recommended)
   - Windows PowerShell:
     - python -m venv .venv
     - .\\.venv\\Scripts\\Activate.ps1
2) Install dependencies:
   - pip install -r requirements.txt
3) Run the API (dev):
   - uvicorn search_api.main:app --reload --host 0.0.0.0 --port 8000
4) Explore auto docs:
   - Open http://localhost:8000/docs
5) Run tests:
   - pytest -q
6) Docker (optional):
   - Build: docker build -t scalable-search-api:local .
   - Run: docker run --rm -p 8000:8000 scalable-search-api:local
7) Docker Compose:
   - docker compose up --build -d
   - Open http://localhost:8000/docs

Repository structure
--------------------
- docs/
  - system-diagram.md
  - architecture.md
  - api-spec.md
- search_api/
  - __init__.py
  - main.py
  - config/settings.py
  - middleware/
    - request_id.py
    - errors.py
  - dependencies/context.py
  - models/schemas.py
  - routes/search.py
  - routes/recrawl.py
  - services/search_service.py
  - services/recrawl_service.py
  - services/rate_limit_service.py
  - adapters/index_adapter.py
  - adapters/queue_adapter.py
  - tasks/worker.py
- tests/
  - test_routes.py
  - test_services.py
  - test_rate_limit.py
- requirements.txt

Notes on scalability
--------------------
This scaffold emphasizes separation of concerns, async IO, and adapter-based design to enable:
- Horizontal scaling of stateless API workers behind an API gateway
- Sharded/replicated indexing services (lexical and vector)
- Tiered caching (client, CDN/edge, gateway, per-shard)
- Durable, prioritized job queues to enforce the 1-hour SLA on re-crawls
- Observability hooks (metrics/tracing/logging) through clear seams (omitted here for brevity)

Authentication and rate limiting
--------------------------------
- API key support via `X-API-Key` (disabled by default; set `SEARCH_API_KEYS` env with comma-separated keys if needed).
- Request ID middleware attaches/propagates `X-Request-Id`.
- In-memory token-bucket rate limiter (replace with Redis/gateway in production). Headers:
  - `X-RateLimit-Limit`, `X-RateLimit-Remaining`; on 429 includes `Retry-After`.

Idempotency for re-crawl
------------------------
- `POST /v1/recrawl` accepts `Idempotency-Key` header.
- Subsequent requests with the same key return HTTP 409 per API spec (demonstrates conflict handling).

Author - Norbert Van