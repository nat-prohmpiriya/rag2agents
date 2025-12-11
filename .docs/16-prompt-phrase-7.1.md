# Phase 7.1 - Usage Tracking Complete Implementation

> **Status:** 🚧 In Progress
> **Related:** Section 7.1 in `04-todos.md`

---

## Overview

เอกสารนี้เป็น prompt สำหรับ implement ส่วนที่ยังไม่ครบของ Usage Tracking:

1. **80% Usage Warning** - แจ้งเตือน user เมื่อใช้งานเกิน threshold
2. **Dedicated Usage History Table** - เก็บ usage history แยกจาก messages
3. **Job Status Tracking** - Track background jobs status

---

## Current State (What's Already Done)

| Component | Status | Location |
|-----------|--------|----------|
| Admin Usage Analytics | ✅ Done | `backend/app/services/admin_usage.py` |
| LiteLLM Integration | ✅ Done | `backend/app/services/litellm_keys.py` |
| User Usage Endpoint | ✅ Done | `backend/app/routes/profile.py` - `/api/profile/usage` |
| Admin Usage Dashboard | ✅ Done | `frontend/src/routes/(admin)/admin/usage/+page.svelte` |
| Token tracking in messages | ✅ Done | `backend/app/models/message.py` - `tokens_used` field |

---

## Task 1: 80% Usage Warning Component

### [1.1] Backend - Add Warning Flags to Usage Response

**1. Goal:** Add `is_warning` and `is_blocked` flags to user usage response based on quota percentage

**2. Context:**
- Existing endpoint: `backend/app/routes/profile.py` - `GET /api/profile/usage`
- Existing schema: `backend/app/schemas/stats.py` - `UserUsageResponse`
- Quota limits are based on user tier or subscription plan

**3. Constraints:**
- Use Python type hints (`X | None` syntax)
- Follow existing response pattern with `BaseResponse`
- Warning at 80%, Upgrade prompt at 95%, Blocked at 100%

**4. Definition of Done:**
- [ ] Add `is_warning: bool`, `is_upgrade_suggested: bool`, `is_blocked: bool` to `UserUsageResponse`
- [ ] Calculate flags based on `quota.percentage`
- [ ] Run `uv run ruff check backend/` - no lint errors
- [ ] Test endpoint returns correct flags at different usage levels

**5. Starter Command:**
```bash
claude -p "Update backend/app/schemas/stats.py to add warning flags (is_warning, is_upgrade_suggested, is_blocked) to UserUsageResponse. Then update backend/app/routes/profile.py GET /usage endpoint to calculate these flags based on quota percentage: 80% = warning, 95% = upgrade suggested, 100% = blocked. Follow existing code patterns."
```

---

### [1.2] Frontend - Usage Warning Banner Component

**1. Goal:** Create a reusable warning banner component that shows usage alerts

**2. Context:**
- Existing UI components in `frontend/src/lib/components/ui/`
- shadcn-svelte Alert component available
- Should be shown in app layout when user is near quota

**3. Constraints:**
- Svelte 5 with runes: `$state()`, `$derived()`, `$props()`
- Use shadcn-svelte components (Alert, Progress)
- Use lucide-svelte icons
- No emojis unless requested

**4. Definition of Done:**
- [ ] Create `frontend/src/lib/components/custom/UsageWarningBanner.svelte`
- [ ] Props: `percentage: number`, `isWarning: boolean`, `isUpgradeSuggested: boolean`, `isBlocked: boolean`
- [ ] Show different messages based on state:
  - 80%: "You've used 80% of your monthly quota"
  - 95%: "You're almost at your limit. Upgrade for more tokens."
  - 100%: "You've reached your limit. Upgrade to continue."
- [ ] Include upgrade button linking to `/pricing`
- [ ] Run `npm run check` - no TypeScript errors

**5. Starter Command:**
```bash
claude -p "Create frontend/src/lib/components/custom/UsageWarningBanner.svelte using Svelte 5 runes. Props: percentage, isWarning, isUpgradeSuggested, isBlocked. Use shadcn-svelte Alert component with variants for warning (amber) and destructive (red). Show progress bar with percentage. Include 'Upgrade' button linking to /pricing. Use AlertTriangle icon from lucide-svelte."
```

---

