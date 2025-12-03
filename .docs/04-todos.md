# RAG Agent Platform - Development Todos

## Document Info

| | |
|--|--|
| **Version** | 2.0 |
| **Date** | December 2024 |
| **Status** | In Progress |
| **Spec Version** | v3 (synced) |

---

## Current Progress Overview

| Component | Status | Notes |
|-----------|--------|-------|
| LiteLLM Proxy | ✅ Done | Running on port 4000, UI available |
| Frontend (SvelteKit) | ✅ Done | Svelte 5 + Tailwind v4 + shadcn-svelte (Phase 1 Complete) |
| Backend (FastAPI) | ✅ Done | Auth + Chat + RAG API (Phase 2 Complete) |
| PostgreSQL + pgvector | ✅ Done | Running in docker with vector support |
| Redis | ✅ Done | Running for LiteLLM cache |
| Vector Store | ✅ Done | pgvector (replaced ChromaDB) |
| Auth System | ✅ Done | JWT + refresh token |
| Chat System | ✅ Done | Streaming, History, Settings, Markdown |
| Conversation API | ✅ Done | CRUD + Messages |
| RAG Pipeline | ✅ Done | Document upload, chunking, embedding, retrieval |
| Project System | ✅ Done | CRUD, Document Assignment, RAG Filtering |
| PII Protection | ❌ Not Started | Presidio integration |
| Agent System | 🔄 In Progress | Backend done, UI done, User agents pending |
| Text-to-SQL | ❌ Not Started | Schema Linking + User Confirm |
| Fine-tuning | ❌ Not Started | Job Dispatcher pattern |

---

## Phase 1: Foundation (Infrastructure & Basic App)

### 1.1 Infrastructure Setup
- [x] Setup LiteLLM Docker Compose
- [x] Create LiteLLM config (Gemini + Groq models)
- [x] Generate environment variables script
- [x] Test LiteLLM proxy connection
- [x] Setup PostgreSQL in docker-compose
- [x] Setup Redis (for LiteLLM cache)
- [x] Verify all containers run together
- [x] Setup LiteLLM UI credentials

### 1.2 Backend Setup (FastAPI)
- [x] Initialize FastAPI project structure
- [x] Setup project dependencies (pyproject.toml with uv)
- [x] Create main.py entrypoint
- [x] Setup CORS middleware
- [x] Create health check endpoint
- [x] Setup database connection (SQLAlchemy async + PostgreSQL)
- [x] Create Alembic migrations setup
- [x] Create base database models (User, Project, Conversation)
- [x] Setup environment configuration (pydantic-settings)

### 1.3 Authentication System
- [x] Create User model & schema
- [x] Implement password hashing (bcrypt)
- [x] Create JWT token utilities
- [x] Implement register endpoint
- [x] Implement login endpoint
- [x] Implement logout endpoint
- [x] Create auth middleware
- [x] Implement /me endpoint (get current user)
- [x] Add refresh token support

### 1.4 Frontend Setup (SvelteKit)
- [x] Initialize SvelteKit project
- [x] Setup Tailwind CSS v4
- [x] Setup i18n (Paraglide)
- [x] Initialize shadcn-svelte
- [x] Add base UI components (Button, Card, Input, Dialog)
- [x] Create base layout component
- [x] Create navigation/header component
- [x] Create sidebar component
- [x] Setup API client (fetch wrapper)
- [x] Create auth store (Svelte stores with runes)
- [x] Implement login page
- [x] Implement register page
- [x] Add protected route logic

### 1.5 Basic Chat Integration
- [x] Create LiteLLM client wrapper in backend
- [x] Implement /chat endpoint (non-streaming)
- [x] Implement /chat/stream endpoint (SSE streaming)
- [x] Create ChatWindow component
- [x] Implement message input component
- [x] Implement message display (markdown support)
- [x] Add code syntax highlighting
- [x] Connect frontend to backend chat API
- [x] Test end-to-end chat flow

