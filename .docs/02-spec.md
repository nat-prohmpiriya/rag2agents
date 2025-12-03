# RAG Agent Platform - Project Specification

## 📋 Document Info

| | |
|--|--|
| **Version** | 4.0 |
| **Date** | December 2024 |
| **Author** | - |
| **Status** | In Development |
| **Changes v4** | PII + Fine-tuning → Optional, Advanced Tools, Multi-Agent Orchestration |

---

## 🎯 Project Overview

| | |
|--|--|
| **Project Name** | RAG Agent Platform |
| **Type** | Domain-Agnostic RAG + Multi-Agent System |
| **Purpose** | Portfolio สำหรับสมัครงาน AI Developer |
| **Target Company** | Sciology (Mental Health/Scientific Research) |

### Key Differentiators

- **Domain-Agnostic**: เปลี่ยน domain ด้วย config file
- **Multi-Agent**: Pre-built agents สำหรับ HR, Legal, Finance, Research
- **Multi-Project**: แยก knowledge base ตาม project
- **Text-to-SQL**: Query database ด้วยภาษาธรรมชาติ + Schema Linking
- **Advanced Tools**: Code executor, API caller, web scraper, file manager
- **Multi-Agent**: Agent-to-agent collaboration, orchestrator pattern
- **Fine-tuning**: (Optional) Train custom models via Job Dispatcher
- **PII Protection**: Auto-mask sensitive data ก่อนส่ง LLM ⭐ NEW v3
- **Production-Ready**: User management, usage limits, monitoring

---

## 🛠 Tech Stack

### Core Technologies

| Layer | Technology | Reason |
|-------|------------|--------|
| **Frontend** | SvelteKit + Svelte 5 + Tailwind v4 + shadcn-svelte | Enterprise-ready UI, White-label support |
| **Backend** | FastAPI (Python) | Async, เหมาะกับ AI/ML, first-class Python |
| **LLM Gateway** | LiteLLM (Library + Proxy) | Unified API, multi-provider, Admin UI |
| **Vector Store** | pgvector (PostgreSQL) | Native PostgreSQL extension, production-ready |
| **Embeddings** | LiteLLM Embedding API (Gemini text-embedding-004) | 768 dims, unified API |
| **Agent Framework** | Custom + LangGraph | เริ่มทำเอง แล้ว upgrade |
| **Monitoring** | Prometheus | Metrics collection |
| **Database** | PostgreSQL + pgvector | Dev & Prod, vector support built-in |

### NEW v3: Privacy & Safety Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PII Detection** | Microsoft Presidio | ตรวจจับข้อมูลส่วนตัว |
| **PII Masking** | Presidio Anonymizer | ปิดบังข้อมูลก่อนส่ง LLM |
| **Schema Linking** | RAG on Schema | หา tables ที่เกี่ยวข้อง |
| **SQL Review** | User Confirmation | ให้ user ยืนยัน SQL ก่อนรัน |

### Advanced Tools Stack ⭐ NEW v4

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Code Executor** | Docker sandbox | Run Python/JS safely |
| **API Caller** | httpx | Call external APIs |
| **Web Scraper** | Playwright/BeautifulSoup | Extract web content |
| **File Manager** | Local storage | User file operations |

### Fine-tuning Stack (Optional/Future)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Job Dispatcher** | FastAPI + Queue | ส่ง job ไป train บน cloud |
| **GPU Provider** | Colab/Kaggle/RunPod | Train models (มี GPU) |
| **Model Hub** | Hugging Face Hub | Store & share models |

### Text-to-SQL Stack (Enhanced)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Schema Linking** | RAG + Embeddings | หา tables/columns ที่เกี่ยวข้อง |
| **SQL Generation** | LLM + Pruned Schema | Generate SQL จาก subset |
| **SQL Review** | User Confirmation UI | ให้ user ยืนยันก่อน execute |
| **Safe Execution** | Read-only sandbox | Execute อย่างปลอดภัย |

### Observability Stack ⭐ NEW

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Tracing** | OpenTelemetry SDK | Distributed tracing |
| **Trace Backend** | Jaeger | Trace visualization (port 16686) |
| **Metrics** | Prometheus | Backend API metrics |
| **Logging** | ❌ ไม่ใช้แยก | ใช้ Trace แทน Log |
| **Context** | RequestContext | user_id, trace_id per request |
| **Response** | BaseResponse[T] | trace_id ในทุก response |

**Design Decisions:**
- ใช้ Trace แทน Log → ลด complexity, ได้ timing + flow ด้วย
- `@traced()` decorator → track input/output ทุก function
- trace_id ใน response body → dev เห็นง่าย, debug สะดวก

### Conversation Search Stack ⭐ NEW

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Full-text Search** | PostgreSQL tsvector + GIN Index | High-performance text search |
| **Ranking** | ts_rank | Relevance scoring |
| **Highlighting** | ts_headline | Snippet with keyword highlight |