### [1.3] Frontend - Integrate Warning Banner in App Layout

**1. Goal:** Show usage warning banner in the main app layout when user is near/at quota

**2. Context:**
- App layout: `frontend/src/routes/(app)/+layout.svelte`
- Profile API: `frontend/src/lib/api/profile.ts` - `getUsage()`
- User context likely in auth store

**3. Constraints:**
- Fetch usage on mount and cache result
- Only show banner when isWarning, isUpgradeSuggested, or isBlocked is true
- Don't block the UI while loading usage

**4. Definition of Done:**
- [ ] Import and use `UsageWarningBanner` in app layout
- [ ] Fetch usage data on component mount
- [ ] Show banner above main content when threshold exceeded
- [ ] Banner can be dismissed (but reappears on page refresh)
- [ ] Run `npm run check` - no errors

**5. Starter Command:**
```bash
claude -p "Modify frontend/src/routes/(app)/+layout.svelte to fetch user usage via profile API on mount. If isWarning or isUpgradeSuggested or isBlocked is true, show UsageWarningBanner component at top of layout. Use Svelte 5 runes for state management. Handle loading and error states gracefully."
```

---

### [1.4] Frontend - Blocked Modal When Quota Exceeded

**1. Goal:** Show a blocking modal when user tries to send chat but is at 100% quota

**2. Context:**
- Chat component: `frontend/src/lib/components/llm-chat2/LLMChat2.svelte`
- Dialog component from shadcn-svelte
- Should prevent sending message when blocked

**3. Constraints:**
- Modal should be non-dismissible except via Upgrade or Close button
- Check quota before sending message
- Use shadcn Dialog component

**4. Definition of Done:**
- [ ] Create `frontend/src/lib/components/custom/QuotaBlockedModal.svelte`
- [ ] Integrate with chat component - check before send
- [ ] Show modal with: "You've reached your monthly limit" message
- [ ] Buttons: "Upgrade Plan" (link to /pricing), "Close"
- [ ] Run `npm run check` - no errors

**5. Starter Command:**
```bash
claude -p "Create frontend/src/lib/components/custom/QuotaBlockedModal.svelte using shadcn Dialog. Show when user is blocked. Message: 'You've reached your monthly token limit'. Two buttons: 'Upgrade Plan' (href /pricing) and 'Close'. Then modify LLMChat2.svelte to check isBlocked before sending message and show this modal if blocked."
```

---

## Task 2: Dedicated Usage History Table

### [2.1] Backend - Create UsageHistory Model

**1. Goal:** Create a dedicated table to store daily aggregated usage per user

**2. Context:**
- Existing models in `backend/app/models/`
- Use SQLAlchemy async with mapped_column
- Current token tracking is scattered in messages table

**3. Constraints:**
- Follow existing model patterns (see `message.py`, `user.py`)
- Use UUID for id, datetime for timestamps
- Include: user_id, date, tokens_used, requests_count, cost, model breakdown

**4. Definition of Done:**
- [ ] Create `backend/app/models/usage_history.py`
- [ ] Fields: id, user_id, date, tokens_used, requests_count, estimated_cost, model_usage (JSONB), created_at
- [ ] Add model to `backend/app/models/__init__.py`
- [ ] Create alembic migration
- [ ] Run `uv run alembic upgrade head` successfully

**5. Starter Command:**
```bash
claude -p "Create backend/app/models/usage_history.py with UsageHistory model. Fields: id (UUID, primary key), user_id (UUID, foreign key to users), date (Date, unique per user), tokens_used (Integer), requests_count (Integer), estimated_cost (Numeric 10,4), model_usage (JSONB for per-model breakdown), created_at (DateTime). Add unique constraint on (user_id, date). Follow existing model patterns. Then add to models/__init__.py and create alembic migration."
```

---

### [2.2] Backend - Create Usage History Service

**1. Goal:** Create service functions to aggregate and store daily usage

**2. Context:**
- LiteLLM integration: `backend/app/services/litellm_keys.py`
- Admin usage service: `backend/app/services/admin_usage.py`
- Need to sync from LiteLLM daily

**3. Constraints:**
- Use `@traced()` decorator for telemetry
- Async functions with proper type hints
- Upsert logic (update if exists, insert if not)

