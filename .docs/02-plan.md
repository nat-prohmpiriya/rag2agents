# Technical Plan: RAG Agent Platform

## Overview

**Document Purpose:** Comprehensive Technical Plan ที่ละเอียดและนำไปปฏิบัติได้จริง โดยอ้างอิงจาก Product Specification (01-spec.md) และ Codebase ปัจจุบัน

**Tech Stack:**
- **Frontend:** SvelteKit 2 + Svelte 5 (Runes) + Tailwind CSS v4 + shadcn-svelte
- **Backend:** FastAPI + Python 3.12 + SQLAlchemy async + PostgreSQL 16
- **AI Integration:** LiteLLM Proxy (Google Gemini)
- **Vector Store:** pgvector (PostgreSQL extension)
- **Caching/Rate Limiting:** Redis
- **Payment:** Stripe
- **Observability:** OpenTelemetry (traces, logs, metrics) + Glitchtip (frontend errors)

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  SvelteKit 2 + Svelte 5 (Runes)                                 │    │
│  │  ├── (app)      → Protected routes (chat, agents, workflows)    │    │
│  │  ├── (admin)    → Admin dashboard                               │    │
│  │  └── (public)   → Landing, pricing, docs                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                    │                                     │
│                              HTTP/REST                                   │
└────────────────────────────────────┼────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              BACKEND                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  FastAPI + Python 3.12                                          │    │
│  │  ├── Routes Layer    → HTTP handling, validation                │    │
│  │  ├── Services Layer  → Business logic, orchestration            │    │
│  │  └── Models Layer    → SQLAlchemy ORM                           │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│           │                    │                    │                    │
│           ▼                    ▼                    ▼                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐       │
│  │  PostgreSQL  │    │    Redis     │    │   LiteLLM Proxy      │       │
│  │  + pgvector  │    │  (Cache/RL)  │    │   (Multi-Provider)   │       │
│  └──────────────┘    └──────────────┘    └──────────────────────┘       │
│                                                     │                    │
└─────────────────────────────────────────────────────┼───────────────────┘
                                                      │
                                                      ▼
                                    ┌─────────────────────────────────┐
                                    │      LLM Providers              │
                                    │  └── Google (Gemini)            │
                                    │                                 │
                                    │                                 │
                                    │                                 │
                                    │                                 │
                                    └─────────────────────────────────┘
```

### 1.2 Request Flow

```
User Request → Frontend
    │
    ▼
