# Phase 6: Project System - Task Prompts

## Overview
ระบบ Project สำหรับจัดกลุ่ม Documents และ Conversations

**Relationships:**
- Project ↔ Document: Many-to-Many (ผ่าน ProjectDocument junction table)
- Project ↔ Conversation: One-to-Many (Conversation.project_id optional FK)
- User → Project: One-to-Many (owner)

---

# PROMPT BACKEND

## Task 1: Project Models & Migration

```
สร้าง/อัปเดต models สำหรับ Project System

1. ตรวจสอบ Project model ที่มีอยู่ใน backend/app/models/project.py
   - ต้องมี fields: id, name, description, user_id, created_at, updated_at

2. สร้าง ProjectDocument junction table (many-to-many)
   - Fields: id, project_id (FK), document_id (FK), added_at
   - Unique constraint บน (project_id, document_id)

3. เพิ่ม project_id ใน Conversation model
   - Optional FK to Project
   - Nullable (conversation ไม่จำเป็นต้องอยู่ใน project)

4. อัปเดต backend/app/models/__init__.py เพิ่ม exports

5. สร้าง Alembic migration

ไฟล์ที่ต้องแก้/สร้าง:
- backend/app/models/project.py
- backend/app/models/project_document.py (ใหม่)
- backend/app/models/conversation.py (เพิ่ม project_id)
- backend/app/models/__init__.py
- backend/alembic/versions/xxx_add_project_system.py
```

---

## Task 2: Project Schemas

```
สร้าง Pydantic schemas สำหรับ Project API

1. สร้าง backend/app/schemas/project.py:
   - ProjectCreate: name (required), description (optional)
   - ProjectUpdate: name (optional), description (optional)
   - ProjectResponse: id, name, description, user_id, created_at, updated_at
   - ProjectListResponse: items, total, page, per_page, pages
   - ProjectDetailResponse: รวม document_count, conversation_count

2. สร้าง schemas สำหรับ assign documents:
   - AssignDocumentsRequest: document_ids (list[uuid])
   - RemoveDocumentsRequest: document_ids (list[uuid])

ไฟล์ที่ต้องสร้าง:
- backend/app/schemas/project.py
```

---

## Task 3: Project Service

```
สร้าง service layer สำหรับ Project operations

1. สร้าง backend/app/services/project.py:
   - create_project(db, user_id, data) -> Project
   - get_project(db, project_id, user_id) -> Project | None
   - get_projects(db, user_id, page, per_page) -> tuple[list[Project], int]
   - update_project(db, project_id, user_id, data) -> Project | None
   - delete_project(db, project_id, user_id) -> bool

2. Document assignment functions:
   - assign_documents(db, project_id, user_id, document_ids) -> int (count added)
   - remove_documents(db, project_id, user_id, document_ids) -> int (count removed)
   - get_project_documents(db, project_id, user_id) -> list[Document]

3. เพิ่ม @traced() decorator สำหรับ telemetry

ไฟล์ที่ต้องสร้าง:
- backend/app/services/project.py
```

---

## Task 4: Project Routes

```
สร้าง API endpoints สำหรับ Project

1. สร้าง backend/app/routes/projects.py:
   - POST /projects - สร้าง project
   - GET /projects - list projects ของ user (with pagination)
   - GET /projects/{id} - get project detail
   - PATCH /projects/{id} - update project
   - DELETE /projects/{id} - delete project

2. Document assignment endpoints:
   - POST /projects/{id}/documents - assign documents
   - DELETE /projects/{id}/documents - remove documents
   - GET /projects/{id}/documents - list documents in project

3. Register router ใน main.py

4. ใช้ BaseResponse wrapper ทุก endpoint

ไฟล์ที่ต้องสร้าง/แก้:
- backend/app/routes/projects.py (ใหม่)
- backend/app/main.py (register router)
```

---

## Task 5: Update RAG for Project Scope

```
อัปเดต RAG service ให้ filter ตาม project

1. แก้ไข backend/app/services/vector_store.py:
   - เพิ่ม parameter project_id ใน search()
   - ถ้ามี project_id ให้ filter เฉพาะ documents ใน project นั้น
   - ใช้ JOIN กับ ProjectDocument table

2. แก้ไข backend/app/services/rag.py:
   - เพิ่ม parameter project_id ใน retrieve_context()

3. แก้ไข backend/app/routes/chat.py:
   - เพิ่ม project_id ใน ChatRequest schema
   - Pass project_id ไป RAG service

4. แก้ไข backend/app/schemas/chat.py:
   - เพิ่ม project_id: uuid.UUID | None ใน ChatRequest

ไฟล์ที่ต้องแก้:
- backend/app/services/vector_store.py
- backend/app/services/rag.py
- backend/app/routes/chat.py
- backend/app/schemas/chat.py
```

---

# PROMPT FRONTEND

## Task 1: Project Types & API Client

```
สร้าง TypeScript types และ API client สำหรับ Project

1. สร้าง frontend/src/lib/api/projects.ts:
   - Types: Project, ProjectCreate, ProjectUpdate, ProjectDetail
   - projectsApi object:
     - list(page, perPage) -> PaginatedResponse<Project>
     - get(id) -> ProjectDetail
     - create(data) -> Project
     - update(id, data) -> Project
     - delete(id) -> void
     - assignDocuments(id, documentIds) -> void
     - removeDocuments(id, documentIds) -> void
     - getDocuments(id) -> Document[]

2. Export จาก frontend/src/lib/api/index.ts

ไฟล์ที่ต้องสร้าง/แก้:
- frontend/src/lib/api/projects.ts (ใหม่)
- frontend/src/lib/api/index.ts
```

---

## Task 2: Project Store