**4. Definition of Done:**
- [ ] Create `backend/app/services/usage_history.py`
- [ ] Functions:
  - `aggregate_daily_usage(user_id, date)` - Get usage from LiteLLM for specific date
  - `sync_user_usage(user_id)` - Sync all missing days for user
  - `get_user_usage_history(user_id, days)` - Get history from local DB
  - `sync_all_users_usage()` - Batch sync for background job
- [ ] Run `uv run ruff check backend/` - no lint errors

**5. Starter Command:**
```bash
claude -p "Create backend/app/services/usage_history.py with functions for usage history management. Use @traced() decorator. Functions: aggregate_daily_usage(user_id, date) fetches from LiteLLM and upserts to usage_history table, sync_user_usage(user_id) syncs missing days, get_user_usage_history(user_id, days) queries local DB, sync_all_users_usage() for batch processing. Follow patterns from admin_usage.py and litellm_keys.py."
```

---

### [2.3] Backend - API Endpoints for Usage History

**1. Goal:** Add API endpoints to get user's usage history

**2. Context:**
- Profile routes: `backend/app/routes/profile.py`
- Admin routes: `backend/app/routes/admin/usage.py`
- Need both user-facing and admin endpoints

**3. Constraints:**
- User can only see their own history
- Admin can see any user's history
- Return last N days with daily breakdown

**4. Definition of Done:**
- [ ] Add `GET /api/profile/usage/history` - User's own history
- [ ] Add `GET /api/admin/users/{user_id}/usage/history` - Admin view of user
- [ ] Response includes: daily data array, totals summary
- [ ] Run `uv run ruff check backend/` - no lint errors

**5. Starter Command:**
```bash
claude -p "Add GET /api/profile/usage/history endpoint to backend/app/routes/profile.py. Query param: days (default 30). Returns UsageHistoryResponse with daily array and totals. Also add GET /api/admin/users/{user_id}/usage/history to admin routes. Use usage_history service. Follow existing route patterns with BaseResponse."
```

---

### [2.4] Frontend - Usage History Chart Component

**1. Goal:** Create a chart component showing usage over time

**2. Context:**
- Admin usage page has charts: `frontend/src/routes/(admin)/admin/usage/+page.svelte`
- Profile page: `frontend/src/routes/(app)/profile/+page.svelte`
- Can use similar chart approach (div-based bar charts)

**3. Constraints:**
- Svelte 5 runes
- Responsive design
- Show tokens, requests, cost per day

**4. Definition of Done:**
- [ ] Create `frontend/src/lib/components/custom/UsageHistoryChart.svelte`
- [ ] Props: `data: DailyUsage[]`, `metric: 'tokens' | 'requests' | 'cost'`
- [ ] Bar chart showing daily values
- [ ] Tooltip on hover showing exact values
- [ ] Add to profile Usage tab
- [ ] Run `npm run check` - no errors

**5. Starter Command:**
```bash
claude -p "Create frontend/src/lib/components/custom/UsageHistoryChart.svelte using Svelte 5 runes. Props: data (array of {date, tokens, requests, cost}), metric ('tokens'|'requests'|'cost'). Create bar chart with CSS (no external library). Show tooltip on hover. Add tabs to switch between metrics. Then integrate into profile page Usage tab."
```

---

## Task 3: Job Status Tracking

### [3.1] Backend - Create Job Model

**1. Goal:** Create a model to track background job status

**2. Context:**
- Will be used for: usage sync, document processing, etc.
- Need to track: status, progress, errors

**3. Constraints:**
- Follow existing model patterns
- Use enum for status
- Store metadata as JSONB

**4. Definition of Done:**
- [ ] Create `backend/app/models/job.py`
- [ ] Enum: `JobStatus` (pending, running, completed, failed, cancelled)
- [ ] Enum: `JobType` (usage_sync, document_processing, etc.)
- [ ] Fields: id, type, status, progress (0-100), user_id, metadata, error, started_at, completed_at, created_at
- [ ] Add to models/__init__.py
- [ ] Create alembic migration

**5. Starter Command:**
```bash
claude -p "Create backend/app/models/job.py with Job model and enums. JobStatus enum: pending, running, completed, failed, cancelled. JobType enum: usage_sync, document_processing, report_generation. Fields: id (UUID), type (JobType), status (JobStatus), progress (Integer 0-100), user_id (UUID nullable), metadata (JSONB), error (Text nullable), started_at, completed_at, created_at. Add to __init__.py and create migration."
```

