# Notification System - RAG Agent Platform

> **Status:** 🔲 Not Started
> **Related:** Phase 7 in todos.md, Admin Settings (NotificationSettings)

---

## Overview

In-app notification system สำหรับแจ้งเตือน user เกี่ยวกับ events ต่างๆ เช่น quota usage, subscription changes, document processing, และ system alerts

**Key Features:**
- In-app notifications (bell icon + dropdown)
- Notification preferences per user
- Email notifications (optional, via SMTP settings)
- Real-time updates (optional, via WebSocket)

**Existing Infrastructure:**
- `NotificationSettings` in admin settings (SMTP config)
- `svelte-sonner` for toast notifications (already integrated)
- `AuditLog` model as reference pattern

---

## Notification Types

| Category | Type | Description | Priority |
|----------|------|-------------|----------|
| **Billing** | `quota_warning` | Usage reaches 80% | high |
| **Billing** | `quota_exceeded` | Usage reaches 100% | critical |
| **Billing** | `subscription_expiring` | Subscription expires in 7 days | high |
| **Billing** | `subscription_renewed` | Subscription renewed successfully | low |
| **Billing** | `payment_failed` | Payment failed | critical |
| **Billing** | `payment_success` | Payment successful | low |
| **Document** | `document_processed` | Document upload/indexing complete | medium |
| **Document** | `document_failed` | Document processing failed | high |
| **System** | `system_maintenance` | Scheduled maintenance | medium |
| **System** | `system_announcement` | General announcement | low |
| **Account** | `welcome` | Welcome new user | low |
| **Account** | `password_changed` | Password changed | medium |

---

## Database Schema

### Notification Table
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,           -- notification type enum
    category VARCHAR(20) NOT NULL,        -- billing, document, system, account
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(10) DEFAULT 'low',   -- low, medium, high, critical
    read_at TIMESTAMP WITH TIME ZONE,
    action_url VARCHAR(500),              -- optional link
    metadata JSONB,                       -- additional data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE   -- auto-delete after expiry
);

CREATE INDEX ix_notifications_user_unread ON notifications(user_id, read_at) WHERE read_at IS NULL;
CREATE INDEX ix_notifications_user_created ON notifications(user_id, created_at DESC);
```

### NotificationPreference Table
```sql
CREATE TABLE notification_preferences (
    id UUID PRIMARY KEY,
    user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN DEFAULT true,
    in_app_enabled BOOLEAN DEFAULT true,
    -- Per-category settings (JSONB for flexibility)
    category_settings JSONB DEFAULT '{
        "billing": {"email": true, "in_app": true},
        "document": {"email": false, "in_app": true},
        "system": {"email": true, "in_app": true},
        "account": {"email": true, "in_app": true}
    }',
    quiet_hours_start TIME,              -- e.g., 22:00
    quiet_hours_end TIME,                -- e.g., 08:00
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Implementation Tasks

### Phase 1: Backend Foundation

---

### [x] [NOTI-01] Notification Model & Migration

**1. Goal:** สร้าง database model สำหรับ notifications และ notification_preferences

**2. Context:**
- Reference: `backend/app/models/audit_log.py` for model pattern
- Reference: `backend/app/models/subscription.py` for enum usage
- Schema design: See Database Schema section above

**3. Constraints:**
- Tech: SQLAlchemy async, PostgreSQL, UUID primary keys
- Pattern: Use `TimestampMixin`, proper type hints (`X | None` syntax)
- Indexes: Add indexes for common queries (user_id, read_at, created_at)
- DO NOT: Create unnecessary relationships at this stage

**4. Definition of Done:**
- [ ] `backend/app/models/notification.py` created with `Notification` model
- [ ] `backend/app/models/notification_preference.py` created with `NotificationPreference` model
- [ ] Enums created: `NotificationType`, `NotificationCategory`, `NotificationPriority`
- [ ] Models exported in `backend/app/models/__init__.py`
- [ ] Alembic migration created and runs successfully
- [ ] `uv run alembic upgrade head` passes

