# 06 - Challenges: Real Problems & How I Solved Them

---

## 🔥 "เจอปัญหาอะไรบ้างตอนทำโปรเจ็คนี้?"

ส่วนนี้รวบรวมปัญหาจริงที่เจอระหว่างพัฒนา พร้อมวิธีแก้ไข — เป็น content ที่ดีสำหรับ behavioral interview

---

## 📄 Challenge 1: Document Processing Pipeline

### The Problem

> "อัพโหลด PDF แล้ว text ออกมาเป็น garbage"

เมื่อ users อัพโหลด PDF บาง files ได้ผลลัพธ์แปลกๆ:
- Text เรียงผิดลำดับ (multi-column layouts)
- ตัวอักษรหาย (embedded fonts)
- ไม่มี text เลย (scanned documents)
- Tables กลายเป็น text ธรรมดา

### The Investigation

```python
# Debug: ดูว่า PDF แต่ละหน้ามี text อะไรบ้าง
import fitz  # PyMuPDF

doc = fitz.open("problem.pdf")
for page_num, page in enumerate(doc):
    text = page.get_text("text")
    print(f"Page {page_num}: {len(text)} chars")
    print(text[:500])  # First 500 chars
```

**Findings:**
1. Multi-column PDFs → text extraction reads left-to-right across columns
2. Scanned PDFs → no text layer, needs OCR
3. Complex layouts → reading order wrong

### The Solution

```python
# document_processor.py

class PDFExtractor:
    async def extract(self, file: UploadFile) -> ExtractedDocument:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")

        pages = []
        for page_num, page in enumerate(doc, 1):
            # Try different extraction methods
            text = self._extract_with_fallback(page)

            if len(text.strip()) < 50:
                # Probably scanned - log warning
                logger.warning(
                    f"Page {page_num} has minimal text - may be scanned",
                    extra={"document": file.filename}
                )

            pages.append(PageContent(
                page_number=page_num,
                content=text,
                metadata={"page": page_num}
            ))

        return ExtractedDocument(pages=pages, total_pages=len(pages))

    def _extract_with_fallback(self, page) -> str:
        # Method 1: Standard text extraction
        text = page.get_text("text")

        if len(text.strip()) > 100:
            return text

        # Method 2: Try with layout preservation
        text = page.get_text("blocks")
        if text:
            # Sort blocks by position (top-to-bottom, left-to-right)
            sorted_blocks = sorted(text, key=lambda b: (b[1], b[0]))
            return "\n".join(b[4] for b in sorted_blocks if b[4].strip())

        # Method 3: Raw text as last resort
        return page.get_text("rawdict").get("text", "")
```

### Lessons Learned

1. **Don't assume uniform input** — PDFs vary wildly in structure
2. **Graceful degradation** — Extract what you can, warn about the rest
3. **Multiple strategies** — Have fallbacks for edge cases
4. **User feedback** — Show warning when extraction quality is poor

### Current Limitation

> "Scanned PDFs ยังไม่รองรับ OCR"

**Why not add OCR now?**
- Tesseract adds complexity and dependencies
- Cloud OCR (Google Vision) adds cost
- Most users have text-based PDFs
- Logged as future enhancement

---

## 🔢 Challenge 2: Embedding Batch Performance

### The Problem

> "Upload เอกสาร 100 หน้า ใช้เวลา 5 นาที"

เมื่อ document มี chunks เยอะ การ embed ทีละ chunk ช้ามาก:

```python
# ❌ Slow: 100 chunks × 200ms = 20 seconds just for embedding
for chunk in chunks:
    embedding = await embed_single(chunk.content)
    chunk.embedding = embedding
```

### The Investigation

```python
# Profile the upload process
import time

start = time.time()
chunks = chunker.chunk(text)  # 0.1s
print(f"Chunking: {time.time() - start:.2f}s")

start = time.time()
for chunk in chunks:
    await embedding_service.embed_single(chunk)  # 200ms each!
print(f"Embedding: {time.time() - start:.2f}s")  # 20s for 100 chunks!
```

**Bottleneck:** Network round-trip per embedding call

### The Solution: Batch Embedding

```python
# embedding_service.py

class EmbeddingService:
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a single API call"""

        # LiteLLM/OpenAI support batch embedding
        BATCH_SIZE = 100  # API limit

        all_embeddings = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]

            response = await self.client.post(
                "/embeddings",
                json={
                    "model": self.model,
                    "input": batch  # Multiple texts!
                }
            )

            data = response.json()
            embeddings = [item["embedding"] for item in data["data"]]
            all_embeddings.extend(embeddings)

        return all_embeddings


# Usage in document processing
async def process_document(file: UploadFile, db: AsyncSession):
    text = await extract_text(file)
    chunks = chunker.chunk(text)

    # Batch embed all chunks at once
    texts = [chunk.content for chunk in chunks]
    embeddings = await embedding_service.embed_batch(texts)  # 1-2 API calls!

    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding

    # Save all at once
    db.add_all(chunks)
    await db.commit()
```