---

### [3.2] Backend - Create Job Service

**1. Goal:** Create service functions to manage jobs

**2. Context:**
- Jobs will be created, updated, and queried
- Need to handle concurrent updates safely

**3. Constraints:**
- Use `@traced()` decorator
- Async functions with type hints
- Handle race conditions with select_for_update

**4. Definition of Done:**
- [ ] Create `backend/app/services/job_service.py`
- [ ] Functions:
  - `create_job(type, user_id, metadata)` - Create new job
  - `update_job_status(job_id, status, progress, error)` - Update job
  - `get_job(job_id)` - Get single job
  - `get_user_jobs(user_id, type, status)` - List user's jobs
  - `get_pending_jobs(type)` - Get pending jobs for processing
  - `cleanup_old_jobs(days)` - Delete old completed jobs
- [ ] Run `uv run ruff check backend/` - no lint errors

**5. Starter Command:**
```bash
claude -p "Create backend/app/services/job_service.py with job management functions. Use @traced() decorator. Functions: create_job, update_job_status, get_job, get_user_jobs, get_pending_jobs, cleanup_old_jobs. Follow service patterns from other services. Handle status transitions properly."
```

---

### [3.3] Backend - Job API Endpoints

**1. Goal:** Add API endpoints for job status

**2. Context:**
- Users should see their own jobs
- Admins should see all jobs
- Need SSE for real-time updates (optional)

**3. Constraints:**
- User can only see their own jobs
- Admin can see all jobs
- Support filtering by type and status

**4. Definition of Done:**
- [ ] Add `GET /api/jobs` - User's jobs (with filters)
- [ ] Add `GET /api/jobs/{job_id}` - Single job detail
- [ ] Add `GET /api/admin/jobs` - All jobs for admin
- [ ] Add `DELETE /api/jobs/{job_id}` - Cancel a pending job
- [ ] Run `uv run ruff check backend/` - no lint errors

**5. Starter Command:**
```bash
claude -p "Create backend/app/routes/jobs.py with job endpoints. GET /api/jobs with query params type, status for filtering. GET /api/jobs/{job_id} for single job. DELETE /api/jobs/{job_id} to cancel pending job. Add admin routes GET /api/admin/jobs. Register router in main.py. Follow existing route patterns."
```

---

### [3.4] Backend - Background Job Runner (Usage Sync)

**1. Goal:** Create a background task that syncs usage from LiteLLM daily

**2. Context:**
- FastAPI has background tasks
- Can also use APScheduler or similar
- Should run daily or on-demand

**3. Constraints:**
- Non-blocking execution
- Log errors properly
- Update job status as it progresses

**4. Definition of Done:**
- [ ] Create `backend/app/tasks/usage_sync.py`
- [ ] Function `run_usage_sync_job()`:
  - Create job record
  - Fetch all active users
  - Sync each user's usage
  - Update progress
  - Mark complete or failed
- [ ] Add endpoint to trigger manually: `POST /api/admin/jobs/usage-sync`
- [ ] Run `uv run ruff check backend/` - no lint errors

**5. Starter Command:**
```bash
claude -p "Create backend/app/tasks/usage_sync.py with run_usage_sync_job function. Creates a job, fetches active users, syncs usage for each using usage_history service, updates progress incrementally, handles errors. Add POST /api/admin/jobs/usage-sync endpoint in admin routes to trigger manually. Use FastAPI BackgroundTasks."
```

---

### [3.5] Frontend - Job Status Component

**1. Goal:** Show job status in the admin panel

**2. Context:**
- Admin panel at `/admin`
- Can add a "Jobs" section or page
- Show running, recent completed, failed jobs

**3. Constraints:**
- Svelte 5 runes
- Real-time updates (polling or manual refresh)
- Show progress bar for running jobs

**4. Definition of Done:**
- [ ] Add to AdminSidebar: Jobs menu item
- [ ] Create `frontend/src/routes/(admin)/admin/jobs/+page.svelte`
- [ ] Show job list with: type, status badge, progress, timestamps
- [ ] Filter by type, status
- [ ] Trigger usage sync button
- [ ] Run `npm run check` - no errors

