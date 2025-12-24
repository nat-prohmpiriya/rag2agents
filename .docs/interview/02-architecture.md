# 02 - Architecture: System Design & Decisions

---

## 🏗️ "อธิบาย Architecture ของระบบหน่อย"

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │           SvelteKit Frontend (localhost:5173)                ││
│  │      Svelte 5 Runes + TailwindCSS + shadcn-svelte           ││
│  └─────────────────────────────────────────────────────────────┘│
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API + SSE Streaming
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │           FastAPI Backend (localhost:8000)                   ││
│  │                                                              ││
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       ││
│  │  │  Routes  │ │Middleware│ │   Auth   │ │Rate Limit│       ││
│  │  └────┬─────┘ └──────────┘ └──────────┘ └──────────┘       ││
│  │       │                                                      ││
│  │  ┌────▼─────────────────────────────────────────────┐       ││
│  │  │              SERVICE LAYER                        │       ││
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │       ││
│  │  │  │  RAG   │ │ Agent  │ │Workflow│ │Billing │     │       ││
│  │  │  │Service │ │ Engine │ │ Engine │ │Service │     │       ││
│  │  │  └────────┘ └────────┘ └────────┘ └────────┘     │       ││
│  │  └──────────────────────────────────────────────────┘       ││
│  └─────────────────────────────────────────────────────────────┘│
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     DATA LAYER                                   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │   LiteLLM    │  │    Redis     │          │
│  │  + pgvector  │  │    Proxy     │  │              │          │
│  │              │  │              │  │              │          │
│  │ • Users      │  │ • Gemini     │  │ • Rate Limit │          │
│  │ • Documents  │  │ • OpenAI     │  │ • Cache      │          │
│  │ • Chunks     │  │ • Anthropic  │  │ • Sessions   │          │
│  │ • Embeddings │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │    Stripe    │  │    MinIO     │                             │
│  │   (Billing)  │  │  (Storage)   │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧅 Layer Pattern: ทำไมแยก Route / Service / Model?

### The Problem with Fat Controllers

เคยเห็น codebase ที่ route handler ยาว 200 บรรทัด ทำทุกอย่างใน function เดียว:

```python
# ❌ Anti-pattern: Fat Controller
@router.post("/documents")
async def upload_document(file: UploadFile, db: AsyncSession):
    # Validate file
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Invalid file type")

    # Extract text (50 lines)
    if file.content_type == "application/pdf":
        # ... PDF extraction logic
    elif file.content_type == "application/docx":
        # ... DOCX extraction logic

    # Chunk text (30 lines)
    chunks = []
    for i in range(0, len(text), CHUNK_SIZE):
        # ... chunking logic

    # Embed chunks (20 lines)
    embeddings = []
    for chunk in chunks:
        # ... embedding logic

    # Save to database (30 lines)
    document = Document(...)
    db.add(document)
    # ... more DB operations

    return document
```

**Problems:**
- ไม่สามารถ reuse logic ได้ (ถ้าต้องการ process document จาก CLI?)
- Test ยากมาก (ต้อง mock HTTP layer)
- เปลี่ยน PDF library ต้องแก้ใน route handler

### The Solution: Layered Architecture

```python
# ✅ Clean Architecture

# Layer 1: Route (HTTP concerns only)
@router.post("/documents")
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    document = await document_service.process_and_store(
        file=file,
        user_id=user.id,
        db=db
    )
    return BaseResponse(trace_id=get_trace_id(), data=document)


# Layer 2: Service (Business Logic)
class DocumentService:
    async def process_and_store(
        self,
        file: UploadFile,
        user_id: UUID,
        db: AsyncSession
    ) -> Document:
        # Orchestrate the workflow
        text = await self.document_processor.extract(file)
        chunks = self.text_chunker.chunk(text)
        embeddings = await self.embedding_service.embed_batch(chunks)
        return await self.repository.save(user_id, chunks, embeddings, db)


# Layer 3: Specialized Services
class DocumentProcessor:
    async def extract(self, file: UploadFile) -> str:
        """Extract text from any supported format"""

class TextChunker:
    def chunk(self, text: str) -> list[Chunk]:
        """Split text into overlapping chunks"""

class EmbeddingService:
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings via LiteLLM"""
```

