# RAG Agent Platform - Project Specification

## 📋 Document Info

| | |
|--|--|
| **Version** | 3.0 |
| **Date** | December 2024 |
| **Author** | - |
| **Status** | Ready for Development |
| **Changes v3** | Job Dispatcher, Schema Linking, PII Masking, SQL Confirmation |

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
- **Fine-tuning**: Train custom models via Job Dispatcher (GPU Cloud)
- **PII Protection**: Auto-mask sensitive data ก่อนส่ง LLM ⭐ NEW v3
- **Production-Ready**: User management, usage limits, monitoring

---

## 🛠 Tech Stack

### Core Technologies

| Layer | Technology | Reason |
|-------|------------|--------|
| **Frontend** | SvelteKit (Static) | เร็ว, รวม container เดียวกับ backend |
| **Backend** | FastAPI (Python) | Async, เหมาะกับ AI/ML, first-class Python |
| **LLM Gateway** | LiteLLM (Library + Proxy) | Unified API, multi-provider, Admin UI |
| **Vector Store** | ChromaDB | Embedded, ง่าย, lightweight |
| **Embeddings** | Sentence-transformers | Open-source, fine-tunable |
| **Agent Framework** | Custom + LangGraph | เริ่มทำเอง แล้ว upgrade |
| **Monitoring** | Prometheus | Metrics collection |
| **Database (Dev)** | SQLite | ง่าย, ไม่ต้อง Docker ⭐ v3 |
| **Database (Prod)** | PostgreSQL | Production-ready |

### NEW v3: Privacy & Safety Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PII Detection** | Microsoft Presidio | ตรวจจับข้อมูลส่วนตัว |
| **PII Masking** | Presidio Anonymizer | ปิดบังข้อมูลก่อนส่ง LLM |
| **Schema Linking** | RAG on Schema | หา tables ที่เกี่ยวข้อง |
| **SQL Review** | User Confirmation | ให้ user ยืนยัน SQL ก่อนรัน |

### Fine-tuning Stack (GPU Cloud)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Job Dispatcher** | FastAPI + Queue | ส่ง job ไป train บน cloud |
| **GPU Provider** | Colab/Kaggle/RunPod | Train models (มี GPU) |
| **Tracking** | Weights & Biases | Experiment tracking |
| **Model Hub** | Hugging Face Hub | Store & share models |
| **Local Inference** | Ollama | Run fine-tuned models |

### Text-to-SQL Stack (Enhanced)

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Schema Linking** | RAG + Embeddings | หา tables/columns ที่เกี่ยวข้อง |
| **SQL Generation** | LLM + Pruned Schema | Generate SQL จาก subset |
| **SQL Review** | User Confirmation UI | ให้ user ยืนยันก่อน execute |
| **Safe Execution** | Read-only sandbox | Execute อย่างปลอดภัย |

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
│  │  │  │  ChromaDB  │  │  │              │  │              │ ││
│  │  │  ├────────────┤  │  │              │  │              │ ││
│  │  │  │ PostgreSQL │  │  │              │  │              │ ││
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

#### 1.3 User Settings
- [ ] Profile management
- [ ] Default model preference
- [ ] Notification settings
- [ ] API key management (for power users)
- [ ] PII masking preferences ⭐ NEW v3

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

#### 3.2 PII Scrubber Implementation

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

