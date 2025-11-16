System Architecture Diagram
===========================

The diagram below shows the high-level components for crawling, indexing, and serving at web scale, including on‑demand re‑crawl with a 1‑hour SLA.

```mermaid
flowchart LR
    %% ========== ENTRY/GATEWAY ==========
    subgraph EDGE["Edge / Gateway Layer"]
      CDN[CDN/Edge Cache]
      APIGW[API Gateway<br/>Auth, Rate Limit, WAF]
    end
    CDN --> APIGW

    %% ========== SEARCH READ PATH ==========
    subgraph API["Search API Cluster (Stateless, Autoscaled)"]
      SR[Search Router<br/>(Shard map, A/B, canary)]
      RC[Result Cache<br/>(Redis/Memcached)]
      RL[Rate Limit & Quotas]
    end
    APIGW --> RL --> SR
    SR -->|cache hit| RC
    RC -->|hit| APIGW
    SR -->|cache miss| QP[Query Planner]
    QP --> RANK[Ranking & Blending]
    RANK --> AGG[Aggregator]

    subgraph SVC["Search Serving Tier (Sharded + Replicated)"]
      direction LR
      L0[L0 Shard Router]
      subgraph LEX["Lexical Index Shards"]
        direction TB
        L1[Shard A: Inverted Index]
        L2[Shard B: Inverted Index]
        L3[Shard N: Inverted Index]
      end
      subgraph VEC["Vector Index Shards (ANN)"]
        direction TB
        V1[Shard A: ANN Graph]
        V2[Shard B: ANN Graph]
        V3[Shard N: ANN Graph]
      end
    end
    QP --> L0
    L0 --> L1 & L2 & L3
    L0 --> V1 & V2 & V3
    L1 --> AGG
    L2 --> AGG
    L3 --> AGG
    V1 --> AGG
    V2 --> AGG
    V3 --> AGG
    AGG --> RC
    RC --> APIGW

    subgraph DS["Document & Feature Stores"]
      DOCS[Doc Store (Blob/Object)]
      META[Doc Metadata (KV/Columnar)]
      LINKS[Link Graph (Column Family)]
      FEATS[Features & Signals<br/>(CTR, freshness, quality)]
    end
    LEX --> META
    VEC --> FEATS
    AGG --> DOCS

    %% ========== CRAWL/RE-CRAWL PIPELINE ==========
    subgraph RECAPI["Recrawl API Cluster (Stateless)"]
      RRL[Rate Limit]
      RAUTH[Auth]
      RAPI[Recrawl Controller]
    end
    APIGW --> RAUTH --> RRL --> RAPI

    subgraph QSYS["Job Queueing (Durable + Priority)"]
      PQ[Priority Queue<br/>(Kafka/Redis/RabbitMQ)]
      SCHED[Scheduler<br/>(Quota, politeness, SLA guardrails)]
    end
    RAPI -->|create jobs| PQ
    PQ --> SCHED

    subgraph CRAWL["Crawler Fleet (Autoscaled)"]
      UF[URL Frontier]
      FETCH[Fetcher Pool<br/>(Robots, politeness, DNS)]
      PARSE[Parse & Extract<br/>(Boilerplate removal, links)]
      DEDUP[Content Deduper<br/>(Simhash/shingling)]
    end
    SCHED --> UF --> FETCH --> PARSE --> DEDUP

    subgraph PIPE["Indexing Pipeline"]
      EXTR[Tokenize & Normalize]
      REV[Reverse Index Build]
      VBUILD[Vector Build/Encode]
      MERGE[Segment Merge & Push]
    end
    DEDUP --> EXTR --> REV --> MERGE
    DEDUP --> VBUILD --> MERGE
    MERGE -->|hot push| LEX
    MERGE -->|hot push| VEC
    PARSE --> DOCS
    PARSE --> META
    PARSE --> LINKS

    %% ========== OPERATIONS ==========
    subgraph OBS["Observability & Control"]
      LOGS[Logs]
      METRICS[Metrics]
      TRACES[Distributed Tracing]
      ADMIN[Admin Console]
      AB[A/B & Canary Control]
    end
    API --> LOGS & METRICS & TRACES
    SVC --> LOGS & METRICS & TRACES
    CRAWL --> LOGS & METRICS
    PIPE --> LOGS & METRICS
    ADMIN --> AB
    SR --> AB
```

Key design points
-----------------
- Stateless API/search tiers for horizontal scale; shards for throughput/latency isolation.
- Priority queues and scheduler allocations to guarantee 1‑hour SLA for on‑demand re‑crawls.
- Hot segment push to serving shards for near‑real‑time freshness without full re‑deploys.
- Multi‑tier caching for read path: CDN → gateway → result cache → shard query caches.
- Strong observability and rollout safety (A/B, canaries, feature flags).


