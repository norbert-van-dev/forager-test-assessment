API Specification (v1)
======================

Authentication
--------------
- API keys via `X-API-Key` header or OAuth2 Bearer token via `Authorization: Bearer <token>`.
- All requests must be over HTTPS.

Rate limiting
-------------
- Enforced at gateway and application layer.
- Responses may include:
  - `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
  - On 429, include `Retry-After` (seconds) and an error body (see Errors).

Pagination
----------
- Cursor-based or offset-based pagination depending on endpoint.
- For search: offset-based with `page` and `size` (default `page=1`, `size=10`, max `size=100`).

Errors
------
Standard error response:
```json
{
  "error": {
    "code": "string",
    "message": "human readable message",
    "details": { "optional": "context" },
    "request_id": "uuid"
  }
}
```
Common HTTP status codes: 200, 202, 400, 401, 403, 404, 409, 422, 429, 500, 503.

Versioning
----------
- Prefix routes with `/v1`. Backwards-compatible responses favored; breaking changes require new version.

Endpoints
---------

1) Search indexed pages
-----------------------
GET `/v1/search`

Query parameters:
- `q` (required, string): Query string.
- `page` (optional, int, default 1, min 1): Page number.
- `size` (optional, int, default 10, max 100): Page size.
- `sort` (optional, enum: `relevance`|`freshness`, default `relevance`)
- `lang` (optional, string): ISO language code hint.
- `site` (optional, string): Restrict to site or host (e.g., `site:example.com`).
- `filters` (optional, string): JSON-encoded key/value filters.
- `fields` (optional, string): Comma-separated fields to return (e.g., `title,url,snippet`).

Response: 200 OK
```json
{
  "query": "string",
  "page": 1,
  "size": 10,
  "total": 12345,
  "results": [
    {
      "doc_id": "string",
      "url": "https://example.com/a",
      "title": "Example Title",
      "snippet": "Result snippet with highlights...",
      "score": 12.34,
      "language": "en",
      "last_crawled_at": "2025-11-16T12:34:56Z",
      "metadata": { "optional": "fields" }
    }
  ],
  "facets": [
    { "name": "language", "counts": [ { "value": "en", "count": 100 }, { "value": "fr", "count": 50 } ] }
  ],
  "request_id": "uuid"
}
```
Errors: 400 (missing/invalid `q`), 401, 429, 500.

2) Request re-crawl (1-hour SLA)
--------------------------------
POST `/v1/recrawl`

Headers:
- Optional idempotency: `Idempotency-Key: <uuid>`

Body:
```json
{
  "urls": ["https://example.com/a", "https://example.com/b"],
  "priority": "normal",  // one of: "low" | "normal" | "high" | "critical"
  "reason": "user_requested_update",
  "callback_url": "https://client.example.com/hooks/crawl-updated"
}
```
Constraints:
- Max 100 URLs per request (batch).

Response: 202 Accepted
```json
{
  "job_group_id": "uuid",
  "jobs": [
    {
      "job_id": "uuid",
      "url": "https://example.com/a",
      "status": "queued",
      "priority": "normal",
      "sla_deadline": "2025-11-16T13:34:56Z",
      "estimated_start_time": "2025-11-16T12:40:00Z"
    }
  ],
  "request_id": "uuid"
}
```
Errors: 400 (invalid URL), 401, 409 (duplicate with same idempotency key), 413 (too many URLs), 422 (validation), 429, 500.

3) Get re-crawl job status
--------------------------
GET `/v1/recrawl/{job_id}`

Response: 200 OK
```json
{
  "job_id": "uuid",
  "url": "https://example.com/a",
  "status": "queued",  // queued | running | succeeded | failed | expired
  "priority": "normal",
  "created_at": "2025-11-16T12:34:56Z",
  "updated_at": "2025-11-16T12:36:00Z",
  "estimated_start_time": "2025-11-16T12:40:00Z",
  "sla_deadline": "2025-11-16T13:34:56Z",
  "result": {
    "last_crawled_at": "2025-11-16T12:50:00Z",
    "doc_id": "string",
    "error": null
  },
  "request_id": "uuid"
}
```
Errors: 401, 404 (job not found), 429, 500.

HTTP semantics
--------------
- 200 OK for successful reads; 202 Accepted for async job creation.
- Use `Cache-Control` judiciously on GET `/v1/search` for hot queries when safe.
- Idempotency: `POST /v1/recrawl` accepts `Idempotency-Key` to avoid duplicate batches.
- Provide `X-Request-Id` in responses for traceability; accept client `X-Request-Id` if provided.