**Key Features:**
- **PostgreSQL Native** - ไม่ต้องติดตั้ง external service (Elasticsearch/Algolia)
- **GIN Index** - ค้นหาล้าน records ใน milliseconds
- **Stemming Support** - "running", "runs", "ran" → หาเจอหมด
- **Relevance Ranking** - เรียงตาม relevance score
- **Auto Highlight** - `ts_headline` ทำ highlight อัตโนมัติ

### Testing Stack ⭐ NEW

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Test Framework** | pytest + pytest-asyncio | Async test support |
| **Fixtures** | Factory Boy | Test data generation |
| **Coverage** | pytest-cov | Coverage report (target >80%) |
| **API Testing** | httpx + TestClient | Integration tests |
| **Mocking** | pytest-mock | External service mocking |

**Test Strategy:**
- Unit tests: Services, Utils (fast, isolated)
- Integration tests: API endpoints (with test DB)
- Coverage target: >80%

### Security Stack ⭐ NEW

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Rate Limiting** | slowapi | Per-user/IP rate limiting |
| **Input Validation** | Pydantic v2 | Request validation |
| **Auth** | JWT + Refresh Token | Authentication |
| **PII Protection** | Presidio | Data privacy |

### DevOps & Infrastructure

| Component | Technology |
|-----------|------------|
| **VPS** | Hetzner CX32 (EU) |
| **PaaS** | Coolify (self-hosted) |
| **CI/CD** | GitHub Actions |
| **Container** | Docker + Docker Compose |
| **SSL** | Let's Encrypt (auto via Coolify) |
| **Version Control** | GitHub |

---

## 💰 Cost Breakdown

| Item | Cost/Month |
|------|------------|
| Hetzner CX32 (4 vCPU, 8GB RAM, 80GB SSD) | €6.80 (~฿260) |
| Coolify | Free |
| GitHub Actions | Free (2,000 min) |
| LiteLLM | Free |
| Hugging Face Hub | Free (public models) |
| Weights & Biases | Free (100GB) |
| **Infrastructure Total** | **~฿260/month** |
| LLM API (OpenAI/Claude/Groq) | Pay-per-use |

### GPU for Fine-tuning (On-demand)

| Provider | Cost | GPU | Notes |
|----------|------|-----|-------|
| **Google Colab** | Free / $10/mo Pro | T4 / A100 | ดีสำหรับเริ่มต้น |
| **Kaggle** | Free (30h/week) | P100 / T4x2 | ฟรีแต่มี limit |
| **RunPod** | ~$0.4/hr | A100 | Serverless, pay-per-use |
| **Modal** | ~$0.3/hr | A10G | Serverless, ง่าย |

**หมายเหตุ**: Fine-tuning ไม่ได้รันบน Hetzner (ไม่มี GPU) แต่ใช้ Job Dispatcher ส่งไป train บน cloud

---

## 🏗 Architecture

### High-Level Architecture (Updated v3)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Hetzner VPS (CX32)                           │
│  ┌────────────────────────────────────────────────────────────┐│
│  │                        Coolify                             ││
│  │                                                            ││
│  │  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐ ││
│  │  │  App Container   │  │   LiteLLM    │  │  Prometheus  │ ││
│  │  │  ┌────────────┐  │  │   Proxy      │  │              │ ││
│  │  │  │Svelte(static)│ │  │              │  │              │ ││
│  │  │  ├────────────┤  │  │              │  │              │ ││
│  │  │  │  FastAPI   │──┼──┼──────────────┼──┼──────────────│ ││
│  │  │  ├────────────┤  │  │              │  │              │ ││
│  │  │  │ PII Scrubber│ │  │              │  │              │ ││
│  │  │  ├────────────┤  │  │              │  │              │ ││
│  │  │  │ PostgreSQL │  │  │              │  │              │ ││
│  │  │  │ + pgvector │  │  │              │  │              │ ││
│  │  │  └────────────┘  │  └──────────────┘  └──────────────┘ ││
│  │  └──────────────────┘                                      ││
│  └────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────┘
          │              │              │              │
          ▼              ▼              ▼              ▼
   ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
   │ LLM APIs  │  │ Customer  │  │ HF Hub    │  │ GPU Cloud │
   │ OpenAI    │  │ Databases │  │ (Models)  │  │ Colab/    │
   │ Claude    │  │ PG/MySQL  │  │           │  │ RunPod    │
   └───────────┘  └───────────┘  └───────────┘  └───────────┘
```

### Data Flow with PII Protection ⭐ NEW v3

```
User Query: "คุณสมชาย โทร 081-234-5678 มียอดค้างชำระเท่าไหร่"
     │
     ▼
┌─────────────────┐
│  PII Scrubber   │  ← ตรวจจับและ mask ข้อมูลส่วนตัว
│  (Presidio)     │
└────────┬────────┘
         │
         ▼
Query: "[PERSON] โทร [PHONE] มียอดค้างชำระเท่าไหร่"
         │
         ▼