**5. Starter Command:**
```bash
claude -p "Create Notification and NotificationPreference models following the pattern in backend/app/models/audit_log.py. See .docs/16-prompt-noti.md for schema details. Create alembic migration after."
```

---

### [x] [NOTI-02] Notification Schemas

**1. Goal:** สร้าง Pydantic schemas สำหรับ notification API requests/responses

**2. Context:**
- Reference: `backend/app/schemas/admin.py` for schema patterns
- Reference: `backend/app/schemas/base.py` for BaseResponse
- Models: `backend/app/models/notification.py`

**3. Constraints:**
- Tech: Pydantic v2 with `ConfigDict(from_attributes=True)`
- Pattern: Separate Create/Update/Response schemas
- DO NOT: Include user object in response (only user_id)

**4. Definition of Done:**
- [ ] `backend/app/schemas/notification.py` created with:
  - `NotificationCreate` - for creating notifications
  - `NotificationResponse` - for API responses
  - `NotificationListResponse` - paginated list
  - `NotificationPreferenceUpdate` - for updating preferences
  - `NotificationPreferenceResponse` - for reading preferences
  - `UnreadCountResponse` - for badge count
- [ ] Schemas imported in `backend/app/schemas/__init__.py`
- [ ] Type hints complete

**5. Starter Command:**
```bash
claude -p "Create Pydantic schemas for notifications in backend/app/schemas/notification.py. Follow patterns from backend/app/schemas/admin.py. See .docs/16-prompt-noti.md for field requirements."
```

---

### [x] [NOTI-03] Notification Service

**1. Goal:** สร้าง service layer สำหรับ notification business logic

**2. Context:**
- Reference: `backend/app/services/audit_log.py` for service pattern
- Models: `backend/app/models/notification.py`
- Schemas: `backend/app/schemas/notification.py`

**3. Constraints:**
- Tech: Async SQLAlchemy, `@traced()` decorator
- Pattern: All DB operations in service layer
- Soft delete: Use `expires_at` instead of hard delete for cleanup
- DO NOT: Send emails in this task (handled by separate email service)

**4. Definition of Done:**
- [ ] `backend/app/services/notification.py` created with:
  - `create_notification(db, user_id, type, title, message, ...)` - create single notification
  - `create_bulk_notifications(db, user_ids, ...)` - create for multiple users
  - `get_notifications(db, user_id, unread_only, limit, offset)` - list with pagination
  - `get_unread_count(db, user_id)` - count for badge
  - `mark_as_read(db, notification_id, user_id)` - mark single as read
  - `mark_all_as_read(db, user_id)` - mark all as read
  - `delete_notification(db, notification_id, user_id)` - soft delete
  - `get_preferences(db, user_id)` - get user preferences
  - `update_preferences(db, user_id, data)` - update preferences
  - `cleanup_expired(db)` - delete expired notifications
- [ ] Service uses `@traced()` decorator
- [ ] Proper error handling

**5. Starter Command:**
```bash
claude -p "Create notification service in backend/app/services/notification.py following patterns from backend/app/services/audit_log.py. See .docs/16-prompt-noti.md for function requirements."
```

---

### [x] [NOTI-04] Notification API Routes

**1. Goal:** สร้าง REST API endpoints สำหรับ notifications

**2. Context:**
- Reference: `backend/app/routes/admin/audit.py` for route patterns
- Service: `backend/app/services/notification.py`
- Schemas: `backend/app/schemas/notification.py`

**3. Constraints:**
- Tech: FastAPI, BaseResponse wrapper, `get_context()` for trace_id
- Auth: All endpoints require authentication (`get_current_user`)
- Pattern: Users can only access their own notifications
- DO NOT: Create admin endpoints in this task (separate task)

