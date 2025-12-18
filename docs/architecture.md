# Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SvelteKit Frontend                                │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐│   │
│  │  │  Pages   │  │  Stores  │  │API Client│  │   UI Components      ││   │
│  │  │(routes/) │  │(.svelte  │  │(lib/api/)│  │   (shadcn-svelte)    ││   │
│  │  │          │  │  .ts)    │  │          │  │                      ││   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTP/REST + SSE
┌──────────────────────────────────▼──────────────────────────────────────────┐
│                              API LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      FastAPI Application                             │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │                        Middleware                               │ │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│ │   │
│  │  │  │   CORS   │  │   Auth   │  │  Rate    │  │   OpenTelemetry  ││ │   │
│  │  │  │          │  │  (JWT)   │  │  Limit   │  │   (Tracing)      ││ │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │   │
│  │  │                         Routes                                  │ │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐ │ │   │
│  │  │  │  Auth  │ │  Chat  │ │  Docs  │ │ Agents │ │  Workflows   │ │ │   │
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘ └──────────────┘ │ │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐ │ │   │
│  │  │  │Billing │ │ Admin  │ │Projects│ │ Health │ │  Webhooks    │ │ │   │
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘ └──────────────┘ │ │   │
│  │  └────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│                            SERVICE LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Business Services                             │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ AuthService  │  │ ChatService  │  │ DocumentSvc  │              │   │
│  │  │ - register   │  │ - chat       │  │ - upload     │              │   │
│  │  │ - login      │  │ - stream     │  │ - process    │              │   │
│  │  │ - refresh    │  │ - history    │  │ - chunk      │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │ RAGService   │  │ AgentService │  │ WorkflowSvc  │              │   │
│  │  │ - embed      │  │ - create     │  │ - execute    │              │   │
│  │  │ - retrieve   │  │ - configure  │  │ - stream     │              │   │
│  │  │ - search     │  │ - link_docs  │  │ - template   │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │BillingService│  │ UsageService │  │ AuditService │              │   │
│  │  │ - checkout   │  │ - track      │  │ - log        │              │   │
│  │  │ - portal     │  │ - summarize  │  │ - query      │              │   │
│  │  │ - webhooks   │  │ - limits     │  │ - export     │              │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│                             DATA LAYER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │   PostgreSQL 16    │  │       Redis        │  │     File Store     │    │
│  │    + pgvector      │  │                    │  │                    │    │
│  │                    │  │  - Rate limiting   │  │  - Uploaded docs   │    │
│  │  - Users           │  │  - Session cache   │  │  - Processed files │    │
│  │  - Documents       │  │  - Temp data       │  │                    │    │
│  │  - Chunks (vectors)│  │                    │  │                    │    │
│  │  - Conversations   │  │                    │  │                    │    │
│  │  - Agents          │  │                    │  │                    │    │
│  │  - Workflows       │  │                    │  │                    │    │
│  │  - Subscriptions   │  │                    │  │                    │    │
│  │  - Audit logs      │  │                    │  │                    │    │
│  │                    │  │                    │  │                    │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
│                                                                              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
┌──────────────────────────────────▼──────────────────────────────────────────┐
│                          EXTERNAL SERVICES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │      LiteLLM       │  │       Stripe       │  │    OpenTelemetry   │    │
│  │      Proxy         │  │                    │  │      Collector     │    │
│  │                    │  │  - Payments        │  │                    │    │
│  │  - OpenAI          │  │  - Subscriptions   │  │  - Traces          │    │
│  │  - Anthropic       │  │  - Invoices        │  │  - Metrics         │    │
│  │  - Google Gemini   │  │  - Webhooks        │  │  - Logs            │    │
│  │                    │  │                    │  │                    │    │
│  │                    │  │                    │  │                    │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## RAG Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCUMENT INGESTION                                   │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
     │  Upload  │────▶│  Parse   │────▶│  Chunk   │────▶│  Embed   │
     │  File    │     │  Content │     │  Text    │     │  Vectors │
     └──────────┘     └──────────┘     └──────────┘     └──────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
     │ PDF,DOCX │     │ Extract  │     │ 512-1024 │     │ 768-dim  │
     │ TXT,MD   │     │ Text     │     │ tokens   │     │ vectors  │
     │ CSV      │     │          │     │ overlap  │     │          │
     └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                              │
                                                              ▼
                                                        ┌──────────┐
                                                        │ pgvector │
                                                        │ Storage  │
                                                        └──────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            QUERY RETRIEVAL                                   │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
     │  User    │────▶│  Embed   │────▶│  Vector  │────▶│  Build   │
     │  Query   │     │  Query   │     │  Search  │     │  Context │
     └──────────┘     └──────────┘     └──────────┘     └──────────┘
                           │                │                │
                           ▼                ▼                ▼
                      ┌──────────┐     ┌──────────┐     ┌──────────┐
                      │ 768-dim  │     │ Top-K    │     │ Ranked   │
                      │ vector   │     │ Cosine   │     │ Chunks + │
                      │          │     │ Similar  │     │ Sources  │
                      └──────────┘     └──────────┘     └──────────┘
                                                              │
                                                              ▼
                                                        ┌──────────┐
                                                        │   LLM    │
                                                        │ Response │
                                                        │ + Sources│
                                                        └──────────┘
