# Product Specification: RAG Agent Platform

## Overview

**Product Name:** RAG Agent Platform
**Problem to Solve:** องค์กรและ developers ต้องการสร้าง AI agents ที่เข้าใจบริบทจากข้อมูลภายในองค์กร (documents) และสามารถทำงานอัตโนมัติผ่าน workflows ได้ โดยไม่ต้องเขียนโค้ดซับซ้อน

**Target Audience:**
- Developers ที่ต้องการสร้าง AI assistants โดยไม่ต้องจัดการ infrastructure
- Business users ที่ต้องการ automate workflows ด้วย AI
- Organizations ที่ต้องการสร้าง knowledge base + AI chatbot

---

## 1. User Personas

### Persona 1: Developer Dan
- **อายุ:** 28 ปี
- **ตำแหน่ง:** Full-stack Developer
- **พฤติกรรม:**
  - ต้องการสร้าง AI agent ที่ตอบคำถามจาก documentation ของบริษัท
  - คุ้นเคยกับ API และ system prompts
  - ต้องการ customize tools และ RAG settings
- **Pain Points:**
  - เสียเวลาจัดการ vector database และ embedding pipeline
  - ยากที่จะ debug และ trace AI responses

### Persona 2: Business Analyst Bella
- **อายุ:** 35 ปี
- **ตำแหน่ง:** Business Analyst
- **พฤติกรรม:**
  - ต้องการ automate report generation และ data processing
  - ไม่ถนัดเขียนโค้ด แต่เข้าใจ flowchart
  - ต้องการ visual tools สำหรับสร้าง workflows
- **Pain Points:**
  - ต้องพึ่งพา developers ตลอดเวลา
  - ไม่มี visibility ว่า workflow รันไปถึงไหน

### Persona 3: Team Lead Tina
- **อายุ:** 40 ปี
- **ตำแหน่ง:** Team Lead / Manager
- **พฤติกรรม:**
  - ต้องการ monitor usage และ costs
  - จัดการ team members และ permissions
  - ดู analytics และ audit logs
- **Pain Points:**
  - ไม่รู้ว่าทีมใช้ AI มากแค่ไหน
  - กลัว data leakage และ PII exposure

---

## 2. User Journeys

### Journey 1: สร้าง AI Agent สำหรับตอบคำถาม Documentation

**Actor:** Developer Dan

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Register/Login | แสดง Dashboard |
| 2 | สร้าง Project ใหม่ "Product Docs" | สร้าง workspace พร้อม default settings |
| 3 | Upload PDF/MD files ของ documentation | แสดง progress, ทำ chunking และ embedding |
| 4 | สร้าง Agent ใหม่ | แสดง form: name, system prompt, tools |
| 5 | เลือก documents ที่จะใช้กับ agent | Link documents กับ agent |
| 6 | ทดสอบ chat กับ agent | Agent ตอบคำถามโดยอ้างอิงจาก documents |
| 7 | Embed agent ไปใช้ใน app อื่น (optional) | ได้ embed code / API key |

### Journey 2: สร้าง Visual Workflow สำหรับ Report Generation

**Actor:** Business Analyst Bella

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Login | แสดง Dashboard |
| 2 | ไปที่ Workflows | แสดงรายการ workflows |
| 3 | สร้าง Workflow ใหม่ | เปิด Visual Editor (canvas) |
| 4 | ลาก "Start" node | วาง node บน canvas |
| 5 | ลาก "HTTP" node (fetch data from API) | Connect กับ Start, config URL |
| 6 | ลาก "LLM" node (summarize data) | Connect กับ HTTP, config prompt |
| 7 | ลาก "End" node | Connect กับ LLM |
| 8 | กด "Run" | แสดง execution status ทีละ node |
| 9 | ดู output ที่ End node | แสดง summarized report |
| 10 | Save และ Schedule (optional) | Workflow พร้อมใช้งาน |

### Journey 3: Monitor Team Usage และ Costs

**Actor:** Team Lead Tina

| Step | Action | System Response |
|------|--------|-----------------|
| 1 | Login (Admin role) | แสดง Admin Dashboard |
| 2 | ไปที่ Billing | แสดง current plan, usage stats |
| 3 | ดู breakdown by agent/workflow | แสดง token usage per agent |
| 4 | ไปที่ Audit Logs | แสดง activity logs |
| 5 | Filter by user/date | แสดง filtered results |
| 6 | Export usage report | Download CSV |

---

## 3. Core Features

### 3.1 Document Management
- **Upload Documents:** รองรับ PDF, DOCX, TXT, MD, CSV
- **Auto-Processing:** Chunking และ embedding อัตโนมัติ
- **Status Tracking:** pending → processing → ready/error
- **Tagging:** จัดกลุ่ม documents ด้วย tags