┌─────────────────┐
│  Query Router   │  ← Classify: RAG / SQL / Both
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│  RAG  │ │ SQL   │
│Pipeline│ │Pipeline│
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         ▼
┌─────────────────┐
│   LLM Response  │  ← Response ไม่มี PII
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  PII Restore    │  ← (Optional) แสดงข้อมูลจริงใน UI
│  (if allowed)   │
└─────────────────┘
```

### Text-to-SQL with Schema Linking ⭐ NEW v3

```
User Query: "ยอดขายของลูกค้า VIP เดือนนี้"
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Schema Linking (RAG on Schema)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Query Embedding ──▶ Search Schema Embeddings                  │
│                              │                                  │
│                              ▼                                  │
│  Database (100 tables) ──▶ Find Relevant: 3 tables             │
│                              │                                  │
│                              ▼                                  │
│  Relevant Tables:                                               │
│  ├── orders (id, customer_id, amount, date)                    │
│  ├── customers (id, name, tier, email)                         │
│  └── customer_tiers (id, name, discount)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: SQL Generation (Pruned Schema Only)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LLM receives:                                                  │
│  - User query                                                   │
│  - Only 3 relevant tables (not 100)                            │
│  - Column descriptions                                          │
│  - Relationships                                                │
│                                                                 │
│  LLM generates:                                                 │
│  SELECT c.name, SUM(o.amount) as total                         │
│  FROM orders o                                                  │
│  JOIN customers c ON o.customer_id = c.id                      │
│  WHERE c.tier = 'VIP' AND o.date >= '2024-12-01'               │
│  GROUP BY c.id                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: User Confirmation ⭐ NEW v3                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  🔍 Generated SQL Query                                  │   │
│  │  ──────────────────────────────────────────────────────  │   │
│  │  SELECT c.name, SUM(o.amount) as total                   │   │
│  │  FROM orders o                                           │   │
│  │  JOIN customers c ON o.customer_id = c.id                │   │
│  │  WHERE c.tier = 'VIP' AND o.date >= '2024-12-01'         │   │
│  │  GROUP BY c.id                                           │   │
│  │                                                          │   │
│  │  ⚠️ This query will read from: orders, customers         │   │
│  │  📊 Estimated rows: ~50                                  │   │
│  │                                                          │   │
│  │  [✅ Execute]  [✏️ Edit]  [❌ Cancel]                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ (User clicks Execute)
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Safe Execution                                        │
├─────────────────────────────────────────────────────────────────┤
│  ✅ Read-only connection                                        │
│  ✅ 30 second timeout                                           │
│  ✅ Max 1000 rows                                                │
│  ✅ No sensitive columns exposed                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Fine-tuning: Job Dispatcher Pattern ⭐ NEW v3

```
┌─────────────────────────────────────────────────────────────────┐
│              Fine-tuning Job Dispatcher Pattern                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Hetzner VPS (No GPU)              GPU Cloud (Colab/RunPod)    │
│  ─────────────────────             ─────────────────────────    │
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │  Admin Panel     │              │  Training Worker │        │
│  │  (Job Dispatcher)│              │  (GPU Instance)  │        │
│  └────────┬─────────┘              └────────┬─────────┘        │
│           │                                  │                  │
│           │ 1. Create Job                    │                  │
│           ▼                                  │                  │
│  ┌──────────────────┐                        │                  │
│  │  Job Queue       │                        │                  │
│  │  (PostgreSQL)    │ ◀──────────────────────┤                  │
│  └────────┬─────────┘   2. Poll for jobs     │                  │
│           │                                  │                  │
│           │                                  │                  │
│           │              3. Download data    │                  │
│           │ ─────────────────────────────▶   │                  │
│           │                                  │                  │
│           │              4. Train model      │                  │
│           │                           ┌──────┴──────┐           │
│           │                           │  GPU Train  │           │
│           │                           │  (LoRA)     │           │
│           │                           └──────┬──────┘           │
│           │                                  │                  │
│           │              5. Push to HF Hub   │                  │
│           │                           ┌──────┴──────┐           │
│           │                           │  HF Hub     │           │
│           │                           │  (Model)    │           │
│           │                           └──────┬──────┘           │
│           │                                  │                  │
│           │ ◀────────────────────────────────┤                  │
│           │   6. Update job status           │                  │
│           │                                  │                  │
│           ▼                                  │                  │
│  ┌──────────────────┐                        │                  │
│  │  Model Registry  │ ◀──────────────────────┘                  │
│  │  (Available to   │   7. Pull model for use                   │
│  │   Platform)      │                                           │
│  └──────────────────┘                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Key Point: 
─────────
- Hetzner VPS = Job Dispatcher (no training here)
- GPU Cloud = Actual training (Colab/Kaggle/RunPod)
- HF Hub = Model storage & sharing
- สิ่งที่ demo = Pipeline การส่ง job, track progress, pull model กลับมาใช้
```

---

## 📦 Features Specification

### 1. User System

#### 1.1 Authentication
- [ ] User registration (email + password)
- [ ] User login / logout
- [ ] Password reset
- [ ] Session management (JWT)

#### 1.2 User Tiers

| Tier | Token Limit | Projects | Documents | Models | Rate Limit |
|------|-------------|----------|-----------|--------|------------|
| **Free** | 50K/month | 3 | 10 | GPT-3.5 | 5 req/min |
| **Pro** | 500K/month | 20 | 100 | GPT-4, Claude | 30 req/min |
| **Enterprise** | Unlimited | Unlimited | Unlimited | All + Custom | 100 req/min |

