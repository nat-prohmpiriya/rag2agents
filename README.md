# RAG Agent Platform

A production-ready AI platform for building intelligent agents with Retrieval-Augmented Generation (RAG), visual workflow automation, and multi-model LLM support.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![SvelteKit](https://img.shields.io/badge/SvelteKit-2.x-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)

## Overview

RAG Agent Platform enables developers and businesses to create AI-powered assistants that understand context from internal documents, execute automated workflows, and integrate with multiple LLM providers - all without complex infrastructure management.

### Key Features

- **RAG Pipeline** - Upload documents (PDF, DOCX, TXT, MD, CSV), auto-chunk, embed, and retrieve with vector similarity search
- **Visual Workflow Builder** - Drag-and-drop canvas with 10+ node types (LLM, Agent, RAG, HTTP, Condition, Loop, etc.)
- **Multi-Model Support** - Switch between OpenAI, Anthropic, Gemini, and Groq via LiteLLM
- **Real-time Streaming** - Server-Sent Events (SSE) for live chat responses
- **Subscription Billing** - Stripe integration with plans, checkout, and customer portal
- **Enterprise Security** - JWT auth, rate limiting, audit logs, and OpenTelemetry observability

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend                                  │
│              SvelteKit 2 + Svelte 5 + Tailwind v4               │
│                    shadcn-svelte UI                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API + SSE Streaming
┌─────────────────────────▼───────────────────────────────────────┐
│                      Backend API                                 │
│                 FastAPI + Python 3.12+                          │
│         Routes → Services → Models → Providers                   │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
│ PostgreSQL  │ │  LiteLLM  │ │   Redis   │ │  Stripe   │
│  + pgvector │ │   Proxy   │ │   Cache   │ │  Billing  │
│  (vectors)  │ │ (OpenAI/  │ │  (rate    │ │           │
│             │ │  Gemini/  │ │  limiting)│ │           │
│             │ │  Groq)    │ │           │ │           │
└─────────────┘ └───────────┘ └───────────┘ └───────────┘
```

### Data Flow: RAG Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Upload  │───▶│ Chunking │───▶│ Embedding│───▶│  Store   │
│  (PDF,   │    │ (text    │    │ (LiteLLM │    │ (pgvector│
│  DOCX)   │    │  splits) │    │  API)    │    │  768-dim)│
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                     │
┌──────────┐    ┌──────────┐    ┌──────────┐         │
│ Response │◀───│   LLM    │◀───│ Retrieve │◀────────┘
│ (with    │    │ (context │    │ (top-k   │
│  sources)│    │  +query) │    │  similar)│
└──────────┘    └──────────┘    └──────────┘
```

## Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| SvelteKit 2.x | Full-stack framework |
| Svelte 5 (Runes) | Reactive UI with `$state`, `$derived`, `$props` |
| Tailwind CSS v4 | Utility-first styling |
| shadcn-svelte | UI component library |
| XYFlow | Workflow diagram canvas |
| PDF.js | Document viewer |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | Async REST API |
| Python 3.12+ | Modern type hints (`X \| None`) |
| SQLAlchemy 2.0 | Async ORM |
| PostgreSQL 16 | Primary database |
| pgvector | Vector similarity search |
| Pydantic v2 | Request/response validation |

### AI & Infrastructure
| Technology | Purpose |
|------------|---------|
| LiteLLM | Unified LLM API (OpenAI, Gemini, Groq) |
| OpenTelemetry | Distributed tracing & observability |
| Redis | Rate limiting & caching |
| Stripe | Payment processing |
| Docker Compose | Container orchestration |

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

### Quick Start

1. **Clone and setup environment**
   ```bash
   git clone https://github.com/yourusername/rag2agents.git
   cd rag2agents
   cp backend/.env.example backend/.env
   ```

2. **Start infrastructure services**
   ```bash
   docker compose up -d
   ```

3. **Setup backend**
   ```bash
   cd backend
   uv sync
   uv run alembic upgrade head
   uv run uvicorn app.main:app --reload --port 8000
   ```

4. **Setup frontend** (new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Project Structure

```
rag2agents/
├── frontend/                 # SvelteKit application
│   ├── src/
│   │   ├── routes/          # Pages & API routes
│   │   ├── lib/
│   │   │   ├── components/  # UI components
│   │   │   │   ├── ui/      # shadcn-svelte
│   │   │   │   └── custom/  # Business components
│   │   │   ├── api/         # API client
│   │   │   └── stores/      # Svelte stores
│   │   └── app.css          # Tailwind styles
│   └── package.json
│
├── backend/                  # FastAPI application
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── models/          # SQLAlchemy ORM
│   │   ├── schemas/         # Pydantic models
│   │   └── core/            # Config & security
│   ├── tests/               # Pytest tests
│   ├── alembic/             # DB migrations
│   └── pyproject.toml
│
├── docker-compose.yml       # Infrastructure services
└── README.md
```

## API Highlights

### Authentication
```http
POST /api/v1/auth/register    # User registration
POST /api/v1/auth/login       # JWT token generation
POST /api/v1/auth/refresh     # Token refresh
```

### Documents & RAG
```http
POST /api/v1/documents        # Upload document
GET  /api/v1/documents/{id}/chunks  # Get document chunks
POST /api/v1/chat/stream      # Chat with RAG (SSE)
```

### Agents & Workflows
```http
POST /api/v1/agents           # Create custom agent
POST /api/v1/workflows        # Create workflow
POST /api/v1/workflows/{id}/execute  # Execute workflow
```

### Billing
```http
POST /api/v1/billing/checkout # Create Stripe checkout
GET  /api/v1/billing/portal   # Customer portal URL
GET  /api/v1/billing/plans    # Available plans
```

## Features in Detail

### 1. Document Management
- Multi-format support: PDF, DOCX, TXT, Markdown, CSV
- Automatic chunking with configurable size
- Status tracking: `pending → processing → ready`
- Tag-based organization

### 2. AI Agents
- Custom system prompts and personalities
- Tool selection (RAG search, summarize, calculator)
- Document linking for knowledge base
- System vs User agent types

### 3. Visual Workflows
- 10+ node types for complex automation
- Real-time execution tracking
- Conditional branching and loops
- HTTP requests and custom functions

### 4. Security & Observability
- JWT authentication with refresh tokens
- Rate limiting per endpoint
- Audit logging for compliance
- OpenTelemetry tracing integration

## Testing

```bash
# Backend tests
cd backend
uv run pytest -v

# Frontend type checking
cd frontend
npm run check
```

## Environment Variables

### Backend (`backend/.env`)
```env
# Required
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ragagent
JWT_SECRET_KEY=your-secret-key-min-32-chars

# Optional
LITELLM_API_BASE=http://localhost:4000
STRIPE_SECRET_KEY=sk_test_...
REDIS_HOST=localhost
OTEL_ENABLED=false
```

## Roadmap

- [ ] Firebase/OAuth authentication
- [ ] Multi-language support (i18n)
- [ ] E2E testing with Playwright
- [ ] Kubernetes deployment manifests
- [ ] AI image generation integration
- [ ] Team collaboration features

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## License

MIT License - see [LICENSE](LICENSE) for details.

---

Built with modern full-stack architecture emphasizing type safety, async patterns, and production-ready practices.
