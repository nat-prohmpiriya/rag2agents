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
- [x] สร้าง LLM service สำหรับ chat completion

**Files:** `backend/app/providers/llm.py`
**Status:** ✅ เสร็จแล้ว - มี LLMClient class รองรับ chat completion, streaming, vision models

---

#### BE-015: Chat streaming (SSE)
- [x] Implement SSE streaming endpoint

**Files:** `backend/app/routes/chat.py:464-625`
**Status:** ✅ เสร็จแล้ว - POST /chat/stream พร้อม SSE streaming

---

#### BE-017: Chat schemas
- [x] สร้าง Pydantic schemas สำหรับ chat

**Files:** `backend/app/schemas/chat.py`
**Status:** ✅ เสร็จแล้ว - มี ChatRequest, ChatResponse, ChatMessage, UsageInfo, SourceInfo, AgentChatResponse

---

#### BE-018: Track token usage
- [x] บันทึก tokens ในแต่ละ message

**Files:** `backend/app/routes/chat.py` (record_chat_usage function)
**Status:** ✅ เสร็จแล้ว - UsageRecord ถูกสร้างหลังทุก chat

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
- [x] ตรวจสอบว่ามี component แสดง message

**Files:** Chat pages (integrated)
**Status:** ✅ เสร็จแล้ว - Render markdown และ code blocks ได้

---

#### FE-011: ChatInput component
- [x] ตรวจสอบว่ามี input component

**Files:** Chat pages (integrated)
**Status:** ✅ เสร็จแล้ว - Enter = send, Shift+Enter = newline

---

#### FE-015: Sidebar conversations
- [x] แสดง recent conversations ใน sidebar

**Files:**
- `frontend/src/lib/components/layout/Sidebar.svelte`
- `frontend/src/lib/components/chat/ChatHistorySidebar.svelte`
**Status:** ✅ เสร็จแล้ว - แสดง conversations grouped by date, search, delete

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
- [x] Extract text จาก PDF และ DOCX

**Files:** `backend/app/services/document_processor.py`
**Status:** ✅ เสร็จแล้ว - มี TextExtractor class รองรับ PDF, DOCX, TXT, MD, CSV

---

#### BE-025: Text chunking
- [x] Split text เป็น chunks

**Files:** `backend/app/services/document_processor.py`
**Status:** ✅ เสร็จแล้ว - มี TextChunker class พร้อม overlapping chunks

---

#### BE-026 - BE-027: Embedding & Vector Store
- [x] Embedding service: `backend/app/services/embedding.py`
- [x] Vector store: `backend/app/services/vector_store.py`

---

#### BE-028: Background document processor
- [x] Process document ใน background

**Files:** `backend/app/services/document_processor.py`
**Status:** ✅ เสร็จแล้ว - มี DocumentProcessor class ครบ pipeline

---

#### BE-030: RAG in chat flow
- [x] RAG service: `backend/app/services/rag.py`
- [x] Integrate กับ chat streaming

**Files:** `backend/app/routes/chat.py:361-393, 524-552`
**Status:** ✅ เสร็จแล้ว - Chat uses document context เมื่อ use_rag=true

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
- [x] เพิ่ม project dropdown ใน chat

**Description:** Dropdown เลือก project เพื่อใช้ documents ของ project นั้นสำหรับ RAG
**Files:**
- `frontend/src/lib/components/llm-chat2/ChatInput.svelte` (Project selector dropdown)
- `frontend/src/lib/components/llm-chat2/LLMChat2.svelte` (projectId prop, project_id in request)
- `frontend/src/routes/(app)/chat/+page.svelte`
- `frontend/src/routes/(app)/chat/[id]/+page.svelte`
**Status:** ✅ เสร็จแล้ว - Project dropdown ใน chat toolbar, เลือก project แล้วส่ง project_id ไปกับ chat request

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
- [x] ใช้ agent config ใน chat

**Files:** `backend/app/routes/chat.py:259-356`
**Status:** ✅ เสร็จแล้ว - AgentEngine integrated, different agents have different behaviors

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
- [x] Implement node executors

**Files:** `backend/app/services/workflow_engine.py`
**Status:** ✅ เสร็จแล้ว - มี executors ครบ: StartNode, EndNode, LLMNode, RAGNode, AgentNode, ConditionNode, LoopNode, HTTPNode, CustomFunctionNode + WorkflowEngine class

---

#### BE-059: Execution status SSE
- [x] Stream execution progress

