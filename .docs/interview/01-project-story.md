# 01 - Project Story: The Journey of RAG2Agents

---

## 🎬 "เล่าเกี่ยวกับโปรเจ็คนี้หน่อย"

### The Problem I Wanted to Solve

ผมเริ่มโปรเจ็คนี้จากการสังเกตปัญหาที่เกิดขึ้นซ้ำๆ ในหลายองค์กร:

> "เรามี ChatGPT แล้ว แต่มันไม่รู้จักเอกสารภายในของเรา"

ทุกบริษัทมี knowledge base ของตัวเอง — คู่มือ, SOPs, technical docs, policies — แต่ LLM ทั่วไปไม่รู้จักข้อมูลเหล่านี้ การจะให้ AI ตอบคำถามเกี่ยวกับเอกสารภายในได้ ต้องสร้าง RAG pipeline ซึ่งต้องการ:

1. **Document Processing** — extract text จาก PDF, DOCX หลายรูปแบบ
2. **Chunking Strategy** — ตัดข้อความเป็นชิ้นๆ อย่างไรให้ยังคง context
3. **Embedding** — แปลง text เป็น vectors
4. **Vector Database** — จัดเก็บและ search vectors
5. **Prompt Engineering** — ออกแบบ prompt ที่รวม context กับ question
6. **Infrastructure** — deploy และ scale ทั้งหมด

สำหรับ dev team ที่มีประสบการณ์ อาจใช้เวลา 2-3 เดือน สำหรับ non-technical teams? แทบเป็นไปไม่ได้

---

### The Vision

> **"Upload เอกสาร → ได้ AI Agent พร้อมใช้ใน 5 นาที"**

ผมต้องการสร้าง platform ที่:

1. **Zero Infrastructure** — ไม่ต้อง setup vector DB, ไม่ต้อง manage embeddings
2. **Multi-Format Support** — PDF, DOCX, TXT, Markdown, CSV ใช้ได้หมด
3. **Visual Workflow** — Non-technical users สร้าง automation ได้ด้วย drag-and-drop
4. **Multi-LLM** — ไม่ lock-in กับ provider เดียว เปลี่ยน model ได้ตลอด
5. **Production-Ready** — Auth, billing, rate limiting, audit logs พร้อมใช้

---

## 🎯 Target Users

### Primary: Tech Teams ในองค์กรขนาดกลาง

**Pain Points:**
- มี internal docs เยอะ แต่ search ไม่เจอ
- ต้องตอบคำถามซ้ำๆ จาก team members
- ไม่มีเวลา build RAG pipeline เอง

**Use Cases:**
- Internal knowledge assistant
- Customer support agent ที่รู้จัก product docs
- Onboarding assistant สำหรับ new hires

### Secondary: SaaS Builders

**Pain Points:**
- ต้องการ embed AI features ใน product
- ไม่ต้องการ maintain LLM infrastructure

**Use Cases:**
- White-label AI assistant
- Document Q&A feature ใน existing product

---

## 🛠️ How I Built It

### Phase 1: Core RAG Pipeline (Foundation)

เริ่มจาก minimum viable product — upload PDF และถามคำถามได้

```
Upload PDF → Extract Text → Chunk → Embed → Store → Search → Answer
```

**Key Decisions:**
- ใช้ **pgvector** แทน dedicated vector DB (simplicity)
- **Async everywhere** ตั้งแต่แรก (scalability)
- **LiteLLM** สำหรับ LLM abstraction (flexibility)

### Phase 2: Agent System

เพิ่มความสามารถให้ AI ทำได้มากกว่าตอบคำถาม

```python
# Agent มี tools ที่เรียกใช้ได้
tools = ["rag_search", "summarize", "calculator", "web_search"]
```

**Why Agents, not just Chat:**
- Chat = ถาม-ตอบ one-shot
- Agent = มี memory, tools, และ reasoning

### Phase 3: Visual Workflow Builder

Non-technical users ต้องการ automation แต่ไม่ต้องการเขียน code

```
[Start] → [Receive Email] → [RAG Search] → [LLM Generate] → [Send Reply]
```

**Implementation:**
- XYFlow สำหรับ drag-drop canvas
- Nodes/Edges เก็บเป็น JSON ใน PostgreSQL
- Workflow Engine execute step-by-step

### Phase 4: Production Features