**4. Definition of Done:**
- [ ] `backend/app/routes/notifications.py` created with:
  - `GET /api/notifications` - list notifications (paginated, filter by unread)
  - `GET /api/notifications/unread-count` - get unread count for badge
  - `POST /api/notifications/{id}/read` - mark as read
  - `POST /api/notifications/read-all` - mark all as read
  - `DELETE /api/notifications/{id}` - delete notification
  - `GET /api/notifications/preferences` - get preferences
  - `PUT /api/notifications/preferences` - update preferences
- [ ] Routes registered in `backend/app/main.py`
- [ ] All responses wrapped in `BaseResponse`
- [ ] Proper HTTP status codes

**5. Starter Command:**
```bash
claude -p "Create notification API routes in backend/app/routes/notifications.py following patterns from backend/app/routes/admin/audit.py. See .docs/16-prompt-noti.md for endpoints."
```

---

### Phase 2: Frontend Implementation

---

### [x] [NOTI-05] Notification API Client

**1. Goal:** สร้าง TypeScript API client สำหรับ notification endpoints

**2. Context:**
- Reference: `frontend/src/lib/api/admin.ts` for API client pattern
- Base client: `frontend/src/lib/api/client.ts`
- API endpoints: See NOTI-04

**3. Constraints:**
- Tech: TypeScript, fetch-based client
- Pattern: Match existing API client patterns
- Types: Create TypeScript interfaces matching backend schemas
- DO NOT: Implement caching in this task

**4. Definition of Done:**
- [ ] `frontend/src/lib/api/notifications.ts` created with:
  - TypeScript interfaces: `Notification`, `NotificationPreference`, etc.
  - `getNotifications(params)` - list notifications
  - `getUnreadCount()` - get badge count
  - `markAsRead(id)` - mark single as read
  - `markAllAsRead()` - mark all as read
  - `deleteNotification(id)` - delete
  - `getPreferences()` - get preferences
  - `updatePreferences(data)` - update preferences
- [ ] Exported in `frontend/src/lib/api/index.ts`
- [ ] Error handling consistent with other API clients

**5. Starter Command:**
```bash
claude -p "Create notification API client in frontend/src/lib/api/notifications.ts following patterns from frontend/src/lib/api/admin.ts. See .docs/16-prompt-noti.md for endpoints."
```

---

### [x] [NOTI-06] Notification Store

**1. Goal:** สร้าง Svelte store สำหรับจัดการ notification state

**2. Context:**
- Reference: `frontend/src/lib/stores/auth.svelte.ts` for store pattern
- API client: `frontend/src/lib/api/notifications.ts`

**3. Constraints:**
- Tech: Svelte 5 runes (`$state()`, `$derived()`)
- Pattern: Singleton store pattern
- Polling: Implement polling for unread count (every 60 seconds)
- DO NOT: Implement WebSocket in this task

**4. Definition of Done:**
- [ ] `frontend/src/lib/stores/notifications.svelte.ts` created with:
  - State: `notifications`, `unreadCount`, `loading`, `preferences`
  - Actions: `fetchNotifications()`, `fetchUnreadCount()`, `markAsRead()`, `markAllAsRead()`, `deleteNotification()`, `fetchPreferences()`, `updatePreferences()`
  - Derived: `hasUnread` computed from unreadCount
  - Auto-polling: Start/stop polling on mount/unmount
- [ ] Exported in `frontend/src/lib/stores/index.ts`
- [ ] Proper loading states

**5. Starter Command:**
```bash
claude -p "Create notification store in frontend/src/lib/stores/notifications.svelte.ts using Svelte 5 runes. Follow patterns from frontend/src/lib/stores/auth.svelte.ts. See .docs/16-prompt-noti.md for requirements."
```

---

### [x] [NOTI-07] Notification Bell Component

**1. Goal:** สร้าง notification bell icon พร้อม dropdown สำหรับ header