### 1.6 Chat Settings UI (Frontend)
- [x] Create ChatSettings component
- [x] Add model selector dropdown (6 models: Gemini + Groq)
- [x] Add temperature slider (0.0 - 2.0)
- [x] Add max tokens input (optional, 100-4096)
- [x] Integrate settings with chat API request
- [x] Test model switching and parameter changes

### 1.7 Chat History & Sidebar (Frontend)
- [x] Create conversations API client
- [x] Create ChatHistorySidebar component (grouped by date)
- [x] Create ChatLayout wrapper component
- [x] Add /chat route (new chat)
- [x] Add /chat/[id] route (chat detail)
- [x] Implement collapsible main sidebar with tooltips
- [x] Add sidebar state persistence (localStorage)
- [x] Implement streaming performance optimization (throttled scroll)
- [x] Add markdown rendering for assistant messages

### 1.8 Chat Enhancements (Backlog)
- [ ] Auto-generate conversation title from first message
- [ ] Add code syntax highlighting (Prism.js/Shiki)
- [ ] Add system prompt per conversation (instruction/personality)
- [ ] Show message timestamps in UI
- [ ] Add message copy button
- [ ] Add regenerate response button

**Phase 1 Deliverable**: User can register, login, and chat with AI

---

## Phase 2: RAG Core (Document & Retrieval)

### 2.1 Document Processing
- [x] Setup pgvector in PostgreSQL (replaced ChromaDB)
- [x] Create document upload endpoint
- [x] Implement file validation (PDF, DOCX, TXT, MD, CSV)
- [x] Integrate PDF text extraction (PyMuPDF)
- [x] Integrate DOCX text extraction (python-docx)
- [x] Create text chunking service (recursive splitter)
- [x] Add metadata extraction

### 2.2 Embedding & Vector Store
- [x] Setup LiteLLM embedding API (replaced sentence-transformers)
- [x] Use Gemini text-embedding-004 model (768 dims)
- [x] Create embedding service
- [x] Implement pgvector for vector storage (replaced ChromaDB)
- [x] Create document indexing pipeline
- [x] Implement document deletion (remove from vector store)

### 2.3 Retrieval Pipeline
- [x] Implement dense search (cosine similarity with pgvector)
- [x] Implement document scope filter (rag_document_ids)
- [ ] Implement hybrid search (Dense + BM25) - optional
- [x] Create query preprocessing
- [x] Implement context assembly
- [ ] Add re-ranking (optional)
- [ ] Add query expansion (optional)
- [ ] Add chunk overlap in chunking (optional)
- [ ] Add metadata filtering (date, file type) - optional
- [ ] Add RAG evaluation metrics (precision/recall) - optional
- [x] Create RAG prompt template

### 2.4 Source Citations
- [x] Track source documents in retrieval
- [x] Include sources in LLM response
- [x] Parse and display sources in frontend
- [x] Link to original document/page

### 2.5 Document Management UI
- [x] Create document list component
- [x] Implement document upload UI (drag & drop)
- [x] Show upload progress
- [x] Display document status (processing, ready, error)
- [x] Implement document delete UI

**Phase 2 Deliverable**: User can upload documents and ask questions with RAG

---

## Phase 3: PII Protection (Privacy & Safety)

### 3.1 Presidio Integration
- [ ] Install Microsoft Presidio (analyzer + anonymizer)
- [ ] Create PIIScrubber service class
- [ ] Implement Thai PII recognizers (phone, ID card, name)
- [ ] Create custom recognizers for medical records

### 3.2 PII Middleware
- [ ] Create PII scrubber middleware
- [ ] Implement privacy level settings (strict/moderate/off)
- [ ] Add PII mapping storage (for potential restoration)
- [ ] Create encrypted audit logging

### 3.3 Privacy Settings UI
- [ ] Add privacy level selector per project
- [ ] Create PII indicator component (show when PII detected)
- [ ] Implement admin PII audit dashboard
- [ ] Add PII stats visualization

**Phase 3 Deliverable**: All queries scrubbed before LLM, audit trail available

---

## Phase 4: Agent System