- **Authentication** — JWT-based auth
- **Billing** — Stripe subscriptions + usage tracking
- **Multi-tenancy** — User-scoped data isolation
- **Observability** — OpenTelemetry tracing

---

## 💭 "ทำไมถึงตัดสินใจทำโปรเจ็คนี้?"

### Technical Motivation

ผมต้องการ prove ว่าสามารถ build production-grade AI platform ได้ end-to-end:

- **Backend:** FastAPI, async SQLAlchemy, complex business logic
- **Frontend:** Modern Svelte 5 with Runes
- **AI/ML:** RAG pipeline, prompt engineering, LLM integration
- **Infrastructure:** Docker, PostgreSQL, Redis
- **Business Logic:** Subscription billing, usage metering

### Learning Goals

1. **RAG at Scale** — ไม่ใช่แค่ demo ที่ทำงานกับ 10 documents
2. **Async Python** — deep understanding ของ async patterns
3. **Vector Search** — เข้าใจ embeddings และ similarity search
4. **Full-Stack Ownership** — design → implement → deploy

---

## 📈 "Scale ของโปรเจ็คเป็นอย่างไร?"

### Codebase Size

```
Backend:   ~15,000 lines Python
Frontend:  ~10,000 lines Svelte/TypeScript
Total:     ~25,000 lines
```

### Components

| Component | Count |
|-----------|-------|
| API Endpoints | 40+ |
| Database Models | 15+ |
| Services | 20+ |
| Frontend Components | 50+ |
| Workflow Node Types | 10 |

### Features Implemented

- [x] User authentication (register, login, JWT)
- [x] Document upload & processing (PDF, DOCX, TXT, MD, CSV)
- [x] RAG pipeline (chunk, embed, search)
- [x] AI Agents with tools
- [x] Visual Workflow Builder
- [x] Real-time streaming chat (SSE)
- [x] Subscription billing (Stripe)
- [x] Usage tracking & analytics
- [x] Admin dashboard
- [x] Audit logging

---

## 🎨 "อะไรที่ทำให้โปรเจ็คนี้ unique?"

### 1. Single Database for Everything

```
PostgreSQL = Relational Data + Vector Search + JSON Storage
```

ไม่ต้อง manage Pinecone/Weaviate แยก — pgvector ทำ vector search ได้ในตัว

### 2. User-Scoped RAG

```sql
-- ไม่ได้ search ทั้ง database
-- Filter by user first, then vector search
WHERE user_id = $1 AND document_id = ANY($2)
ORDER BY embedding <=> query_embedding
```

ทำให้ scale ได้ดีกว่า global search

### 3. Visual Workflow ที่ Connect กับ RAG

ไม่ใช่แค่ chat — สร้าง automation ที่ใช้ knowledge base ได้

```
[Receive Ticket] → [RAG Search Docs] → [LLM Classify] → [Route to Team]
```

### 4. LLM Provider Agnostic

```python
# เปลี่ยน provider ได้ทันที
model = "gemini/gemini-2.0-flash"  # or "gpt-4", "claude-3"
```

ไม่ lock-in กับ vendor เดียว

---

## 🔮 "อนาคตของโปรเจ็คนี้?"

### Short-term Roadmap

1. **OCR Support** — Scanned PDFs
2. **More Integrations** — Slack, Discord, Email
3. **Advanced RAG** — Hybrid search (keyword + semantic)
4. **Agent Memory** — Long-term conversation memory

### Long-term Vision

- **Self-hosted Option** — Enterprise customers deploy on their infra
- **Marketplace** — Share/sell agent templates
- **API-first** — Developers embed in their apps

---

## 💡 Key Takeaways

เมื่อเล่าเกี่ยวกับ project story ควรเน้น:

1. **Problem → Solution** — ไม่ใช่แค่ "ผมทำ RAG platform" แต่ "องค์กรมีปัญหา X, ผมแก้ด้วย Y"

2. **Technical Depth** — แสดงว่าเข้าใจ underlying technology ไม่ใช่แค่ใช้ library

3. **Decision Making** — ทำไมเลือก pgvector? ทำไม async? มี reasoning

4. **Scale Awareness** — รู้ว่า design จะ scale อย่างไร มี bottleneck ตรงไหน

5. **End-to-End Ownership** — ทำตั้งแต่ design จนถึง deploy ไม่ใช่แค่ทำส่วนเดียว

---

*ต่อไป: [02-architecture.md](./02-architecture.md) — Deep dive into system architecture*
