# Phase 3: PII Protection - Implementation Prompts

## Overview

**Goal**: ปกป้องข้อมูลส่วนตัว (PII) ก่อนส่งไป LLM โดยใช้ Microsoft Presidio

**Architecture**:
```
User Input ──▶ PII Scrubber ──▶ RAG/Chat ──▶ LLM ──▶ Response
                    │
                    ▼
              ┌─────────────┐
              │ Audit Log   │ (encrypted)
              │ + Mapping   │ (for restore)
              └─────────────┘
```

**Privacy Levels**:
| Level | Mask | Use Case |
|-------|------|----------|
| strict | ทุก PII | Mental Health, Medical |
| moderate | sensitive only (ID, credit card) | General Business |
| off | ไม่ mask | Internal use |

**PII Types**:
| Type | Example | Detection |
|------|---------|-----------|
| PERSON | คุณสมชาย ใจดี | NER + Pattern |
| PHONE | 081-234-5678 | Regex |
| EMAIL | test@example.com | Regex |
| ID_CARD | 1-1234-56789-01-2 | Regex (13 digits) |
| CREDIT_CARD | 4111-1111-1111-1111 | Luhn + Regex |
| LOCATION | กรุงเทพ | NER |
| MEDICAL_RECORD | HN: 12345 | Custom Regex |

---

## Backend Tasks

### Task B1: Install Presidio & Create PIIScrubber

**Files**: `backend/app/privacy/pii_scrubber.py` (NEW)

**Context**:
- `.docs/02-spec.md` section 3 (PII Protection System)
- `backend/app/services/rag.py` - ดู service pattern

**Requirements**:
1. Add dependencies to `pyproject.toml`:
   ```
   presidio-analyzer>=2.2.0
   presidio-anonymizer>=2.2.0
   ```
2. Create `PIIScrubber` class with methods:
   - `scrub(text, level) -> tuple[str, dict]` - returns (scrubbed_text, mapping)
   - `_get_entities_for_level(level) -> list` - returns entity types to detect
3. Use Presidio's `AnalyzerEngine` and `AnonymizerEngine`
4. Return mapping for potential restoration: `{"[PERSON_0]": "original_name"}`

**Testing**:
```bash
cd backend && uv sync
cd backend && uv run python -c "
from app.privacy.pii_scrubber import PIIScrubber
scrubber = PIIScrubber()
text = 'คุณสมชาย โทร 081-234-5678'
result, mapping = scrubber.scrub(text, 'strict')
print(f'Result: {result}')
print(f'Mapping: {mapping}')
"
```

---

### Task B2: Thai PII Recognizers

**Files**: `backend/app/privacy/thai_recognizers.py` (NEW)

**Context**:
- Presidio custom recognizer docs
- Thai phone format: 0X-XXX-XXXX or 0XX-XXX-XXXX
- Thai ID card: 13 digits (X-XXXX-XXXXX-XX-X)

**Requirements**:
1. Create `ThaiPhoneRecognizer` class (extends `PatternRecognizer`)
   - Pattern: `0[689]\d-\d{3}-\d{4}` หรือ `0[689]\d{8}`
2. Create `ThaiIDCardRecognizer` class
   - Pattern: 13 digits with optional dashes
   - Validate checksum (digit 13)
3. Create `ThaiNameRecognizer` class (optional, use spaCy NER)
4. Register recognizers in `PIIScrubber.__init__()`

**Testing**:
```bash
cd backend && uv run python -c "
from app.privacy.pii_scrubber import PIIScrubber
scrubber = PIIScrubber()
# Test Thai phone
text1 = 'โทร 081-234-5678 หรือ 0912345678'
print(scrubber.scrub(text1, 'strict'))
# Test Thai ID
text2 = 'บัตรประชาชน 1-1234-56789-01-2'
print(scrubber.scrub(text2, 'strict'))
"
```

---

### Task B3: Medical Record Recognizers

**Files**: `backend/app/privacy/medical_recognizers.py` (NEW)

**Context**:
- Hospital Number (HN): typically 5-10 digits
- Patient ID formats vary by hospital

**Requirements**:
1. Create `MedicalRecordRecognizer` class
   - Patterns: `HN:?\s*\d{5,10}`, `ผู้ป่วย\s*#?\d+`, `Patient\s*ID:?\s*\d+`