class PIIScrubber:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Add Thai language support
        self.analyzer.registry.add_recognizer(ThaiPhoneRecognizer())
        self.analyzer.registry.add_recognizer(ThaiIDCardRecognizer())
        
    def scrub(self, text: str, level: str = "strict") -> tuple[str, dict]:
        """
        Scrub PII from text.
        Returns: (scrubbed_text, mapping)
        """
        # Analyze
        results = self.analyzer.analyze(
            text=text,
            language="th",
            entities=self._get_entities_for_level(level)
        )
        
        # Create mapping for potential restoration
        mapping = {}
        for i, result in enumerate(results):
            placeholder = f"[{result.entity_type}_{i}]"
            original = text[result.start:result.end]
            mapping[placeholder] = original
        
        # Anonymize
        scrubbed = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
                "PERSON": OperatorConfig("replace", {"new_value": "[PERSON]"}),
                "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
                "EMAIL": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
            }
        )
        
        return scrubbed.text, mapping
    
    def _get_entities_for_level(self, level: str) -> list:
        if level == "strict":
            return ["PERSON", "PHONE_NUMBER", "EMAIL", "LOCATION", 
                    "CREDIT_CARD", "ID_CARD", "DATE_OF_BIRTH"]
        elif level == "moderate":
            return ["CREDIT_CARD", "ID_CARD", "MEDICAL_LICENSE"]
        else:
            return []

# Usage in chat pipeline
scrubber = PIIScrubber()

user_input = "คุณสมชาย ใจดี โทร 081-234-5678 มีอาการซึมเศร้า"
scrubbed, mapping = scrubber.scrub(user_input, level="strict")
# scrubbed = "[PERSON] โทร [PHONE] มีอาการซึมเศร้า"
# mapping = {"[PERSON]": "คุณสมชาย ใจดี", "[PHONE]": "081-234-5678"}

# Send scrubbed text to LLM
response = llm.generate(scrubbed)
```

#### 3.3 Integration Points

```
┌─────────────────────────────────────────────────────────────────┐
│                   PII Protection Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Input ──▶ PII Scrubber ──▶ RAG/SQL ──▶ LLM ──▶ Response   │
│       │              │                              │           │
│       │              ▼                              │           │
│       │         Mapping                             │           │
│       │         (stored)                            │           │
│       │              │                              │           │
│       │              └──────────────────────────────┤           │
│       │                                             │           │
│       │                                             ▼           │
│       │                                    ┌─────────────┐      │
│       │                                    │ Audit Log   │      │
│       │                                    │ (encrypted) │      │
│       └────────────────────────────────────┴─────────────┘      │
│                                                                 │
│  Note: Original PII is stored encrypted, only for audit        │
│        LLM never sees actual PII                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4. Agent System

#### 4.1 Pre-built Agents

| Agent | Description | Tools |
|-------|-------------|-------|
| **General** | General-purpose assistant | RAG search, summarize |
| **HR** | HR policy & recruitment | Resume parser, policy RAG, skill matcher |
| **Legal** | Legal analysis & research | Contract analyzer, law search, case compare |
| **Finance** | Financial analysis | Financial calculator, report analyzer, SQL query |
| **Research** | Research assistant | Paper search, citation finder |
| **Data Analyst** | Data analysis | SQL query, chart generator, data summary |
| **Mental Health** | Research assistant ⭐ NEW v3 | PII-safe RAG, anonymized case search |

#### 4.2 Mental Health Agent ⭐ NEW v3

```yaml
agent:
  name: "Mental Health Research Assistant"
  description: "ผู้ช่วยวิจัยด้านสุขภาพจิต (PII Protected)"
  icon: "🧠"
  
persona:
  system_prompt: |
    คุณเป็นผู้ช่วยวิจัยด้านสุขภาพจิต
    - ตอบโดยอิงหลักวิชาการและงานวิจัย
    - ไม่ให้คำวินิจฉัยหรือคำแนะนำทางการแพทย์
    - ปกป้องความเป็นส่วนตัวของข้อมูลผู้ป่วย
    - แนะนำให้ปรึกษาผู้เชี่ยวชาญเสมอ

privacy:
  pii_level: "strict"  # Always strict for mental health
  audit_logging: true
  data_retention: "encrypted"

tools:
  - name: "rag_search"
    description: "ค้นหาจากเอกสารวิจัย"
  - name: "case_search"
    description: "ค้นหา case studies (anonymized)"
  - name: "citation_finder"
    description: "หา reference งานวิจัย"

knowledge_base:
  sources:
    - type: "local"
      path: "./data/mental_health/"
    - type: "pubmed"
      api: "pubmed_search"
```

