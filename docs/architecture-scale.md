# Invoice Tracker — Scalability Architecture (10M+ Users)

## Current Bottlenecks (Baseline)

| Component | Current Limit | Reason |
|---|---|---|
| Single PostgreSQL instance | ~500 concurrent connections | No pooling layer, no replicas |
| Single FastAPI container | ~2 000 req/s | No horizontal scaling |
| Single Nginx | ~10 000 req/s | No CDN, no L4 load balancer |
| Synchronous PDF rendering | Blocks request thread | ReportLab blocks event loop |
| In-process rate limiting | Not shared across instances | slowapi state is per-process |
| No caching | Every dashboard hit = full DB scan | Raw SQL aggregations every request |
| Refresh token lookup | Full-table hash scan | No Redis; hits PostgreSQL every request |

---

## 1. Target Architecture Overview

```mermaid
graph TB
    subgraph Users["10M+ Users (Global)"]
        U["Browser / Mobile"]
    end

    subgraph Edge["Edge Layer"]
        CDN["CDN\n(Cloudflare / CloudFront)\n• Static assets cached globally\n• DDoS protection\n• Bot mitigation\n• Geo-routing"]
        WAF["WAF\n• OWASP rule sets\n• IP reputation\n• Rate limiting (edge)"]
    end

    subgraph LB["Load Balancing Layer"]
        GLB["Global Load Balancer\n(Anycast DNS)\nRegion failover"]
        R1["Region: EU-West"]
        R2["Region: US-East"]
        R3["Region: AP-Southeast"]
    end

    subgraph RegionStack["Regional Stack (repeated per region)"]
        NLB["L4 Load Balancer\n(AWS NLB / GCP NGLB)\nTCP passthrough"]
        ALB["L7 Application LB\n(Nginx / Envoy)\nTLS termination\nHTTP/2 + gRPC"]

        subgraph FECluster["Frontend Cluster (auto-scaled)"]
            FE1["Nuxt Nitro :3000"]
            FE2["Nuxt Nitro :3000"]
            FEN["Nuxt Nitro :3000"]
        end

        subgraph APICluster["API Cluster (auto-scaled)"]
            BE1["FastAPI :8000"]
            BE2["FastAPI :8000"]
            BEN["FastAPI :8000"]
        end

        subgraph Workers["Async Worker Pool"]
            W1["PDF Worker"]
            W2["Email Worker"]
            W3["Metrics Aggregator"]
        end

        subgraph Cache["Cache Layer"]
            RD1["Redis Primary\n(Valkey)"]
            RD2["Redis Replica"]
            RD3["Redis Replica"]
        end

        subgraph Queue["Message Bus"]
            MQ["Kafka / RabbitMQ\n• pdf.generate\n• email.send\n• invoice.updated\n• payment.processed"]
        end

        subgraph DBLayer["Database Layer"]
            PGW["PgBouncer\n(connection pool)\nPool: 5 000 server conns"]
            PGP["PostgreSQL Primary\n(writes)"]
            PGR1["PostgreSQL Replica 1\n(reads — analytics)"]
            PGR2["PostgreSQL Replica 2\n(reads — API queries)"]
        end

        subgraph Obs["Observability"]
            Prom["Prometheus"]
            Graf["Grafana"]
            Loki["Loki (logs)"]
            Tempo["Tempo (traces)"]
            Alert["Alertmanager"]
        end
    end

    U --> CDN --> WAF --> GLB
    GLB --> R1 & R2 & R3
    R1 --> NLB --> ALB
    ALB --> FE1 & FE2 & FEN
    ALB --> BE1 & BE2 & BEN
    BE1 & BE2 & BEN --> RD1
    RD1 --> RD2 & RD3
    BE1 & BE2 & BEN --> PGW
    BE1 & BE2 & BEN --> MQ
    MQ --> W1 & W2 & W3
    W1 & W2 & W3 --> PGW
    PGW --> PGP
    PGW --> PGR1 & PGR2
    PGP --> PGR1 & PGR2
    BE1 & BE2 & BEN --> Prom
    W1 & W2 & W3 --> Prom
    Prom --> Graf & Alert
    BE1 & BE2 & BEN --> Loki
    BE1 & BE2 & BEN --> Tempo
```

---

## 2. Database Scaling Strategy