#### 1.3 User Profile ⭐ NEW
- [x] User profile fields (first_name, last_name, avatar_url)
- [ ] Profile update API endpoint
- [ ] Profile settings page UI
- [ ] Avatar upload (stored in local storage)

#### 1.4 User Settings ⭐ NEW
- [ ] UserSettings model (theme, language, default_model, etc.)
- [ ] Settings CRUD API
- [ ] Settings page UI with sections:
  - General (theme, language)
  - AI preferences (default model, temperature)
  - Notifications (optional)
  - API keys (for power users, optional)
  - PII masking preferences (optional)

---

### 2. Project System

#### 2.1 Project Management
- [ ] Create / Edit / Delete projects
- [ ] Project naming & description
- [ ] Project icon/color selection
- [ ] Project archiving

#### 2.2 Project Components

| Component | Description |
|-----------|-------------|
| **Documents** | Isolated knowledge base per project |
| **Database Connections** | External DB for Text-to-SQL |
| **Conversations** | Chat history within project |
| **Agent** | Assigned agent for project |
| **Settings** | Model, temperature, custom prompts |
| **Privacy Settings** | PII masking level ⭐ NEW v3 |

#### 2.3 Privacy Settings ⭐ NEW v3

| Level | Description | Use Case |
|-------|-------------|----------|
| **Strict** | Mask ทุก PII (ชื่อ, เบอร์, อีเมล, etc.) | Mental health, Medical |
| **Moderate** | Mask เฉพาะ sensitive (SSN, บัตร) | General business |
| **Off** | ไม่ mask (internal use only) | Non-sensitive data |

---

### 3. PII Protection System ⭐ NEW v3

#### 3.1 Supported PII Types

| Type | Examples | Detection |
|------|----------|-----------|
| **PERSON** | ชื่อคน | NER + Pattern |
| **PHONE** | 081-xxx-xxxx | Regex |
| **EMAIL** | xxx@xxx.com | Regex |
| **ID_CARD** | เลขบัตรประชาชน | Regex |
| **CREDIT_CARD** | เลขบัตรเครดิต | Luhn + Regex |
| **LOCATION** | ที่อยู่ | NER |
| **DATE_OF_BIRTH** | วันเกิด | Pattern |
| **MEDICAL_RECORD** | เลข HN, รหัสผู้ป่วย | Custom |

#### 3.2 PII Scrubber Behavior

- ใช้ Microsoft Presidio สำหรับ detect และ mask
- รองรับภาษาไทย (custom recognizers)
- Return: `(scrubbed_text, mapping)` สำหรับ restore ถ้าจำเป็น
- Mapping เก็บแบบ encrypted สำหรับ audit

#### 3.3 Integration Flow

```
User Input → PII Scrubber → RAG/SQL → LLM → Response
                  ↓
            Mapping (encrypted) → Audit Log
```

**Note**: LLM ไม่เห็น PII จริง, Original เก็บ encrypted สำหรับ audit เท่านั้น

---

### 4. Agent System

#### 4.1 Agent Types

| Type | Description | Created By |
|------|-------------|------------|
| **System Agents** | Pre-built agents from YAML config | Admin |
| **User Agents** | Custom agents created by users | User |

#### 4.2 Pre-built System Agents

| Agent | Description | Tools |
|-------|-------------|-------|
| **General** | General-purpose assistant | RAG search, summarize |
| **HR** | HR policy & recruitment | Resume parser, policy RAG, skill matcher |
| **Legal** | Legal analysis & research | Contract analyzer, law search, case compare |
| **Finance** | Financial analysis | Financial calculator, report analyzer, SQL query |
| **Research** | Research assistant | Paper search, citation finder |
| **Data Analyst** | Data analysis | SQL query, chart generator, data summary |
| **Mental Health** | Research assistant ⭐ NEW v3 | PII-safe RAG, anonymized case search |

#### 4.3 User-Created Agents ⭐ NEW

Users can create their own agents with:
- Custom name, description, icon
- Custom system prompt
- Selected tools
- **Linked documents/project** (personalized knowledge base)

**User Agent Fields**: id, user_id, name, slug, description, icon, system_prompt, tools[], document_ids[], project_id, is_active

#### 4.4 Mental Health Agent ⭐ NEW v3

Special agent for mental health domain:
- **Privacy**: Always strict PII masking
- **Persona**: Research-focused, no medical advice
- **Tools**: PII-safe RAG, anonymized case search, citation finder
- **Audit**: Full logging enabled

---

### 5. RAG System

#### 5.1 Document Processing
- [x] Supported formats: PDF, DOCX, TXT, MD, CSV
- [x] Automatic text extraction (PyMuPDF, python-docx)
- [x] Smart chunking (recursive splitter)
- [x] Metadata extraction
- [ ] PII detection on upload ⭐ NEW v3

#### 5.2 Vector Store
- [x] pgvector integration (replaced ChromaDB)
- [ ] Per-project collections
- [ ] Schema embeddings for Text-to-SQL ⭐ NEW v3
- [x] Embedding model: Gemini text-embedding-004 (768 dims via LiteLLM)
- [ ] Hybrid search (Dense + BM25) - optional

