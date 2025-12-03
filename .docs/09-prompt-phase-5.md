# Phase 5: Text-to-SQL with Schema Linking - Implementation Prompts

## Overview

**Goal**: User สามารถ query database ด้วยภาษาธรรมชาติ โดยมี Schema Linking และ User Confirmation

**Architecture**:
```
User Query ──▶ Schema Linking ──▶ SQL Generation ──▶ User Confirm ──▶ Safe Execute
                (RAG on Schema)    (Pruned Schema)     (Review SQL)     (Read-only)
```

**Key Features**:
- Schema Linking: ใช้ RAG หา tables ที่เกี่ยวข้อง (ไม่ส่งทั้ง 100 tables)
- User Confirmation: แสดง SQL ให้ user ยืนยันก่อน execute
- Safe Execution: Read-only, timeout 30s, max 1000 rows

**Supported Databases**: PostgreSQL, MySQL

---

## Backend Tasks

### Task B1: Database Connection Model

**Files**: `backend/app/models/db_connection.py` (NEW)

**Context**:
- `backend/app/models/project.py` - ดู model pattern
- Connection string ต้อง encrypt

**Requirements**:
1. Create `DatabaseConnection` model:
   - id, project_id (FK), name, db_type (postgres/mysql)
   - host, port, database, username, password (encrypted)
   - is_active, created_at, updated_at
2. Encrypt password using Fernet (from cryptography)
3. Add relationship to Project (one-to-many)

**Testing**:
```bash
cd backend && uv run python -c "
from app.models.db_connection import DatabaseConnection
print('DatabaseConnection model OK')
"
```

---

### Task B2: Database Connection Service

**Files**: `backend/app/services/db_connection.py` (NEW)

**Context**:
- `backend/app/services/document.py` - ดู service pattern

**Requirements**:
1. Create `DatabaseConnectionService`:
   - `create_connection()` - save with encrypted password
   - `test_connection()` - verify connection works
   - `get_connection()` - get by id with decrypted password
   - `list_connections()` - list by project_id
   - `delete_connection()` - remove connection
2. Use SQLAlchemy for actual DB connection
3. Support both PostgreSQL and MySQL

**Testing**:
```bash
cd backend && uv run python -c "
from app.services.db_connection import db_connection_service
print('DB Connection service OK')
"
```

---

### Task B3: Schema Extractor

**Files**: `backend/app/text2sql/schema_extractor.py` (NEW)

**Context**:
- Need to extract: tables, columns, types, relationships, descriptions

**Requirements**:
1. Create `SchemaExtractor` class:
   - `extract_schema(connection_id) -> list[TableSchema]`
   - Extract: table_name, columns (name, type, nullable, pk, fk)
   - Detect relationships (foreign keys)