```mermaid
graph TB
    subgraph App["API Instances"]
        A1["FastAPI #1"]
        A2["FastAPI #2"]
        AN["FastAPI #N"]
    end

    subgraph Pool["PgBouncer — Transaction Pooling"]
        PB["PgBouncer\n• server_pool_size = 5000\n• max_client_conn = 50000\n• pool_mode = transaction\n• Multiplexes N app conns → M DB conns"]
    end

    subgraph Primary["Write Path"]
        PGP["PostgreSQL Primary\n• Writes only\n• Synchronous replication → Replica 1\n• Asynchronous → Replica 2, 3"]
    end

    subgraph ReadReplicas["Read Path (load balanced)"]
        PGR1["Replica 1\nAPI read queries\n(clients, invoices list)"]
        PGR2["Replica 2\nAnalytics / dashboard\n(heavy aggregations)"]
        PGR3["Replica 3\nReporting / exports\n(long-running queries)"]
    end

    subgraph Sharding["Org-level Sharding (Phase 2 — >50M orgs)"]
        SH1["Shard 1\norg_id hash % 4 == 0"]
        SH2["Shard 2\norg_id hash % 4 == 1"]
        SH3["Shard 3\norg_id hash % 4 == 2"]
        SH4["Shard 4\norg_id hash % 4 == 3"]
        Router["Citus / Vitess Router\nRoutes by org_id"]
    end

    A1 & A2 & AN -->|"all traffic"| PB
    PB -->|"INSERT/UPDATE/DELETE"| PGP
    PB -->|"SELECT (non-analytics)"| PGR1 & PGR2
    PB -->|"SELECT (aggregations)"| PGR3
    PGP -->|"WAL streaming"| PGR1 & PGR2 & PGR3
    PB -.->|"Phase 2"| Router
    Router --> SH1 & SH2 & SH3 & SH4
```

### Read/Write Routing Rules

| Query Type | Route | Reason |
|---|---|---|
| `INSERT`, `UPDATE`, `DELETE` | Primary | Consistency required |
| `SELECT` invoices list / clients | Replica 1 | Low latency, high volume |
| `SELECT` dashboard aggregations | Replica 2 | Isolated from API traffic |
| `SELECT` PDF data (invoice + items) | Replica 1 | Read-only snapshot |
| `SELECT ... FOR UPDATE` (payments) | Primary | Requires write lock |
| Auth token lookups | Redis first → Primary fallback | Avoid DB on hot path |

---

## 3. Caching Strategy (Redis / Valkey)

```mermaid
flowchart TD
    Req["API Request"] --> AuthC{"Token in\nRedis cache?"}
    AuthC -- Hit --> Claims["Return cached claims\n(TTL: remaining token lifetime)"]
    AuthC -- Miss --> PGAUTH["Query PostgreSQL\nVerify token hash"]
    PGAUTH --> StoreC["Cache claims in Redis\nKey: sha256(token)\nTTL: 5 min"]
    StoreC --> Claims

    Claims --> DashC{"Dashboard summary\nin Redis?"}
    DashC -- Hit --> DashResp["Return cached response\n(TTL: 60s per org)"]
    DashC -- Miss --> PGDASH["Run aggregation query\nPostgreSQL Replica 2"]
    PGDASH --> StoreDash["Cache result\nKey: dash:org:{org_id}\nTTL: 60s"]
    StoreDash --> DashResp

    subgraph Invalidation["Cache Invalidation Events"]
        PayEv["payment.processed event"] --> InvDash["Invalidate dash:org:{org_id}"]
        InvEv["invoice.created / updated"] --> InvDash
        InvEv --> InvList["Invalidate invoices:org:{org_id}:*"]
        CliEv["client.updated"] --> InvCliList["Invalidate clients:org:{org_id}:*"]
    end
```

### Cache Key Taxonomy

| Key Pattern | TTL | Contents |
|---|---|---|
| `token:claims:{sha256}` | Remaining token lifetime | JWT claims dict (no secret) |
| `dash:org:{org_id}` | 60s | Dashboard summary JSON |
| `invoices:org:{org_id}:list:{hash(params)}` | 30s | Paginated invoice list |
| `clients:org:{org_id}:list:{hash(params)}` | 30s | Paginated client list |
| `rl:ip:{ip}` | 60s | Rate limit counter (replaces slowapi in-process) |
| `rl:user:{user_id}` | 60s | Per-user rate limit counter |
| `refresh:blacklist:{token_hash}` | Token TTL | Revoked refresh token tombstone |

---

## 4. Async PDF Generation (Offloaded)

### Current (Blocking)
```
Request → FastAPI → ReportLab (blocks event loop ~200-800ms) → Response
```

### Scaled (Non-blocking)

