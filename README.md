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
  - models/schemas.py
  - routes/search.py
  - routes/recrawl.py
  - services/search_service.py
  - services/recrawl_service.py
  - adapters/index_adapter.py
  - adapters/queue_adapter.py
  - tasks/worker.py
- tests/
  - test_routes.py
  - test_services.py
- requirements.txt

Notes on scalability
--------------------
This scaffold emphasizes separation of concerns, async IO, and adapter-based design to enable:
- Horizontal scaling of stateless API workers behind an API gateway
- Sharded/replicated indexing services (lexical and vector)
- Tiered caching (client, CDN/edge, gateway, per-shard)
- Durable, prioritized job queues to enforce the 1-hour SLA on re-crawls
- Observability hooks (metrics/tracing/logging) through clear seams (omitted here for brevity)

Pushing to GitHub (reminder)
----------------------------
When you’re ready, create your first commit and push incrementally:
1) Stage and commit:
   - git add .
   - git commit -m "Initialize project: docs, API spec, FastAPI scaffold, tests"
2) Create GitHub repo (if not yet made) and set remote:
   - git remote add origin <your_repo_url>
3) Push:
   - git push -u origin main

Make small, logical commits as you iterate. For example:
- docs: add scaling plan details
- api: add rate limiting dependency
- services: plug in real index adapter
- tests: add load-shape tests


