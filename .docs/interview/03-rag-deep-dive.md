# 03 - RAG Deep Dive: Building the Intelligence Layer

---

## 🧠 "อธิบาย RAG Pipeline ของคุณหน่อย"

### What is RAG and Why?

**RAG = Retrieval-Augmented Generation**

LLMs มีปัญหาหลัก 2 อย่าง:
1. **Knowledge Cutoff** — ไม่รู้ข้อมูลหลัง training date
2. **No Private Data** — ไม่รู้จัก internal documents ขององค์กร

**RAG แก้ปัญหานี้โดย:**
```
Query → Find relevant documents → Include in prompt → LLM generates answer
```

ไม่ต้อง fine-tune model ใหม่ — แค่ "บอก" LLM ว่าข้อมูลที่เกี่ยวข้องคืออะไร

---

### The Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     INDEXING PHASE (Offline)                     │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │  Upload  │ → │ Extract  │ → │  Chunk   │ → │  Embed   │     │
│  │  (PDF)   │   │  (Text)  │   │ (2000ch) │   │ (768dim) │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                                      │          │
│                                               ┌──────▼──────┐   │
│                                               │   pgvector  │   │
│                                               │   Storage   │   │
│                                               └─────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     QUERY PHASE (Online)                         │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │  Query   │ → │  Embed   │ → │  Search  │ → │  Top-K   │     │
│  │  (Text)  │   │  Query   │   │ pgvector │   │  Chunks  │     │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘     │
│                                                      │          │
│                                               ┌──────▼──────┐   │
│  ┌──────────┐   ┌──────────┐                 │   Build     │   │
│  │ Response │ ← │   LLM    │ ← ─ ─ ─ ─ ─ ─ ─ │   Prompt    │   │
│  │          │   │ Generate │                 │             │   │
│  └──────────┘   └──────────┘                 └─────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📄 Document Processing: "รองรับไฟล์อะไรบ้าง? ทำยังไง?"

### Supported Formats

| Format | Library | Challenges |
|--------|---------|------------|
| **PDF** | PyMuPDF (fitz) | Tables, images, multi-column layouts |
| **DOCX** | python-docx | Styles, headers/footers |
| **TXT/MD** | Built-in | Encoding issues |
| **CSV** | pandas | Structure preservation |

### The Strategy Pattern

```python
# document_processor.py
class DocumentProcessor:
    def __init__(self):
        self.extractors = {
            "application/pdf": PDFExtractor(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXExtractor(),
            "text/plain": TextExtractor(),
            "text/markdown": TextExtractor(),
            "text/csv": CSVExtractor(),
        }

    async def extract(self, file: UploadFile) -> ExtractedDocument:
        extractor = self.extractors.get(file.content_type)
        if not extractor:
            raise UnsupportedFormatError(file.content_type)

        return await extractor.extract(file)


class PDFExtractor:
    async def extract(self, file: UploadFile) -> ExtractedDocument:
        content = await file.read()
        doc = fitz.open(stream=content, filetype="pdf")

        pages = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text("text")
            pages.append(PageContent(
                page_number=page_num,
                content=text,
                # Metadata for source attribution
                metadata={"page": page_num}
            ))

        return ExtractedDocument(pages=pages, total_pages=len(pages))
```

### Real Challenges Encountered

**Challenge 1: Scanned PDFs**

```python
# Some PDFs are just images - no text to extract!
text = page.get_text("text")
if len(text.strip()) < 50:
    # Probably a scanned image
    # TODO: Integrate OCR (Tesseract or cloud vision)
    logger.warning(f"Page {page_num} appears to be scanned - no text extracted")
```

**Status:** OCR not yet implemented — logged as limitation

**Challenge 2: Tables in PDFs**

```
Original Table:         Extracted Text:
┌────┬────┬────┐        "Name Age City
│Name│Age │City│         John 30 NYC
├────┼────┼────┤         Jane 25 LA"
│John│ 30 │NYC │
│Jane│ 25 │LA  │
└────┴────┴────┘
```

**Current Approach:** Accept degraded table extraction, recommend CSV for tabular data

---

## ✂️ Chunking Strategy: "ทำไมต้อง chunk? ทำยังไง?"

### Why Chunking is Necessary

**LLM Context Limits:**
- GPT-4: 128K tokens (~300 pages)
- Gemini: 1M tokens (~2500 pages)
- But cost scales with tokens!