**2. Context:**
- Reference: `frontend/src/lib/components/ui/` for UI components
- Store: `frontend/src/lib/stores/notifications.svelte.ts`
- Location: จะใช้ใน header/navbar

**3. Constraints:**
- Tech: Svelte 5, shadcn-svelte components
- UI: Bell icon with badge count, dropdown with notification list
- Pattern: Use `Popover` or `DropdownMenu` from shadcn
- DO NOT: Create full notification page in this task

**4. Definition of Done:**
- [ ] `frontend/src/lib/components/notifications/NotificationBell.svelte` created with:
  - Bell icon (use lucide-svelte `Bell` icon)
  - Badge showing unread count (hide if 0)
  - Dropdown/Popover on click
  - List of recent notifications (max 5-10)
  - "Mark all as read" action
  - "View all" link to notification page
  - Loading state
  - Empty state
- [ ] `frontend/src/lib/components/notifications/NotificationItem.svelte` for individual items
- [ ] Responsive design
- [ ] Exported in `frontend/src/lib/components/notifications/index.ts`

**5. Starter Command:**
```bash
claude -p "Create NotificationBell component in frontend/src/lib/components/notifications/. Use shadcn-svelte Popover, lucide-svelte Bell icon. See .docs/16-prompt-noti.md for requirements."
```

---

### [x] [NOTI-08] Integrate Bell into Header

**1. Goal:** เพิ่ม NotificationBell component เข้าไปใน app header

**2. Context:**
- Component: `frontend/src/lib/components/notifications/NotificationBell.svelte`
- Header location: Look for existing header/navbar component
- Store: Initialize notification polling on app load

**3. Constraints:**
- Show only when user is logged in
- Position: Right side of header, before user menu
- DO NOT: Break existing header functionality

**4. Definition of Done:**
- [ ] NotificationBell added to header component
- [ ] Shows only when authenticated
- [ ] Notification store initialized on app load
- [ ] Polling starts when user logs in, stops on logout
- [ ] No visual regression in header

**5. Starter Command:**
```bash
claude -p "Integrate NotificationBell into the app header. Find the header component, add the bell icon next to user menu. Initialize notification store on auth. See .docs/16-prompt-noti.md"
```

---

### [x] [NOTI-09] Notifications Page

**1. Goal:** สร้างหน้า notifications สำหรับดู notifications ทั้งหมด

**2. Context:**
- Store: `frontend/src/lib/stores/notifications.svelte.ts`
- Route: `/notifications` หรือ `/settings/notifications`
- Reference: Look at existing list pages for patterns

**3. Constraints:**
- Tech: Svelte 5, shadcn-svelte
- Features: Infinite scroll or pagination, filter by read/unread
- DO NOT: Include preference settings in this page (separate task)

**4. Definition of Done:**
- [ ] `frontend/src/routes/(app)/notifications/+page.svelte` created
- [ ] List all notifications with pagination/infinite scroll
- [ ] Filter: All / Unread only
- [ ] Mark as read on click
- [ ] Mark all as read button
- [ ] Delete individual notifications
- [ ] Empty state
- [ ] Proper loading states

**5. Starter Command:**
```bash
claude -p "Create notifications page at frontend/src/routes/(app)/notifications/+page.svelte. Show all notifications with pagination and read/unread filter. See .docs/16-prompt-noti.md"
```

---

### [NOTI-10] Notification Preferences Page

**1. Goal:** สร้างหน้า settings สำหรับ notification preferences

**2. Context:**
- Store: `frontend/src/lib/stores/notifications.svelte.ts`
- Route: `/settings/notifications` หรือ add to existing settings page
- Reference: `frontend/src/routes/(admin)/admin/settings/+page.svelte`

**3. Constraints:**
- Tech: Svelte 5, shadcn-svelte form components
- Features: Toggle per category, quiet hours
- DO NOT: Make it too complex initially

