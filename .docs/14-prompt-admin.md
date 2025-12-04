# Admin Panel - RAG Agent Platform

> **Status:** Planning
> **Related:** Phase 7 in todos.md, LiteLLM Features (15-note-feature-litellm.md)

---

## Overview

Admin Panel for managing users, subscriptions, usage, and system settings.

**Key Integrations:**
- LiteLLM: Virtual Keys, Cost Tracking, Rate Limiting
- Stripe: Subscription billing
- PostgreSQL: Users, Plans, Subscriptions

---

## Pricing Plans

| Plan | Price | Tokens/mo | Requests/day | Documents | Models |
|------|-------|-----------|--------------|-----------|--------|
| **Free** | $0 | 50K | 20 | 5 | Basic |
| **Pro** | $19/mo | 500K | 200 | 50 | Standard |
| **Premium** | $49/mo | 2M | 1,000 | 200 | All |
| **Enterprise** | Custom | Unlimited | Unlimited | Unlimited | All + Custom |

**Model Access:**
- Basic: gemini-2.0-flash, llama-3.3-70b
- Standard: + gemini-2.0-pro
- All: + claude-3.5-sonnet, gpt-4-turbo

---

## Implementation Tasks

### [x] Task 1: Database Schema

Create tables for plans and subscriptions.

**Tables:**
- `plans` - pricing plans (name, price, limits, allowed_models)
- `subscriptions` - user subscriptions (user_id, plan_id, status, stripe_id, litellm_key_id)
- `invoices` - payment history

**Reference:** Look at existing models in `backend/app/models/`

---

### [x] Task 2: Plan CRUD API

Backend APIs for plan management.

**Location:** `backend/app/routes/admin/plans.py`

**Endpoints:**
- `GET /api/admin/plans` - List all plans
- `POST /api/admin/plans` - Create plan
- `PUT /api/admin/plans/:id` - Update plan
- `DELETE /api/admin/plans/:id` - Delete plan

**Requirements:**
- Admin-only access (require_admin dependency)
- Return subscriber count per plan
- Sync LiteLLM keys when plan limits change

---

### [x] Task 3: Subscription API

Backend APIs for subscription management.

**Location:** `backend/app/routes/admin/subscriptions.py`

**Endpoints:**
- `GET /api/admin/subscriptions` - List subscriptions
- `POST /api/admin/subscriptions/:id/upgrade` - Upgrade user
- `POST /api/admin/subscriptions/:id/downgrade` - Downgrade user
- `POST /api/admin/subscriptions/:id/cancel` - Cancel subscription

**Requirements:**
- Create LiteLLM Virtual Key when subscription created
- Update LiteLLM key limits on plan change
- Handle Stripe webhook events

---

### [x] Task 4: Admin Dashboard Page

Overview page with key metrics.

**Location:** `frontend/src/routes/(admin)/admin/+page.svelte`

**Widgets:**
- Total users, active today
- Total requests today/month (from LiteLLM)
- Total cost today/month (from LiteLLM)
- Revenue MRR/ARR
- Subscribers by plan (pie chart)
- Usage over time (line chart)

**Reference:** Look at existing dashboard patterns in frontend

---

### [x] Task 5: Plan List Page

Admin page to view and manage plans.

**Location:** `frontend/src/routes/(admin)/admin/plans/+page.svelte`

**Features:**
- Grid of plan cards showing: name, price, limits, subscriber count
- Create plan button -> opens form
- Edit/Delete actions per plan
- Stats: total plans, total subscribers, MRR

---

### [x] Task 6: Plan Form Component

Form for creating/editing plans.

**Location:** `frontend/src/lib/components/admin/PlanForm.svelte`

**Sections:**
1. Basic Info: name, slug, active toggle
2. Pricing: monthly price, annual price (calculate savings %)
3. Usage Limits: tokens, requests, documents, projects, agents, file size
4. Rate Limit: requests per minute
5. Model Access: checkbox list grouped by tier (basic/standard/premium)
6. Features: API access, priority support, team members

**Behaviors:**
- Auto-generate slug from name
- Slider for token limits
- Quick-select buttons for model tiers

---

### [x] Task 7: User List Page

Admin page to view and manage users.

**Location:** `frontend/src/routes/(admin)/admin/users/+page.svelte`

**Columns:**
- Email, Name, Plan (badge), Status, Usage (progress bar), Revenue, Last Active

**Features:**
- Search by email/name
- Filter by plan, status
- Bulk actions: change plan, suspend

**Actions per user:**
- Edit, Change Plan, Suspend, Ban, Delete

---

### [x] Task 8: User Detail Page

Detailed view of single user.

**Location:** `frontend/src/routes/(admin)/admin/users/[id]/+page.svelte`

**Sections:**
- Profile info
- Subscription & billing
- Usage stats + chart
- Recent conversations
- Documents uploaded
- Activity log

---

### [x] Task 9: Usage Analytics Page

View usage and cost analytics.

**Location:** `frontend/src/routes/(admin)/admin/usage/+page.svelte`

**Data from LiteLLM:**
- `/spend/logs` - Detailed logs
- `/spend/users` - Usage by user

**Views:**
- By User: tokens, requests, cost per user
- By Model: usage breakdown by model
- By Plan: cost vs revenue per plan

**Charts:**
- Daily cost trend
- Cost by model (pie)
- Revenue vs Cost (profit margin)

---

### [x] Task 10: LiteLLM Integration Service

Service for managing LiteLLM Virtual Keys.

**Location:** `backend/app/services/litellm_service.py`

**Functions:**
- `create_key_for_user(user_id, plan)` - Create virtual key with plan limits
- `update_key(key_id, plan)` - Update key limits
- `delete_key(key_id)` - Delete key
- `get_usage(user_id)` - Get user's usage