**Embedding Quality:**
- Embeddings work best on focused text
- Entire document → generic embedding → poor retrieval

**Solution:** Split into smaller, meaningful chunks

### The Chunking Algorithm

```python
# text_chunker.py
class TextChunker:
    def __init__(
        self,
        chunk_size: int = 2000,      # Characters per chunk
        chunk_overlap: int = 200,    # Overlap between chunks
        min_chunk_size: int = 100    # Don't create tiny chunks
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str, metadata: dict = None) -> list[Chunk]:
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size

            # Find a good break point (sentence/paragraph)
            if end < len(text):
                end = self._find_break_point(text, end)

            chunk_text = text[start:end].strip()

            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(Chunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    start_char=start,
                    end_char=end,
                    metadata={
                        **(metadata or {}),
                        "chunk_index": chunk_index
                    }
                ))
                chunk_index += 1

            # Move start, accounting for overlap
            start = end - self.chunk_overlap

        return chunks

    def _find_break_point(self, text: str, position: int) -> int:
        """Find nearest sentence/paragraph end"""
        # Look for paragraph break first
        para_break = text.rfind("\n\n", position - 200, position + 200)
        if para_break != -1:
            return para_break + 2

        # Look for sentence end
        for punct in [". ", "! ", "? "]:
            sent_break = text.rfind(punct, position - 100, position + 100)
            if sent_break != -1:
                return sent_break + 2

        # Fallback to exact position
        return position
```

### Visual Example

```
Document: "Lorem ipsum dolor sit amet, consectetur adipiscing elit.
           Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
           Ut enim ad minim veniam, quis nostrud exercitation..."

Chunk 1 (0-2000): "Lorem ipsum dolor sit amet... exercitation"
                                                    ↑
Chunk 2 (1800-3800): "...quis nostrud exercitation... consequat"
                      ↑ overlap ↑
Chunk 3 (3600-5600): "...Duis aute irure dolor... laboris nisi"
```

### Why Overlap?

```
Without overlap:
"...the company's annual revenue was" | "$50 million in 2023..."
         Chunk 1                      |         Chunk 2

Query: "What was the company's revenue in 2023?"
→ Neither chunk has complete answer!

With overlap:
"...the company's annual revenue was $50 million in 2023..."
         Chunk 1                     ↑ Overlap contains answer ↑

Query: "What was the company's revenue in 2023?"
→ Chunk 1 has complete answer
```

---

## 🔢 Embedding: "ใช้ embedding model อะไร? ทำไม?"

### Model Selection

| Model | Dimensions | Provider | Cost | Quality |
|-------|------------|----------|------|---------|
| **text-embedding-004** | 768 | Google | Low | High |
| text-embedding-3-small | 1536 | OpenAI | Medium | High |
| text-embedding-3-large | 3072 | OpenAI | High | Highest |

**Choice: text-embedding-004 (Gemini)**
- 768 dimensions = smaller storage, faster search
- Quality comparable to OpenAI
- Lower cost per token
- Consistent with using Gemini for LLM

### Embedding Service Implementation

```python
# embedding_service.py
class EmbeddingService:
    def __init__(self):
        self.model = "text-embedding-004"
        self.client = httpx.AsyncClient(
            base_url=settings.LITELLM_BASE_URL,
            timeout=30.0
        )

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query - optimized for speed"""
        response = await self.client.post(
            "/embeddings",
            json={
                "model": self.model,
                "input": text
            }
        )
        return response.json()["data"][0]["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts - optimized for throughput"""
        # Batch for efficiency
        BATCH_SIZE = 100
        all_embeddings = []

        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            response = await self.client.post(
                "/embeddings",
                json={
                    "model": self.model,
                    "input": batch
                }
            )
            embeddings = [d["embedding"] for d in response.json()["data"]]
            all_embeddings.extend(embeddings)

        return all_embeddings
```

### Embedding Characteristics

```python
# What embeddings capture
text1 = "The cat sat on the mat"
text2 = "A feline rested on the rug"      # Similar meaning!
text3 = "Python is a programming language"  # Different topic

embed1 = await service.embed_query(text1)  # [0.1, -0.3, 0.5, ...]
embed2 = await service.embed_query(text2)  # [0.12, -0.28, 0.48, ...]  ← Similar!
embed3 = await service.embed_query(text3)  # [-0.4, 0.2, 0.1, ...]    ← Different

cosine_similarity(embed1, embed2) = 0.95  # High similarity
cosine_similarity(embed1, embed3) = 0.23  # Low similarity
```