```

## Workflow Execution Engine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WORKFLOW BUILDER                                     │
└─────────────────────────────────────────────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │         Visual Canvas               │
                    │         (XYFlow)                    │
                    │                                     │
                    │    ┌─────┐      ┌─────┐            │
                    │    │Start│─────▶│ LLM │            │
                    │    └─────┘      └──┬──┘            │
                    │                    │               │
                    │              ┌─────▼─────┐         │
                    │              │ Condition │         │
                    │              └─────┬─────┘         │
                    │             ┌──────┴──────┐        │
                    │             ▼             ▼        │
                    │         ┌─────┐       ┌─────┐     │
                    │         │ RAG │       │HTTP │     │
                    │         └──┬──┘       └──┬──┘     │
                    │            └──────┬──────┘        │
                    │                   ▼               │
                    │               ┌─────┐             │
                    │               │ End │             │
                    │               └─────┘             │
                    └─────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       EXECUTION ENGINE                                       │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │                    Node Type Handlers                             │
    │                                                                   │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
    │  │  Start  │ │   LLM   │ │  Agent  │ │   RAG   │ │  Tool   │   │
    │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
    │                                                                   │
    │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
    │  │Condition│ │  Loop   │ │  HTTP   │ │ Custom  │ │   End   │   │
    │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
    └──────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼

    ┌──────────────────────────────────────────────────────────────────┐
    │                   Execution Flow                                  │
    │                                                                   │
    │   Parse Graph ──▶ Topological Sort ──▶ Execute Nodes             │
    │                                              │                    │
    │                                              ▼                    │
    │                                    ┌─────────────────┐           │
    │                                    │  SSE Streaming  │           │
    │                                    │  Event Updates  │           │
    │                                    └─────────────────┘           │
    └──────────────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          JWT AUTHENTICATION                                  │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌────────────┐                                      ┌────────────┐
    │   Client   │                                      │   Server   │
    └─────┬──────┘                                      └─────┬──────┘
          │                                                   │
          │  POST /auth/login {email, password}               │
          │──────────────────────────────────────────────────▶│
          │                                                   │
          │                                    ┌──────────────┴──────────────┐
          │                                    │ 1. Validate credentials      │
          │                                    │ 2. bcrypt.verify(password)   │
          │                                    │ 3. Generate JWT tokens        │
          │                                    │    - access_token (30 min)   │
          │                                    │    - refresh_token (7 days)  │
          │                                    └──────────────┬──────────────┘
          │                                                   │
          │  {access_token, refresh_token}                    │
          │◀──────────────────────────────────────────────────│
          │                                                   │
          │  GET /api/resource                                │
          │  Authorization: Bearer <access_token>             │
          │──────────────────────────────────────────────────▶│
          │                                    ┌──────────────┴──────────────┐
          │                                    │ 1. Decode & verify JWT       │
          │                                    │ 2. Check expiration          │
          │                                    │ 3. Load user from DB         │
          │                                    └──────────────┬──────────────┘
          │  {data}                                           │
          │◀──────────────────────────────────────────────────│
          │                                                   │
          │  POST /auth/refresh                               │
          │  {refresh_token}                                  │
          │──────────────────────────────────────────────────▶│
          │                                                   │
          │  {new_access_token}                               │
          │◀──────────────────────────────────────────────────│
          │                                                   │
```