### 4.1 Agent Core (Backend)
- [x] Create Agent model & schema
- [x] Implement agent configuration loader (YAML)
- [x] Create agent registry (TOOL_REGISTRY)
- [x] Implement agent execution engine (AgentEngine)
- [x] Add tool execution framework (BaseTool)
- [x] Create agent routes (list, get, tools)
- [x] Integrate agent_slug with chat endpoint

### 4.2 Built-in Tools
- [x] Create RAG search tool
- [ ] Create summarize tool
- [ ] Create calculator tool
- [ ] Create web search tool (optional)

### 4.3 Pre-built System Agents (YAML)
- [x] Create General agent (general.yaml)
- [ ] Create HR agent (hr.yaml)
- [ ] Create Legal agent (legal.yaml)
- [x] Create Finance agent (finance.yaml)
- [ ] Create Research agent (research.yaml)
- [ ] Create Mental Health agent (mental_health.yaml) - PII-safe

### 4.4 Agent UI (Frontend)
- [x] Create Agent API client (agents.ts)
- [x] Create Agent store (agents.svelte.ts)
- [x] Create AgentSelector component (dropdown)
- [x] Create AgentCard component
- [x] Create AgentThinking component (step-by-step display)
- [x] Integrate AgentSelector into ChatHeader
- [x] Pass agent_slug in chat requests
- [x] Create Agents page (/agents)
- [x] Add Agents link to Sidebar

### 4.5 User-Created Agents ⭐ NEW
- [ ] Update Agent model with user_id, document_ids, project_id
- [ ] Create agent CRUD API (POST/PUT/DELETE)
- [ ] Create AgentForm component (create/edit)
- [ ] Add "New Agent" button on Agents page
- [ ] Implement document linking in agent form
- [ ] Implement project scoping

**Phase 4 Deliverable**: User can select different agents for different tasks, create custom agents

---

## Phase 5: Text-to-SQL with Schema Linking

### 5.1 Database Connection Management
- [ ] Create DatabaseConnection model
- [ ] Implement secure connection storage
- [ ] Create connection test endpoint
- [ ] Support PostgreSQL and MySQL

### 5.2 Schema Linking (RAG on Schema)
- [ ] Extract schema metadata from connected databases
- [ ] Create schema embedding service
- [ ] Build schema vector index
- [ ] Implement relevant table finder
- [ ] Create schema pruning logic

### 5.3 SQL Generation
- [ ] Create SQL generator with pruned schema
- [ ] Implement SQL validation (SELECT only)
- [ ] Add safety checks (no DROP, DELETE, etc.)
- [ ] Create query explanation generator

### 5.4 User Confirmation UI
- [ ] Create SQLConfirm component
- [ ] Display generated SQL with syntax highlighting
- [ ] Show affected tables and estimated rows
- [ ] Add Edit/Execute/Cancel buttons
- [ ] Implement "Don't ask again" option

### 5.5 Safe Execution
- [ ] Create read-only database executor
- [ ] Implement query timeout (30 seconds)
- [ ] Add row limit (1000 rows)
- [ ] Create result formatter (table/chart)

**Phase 5 Deliverable**: User can query database safely with confirmation

---

## Phase 6: Project System

### 6.1 Project Backend (MVP)
- [x] Update Project model (already exists, verify fields)
- [x] Create ProjectDocument junction table (many-to-many)
- [x] Add project_id to Conversation (optional FK, one-to-many)
- [x] Implement project CRUD API
- [x] Implement assign/remove documents to project API
- [x] Update RAG to filter by project (optional scope)
- [x] Create database migration

### 6.2 Project UI (MVP)
- [x] Create project list in sidebar
- [x] Implement create/edit project dialog
- [x] Add project switching
- [x] Create project detail page (show documents/conversations)
- [x] Implement assign documents UI
- [x] Filter chat by project context

### 6.3 Conversation Management
- [x] Create Conversation model
- [x] Create Message model
- [x] Implement conversation CRUD API
- [x] Add conversation history retrieval
- [ ] Implement context window management (later)
- [ ] Add conversation summarization (later)

### 6.4 Project Enhancements (Later - NOT MVP)
- [ ] Team/Multi-user support (ProjectMember, roles, permissions)
- [ ] Project settings (privacy level, default agent)
- [ ] Project archive/restore (soft delete)
- [ ] Project templates
- [ ] Bulk assign documents
- [ ] Project search/filter
- [ ] Project stats (doc count, usage)