```
สร้าง Svelte store สำหรับจัดการ project state

1. สร้าง frontend/src/lib/stores/projects.svelte.ts:
   - projects: Project[] - list ทั้งหมด
   - currentProject: Project | null - project ที่เลือกอยู่
   - loading: boolean
   - Functions:
     - loadProjects()
     - selectProject(id | null)
     - createProject(data)
     - updateProject(id, data)
     - deleteProject(id)

2. ใช้ Svelte 5 runes ($state, $derived)

3. เก็บ currentProjectId ใน localStorage

ไฟล์ที่ต้องสร้าง:
- frontend/src/lib/stores/projects.svelte.ts
```

---

## Task 3: Project Sidebar Component

```
สร้าง component แสดง projects ใน sidebar

1. สร้าง frontend/src/lib/components/projects/ProjectList.svelte:
   - แสดง list ของ projects
   - Highlight project ที่เลือกอยู่
   - ปุ่ม "All Documents" (ไม่เลือก project)
   - ปุ่ม "+" สร้าง project ใหม่
   - Click เพื่อ switch project

2. ใช้ Svelte 5 syntax ($props, $state, $derived)

3. ใช้ shadcn-svelte components (Button, ScrollArea)

ไฟล์ที่ต้องสร้าง:
- frontend/src/lib/components/projects/ProjectList.svelte
```

---

## Task 4: Create/Edit Project Dialog

```
สร้าง dialog สำหรับสร้าง/แก้ไข project

1. สร้าง frontend/src/lib/components/projects/ProjectDialog.svelte:
   - Props: open, project (null = create, object = edit), onClose, onSave
   - Form fields: name (required), description (optional)
   - Validation: name required, max length
   - Loading state ขณะ save

2. ใช้ shadcn-svelte: Dialog, Input, Textarea, Button

ไฟล์ที่ต้องสร้าง:
- frontend/src/lib/components/projects/ProjectDialog.svelte
```

---

## Task 5: Project Detail Page

```
สร้างหน้า project detail

1. สร้าง frontend/src/routes/(app)/projects/[id]/+page.svelte:
   - แสดง project info (name, description)
   - Tab: Documents | Conversations
   - Documents tab: list documents พร้อมปุ่ม assign/remove
   - Conversations tab: list conversations ใน project
   - ปุ่ม Edit project
   - ปุ่ม Delete project (with confirm)

2. สร้าง +page.ts สำหรับ load project data

ไฟล์ที่ต้องสร้าง:
- frontend/src/routes/(app)/projects/[id]/+page.svelte
- frontend/src/routes/(app)/projects/[id]/+page.ts
```

---

## Task 6: Assign Documents Dialog

```
สร้าง dialog สำหรับ assign documents เข้า project

1. สร้าง frontend/src/lib/components/projects/AssignDocumentsDialog.svelte:
   - Props: open, projectId, existingDocumentIds, onClose, onAssign
   - แสดง list documents ทั้งหมดของ user
   - Checkbox เลือก documents
   - Filter: แสดงเฉพาะที่ยังไม่ได้ assign
   - ปุ่ม Assign selected

2. ใช้ shadcn-svelte: Dialog, Checkbox, Button, ScrollArea

ไฟล์ที่ต้องสร้าง:
- frontend/src/lib/components/projects/AssignDocumentsDialog.svelte
```

---

## Task 7: Update Chat to Support Project Context

```
อัปเดต Chat ให้รองรับ project context

1. แก้ไข frontend/src/lib/api/chat.ts:
   - เพิ่ม project_id ใน ChatRequest interface

2. แก้ไข frontend/src/lib/components/llm-chat/LLMChat.svelte:
   - รับ prop projectId (optional)
   - ส่ง project_id ไปกับ chat request เมื่อ use_rag = true

3. แก้ไข frontend/src/lib/components/llm-chat/ChatHeader.svelte:
   - แสดง project name ถ้ามี projectId

ไฟล์ที่ต้องแก้:
- frontend/src/lib/api/chat.ts
- frontend/src/lib/components/llm-chat/LLMChat.svelte
- frontend/src/lib/components/llm-chat/ChatHeader.svelte
```

---

## Task 8: Integrate Project into Layout

```
รวม Project system เข้ากับ layout หลัก

1. แก้ไข frontend/src/lib/components/layout/Sidebar.svelte:
   - เพิ่ม ProjectList component
   - แสดงใต้ navigation หลัก

2. แก้ไข frontend/src/routes/(app)/+layout.svelte:
   - Load projects เมื่อ mount
   - Pass currentProject ไป child routes

3. แก้ไข frontend/src/routes/(app)/chat/+page.svelte:
   - ใช้ currentProject สำหรับ RAG scope

ไฟล์ที่ต้องแก้:
- frontend/src/lib/components/layout/Sidebar.svelte
- frontend/src/routes/(app)/+layout.svelte
- frontend/src/routes/(app)/chat/+page.svelte
```

---

# Execution Order

## แนะนำลำดับการทำ:

### Backend First:
1. Task 1: Models & Migration
2. Task 2: Schemas
3. Task 3: Service
4. Task 4: Routes
5. Task 5: Update RAG

### Then Frontend:
1. Task 1: Types & API
2. Task 2: Store
3. Task 3: Project List
4. Task 4: Create/Edit Dialog
5. Task 5: Detail Page
6. Task 6: Assign Documents
7. Task 7: Chat Integration
8. Task 8: Layout Integration

---

# Notes

- ใช้ Svelte 5 runes syntax (ไม่ใช่ Svelte 4)
- ใช้ BaseResponse wrapper ทุก API endpoint
- ใช้ @traced() decorator ใน services
- Type hints ทุก function ใน Python
- ทดสอบ API ด้วย curl หรือ Postman ก่อนทำ frontend