2. Support PostgreSQL (information_schema)
3. Support MySQL (information_schema)
4. Cache schema (don't re-extract every time)

**TableSchema**:
```python
class ColumnSchema(BaseModel):
    name: str
    data_type: str
    nullable: bool
    is_primary_key: bool
    foreign_key: str | None  # "table.column"
    description: str | None

class TableSchema(BaseModel):
    name: str
    columns: list[ColumnSchema]
    description: str | None
    row_count: int | None
```

**Testing**:
```bash
cd backend && uv run python -c "
from app.text2sql.schema_extractor import SchemaExtractor
print('Schema extractor OK')
"
```

---

### Task B4: Schema Embedding Service

**Files**: `backend/app/text2sql/schema_embedder.py` (NEW)

**Context**:
- `backend/app/services/embedding.py` - ใช้ existing embedding service
- `backend/app/services/vector_store.py` - ดู vector storage pattern

**Requirements**:
1. Create `SchemaEmbedder` class:
   - `embed_schema(connection_id)` - embed all tables/columns
   - `search_relevant_tables(query, top_k=5) -> list[TableSchema]`
2. Embed format: "Table: {name}. {description}. Columns: {col1}, {col2}..."
3. Store in pgvector (separate collection/table for schema)
4. Re-embed when schema changes

**Testing**:
```bash
cd backend && uv run python -c "
from app.text2sql.schema_embedder import SchemaEmbedder
print('Schema embedder OK')
"
```

---

### Task B5: SQL Generator

**Files**: `backend/app/text2sql/sql_generator.py` (NEW)

**Context**:
- `backend/app/providers/llm.py` - ใช้ llm_client

**Requirements**:
1. Create `SQLGenerator` class:
   - `generate(query, relevant_tables) -> SQLGenerationResult`
2. Build prompt with pruned schema only
3. Return: sql, explanation, affected_tables, estimated_rows
4. Validate SQL: SELECT only (no INSERT, UPDATE, DELETE, DROP)

**Prompt Template**:
```
Given this database schema:
{pruned_schema}

Generate a SQL query to answer: {user_query}

Rules:
- Use only SELECT statements
- No DELETE, UPDATE, DROP, or INSERT
- Include only necessary columns
- Add appropriate WHERE clauses

Respond in JSON:
{"sql": "...", "explanation": "...", "tables": [...]}
```

**Testing**:
```bash
cd backend && uv run python -c "
from app.text2sql.sql_generator import SQLGenerator
print('SQL generator OK')
"
```

---

### Task B6: SQL Validator

**Files**: `backend/app/text2sql/sql_validator.py` (NEW)

**Context**:
- Safety checks before execution

**Requirements**:
1. Create `SQLValidator` class:
   - `validate(sql) -> ValidationResult`
2. Check for dangerous statements: DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER
3. Check for dangerous functions: SLEEP, BENCHMARK, LOAD_FILE
4. Parse SQL to verify it's SELECT only
5. Return: is_valid, errors, warnings

**Testing**:
```bash
cd backend && uv run python -c "
from app.text2sql.sql_validator import SQLValidator
validator = SQLValidator()
print(validator.validate('SELECT * FROM users'))
print(validator.validate('DROP TABLE users'))
"
```

---

### Task B7: Safe SQL Executor

**Files**: `backend/app/text2sql/executor.py` (NEW)

**Context**:
- Must be read-only with safety limits

**Requirements**:
1. Create `SafeSQLExecutor` class:
   - `execute(connection_id, sql) -> ExecutionResult`
2. Safety features:
   - Read-only connection (use transaction with ROLLBACK)
   - Timeout: 30 seconds
   - Row limit: 1000 rows (add LIMIT if not present)
   - Memory limit check
3. Return: rows, columns, execution_time, row_count

**Testing**:
```bash
cd backend && uv run python -c "
from app.text2sql.executor import SafeSQLExecutor
print('SQL executor OK')
"
```

---

### Task B8: Text-to-SQL Routes

**Files**: `backend/app/routes/text2sql.py` (NEW)

**Context**:
- `backend/app/routes/chat.py` - ดู route pattern

**Requirements**:
1. Create routes:
   - `POST /api/projects/{id}/databases` - Add connection
   - `GET /api/projects/{id}/databases` - List connections
   - `POST /api/projects/{id}/databases/{db_id}/test` - Test connection
   - `POST /api/projects/{id}/databases/{db_id}/sync-schema` - Extract & embed schema
   - `POST /api/projects/{id}/databases/{db_id}/generate-sql` - Generate SQL from query
   - `POST /api/projects/{id}/databases/{db_id}/execute` - Execute confirmed SQL
   - `GET /api/projects/{id}/databases/{db_id}/schema` - Get schema info
2. Register in `main.py`

**API Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/projects/{id}/databases | Add DB connection |
| GET | /api/projects/{id}/databases | List connections |
| POST | /api/projects/{id}/databases/{db_id}/test | Test connection |
| POST | /api/projects/{id}/databases/{db_id}/sync-schema | Sync schema |
| POST | /api/projects/{id}/databases/{db_id}/generate-sql | Generate SQL |
| POST | /api/projects/{id}/databases/{db_id}/execute | Execute SQL |

**Testing**:
```bash
TOKEN="your-jwt-token"
# Add connection
curl -s -X POST http://localhost:8000/api/projects/PROJECT_ID/databases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Sales DB", "db_type": "postgres", "host": "localhost", "port": 5432, "database": "sales", "username": "user", "password": "pass"}' | jq

# Generate SQL
curl -s -X POST http://localhost:8000/api/projects/PROJECT_ID/databases/DB_ID/generate-sql \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "ยอดขายของลูกค้า VIP เดือนนี้"}' | jq
```

---

## Frontend Tasks

### Task F1: Database Connection API

**Files**: `frontend/src/lib/api/databases.ts` (NEW)

**Context**:
- `frontend/src/lib/api/projects.ts` - ดู pattern

**Requirements**:
1. Create types: `DatabaseConnection`, `TableSchema`, `SQLGenerationResult`, `ExecutionResult`
2. Create functions:
   - `addConnection()`, `listConnections()`, `testConnection()`
   - `syncSchema()`, `getSchema()`
   - `generateSQL()`, `executeSQL()`
3. Export in `index.ts`

**Testing**: `cd frontend && npm run check`

---

### Task F2: Database Connection Manager

**Files**: `frontend/src/lib/components/databases/ConnectionManager.svelte` (NEW)

**Context**:
- `frontend/src/lib/components/ui/dialog/` - ดู Dialog

**Requirements**:
1. List existing connections
2. Add new connection dialog (form: name, type, host, port, db, user, pass)
3. Test connection button
4. Delete connection
5. Sync schema button

**Testing**: `cd frontend && npm run check`

---

### Task F3: SQL Confirm Component

**Files**: `frontend/src/lib/components/text2sql/SQLConfirm.svelte` (NEW)

**Context**:
- Need syntax highlighting for SQL

**Requirements**:
1. Display generated SQL with syntax highlighting
2. Show: affected tables, estimated rows, explanation
3. Buttons: Execute, Edit, Cancel
4. Optional: "Don't ask again" checkbox
5. Props: `sql`, `explanation`, `tables`, `onExecute`, `onEdit`, `onCancel`

**Testing**: `cd frontend && npm run check`

---

### Task F4: SQL Result Viewer

**Files**: `frontend/src/lib/components/text2sql/SQLResult.svelte` (NEW)

**Context**:
- Display query results as table

**Requirements**:
1. Display results as table
2. Show: columns, rows, execution time, row count
3. Pagination if > 100 rows
4. Export to CSV button
5. Props: `result: ExecutionResult`

**Testing**: `cd frontend && npm run check`

---

### Task F5: Text-to-SQL Chat Integration

**Files**: Update `frontend/src/lib/components/llm-chat/LLMChat.svelte`

**Context**:
- Integrate SQL generation/execution into chat flow

**Requirements**:
1. Detect when response contains SQL suggestion
2. Show SQLConfirm component inline
3. On execute, show SQLResult
4. Store SQL history in conversation

**Testing**: Manual - ask SQL question, confirm, see results

---

### Task F6: Database Settings Page

**Files**: `frontend/src/routes/(app)/projects/[id]/databases/+page.svelte` (NEW)

**Context**:
- `frontend/src/routes/(app)/projects/` - ดู project pages

**Requirements**:
1. Show ConnectionManager component
2. Show schema browser (list tables/columns)
3. Test query interface

**Testing**: Navigate to /projects/{id}/databases

---

## Execution Order

```
Backend:  B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8
Frontend: F1 → F2 → F3 → F4 → F5 → F6
```

**Dependencies**:
- B3-B4 depend on B1-B2 (connection)
- B5 depends on B4 (schema embeddings)
- B7 depends on B6 (validation)
- Frontend depends on Backend B8

---

## API Testing (After Backend Done)

```bash
TOKEN="your-jwt-token"
PROJECT_ID="your-project-id"

# 1. Add database connection
DB_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/projects/$PROJECT_ID/databases" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Database",
    "db_type": "postgres",
    "host": "localhost",
    "port": 5432,
    "database": "sales",
    "username": "user",
    "password": "password"
  }')
DB_ID=$(echo $DB_RESPONSE | jq -r '.data.id')
echo "Database ID: $DB_ID"

# 2. Test connection
curl -s -X POST "http://localhost:8000/api/projects/$PROJECT_ID/databases/$DB_ID/test" \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Sync schema
curl -s -X POST "http://localhost:8000/api/projects/$PROJECT_ID/databases/$DB_ID/sync-schema" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Generate SQL
curl -s -X POST "http://localhost:8000/api/projects/$PROJECT_ID/databases/$DB_ID/generate-sql" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "ยอดขายของลูกค้า VIP เดือนนี้"}' | jq

# 5. Execute SQL (after user confirms)
curl -s -X POST "http://localhost:8000/api/projects/$PROJECT_ID/databases/$DB_ID/execute" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT c.name, SUM(o.amount) FROM orders o JOIN customers c ON o.customer_id = c.id WHERE c.tier = '\''VIP'\'' GROUP BY c.id"}' | jq
```

---

## Quick Reference

### Safety Checks
```python
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER",
    "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE"
]

DANGEROUS_FUNCTIONS = [
    "SLEEP", "BENCHMARK", "LOAD_FILE", "INTO OUTFILE", "INTO DUMPFILE"
]
```

### Schema Embedding Format
```
Table: orders
Description: Customer orders with amounts and dates
Columns: id (int, PK), customer_id (int, FK->customers.id), amount (decimal), created_at (timestamp)
```

### SQL Generation Prompt
```
Given this database schema:
Table: orders (id, customer_id, amount, created_at)
Table: customers (id, name, tier, email)

Generate SQL for: "ยอดขายของลูกค้า VIP เดือนนี้"
```

---

*Last updated: December 2024*
