# Development Tasks: RAG Agent Platform

## Overview

Tasks แบ่งตาม Phase โดยเรียงลำดับตาม Dependency Order
- `[x]` = Completed
- `[ ]` = Pending
- `[~]` = In Progress

---

## PHASE 1: Foundation & Authentication

### 1.1 Backend Core Setup

#### BE-001: Add UserTier enum
- [x] User model มีอยู่แล้ว
- [ ] เปลี่ยน `tier` จาก string เป็น Enum

**Description:** เพิ่ม UserTier enum (FREE, STARTER, PRO, ENTERPRISE) และใช้ใน User model
**Files:** `backend/app/models/user.py`
**Reference:** ดู pattern จาก `MessageRole` enum ใน `backend/app/models/message.py`
**Done when:** Migration run สำเร็จ, enum ใช้งานได้

---

#### BE-002 - BE-009: Auth Backend
- [x] Password hashing: `backend/app/core/security.py`
- [x] JWT tokens: `backend/app/core/security.py`
- [x] Auth schemas: `backend/app/schemas/auth.py`
- [x] Auth service: `backend/app/services/auth.py`
- [x] Auth dependency: `backend/app/core/dependencies.py`
- [x] Auth routes: `backend/app/routes/auth.py`
- [x] Profile routes: `backend/app/routes/profile.py`

---

### 1.2 Frontend Auth

#### FE-001 - FE-007: Auth Frontend
- [x] Auth store: `frontend/src/lib/stores/auth.svelte.ts`
- [x] API client: `frontend/src/lib/api/client.ts`
- [x] Auth API: `frontend/src/lib/api/auth.ts`
- [x] Login page: `frontend/src/routes/login/+page.svelte`
- [x] Register page: `frontend/src/routes/register/+page.svelte`
- [x] Auth guard: `frontend/src/routes/(app)/+layout.svelte`
- [x] Settings page: `frontend/src/routes/(app)/settings/+page.svelte`

---

## PHASE 2: Chat System

### 2.1 Backend Chat

#### BE-010 - BE-013: Chat Models & Service
- [x] Conversation model: `backend/app/models/conversation.py`
- [x] Message model: `backend/app/models/message.py`
- [x] Conversation service: `backend/app/services/conversation.py`
- [x] Conversations routes: `backend/app/routes/conversations.py`

---

#### BE-014: LiteLLM chat integration
- [ ] สร้าง LLM service สำหรับ chat completion

**Description:** สร้าง service ที่เรียก LiteLLM API สำหรับ chat (ทั้ง sync และ stream)
**Files:** `backend/app/services/llm.py`
**Reference:**
- Config: `backend/app/config.py` (litellm_api_url, litellm_api_key)
- Pattern: ดู async service ใน `backend/app/services/embedding.py`
**Input:** messages list, model name, stream flag
**Output:** LLM response หรือ async generator สำหรับ streaming
**Done when:** ส่ง message แล้วได้ response จาก LLM

---

#### BE-015: Chat streaming (SSE)
- [ ] Implement SSE streaming endpoint

**Description:** สร้าง POST /chat/stream ที่ stream LLM response กลับ frontend ผ่าน SSE
**Files:** `backend/app/routes/chat.py`
**Reference:**
- SSE: ใช้ `sse-starlette` library
- RAG: `backend/app/services/rag.py` (retrieve_context, build_rag_prompt)
- Conversation: `backend/app/services/conversation.py` (add_message)
**Input:** ChatRequest (message, conversation_id?, agent_slug?, project_id?)
**Output:** SSE events - start, chunk, sources, done, error
**Dependencies:** `pip install sse-starlette`
**Done when:** Frontend receives streaming chunks, messages saved to DB

---

#### BE-017: Chat schemas
- [ ] สร้าง Pydantic schemas สำหรับ chat

**Description:** สร้าง ChatRequest, ChatResponse, StreamEvent schemas
**Files:** `backend/app/schemas/chat.py`
**Reference:** ดู pattern จาก `backend/app/schemas/auth.py`
**Done when:** Schemas validate ถูกต้อง

---

#### BE-018: Track token usage
- [ ] บันทึก tokens ในแต่ละ message

