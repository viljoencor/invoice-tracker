# Invoice Tracker — System Architecture

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph Browser["Browser (SPA)"]
        UI["Nuxt 3 SPA\n(Vue 3 + Pinia + Tailwind)"]
    end

    subgraph Docker["Docker Network: app_network"]
        subgraph Nginx["nginx:443 (TLS 1.2/1.3)"]
            NX["Nginx Reverse Proxy\n• HSTS max-age=31536000\n• auth_limit: 5r/min\n• api_limit: 10r/s burst=20\n• HTTP→HTTPS 301"]
        end

        subgraph FE["frontend:3000"]
            Nuxt["Nuxt 3 Nitro Server\n(BFF / SSR-disabled SPA host)"]
            Proxy["Nitro Proxy Handler\n/api/proxy/[...path]"]
            Auth_BFF["Auth Handlers\n/api/auth/login|logout|refresh"]
            CSRF["CSRF Middleware\nOrigin == Host check"]
        end

        subgraph BE["backend:8000"]
            FastAPI["FastAPI (async)\nUvicorn ASGI"]
            Trace["TraceIdMiddleware"]
            Timeout["TimeoutMiddleware (55s)"]
            Rate["slowapi Rate Limiter"]
            AuthR["Auth Router"]
            ClientsR["Clients Router"]
            InvoicesR["Invoices Router"]
            PaymentsR["Payments Router"]
            DashR["Dashboard Router"]
            Metrics["Prometheus /metrics"]
            PDF["ReportLab PDF Service"]
        end

        subgraph DB["db:5432"]
            PG["PostgreSQL 16"]
        end
    end

    Browser -->|"HTTPS"| NX
    NX -->|"/api/auth/*"| Nuxt
    NX -->|"/api/*"| Nuxt
    NX -->|"/ SPA assets"| Nuxt
    NX -->|"/healthz"| FastAPI
    Nuxt --> CSRF
    CSRF --> Auth_BFF
    CSRF --> Proxy
    Proxy -->|"Bearer <at_cookie>\nInternal HTTP"| FastAPI
    Auth_BFF -->|"Internal HTTP"| FastAPI
    FastAPI --> Trace
    Trace --> Timeout
    Timeout --> Rate
    Rate --> AuthR & ClientsR & InvoicesR & PaymentsR & DashR
    InvoicesR --> PDF
    AuthR & ClientsR & InvoicesR & PaymentsR & DashR -->|"SQLAlchemy async"| PG