**4. Definition of Done:**
- [ ] Notification preferences UI created (new page or section in settings)
- [ ] Toggle: Enable/disable email notifications
- [ ] Toggle: Enable/disable in-app notifications
- [ ] Per-category settings (billing, document, system, account)
- [ ] Optional: Quiet hours settings
- [ ] Save button with loading state
- [ ] Success toast on save

**5. Starter Command:**
```bash
claude -p "Create notification preferences UI. Can be a new page or add to existing settings. Allow toggling email/in-app per category. See .docs/16-prompt-noti.md"
```

---

### Phase 3: Backend Integration

---

### [x] [NOTI-11] Notification Triggers - Billing

**1. Goal:** เพิ่ม notification triggers สำหรับ billing events

**2. Context:**
- Service: `backend/app/services/notification.py`
- Billing service: `backend/app/services/stripe_service.py`
- Subscription service: `backend/app/services/subscription.py`
- Quota service: `backend/app/services/quota.py`

**3. Constraints:**
- Trigger notifications after successful DB operations
- Check user preferences before creating notification
- DO NOT: Block main operation if notification fails (use try/except)

**4. Definition of Done:**
- [ ] Quota warning notification at 80% usage
- [ ] Quota exceeded notification at 100%
- [ ] Subscription renewal notification
- [ ] Payment success notification
- [ ] Payment failed notification
- [ ] Subscription expiring notification (need scheduled job - can skip if complex)

**5. Starter Command:**
```bash
claude -p "Add notification triggers to billing-related services. Send quota_warning at 80%, quota_exceeded at 100%, payment_success/failed on Stripe webhooks. See .docs/16-prompt-noti.md"
```

---

### [] [NOTI-12] Notification Triggers - Documents

**1. Goal:** เพิ่ม notification triggers สำหรับ document processing events

**2. Context:**
- Service: `backend/app/services/notification.py`
- Document service: `backend/app/services/document.py`
- Document processor: `backend/app/services/document_processor.py`

**3. Constraints:**
- Notify after document processing completes (success or failure)
- Include document name in notification
- DO NOT: Notify for every small operation

**4. Definition of Done:**
- [ ] `document_processed` notification when indexing completes
- [ ] `document_failed` notification when processing fails
- [ ] Include document name and error message (if failed)
- [ ] Link to document in notification

**5. Starter Command:**
```bash
claude -p "Add notification triggers to document processing. Notify user when document processing completes or fails. See .docs/16-prompt-noti.md"
```

---

### [x] [NOTI-13] Admin Notification API

**1. Goal:** สร้าง admin API สำหรับ broadcast notifications

**2. Context:**
- Reference: `backend/app/routes/admin/` for admin route patterns
- Service: `backend/app/services/notification.py`

**3. Constraints:**
- Admin only access
- Allow targeting: all users, specific plan, specific users
- DO NOT: Allow sending to external emails

**4. Definition of Done:**
- [ ] `backend/app/routes/admin/notifications.py` created with:
  - `GET /api/admin/notifications/stats` - notification statistics
  - `POST /api/admin/notifications/broadcast` - send to all users
  - `POST /api/admin/notifications/send` - send to specific users