**Description:** หลัง LLM response ให้บันทึก tokens_used ใน Message และสร้าง UsageRecord
**Files:** `backend/app/services/usage.py`, `backend/app/routes/chat.py`
**Reference:**
- UsageRecord model: `backend/app/models/usage.py`
- Message.tokens_used field: `backend/app/models/message.py`
**Done when:** UsageRecord ถูกสร้างหลังทุก chat

---

### 2.2 Frontend Chat

#### FE-008 - FE-014: Chat Frontend
- [x] Chat store: `frontend/src/lib/stores/chats.svelte.ts`
- [x] Chat API: `frontend/src/lib/api/chat.ts`
- [x] Chat page: `frontend/src/routes/(app)/chat/+page.svelte`
- [x] Chat [id] page: `frontend/src/routes/(app)/chat/[id]/+page.svelte`
- [x] Chats list: `frontend/src/routes/(app)/chats/+page.svelte`

---

#### FE-010: ChatMessage component
- [ ] ตรวจสอบว่ามี component แสดง message

**Description:** Component แสดง chat message พร้อม markdown rendering และ code highlighting
**Files:** `frontend/src/lib/components/chat/ChatMessage.svelte`
**Reference:**
- Icons: `frontend/src/lib/components/icons/`
- Markdown: ใช้ `marked` + `highlight.js`
**Done when:** Render markdown และ code blocks ได้

---

#### FE-011: ChatInput component
- [ ] ตรวจสอบว่ามี input component

**Description:** Textarea สำหรับพิมพ์ message พร้อม keyboard shortcuts
**Files:** `frontend/src/lib/components/chat/ChatInput.svelte`
**Reference:** ดู Textarea component จาก `frontend/src/lib/components/ui/textarea/`
**Done when:** Enter = send, Shift+Enter = newline

---

#### FE-015: Sidebar conversations
- [ ] แสดง recent conversations ใน sidebar

**Description:** แสดงรายการ conversations ล่าสุดใน sidebar
**Files:** `frontend/src/lib/components/layout/Sidebar.svelte`
**Reference:**
- Store: `frontend/src/lib/stores/chats.svelte.ts`
- API: `frontend/src/lib/api/conversations.ts`
**Done when:** Click conversation → navigate to chat

---

## PHASE 3: Document & RAG

### 3.1 Backend Documents

#### BE-019 - BE-023: Document Models & Service
- [x] Document model: `backend/app/models/document.py`
- [x] DocumentChunk model: `backend/app/models/chunk.py`
- [x] Storage service: `backend/app/services/storage.py`
- [x] Document service: `backend/app/services/document.py`
- [x] Documents routes: `backend/app/routes/documents.py`

---

#### BE-024: PDF/DOCX parser
- [ ] Extract text จาก PDF และ DOCX

**Description:** สร้าง parser functions สำหรับ extract text จากไฟล์ต่างๆ
**Files:** `backend/app/services/document_processor.py`
**Reference:** ดู file_type field ใน Document model
**Dependencies:** `pip install pymupdf python-docx`
**Supported types:** PDF, DOCX, TXT, MD, CSV
**Done when:** Parse ไฟล์แต่ละ type ได้ถูกต้อง

---

#### BE-025: Text chunking
- [ ] Split text เป็น chunks

**Description:** แบ่ง text เป็น overlapping chunks สำหรับ embedding
**Files:** `backend/app/services/document_processor.py`
**Config:** chunk_size=500 words, overlap=100 words
**Done when:** Chunks generated correctly with overlap

---

#### BE-026 - BE-027: Embedding & Vector Store
- [x] Embedding service: `backend/app/services/embedding.py`
- [x] Vector store: `backend/app/services/vector_store.py`

---

#### BE-028: Background document processor
- [ ] Process document ใน background

**Description:** Pipeline: upload → parse → chunk → embed → save chunks
**Files:** `backend/app/services/document_processor.py`
**Reference:**
- Document.status enum: pending → processing → ready/error
- Embedding: `backend/app/services/embedding.py`
- Chunk model: `backend/app/models/chunk.py`
**Done when:** Upload → status changes: pending → processing → ready

---

#### BE-030: RAG in chat flow
- [x] RAG service: `backend/app/services/rag.py`
- [ ] Integrate กับ chat streaming

**Description:** ใน chat stream ให้เรียก retrieve_context และ build_rag_prompt ก่อนส่งไป LLM
**Files:** `backend/app/routes/chat.py`
**Reference:** `backend/app/services/rag.py`
**Done when:** Chat uses document context when agent has documents