### Benefits Realized

| Aspect | Before | After |
|--------|--------|-------|
| **Testing** | Mock HTTP, DB, LLM ทั้งหมด | Test service แยก, mock dependencies |
| **Reusability** | ทำ CLI ต้อง copy code | เรียก service เดียวกัน |
| **Changes** | เปลี่ยน PDF library แก้หลายที่ | แก้แค่ DocumentProcessor |
| **Readability** | 200 line function | 20 line function + clear services |

---

## 🔌 Dependency Injection: ทำไมสำคัญ?

### FastAPI Dependencies ที่ใช้

```python
# 1. Database Session - สร้างใหม่ทุก request, cleanup อัตโนมัติ
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# 2. Current User - verify JWT, load user
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = verify_jwt(token)
    user = await get_user_by_id(db, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(401, "Invalid user")
    return user

# 3. Request Context - trace_id สำหรับ distributed tracing
def get_context() -> RequestContext:
    ctx = _request_context.get()
    if ctx is None:
        raise RuntimeError("No request context")
    return ctx

# Usage in route
@router.get("/me")
async def get_me(
    user: User = Depends(get_current_user),  # Auto-injected
    db: AsyncSession = Depends(get_db)       # Auto-injected
):
    return user
```

### Why DI Instead of Global State?

```python
# ❌ Global state - hard to test, not thread-safe
db_session = create_session()

@router.get("/users")
async def get_users():
    return await db_session.query(User).all()  # Which session? Race condition?


# ✅ Dependency Injection - explicit, testable
@router.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    return await db.query(User).all()  # Clear ownership

# In tests
async def test_get_users():
    async with test_session() as db:
        result = await get_users(db=db)  # Inject test DB
```

---

## 🔀 "ทำไมเลือก Async ตั้งแต่แรก?"

### The Story

ตอนเริ่มโปรเจ็ค มีคำถามว่าจะใช้ sync หรือ async

**Sync Option:**
- Simple, เข้าใจง่าย
- Flask, Django (traditional)
- แต่ block thread เมื่อรอ I/O

**Async Option:**
- ซับซ้อนกว่า
- FastAPI, asyncio
- ไม่ block, handle concurrent requests ได้มากกว่า

### Analysis

ดู I/O operations ในระบบ:

```
1. Database queries     → 50-200ms
2. LLM API calls       → 1-10 seconds
3. Embedding API calls → 100-500ms
4. File storage        → 50-100ms
```

**LLM calls ใช้เวลานานมาก!** ถ้าใช้ sync และมี 100 concurrent users:

```
Sync: 100 requests × 5 seconds = 100 threads blocked
Async: 100 requests × 5 seconds = 1 thread, 100 coroutines
```

### Decision: Async Everywhere

```python
# All external calls are async
async def retrieve_and_answer(query: str, db: AsyncSession):
    # 1. Embed query (100ms, non-blocking)
    embedding = await embedding_service.embed_query(query)

    # 2. Vector search (50ms, non-blocking)
    chunks = await vector_store.search(db, embedding)

    # 3. LLM call (5000ms, non-blocking!)
    response = await llm_client.complete(build_prompt(query, chunks))

    return response
```

**Result:** Single process handles hundreds of concurrent LLM requests

### Trade-offs Encountered

| Challenge | Solution |
|-----------|----------|
| Async SQLAlchemy learning curve | อ่าน docs, เข้าใจ session lifecycle |
| Connection pool exhaustion | Proper pool size tuning |
| Debugging async stack traces | Better logging, trace IDs |
| Testing async code | pytest-asyncio, async fixtures |

---

## 🗄️ "ทำไมใช้ PostgreSQL + pgvector?"

### The Alternatives Considered

| Option | Pros | Cons |
|--------|------|------|
| **Pinecone** | Managed, fast, scalable | $$, separate service, sync complexity |
| **Weaviate** | Open source, feature-rich | Another DB to manage, operational overhead |
| **Chroma** | Simple, embedded | Not production-ready, SQLite-based |
| **pgvector** | Integrated with Postgres | Newer, less optimized for billions |

### Why pgvector Won

**1. Single Database = Simpler Operations**