- [ ] Audit log entries for admin notifications
- [ ] Rate limiting consideration (don't spam users)

**5. Starter Command:**
```bash
claude -p "Create admin notification routes for broadcasting system announcements. Allow sending to all users or specific groups. See .docs/16-prompt-noti.md"
```

---

### Phase 4: Optional Enhancements

---

### [] [NOTI-14] Email Notification Service

**1. Goal:** สร้าง email service สำหรับส่ง email notifications

**2. Context:**
- Settings: `NotificationSettings` in admin settings (SMTP config)
- Service: `backend/app/services/notification.py`

**3. Constraints:**
- Use SMTP settings from admin settings
- Check user email preferences before sending
- Queue emails instead of sending synchronously (optional)
- DO NOT: Send emails without user consent

**4. Definition of Done:**
- [ ] `backend/app/services/email.py` created with:
  - `send_email(to, subject, body)` - basic send
  - `send_notification_email(user, notification)` - send notification as email
- [ ] Email templates for each notification type
- [ ] Respect user preferences (email_enabled)
- [ ] Error handling for SMTP failures
- [ ] Integration with notification service

**5. Starter Command:**
```bash
claude -p "Create email notification service using SMTP settings from admin config. Send notification emails based on user preferences. See .docs/16-prompt-noti.md"
```

---

### [] [NOTI-15] WebSocket Real-time Notifications

**1. Goal:** เพิ่ม real-time notifications ผ่าน WebSocket

**2. Context:**
- Existing WebSocket: Check if chat already uses WebSocket
- Store: `frontend/src/lib/stores/notifications.svelte.ts`

**3. Constraints:**
- Optional enhancement - polling is acceptable fallback
- Reuse existing WebSocket connection if available
- DO NOT: Create complex pub/sub system

**4. Definition of Done:**
- [ ] Backend WebSocket endpoint for notifications
- [ ] Frontend connects to WebSocket on auth
- [ ] Push new notifications in real-time
- [ ] Update unread count immediately
- [ ] Fallback to polling if WebSocket fails

**5. Starter Command:**
```bash
claude -p "Add WebSocket support for real-time notifications. Push new notifications immediately instead of polling. See .docs/16-prompt-noti.md"
```

---

### [] [NOTI-16] Notification Cleanup Job

**1. Goal:** สร้าง background job สำหรับ cleanup expired notifications

**2. Context:**
- Service: `backend/app/services/notification.py` (cleanup_expired function)
- Consider: APScheduler, Celery, or simple cron

**3. Constraints:**
- Run daily or weekly
- Delete notifications older than 30 days (configurable)
- Delete read notifications older than 7 days (optional)
- DO NOT: Delete unread critical notifications

**4. Definition of Done:**
- [ ] Background job configured to run periodically
- [ ] Cleanup expired notifications based on `expires_at`
- [ ] Optional: Cleanup old read notifications
- [ ] Logging for cleanup operations

**5. Starter Command:**
```bash
claude -p "Create background job for cleaning up expired notifications. Run daily, delete notifications past expires_at. See .docs/16-prompt-noti.md"
```

---

## API Summary

### User APIs
```
GET    /api/notifications                - List notifications
GET    /api/notifications/unread-count   - Get unread count
POST   /api/notifications/{id}/read      - Mark as read
POST   /api/notifications/read-all       - Mark all as read
DELETE /api/notifications/{id}           - Delete notification
GET    /api/notifications/preferences    - Get preferences
PUT    /api/notifications/preferences    - Update preferences
```

### Admin APIs
```
GET    /api/admin/notifications/stats     - Notification statistics
POST   /api/admin/notifications/broadcast - Send to all users
POST   /api/admin/notifications/send      - Send to specific users
```

---

## Implementation Order

**Phase 1: Backend Foundation** (Required)
1. NOTI-01: Model & Migration
2. NOTI-02: Schemas
3. NOTI-03: Service
4. NOTI-04: API Routes

**Phase 2: Frontend Implementation** (Required)
5. NOTI-05: API Client
6. NOTI-06: Store
7. NOTI-07: Bell Component
8. NOTI-08: Header Integration
9. NOTI-09: Notifications Page
10. NOTI-10: Preferences Page

**Phase 3: Backend Integration** (Important)
11. NOTI-11: Billing Triggers
12. NOTI-12: Document Triggers
13. NOTI-13: Admin API

**Phase 4: Optional Enhancements**
14. NOTI-14: Email Service
15. NOTI-15: WebSocket
16. NOTI-16: Cleanup Job

---

## Notes

- Follow existing code patterns in the codebase
- Use shadcn-svelte components for UI
- All backend functions should have `@traced()` decorator
- Wrap all API responses in `BaseResponse`
- Test each phase before moving to next

---

*Document created: December 2024*