### Results

| Approach | 100 Chunks | 500 Chunks |
|----------|------------|------------|
| Sequential | 20s | 100s |
| Batched | 2s | 8s |
| **Improvement** | **10x** | **12x** |

### Lessons Learned

1. **Profile before optimizing** — Find the actual bottleneck
2. **Use batch APIs** — Most services support batching
3. **Reduce network calls** — Latency compounds quickly

---

## 🔍 Challenge 3: Vector Search Performance

### The Problem

> "Search ช้าเมื่อมี documents เยอะ"

เมื่อ user มี 1000+ documents (100K+ chunks) search เริ่มช้า:

```sql
-- Naive search: scan all vectors
SELECT * FROM document_chunks
ORDER BY embedding <=> $query_embedding
LIMIT 5;
-- 500ms+ for 100K vectors
```

### The Investigation

```sql
EXPLAIN ANALYZE
SELECT id, content, embedding <=> $query AS distance
FROM document_chunks
ORDER BY distance
LIMIT 5;

-- Output:
-- Seq Scan on document_chunks (cost=0.00..25000.00)
-- Sort (cost=25000.00..25001.00)
-- No index usage!
```

### The Solution: Scoped Search + Indexing

**1. Filter Before Search**

```python
# vector_store.py

async def search(
    self,
    db: AsyncSession,
    query_embedding: list[float],
    user_id: UUID,
    document_ids: list[UUID] | None = None,
    top_k: int = 5
) -> list[ChunkResult]:

    query = select(
        DocumentChunk.id,
        DocumentChunk.content,
        DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
    ).join(
        Document, DocumentChunk.document_id == Document.id
    ).where(
        Document.user_id == user_id  # Filter first!
    )

    if document_ids:
        query = query.where(Document.id.in_(document_ids))

    query = query.order_by("distance").limit(top_k)

    result = await db.execute(query)
    return [ChunkResult(**row._asdict()) for row in result.fetchall()]
```

**2. HNSW Index**

```sql
-- Create HNSW index for approximate nearest neighbor
CREATE INDEX ix_chunks_embedding_hnsw
ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Set search parameters
SET hnsw.ef_search = 100;  -- Higher = better recall, slower
```

**3. Partial Index per User (Future)**

```sql
-- For high-volume users, consider partial indexes
CREATE INDEX ix_chunks_user_123
ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WHERE document_id IN (SELECT id FROM documents WHERE user_id = 'user-123');
```

### Results

| Scenario | Before | After |
|----------|--------|-------|
| 10K chunks, global search | 200ms | 200ms |
| 100K chunks, global search | 500ms | 450ms |
| 100K chunks, user-scoped (1K) | 500ms | **50ms** |

### Lessons Learned

1. **Filter before search** — Reduce search space dramatically
2. **Indexes matter** — HNSW for large vector sets
3. **User isolation helps performance** — Multi-tenant scoping is a feature

---

## 🌊 Challenge 4: Streaming Response Handling

### The Problem

> "Client disconnect ระหว่าง streaming ทำให้ server error"

เมื่อ user ปิด browser ระหว่าง LLM กำลัง stream:

```
ERROR: Connection reset by peer
ERROR: Cannot write to closed stream
```

### The Investigation

```python
# Original code - no disconnect handling
@router.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    async def generate():
        async for chunk in llm.stream_completion(messages):
            yield f"data: {json.dumps({'content': chunk})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Problem:** Generator continues even after client disconnects

### The Solution: Graceful Disconnect Handling

```python
# routes/chat.py
from starlette.requests import Request