```python
# Without pgvector (2 databases)
async def save_document(doc, chunks, embeddings):
    # Save to Postgres
    await postgres.insert(doc)
    await postgres.insert_many(chunks)

    # Sync to Pinecone (what if this fails?)
    await pinecone.upsert(embeddings)

    # Consistency nightmare!


# With pgvector (1 database)
async def save_document(doc, chunks, embeddings):
    async with db.begin():
        db.add(Document(**doc))
        for chunk, emb in zip(chunks, embeddings):
            db.add(DocumentChunk(content=chunk, embedding=emb))
        # All or nothing - ACID transaction!
```

**2. JOINs กับ Relational Data**

```sql
-- pgvector allows filtering BEFORE vector search
SELECT c.content, c.embedding <=> $query AS distance
FROM document_chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.user_id = $user_id              -- Filter first
  AND d.project_id = $project_id        -- Reduce search space
ORDER BY distance
LIMIT 10;
```

**3. Cost & Simplicity**

- ไม่มี additional monthly cost (vs Pinecone ~$70/month minimum)
- ไม่ต้อง manage separate service
- Standard Postgres backup/restore

### Limitations Accepted

- **Scale:** pgvector handles millions, not billions (acceptable for our use case)
- **Speed:** HNSW index ต้อง tune เอง (vs managed services auto-optimize)

---

## 🔄 "Request Flow เป็นอย่างไร?"

### Complete Request Lifecycle

```
1. Request Arrives
   │
   ▼
2. CORS Middleware → Check allowed origins
   │
   ▼
3. TraceContextMiddleware → Generate trace_id, attach to request
   │
   ▼
4. MetricsMiddleware → Start timing
   │
   ▼
5. Route Handler
   │
   ├── Dependency: get_db() → Create DB session
   ├── Dependency: get_current_user() → Verify JWT
   ├── Dependency: RateLimiter() → Check rate limit
   │
   ▼
6. Service Layer → Business logic
   │
   ▼
7. Response
   │
   ├── Commit DB transaction
   ├── Close DB session
   ├── Record metrics
   │
   ▼
8. BaseResponse wrapper → {trace_id, data, error}
```

### Code Walkthrough

```python
# main.py - Middleware stack
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS)
app.add_middleware(TraceContextMiddleware)
app.add_middleware(MetricsMiddleware)

# routes/chat.py - Route handler
@router.post("/chat/stream")
@limiter.limit("30/minute")
async def stream_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # All dependencies resolved before this runs
    ctx = get_context()

    async def generate():
        async for chunk in rag_service.stream_answer(
            db=db,
            query=request.message,
            user_id=user.id,
            document_ids=request.document_ids
        ):
            yield f"data: {json.dumps({'content': chunk})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 🎭 "Singleton Pattern ใช้ตรงไหน?"

### Problem: Creating Expensive Clients

```python
# ❌ Create client every request - expensive!
@router.post("/embed")
async def embed(text: str):
    client = LiteLLMClient(api_key=API_KEY)  # New client!
    return await client.embed(text)
```

### Solution: Singleton Services

```python
# services/embedding.py
_embedding_service: EmbeddingService | None = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService(
            model="text-embedding-004",
            api_key=settings.LITELLM_API_KEY
        )
    return _embedding_service


# Usage in route
@router.post("/embed")
async def embed(text: str):
    service = get_embedding_service()  # Reuse instance
    return await service.embed(text)
```

### Applied To

| Service | Why Singleton |
|---------|---------------|
| `EmbeddingService` | HTTP client pool reuse |
| `LLMClient` | Connection pooling |
| `VectorStore` | Configuration cached |
| `StripeClient` | API client reuse |

---

## 📊 Summary: Architecture Decisions

| Decision | Alternative | Why This Choice |
|----------|-------------|-----------------|
| **Layered Architecture** | Fat controllers | Testability, reusability |
| **Async Python** | Sync | LLM calls are slow, need concurrency |
| **pgvector** | Pinecone/Weaviate | Simplicity, ACID, cost |
| **FastAPI DI** | Global state | Explicit, testable |
| **Service Singletons** | New instance per request | Performance |
| **BaseResponse wrapper** | Raw responses | Consistency, tracing |

---

*ต่อไป: [03-rag-deep-dive.md](./03-rag-deep-dive.md) — Deep dive into RAG pipeline*