---

### 5. RAG System

#### 5.1 Document Processing
- [ ] Supported formats: PDF, DOCX, TXT, MD, CSV
- [ ] Automatic text extraction
- [ ] Smart chunking (semantic / recursive)
- [ ] Metadata extraction
- [ ] PII detection on upload ⭐ NEW v3

#### 5.2 Vector Store
- [ ] ChromaDB integration
- [ ] Per-project collections
- [ ] Schema embeddings for Text-to-SQL ⭐ NEW v3
- [ ] Embedding model: multilingual-e5-base (or fine-tuned)
- [ ] Hybrid search (Dense + BM25)

#### 5.3 Retrieval Pipeline
- [ ] PII scrubbing on query ⭐ NEW v3
- [ ] Query preprocessing
- [ ] Hybrid search (dense + sparse)
- [ ] Reciprocal Rank Fusion (RRF)
- [ ] Re-ranking (optional)
- [ ] Context assembly

---

### 6. Text-to-SQL System (Enhanced v3)

#### 6.1 Schema Linking ⭐ NEW v3

**Problem**: Database มี 100 ตาราง ส่งทั้งหมดให้ LLM จะ:
- Token เยอะมาก (แพง)
- LLM งง ตอบผิด

**Solution**: RAG on Schema

```python
class SchemaLinker:
    def __init__(self, db_connection):
        self.db = db_connection
        self.embedder = SentenceTransformer('intfloat/multilingual-e5-base')
        self.schema_index = None
        
    def build_schema_index(self):
        """Build embeddings for all tables/columns"""
        schema_docs = []
        
        for table in self.db.get_tables():
            # Create searchable description
            desc = f"Table: {table.name}. {table.description}. "
            desc += f"Columns: {', '.join([c.name for c in table.columns])}"
            
            schema_docs.append({
                "table": table.name,
                "text": desc,
                "columns": table.columns
            })
        
        # Create embeddings
        embeddings = self.embedder.encode([d["text"] for d in schema_docs])
        self.schema_index = faiss.IndexFlatL2(embeddings.shape[1])
        self.schema_index.add(embeddings)
        self.schema_docs = schema_docs
        
    def find_relevant_tables(self, query: str, top_k: int = 5) -> list:
        """Find tables relevant to the query"""
        query_embedding = self.embedder.encode([query])
        distances, indices = self.schema_index.search(query_embedding, top_k)
        
        relevant = []
        for idx in indices[0]:
            relevant.append(self.schema_docs[idx])
        
        return relevant

# Usage
linker = SchemaLinker(customer_db)
linker.build_schema_index()

query = "ยอดขายของลูกค้า VIP เดือนนี้"
relevant_tables = linker.find_relevant_tables(query, top_k=3)
# Returns: [orders, customers, customer_tiers]
# NOT all 100 tables
```

#### 6.2 SQL Generation with Pruned Schema

```python
def generate_sql(query: str, relevant_tables: list) -> str:
    """Generate SQL using only relevant tables"""
    
    # Build pruned schema context
    schema_context = "Available tables:\n"
    for table in relevant_tables:
        schema_context += f"\nTable: {table['table']}\n"
        schema_context += f"Columns:\n"
        for col in table['columns']:
            schema_context += f"  - {col.name} ({col.type}): {col.description}\n"
    
    prompt = f"""Given this database schema:
{schema_context}

Generate a SQL query to answer: {query}

Rules:
- Use only SELECT statements
- No DELETE, UPDATE, DROP, or INSERT
- Include only necessary columns
- Add appropriate WHERE clauses

SQL:"""

    response = llm.generate(prompt)
    return response.strip()
```

#### 6.3 User Confirmation Step ⭐ NEW v3