#### 5.3 Retrieval Pipeline
- [ ] PII scrubbing on query ⭐ NEW v3
- [x] Query preprocessing
- [x] Dense search (cosine similarity with pgvector)
- [ ] Hybrid search (dense + sparse) - optional
- [ ] Re-ranking (optional)
- [x] Context assembly

---

### 6. Database Integration & sql_query Tool

#### 6.1 Schema Linking ⭐ NEW v3

**Problem**: Database มี 100 ตาราง ส่งทั้งหมดให้ LLM = Token เยอะ + LLM งง

**Solution**: RAG on Schema
1. Embed schema ของทุก table/column
2. User query → search หา relevant tables (top 3-5)
3. ส่งแค่ pruned schema ให้ LLM

#### 6.2 SQL Generation Flow

```
User Query → Schema Linking → Pruned Schema → LLM → Generated SQL
```

**Rules for LLM**:
- SELECT only (no DELETE, UPDATE, DROP)
- Include only necessary columns
- Add appropriate WHERE clauses

#### 6.3 User Confirmation ⭐ NEW v3

Before execution, show user:
- Generated SQL with syntax highlighting
- Tables accessed
- Estimated rows
- Safety check status

**Actions**: Execute / Edit / Cancel

#### 6.4 Safety Features (Enhanced v3)

| Feature | v2 | v3 |
|---------|----|----|
| Read-only mode | ✅ | ✅ |
| Query whitelist | ✅ | ✅ |
| Row limit | ✅ | ✅ |
| Timeout | ✅ | ✅ |
| **Schema Linking** | ❌ | ✅ NEW |
| **User Confirmation** | ❌ | ✅ NEW |
| **Schema Pruning** | ❌ | ✅ NEW |
| **Query Explanation** | ❌ | ✅ NEW |

---

### 7. Tools System ⭐ UPDATED v4

#### 7.1 Available Tools

| Tool | Description | Safety | Phase |
|------|-------------|--------|-------|
| **rag_search** | Search documents | Per-project scope | ✅ Done |
| **summarize** | Summarize text | - | 🔄 In Progress |
| **calculator** | Math calculations | - | 🔄 In Progress |
| **sql_query** | Query database (Text-to-SQL) | Read-only, User confirm | Phase 5 |
| **image_analyze** | Analyze images (Gemini Vision) | - | Phase 6 |
| **image_gen** | Generate images (Imagen) | Rate limited | Phase 6 |
| **image_edit** | Edit images (Inpainting) | Rate limited | Phase 6 |
| **code_executor** | Run Python/JS in Docker | Isolated container | Phase 6 |
| **api_caller** | Call external APIs | Rate limited | Phase 6 |
| **file_manager** | Read/write user files | Scoped to user dir | Phase 6 |
| **web_scraper** | Extract web content | Robots.txt compliant | Phase 6 |
| **tts** | Text-to-Speech (Gemini TTS) | - | Phase 6 |

#### 7.2 sql_query Tool (Text-to-SQL) ⭐

**Features**:
- Schema Linking (RAG on Schema) - หา tables ที่เกี่ยวข้อง
- SQL Generation with pruned schema
- User Confirmation UI - ยืนยันก่อนรัน
- Safe Execution - read-only, timeout, row limit

**See Section 6 for details**

#### 7.3 Image & Multimodal Tools ⭐ NEW

| Tool | Provider | Use Case |
|------|----------|----------|
| **image_analyze** | Gemini Vision | วิเคราะห์รูป, อ่าน chart, OCR |
| **image_gen** | Imagen 3 | สร้างรูปจาก prompt |
| **image_edit** | Imagen (Inpainting) | แก้ไขบางส่วนของรูป |
| **tts** | Gemini 2.5 TTS | แปลง text เป็นเสียง |

**Example Use Cases**:
```
User: "วิเคราะห์ chart นี้ให้หน่อย" [แนบรูป]
Agent: [image_analyze] → "ยอดขาย Q3 สูงสุดที่ 2.5M..."

User: "สร้าง logo บริษัท minimal style สีฟ้า"
Agent: [image_gen] → 🖼️ Generated logo

User: "อ่านข้อความในรูปนี้ให้ฟังหน่อย"
Agent: [image_analyze] → [tts] → 🔊 Audio output
```

#### 7.5 Multi-Agent Orchestration

**Orchestrator Pattern**:
- Orchestrator Agent รับ task จาก user
- แบ่งงานให้ Specialized Agents (Research, Coder, Writer)
- รวม results และ respond กลับ user

#### 7.6 Workflow Builder

Users can create custom workflows:
- Visual drag-and-drop builder
- Trigger-based automation
- Scheduled tasks

---

### 8. User Profile & Settings ⭐ NEW

#### 8.1 User Profile

| Field | Type | Description |
|-------|------|-------------|
| first_name | string | User's first name |
| last_name | string | User's last name |
| avatar_url | string | URL to avatar image |

**API Endpoints**:
- `GET /api/users/me` - Get current user profile
- `PUT /api/users/me` - Update profile (first_name, last_name)
- `POST /api/users/me/avatar` - Upload avatar image