### 3.2 Agent Builder
- **Custom Agents:** ตั้งชื่อ, icon, description
- **System Prompt:** กำหนด personality และ instructions
- **Tool Selection:** เลือก tools ที่ agent ใช้ได้
  - `rag_search` - ค้นหาจาก documents
  - `summarize` - สรุปเนื้อหา
  - `calculator` - คำนวณ
  - `web_search` - ค้นหาจาก web
- **Document Linking:** เชื่อม documents กับ agent
- **Source Types:** System agents (pre-built) vs User agents (custom)

### 3.3 Visual Workflow Builder
- **Drag-and-Drop Canvas:** สร้าง workflows แบบ visual
- **Node Types:**
  - `start` / `end` - จุดเริ่มต้นและสิ้นสุด
  - `llm` - เรียกใช้ LLM (Google Gemini)
  - `agent` - เรียกใช้ custom agent
  - `rag` - ค้นหาจาก knowledge base
  - `tool` - เรียกใช้ external tools
  - `condition` - if/else branching
  - `loop` - วนซ้ำ
  - `custom_function` - custom code
  - `http` - HTTP requests
- **Execution Tracking:** ดู status ทีละ node แบบ real-time
- **Templates:** Pre-built workflows เป็นตัวอย่าง

### 3.4 Chat Interface
- **Real-time Chat:** Streaming responses
- **Conversation History:** บันทึกและค้นหาประวัติ
- **Project-based:** จัดกลุ่ม conversations ตาม project
- **Agent Selection:** เลือก agent ที่จะ chat ด้วย

### 3.5 Project Organization
- **Workspaces:** แยก documents, agents, conversations ตาม project
- **Privacy Levels:** strict, moderate, off (PII protection)
- **Team Sharing:** (future) แชร์ project กับ team members

### 3.6 Billing & Usage
- **Subscription Plans:** Free, Pro, Enterprise
- **Usage Tracking:** Token usage per agent/workflow
- **Invoices:** ออก invoice อัตโนมัติ
- **Notifications:** แจ้งเตือนเมื่อใกล้ถึง limit

### 3.7 Notifications
- **In-app Notifications:** แจ้งเตือนใน app
- **Notification Preferences:** เลือกรับ/ไม่รับ notifications
- **Activity Alerts:** Document ready, workflow completed, usage warning

---

## 4. Success Metrics

### User Engagement
| Metric | Target |
|--------|--------|
| Daily Active Users (DAU) | 1,000+ |
| Documents uploaded per user/month | 10+ |
| Agents created per user | 3+ |
| Chat messages per user/day | 20+ |
| Workflow executions per week | 50+ |

### Business Metrics
| Metric | Target |
|--------|--------|
| Conversion (Free → Pro) | 5%+ |
| Monthly Recurring Revenue (MRR) | Growth 15%/month |
| Churn Rate | < 5%/month |
| Customer Satisfaction (NPS) | 50+ |

### Technical Metrics
| Metric | Target |
|--------|--------|
| Document processing time | < 30 seconds |
| Chat response latency (TTFB) | < 500ms |
| Workflow execution success rate | > 95% |
| System uptime | 99.9% |

---

## 5. Edge Cases

### Document Upload
| Case | Handling |
|------|----------|
| File too large (> 50MB) | Reject with error message |
| Unsupported file type | Show supported types list |
| Corrupted file | Mark as error, notify user |
| Empty file | Warn user, allow skip |
| Duplicate filename | Auto-rename with suffix |

### Agent Chat
| Case | Handling |
|------|----------|
| No documents linked | Agent responds without RAG |
| All documents still processing | Show "Documents are being processed" |
| LLM API timeout | Retry 3x, then show error |
| Token limit exceeded | Truncate context, notify user |
| Inappropriate content | Content filter, log for review |

### Workflow Execution
| Case | Handling |
|------|----------|
| Infinite loop detected | Auto-stop after max iterations |
| Node execution error | Mark node as failed, option to retry |
| External API failure (HTTP node) | Retry with backoff, then fail |
| User cancels mid-execution | Graceful stop, save partial results |
| Workflow deleted during execution | Complete current run, then cleanup |

### Billing
| Case | Handling |
|------|----------|
| Usage exceeds plan limit | Notify user, option to upgrade |
| Payment failed | Grace period 7 days, then suspend |
| Refund request | Case-by-case review |
| Free tier abuse | Rate limiting, account review |

### Security
| Case | Handling |
|------|----------|
| PII detected in documents | Based on privacy_level setting |
| Unauthorized API access | Return 401/403, log attempt |
| Injection attacks (prompt injection) | Input sanitization, monitoring |
| Data export request (GDPR) | Provide data export tool |

---

## Notes

เอกสารนี้เน้น Product/UX perspective โดยไม่พูดถึง technical implementation ส่งต่อให้ System Architect ในขั้นตอน `/plan`