2. Create `ThaiMedicalLicenseRecognizer` (optional)
   - Pattern: ใบอนุญาตเลขที่ XXXXX
3. Register in PIIScrubber

**Testing**:
```bash
cd backend && uv run python -c "
from app.privacy.pii_scrubber import PIIScrubber
scrubber = PIIScrubber()
text = 'ผู้ป่วย HN: 12345 มีอาการ...'
print(scrubber.scrub(text, 'strict'))
"
```

---

### Task B4: PII Middleware

**Files**: `backend/app/privacy/middleware.py` (NEW)

**Context**:
- `backend/app/middleware/trace.py` - ดู middleware pattern
- `backend/app/routes/chat.py` - integration point

**Requirements**:
1. Create `PIIMiddleware` class หรือ dependency function
2. Auto-scrub user message before processing
3. Store mapping in request context (for potential restore)
4. Pass `pii_level` from project settings or request

**Integration** (ใน chat.py):
```python
# Before sending to LLM
scrubbed_message, pii_mapping = pii_scrubber.scrub(
    data.message,
    level=project.pii_level or "off"
)
```

**Testing**:
```bash
cd backend && uv run python -c "
from app.privacy.middleware import scrub_request
result = scrub_request('คุณสมชาย โทร 081-234-5678', level='strict')
print(result)
"
```

---

### Task B5: Privacy Level Settings

**Files**:
- Update `backend/app/models/project.py`
- Update `backend/app/schemas/project.py`

**Context**:
- `backend/app/models/project.py` - existing Project model
- `backend/app/schemas/project.py` - existing schemas

**Requirements**:
1. Add `pii_level` field to Project model:
   ```python
   pii_level: Mapped[str] = mapped_column(String(20), default="off")  # strict, moderate, off
   ```
2. Add `PIILevel` enum in schemas
3. Update `ProjectCreate`, `ProjectUpdate`, `ProjectResponse` schemas
4. Create migration: `uv run alembic revision --autogenerate -m "add_pii_level_to_project"`

**Testing**:
```bash
cd backend && uv run alembic upgrade head
cd backend && uv run python -c "
from app.models.project import Project
print('pii_level field exists:', hasattr(Project, 'pii_level'))
"
```

---

### Task B6: PII Mapping Storage

**Files**: `backend/app/models/pii_mapping.py` (NEW)

**Context**:
- `backend/app/models/message.py` - ดู model pattern

**Requirements**:
1. Create `PIIMapping` model:
   - id, message_id (FK), mapping (JSON, encrypted), created_at
2. Store mapping when PII is detected
3. Use for potential restoration (admin only)
4. Auto-delete after retention period (e.g., 30 days)

**Note**: Mapping should be encrypted at rest (use Fernet or similar)

**Testing**:
```bash
cd backend && uv run python -c "
from app.models.pii_mapping import PIIMapping
print('PIIMapping model OK')
"
```

---

### Task B7: Encrypted Audit Logging

**Files**: `backend/app/privacy/audit_logger.py` (NEW)

**Context**:
- `backend/app/core/telemetry.py` - ดู logging pattern

**Requirements**:
1. Create `PIIAuditLogger` class
2. Log: timestamp, user_id, project_id, pii_types_detected, count, level
3. Do NOT log actual PII values
4. Store in `pii_audit_logs` table

**Model**:
```python
class PIIAuditLog(Base):
    id: uuid
    user_id: uuid (FK)
    project_id: uuid (FK, nullable)
    message_id: uuid (FK, nullable)
    pii_types: list[str]  # ["PERSON", "PHONE"]
    pii_count: int
    privacy_level: str
    created_at: datetime
```

**Testing**:
```bash
cd backend && uv run python -c "
from app.privacy.audit_logger import PIIAuditLogger
logger = PIIAuditLogger()
print('Audit logger OK')
"
```

---

### Task B8: PII Audit Routes

**Files**: `backend/app/routes/admin/pii.py` (NEW)

**Context**:
- `backend/app/routes/projects.py` - ดู route pattern

**Requirements**:
1. Create admin routes (require admin role):
   - `GET /api/admin/pii/audit` - List audit logs (paginated)
   - `GET /api/admin/pii/stats` - Aggregate stats (count by type, by project)
2. Filter by: date range, project_id, pii_type
3. Return summary, not raw PII