#### 8.2 User Settings Model

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| theme | enum | system | light, dark, system |
| language | enum | en | en, th |
| default_model | string | null | Preferred LLM model |
| default_temperature | float | 0.7 | Default temperature |
| notifications_enabled | bool | true | Enable notifications |

**API Endpoints**:
- `GET /api/users/me/settings` - Get user settings
- `PUT /api/users/me/settings` - Update settings

#### 8.3 Settings Page UI

Sections:
1. **Profile** - Name, avatar
2. **General** - Theme, language
3. **AI Preferences** - Default model, temperature
4. **Account** - Email, password change (future)

---

### 9. Admin & Monitoring

#### 9.1 Admin Panel
- [ ] User management (view, edit, suspend)
- [ ] Usage overview (all users)
- [ ] System health dashboard
- [ ] Cost tracking
- [ ] Fine-tuning job management
- [ ] Database connection management
- [ ] PII audit logs ⭐ NEW v3

#### 9.2 PII Audit Dashboard ⭐ NEW v3

Shows:
- Total queries processed
- Queries with PII detected (%)
- PII types breakdown (PERSON, PHONE, EMAIL, etc.)
- Recent PII events table (time, user, project, types, action)

---

## 📁 Project Structure (Actual)

```
llm-application-framework/
├── backend/
│   ├── app/
│   │   ├── routes/                     # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── users.py               # Profile & Settings ⭐ NEW
│   │   │   ├── chat.py
│   │   │   ├── projects.py
│   │   │   ├── documents.py
│   │   │   ├── agents.py
│   │   │   ├── conversations.py
│   │   │   └── health.py
│   │   │
│   │   ├── core/
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   ├── dependencies.py
│   │   │   ├── exceptions.py
│   │   │   ├── telemetry.py
│   │   │   └── context.py
│   │   │
│   │   ├── middleware/
│   │   │   └── trace.py
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── user_settings.py       # User preferences ⭐ NEW
│   │   │   ├── project.py
│   │   │   ├── conversation.py
│   │   │   ├── message.py
│   │   │   ├── document.py
│   │   │   ├── chunk.py
│   │   │   ├── agent.py
│   │   │   └── project_document.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── conversation.py
│   │   │   ├── chat.py
│   │   │   ├── agent.py
│   │   │   └── vector.py
│   │   │
│   │   ├── services/
│   │   │   ├── auth.py
│   │   │   ├── project.py
│   │   │   ├── document.py
│   │   │   ├── document_processor.py
│   │   │   ├── conversation.py
│   │   │   ├── agent.py
│   │   │   ├── agent_loader.py
│   │   │   ├── rag.py
│   │   │   ├── embedding.py
│   │   │   ├── vector_store.py
│   │   │   ├── storage.py
│   │   │   └── models.py
│   │   │
│   │   ├── providers/
│   │   │   └── llm.py
│   │   │
│   │   ├── agents/
│   │   │   ├── engine.py
│   │   │   └── tools/
│   │   │       ├── base.py
│   │   │       ├── rag_search.py
│   │   │       ├── summarize.py
│   │   │       └── calculator.py
│   │   │
│   │   ├── config.py
│   │   └── main.py
│   │
│   ├── configs/agents/                 # Agent YAML configs
│   │   ├── general.yaml
│   │   ├── research.yaml
│   │   └── ...
│   │
│   └── pyproject.toml
│
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +page.svelte
│   │   │   ├── +layout.svelte
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── (app)/                  # Protected routes
│   │   │       ├── +layout.svelte
│   │   │       ├── dashboard/
│   │   │       ├── chat/[id]/
│   │   │       ├── projects/[id]/
│   │   │       ├── documents/
│   │   │       ├── agents/
│   │   │       ├── settings/           # Pending
│   │   │       ├── sql-query/          # Pending
│   │   │       └── fine-tuning/        # Optional
│   │   │
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── ui/                 # shadcn-svelte
│   │   │   │   ├── llm-chat/
│   │   │   │   ├── sidebar/
│   │   │   │   └── ...
│   │   │   ├── stores/
│   │   │   ├── api/
│   │   │   └── types/
│   │   │
│   │   └── app.html
│   │
│   └── package.json
│
├── .docs/                              # Project documentation
├── .claude/                            # Claude Code configs
├── docker-compose.yml
└── CLAUDE.md
```

---

## 📅 Development Phases (Updated v4)

### Phase 1: Foundation ✅ DONE
**Goal**: Basic working app with authentication

- [x] Setup project structure
- [x] FastAPI backend skeleton
- [x] SvelteKit frontend skeleton
- [x] PostgreSQL + pgvector for dev & production
- [x] User authentication (register/login)
- [x] Basic chat UI
- [x] LiteLLM integration
- [x] Docker containerization

**Deliverable**: User can login and chat with AI

---

### Phase 2: RAG Core ✅ DONE
**Goal**: Document upload and RAG working