```mermaid
sequenceDiagram
    actor Browser
    participant API as FastAPI
    participant MQ as Kafka
    participant W as PDF Worker
    participant S3 as Object Storage<br/>(S3 / R2)
    participant Redis

    Browser->>+API: GET /invoices/{id}/pdf
    API->>Redis: Check pdf:{invoice_id}:{version} exists?
    Redis-->>API: Miss
    API->>MQ: Publish pdf.generate {invoice_id, org_id, version}
    API-->>-Browser: 202 Accepted<br/>{job_id, poll_url}

    MQ->>+W: Consume pdf.generate event
    W->>DB: Fetch invoice + client + items
    W->>W: ReportLab render (~500ms, isolated)
    W->>S3: PUT invoice-pdfs/{org_id}/{invoice_id}/{version}.pdf
    W->>Redis: SET pdf:{invoice_id}:{version} = s3_presigned_url (TTL: 1h)
    W-->>-MQ: Ack

    Browser->>+API: GET /invoices/{id}/pdf/status
    API->>Redis: GET pdf:{invoice_id}:{version}
    Redis-->>API: presigned URL
    API-->>-Browser: 200 {url} — redirect to S3
    Browser->>S3: GET presigned URL
    S3-->>Browser: PDF bytes (direct, no API hop)
```

---

## 5. Rate Limiting at Scale (Distributed)

```mermaid
graph LR
    subgraph EdgeRL["Edge Rate Limiting (Cloudflare)"]
        E1["DDoS / volumetric\n>1000 req/5s per IP → block"]
        E2["Auth endpoints\n10 req/min per IP → 429"]
    end

    subgraph NginxRL["Nginx Rate Limiting"]
        N1["auth_limit: 5 r/min per IP\nburst=2 nodelay"]
        N2["api_limit: 100 r/s per IP\nburst=200"]
    end

    subgraph AppRL["App-level Rate Limiting (Redis)"]
        R1["Per-user: 300 req/min\nKey: rl:user:{id}"]
        R2["Per-org: 3000 req/min\nKey: rl:org:{id}"]
        R3["Payment endpoint: 10/min per org\nKey: rl:pay:{org_id}"]
        Script["Lua script (atomic)\nINCR + EXPIRE in one RTT"]
    end

    Request --> E1 --> E2 --> N1 & N2 --> R1 & R2 & R3
    R1 & R2 & R3 --> Script
```

---

## 6. Multi-Region Active-Active (Global Scale)

```mermaid
graph TB
    subgraph Global
        DNS["Global Anycast DNS\nLatency-based routing"]
    end

    subgraph EU["EU-West (Primary)"]
        EU_ALB["ALB"] --> EU_FE["FE Cluster x5"]
        EU_ALB --> EU_BE["BE Cluster x10"]
        EU_BE --> EU_Redis["Redis Cluster\n3 primary + 3 replica"]
        EU_BE --> EU_PG["PostgreSQL\nPrimary (writes)"]
        EU_PG --> EU_PGR["Read Replicas x3"]
    end

    subgraph US["US-East (Secondary)"]
        US_ALB["ALB"] --> US_FE["FE Cluster x5"]
        US_ALB --> US_BE["BE Cluster x10"]
        US_BE --> US_Redis["Redis Cluster"]
        US_BE --> US_PG["PostgreSQL\nRead Replica (local reads)"]
        US_BE -.->|"Cross-region writes\n(low volume)"| EU_PG
    end

    subgraph AP["AP-Southeast (Secondary)"]
        AP_ALB["ALB"] --> AP_FE["FE Cluster x3"]
        AP_ALB --> AP_BE["BE Cluster x5"]
        AP_BE --> AP_Redis["Redis Cluster"]
        AP_BE --> AP_PG["PostgreSQL\nRead Replica (local reads)"]
        AP_BE -.->|"Cross-region writes"| EU_PG
    end

    DNS --> EU_ALB
    DNS --> US_ALB
    DNS --> AP_ALB
    EU_PG -->|"WAL replication"| US_PG & AP_PG
```

### Write Routing in Multi-Region

- **Reads** → always hit local region replica (< 10ms latency)
- **Writes** → route to primary region via internal gRPC (50-200ms cross-region acceptable for financial data consistency)
- **Payment writes** → always primary (idempotency key prevents double-write on retry)
- **Phase 2**: Migrate to CockroachDB or PlanetScale for true active-active writes

---

## 7. Auto-Scaling Policy

```mermaid
graph LR
    subgraph Metrics["Scaling Triggers"]
        M1["CPU > 70% (2min avg)"]
        M2["p99 latency > 500ms"]
        M3["Queue depth > 1000 msgs"]
        M4["Active connections > 80% pool"]
    end

    subgraph ScaleOut["Scale Out"]
        S1["FE: +2 pods (max 20)"]
        S2["BE: +3 pods (max 50)"]
        S3["Workers: +2 pods (max 30)"]
        S4["PgBouncer: +1 pool (vertical)"]
    end

    subgraph ScaleIn["Scale In"]
        SI1["CPU < 30% (10min avg)\nFE: -1 pod (min 2)"]
        SI2["Queue depth < 100\nWorkers: -1 pod (min 1)"]
    end

    M1 --> S2
    M2 --> S1 & S2
    M3 --> S3
    M4 --> S4
    SI1 --> SI2
```