SvelteKit API Client ($lib/api/*)
    │
    ├── JWT Token (Authorization Header)
    │
    ▼
FastAPI Backend
    │
    ├── Middleware (CORS, TraceContext, Metrics)
    │
    ├── Routes Layer (Validation, Auth)
    │       │
    │       ▼
    ├── Services Layer (Business Logic)
    │       │
    │       ├── Database Operations (SQLAlchemy Async)
    │       │
    │       ├── RAG Operations (Vector Search)
    │       │       │
    │       │       ├── Embedding Service (text-embedding-004)
    │       │       │
    │       │       └── Vector Store (pgvector)
    │       │
    │       └── LLM Operations
    │               │
    │               ▼
    │           LiteLLM Proxy
    │               │
    │               ├── Rate Limiting (Redis)
    │               ├── Usage Tracking
    │               └── Multi-Provider Routing
    │
    ▼
Response → Frontend
```

### 1.3 Data Flow for Key Features

#### Document Upload & Processing
```
1. User uploads file → POST /api/v1/documents/upload
2. Store file to local storage (or S3 in production)
3. Create Document record (status: pending)
4. Background task: Document Processing
   ├── Parse file (PDF/DOCX/TXT/MD/CSV)
   ├── Chunk content (split into smaller pieces)
   ├── Generate embeddings (via LiteLLM → Gemini)
   └── Store chunks with embeddings (pgvector)
5. Update Document status (ready/error)
6. Notify user (in-app notification)
```

#### Agent Chat with RAG
```
1. User sends message → POST /api/v1/chat/stream
2. Load Agent configuration (system_prompt, tools, linked_documents)
3. If RAG enabled:
   ├── Embed user query
   ├── Vector search in linked documents
   └── Retrieve top-k relevant chunks
4. Build prompt (system + context + history + user message)
5. Call LLM via LiteLLM (streaming)
6. Stream response to user (SSE)
7. Save message to database
8. Track usage (tokens, cost)
```

#### Workflow Execution
```
1. User triggers workflow → POST /api/v1/workflows/{id}/execute
2. Create WorkflowExecution record
3. Parse workflow nodes and edges (DAG)
4. Execute nodes sequentially:
   ├── start → Initialize context
   ├── llm   → Call LLM, pass output to next
   ├── agent → Call agent (with RAG if configured)
   ├── http  → Make HTTP request
   ├── rag   → Search documents
   ├── condition → Branch based on logic
   ├── loop  → Iterate over data
   └── end   → Return final output
5. Update node_states in real-time
6. Save outputs and logs
7. Track total tokens used
```

---

## 2. Data Model / Schema

### 2.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    USERS & AUTH                                          │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────┐                   ┌─────────────┐                   ┌─────────────┐    │
│  │    User     │ 1 ────────── * │  Subscription │ * ────────── 1 │     Plan      │    │
│  │─────────────│                   │─────────────│                   │─────────────│    │
│  │ id (UUID)   │                   │ id          │                   │ id          │    │
│  │ email       │                   │ user_id     │                   │ name        │    │
│  │ username    │                   │ plan_id     │                   │ plan_type   │    │
│  │ password    │                   │ status      │                   │ price       │    │
│  │ tier        │                   │ stripe_id   │                   │ limits      │    │
│  │ is_active   │                   │ litellm_key │                   │ stripe_id   │    │
│  │ is_superuser│                   │ dates...    │                   │             │    │
│  └─────────────┘                   └─────────────┘                   └─────────────┘    │
│        │                                 │                                               │
│        │ 1                               │                                               │
│        │                                 ▼ *                                             │
│        │                           ┌─────────────┐                                       │
│        │                           │   Invoice   │                                       │
│        │                           └─────────────┘                                       │
│        │                                                                                 │
└────────┼────────────────────────────────────────────────────────────────────────────────┘
         │
         │ 1
         │
         ├──────────────────────────────────────────────────────────────────────────────┐
         │                                                                              │
         ▼ *                                                                            │
┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│                                    PROJECTS & CONTENT                                │ │
├─────────────────────────────────────────────────────────────────────────────────────┤ │
│                                                                                      │ │
│  ┌─────────────┐                   ┌─────────────┐                                   │ │
│  │   Project   │ * ────────── * │  Document   │                                     │ │
│  │─────────────│   (via M2M)      │─────────────│                                   │ │
│  │ id (UUID)   │                   │ id (UUID)   │                                   │ │
│  │ name        │ ProjectDocument   │ filename    │                                   │ │
│  │ description │ ┌─────────────┐   │ file_type   │                                   │ │
│  │ user_id     │ │ project_id  │   │ file_path   │                                   │ │
│  │ privacy_lvl │ │ document_id │   │ status      │                                   │ │
│  └─────────────┘ └─────────────┘   │ tags[]      │                                   │ │
│        │                           │ user_id     │                                   │ │
│        │ 1                         └─────────────┘                                   │ │
│        │                                 │ 1                                         │ │
│        ▼ *                               │                                           │ │
│  ┌─────────────┐                         ▼ *                                         │ │
│  │    Agent    │                   ┌───────────────┐                                 │ │
│  │─────────────│                   │ DocumentChunk │                                 │ │
│  │ id (UUID)   │                   │───────────────│                                 │ │
│  │ name        │                   │ id (UUID)     │                                 │ │
│  │ slug        │                   │ document_id   │                                 │ │
│  │ system_prompt│                  │ content       │                                 │ │
│  │ tools[]     │                   │ embedding[768]│ ← pgvector                      │ │
│  │ document_ids│                   │ chunk_index   │                                 │ │
│  │ source      │                   │ metadata      │                                 │ │
│  │ project_id  │                   └───────────────┘                                 │ │
│  │ user_id     │                                                                     │ │
│  └─────────────┘                                                                     │ │
│        │                                                                             │ │
└────────┼─────────────────────────────────────────────────────────────────────────────┘ │
         │                                                                               │
         │                                                                               │
┌────────┼───────────────────────────────────────────────────────────────────────────────┘
│        │
│        ▼
├─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    CONVERSATIONS & CHAT                                  │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────┐                   ┌─────────────┐                                       │
│  │Conversation │ 1 ────────── * │   Message   │                                        │
│  │─────────────│                   │─────────────│                                       │
│  │ id (UUID)   │                   │ id (UUID)   │                                       │
│  │ title       │                   │ conv_id     │                                       │
│  │ project_id  │                   │ role        │ (user/assistant/system)               │
│  │ user_id     │                   │ content     │                                       │
│  └─────────────┘                   │ tokens_used │                                       │
│                                    │ search_vec  │ ← tsvector (FTS)                      │
│                                    └─────────────┘                                       │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    WORKFLOWS                                             │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────┐                   ┌───────────────────┐                                 │
│  │  Workflow   │ 1 ────────── * │ WorkflowExecution │                                   │
│  │─────────────│                   │───────────────────│                                 │
│  │ id (UUID)   │                   │ id (UUID)         │                                 │
│  │ name        │                   │ workflow_id       │                                 │
│  │ description │                   │ user_id           │                                 │
│  │ nodes[]     │ (JSON)            │ status            │ (pending/running/completed/...)  │
│  │ edges[]     │ (JSON)            │ inputs{}          │                                 │
│  │ viewport{}  │ (JSON)            │ outputs{}         │                                 │
│  │ status      │                   │ node_states{}     │                                 │
│  │ is_template │                   │ current_node_id   │                                 │
│  │ user_id     │                   │ logs[]            │                                 │
│  └─────────────┘                   │ total_tokens      │                                 │
│                                    └───────────────────┘                                 │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    USAGE & BILLING                                       │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────────┐               ┌─────────────────┐                                   │
│  │   UsageRecord   │               │  UsageSummary   │                                   │
│  │─────────────────│               │─────────────────│                                   │
│  │ id (UUID)       │               │ id (UUID)       │                                   │
│  │ user_id         │               │ user_id         │                                   │
│  │ request_type    │               │ period          │ (YYYY-MM)                         │
│  │ model           │               │ total_requests  │                                   │
│  │ tokens_in/out   │               │ total_tokens    │                                   │
│  │ cost            │               │ total_credits   │                                   │
│  │ credits_used    │               │ total_cost      │                                   │
│  │ latency_ms      │               │ breakdown by    │                                   │
│  │ conversation_id │               │ request type    │                                   │
│  │ agent_id        │               └─────────────────┘                                   │
│  │ litellm_call_id │                                                                     │
│  └─────────────────┘                                                                     │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    SYSTEM & ADMIN                                        │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                          │
│  ┌─────────────┐   ┌─────────────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │  AuditLog   │   │NotificationPreference│   │Notification │   │   Setting   │          │
│  │─────────────│   │─────────────────────│   │─────────────│   │─────────────│          │
│  │ id          │   │ user_id             │   │ id          │   │ key         │          │
│  │ user_id     │   │ email_*             │   │ user_id     │   │ value       │          │
│  │ action      │   │ push_*              │   │ type        │   │ encrypted   │          │
│  │ resource    │   │ in_app_*            │   │ title       │   └─────────────┘          │
│  │ details{}   │   └─────────────────────┘   │ is_read     │                            │
│  └─────────────┘                             └─────────────┘                            │
│                                                                                          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Database Schema (SQLAlchemy Models)

| Model | Table | Key Fields | Relationships |
|-------|-------|------------|---------------|
| `User` | `users` | id, email, username, tier, is_superuser | projects, conversations, documents, agents, subscriptions, usage_* |
| `Project` | `projects` | id, name, user_id, privacy_level | user, conversations, project_documents, agents |
| `Document` | `documents` | id, filename, file_type, status, user_id | user, chunks, project_documents |
| `DocumentChunk` | `document_chunks` | id, document_id, content, embedding[768] | document |
| `Agent` | `agents` | id, name, slug, system_prompt, tools[], document_ids[] | user, project |
| `Conversation` | `conversations` | id, title, project_id, user_id | user, project, messages |
| `Message` | `messages` | id, conversation_id, role, content, tokens_used | conversation |
| `Workflow` | `workflows` | id, name, nodes[], edges[], status | user, executions |
| `WorkflowExecution` | `workflow_executions` | id, workflow_id, status, node_states{} | workflow, user |
| `Plan` | `plans` | id, name, plan_type, price, limits | subscriptions |
| `Subscription` | `subscriptions` | id, user_id, plan_id, status, stripe_id | user, plan, invoices |
| `Invoice` | `invoices` | id, subscription_id, amount, status | subscription, user |
| `UsageRecord` | `usage_records` | id, user_id, request_type, tokens, cost | user |
| `UsageSummary` | `usage_summaries` | id, user_id, period, totals | user |

### 2.3 Enums & Constants

```python
# Document Processing
class DocumentStatus(Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    error = "error"

# Agent Tools
class AgentTool(Enum):
    rag_search = "rag_search"
    summarize = "summarize"
    calculator = "calculator"
    web_search = "web_search"

# Agent Source
class AgentSource(Enum):
    system = "system"  # Pre-built from YAML
    user = "user"      # Created by users

# Workflow Nodes
class NodeType(Enum):
    start = "start"
    end = "end"
    llm = "llm"
    agent = "agent"
    rag = "rag"
    tool = "tool"
    condition = "condition"
    loop = "loop"
    custom_function = "custom_function"
    http = "http"

# Workflow/Execution Status
class WorkflowStatus(Enum):
    draft = "draft"
    active = "active"
    archived = "archived"

class ExecutionStatus(Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"

# Message Roles
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

# Project Privacy
class PrivacyLevel(Enum):
    STRICT = "strict"      # Full PII protection
    MODERATE = "moderate"  # Partial protection
    OFF = "off"            # No protection

# Subscription
class SubscriptionStatus(Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PAUSED = "paused"
    EXPIRED = "expired"

# Plan Types
class PlanType(Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"

# Usage Request Types
class RequestType(Enum):
    CHAT = "chat"
    RAG = "rag"
    AGENT = "agent"
    EMBEDDING = "embedding"
    IMAGE = "image"
    TOOL = "tool"
```

---

## 3. API Definition

### 3.1 API Overview

**Base URL:** `/api/v1`
**Authentication:** JWT Bearer Token
**Response Format:** `BaseResponse<T>` with `trace_id`

```json
{
  "trace_id": "abc123",
  "data": { ... },
  "error": null,
  "detail": null
}
```

### 3.2 API Endpoints

#### Authentication (`/auth`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login, get tokens | No |
| POST | `/auth/refresh` | Refresh access token | Yes |
| POST | `/auth/logout` | Logout, invalidate refresh | Yes |
| POST | `/auth/forgot-password` | Request password reset | No |
| POST | `/auth/reset-password` | Reset password | No |

#### Profile (`/profile`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/profile` | Get current user profile | Yes |
| PUT | `/profile` | Update profile | Yes |
| PUT | `/profile/password` | Change password | Yes |

#### Projects (`/projects`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/projects` | List user's projects | Yes |
| POST | `/projects` | Create new project | Yes |
| GET | `/projects/{id}` | Get project details | Yes |
| PUT | `/projects/{id}` | Update project | Yes |
| DELETE | `/projects/{id}` | Delete project | Yes |
| POST | `/projects/{id}/documents` | Add document to project | Yes |
| DELETE | `/projects/{id}/documents/{doc_id}` | Remove document from project | Yes |

#### Documents (`/documents`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/documents` | List user's documents | Yes |
| POST | `/documents/upload` | Upload document (multipart) | Yes |
| GET | `/documents/{id}` | Get document details | Yes |
| DELETE | `/documents/{id}` | Delete document | Yes |
| PUT | `/documents/{id}` | Update document metadata | Yes |
| POST | `/documents/{id}/reprocess` | Re-process document | Yes |
| GET | `/documents/{id}/chunks` | List document chunks | Yes |

#### Agents (`/agents`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/agents` | List all agents (system + user) | Yes |
| POST | `/agents` | Create new agent | Yes |
| GET | `/agents/{slug}` | Get agent by slug | Yes |
| PUT | `/agents/{slug}` | Update agent | Yes |
| DELETE | `/agents/{slug}` | Delete agent | Yes |

#### Conversations (`/conversations`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/conversations` | List conversations | Yes |
| POST | `/conversations` | Create new conversation | Yes |
| GET | `/conversations/{id}` | Get conversation with messages | Yes |
| DELETE | `/conversations/{id}` | Delete conversation | Yes |
| PUT | `/conversations/{id}` | Update conversation (title) | Yes |
| GET | `/conversations/search` | Full-text search messages | Yes |

#### Chat (`/chat`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/chat/stream` | Chat with streaming (SSE) | Yes |
| POST | `/chat/send` | Chat without streaming | Yes |

**Chat Request Body:**
```json
{
  "message": "string",
  "conversation_id": "uuid (optional)",
  "agent_slug": "string (optional)",
  "project_id": "uuid (optional)"
}
```

#### Workflows (`/workflows`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/workflows` | List user's workflows | Yes |
| POST | `/workflows` | Create new workflow | Yes |
| GET | `/workflows/{id}` | Get workflow details | Yes |
| PUT | `/workflows/{id}` | Update workflow (nodes, edges) | Yes |
| DELETE | `/workflows/{id}` | Delete workflow | Yes |
| POST | `/workflows/{id}/execute` | Execute workflow | Yes |
| GET | `/workflows/{id}/executions` | List execution history | Yes |
| GET | `/workflows/executions/{exec_id}` | Get execution details | Yes |
| POST | `/workflows/executions/{exec_id}/cancel` | Cancel running execution | Yes |

#### Billing (`/billing`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/billing/subscription` | Get current subscription | Yes |
| GET | `/billing/usage` | Get usage summary | Yes |
| GET | `/billing/invoices` | List invoices | Yes |
| POST | `/billing/checkout` | Create Stripe checkout session | Yes |
| POST | `/billing/portal` | Create Stripe customer portal | Yes |

#### Notifications (`/notifications`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/notifications` | List notifications | Yes |
| PUT | `/notifications/{id}/read` | Mark as read | Yes |
| PUT | `/notifications/read-all` | Mark all as read | Yes |
| GET | `/notifications/preferences` | Get preferences | Yes |
| PUT | `/notifications/preferences` | Update preferences | Yes |

#### Webhooks (`/webhooks`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/webhooks/stripe` | Handle Stripe webhooks | Stripe Signature |

#### Health (`/health`)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Basic health check | No |
| GET | `/health/detailed` | Detailed health (DB, Redis, LiteLLM) | Admin |

### 3.3 Admin APIs (`/admin`)

| Router | Endpoints | Description |
|--------|-----------|-------------|
| `/admin/users` | CRUD users, manage roles | User management |
| `/admin/plans` | CRUD plans | Plan management |
| `/admin/subscriptions` | View/manage subscriptions | Subscription admin |
| `/admin/usage` | View usage across users | Usage analytics |
| `/admin/audit` | View audit logs | Audit trail |
| `/admin/settings` | Manage system settings | System config |
| `/admin/system` | System health, LiteLLM keys | System admin |
| `/admin/notifications` | Send notifications to users | Notification admin |
| `/admin/dashboard` | Dashboard stats | Overview stats |

---

## 4. Component Structure

### 4.1 Backend Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings (Pydantic)
│   │
│   ├── core/                   # Core utilities
│   │   ├── database.py         # SQLAlchemy engine, session
│   │   ├── context.py          # Request context (trace_id)
│   │   ├── exceptions.py       # Custom exceptions
│   │   ├── telemetry.py        # OpenTelemetry setup
│   │   └── security.py         # JWT, password hashing
│   │
│   ├── middleware/             # FastAPI middleware
│   │   ├── __init__.py
│   │   └── trace.py            # TraceContext, Metrics
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py             # TimestampMixin
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── chunk.py
│   │   ├── agent.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── workflow.py
│   │   ├── plan.py
│   │   ├── subscription.py
│   │   ├── invoice.py
│   │   ├── usage.py
│   │   ├── notification.py
│   │   ├── notification_preference.py
│   │   ├── audit_log.py
│   │   └── setting.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── base.py             # BaseResponse, ErrorResponse
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── agent.py
│   │   ├── chat.py
│   │   ├── conversation.py
│   │   ├── workflow.py
│   │   ├── billing.py
│   │   └── notification.py
│   │
│   ├── routes/                 # API routes
│   │   ├── __init__.py
│   │   ├── health.py
│   │   ├── auth.py
│   │   ├── profile.py
│   │   ├── projects.py
│   │   ├── documents.py
│   │   ├── agents.py
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   ├── workflows.py
│   │   ├── billing.py
│   │   ├── notifications.py
│   │   ├── webhooks.py
│   │   └── admin/              # Admin routes
│   │       ├── users.py
│   │       ├── plans.py
│   │       ├── subscriptions.py
│   │       ├── usage.py
│   │       ├── audit.py
│   │       ├── settings.py
│   │       ├── system.py
│   │       ├── notifications.py
│   │       └── dashboard.py
│   │
│   └── services/               # Business logic
│       ├── __init__.py
│       ├── auth.py
│       ├── project.py
│       ├── document.py
│       ├── document_processor.py
│       ├── agent.py
│       ├── agent_loader.py     # Load system agents from YAML
│       ├── conversation.py
│       ├── rag.py              # RAG orchestration
│       ├── embedding.py        # Embedding via LiteLLM
│       ├── vector_store.py     # pgvector operations
│       ├── workflow.py
│       ├── workflow_engine.py  # Execute workflow nodes
│       ├── subscription.py
│       ├── stripe_service.py
│       ├── usage.py
│       ├── quota.py
│       ├── notification.py
│       ├── audit_log.py
│       ├── settings.py
│       ├── storage.py          # File storage (local/S3)
│       ├── litellm_keys.py     # LiteLLM API key management
│       ├── system_health.py
│       ├── admin_users.py
│       ├── admin_usage.py
│       └── admin_stats.py
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/                      # Test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_documents.py
│   └── ...
│
├── pyproject.toml              # Dependencies (uv)
└── alembic.ini
```

### 4.2 Frontend Structure

```
frontend/
├── src/
│   ├── app.html                # HTML template
│   ├── app.css                 # Global styles (Tailwind)
│   │
│   ├── lib/
│   │   ├── index.ts
│   │   ├── utils.ts            # Utility functions
│   │   │
│   │   ├── api/                # API client modules
│   │   │   ├── index.ts
│   │   │   ├── client.ts       # Base fetch wrapper
│   │   │   ├── auth.ts
│   │   │   ├── chat.ts
│   │   │   ├── agents.ts
│   │   │   ├── documents.ts
│   │   │   ├── projects.ts
│   │   │   ├── conversations.ts
│   │   │   ├── workflows.ts
│   │   │   ├── billing.ts
│   │   │   ├── profile.ts
│   │   │   ├── notifications.ts
│   │   │   └── admin.ts
│   │   │
│   │   ├── stores/             # Svelte 5 Runes stores
│   │   │   ├── index.ts
│   │   │   ├── auth.svelte.ts
│   │   │   ├── projects.svelte.ts
│   │   │   ├── agents.svelte.ts
│   │   │   ├── chats.svelte.ts
│   │   │   ├── sidebar.svelte.ts
│   │   │   └── notifications.svelte.ts
│   │   │
│   │   ├── types/              # TypeScript types
│   │   │   ├── index.ts
│   │   │   └── api.ts
│   │   │
│   │   └── components/         # Reusable components
│   │       ├── ui/             # shadcn-svelte components
│   │       │   ├── button/
│   │       │   ├── card/
│   │       │   ├── dialog/
│   │       │   ├── input/
│   │       │   ├── select/
│   │       │   ├── table/
│   │       │   ├── tabs/
│   │       │   └── ... (more UI primitives)
│   │       │
│   │       ├── layout/         # Layout components
│   │       │   ├── Sidebar.svelte
│   │       │   ├── Header.svelte
│   │       │   └── index.ts
│   │       │
│   │       ├── chat/           # Chat components
│   │       │   ├── ChatMessage.svelte
│   │       │   ├── ChatInput.svelte
│   │       │   └── index.ts
│   │       │
│   │       ├── workflow/       # Workflow builder
│   │       │   ├── WorkflowCanvas.svelte
│   │       │   └── nodes/
│   │       │       ├── StartNode.svelte
│   │       │       ├── EndNode.svelte
│   │       │       ├── LLMNode.svelte
│   │       │       ├── AgentNode.svelte
│   │       │       ├── RAGNode.svelte
│   │       │       ├── HTTPNode.svelte
│   │       │       ├── ConditionNode.svelte
│   │       │       └── index.ts
│   │       │
│   │       ├── landing/        # Landing page components
│   │       ├── notifications/  # Notification components
│   │       └── icons/          # Icon components
│   │
│   └── routes/                 # SvelteKit routes
│       ├── +layout.svelte      # Root layout
│       ├── +page.svelte        # Landing page
│       │
│       ├── login/
│       │   └── +page.svelte
│       │
│       ├── register/
│       │   └── +page.svelte
│       │
│       ├── (app)/              # Protected app routes
│       │   ├── +layout.svelte  # App layout (sidebar)
│       │   │
│       │   ├── chat/
│       │   │   ├── +page.svelte
│       │   │   └── [id]/+page.svelte
│       │   │
│       │   ├── chats/
│       │   │   └── +page.svelte
│       │   │
│       │   ├── agents/
│       │   │   ├── +page.svelte
│       │   │   ├── new/+page.svelte
│       │   │   └── [slug]/
│       │   │       ├── +page.svelte
│       │   │       └── edit/+page.svelte
│       │   │
│       │   ├── documents/
│       │   │   ├── +page.svelte
│       │   │   └── [id]/+page.svelte
│       │   │
│       │   ├── projects/
│       │   │   ├── +page.svelte
│       │   │   └── [id]/+page.svelte
│       │   │
│       │   ├── workflows/
│       │   │   ├── +page.svelte
│       │   │   └── [id]/+page.svelte
│       │   │
│       │   ├── billing/
│       │   │   ├── success/+page.svelte
│       │   │   └── cancel/+page.svelte
│       │   │
│       │   ├── settings/
│       │   │   └── +page.svelte
│       │   │
│       │   ├── notifications/
│       │   │   └── +page.svelte
│       │   │
│       │   └── images/
│       │       └── +page.svelte
│       │
│       ├── (admin)/            # Admin routes
│       │   └── admin/
│       │       ├── +page.svelte
│       │       ├── users/
│       │       │   ├── +page.svelte
│       │       │   └── [id]/+page.svelte
│       │       ├── plans/+page.svelte
│       │       ├── subscriptions/+page.svelte
│       │       ├── usage/+page.svelte
│       │       ├── audit/+page.svelte
│       │       ├── settings/+page.svelte
│       │       └── system/+page.svelte
│       │
│       └── (public)/           # Public pages
│           ├── about/+page.svelte
│           ├── pricing/+page.svelte
│           ├── changelog/+page.svelte
│           ├── privacy/+page.svelte
│           ├── terms/+page.svelte
│           └── contact/+page.svelte
│
├── static/                     # Static assets
├── svelte.config.js
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## 5. Third-party Integrations

### 5.1 Required Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **PostgreSQL 16** | Main database | `DATABASE_URL` |
| **pgvector** | Vector storage for embeddings | PostgreSQL extension |
| **Redis** | Rate limiting, caching | `REDIS_HOST`, `REDIS_PORT` |
| **LiteLLM Proxy** | Multi-LLM gateway | `LITELLM_API_URL`, `LITELLM_API_KEY` |

### 5.2 LLM Providers (via LiteLLM)

| Provider | Models | Use Case |
|----------|--------|----------|
| **Google** | Gemini 2.5 Pro, Gemini 2.5 Flash, text-embedding-004 | Chat, RAG, Embeddings |

### 5.3 Payment (Stripe)

| Integration | Purpose |
|-------------|---------|
| Checkout Sessions | Subscription purchase |
| Customer Portal | Manage subscription |
| Webhooks | Handle payment events |
| Products & Prices | Plan definitions |

**Required Env Vars:**
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PUBLISHABLE_KEY`

### 5.4 Observability

#### Backend: OpenTelemetry (OTEL)

ส่ง **traces, logs, metrics** ผ่าน OTEL Collector เท่านั้น

| Signal | Description | Export Target |
|--------|-------------|---------------|
| **Traces** | Distributed tracing (requests, DB, LLM calls) | OTEL Collector → Jaeger/Tempo |
| **Logs** | Structured logging (JSON format) | OTEL Collector → Loki/Elasticsearch |
| **Metrics** | Application metrics (latency, throughput) | OTEL Collector → Prometheus |

```
Backend → OTEL Collector → Multiple Backends
              │
              ├── Traces  → Jaeger / Tempo
              ├── Logs    → Loki / Elasticsearch
              └── Metrics → Prometheus
```

**Required Env Vars:**
- `OTEL_ENABLED` - Enable/disable OTEL
- `OTEL_EXPORTER_ENDPOINT` - OTEL Collector endpoint (gRPC)
- `OTEL_SERVICE_NAME` - Service name for traces

#### Frontend: Glitchtip

ใช้ **Glitchtip** (Sentry-compatible) สำหรับ error tracking และ performance monitoring

| Feature | Description |
|---------|-------------|
| **Error Tracking** | Capture JS errors, unhandled rejections |
| **Performance** | Page load, API call timing |
| **User Context** | Track user sessions, breadcrumbs |
| **Source Maps** | Map minified code to source |

**Required Env Vars:**
- `PUBLIC_GLITCHTIP_DSN` - Glitchtip DSN for frontend

### 5.5 File Storage

| Type | Implementation |
|------|----------------|
| **Local** (Dev) | `./uploads` directory |
| **S3** (Prod) | AWS S3 or compatible (MinIO) |

### 5.6 Python Libraries

| Library | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy[asyncio]` | Async ORM |
| `asyncpg` | PostgreSQL driver |
| `pydantic-settings` | Settings management |
| `python-jose` | JWT handling |
| `passlib[bcrypt]` | Password hashing |
| `litellm` | LLM API client |
| `pgvector` | Vector operations |
| `python-multipart` | File uploads |
| `stripe` | Payment integration |
| `opentelemetry-*` | Observability |
| `redis` | Redis client |
| `alembic` | Database migrations |

### 5.7 Frontend Libraries

| Library | Purpose |
|---------|---------|
| `@sveltejs/kit` | SvelteKit framework |
| `svelte` | UI framework (v5 Runes) |
| `tailwindcss` | CSS framework (v4) |
| `shadcn-svelte` | UI components |
| `@xyflow/svelte` | Workflow canvas |
| `lucide-svelte` | Icons |
| `mode-watcher` | Dark mode |
| `bits-ui` | Headless UI primitives |
| `@sentry/svelte` | Glitchtip/Sentry SDK (error tracking) |

---

## 6. Security & Scalability

### 6.1 Authentication & Authorization

| Layer | Implementation |
|-------|----------------|
| **Auth Method** | JWT (Access + Refresh tokens) |
| **Access Token** | 30 min expiry, HS256 |
| **Refresh Token** | 7 days expiry |
| **Password** | bcrypt hashing |
| **Admin Check** | `is_superuser` field |

### 6.2 Security Measures

| Concern | Mitigation |
|---------|------------|
| **XSS** | React/Svelte auto-escaping, CSP headers |
| **CSRF** | SameSite cookies, CORS configuration |
| **SQL Injection** | SQLAlchemy ORM, parameterized queries |
| **Prompt Injection** | Input sanitization, monitoring |
| **PII Protection** | Privacy level settings per project |
| **Rate Limiting** | Redis-based (via LiteLLM) |
| **API Keys** | Encrypted storage, rotation support |

### 6.3 CORS Configuration

```python
cors_origins: list[str] = [
    "http://localhost:5173",  # Dev frontend
    "http://localhost:3000",
    # Production domains added via env
]
```

### 6.4 Rate Limiting (via LiteLLM)

| Plan | Requests/min | Requests/day |
|------|--------------|--------------|
| Free | 10 | 1,000 |
| Pro | 60 | 10,000 |
| Enterprise | Unlimited | Unlimited |

### 6.5 Scalability Considerations

#### Horizontal Scaling
```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Backend Pod 1  │ │  Backend Pod 2  │ │  Backend Pod 3  │
└─────────────────┘ └─────────────────┘ └─────────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
              ┌─────▼─────┐    ┌──────▼──────┐
              │ PostgreSQL │    │    Redis    │
              │  (Primary) │    │   Cluster   │
              └─────┬─────┘    └─────────────┘
                    │
              ┌─────▼─────┐
              │ PostgreSQL │
              │  (Replica) │
              └───────────┘
```

#### Performance Optimizations

| Area | Strategy |
|------|----------|
| **Database** | Connection pooling, read replicas, indexing |
| **Vector Search** | HNSW index on pgvector, limit top-k |
| **Caching** | Redis for sessions, frequent queries |
| **Static Files** | CDN for frontend assets |
| **Background Tasks** | Document processing in background workers |
| **Streaming** | SSE for chat responses |

#### Database Indexes

```sql
-- Key indexes for performance
CREATE INDEX ix_documents_user_status ON documents(user_id, status);
CREATE INDEX ix_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX ix_chunks_document ON document_chunks(document_id);
CREATE INDEX ix_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ix_usage_user_created ON usage_records(user_id, created_at);
```

### 6.6 Monitoring & Alerting

| Metric | Threshold | Alert |
|--------|-----------|-------|
| API Latency P99 | > 2s | Critical |
| Error Rate | > 5% | Warning |
| Database Connections | > 80% pool | Warning |
| Memory Usage | > 85% | Warning |
| LLM Provider Errors | > 10/min | Critical |

---

## Notes

เอกสารนี้เป็น Technical Plan ที่สร้างจากการวิเคราะห์ codebase ปัจจุบัน พร้อมทั้งอ้างอิง Product Specification (01-spec.md)

**ขั้นตอนถัดไป:**
1. ใช้ `/task` เพื่อแตกงานออกเป็น Development Tasks
2. แต่ละ task ควรเป็น small, testable units
3. เรียงลำดับตาม dependency order
