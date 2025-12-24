# 04 - Database Design: Schema, pgvector, and Data Modeling

---

## 🗄️ "อธิบาย Database Schema หน่อย"

### The Core Domain Model

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │──1:N──│   Project   │──1:N──│    Agent    │
└─────────────┘       └─────────────┘       └─────────────┘
       │                     │                     │
       │                     │                     │
      1:N                  M:N                   links
       │                     │                     │
       ▼                     ▼                     ▼
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Document   │◄──────│ProjectDocs  │       │ Linked Docs │
└─────────────┘       │   (M:N)     │       └─────────────┘
       │              └─────────────┘
       │
      1:N
       │
       ▼
┌─────────────┐
│DocumentChunk│◄── embedding (768-dim vector)
└─────────────┘


┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │──1:N──│Conversation │──1:N──│   Message   │
└─────────────┘       └─────────────┘       └─────────────┘


┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │──1:N──│ Subscription│──1:N──│   Invoice   │
└─────────────┘       └─────────────┘       └─────────────┘
       │                     │
       │                    1:1
       │                     │
      1:N                    ▼
       │              ┌─────────────┐
       │              │    Plan     │
       │              └─────────────┘
       ▼
┌─────────────┐
│ UsageRecord │
└─────────────┘
```

---

## 👤 User Model: "Authentication & Multi-tenancy"

### The User Table

```python
# models/user.py
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))
    avatar_url = Column(String(500))

    # Status & Permissions
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    tier = Column(String(50), default="free")  # free, pro, enterprise

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user")
```

### Design Decisions

**Why `tier` on User?**
```python
# Fast access control without joining subscription table
if user.tier == "free":
    raise HTTPException(403, "Upgrade to access this feature")
```

**Why `cascade="all, delete-orphan"`?**
```python
# When user is deleted, all their data is deleted
await db.delete(user)  # Documents, agents, conversations... all gone
```

---

## 📄 Document & Chunk Models: "The RAG Data Layer"

### Document Table

```python
# models/document.py
class DocumentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # File info
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer)  # bytes
    file_path = Column(String(500))  # storage location

    # Processing status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    error_message = Column(Text)

    # Stats
    chunk_count = Column(Integer, default=0)

    # Metadata
    description = Column(Text)
    tags = Column(ARRAY(String), default=[])

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))

    # Indexes for common queries
    __table_args__ = (
        Index("ix_documents_user_status", "user_id", "status"),
        Index("ix_documents_user_created", "user_id", "created_at"),
    )