- [x] Document upload API
- [x] PDF/DOCX text extraction (PyMuPDF, python-docx)
- [x] Text chunking (recursive splitter)
- [x] pgvector integration
- [x] Embedding generation (LiteLLM + Gemini text-embedding-004)
- [x] Basic retrieval (dense search with cosine similarity)
- [x] Source citations in responses
- [x] Document management UI

**Deliverable**: User can upload docs and ask questions

---

### Phase 3: Agent System 🔄 IN PROGRESS
**Goal**: Multi-agent with tools

- [x] Agent base class
- [x] Agent configuration loader (YAML)
- [x] Agent execution engine
- [x] rag_search tool
- [ ] summarize tool
- [ ] calculator tool
- [x] Pre-built agents (General, Finance)
- [x] Agent selector UI
- [x] Agent thinking display
- [x] User-created agents

**Deliverable**: User can select agents for different tasks

---

### Phase 4: Project System ✅ DONE
**Goal**: Multi-project with isolated data

- [x] Project CRUD API
- [x] Per-project document storage
- [x] Per-project conversations
- [x] Project settings UI
- [x] Project switching in sidebar
- [x] Project-scoped RAG queries

**Deliverable**: User can organize work into projects

---

### Phase 5: Database Integration (sql_query tool)
**Goal**: Safe database queries with user confirmation

- [ ] Database connection management
- [ ] Schema embedding & indexing
- [ ] Schema linking (RAG on schema)
- [ ] sql_query tool implementation
- [ ] SQL validation & safety checks
- [ ] User confirmation UI
- [ ] Query execution (read-only)
- [ ] Result formatting (table, chart)
- [ ] Data Analyst agent with sql_query tool

**Deliverable**: Agent can query database safely with confirmation

---

### Phase 6: Advanced Tools
**Goal**: Powerful tools for agents

- [ ] **code_executor tool** - Run Python/JS in sandbox
- [ ] **api_caller tool** - Call external APIs
- [ ] **file_manager tool** - Read/write user files
- [ ] **Web Scraper Tool** - Extract web content
- [ ] **Multi-Agent Orchestration** - Agent-to-agent communication
- [ ] **Orchestrator Agent** - Delegate tasks to specialized agents
- [ ] **Workflow Builder UI** - Visual agent workflow creation
- [ ] **Scheduled Tasks** - Trigger-based automation

**Deliverable**: Agents can use powerful tools and collaborate on complex tasks

---

### Phase 7: Polish & Production
**Goal**: Production-ready features

- [ ] Usage tracking service
- [ ] User limits & quotas
- [ ] Rate limiting
- [ ] Usage dashboard UI
- [ ] Admin panel (full)
- [ ] Debug panel
- [ ] Error handling & retry
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation

**Deliverable**: Ready for demo/production

---

### Optional Phases

#### PII Protection (On Request)
> เมื่อมี target ที่ต้องการ (Mental Health, Medical)

- [ ] Presidio integration
- [ ] Thai PII recognizers
- [ ] PII scrubber middleware
- [ ] Privacy level settings
- [ ] PII audit logging

#### Fine-tuning Module (On Request)
> เมื่อ RAG + Prompting ไม่เพียงพอ

- [ ] Job Dispatcher API
- [ ] GPU Cloud integration
- [ ] Hugging Face Hub integration
- [ ] Fine-tuning dashboard UI

---

## 🎓 Skills Coverage (Updated v3)

| Job Requirement | Project Feature | Status |
|-----------------|-----------------|--------|
| **RAG Pipeline** | Document upload, embedding, retrieval | ✅ |
| **Agentic AI** | Multi-agent system, tools, reasoning | ✅ |
| **Fine-tuning LLMs** | Job Dispatcher + GPU Cloud training | ✅ |
| **Hugging Face** | Transformers, PEFT, Hub | ✅ |
| **Python Scientific** | NumPy, Pandas, Data processing | ✅ |
| **RESTful APIs** | Full REST API | ✅ |
| **MLOps** | Prometheus, W&B, model deployment | ✅ |
| **CI/CD** | GitHub Actions | ✅ |
| **Large-scale Data** | Document processing, SQL queries | ✅ |
| **Data Privacy** | PII Protection (Presidio) | ✅ NEW v3 |
| **Mental Health Domain** | PII-safe agent, audit logging | ✅ NEW v3 |

### ครบทุก Requirements + Domain-specific สำหรับ Sciology ✅

---

## 💬 Interview Talking Points (Updated v3)

### Elevator Pitch
> "ผมสร้าง RAG Agent Platform ที่เป็น domain-agnostic template รองรับ multi-project แต่ละ project มี isolated knowledge base และ privacy settings ที่แยกกัน สามารถต่อ database ลูกค้าได้โดยตรงผ่าน Text-to-SQL ที่มี Schema Linking หา tables ที่เกี่ยวข้องก่อน ไม่ต้องส่งทั้ง 100 ตาราง และมี User Confirmation ให้ review SQL ก่อนรัน ที่สำคัญคือมี PII Protection ใช้ Presidio mask ข้อมูลส่วนตัวก่อนส่งไป LLM เหมาะกับงาน Mental Health ที่ sensitive สูง"

### Technical Deep-Dives

**Q: Conversation Search ทำยังไง?** ⭐ NEW

