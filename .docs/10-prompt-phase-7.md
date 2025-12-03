# Phase 7: Fine-tuning Module (Job Dispatcher) - Implementation Prompts

## Overview

**Goal**: User สามารถสร้าง training jobs, track progress, และใช้ trained models

**Architecture** (Job Dispatcher Pattern):
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Admin Panel    │ ──▶ │  Job Queue      │ ◀── │  GPU Cloud      │
│  (Create Job)   │     │  (PostgreSQL)   │     │  (Colab/RunPod) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  HF Hub         │
                                                │  (Store Model)  │
                                                └─────────────────┘
```

**Key Point**: Training ไม่รันบน Hetzner VPS (ไม่มี GPU) แต่รันบน Colab/Kaggle/RunPod

**Job Types**:
| Type | Base Model | Use Case |
|------|------------|----------|
| embedding | multilingual-e5-base | Custom domain embeddings |
| classifier | bert-base-multilingual | Text classification |
| llm_lora | Llama/Mistral | Custom LLM behavior |

**Job Status**: pending → running → completed/failed

---

## Backend Tasks

### Task B1: FinetuneJob Model

**Files**: `backend/app/models/finetune_job.py` (NEW)

**Context**:
- `backend/app/models/project.py` - ดู model pattern

**Requirements**:
1. Create `FinetuneJob` model:
   - id, user_id (FK), project_id (FK, nullable)
   - job_type: embedding, classifier, llm_lora
   - base_model: HF model name
   - training_data_url: URL to download data
   - output_model: HF Hub path (username/model-name)
   - gpu_provider: colab, kaggle, runpod
   - status: pending, running, completed, failed
   - progress: 0-100
   - error: error message if failed
   - logs_url: W&B or logs URL
   - created_at, started_at, completed_at
2. Add `JobType` and `JobStatus` enums
3. Add `GPUProvider` enum

**Testing**:
```bash
cd backend && uv run python -c "
from app.models.finetune_job import FinetuneJob, JobType, JobStatus
print('FinetuneJob model OK')
"
```

---

### Task B2: FinetuneJob Schemas

**Files**: `backend/app/schemas/finetune.py` (NEW)

**Context**:
- `backend/app/schemas/project.py` - ดู schema pattern

**Requirements**:
1. Create schemas:
   - `FinetuneJobCreate`: job_type, base_model, training_data_url, output_model, gpu_provider
   - `FinetuneJobUpdate`: status, progress, error, logs_url (for worker updates)
   - `FinetuneJobResponse`: full job info
   - `FinetuneJobList`: list of jobs
   - `TrainingDataUpload`: for file upload
2. Add validation rules

**Testing**:
```bash
cd backend && uv run python -c "
from app.schemas.finetune import FinetuneJobCreate, FinetuneJobResponse
print('Finetune schemas OK')
"
```

---

### Task B3: FinetuneJob Service

**Files**: `backend/app/services/finetune.py` (NEW)

**Context**:
- `backend/app/services/document.py` - ดู service pattern

**Requirements**:
1. Create `FinetuneService`:
   - `create_job()` - create new job with status=pending
   - `get_job()`, `list_jobs()` - by user/project
   - `update_job()` - update status/progress (for worker)
   - `get_pending_jobs()` - for worker polling
   - `cancel_job()` - set status=failed
2. Validate base_model against allowed models list
3. Validate output_model format (username/model-name)

**Testing**:
```bash
cd backend && uv run python -c "
from app.services.finetune import finetune_service
print('Finetune service OK')
"
```

---

### Task B4: Training Data Service

**Files**: `backend/app/services/training_data.py` (NEW)

**Context**:
- `backend/app/services/storage.py` - ดู storage pattern

**Requirements**:
1. Create `TrainingDataService`:
   - `upload_data()` - save training data file
   - `validate_data()` - check format (CSV, JSONL)
   - `get_download_url()` - generate signed URL for worker
   - `delete_data()` - cleanup after job complete
2. Supported formats:
   - Embedding: CSV with "text" column
   - Classifier: CSV with "text", "label" columns
   - LLM: JSONL with "instruction", "response"
3. Store in object storage or local filesystem

**Testing**:
```bash
cd backend && uv run python -c "
from app.services.training_data import training_data_service
print('Training data service OK')
"
```

---

### Task B5: FinetuneJob Routes

**Files**: `backend/app/routes/finetune.py` (NEW)

**Context**:
- `backend/app/routes/documents.py` - ดู route pattern

**Requirements**:
1. Create routes:
   - `POST /api/finetune/jobs` - Create job
   - `GET /api/finetune/jobs` - List user's jobs
   - `GET /api/finetune/jobs/{id}` - Get job details
   - `PATCH /api/finetune/jobs/{id}` - Update job (worker)
   - `DELETE /api/finetune/jobs/{id}` - Cancel job
   - `GET /api/finetune/jobs/pending` - Get pending jobs (worker)
   - `POST /api/finetune/upload` - Upload training data
2. Add worker authentication (separate API key)
3. Register in `main.py`

**API Endpoints**:
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/finetune/jobs | Create job | User |
| GET | /api/finetune/jobs | List jobs | User |
| GET | /api/finetune/jobs/{id} | Get job | User |
| PATCH | /api/finetune/jobs/{id} | Update job | Worker |
| DELETE | /api/finetune/jobs/{id} | Cancel job | User |
| GET | /api/finetune/jobs/pending | Get pending | Worker |
| POST | /api/finetune/upload | Upload data | User |

**Testing**:
```bash
TOKEN="your-jwt-token"
# Create job
curl -s -X POST http://localhost:8000/api/finetune/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "embedding",
    "base_model": "intfloat/multilingual-e5-base",
    "training_data_url": "https://storage.../data.csv",
    "output_model": "myuser/custom-embedding",
    "gpu_provider": "colab"
  }' | jq