---

### 3.2 Frontend Documents

#### FE-016 - FE-019: Documents Frontend
- [x] Documents API: `frontend/src/lib/api/documents.ts`
- [x] Documents list: `frontend/src/routes/(app)/documents/+page.svelte`
- [x] Document detail: `frontend/src/routes/(app)/documents/[id]/+page.svelte`

---

#### FE-018: Document upload UI
- [ ] ตรวจสอบ upload component

**Description:** Drag-drop zone, file picker, progress bar สำหรับ upload
**Files:** Documents page หรือ separate component
**Reference:** uploadFile function ใน `frontend/src/lib/api/client.ts`
**File types:** PDF, DOCX, TXT, MD, CSV
**Done when:** Upload with progress bar ทำงาน

---

#### FE-020: Document status polling
- [ ] Poll status จนกว่าจะ ready/error

**Description:** หลัง upload ให้ poll status ทุก 2 วินาที จนกว่าจะ ready หรือ error
**Files:** `frontend/src/routes/(app)/documents/+page.svelte`
**Done when:** Status auto-updates บน page

---

## PHASE 4: Project Management

### 4.1 Backend Projects

#### BE-031 - BE-037: Projects Backend
- [x] Project model: `backend/app/models/project.py`
- [x] ProjectDocument M2M: `backend/app/models/project_document.py`
- [x] Project service: `backend/app/services/project.py`
- [x] Projects routes: `backend/app/routes/projects.py`
- [ ] ตรวจสอบ M2M operations (add/remove document)

---

### 4.2 Frontend Projects

#### FE-021 - FE-026: Projects Frontend
- [x] Projects store: `frontend/src/lib/stores/projects.svelte.ts`
- [x] Projects API: `frontend/src/lib/api/projects.ts`
- [x] Projects list: `frontend/src/routes/(app)/projects/+page.svelte`
- [x] Project detail: `frontend/src/routes/(app)/projects/[id]/+page.svelte`
- [x] ProjectDialog: `frontend/src/lib/components/projects/ProjectDialog.svelte`
- [x] AssignDocumentsDialog: `frontend/src/lib/components/projects/AssignDocumentsDialog.svelte`

---

#### FE-027: Project selector in chat
- [ ] เพิ่ม project dropdown ใน chat

**Description:** Dropdown เลือก project เพื่อใช้ documents ของ project นั้นสำหรับ RAG
**Files:** Chat page
**Reference:**
- Select component: `frontend/src/lib/components/ui/select/`
- Projects store: `frontend/src/lib/stores/projects.svelte.ts`
**Done when:** Chat ใช้ project's documents สำหรับ RAG

---

## PHASE 5: Agent Builder

### 5.1 Backend Agents

#### BE-038 - BE-045: Agents Backend
- [x] Agent model: `backend/app/models/agent.py`
- [x] AgentTool enum: `backend/app/models/agent.py`
- [x] Agent service: `backend/app/services/agent.py`
- [x] AgentLoader: `backend/app/services/agent_loader.py`
- [x] Agents routes: `backend/app/routes/agents.py`

---

#### BE-042: System agents YAML
- [ ] สร้าง YAML config สำหรับ pre-built agents

**Description:** Define system agents (general, coder, writer) ใน YAML file
**Files:** `backend/app/agents/system_agents.yaml`
**Reference:** AgentLoader service จะ load agents จาก file นี้
**Fields:** slug, name, icon, description, system_prompt, tools[]
**Done when:** System agents load ตอน app startup

---

#### BE-044: Agent in chat flow
- [ ] ใช้ agent config ใน chat

**Description:** เมื่อ chat กับ agent ให้ใช้ system_prompt และ tools ของ agent นั้น
**Files:** `backend/app/routes/chat.py`
**Reference:**
- Agent service: `backend/app/services/agent.py`
- RAG service: `backend/app/services/rag.py`
**Done when:** Different agents มี different behaviors

---

### 5.2 Frontend Agents