## Database Schema (Simplified)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTITY RELATIONSHIPS                               │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │     User     │
    │──────────────│
    │ id           │
    │ email        │
    │ password_hash│
    │ tier         │
    │ is_superuser │
    └──────┬───────┘
           │
           │ 1:N
           │
    ┌──────┴──────────────────────────────────────────────────┐
    │                         │                                │
    ▼                         ▼                                ▼
┌──────────┐           ┌──────────────┐               ┌──────────────┐
│ Project  │           │ Conversation │               │ Subscription │
│──────────│           │──────────────│               │──────────────│
│ id       │           │ id           │               │ id           │
│ name     │           │ title        │               │ stripe_id    │
│ user_id  │           │ user_id      │               │ plan_id      │
└────┬─────┘           │ project_id   │               │ status       │
     │                 └──────┬───────┘               └──────────────┘
     │ 1:N                    │ 1:N
     │                        │
     ▼                        ▼
┌──────────────┐       ┌──────────────┐
│   Document   │       │   Message    │
│──────────────│       │──────────────│
│ id           │       │ id           │
│ filename     │       │ role         │
│ status       │       │ content      │
│ project_id   │       │ conversation │
└──────┬───────┘       └──────────────┘
       │ 1:N
       │
       ▼
┌──────────────────┐
│  DocumentChunk   │
│──────────────────│
│ id               │
│ content          │
│ embedding (768d) │◀──── pgvector
│ document_id      │
└──────────────────┘


┌──────────────┐           ┌──────────────┐
│    Agent     │           │   Workflow   │
│──────────────│           │──────────────│
│ id           │           │ id           │
│ name         │           │ name         │
│ system_prompt│           │ config (JSON)│
│ tools        │           │ is_published │
│ user_id      │           │ user_id      │
│ is_system    │           └──────┬───────┘
└──────────────┘                  │ 1:N
                                  │
                                  ▼
                          ┌────────────────────┐
                          │ WorkflowExecution  │
                          │────────────────────│
                          │ id                 │
                          │ status             │
                          │ input              │
                          │ output             │
                          │ execution_history  │
                          └────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DOCKER COMPOSE SETUP                                 │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                         app-network                                  │
    │                                                                      │
    │   ┌─────────────────┐     ┌─────────────────┐                       │
    │   │    Frontend     │     │     Backend     │                       │
    │   │   (Optional)    │     │    FastAPI      │                       │
    │   │   Port: 5173    │     │   Port: 8000    │                       │
    │   └─────────────────┘     └────────┬────────┘                       │
    │                                    │                                 │
    │          ┌─────────────────────────┼─────────────────────────┐      │
    │          │                         │                         │      │
    │          ▼                         ▼                         ▼      │
    │   ┌─────────────┐          ┌─────────────┐          ┌─────────────┐│
    │   │ PostgreSQL  │          │    Redis    │          │   LiteLLM   ││
    │   │   :5432     │          │    :6379    │          │    :4000    ││
    │   │             │          │             │          │             ││
    │   │  + pgvector │          │             │          │  + Postgres ││
    │   │             │          │             │          │    :5433    ││
    │   └─────────────┘          └─────────────┘          └─────────────┘│
    │                                                                      │
    └─────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────────┐
    │                    MONITORING (Optional Profile)                     │
    │                                                                      │
    │   ┌───────────────────────┐     ┌───────────────────────┐          │
    │   │  OpenTelemetry        │     │      Jaeger           │          │
    │   │  Collector            │────▶│      :16686           │          │
    │   │  :4317 (gRPC)         │     │      (Traces UI)      │          │
    │   └───────────────────────┘     └───────────────────────┘          │
    │                                                                      │
    └─────────────────────────────────────────────────────────────────────┘
