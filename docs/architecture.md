Architecture and Scaling Plan
=============================

Traffic and throughput targets
------------------------------
- Crawl: ~4B pages/month ≈ 4e9 / (30×24×3600) ≈ ~1,543 pages/sec average; plan for 3–5× spikes.
- Queries: ~100B/month ≈ 1e11 / (30×24×3600) ≈ ~38,580 QPS average; plan for 5–10× peaks.
- On‑demand re‑crawl: 1‑hour SLA with bursty submission patterns; reserve capacity and use priority queues.

Core services
-------------
1) API Gateway and Edge
   - Concerns: TLS termination, auth (API keys/OAuth2), WAF, DDoS protection, rate limiting, request shaping, CDN caching for static assets and cacheable search results (e.g., popular queries).
   - Scaling: Managed gateway with autoscaling and Anycast IPs; multi‑region; rollouts via canaries.

2) Search API Cluster (Stateless)
   - Concerns: Request validation, authentication, rate limiting and quotas, query parsing, query planning, and aggregation. No per‑request durable state.
   - Scaling: Horizontal pod autoscaling based on CPU/RPS/p95 latency; separate read/write pools; safe deployments with blue/green.

3) Search Serving Tier (Sharded + Replicated)
   - Lexical (Inverted) Index Shards: Token → postings lists; optimized for BM25/lexical retrieval; shard by term or document ranges; replicate for availability. Keep hot postings in RAM with compressed blocks.
   - Vector (ANN) Index Shards: Encode doc embeddings; ANN graphs (HNSW/IVF‑PQ/ScaNN) per shard; approximate search with multi‑probe; replicate for availability; re‑rank lexically or blend.
   - Query Router: Maintains shard map and replicas; load‑aware routing; retries and circuit breaking; A/B routing for model/feature experiments.
   - Aggregator: Merges shard results, applies business rules, diverse results, snippets via precomputed fields, fetches doc metadata when needed.
   - Scaling: Add shards for throughput; add replicas for availability; deploy per region; keep tight SLAs with admission control and backpressure.

4) Result Caching
   - Layering: CDN/Edge → gateway cache → API in‑mem cache → shard query node cache (e.g., query → candidate set; doc features).
   - TTLs: Short TTLs (seconds–minutes) for hot queries; explicit cache bypass for personalized or low‑latency freshness needs.
   - Scaling: Redis/Memcached clusters with partitioning and replication.

5) Crawl & Re‑crawl Pipeline
   - Priority Queue: Durable, partitioned queue (Kafka/Redis/RabbitMQ) with priority for SLA jobs; idempotent job keys; DLQ for poison jobs.
   - Scheduler: Enforces domain politeness (robots, rate limit per host/IP), budget/quotas, and reserved capacity for SLA jobs. Maintains URL frontier.
   - Fetchers: Distributed fetch pool; HTTP/2/3, connection reuse, TLS session resumption; DNS cache; backoff on errors; content compression.
   - Parse & Extract: Boilerplate removal; HTML to text; language detection; link extraction; canonicalization; structured data extraction.
   - Deduplication: Content hashing (simhash, shingling) to avoid redundant indexing; near‑dup detection.
   - Persistence: Raw page blobs in object storage; metadata in KV/column store; link graph in column family store.
   - Scaling: Auto‑scale fetchers by queue depth and time‑to‑SLA; allocate quota to SLA class to guarantee 1‑hour completion; track per‑domain budgets to avoid overload.

6) Indexing Pipeline
   - Feature extraction and normalization; stopwords, stemming/lemmatization; tokenization with Unicode rules.
   - Reverse index build with incremental segments; periodic merges to reduce fragmentation. Push new segments hot to serving shards.
   - Vector build: Document embedding with offline/nearline models; ANN graph updates; segmentized to allow fast swaps.
   - Scaling: Parallel batch jobs with streaming ingestion; MapReduce‑style jobs for heavy merges; bounded memory; backpressure when shards lag.

7) Data Stores
   - Doc Store: Object storage (S3/GCS/Azure) for raw/processed content; CDN for hot blobs.
   - Metadata Store: KV or wide column store (e.g., DynamoDB/Bigtable/Cassandra/RocksDB) for doc metadata and features.
   - Link Graph: Column family store with adjacency lists and per‑edge weights; periodic computations (PageRank/cheirank/etc.).
   - Scaling: Partitioning by docID/host; multi‑AZ replication; read replicas for query tier.

8) Observability & Control
   - Metrics (RED/USE), tracing, central logs. SLOs: search p95 latency, crawl SLA compliance, index freshness.
   - Admin console: rollout control, A/B experiments, feature flags, emergency kill‑switches.

Meeting the numbers
-------------------
- Crawling 4B/month: Average ~1.5K pages/sec. With politeness and retries, provision for 5–10K pages/sec sustained capacity. Autoscale fetchers on queue depth and SLA backlog.
- Serving 100B/month: Average ~38.5K QPS. With p95 < 150ms target, budget latency by stage (gateway <10ms, API <10ms, routing <10ms, shard <50–80ms, aggregation <30ms, network <20ms). Scale shards horizontally and cache aggressively.
- Re‑crawl 1‑hour SLA: Reserve capacity in queue and fetchers, priority scheduling, explicit SLAs per class (e.g., P0). Preemption/backfill logic when under‑utilized.

Failure modes and resiliency
----------------------------
- Multi‑AZ deployments per region, cross‑region replicas for search serving and data stores. Read‑only failover for severe incidents.
- Circuit breakers and retries at query router. Bulkhead isolation between crawl and search paths.
- DLQ and reprocessing for crawl failures. Idempotent job submission keyed by URL/tenant/time window.

Security
--------
- API key or OAuth2 for clients; WAF and bot controls. Encryption in transit and at rest. Secrets in a vault. Least privilege for services.

Cost awareness
--------------
- Cache first; reduce shard pressure. Compress postings; quantize vectors where possible. Batch background tasks; use spot for non‑SLA workloads. Right‑size replicas in off‑peak with autoscaling.