---

## 8. Observability Stack (Production)

```mermaid
graph LR
    subgraph Sources["Instrumentation"]
        BE["FastAPI\nOpenTelemetry SDK\nPrometheus /metrics"]
        FE["Nuxt Nitro\nStructured JSON logs\nWeb Vitals"]
        PG["PostgreSQL\npg_stat_statements\nSlow query log"]
        RD["Redis\nRedis INFO\ncommand latency"]
        MQ["Kafka\nconsumer lag metrics"]
    end

    subgraph Collection["Collection"]
        OC["OpenTelemetry Collector\nBatching + sampling"]
        PA["Prometheus Agent\nRemote write"]
        FA["Fluentbit\nLog shipping"]
    end

    subgraph Storage["Storage & Querying"]
        Mimir["Grafana Mimir\n(metrics, long-term)"]
        Loki["Grafana Loki\n(logs)"]
        Tempo["Grafana Tempo\n(traces)"]
    end

    subgraph Dashboards["Dashboards & Alerts"]
        Graf["Grafana\n• Org-level SLOs\n• API latency p50/p95/p99\n• Error rate by route\n• Queue consumer lag\n• DB replication lag\n• Cache hit rate"]
        AM["Alertmanager\n• PagerDuty on-call\n• Slack #incidents\n• Auto-runbook links"]
    end

    BE & FE --> OC
    PG & RD & MQ --> PA
    BE & FE --> FA
    OC --> Mimir & Loki & Tempo
    PA --> Mimir
    FA --> Loki
    Mimir & Loki & Tempo --> Graf
    Graf --> AM
```

### SLO Targets at 10M Users

| Metric | Target |
|---|---|
| API availability | 99.95% (< 4.4h downtime/year) |
| p99 API latency (read) | < 200ms |
| p99 API latency (write) | < 500ms |
| PDF generation (async) | < 5s end-to-end |
| Auth endpoint latency p99 | < 300ms |
| DB replication lag | < 1s |
| Cache hit rate | > 85% |
| Error rate | < 0.1% |

---

## 9. Migration Roadmap (Baseline → 10M Users)

```mermaid
gantt
    title Scaling Phases
    dateFormat  YYYY-MM
    section Phase 1 — 0 to 100K users
    Add PgBouncer connection pool     :p1a, 2026-09, 1M
    Add Redis (token cache + rate limit) :p1b, 2026-09, 2M
    Add read replica (1x)             :p1c, 2026-10, 1M
    Horizontally scale FastAPI (3 pods) :p1d, 2026-10, 1M
    CDN for static assets             :p1e, 2026-10, 1M
    Offload PDF to async worker       :p1f, 2026-11, 2M

    section Phase 2 — 100K to 1M users
    Add second read replica (analytics) :p2a, 2027-01, 1M
    Kafka message bus                 :p2b, 2027-01, 2M
    Multi-AZ PostgreSQL (HA failover) :p2c, 2027-02, 2M
    Redis Cluster mode                :p2d, 2027-03, 1M
    Horizontal FE scaling (5 pods)    :p2e, 2027-03, 1M
    Distributed tracing (OTel)        :p2f, 2027-04, 2M
    WAF + edge rate limiting          :p2g, 2027-05, 1M

    section Phase 3 — 1M to 10M users
    Second region (active-passive)    :p3a, 2027-07, 3M
    Citus sharding by org_id          :p3b, 2027-09, 4M
    Third region (active-active reads) :p3c, 2028-01, 3M
    True active-active writes (CockroachDB / Spanner) :p3d, 2028-04, 6M
```

---

## 10. Security Additions at Scale

| Threat | Current | At Scale |
|---|---|---|
| Credential stuffing | 5 r/min Nginx | Edge WAF + device fingerprinting + CAPTCHA threshold |
| JWT secret compromise | Single secret | Key rotation via KMS (AWS KMS / Vault); kid in JWT header |
| Org data leak (tenant isolation) | org_id in SQL WHERE | Row-level security in PostgreSQL (`ALTER TABLE ENABLE ROW LEVEL SECURITY`) |
| DDoS | Nginx rate limit | Cloudflare Magic Transit + anycast absorption |
| Secrets in env vars | `.env` files | HashiCorp Vault / AWS Secrets Manager with dynamic credentials |
| DB credentials rotation | Manual | Vault database secrets engine (auto-rotate every 24h) |
| Supply chain | `pyproject.toml` | Renovate bot + `pip-audit` in CI + Docker image signing (Sigstore) |