```

### DocumentChunk Table (with pgvector)

```python
# models/document_chunk.py
from pgvector.sqlalchemy import Vector

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID, primary_key=True, default=uuid4)
    document_id = Column(UUID, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)

    # Content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order in document

    # The star of the show: 768-dimensional embedding
    embedding = Column(Vector(768))

    # Metadata for source attribution
    metadata = Column(JSONB, default={})
    # Example: {"page": 5, "section": "Introduction", "start_char": 1000}

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_chunks_document", "document_id"),
        # Vector index for similarity search
        Index(
            "ix_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )
```

### The Relationship

```
Document (1) ──────── (N) DocumentChunk
    │                        │
    │                        │
    └── filename             └── embedding
    └── status                   content
    └── chunk_count              metadata (page, section)
```

---

## 🔍 pgvector Deep Dive: "Vector Search in PostgreSQL"

### Setting Up pgvector

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table with vector column
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    content TEXT NOT NULL,
    embedding VECTOR(768),  -- 768 dimensions
    metadata JSONB
);
```

### Index Types

**IVFFlat (Inverted File with Flat Compression)**
```sql
CREATE INDEX ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Pros: Faster index build, less memory
-- Cons: Lower recall, needs tuning
-- Best for: < 1M vectors
```

**HNSW (Hierarchical Navigable Small World)**
```sql
CREATE INDEX ON document_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Pros: Better recall, faster queries
-- Cons: Slower index build, more memory
-- Best for: Production, accuracy matters
```

### Why I Chose HNSW

```python
# We prioritize retrieval quality over index build time
# Documents are uploaded once, searched many times

# HNSW parameters:
# m = 16: Max connections per node (higher = better recall, more memory)
# ef_construction = 64: Build-time search depth (higher = better index, slower build)
```

### Search Operations

```python
# Cosine distance (0 = identical, 2 = opposite)
await db.execute(
    select(DocumentChunk)
    .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
    .limit(5)
)

# L2 (Euclidean) distance
.order_by(DocumentChunk.embedding.l2_distance(query_vector))

# Inner product (negative, for normalized vectors)
.order_by(DocumentChunk.embedding.max_inner_product(query_vector))
```

---

## 🤖 Agent Model: "AI Assistants with Tools"

```python
# models/agent.py
class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="SET NULL"))

    # Identity
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)  # URL-friendly
    description = Column(Text)
    avatar_url = Column(String(500))

    # Behavior
    system_prompt = Column(Text)

    # Tools this agent can use
    tools = Column(ARRAY(String), default=[])
    # Example: ["rag_search", "summarize", "calculator"]

    # Documents this agent has access to
    document_ids = Column(ARRAY(UUID), default=[])

    # Configuration
    config = Column(JSONB, default={})
    # Example: {"temperature": 0.7, "max_tokens": 2000}

    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Design Decisions

**Why `tools` as ARRAY instead of separate table?**
```python
# Tools are a fixed set, not user-created entities
# ARRAY is simpler and sufficient
tools = ["rag_search", "summarize"]

# vs. many-to-many relationship (overkill)
agent.tools → agent_tools → tools
```

**Why `document_ids` as ARRAY?**
```python
# Agent can access specific documents
# Allows scoped RAG searches
chunks = await vector_store.search(
    user_id=agent.user_id,
    document_ids=agent.document_ids  # Only these docs
)
```

---

## 🔄 Workflow Model: "Visual Automation"

```python
# models/workflow.py
class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID, ForeignKey("projects.id", ondelete="SET NULL"))

    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Visual editor data (from XYFlow)
    nodes = Column(JSONB, nullable=False, default=[])
    edges = Column(JSONB, nullable=False, default=[])
    viewport = Column(JSONB, default={"x": 0, "y": 0, "zoom": 1})

    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

### Why Store Nodes/Edges as JSON?

```json
{
  "nodes": [
    {
      "id": "node-1",
      "type": "start",
      "position": {"x": 100, "y": 100},
      "data": {}
    },
    {
      "id": "node-2",
      "type": "llm",
      "position": {"x": 300, "y": 100},
      "data": {
        "prompt": "Summarize: {{input}}",
        "model": "gemini-2.0-flash"
      }
    },
    {
      "id": "node-3",
      "type": "end",
      "position": {"x": 500, "y": 100},
      "data": {}
    }
  ],
  "edges": [
    {"id": "e1", "source": "node-1", "target": "node-2"},
    {"id": "e2", "source": "node-2", "target": "node-3"}
  ]
}
```

**Advantages:**
1. **XYFlow Compatible** — Direct save/load from visual editor
2. **Flexible Schema** — Different node types have different data
3. **Atomic Updates** — Save entire workflow state at once
4. **Versioning** — Easy to snapshot entire workflow

**Trade-offs:**
- Can't query individual nodes efficiently
- No foreign key constraints on node references
- Acceptable because workflows are always loaded/saved as a unit

---

## 💰 Subscription & Usage: "Billing Data Model"

```python
# models/subscription.py
class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    PAUSED = "paused"
    EXPIRED = "expired"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, unique=True)
    plan_id = Column(UUID, ForeignKey("plans.id"), nullable=False)

    # Stripe integration
    stripe_subscription_id = Column(String(100), unique=True)
    stripe_customer_id = Column(String(100))

    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)

    # Billing cycle
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))

    # Usage tracking
    credits_used = Column(Integer, default=0)
    credits_limit = Column(Integer)  # From plan

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    canceled_at = Column(DateTime(timezone=True))


# models/usage_record.py
class UsageRecord(Base):
    __tablename__ = "usage_records"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # What was used
    request_type = Column(String(50), nullable=False)
    # chat, rag, embedding, image, tool

    model = Column(String(100))  # gemini-2.0-flash

    # Token counts
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)

    # Cost
    credits_used = Column(Integer, default=0)

    # Performance
    latency_ms = Column(Integer)

    # Context
    agent_id = Column(UUID, ForeignKey("agents.id", ondelete="SET NULL"))
    conversation_id = Column(UUID, ForeignKey("conversations.id", ondelete="SET NULL"))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_usage_user_created", "user_id", "created_at"),
        Index("ix_usage_user_type", "user_id", "request_type"),
    )
```