> "ใช้ **PostgreSQL Full-text Search** พร้อม **GIN Index** ครับ ไม่ต้องพึ่ง external service อย่าง Elasticsearch หรือ Algolia ค้นหา conversations ได้ภายใน milliseconds แม้มีข้อมูลล้าน records รองรับ **stemming** (running/runs/ran หาเจอหมด) และ **relevance ranking** พร้อม **auto-highlight** snippet ที่ match เหมือนที่ Gemini และ Claude ทำ"

**Q: ถ้า Database Schema ของลูกค้าซับซ้อนมาก มี 100 ตาราง LLM จะไม่งงเหรอ?** ⭐ NEW

> "เราทำ Schema Linking ครับ คือ embed schema ของทุก table/column ไว้ก่อน เวลา user ถามคำถาม เราเอา query ไป search หา tables ที่เกี่ยวข้อง ได้มา 2-3 tables แล้วค่อยส่งแค่ schema ส่วนนั้นให้ LLM ไม่ใช่ส่งทั้งหมด ทำให้ token น้อยลง LLM ไม่งง และตอบถูกมากขึ้น"

**Q: ทำไมถึงเลือกแยก Service Backend (FastAPI) กับ Frontend (SvelteKit)?** ⭐ NEW

> "Python เป็น first-class citizen ของงาน AI/ML ครับ การใช้ FastAPI ทำให้ integrate กับ library อย่าง LangChain, Presidio, Pandas, sentence-transformers ได้ดีกว่า และรองรับ async process นานๆ เช่น training job, document processing ได้ดีกว่า JavaScript runtime"

**Q: Fine-tuning ทำยังไงถ้าไม่มี GPU บน server?**

> "ผมทำเป็น Job Dispatcher pattern ครับ Hetzner VPS เป็นแค่ตัวสร้างและจัดการ job ส่วน training จริงรันบน Google Colab หรือ RunPod ที่มี GPU พอ train เสร็จ push model ขึ้น Hugging Face Hub แล้ว platform ก็ดึงมาใช้ได้เลย สิ่งที่ demo คือ pipeline ทั้งหมด ไม่ใช่แค่การ train"

**Q: ข้อมูล Mental Health sensitive มาก จัดการยังไง?**

> "ใช้ Microsoft Presidio ครับ ทำ PII Scrubber ที่ detect และ mask ข้อมูลส่วนตัวก่อนส่งไป LLM เช่น ชื่อคนไข้ เบอร์โทร รหัสผู้ป่วย ทั้งหมด mask หมด LLM ไม่เห็นของจริงเลย แต่ยังตอบคำถามได้ พร้อมมี audit log ไว้ตรวจสอบว่า mask อะไรไปบ้าง"

**Q: Text-to-SQL อันตรายไหม ให้ LLM เขียน SQL?**

> "ผมมี safety หลายชั้นครับ: 1) Schema Pruning ส่งแค่ tables ที่เกี่ยวข้อง ไม่ expose ทั้งหมด 2) Validation ตรวจว่าเป็น SELECT only 3) User Confirmation แสดง SQL ให้ user กดยืนยันก่อนรัน 4) Execute บน read-only connection มี timeout และ row limit"

---

## 📎 Appendix

### A. Configuration Files

> ดู implementation จริงที่:
> - `.env.example` - Environment variables
> - `docker-compose.yml` - Development setup
> - `docker-compose.prod.yml` - Production setup
> - `.claude/api-routes.md` - Full API documentation

---

## ✅ Ready to Start

- [ ] Create GitHub repository
- [ ] Setup Hetzner VPS
- [ ] Install Coolify
- [ ] Configure GitHub Actions
- [ ] Create Hugging Face account & token
- [ ] Setup Presidio for PII protection
- [ ] Begin Phase 1

---

## 📊 Timeline Summary

| Phase | Features | Status |
|-------|----------|--------|
| 1. Foundation | Auth, Chat, LiteLLM | ✅ Done |
| 2. RAG Core | Documents, Embeddings, Retrieval | ✅ Done |
| 3. Agent System | Tools (rag_search, summarize), User agents | 🔄 In Progress |
| 4. Project System | Multi-project, Isolated data | ✅ Done |
| 5. Database Integration | sql_query tool, Schema Linking | Pending |
| 6. Advanced Tools | code_executor, api_caller, web_scraper | Pending |
| 7. Polish | Production-ready | Pending |

### Optional (On Request)
| Feature | When to implement |
|---------|-------------------|
| **PII Protection** | เมื่อมี target ที่ต้องการ (Mental Health, Medical) |
| **Fine-tuning** | เมื่อ RAG + Prompting ไม่เพียงพอ |

---

## 🎯 Key Improvements in v4.2

| Feature | Before | After |
|---------|--------|-------|
| **Text-to-SQL** | Separate Phase | sql_query tool (Agent tool) |
| **Tools** | Unstructured | Clear tool table with phases |
| **Phase Order** | Inconsistent | Aligned with actual progress |

---

*Document Version 4.2 - December 2024*
*Changes: Restructured Text-to-SQL as sql_query tool, Updated phase order*