# List jobs
curl -s http://localhost:8000/api/finetune/jobs \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

### Task B6: Model Registry

**Files**: `backend/app/services/model_registry.py` (NEW)

**Context**:
- Track deployed models for use in platform

**Requirements**:
1. Create `ModelRegistry` service:
   - `register_model()` - add completed model to registry
   - `list_models()` - list available models by type
   - `get_model()` - get model info
   - `deploy_model()` - mark model as ready for use
   - `delete_model()` - remove from registry
2. Store: hf_path, type, status, deployed_at
3. Integration with LiteLLM config (for LLM models)

**Testing**:
```bash
cd backend && uv run python -c "
from app.services.model_registry import model_registry
print('Model registry OK')
"
```

---

### Task B7: Colab Worker Template

**Files**: `training/worker.py`, `training/colab_notebook.ipynb` (NEW)

**Context**:
- ไฟล์นี้รันบน Colab ไม่ใช่บน server

**Requirements**:
1. Create `worker.py`:
   - Poll for pending jobs
   - Download training data
   - Train based on job_type
   - Push model to HF Hub
   - Update job status
2. Create `colab_notebook.ipynb`:
   - Install dependencies
   - Login to HF Hub, W&B
   - Run worker loop
3. Support job types:
   - `train_embedding()` - sentence-transformers
   - `train_classifier()` - transformers Trainer
   - `train_lora()` - peft + trl

**Worker Loop**:
```python
while True:
    job = api.get_pending_job()
    if job:
        api.update_status(job.id, "running")
        try:
            train(job)
            api.update_status(job.id, "completed")
        except Exception as e:
            api.update_status(job.id, "failed", error=str(e))
    sleep(60)
```

**Testing**: Run in Colab with test job

---

## Frontend Tasks

### Task F1: Finetune API Client

**Files**: `frontend/src/lib/api/finetune.ts` (NEW)

**Context**:
- `frontend/src/lib/api/documents.ts` - ดู pattern

**Requirements**:
1. Create types: `FinetuneJob`, `JobType`, `JobStatus`, `GPUProvider`
2. Create functions:
   - `createJob()`, `listJobs()`, `getJob()`
   - `cancelJob()`, `uploadTrainingData()`
3. Export in `index.ts`

**Testing**: `cd frontend && npm run check`

---

### Task F2: Job Creation Form

**Files**: `frontend/src/lib/components/finetune/JobCreateForm.svelte` (NEW)

**Context**:
- `frontend/src/lib/components/ui/select/` - ดู Select
- `frontend/src/lib/components/ui/input/` - ดู Input

**Requirements**:
1. Form fields:
   - Job type dropdown (embedding, classifier, llm_lora)
   - Base model dropdown (filtered by type)
   - Training data upload
   - Output model name input
   - GPU provider dropdown
2. Validation before submit
3. Props: `onSubmit: (job) => void`

**Testing**: `cd frontend && npm run check`

---

### Task F3: Job Status Card

**Files**: `frontend/src/lib/components/finetune/JobStatusCard.svelte` (NEW)