**Files:**
- `backend/app/routes/workflows.py` (workflow_chat_stream endpoint)
- `backend/app/services/workflow_engine.py` (WorkflowEngineStream class)
**Status:** ✅ เสร็จแล้ว - มี SSE events: node_id, node_type, status, done

---

### 6.2 Frontend Workflows

#### FE-036 - FE-037: Workflows Frontend Base
- [x] Workflows API: `frontend/src/lib/api/workflows.ts`
- [x] Workflows list: `frontend/src/routes/(app)/workflows/+page.svelte`
- [x] Workflow editor: `frontend/src/routes/(app)/workflows/[id]/+page.svelte`

---

#### FE-038: Setup @xyflow/svelte
- [x] Install และ configure Svelte Flow

**Files:** `frontend/src/lib/components/workflow/WorkflowCanvas.svelte`
**Status:** ✅ เสร็จแล้ว

---

#### FE-039-044: Node components
- [x] สร้าง custom node components

**Files:** `frontend/src/lib/components/workflow/nodes/`
- StartNode.svelte
- EndNode.svelte
- LLMNode.svelte
- HTTPNode.svelte
- RAGNode.svelte
- ConditionNode.svelte
- AgentNode.svelte
**Status:** ✅ เสร็จแล้ว

---

#### FE-045: WorkflowCanvas
- [x] Canvas component with drag-drop

**Files:** `frontend/src/lib/components/workflow/WorkflowCanvas.svelte`
**Status:** ✅ เสร็จแล้ว

---

#### FE-047-050: Workflow editor features
- [x] Node palette - `NodePalette.svelte`
- [x] Save workflow - save to backend
- [x] Execute workflow - trigger และ show progress
- [x] Node config panel - `NodeConfigPanel.svelte`
- [x] Execution overlay - BE-059 SSE เสร็จแล้ว

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
- [x] ตรวจสอบว่ามี get_admin_user dependency

**Files:** `backend/app/core/dependencies.py:104-118`
**Status:** ✅ เสร็จแล้ว - มี `require_admin` dependency

---

#### BE-067-071: Admin routes
- [x] ตรวจสอบว่ามี admin routes ครบ

**Files:** `backend/app/routes/admin/`
- users.py ✅
- plans.py ✅
- usage.py ✅
- audit.py ✅
- dashboard.py ✅
- subscriptions.py ✅
- settings.py ✅
- notifications.py ✅
- system.py ✅
**Status:** ✅ เสร็จแล้ว

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
- [x] ตรวจสอบ notification implementation

**Files:**
- `backend/app/schemas/notification.py` ✅
- `backend/app/services/notification.py` ✅
- `backend/app/services/notification_sse.py` ✅ (real-time)
- `backend/app/routes/notifications.py` (via admin routes) ✅
**Status:** ✅ เสร็จแล้ว

---

### 8.2 Frontend Notifications

#### FE-066-067: Notifications Base
- [x] Notifications store: `frontend/src/lib/stores/notifications.svelte.ts`
- [x] Notifications API: `frontend/src/lib/api/notifications.ts`

---

#### FE-068-071: Notification UI
- [x] Bell component with badge (in Sidebar)
- [x] Notifications page
- [x] Notification list with filter, pagination
- [x] Mark as read, delete

**Files:** `frontend/src/routes/(app)/notifications/+page.svelte`
**Status:** ✅ เสร็จแล้ว

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
| 2 - Chat | 17 | 17 | 100% ✅ |
| 3 - Documents | 14 | 15 | 93% |
| 4 - Projects | 14 | 14 | 100% ✅ |
| 5 - Agents | 15 | 16 | 94% |
| 6 - Workflows | 14 | 14 | 100% ✅ |
| 7 - Admin | 17 | 17 | 100% ✅ |
| 8 - Notifications | 11 | 12 | 92% |

### Remaining Tasks

1. **BE-001**: UserTier enum (เปลี่ยน tier จาก string เป็น Enum)
2. **BE-042**: System agents YAML (pre-built agents config)
3. **FE-018**: Document upload UI (drag-drop component)
4. **FE-020**: Document status polling
5. **FE-078-079**: Error Tracking (Glitchtip/Sentry)

---

## Notes

1. **Codebase พร้อมแล้ว 95%+** - Core features ทั้งหมดเสร็จแล้ว
2. **Chat + RAG + Agent + Workflow** - ✅ ทำงานได้ครบ
3. **Remaining** - เป็น polish และ enhancement เล็กน้อย
4. **Ready for production** - หลัง fix remaining tasks