### Usage Analytics Query

```python
# Get user's usage this month
async def get_monthly_usage(db: AsyncSession, user_id: UUID) -> UsageSummary:
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)

    result = await db.execute(
        select(
            func.sum(UsageRecord.credits_used).label("total_credits"),
            func.sum(UsageRecord.tokens_input).label("total_input_tokens"),
            func.sum(UsageRecord.tokens_output).label("total_output_tokens"),
            func.count(UsageRecord.id).label("total_requests"),
            func.avg(UsageRecord.latency_ms).label("avg_latency")
        )
        .where(UsageRecord.user_id == user_id)
        .where(UsageRecord.created_at >= month_start)
    )

    return UsageSummary(**result.fetchone()._asdict())
```

---

## 📝 Audit Logging: "Who Did What When"

```python
# models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="SET NULL"))

    # Action details
    action = Column(String(100), nullable=False)
    # document_upload, agent_create, login, etc.

    resource_type = Column(String(50))
    resource_id = Column(UUID)

    # Additional context
    metadata = Column(JSONB, default={})
    # {"filename": "report.pdf", "size_bytes": 1024}

    # Request info
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(500))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_user_action", "user_id", "action"),
        Index("ix_audit_resource", "resource_type", "resource_id"),
    )
```

### Logging Usage

```python
# services/audit_log.py
async def log_action(
    db: AsyncSession,
    user_id: UUID,
    action: str,
    resource_type: str = None,
    resource_id: UUID = None,
    metadata: dict = None,
    request: Request = None
):
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata or {},
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    db.add(audit_log)
    await db.flush()
```

---

## 🔧 Migrations: "Evolving the Schema"

### Alembic Setup

```python
# alembic/versions/001_initial.py
def upgrade():
    # Enable pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        # ...
    )

    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE")),
        # ...
    )

    # Create document_chunks with vector column
    op.create_table(
        "document_chunks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(768)),  # pgvector type
        # ...
    )

    # Create HNSW index
    op.execute("""
        CREATE INDEX ix_chunks_embedding
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade():
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
```

### Migration Best Practices

```bash
# Create new migration
alembic revision --autogenerate -m "add_workflow_status"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

---

## 📊 Performance Optimizations

### Indexes Strategy

```python
# Composite indexes for common queries
__table_args__ = (
    # "Get user's documents ordered by date"
    Index("ix_documents_user_created", "user_id", "created_at"),

    # "Get user's documents by status"
    Index("ix_documents_user_status", "user_id", "status"),

    # "Get usage records for billing period"
    Index("ix_usage_user_created", "user_id", "created_at"),
)
```

### Connection Pooling

```python
# database.py
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # Max connections in pool
    max_overflow=10,        # Extra connections if needed
    pool_pre_ping=True,     # Check connection health
    pool_recycle=3600,      # Recycle connections hourly
)
```

### Query Optimization

```python
# ❌ N+1 problem
users = await db.execute(select(User))
for user in users:
    docs = await db.execute(
        select(Document).where(Document.user_id == user.id)
    )  # N additional queries!

# ✅ Eager loading
users = await db.execute(
    select(User).options(selectinload(User.documents))
)  # 2 queries total
```

---

## 🎯 Key Takeaways

| Topic | Key Points |
|-------|------------|
| **Schema Design** | User-scoped multi-tenancy, cascade deletes |
| **pgvector** | 768-dim embeddings, HNSW index, cosine similarity |
| **JSON Columns** | Workflow nodes/edges, agent config, metadata |
| **Indexes** | Composite for common queries, HNSW for vectors |
| **Migrations** | Alembic, backward compatible changes |
| **Performance** | Connection pooling, eager loading, proper indexes |

---

*ต่อไป: [05-api-security.md](./05-api-security.md) — API design and security measures*