**Context**:
- `frontend/src/lib/components/ui/card/` - ดู Card
- `frontend/src/lib/components/ui/badge/` - ดู Badge

**Requirements**:
1. Display: job type, base model, status badge, progress bar
2. Status colors: pending=yellow, running=blue, completed=green, failed=red
3. Show: created time, duration, error message if failed
4. Action buttons: View logs, Cancel (if pending/running), Deploy (if completed)
5. Props: `job: FinetuneJob`

**Testing**: `cd frontend && npm run check`

---

### Task F4: Finetune Dashboard

**Files**: `frontend/src/routes/(app)/finetune/+page.svelte` (NEW)

**Context**:
- `frontend/src/routes/(app)/documents/+page.svelte` - ดู page pattern

**Requirements**:
1. Header with "Create Job" button
2. Job list with JobStatusCard components
3. Filter by: status, job_type
4. Auto-refresh running jobs (poll every 10s)
5. Empty state when no jobs

**Testing**: Navigate to /finetune

---

### Task F5: Job Detail Page

**Files**: `frontend/src/routes/(app)/finetune/[id]/+page.svelte` (NEW)

**Context**:
- Show full job details and logs

**Requirements**:
1. Full job info: all fields
2. Progress visualization
3. Logs viewer (if available)
4. Training metrics (from W&B)
5. Deploy button for completed jobs

**Testing**: Navigate to /finetune/{job_id}

---

### Task F6: Model Registry Page

**Files**: `frontend/src/routes/(app)/models/+page.svelte` (NEW)

**Context**:
- List deployed models

**Requirements**:
1. List available models by type
2. Show: model name, type, HF path, deployed date
3. Use model button (copy path or integrate)
4. Delete model button

**Testing**: Navigate to /models

---

## Execution Order

```
Backend:  B1 → B2 → B3 → B4 → B5 → B6 → B7
Frontend: F1 → F2 → F3 → F4 → F5 → F6
```

**Dependencies**:
- B3 depends on B1-B2
- B5 depends on B3-B4
- B7 can run in parallel (separate Colab)
- Frontend depends on Backend B5

---

## API Testing (After Backend Done)

```bash
TOKEN="your-jwt-token"
WORKER_KEY="worker-api-key"

# 1. Upload training data
curl -s -X POST http://localhost:8000/api/finetune/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@training_data.csv" | jq

# 2. Create job
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/finetune/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_type": "embedding",
    "base_model": "intfloat/multilingual-e5-base",
    "training_data_url": "https://storage.../data.csv",
    "output_model": "myuser/custom-e5-hr",
    "gpu_provider": "colab"
  }')
JOB_ID=$(echo $JOB_RESPONSE | jq -r '.data.id')
echo "Job ID: $JOB_ID"

# 3. List jobs
curl -s http://localhost:8000/api/finetune/jobs \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Get pending jobs (worker)
curl -s http://localhost:8000/api/finetune/jobs/pending \
  -H "Authorization: Bearer $WORKER_KEY" | jq

# 5. Update job status (worker)
curl -s -X PATCH "http://localhost:8000/api/finetune/jobs/$JOB_ID" \
  -H "Authorization: Bearer $WORKER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "running", "progress": 50}' | jq

# 6. Complete job (worker)
curl -s -X PATCH "http://localhost:8000/api/finetune/jobs/$JOB_ID" \
  -H "Authorization: Bearer $WORKER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed", "progress": 100}' | jq
```

---

## Quick Reference

### Job Types & Base Models
```python
ALLOWED_MODELS = {
    "embedding": [
        "intfloat/multilingual-e5-base",
        "intfloat/multilingual-e5-large",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ],
    "classifier": [
        "bert-base-multilingual-cased",
        "xlm-roberta-base",
    ],
    "llm_lora": [
        "meta-llama/Llama-2-7b-hf",
        "mistralai/Mistral-7B-v0.1",
    ],
}
```

### Training Data Formats
```
# Embedding (CSV)
text
"This is sentence 1"
"This is sentence 2"

# Classifier (CSV)
text,label
"Positive review",positive
"Negative review",negative

# LLM (JSONL)
{"instruction": "Translate to Thai", "input": "Hello", "output": "สวัสดี"}
```

### Worker Authentication
```python
# Separate API key for worker
WORKER_API_KEY = os.getenv("FINETUNE_WORKER_KEY")

# Verify in route
def verify_worker_key(key: str = Header(...)):
    if key != WORKER_API_KEY:
        raise HTTPException(403, "Invalid worker key")
```

---

*Last updated: December 2024*