**5. Starter Command:**
```bash
claude -p "Create frontend/src/routes/(admin)/admin/jobs/+page.svelte for admin job management. Show table with columns: type, status (badge), progress (bar), started_at, completed_at, error. Add filters for type and status. Add 'Sync Usage' button to trigger POST /api/admin/jobs/usage-sync. Add Jobs to AdminSidebar navItems. Use Svelte 5 runes."
```

---

## Files Summary

### Backend Files

| Task | Action | File |
|------|--------|------|
| 1.1 | MODIFY | `backend/app/schemas/stats.py` |
| 1.1 | MODIFY | `backend/app/routes/profile.py` |
| 2.1 | CREATE | `backend/app/models/usage_history.py` |
| 2.2 | CREATE | `backend/app/services/usage_history.py` |
| 2.3 | MODIFY | `backend/app/routes/profile.py` |
| 2.3 | MODIFY | `backend/app/routes/admin/users.py` |
| 3.1 | CREATE | `backend/app/models/job.py` |
| 3.2 | CREATE | `backend/app/services/job_service.py` |
| 3.3 | CREATE | `backend/app/routes/jobs.py` |
| 3.4 | CREATE | `backend/app/tasks/usage_sync.py` |

### Frontend Files

| Task | Action | File |
|------|--------|------|
| 1.2 | CREATE | `frontend/src/lib/components/custom/UsageWarningBanner.svelte` |
| 1.3 | MODIFY | `frontend/src/routes/(app)/+layout.svelte` |
| 1.4 | CREATE | `frontend/src/lib/components/custom/QuotaBlockedModal.svelte` |
| 1.4 | MODIFY | `frontend/src/lib/components/llm-chat2/LLMChat2.svelte` |
| 2.4 | CREATE | `frontend/src/lib/components/custom/UsageHistoryChart.svelte` |
| 2.4 | MODIFY | `frontend/src/routes/(app)/profile/+page.svelte` |
| 3.5 | CREATE | `frontend/src/routes/(admin)/admin/jobs/+page.svelte` |
| 3.5 | MODIFY | `frontend/src/lib/components/layout/AdminSidebar.svelte` |

### Migrations

| Task | Migration |
|------|-----------|
| 2.1 | `add_usage_history_table.py` |
| 3.1 | `add_jobs_table.py` |

---

## Task Dependencies

```
Task 1 (Usage Warning):
1.1 Backend flags ──► 1.2 Warning Banner ──► 1.3 Layout Integration
                                         └──► 1.4 Blocked Modal

Task 2 (Usage History):
2.1 Model ──► 2.2 Service ──► 2.3 API Endpoints ──► 2.4 Frontend Chart

Task 3 (Job Tracking):
3.1 Model ──► 3.2 Service ──► 3.3 API Endpoints ──► 3.4 Background Task
                                                └──► 3.5 Frontend Page
```

---

## Recommended Implementation Order

### Phase A: Quick Wins (User-Facing)
1. **Task 1.1** - Add warning flags to usage response
2. **Task 1.2** - Create warning banner component
3. **Task 1.3** - Integrate warning in app layout
4. **Task 1.4** - Create blocked modal for chat

### Phase B: Data Infrastructure
5. **Task 2.1** - Create UsageHistory model + migration
6. **Task 2.2** - Create usage history service
7. **Task 2.3** - Add usage history API endpoints
8. **Task 2.4** - Create usage history chart

### Phase C: Background Jobs
9. **Task 3.1** - Create Job model + migration
10. **Task 3.2** - Create job service
11. **Task 3.3** - Add job API endpoints
12. **Task 3.4** - Create usage sync background task
13. **Task 3.5** - Create admin jobs page

---

## Verification Checklist

After completing all tasks:

- [ ] User sees warning banner at 80% usage
- [ ] User sees upgrade prompt at 95% usage
- [ ] User is blocked from sending messages at 100% usage
- [ ] Usage history is stored in dedicated table
- [ ] User can see usage history chart in profile
- [ ] Admin can see all jobs in admin panel
- [ ] Usage sync job runs successfully
- [ ] All `npm run check` pass
- [ ] All `uv run ruff check backend/` pass
- [ ] All migrations applied successfully

---

*Document created: December 2024*