#### FE-028 - FE-035: Agents Frontend
- [x] Agents store: `frontend/src/lib/stores/agents.svelte.ts`
- [x] Agents API: `frontend/src/lib/api/agents.ts`
- [x] Agents list: `frontend/src/routes/(app)/agents/+page.svelte`
- [x] Agent detail: `frontend/src/routes/(app)/agents/[slug]/+page.svelte`
- [x] Agent create: `frontend/src/routes/(app)/agents/new/+page.svelte`
- [x] Agent edit: `frontend/src/routes/(app)/agents/[slug]/edit/+page.svelte`
- [x] AgentSelector: `frontend/src/lib/components/agents/AgentSelector.svelte`
- [x] AgentFormDialog: `frontend/src/lib/components/agents/AgentFormDialog.svelte`

---

## PHASE 6: Visual Workflow Builder

### 6.1 Backend Workflows

#### BE-046 - BE-050: Workflow Models & Service
- [x] Workflow model: `backend/app/models/workflow.py`
- [x] WorkflowExecution model: `backend/app/models/workflow.py`
- [x] NodeType enum: `backend/app/models/workflow.py`
- [x] Workflow service: `backend/app/services/workflow.py`
- [x] Workflows routes: `backend/app/routes/workflows.py`

---

#### BE-051-057: Workflow node executors
- [ ] Implement node executors

**Description:** สร้าง WorkflowEngine class ที่ execute แต่ละ node type
**Files:** `backend/app/services/workflow_engine.py`
**Reference:**
- NodeType enum: `backend/app/models/workflow.py`
- LLM service: `backend/app/services/llm.py`
- RAG service: `backend/app/services/rag.py`
**Node types:** start, end, llm, http, rag, condition, loop, agent
**Done when:** Execute workflow จาก start → end ได้

---

#### BE-059: Execution status SSE
- [ ] Stream execution progress

**Description:** SSE endpoint สำหรับ stream workflow execution status แบบ real-time
**Files:** `backend/app/routes/workflows.py`
**Reference:** ดู SSE pattern จาก chat streaming (BE-015)
**Events:** node_start, node_complete, error, done
**Done when:** Frontend เห็น node status เปลี่ยนแบบ real-time

---

### 6.2 Frontend Workflows

#### FE-036 - FE-037: Workflows Frontend Base
- [x] Workflows API: `frontend/src/lib/api/workflows.ts`
- [x] Workflows list: `frontend/src/routes/(app)/workflows/+page.svelte`
- [x] Workflow editor: `frontend/src/routes/(app)/workflows/[id]/+page.svelte`

---

#### FE-038: Setup @xyflow/svelte
- [ ] Install และ configure Svelte Flow

**Description:** Setup base canvas component สำหรับ workflow builder
**Files:** `frontend/src/lib/components/workflow/WorkflowCanvas.svelte`
**Dependencies:** `npm install @xyflow/svelte`
**Reference:** https://svelteflow.dev/
**Done when:** Canvas renders with controls และ background

---

#### FE-039-044: Node components
- [ ] สร้าง custom node components

**Description:** สร้าง Svelte components สำหรับแต่ละ node type
**Files:** `frontend/src/lib/components/workflow/nodes/`
**Reference:** @xyflow/svelte Handle, Position components
**Nodes:** StartNode, EndNode, LLMNode, HTTPNode, RAGNode, ConditionNode
**Done when:** แต่ละ node render และ config ได้

---

#### FE-045: WorkflowCanvas
- [ ] Canvas component with drag-drop

**Description:** Canvas ที่ add/connect/delete nodes ได้
**Files:** `frontend/src/lib/components/workflow/WorkflowCanvas.svelte`
**Done when:** Drag nodes, connect edges, delete nodes

---

#### FE-047-050: Workflow editor features
- [ ] Node palette - drag nodes จาก sidebar
- [ ] Save workflow - save to backend
- [ ] Execute workflow - trigger และ show progress
- [ ] Execution overlay - show node status real-time

---

## PHASE 7: Admin & Analytics

### 7.1 Backend Admin

#### BE-060 - BE-065: Admin Models
- [x] Plan model: `backend/app/models/plan.py`
- [x] Subscription model: `backend/app/models/subscription.py`
- [x] Invoice model: `backend/app/models/invoice.py`
- [x] UsageRecord model: `backend/app/models/usage.py`
- [x] UsageSummary model: `backend/app/models/usage.py`
- [x] AuditLog model: `backend/app/models/audit_log.py`

---

#### BE-066: Admin user guard
- [ ] ตรวจสอบว่ามี get_admin_user dependency