```

---

## 2. Database Schema (Entity-Relationship)

```mermaid
erDiagram
    orgs {
        UUID id PK
        string name
        datetime created_at
    }

    users {
        UUID id PK
        string email UK
        string password_hash
        string name
        datetime created_at
    }

    org_members {
        UUID org_id PK
        UUID user_id PK
        string role
    }

    clients {
        UUID id PK
        UUID org_id FK
        string name
        string email
        string billing_address
        jsonb meta
    }

    invoices {
        UUID id PK
        UUID org_id FK
        UUID client_id FK
        string number UK
        date issue_date
        date due_date
        string currency
        int subtotal_cents
        int tax_cents
        int total_cents
        int balance_cents
        string status
        string notes
        jsonb meta
    }

    invoice_items {
        UUID invoice_id PK
        int line_no PK
        string description
        float qty
        int unit_price_cents
        int tax_rate_bp
        int line_total_cents
    }

    invoice_seq {
        UUID org_id PK
        int next_seq
    }

    payments {
        UUID id PK
        UUID org_id FK
        UUID invoice_id FK
        int amount_cents
        date received_at
        string method
        string reference
        string idempotency_key UK
    }

    refresh_tokens {
        UUID id PK
        string token_hash UK
        UUID user_id FK
        UUID org_id FK
        datetime expires_at
        bool revoked
    }

    orgs ||--o{ org_members : "has members"
    users ||--o{ org_members : "belongs to"
    orgs ||--o{ clients : "owns"
    orgs ||--o{ invoices : "owns"
    orgs ||--|{ invoice_seq : "counter"
    clients ||--o{ invoices : "billed on"
    invoices ||--o{ invoice_items : "contains"
    invoices ||--o{ payments : "paid by"
    users ||--o{ refresh_tokens : "issued to"
    orgs ||--o{ refresh_tokens : "scoped to"
```

---

## 3. Authentication & Token Lifecycle

```mermaid
sequenceDiagram
    actor Browser
    participant Nitro as Nitro BFF<br/>(frontend:3000)
    participant FastAPI as FastAPI<br/>(backend:8000)
    participant PG as PostgreSQL

    Browser->>+Nitro: POST /api/auth/login {email, password}
    Nitro->>Nitro: CSRF check (Origin == Host)
    Nitro->>+FastAPI: POST /api/v1/auth/login
    FastAPI->>PG: SELECT user WHERE email=...
    PG-->>FastAPI: user row
    FastAPI->>FastAPI: verify Argon2id hash
    FastAPI->>PG: INSERT refresh_token (SHA-256 hash)
    FastAPI-->>-Nitro: {access_token, refresh_token}
    Nitro->>Browser: Set-Cookie: at (httpOnly, 30min)<br/>Set-Cookie: rt (httpOnly, 12h)<br/>Set-Cookie: session (12h, JS-readable)
    Nitro-->>-Browser: {ok: true}

    Note over Browser,PG: Subsequent authenticated requests

    Browser->>+Nitro: GET /api/proxy/invoices (cookies auto-sent)
    Nitro->>Nitro: Read at cookie — whitelist path check
    Nitro->>+FastAPI: GET /api/v1/invoices<br/>Authorization: Bearer <at>
    FastAPI->>FastAPI: JWT verify (HS256)<br/>extract sub, org_id, role
    FastAPI->>PG: SELECT invoices WHERE org_id=...
    PG-->>FastAPI: rows
    FastAPI-->>-Nitro: 200 JSON
    Nitro-->>-Browser: 200 JSON

    Note over Browser,PG: Token refresh (at expired)

    Browser->>+Nitro: GET /api/proxy/... (stale at cookie)
    Nitro->>FastAPI: Request → 401
    Nitro->>+FastAPI: POST /api/v1/auth/refresh {refresh_token}
    FastAPI->>PG: SELECT token WHERE hash=... AND NOT revoked
    FastAPI->>PG: UPDATE token SET revoked=true (rotate)
    FastAPI->>PG: INSERT new refresh_token
    FastAPI-->>-Nitro: {access_token, refresh_token}
    Nitro->>Browser: Set-Cookie: new at + rt + session
    Nitro->>FastAPI: Retry original request with new at
    FastAPI-->>Nitro: 200 JSON
    Nitro-->>-Browser: 200 JSON
```

---

## 4. Payment Idempotency & Concurrency Flow

```mermaid
flowchart TD
    A["POST /payments\n+ Idempotency-Key header"] --> B{Key header present?}
    B -- No --> E1["400 Bad Request"]
    B -- Yes --> C["Pre-check: SELECT payment\nWHERE org_id + idempotency_key"]
    C -- Found --> R["Return existing result\n(idempotent replay)"]
    C -- Not found --> D["SELECT invoice FOR UPDATE\n(row lock)"]
    D --> F["Re-check idempotency inside lock"]
    F -- Race: found --> R
    F -- Still not found --> G{invoice.status valid?}
    G -- void or paid --> E2["409 Conflict"]
    G -- OK --> H{amount_cents ≤ balance_cents?}
    H -- No --> E3["422 Unprocessable"]
    H -- Yes --> I["INSERT payment record"]
    I --> J["invoice.balance_cents -= amount"]
    J --> K{balance == 0?}
    K -- Yes --> L["status = 'paid'"]
    K -- No --> M["status = 'partially_paid'"]
    L & M --> N["COMMIT — lock released"]
    N --> O["200 {payment_id, invoice_status, balance_cents}"]
    D -- IntegrityError --> R
```

---

## 5. Frontend Routing & State Architecture

```mermaid
graph LR
    subgraph Middleware
        AuthMW["auth.ts\n(route guard)"]
    end

    subgraph Pages
        Login["/login"]
        Dashboard["/\n(index)"]
        Clients["/clients"]
        ClientDetail["/clients/:id"]
        Invoices["/invoices"]
        InvoiceNew["/invoices/new"]
        InvoiceDetail["/invoices/:id"]
    end

    subgraph Stores
        InvStore["invoices store\n{items, loaded, pending, error}"]
        CliStore["clients store\n{items, loaded, pending, error}"]
    end

    subgraph Composables
        UseApi["useApi()\nget/post/patch/del\ngetArrayBuffer"]
        UseAuth["useAuth()\nisAuthenticated\nlogout()"]
    end

    subgraph Cookies
        Session["session cookie\n(not httpOnly — JS-readable)"]
        AT["at cookie\n(httpOnly — invisible to JS)"]
        RT["rt cookie\n(httpOnly — invisible to JS)"]
    end

    AuthMW -->|"session≠'1'"| Login
    AuthMW -->|"session='1'"| Dashboard

    Dashboard --> InvStore & CliStore
    Clients --> CliStore
    Invoices --> InvStore

    InvStore --> UseApi
    CliStore --> UseApi
    Dashboard --> UseApi

    UseAuth --> Session
    UseApi -->|"/api/proxy/*"| AT
    AT -->|"auto on request"| Nitro["Nitro BFF Proxy"]
```

---

## 6. Infrastructure Topology (Production)

```mermaid
graph TB
    Internet["Internet"] -->|"443/TLS"| LB["Load Balancer / DNS"]
    LB --> NX["Nginx\nnginx:443\nTLS termination\nRate limiting\nHSTS\nHTTP→HTTPS 301"]

    NX -->|"/healthz direct"| BE
    NX -->|"/api/auth/* — auth_limit\n5r/min per IP"| FE
    NX -->|"/api/* — api_limit\n10r/s burst=20"| FE
    NX -->|"/ SPA + static assets\ncache 30d immutable"| FE

    subgraph Docker["Docker Swarm / Compose — app_network (bridge)"]
        FE["frontend:3000\nNuxt 3 Nitro\nCPU: 2c / 0.5c res\nMem: 2G / 512M res"]
        BE["backend:8000\nFastAPI + Uvicorn\nCPU: 2c / 0.5c res\nMem: 2G / 512M res\nPool: 30+20 conns"]
        PG["db:5432\nPostgreSQL 16\nCPU: 2c / 1c res\nMem: 2G / 1G res"]
    end

    FE -->|"Internal HTTP\nNUXT_API_BASE=http://backend:8000/api/v1"| BE
    BE -->|"SQLAlchemy async\nAsyncPG driver"| PG

    PG --- V1[("Volume: db_prod_data")]
    NX --- V2[("Volume: nginx_cache")]

    BE -->|"/metrics"| Prom["Prometheus\n(scrape target)"]
```

---

## 7. Request Middleware Stack (FastAPI)

```mermaid
graph TD
    Req["Incoming HTTP Request"] --> T["TraceIdMiddleware\n• Validate/generate trace ID\n• Inject x-trace-id header"]
    T --> TO["TimeoutMiddleware\n• 55s deadline → 504 if exceeded"]
    TO --> CORS["CORSMiddleware\n• Origin whitelist\n• credentials: true"]
    TO --> RL["slowapi Rate Limiter\n• Per-route decorator\n• RateLimitExceeded → 429"]
    RL --> Router["FastAPI Router"]
    Router --> Auth{"JWT Auth\nDepends(get_current_claims)"}
    Auth -- Invalid --> E401["401 Unauthorized"]
    Auth -- Valid --> RBAC{"require_role()\ncheck claims.role"}
    RBAC -- Insufficient --> E403["403 Forbidden"]
    RBAC -- OK --> Handler["Route Handler\n(org_id scoped queries)"]
    Handler --> PG["PostgreSQL\n(SQLAlchemy async)"]
    PG --> Resp["Response"]

    subgraph GlobalExceptionHandlers["Global Exception Handlers"]
        EH1["SQLAlchemyError → 500 sanitized"]
        EH2["RequestValidationError → 422 field errors"]
        EH3["RateLimitExceeded → 429"]
        EH4["Exception → 500 (prod: sanitized / dev: trace)"]
    end
```

---

## 8. Invoice Number Generation (Atomic Sequence)

```mermaid
sequenceDiagram
    participant H as Route Handler
    participant PG as PostgreSQL

    H->>PG: INSERT INTO invoice_seq(org_id, next_seq)<br/>VALUES (:org_id, 1)<br/>ON CONFLICT (org_id)<br/>DO UPDATE SET next_seq = invoice_seq.next_seq + 1<br/>RETURNING next_seq
    PG-->>H: next_seq = N
    H->>H: number = f"INV-{year}-{N:05d}"
    H->>PG: INSERT INTO invoices (..., number=number, ...)
    Note over H,PG: Atomic — no race condition possible.<br/>No separate SELECT then UPDATE.
```

---

## Key Design Decisions

| Concern | Solution |
|---|---|
| **Multi-tenancy** | Every table row carries `org_id`; JWT embeds `org_id`; every query scopes by it |
| **Token security** | `at` in `httpOnly` cookie (no JS access); `session` flag readable for route guards; refresh tokens stored as SHA-256 hash |
| **Payment idempotency** | `(org_id, idempotency_key)` unique constraint + `SELECT FOR UPDATE` row lock prevents double-charge under concurrency |
| **Money precision** | Integer cents throughout; `Decimal` + `ROUND_HALF_UP` for tax accumulation before insert |
| **CSRF protection** | Nitro server middleware enforces `Origin == Host` on all state-changing requests |
| **Rate limiting** | Dual-layer: Nginx (IP-level, 5r/min auth / 10r/s API) + slowapi (app-level, per-route) |
| **Open proxy prevention** | Nitro proxy validates path against explicit whitelist before forwarding to FastAPI |
| **Observability** | Trace IDs propagated end-to-end via `x-trace-id`; Prometheus `/metrics`; structured JSON logs in production |
| **PDF generation** | On-demand ReportLab rendering, streamed as `application/pdf` — no caching |
| **Invoice numbering** | `INSERT ... ON CONFLICT DO UPDATE RETURNING` — single atomic statement, no locks needed |
