# RAG2Agents - Interview Guide

เอกสารนี้รวบรวมคำถาม-คำตอบเชิงลึกสำหรับการสัมภาษณ์โปรเจ็ค **RAG2Agents** เขียนในรูปแบบ storytelling เพื่อให้เข้าใจ context, การตัดสินใจ, และบทเรียนที่ได้เรียนรู้

---

## 📚 สารบัญ

| ไฟล์ | หัวข้อ | เนื้อหา |
|------|--------|---------|
| [01-project-story.md](./01-project-story.md) | **Project Story** | ที่มาของโปรเจ็ค, ปัญหาที่ต้องการแก้, vision, target users |
| [02-architecture.md](./02-architecture.md) | **Architecture** | System design, layer pattern, tech stack decisions, trade-offs |
| [03-rag-deep-dive.md](./03-rag-deep-dive.md) | **RAG Deep Dive** | Document processing, chunking strategy, embedding, vector search |
| [04-database-design.md](./04-database-design.md) | **Database Design** | Schema design, pgvector, relationships, performance tuning |
| [05-api-security.md](./05-api-security.md) | **API & Security** | REST design, JWT auth, rate limiting, audit logging |
| [06-challenges.md](./06-challenges.md) | **Challenges** | ปัญหาที่เจอจริง, debugging stories, วิธีแก้ไข |
| [07-lessons-learned.md](./07-lessons-learned.md) | **Lessons Learned** | สิ่งที่เรียนรู้, ถ้าทำใหม่จะทำอะไรต่าง, advice |

---

## 🎯 วิธีใช้เอกสารนี้

### สำหรับเตรียมสัมภาษณ์
1. อ่าน **01-project-story.md** ก่อน เพื่อเข้าใจ big picture
2. เลือกอ่านหมวดที่ตรงกับ job position
3. ฝึกเล่าเป็น story ไม่ใช่แค่ตอบ technical

### สำหรับ Technical Interviews
- **Backend Focus:** 02, 03, 04, 05
- **System Design:** 02, 03, 06
- **Problem Solving:** 06, 07

---

## 🏗️ Project Overview

```
RAG2Agents - SaaS Platform for Building AI Agents with RAG

┌─────────────────────────────────────────────────────────────┐
│                 SvelteKit Frontend                           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   FastAPI Backend                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │   RAG   │  │ Agents  │  │Workflow │  │ Billing │        │
│  │Pipeline │  │ Engine  │  │ Engine  │  │ Stripe  │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────────────────────────────────────────┘
        │              │              │              │
   PostgreSQL     LiteLLM        Redis          Stripe
   + pgvector     (Gemini)    (Rate Limit)    (Payment)
```

---

## 💡 Key Highlights

เมื่อถูกถามว่า "เล่าเกี่ยวกับโปรเจ็คนี้หน่อย" ควรพูดถึง:

1. **Problem Statement:** องค์กรต้องการ AI Assistant ที่เข้าใจ context ของตัวเอง แต่การสร้าง RAG pipeline ซับซ้อนมาก

2. **Solution:** Platform ที่ให้ upload เอกสาร → ได้ AI Agent พร้อมใช้ทันที + Visual Workflow Builder สำหรับ non-technical users

3. **Technical Depth:**
   - RAG with pgvector (ไม่ต้องแยก vector DB)
   - Async-first architecture (high concurrency)
   - Multi-LLM support via LiteLLM
   - Real-time streaming with SSE

4. **Scale Considerations:**
   - User-scoped vector search
   - Rate limiting + usage tracking
   - Subscription billing integration

---

## 📊 Tech Stack Quick Reference

| Layer | Technology | Why |
|-------|------------|-----|
| Frontend | SvelteKit 2 + Svelte 5 | Reactive without virtual DOM, Runes simplify state |
| Backend | FastAPI | Async-native, auto-docs, type hints |
| Database | PostgreSQL + pgvector | Single DB for relational + vector data |
| LLM | LiteLLM (Gemini) | Unified API, easy provider switching |
| Auth | JWT | Stateless, scalable |
| Billing | Stripe | Industry standard |

---

*อ่านแต่ละไฟล์เพื่อ deep dive ในแต่ละหัวข้อ*