**Description:** Dependency ที่ check is_superuser สำหรับ admin routes
**Files:** `backend/app/core/dependencies.py`
**Reference:** ดู get_current_user dependency
**Done when:** Non-admin users get 403

---

#### BE-067-071: Admin routes
- [ ] ตรวจสอบว่ามี admin routes ครบ

**Files to check:**
- `backend/app/routes/admin/users.py`
- `backend/app/routes/admin/plans.py`
- `backend/app/routes/admin/usage.py`
- `backend/app/routes/admin/audit.py`
- `backend/app/routes/admin/dashboard.py`

---

#### BE-072-074: Billing
- [x] StripeService: `backend/app/services/stripe_service.py`
- [x] Billing routes: `backend/app/routes/billing.py`
- [x] Webhooks routes: `backend/app/routes/webhooks.py`

---

### 7.2 Frontend Admin

#### FE-051-065: Admin & Billing Frontend
- [x] Admin API: `frontend/src/lib/api/admin.ts`
- [x] Admin pages: `frontend/src/routes/(admin)/admin/...`
- [x] Billing API: `frontend/src/lib/api/billing.ts`
- [x] Billing pages: `frontend/src/routes/(app)/billing/...`
- [x] Pricing page: `frontend/src/routes/(public)/pricing/+page.svelte`

---

## PHASE 8: Notifications & Polish

### 8.1 Backend Notifications

#### BE-075-076: Notification Models
- [x] Notification model: `backend/app/models/notification.py`
- [x] NotificationPreference model: `backend/app/models/notification_preference.py`

---

#### BE-077-080: Notification Service & Routes
- [ ] ตรวจสอบ notification implementation

**Files to check:**
- `backend/app/schemas/notification.py`
- `backend/app/services/notification.py`
- `backend/app/routes/notifications.py`

**Triggers to implement:**
- Document ready
- Workflow complete
- Usage warning (approaching limit)

---

### 8.2 Frontend Notifications

#### FE-066-067: Notifications Base
- [x] Notifications store: `frontend/src/lib/stores/notifications.svelte.ts`
- [x] Notifications API: `frontend/src/lib/api/notifications.ts`

---

#### FE-068-071: Notification UI
- [ ] Bell component with badge
- [ ] Notification dropdown
- [ ] Notifications page
- [ ] Notification preferences in settings

**Files:** Header component, `frontend/src/routes/(app)/notifications/+page.svelte`
**Reference:** ดู dropdown pattern จาก `frontend/src/lib/components/ui/dropdown-menu/`

---

### 8.3 Public Pages & Observability

#### FE-072-077: Public Pages
- [x] Landing, About, Privacy, Terms, Contact, Changelog
- **Files:** `frontend/src/routes/(public)/...`

---

#### BE-081-083: OpenTelemetry
- [x] Telemetry setup: `backend/app/core/telemetry.py`

---

#### FE-078-079: Error Tracking
- [ ] Setup Glitchtip/Sentry

**Description:** Frontend error tracking และ performance monitoring
**Files:** `frontend/src/hooks.client.ts`

---

## Summary

### Progress by Phase

| Phase | Done | Total | % |
|-------|------|-------|---|
| 1 - Auth | 15 | 16 | 94% |
| 2 - Chat | 11 | 17 | 65% |
| 3 - Documents | 10 | 15 | 67% |
| 4 - Projects | 13 | 14 | 93% |
| 5 - Agents | 14 | 16 | 88% |
| 6 - Workflows | 6 | 14 | 43% |
| 7 - Admin | 14 | 17 | 82% |
| 8 - Notifications | 8 | 12 | 67% |

### Priority Tasks

1. **BE-014: LiteLLM integration** - Core feature
2. **BE-015: Chat streaming (SSE)** - Core feature
3. **BE-028: Document processor** - RAG pipeline
4. **BE-044: Agent in chat flow** - Agent behaviors
5. **BE-051-057: Workflow node executors** - Workflow engine
6. **FE-038-050: Workflow UI** - Visual builder

---

## Notes

1. **Codebase พร้อมแล้ว 70%+** - Models, routes, services ส่วนใหญ่เสร็จ
2. **Focus on integration** - เน้นต่อ components (LLM + RAG + Streaming)
3. **Workflow ต้องทำมากสุด** - ยังขาด engine และ UI
4. **Test end-to-end** - ทดสอบ flow ทั้งหมดหลังต่อเสร็จ