@router.post("/chat/stream")
async def stream_chat(
    chat_request: ChatRequest,
    request: Request,  # Starlette request for disconnect check
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    async def generate():
        try:
            async for chunk in rag_service.stream_answer(
                db=db,
                query=chat_request.message,
                user_id=user.id
            ):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping stream")
                    break

                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # Send completion event
            if not await request.is_disconnected():
                yield "event: done\ndata: {}\n\n"

        except asyncio.CancelledError:
            logger.info("Stream cancelled")
            raise

        except Exception as e:
            logger.exception("Stream error")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
```

### Frontend Error Handling

```typescript
// Frontend SSE handling
const eventSource = new EventSource('/api/chat/stream', {...});

eventSource.onerror = (event) => {
    if (eventSource.readyState === EventSource.CLOSED) {
        console.log('Stream ended normally');
    } else {
        console.error('Stream error, attempting reconnect...');
        // Optionally retry
    }
    eventSource.close();
};

// Clean up on component unmount
onDestroy(() => {
    eventSource.close();
});
```

### Lessons Learned

1. **Always handle disconnects** — Clients disconnect unexpectedly
2. **Check connection state** — `request.is_disconnected()` in FastAPI
3. **Clean up resources** — Don't leave dangling LLM calls
4. **Frontend cleanup** — Close EventSource on unmount

---

## 💾 Challenge 5: Database Connection Pool Exhaustion

### The Problem

> "ทำไม API response เริ่มช้าลง แล้วก็ timeout"

หลังจาก deploy ไป production สักพัก:

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 10 reached
```

### The Investigation

```python
# Check connection usage
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "checkout")
def log_checkout(dbapi_connection, connection_record, connection_proxy):
    logger.debug(f"Connection checked out: {connection_record}")

@event.listens_for(engine.sync_engine, "checkin")
def log_checkin(dbapi_connection, connection_record):
    logger.debug(f"Connection returned: {connection_record}")
```

**Finding:** Connections checked out but never returned — leaked!

```python
# The bug
async def get_document(db: AsyncSession, doc_id: UUID):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    if not result:
        raise HTTPException(404)  # Connection not returned!
    return result.scalar_one()
```

### The Solution

**1. Always Use Context Manager**

```python
# database.py
from contextlib import asynccontextmanager

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        # Session automatically closed by context manager
```

**2. Proper Pool Configuration**

```python
# database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Base pool size
    max_overflow=30,        # Extra connections when needed
    pool_timeout=30,        # Wait time for connection
    pool_recycle=1800,      # Recycle connections every 30 min
    pool_pre_ping=True,     # Check connection health
)
```

**3. Connection Health Monitoring**

```python
# health.py
@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    # Check DB connection
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        return {"status": "unhealthy", "db": str(e)}

    # Check pool status
    pool = db.get_bind().pool
    return {
        "status": "healthy",
        "db_pool": {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow()
        }
    }
```

### Lessons Learned

1. **Always use context managers** — Ensures cleanup
2. **Monitor pool metrics** — Know when you're running low
3. **Set appropriate pool sizes** — Based on expected concurrency
4. **Pool pre-ping** — Detect stale connections

---

## 🔒 Challenge 6: Race Condition in Usage Tracking

### The Problem

> "Usage credits ไม่ตรงกับจำนวน requests จริง"

Users complained credits deducted wrong:
- Sometimes too many
- Sometimes too few
- Inconsistent

### The Investigation

```python
# Original code
async def record_usage(db: AsyncSession, user_id: UUID, credits: int):
    # Get current subscription
    sub = await db.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )
    subscription = sub.scalar_one()

    # Update credits
    subscription.credits_used += credits  # Race condition!
    await db.commit()
```

**Problem:** Concurrent requests read same value, both increment, one update lost

```
Request A: Read credits_used = 100
Request B: Read credits_used = 100
Request A: Write credits_used = 105
Request B: Write credits_used = 103  # Overwrites A's update!
```

### The Solution: Atomic Update

```python
# services/usage.py
from sqlalchemy import update

async def record_usage(
    db: AsyncSession,
    user_id: UUID,
    credits: int,
    request_type: str,
    model: str,
    tokens_input: int,
    tokens_output: int,
    latency_ms: int
):
    # 1. Atomic credit update
    await db.execute(
        update(Subscription)
        .where(Subscription.user_id == user_id)
        .values(credits_used=Subscription.credits_used + credits)  # Atomic!
    )

    # 2. Create usage record
    usage = UsageRecord(
        user_id=user_id,
        request_type=request_type,
        model=model,
        credits_used=credits,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        latency_ms=latency_ms
    )
    db.add(usage)

    await db.commit()
```

**Alternative: SELECT FOR UPDATE**

```python
async def deduct_credits_with_lock(db: AsyncSession, user_id: UUID, credits: int):
    # Lock the row
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .with_for_update()  # Row-level lock
    )
    subscription = result.scalar_one()

    if subscription.credits_used + credits > subscription.credits_limit:
        raise InsufficientCreditsError()

    subscription.credits_used += credits
    await db.commit()
```

### Lessons Learned

1. **Identify concurrent operations** — Anything that reads-then-writes
2. **Use atomic updates** — SQL `SET x = x + 1` is atomic
3. **Use locks when needed** — `FOR UPDATE` for complex logic
4. **Test concurrent scenarios** — Use load testing

---

## 📊 Challenge Summary

| Challenge | Root Cause | Solution |
|-----------|------------|----------|
| PDF extraction | Varied document formats | Multiple extraction strategies + fallbacks |
| Slow embedding | Sequential API calls | Batch embedding |
| Slow vector search | No filtering/indexing | User-scoped search + HNSW index |
| Stream disconnect | No disconnect handling | Check `is_disconnected()` |
| Connection pool | Leaked connections | Context managers + proper config |
| Race condition | Read-modify-write | Atomic SQL updates |

---

## 🎯 Interview Tips

เมื่อถูกถาม "Tell me about a challenging problem you solved":

1. **Describe the symptom** — "Users reported slow uploads"
2. **Explain investigation** — "I profiled and found embedding was the bottleneck"
3. **Show the solution** — "I implemented batch embedding, reducing time by 10x"
4. **Share the lesson** — "I learned to always profile before optimizing"

**Structure:** Situation → Task → Action → Result (STAR)

---

*ต่อไป: [07-lessons-learned.md](./07-lessons-learned.md) — Reflections and what I'd do differently*