```
┌─────────────────────────────────────────────────────────────────┐
│  SQL Review & Confirmation                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📝 Your Question:                                              │
│  "ยอดขายของลูกค้า VIP เดือนนี้"                                  │
│                                                                 │
│  ────────────────────────────────────────────────────────────── │
│                                                                 │
│  🔍 Generated SQL:                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ SELECT c.name, SUM(o.amount) as total                     │ │
│  │ FROM orders o                                             │ │
│  │ JOIN customers c ON o.customer_id = c.id                  │ │
│  │ WHERE c.tier = 'VIP'                                      │ │
│  │   AND o.created_at >= '2024-12-01'                        │ │
│  │ GROUP BY c.id                                             │ │
│  │ ORDER BY total DESC                                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ────────────────────────────────────────────────────────────── │
│                                                                 │
│  📊 Query Analysis:                                             │
│  • Tables accessed: orders, customers                          │
│  • Estimated rows: ~50                                          │
│  • Estimated time: <1 second                                    │
│  • Safety check: ✅ Read-only query                             │
│                                                                 │
│  ────────────────────────────────────────────────────────────── │
│                                                                 │
│  [✅ Execute Query]  [✏️ Edit SQL]  [❌ Cancel]                  │
│                                                                 │
│  ☐ Don't ask again for similar queries (this session)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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

### 7. Fine-tuning Module (Updated v3)

#### 7.1 Job Dispatcher Architecture ⭐ UPDATED

**สำคัญ**: Fine-tuning ไม่รันบน Hetzner (ไม่มี GPU)

| Component | Location | Purpose |
|-----------|----------|---------|
| **Job Dispatcher** | Hetzner VPS | สร้าง/จัดการ jobs |
| **Job Queue** | PostgreSQL | เก็บ job status |
| **Training Worker** | Colab/RunPod | Train จริง (GPU) |
| **Model Storage** | HF Hub | เก็บ trained models |

#### 7.2 Job Lifecycle

```python
# 1. User creates job via Admin Panel
job = {
    "id": "job-001",
    "type": "embedding",
    "base_model": "intfloat/multilingual-e5-base",
    "training_data_url": "https://storage.../data.csv",
    "output_model": "username/custom-embedding",
    "status": "pending",
    "gpu_provider": "colab"  # or "runpod", "kaggle"
}

# 2. Job saved to queue
db.jobs.insert(job)

# 3. Training Worker (on Colab) polls for jobs
# worker.py - runs on Colab
while True:
    job = api.get_pending_job()
    if job:
        # Download training data
        data = download(job.training_data_url)
        
        # Train model
        model = train(job.base_model, data)
        
        # Push to HF Hub
        model.push_to_hub(job.output_model)
        
        # Update job status
        api.update_job(job.id, status="completed")
    
    sleep(60)

# 4. Platform pulls model from HF Hub
model = SentenceTransformer("username/custom-embedding")
```

#### 7.3 Training Worker Setup (Colab Notebook)

```python
# Fine-tuning Worker - Run on Google Colab
# ========================================

# 1. Install dependencies
!pip install sentence-transformers transformers peft trl wandb

# 2. Login to services
from huggingface_hub import login
login(token="hf_xxx")

import wandb
wandb.login()

# 3. Worker loop
import requests
import time

API_URL = "https://your-platform.com/api/finetune"
API_KEY = "your-api-key"