---

## 🔍 Vector Search: "pgvector ทำงานอย่างไร?"

### Storing Embeddings

```python
# models/document_chunk.py
class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID, primary_key=True, default=uuid4)
    document_id = Column(UUID, ForeignKey("documents.id"))
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer)

    # pgvector column - 768 dimensions
    embedding = Column(Vector(768))

    metadata = Column(JSONB, default={})
```

```sql
-- Create index for faster search
CREATE INDEX ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Or HNSW for better recall
CREATE INDEX ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Search Implementation

```python
# vector_store.py
class PgVectorStore:
    async def search(
        self,
        db: AsyncSession,
        query_embedding: list[float],
        user_id: UUID,
        document_ids: list[UUID] | None = None,
        top_k: int = 5
    ) -> list[ChunkResult]:
        # Build query with filters
        query = select(
            DocumentChunk.id,
            DocumentChunk.content,
            DocumentChunk.metadata,
            # Cosine distance (0 = identical, 2 = opposite)
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
        ).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            Document.user_id == user_id  # User isolation!
        )

        # Optional: filter to specific documents
        if document_ids:
            query = query.where(Document.id.in_(document_ids))

        # Order by similarity, limit results
        query = query.order_by("distance").limit(top_k)

        result = await db.execute(query)

        return [
            ChunkResult(
                chunk_id=row.id,
                content=row.content,
                metadata=row.metadata,
                score=1 - row.distance  # Convert distance to similarity
            )
            for row in result.fetchall()
        ]
```

### Why Filter BEFORE Vector Search?

```sql
-- ❌ Search entire database, then filter
SELECT * FROM document_chunks
ORDER BY embedding <=> $query
LIMIT 100;
-- Then filter by user_id in application...
-- Problem: Searched millions of irrelevant chunks!

-- ✅ Filter first, then search subset
SELECT * FROM document_chunks c
JOIN documents d ON c.document_id = d.id
WHERE d.user_id = $user_id  -- Only this user's 1000 chunks
ORDER BY c.embedding <=> $query
LIMIT 5;
-- Much faster, more relevant results!
```

---

## 💬 Prompt Engineering: "RAG prompt หน้าตาเป็นอย่างไร?"

### The RAG Prompt Template

```python
# rag_service.py
RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions based on the provided context.

INSTRUCTIONS:
1. Answer ONLY based on the provided context
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question"
3. When citing information, mention the source (e.g., "According to [filename]...")
4. Be concise and accurate
5. Never make up information

CONTEXT:
{context}

---
Answer the user's question based on the above context."""


def build_rag_prompt(query: str, chunks: list[ChunkResult]) -> list[ChatMessage]:
    # Build context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("filename", f"Source {i}")
        page = chunk.metadata.get("page", "")
        page_info = f", Page {page}" if page else ""

        context_parts.append(f"[{source}{page_info}]\n{chunk.content}")

    context = "\n\n---\n\n".join(context_parts)

    return [
        ChatMessage(
            role="system",
            content=RAG_SYSTEM_PROMPT.format(context=context)
        ),
        ChatMessage(
            role="user",
            content=query
        )
    ]
```

### Real Example

```
SYSTEM: You are a helpful assistant...

CONTEXT:
[company_policy.pdf, Page 12]
Annual leave policy: All full-time employees are entitled to 15 days
of paid annual leave per year. Leave must be requested at least 2 weeks
in advance and approved by the direct supervisor.

---

[hr_handbook.pdf, Page 45]
Sick leave: Employees can take up to 30 days of sick leave per year
with a valid medical certificate. For absences longer than 3 days,
a doctor's note is required.

---

USER: How many days of annual leave do I get?

ASSISTANT: According to the company policy (company_policy.pdf, Page 12),
full-time employees are entitled to 15 days of paid annual leave per year.
Leave must be requested at least 2 weeks in advance and approved by your
direct supervisor.
```

---

## 📊 Source Attribution: "ทำให้ user รู้ว่าข้อมูลมาจากไหน"

### Why Sources Matter

```
Without sources:
AI: "The company revenue was $50 million"
User: "How do I know this is accurate?"