**LiteLLM Key Config:**
- max_budget: based on plan
- tpm_limit: plan.monthly_tokens / 30 / 24 / 60
- rpm_limit: plan.rate_limit_rpm
- models: plan.allowed_models

---

### [x] Task 11: Stripe Integration

Payment processing with Stripe.

**Location:** `backend/app/services/stripe_service.py`

**Functions:**
- Create checkout session
- Handle webhook events (subscription.created, updated, deleted)
- Create customer portal session

**Webhook Events:**
- `customer.subscription.created` -> Create subscription, create LiteLLM key
- `customer.subscription.updated` -> Update subscription, update key
- `customer.subscription.deleted` -> Cancel subscription, delete key
- `invoice.paid` -> Record invoice

---

### [x] Task 12: Quota & Rate Limit UI

Show users their usage and limits.

**Location:** `frontend/src/lib/components/UsageWidget.svelte`

**Display:**
- Tokens used / limit (progress bar)
- Requests today / limit
- Days until reset

**Alerts:**
- 80%: Warning notification
- 95%: Upgrade prompt
- 100%: Blocked modal with upgrade CTA

---

### [x] Task 13: System Monitoring Page

Health and performance monitoring.

**Location:** `frontend/src/routes/(admin)/admin/system/+page.svelte`

**Health Status:**
- LiteLLM Proxy: status, response time, models available
- PostgreSQL: connections, database size, response time
- Redis: memory, connected clients, hit rate

**Features:**
- Auto-refresh every 30 seconds (toggleable)
- Overall system status banner
- Service status cards with detailed metrics
- Connection progress bars
- Error display when services are down

---

### [x] Task 14: Audit Logs Page

Track admin actions.

**Location:** `frontend/src/routes/(admin)/admin/audit/+page.svelte`

**Log Fields:**
- Timestamp, Admin, Action, Target, Details, IP

**Tracked Actions:**
- Plan changes
- User upgrades/downgrades
- Refunds
- Suspend/Ban

**Implementation:**
- Backend:
  - Model: `backend/app/models/audit_log.py` - AuditLog model with AuditAction enum
  - Schema: `backend/app/schemas/admin.py` - AuditLogResponse, AuditLogListResponse, etc.
  - Service: `backend/app/services/audit_log.py` - CRUD operations for audit logs
  - Routes: `backend/app/routes/admin/audit.py` - API endpoints for listing/filtering logs
- Frontend:
  - API: `frontend/src/lib/api/admin.ts` - getAuditLogs, getAuditActionTypes, etc.
  - Page: `frontend/src/routes/(admin)/admin/audit/+page.svelte`
- Migration: `backend/alembic/versions/a0352c1591b2_add_audit_logs_table.py`
- Integrated with: users.py, plans.py admin routes

---

### [x] Task 15: Settings Page

Admin settings configuration.

**Location:** `frontend/src/routes/(admin)/admin/settings/+page.svelte`

**Sections:**
- General: site name, default plan, trial period
- Payment: Stripe keys, currency
- LiteLLM: proxy URL, master key
- Notifications: Slack webhook, email templates

**Implementation:**
- Backend:
  - Model: `backend/app/models/setting.py` - Setting model with SettingCategory enum
  - Schema: `backend/app/schemas/admin.py` - SettingResponse, AllSettingsResponse, GeneralSettings, PaymentSettings, LiteLLMSettings, NotificationSettings
  - Service: `backend/app/services/settings.py` - CRUD operations for settings with secret masking
  - Routes: `backend/app/routes/admin/settings.py` - API endpoints for reading/updating settings
- Frontend:
  - API: `frontend/src/lib/api/admin.ts` - getAllSettings, updateAllSettings, etc.
  - Page: `frontend/src/routes/(admin)/admin/settings/+page.svelte` - Tabbed settings form with secret visibility toggle
- Migration: `backend/alembic/versions/098ce5900338_add_settings_table.py`
- Features:
  - Key-value storage with categories
  - Secret masking (only shows masked values, updates only when not masked)
  - Audit logging on settings changes
  - Initialize default settings endpoint

---

## API Summary

### Admin APIs
```
/api/admin/dashboard       - Dashboard stats
/api/admin/plans           - Plan CRUD
/api/admin/subscriptions   - Subscription management
/api/admin/users           - User management
/api/admin/usage           - Usage analytics
/api/admin/audit           - Audit logs
/api/admin/settings        - Settings
```

### LiteLLM APIs (Proxy)
```
POST /key/generate         - Create virtual key
POST /key/update           - Update key limits
GET  /key/info             - Key details
GET  /spend/logs           - Usage logs
GET  /spend/users          - Usage by user
```

---

## Implementation Order

**Phase 1: Foundation**
1. Task 1: Database Schema
2. Task 2: Plan CRUD API
3. Task 10: LiteLLM Integration Service

**Phase 2: Admin UI**
4. Task 4: Admin Dashboard
5. Task 5: Plan List Page
6. Task 6: Plan Form Component
7. Task 7: User List Page

**Phase 3: Billing**
8. Task 3: Subscription API
9. Task 11: Stripe Integration
10. Task 12: Quota UI

**Phase 4: Monitoring**
11. Task 8: User Detail Page
12. Task 9: Usage Analytics
13. Task 13: System Monitoring
14. Task 14: Audit Logs
15. Task 15: Settings

---

## Notes

- Claude Code can look at existing patterns in codebase
- Follow existing code style (Svelte 5 runes, FastAPI patterns)
- Use shadcn-svelte components
- LiteLLM docs: https://docs.litellm.ai/docs/proxy/virtual_keys

---

*Document created: December 2024*