while True:
    # Poll for pending jobs
    response = requests.get(
        f"{API_URL}/jobs/pending",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    
    jobs = response.json()
    
    for job in jobs:
        print(f"Processing job: {job['id']}")
        
        # Update status to running
        requests.patch(
            f"{API_URL}/jobs/{job['id']}",
            json={"status": "running"}
        )
        
        try:
            if job['type'] == 'embedding':
                train_embedding(job)
            elif job['type'] == 'classifier':
                train_classifier(job)
            elif job['type'] == 'llm_lora':
                train_lora(job)
            
            # Update status to completed
            requests.patch(
                f"{API_URL}/jobs/{job['id']}",
                json={"status": "completed"}
            )
            
        except Exception as e:
            requests.patch(
                f"{API_URL}/jobs/{job['id']}",
                json={"status": "failed", "error": str(e)}
            )
    
    time.sleep(60)  # Poll every minute
```

#### 7.4 Fine-tuning UI (Updated)

```
┌─────────────────────────────────────────────────────────────────┐
│  Fine-tuning Dashboard                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ℹ️ Note: Training runs on GPU cloud (Colab/RunPod), not local  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Create New Training Job                                 │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ Type:  [Embedding ▼]                                    │   │
│  │ Base Model: [multilingual-e5-base ▼]                    │   │
│  │ Training Data: [Upload CSV] or [Select from Documents]  │   │
│  │ GPU Provider: [Google Colab ▼]                          │   │
│  │ Output Name: [custom-e5-hr________________]             │   │
│  │                                        [Create Job]     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Training Jobs                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Job ID  │ Type      │ Provider │ Status  │ Actions       │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ job-001 │ Embedding │ Colab    │ Running │ [View Logs]   │ │
│  │ job-002 │ Classifier│ Kaggle   │ Done    │ [Deploy]      │ │
│  │ job-003 │ LLM LoRA  │ RunPod   │ Pending │ [Cancel]      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 8. Admin & Monitoring

#### 8.1 Admin Panel
- [ ] User management (view, edit, suspend)
- [ ] Usage overview (all users)
- [ ] System health dashboard
- [ ] Cost tracking
- [ ] Fine-tuning job management
- [ ] Database connection management
- [ ] PII audit logs ⭐ NEW v3

#### 8.2 PII Audit Dashboard ⭐ NEW v3

```
┌─────────────────────────────────────────────────────────────────┐
│  PII Audit Dashboard                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Summary (Last 7 days)                                          │
│  ─────────────────────                                          │
│  Total queries processed: 1,234                                 │
│  Queries with PII detected: 89 (7.2%)                          │
│  PII successfully masked: 89 (100%)                             │
│  PII types detected:                                            │
│    • PERSON: 45                                                 │
│    • PHONE: 32                                                  │
│    • EMAIL: 12                                                  │
│                                                                 │
│  Recent PII Events                                              │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │ Time      │ User  │ Project │ PII Types │ Action          │ │
│  ├───────────────────────────────────────────────────────────┤ │
│  │ 10:32:01  │ u-001 │ Mental  │ PERSON    │ Masked          │ │
│  │ 10:30:45  │ u-002 │ HR      │ PHONE,ID  │ Masked          │ │
│  │ 10:28:12  │ u-001 │ Mental  │ PERSON    │ Masked          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure (Updated v3)

```
rag-agent-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── projects.py
│   │   │   ├── documents.py
│   │   │   ├── agents.py
│   │   │   ├── admin.py
│   │   │   ├── database.py
│   │   │   └── finetune.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   ├── database.py
│   │   │   └── llm_client.py
│   │   │
│   │   ├── privacy/                    # ⭐ NEW v3
│   │   │   ├── __init__.py
│   │   │   ├── pii_scrubber.py         # Presidio integration
│   │   │   ├── thai_recognizers.py     # Thai PII patterns
│   │   │   ├── audit_logger.py         # PII audit logging
│   │   │   └── middleware.py           # Auto-scrub middleware
│   │   │
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── conversation.py
│   │   │   ├── document.py
│   │   │   ├── db_connection.py
│   │   │   ├── finetune_job.py
│   │   │   └── pii_audit.py            # ⭐ NEW v3
│   │   │
│   │   ├── rag/
│   │   │   ├── embeddings.py
│   │   │   ├── chunking.py
│   │   │   ├── retriever.py
│   │   │   └── pipeline.py
│   │   │
│   │   ├── agents/
│   │   │   ├── base.py
│   │   │   ├── engine.py
│   │   │   ├── tools/
│   │   │   │   ├── rag_search.py
│   │   │   │   ├── summarize.py
│   │   │   │   ├── sql_query.py
│   │   │   │   └── chart_gen.py
│   │   │   └── prebuilt/
│   │   │       ├── general.py
│   │   │       ├── hr.py
│   │   │       ├── legal.py
│   │   │       ├── finance.py
│   │   │       ├── data_analyst.py
│   │   │       └── mental_health.py    # ⭐ NEW v3
│   │   │
│   │   ├── text2sql/
│   │   │   ├── __init__.py
│   │   │   ├── schema_linker.py        # ⭐ NEW v3 - RAG on schema
│   │   │   ├── generator.py
│   │   │   ├── validator.py
│   │   │   ├── executor.py
│   │   │   ├── confirmation.py         # ⭐ NEW v3 - User confirm
│   │   │   └── visualizer.py
│   │   │
│   │   ├── finetune/
│   │   │   ├── __init__.py
│   │   │   ├── job_dispatcher.py       # ⭐ UPDATED v3
│   │   │   ├── job_queue.py
│   │   │   ├── data_prep.py
│   │   │   └── hub.py
│   │   │
│   │   └── main.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +page.svelte
│   │   │   ├── +layout.svelte
│   │   │   ├── login/
│   │   │   ├── projects/
│   │   │   ├── settings/
│   │   │   ├── database/
│   │   │   ├── finetune/
│   │   │   ├── privacy/                # ⭐ NEW v3
│   │   │   └── admin/
│   │   ├── lib/
│   │   │   ├── components/
│   │   │   │   ├── Chat/
│   │   │   │   ├── Sidebar/
│   │   │   │   ├── AgentSelector/
│   │   │   │   ├── SQLConfirm/         # ⭐ NEW v3
│   │   │   │   ├── PIIIndicator/       # ⭐ NEW v3
│   │   │   │   └── DebugPanel/
│   │   │   └── stores/
│   │   └── app.html
│   └── package.json
│
├── training/                           # Worker scripts for GPU cloud
│   ├── worker.py                       # Main worker loop
│   ├── train_embedding.py
│   ├── train_classifier.py
│   ├── train_lora.py
│   └── colab_notebook.ipynb           # Ready-to-run Colab notebook
│
├── configs/
│   ├── agents/
│   │   └── mental_health.yaml          # ⭐ NEW v3
│   └── pii/                            # ⭐ NEW v3
│       ├── thai_patterns.yaml
│       └── entity_config.yaml
│
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml          # Uses SQLite
│
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    ├── AGENTS.md
    ├── TEXT2SQL.md
    ├── FINETUNING.md
    └── PII_PROTECTION.md               # ⭐ NEW v3
```

---

## 📅 Development Phases (Updated v3)

### Phase 1: Foundation (Week 1-2)
**Goal**: Basic working app with authentication

- [ ] Setup project structure
- [ ] Setup Hetzner VPS + Coolify
- [ ] Setup GitHub Actions CI/CD
- [ ] FastAPI backend skeleton
- [ ] SvelteKit frontend skeleton
- [ ] **SQLite for development** ⭐ v3
- [ ] User authentication (register/login)
- [ ] Basic chat UI (no RAG yet)
- [ ] LiteLLM integration (single model)
- [ ] Docker containerization

**Deliverable**: User can login and chat with AI

---

### Phase 2: RAG Core (Week 3-4)
**Goal**: Document upload and RAG working

- [ ] Document upload API
- [ ] PDF/DOCX text extraction
- [ ] Text chunking (recursive)
- [ ] ChromaDB integration
- [ ] Embedding generation
- [ ] Basic retrieval (dense search)
- [ ] Source citations in responses
- [ ] Document management UI

**Deliverable**: User can upload docs and ask questions

---

### Phase 3: PII Protection ⭐ NEW v3 (Week 5)
**Goal**: Protect sensitive data before LLM

- [ ] Presidio integration
- [ ] Thai PII recognizers (phone, ID card)
- [ ] PII scrubber middleware
- [ ] Privacy level settings per project
- [ ] PII audit logging
- [ ] Admin audit dashboard
- [ ] PII indicator in UI

**Deliverable**: All queries scrubbed before LLM, audit trail

---

### Phase 4: Agent System (Week 6-7)
**Goal**: Multi-agent with tools

- [ ] Agent base class
- [ ] Agent configuration loader (YAML)
- [ ] Agent execution engine
- [ ] Basic tools (search, summarize)
- [ ] Pre-built agents (General, HR, Legal, **Mental Health**)
- [ ] Agent selector UI
- [ ] Agent thinking display
- [ ] Tool execution visualization

**Deliverable**: User can select agents for different tasks

---

### Phase 5: Text-to-SQL with Schema Linking (Week 8-9)
**Goal**: Safe database queries with user confirmation

- [ ] Database connection management
- [ ] **Schema embedding & indexing** ⭐ v3
- [ ] **Schema linking (RAG on schema)** ⭐ v3
- [ ] SQL generation with pruned schema
- [ ] SQL validation & safety checks
- [ ] **User confirmation UI** ⭐ v3
- [ ] Query execution (read-only)
- [ ] Result formatting (table, chart)
- [ ] Data Analyst agent

**Deliverable**: User can query database safely with confirmation

---

### Phase 6: Project System (Week 10)
**Goal**: Multi-project with isolated data

- [ ] Project CRUD API
- [ ] Per-project document storage
- [ ] Per-project conversations
- [ ] Per-project privacy settings ⭐ v3
- [ ] Project settings UI
- [ ] Project switching in sidebar
- [ ] Project-scoped RAG queries
- [ ] **Switch to PostgreSQL for production** ⭐ v3

**Deliverable**: User can organize work into projects

---

### Phase 7: Fine-tuning Module (Week 11)
**Goal**: Train custom models via Job Dispatcher

- [ ] **Job Dispatcher API** ⭐ v3
- [ ] **Job Queue (PostgreSQL)** ⭐ v3
- [ ] **Colab Worker notebook** ⭐ v3
- [ ] Training data preparation tools
- [ ] Hugging Face Hub integration
- [ ] Fine-tuning dashboard UI
- [ ] Model deployment flow
- [ ] Integration with platform (use custom models)

**Deliverable**: User can create training jobs, track progress, use trained models

---

### Phase 8: Polish & Production (Week 12)
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

### A. Environment Variables (Updated v3)

```env
# App
APP_NAME=RAG Agent Platform
APP_ENV=development  # or production
SECRET_KEY=your-secret-key

# Database
# Development (SQLite)
DATABASE_URL=sqlite:///./data/app.db

# Production (PostgreSQL)
# DATABASE_URL=postgresql://user:pass@localhost:5432/ragagent

# LiteLLM
LITELLM_MASTER_KEY=sk-master-key
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-xxx

# Embeddings
EMBEDDING_MODEL=intfloat/multilingual-e5-base

# Hugging Face
HF_TOKEN=hf_xxx
HF_USERNAME=your-username

# PII Protection (NEW v3)
PII_DEFAULT_LEVEL=strict  # strict, moderate, off
PII_AUDIT_ENABLED=true
PRESIDIO_LOG_LEVEL=INFO

# Fine-tuning
FINETUNE_GPU_PROVIDER=colab  # colab, kaggle, runpod
WANDB_API_KEY=xxx

# Storage
UPLOAD_DIR=/data/uploads
CHROMA_DIR=/data/chroma
MODELS_DIR=/data/models
```

### B. API Endpoints (Updated v3)

```
Auth
  POST   /api/auth/register
  POST   /api/auth/login
  POST   /api/auth/logout
  GET    /api/auth/me

Projects
  GET    /api/projects
  POST   /api/projects
  GET    /api/projects/{id}
  PUT    /api/projects/{id}
  DELETE /api/projects/{id}
  PUT    /api/projects/{id}/privacy         # NEW v3

Documents
  GET    /api/projects/{id}/documents
  POST   /api/projects/{id}/documents
  DELETE /api/projects/{id}/documents/{doc_id}

Chat
  POST   /api/projects/{id}/chat
  GET    /api/projects/{id}/conversations
  GET    /api/projects/{id}/conversations/{conv_id}

Agents
  GET    /api/agents
  GET    /api/agents/{id}

Database Connections
  GET    /api/projects/{id}/databases
  POST   /api/projects/{id}/databases
  GET    /api/projects/{id}/databases/{db_id}/schema
  POST   /api/projects/{id}/databases/{db_id}/link-schema   # NEW v3
  POST   /api/projects/{id}/databases/{db_id}/generate-sql  # NEW v3
  POST   /api/projects/{id}/databases/{db_id}/confirm-sql   # NEW v3
  POST   /api/projects/{id}/databases/{db_id}/execute       # NEW v3

Fine-tuning
  GET    /api/finetune/jobs
  POST   /api/finetune/jobs
  GET    /api/finetune/jobs/{job_id}
  PATCH  /api/finetune/jobs/{job_id}        # Worker updates status
  GET    /api/finetune/jobs/pending         # Worker polls this
  GET    /api/finetune/models
  POST   /api/finetune/models/{model_id}/deploy

Privacy (NEW v3)
  GET    /api/admin/pii/audit
  GET    /api/admin/pii/stats
  POST   /api/privacy/scrub                 # Test PII scrubbing

Admin
  GET    /api/admin/users
  PUT    /api/admin/users/{id}
  GET    /api/admin/usage
```

### C. Docker Compose (Development - SQLite)

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=development
      - DATABASE_URL=sqlite:///./data/app.db
      - LITELLM_URL=http://litellm:4000
      - PII_DEFAULT_LEVEL=strict
    volumes:
      - ./data:/data
      - ./backend:/app/backend

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "4000:4000"
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
    volumes:
      - ./litellm-config.yaml:/app/config.yaml
```

### D. Docker Compose (Production - PostgreSQL)

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/ragagent
      - LITELLM_URL=http://litellm:4000
      - PII_DEFAULT_LEVEL=strict
      - PII_AUDIT_ENABLED=true
    depends_on:
      - db
      - litellm
    volumes:
      - app_data:/data

  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "4000:4000"
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
    volumes:
      - ./litellm-config.yaml:/app/config.yaml

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=ragagent
    volumes:
      - postgres_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

volumes:
  app_data:
  postgres_data:
```

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

| Phase | Week | Features |
|-------|------|----------|
| 1. Foundation | 1-2 | Auth, Chat, LiteLLM, SQLite |
| 2. RAG Core | 3-4 | Documents, Embeddings, Retrieval |
| 3. PII Protection | 5 | Presidio, Audit logging ⭐ NEW |
| 4. Agent System | 6-7 | Multi-agent, Mental Health agent |
| 5. Text-to-SQL | 8-9 | Schema Linking, User Confirm ⭐ NEW |
| 6. Project System | 10 | Multi-project, PostgreSQL |
| 7. Fine-tuning | 11 | Job Dispatcher, GPU Cloud ⭐ NEW |
| 8. Polish | 12 | Production-ready |

**Total: 12 weeks (3 months)**

---

## 🎯 Key Improvements in v3

| Feature | Before (v2) | After (v3) |
|---------|-------------|------------|
| **Fine-tuning** | Train on Hetzner (impossible) | Job Dispatcher → GPU Cloud |
| **Text-to-SQL** | Send all schema | Schema Linking (RAG on schema) |
| **SQL Safety** | Auto-execute | User Confirmation required |
| **PII** | None | Presidio auto-masking |
| **Dev Database** | PostgreSQL | SQLite (faster dev) |
| **Mental Health** | Generic agent | Specialized PII-safe agent |

---

*Document Version 3.0 - December 2024*
*Added: PII Protection, Schema Linking, SQL Confirmation, Job Dispatcher*
*Target: Sciology (Mental Health/Scientific Research)*