With sources:
AI: "According to Annual Report 2023 (page 15), the company revenue was $50 million"
User: "I can verify this!" ✓
```

### Implementation

```python
# After getting LLM response, compile sources
async def answer_with_sources(
    query: str,
    db: AsyncSession,
    user_id: UUID
) -> AnswerWithSources:
    # 1. Retrieve chunks
    chunks = await vector_store.search(db, embed(query), user_id)

    # 2. Generate answer
    answer = await llm.complete(build_rag_prompt(query, chunks))

    # 3. Compile sources
    sources = []
    seen_docs = set()
    for chunk in chunks:
        doc_id = chunk.metadata.get("document_id")
        if doc_id not in seen_docs:
            sources.append(Source(
                document_id=doc_id,
                filename=chunk.metadata.get("filename"),
                page=chunk.metadata.get("page"),
                relevance_score=chunk.score
            ))
            seen_docs.add(doc_id)

    return AnswerWithSources(
        answer=answer,
        sources=sources
    )
```

### Frontend Display

```svelte
<div class="answer">
  {@html answer}
</div>

<div class="sources">
  <h4>Sources:</h4>
  {#each sources as source}
    <a href="/documents/{source.document_id}">
      📄 {source.filename}
      {#if source.page}(Page {source.page}){/if}
      <span class="score">{(source.relevance_score * 100).toFixed(0)}% match</span>
    </a>
  {/each}
</div>
```

---

## 🚀 Streaming: "ทำไมต้อง stream? ทำยังไง?"

### The UX Problem

```
Non-streaming:
User clicks send → Waits 5 seconds → Full response appears
User: "Is it working? Did it crash?"

Streaming:
User clicks send → First word appears in 200ms → Words flow in
User: "It's thinking! I can see progress!"
```

### SSE Implementation

```python
# routes/chat.py
@router.post("/chat/stream")
async def stream_chat(request: ChatRequest, ...):
    async def generate():
        # 1. Retrieve context
        chunks = await rag_service.retrieve(request.message, user_id)

        # 2. Stream LLM response
        async for token in llm_client.stream_completion(
            messages=build_rag_prompt(request.message, chunks)
        ):
            yield f"event: message\ndata: {json.dumps({'content': token})}\n\n"

        # 3. Send sources after content complete
        sources = compile_sources(chunks)
        yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

        # 4. Signal completion
        yield f"event: done\ndata: {{}}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )
```

```typescript
// Frontend SSE handling
const eventSource = new EventSource('/api/v1/chat/stream', {
  method: 'POST',
  body: JSON.stringify({ message: query })
});

let fullResponse = '';

eventSource.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  fullResponse += data.content;
  updateUI(fullResponse);  // Update in real-time
});

eventSource.addEventListener('sources', (event) => {
  const sources = JSON.parse(event.data);
  displaySources(sources);
});

eventSource.addEventListener('done', () => {
  eventSource.close();
});
```

---

## 📈 Performance Considerations

### Latency Breakdown

```
Typical RAG query:
├── Embed query:      100-200ms
├── Vector search:     50-100ms
├── Build prompt:       10-20ms
├── LLM generation: 1000-5000ms (streamed)
└── Total TTFB:       200-400ms (time to first byte)
```

### Optimizations Applied

| Optimization | Before | After |
|--------------|--------|-------|
| Async embedding | 500ms (sync) | 150ms (async) |
| Batch embedding on upload | 100 API calls | 1 batch call |
| Filter before search | Search 1M chunks | Search 1K chunks |
| Connection pooling | New connection/request | Reuse connections |

---

## 🎯 Key Takeaways

เมื่อถูกถามเกี่ยวกับ RAG ควรพูดถึง:

1. **Pipeline Understanding** — ไม่ใช่แค่ "ใช้ LangChain" แต่เข้าใจทุก step
2. **Chunking Strategy** — ทำไม overlap? ขนาดเท่าไหร่? break points?
3. **Embedding Choice** — model ไหน? dimensions? trade-offs?
4. **Search Optimization** — filter before search, indexing, scoping
5. **Source Attribution** — ทำให้ answers verifiable
6. **Streaming UX** — ทำไมสำคัญ? implement อย่างไร?

---

*ต่อไป: [04-database-design.md](./04-database-design.md) — Database schema and pgvector deep dive*