```

## Security Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SECURITY ARCHITECTURE                               │
└─────────────────────────────────────────────────────────────────────────────┘

    Request Flow:

    ┌───────┐     ┌───────┐     ┌───────┐     ┌───────┐     ┌───────┐
    │ HTTPS │────▶│ CORS  │────▶│ Rate  │────▶│  JWT  │────▶│ Route │
    │       │     │ Check │     │ Limit │     │ Auth  │     │Handler│
    └───────┘     └───────┘     └───────┘     └───────┘     └───────┘

    Rate Limiting:
    ┌────────────────────────────────────────────────────────────────────┐
    │  Endpoint              │  Limit                                    │
    │────────────────────────┼───────────────────────────────────────────│
    │  /auth/login           │  5 requests/minute                        │
    │  /auth/register        │  3 requests/minute                        │
    │  /api/* (default)      │  60 requests/minute                       │
    │  /chat/stream          │  30 requests/minute                       │
    └────────────────────────────────────────────────────────────────────┘

    Data Protection:
    ┌────────────────────────────────────────────────────────────────────┐
    │  Layer                 │  Protection                               │
    │────────────────────────┼───────────────────────────────────────────│
    │  Password              │  bcrypt hashing with salt                 │
    │  JWT                   │  HS256 signing, 32-char min secret        │
    │  Database              │  Parameterized queries (SQLAlchemy)       │
    │  API                   │  Pydantic input validation                │
    │  Files                 │  Type validation, size limits             │
    └────────────────────────────────────────────────────────────────────┘
```

## Mermaid Diagrams

### System Overview (for GitHub/documentation viewers)

```mermaid
graph TB
    subgraph Client["Client Layer"]
        FE[SvelteKit Frontend]
    end

    subgraph API["API Layer"]
        GW[FastAPI Gateway]
        MW[Middleware<br/>CORS, Auth, Rate Limit]
    end

    subgraph Services["Service Layer"]
        AS[Auth Service]
        CS[Chat Service]
        DS[Document Service]
        RS[RAG Service]
        AGS[Agent Service]
        WS[Workflow Service]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL<br/>+ pgvector)]
        RD[(Redis)]
        FS[(File Storage)]
    end

    subgraph External["External Services"]
        LLM[LiteLLM Proxy]
        ST[Stripe]
        OT[OpenTelemetry]
    end

    FE --> GW
    GW --> MW
    MW --> AS & CS & DS & RS & AGS & WS

    AS & CS & DS & RS & AGS & WS --> PG
    AS & CS --> RD
    DS --> FS

    CS & RS & AGS & WS --> LLM
    AS --> ST
    MW --> OT
```

### RAG Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant DS as DocumentService
    participant RS as RAGService
    participant LLM as LiteLLM
    participant DB as PostgreSQL

    Note over U,DB: Document Ingestion
    U->>API: Upload PDF
    API->>DS: Process document
    DS->>DS: Parse & chunk text
    DS->>LLM: Generate embeddings
    LLM-->>DS: 768-dim vectors
    DS->>DB: Store chunks + vectors

    Note over U,DB: Query & Retrieval
    U->>API: Chat message
    API->>RS: retrieve_context()
    RS->>LLM: Embed query
    LLM-->>RS: Query vector
    RS->>DB: Vector similarity search
    DB-->>RS: Top-K chunks
    RS->>RS: Build prompt with context
    RS->>LLM: Generate response
    LLM-->>API: Streamed response
    API-->>U: SSE events
```

### Workflow Execution

```mermaid
stateDiagram-v2
    [*] --> Pending: Create workflow
    Pending --> Running: Execute
    Running --> NodeExec: Process node

    state NodeExec {
        [*] --> Start
        Start --> LLM: next
        LLM --> Condition: evaluate
        Condition --> RAG: if true
        Condition --> HTTP: if false
        RAG --> End
        HTTP --> End
    }

    NodeExec --> Completed: All nodes done
    NodeExec --> Failed: Error occurred
    Completed --> [*]
    Failed --> [*]
```