**Phase 6 MVP Deliverable**: User can organize documents into projects, RAG scoped by project

---

## Phase 7: Fine-tuning Module (Job Dispatcher)

### 7.1 Job Dispatcher API
- [ ] Create FinetuneJob model
- [ ] Implement job CRUD endpoints
- [ ] Create job queue (PostgreSQL-based)
- [ ] Add job status tracking (pending/running/completed/failed)
- [ ] Create worker poll endpoint (/jobs/pending)

### 7.2 Training Data Preparation
- [ ] Create training data upload endpoint
- [ ] Implement data validation
- [ ] Create data format converters
- [ ] Add data storage (for worker download)

### 7.3 GPU Cloud Integration
- [ ] Create Colab worker notebook template
- [ ] Implement Hugging Face Hub integration
- [ ] Add Weights & Biases tracking
- [ ] Create model deployment flow

### 7.4 Fine-tuning UI
- [ ] Create fine-tuning dashboard
- [ ] Implement job creation form
- [ ] Add job status display
- [ ] Show training logs/metrics
- [ ] Create model deployment button

**Phase 7 Deliverable**: User can create training jobs, track progress, use trained models

---

## Phase 8: Polish & Production

### 8.1 Usage Tracking
- [ ] Create usage tracking service
- [ ] Track token usage per user
- [ ] Track request count per user
- [ ] Calculate cost per user
- [ ] Store usage history

### 8.2 Limits & Quotas
- [ ] Implement user tier system (Free/Pro/Enterprise)
- [ ] Add token quota (monthly)
- [ ] Add rate limiting (requests/minute)
- [ ] Add document upload limit
- [ ] Add project count limit
- [ ] Implement 80% usage warning
- [ ] Implement limit reached blocking

### 8.3 Debug Panel
- [ ] Create debug panel component (collapsible)
- [ ] Show retrieved chunks
- [ ] Display similarity scores
- [ ] Show retrieval latency
- [ ] Display token count
- [ ] Show cost estimation

### 8.4 Admin Panel
- [ ] Create admin routes (protected)
- [ ] Implement user list view
- [ ] Add user edit (tier, limits)
- [ ] Add user suspend/ban
- [ ] Create usage dashboard
- [ ] Add system metrics view
- [ ] Create PII audit viewer

### 8.5 Polish & Optimization
- [ ] Add comprehensive error handling
- [ ] Implement retry logic
- [ ] Add loading states throughout
- [ ] Optimize database queries
- [ ] Add caching where appropriate
- [ ] Performance testing
- [ ] Security audit

**Phase 8 Deliverable**: Production-ready application

---

## Technical Debt & Improvements

- [ ] Add comprehensive unit tests
- [ ] Add integration tests
- [ ] Setup CI/CD pipeline (GitHub Actions)
- [ ] Add API documentation (OpenAPI/Swagger)
- [ ] Create deployment documentation
- [ ] Setup monitoring (Prometheus + Grafana)
- [ ] Add logging infrastructure
- [ ] Security audit
- [ ] Create user documentation

---

## Notes

### Priority Order
1. **Phase 1** - Foundation (Auth, Chat)
2. **Phase 2** - RAG Core (Documents, Retrieval)
3. **Phase 3** - PII Protection (Privacy) ⭐ Important for Mental Health
4. **Phase 4** - Agent System (Multi-agent)
5. **Phase 5** - Text-to-SQL (Schema Linking) ⭐ Key differentiator
6. **Phase 6** - Project System (Organization)
7. **Phase 7** - Fine-tuning (Job Dispatcher)
8. **Phase 8** - Polish (Production-ready)

### Current Focus
> **Phase 4 In Progress!** Agent System: Backend done, Frontend UI done.
> **Next Step**: User-Created Agents feature (Backend CRUD + Frontend Form)

### Blockers
- None currently

---

*Last updated: December 3, 2024*
*Synced with spec v3.1 (User-Created Agents)*