**API Endpoints**:
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/pii/audit | List audit logs |
| GET | /api/admin/pii/stats | PII statistics |

**Testing**:
```bash
TOKEN="admin-jwt-token"
curl -s http://localhost:8000/api/admin/pii/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Frontend Tasks

### Task F1: Privacy Level Selector

**Files**: `frontend/src/lib/components/projects/PrivacyLevelSelector.svelte` (NEW)

**Context**:
- `frontend/src/lib/components/ui/select/` - ดู Select component
- `frontend/src/lib/api/projects.ts` - update project API

**Requirements**:
1. Dropdown with 3 options: Strict, Moderate, Off
2. Show description for each level
3. Props: `value`, `onchange`
4. Use in Project create/edit dialog

**Testing**: `cd frontend && npm run check`

---

### Task F2: PII Indicator Component

**Files**: `frontend/src/lib/components/privacy/PIIIndicator.svelte` (NEW)

**Context**:
- `frontend/src/lib/components/ui/badge/` - ดู Badge

**Requirements**:
1. Show badge when PII was detected in message
2. Display: icon + "PII Protected" or count
3. Tooltip: list of PII types detected
4. Props: `piiTypes: string[]`, `count: number`

**Usage** (in ChatMessage):
```svelte
{#if message.piiDetected}
  <PIIIndicator piiTypes={message.piiTypes} count={message.piiCount} />
{/if}
```

**Testing**: `cd frontend && npm run check`

---

### Task F3: Admin PII Audit Dashboard

**Files**: `frontend/src/routes/(app)/admin/pii/+page.svelte` (NEW)

**Context**:
- `frontend/src/routes/(app)/documents/+page.svelte` - ดู page pattern

**Requirements**:
1. Table of audit logs: timestamp, user, project, PII types, count
2. Filters: date range, project, PII type
3. Pagination
4. Require admin role (redirect if not admin)

**Testing**: Navigate to /admin/pii as admin user

---

### Task F4: PII Stats Visualization

**Files**: `frontend/src/lib/components/admin/PIIStats.svelte` (NEW)

**Context**:
- Consider using simple bars/charts (no heavy chart library needed)

**Requirements**:
1. Show summary stats:
   - Total queries processed
   - Queries with PII detected (count + %)
   - PII by type (bar chart or list)
2. Time range selector (7d, 30d, 90d)
3. Props: `stats: PIIStatsResponse`

**Testing**: `cd frontend && npm run check`

---

## Execution Order

```
Backend:  B1 → B2 → B3 → B4 → B5 → B6 → B7 → B8
Frontend: F1 → F2 → F3 → F4
```

**Dependencies**:
- B2, B3 depend on B1 (PIIScrubber)
- B4 depends on B1-B3 (all recognizers)
- B5 can run parallel with B2-B3
- Frontend depends on Backend B4, B5, B8

---

## API Testing (After Backend Done)

```bash
# 1. Get admin token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' | jq -r '.data.access_token')

# 2. Create project with PII level
curl -s -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mental Health Research", "pii_level": "strict"}' | jq

# 3. Chat with PII (should be scrubbed)
curl -s -X POST http://localhost:8000/api/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "คุณสมชาย โทร 081-234-5678 มีอาการซึมเศร้า",
    "project_id": "PROJECT_ID_HERE"
  }' | jq

# 4. Check audit logs
curl -s http://localhost:8000/api/admin/pii/audit \
  -H "Authorization: Bearer $TOKEN" | jq

# 5. Check stats
curl -s http://localhost:8000/api/admin/pii/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Quick Reference

### Presidio Usage
```python
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine

# Custom recognizer
class ThaiPhoneRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [Pattern("THAI_PHONE", r"0[689]\d-?\d{3}-?\d{4}", 0.85)]
        super().__init__(supported_entity="PHONE_NUMBER", patterns=patterns)
```

### Privacy Level Enum
```python
class PIILevel(str, Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    OFF = "off"
```

### Scrub Result
```python
# Input
text = "คุณสมชาย โทร 081-234-5678"

# Output
scrubbed = "[PERSON] โทร [PHONE]"
mapping = {"[PERSON_0]": "คุณสมชาย", "[PHONE_0]": "081-234-5678"}
```

---

*Last updated: December 2024*
