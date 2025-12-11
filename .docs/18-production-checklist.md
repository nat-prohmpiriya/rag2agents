# Production Checklist: Portfolio ที่เก็บเงินได้จริง

## Executive Summary

| หมวด | สถานะปัจจุบัน | ต้องทำเพิ่ม |
|------|:-------------:|:-----------:|
| Auth System | 70% | Password Reset, Email Verify |
| Payment/Billing | 85% | ✅ มี Stripe แล้ว |
| Email System | 0% | ❌ ยังไม่มีเลย |
| Quota/Usage | 100% | ✅ เสร็จแล้ว |
| Admin Panel | 100% | ✅ เสร็จแล้ว |
| Frontend | 80% | Pricing Page, Reset Flow |
| Security | 75% | Rate Limit, HTTPS |
| Testing | 20% | Unit Tests, CI/CD |
| Deployment | 50% | Production Config |

---

## ทางเลือก: 2 Paths

### Path A: ใช้ Firebase Auth (แนะนำ - เร็วกว่า)

```
เปลี่ยน Auth → Firebase = ได้ฟรี:
✅ Password Reset (Firebase ส่ง email ให้)
✅ Email Verification (Firebase ส่ง email ให้)
✅ Google/GitHub Login (built-in)
✅ Session Management (built-in)

งานที่ต้องทำ: ~1 week
```

### Path B: ทำ Auth เอง + SMTP

```
ต้องทำเอง:
• Password Reset Flow + Token
• Email Verification Flow
• SMTP Integration (Gmail/Resend)
• Email Templates

งานที่ต้องทำ: ~2-3 weeks
```

---

## Checklist แบบละเอียด

### 1. AUTH SYSTEM

#### สิ่งที่มีแล้ว ✅
- [x] JWT Authentication (Access + Refresh token)
- [x] Password hashing (bcrypt)
- [x] User Registration `/auth/register`
- [x] User Login `/auth/login`
- [x] Token Refresh `/auth/refresh`
- [x] Get Current User `/auth/me`
- [x] Change Password `/profile/change-password`
- [x] Delete Account `/profile/delete-account`

#### สิ่งที่ขาด ❌

| Task | Priority | ถ้าใช้ Firebase | ถ้าทำเอง |
|------|:--------:|:---------------:|:--------:|
| Password Reset | 🔴 Critical | ✅ ได้ฟรี | 2-3 days |
| Email Verification | 🟡 High | ✅ ได้ฟรี | 1-2 days |
| OAuth (Google/GitHub) | 🟢 Nice | ✅ ได้ฟรี | 2-3 days |
| 2FA/MFA | 🟢 Nice | ✅ ได้ฟรี | 3-5 days |
| Token Blacklist | 🟢 Nice | ✅ ได้ฟรี | 1 day |

---

### 2. PAYMENT/BILLING

#### สิ่งที่มีแล้ว ✅
- [x] Plan Model (FREE, PRO, ENTERPRISE)
- [x] Subscription Model (status, dates, stripe IDs)
- [x] Invoice Model
- [x] Stripe Service (`stripe_service.py`)
- [x] Checkout Session `/billing/checkout`
- [x] Customer Portal `/billing/portal`
- [x] Get Plans `/billing/plans`
- [x] Webhook Handler `/webhooks/stripe`
  - [x] subscription.created
  - [x] subscription.updated
  - [x] subscription.deleted
  - [x] invoice.paid
  - [x] invoice.payment_failed
- [x] LiteLLM Key Integration (auto-create on subscription)
- [x] Admin: Subscription Management

#### สิ่งที่ขาด ❌

| Task | Priority | เวลา | หมายเหตุ |
|------|:--------:|:----:|----------|
| Pricing Page UI | 🟡 High | 1 day | แสดง plans + checkout button |
| Refund Process | 🟢 Nice | 1 day | Stripe มี API |
| Invoice PDF | 🟢 Nice | 1 day | Stripe มี hosted invoice |
| Proration | 🟢 Nice | - | Stripe จัดการให้ |

---

### 3. EMAIL SYSTEM

#### สิ่งที่มีแล้ว ✅
- [x] Notification Model (database)
- [x] Notification Preferences Model

#### สิ่งที่ขาด ❌

| Task | Priority | ถ้าใช้ Firebase + Stripe | ถ้าทำเอง |
|------|:--------:|:-----------------------:|:--------:|
| Password Reset Email | 🔴 Critical | ✅ Firebase ส่งให้ | 1 day |
| Email Verification | 🟡 High | ✅ Firebase ส่งให้ | 1 day |
| Payment Receipt | 🟡 High | ✅ Stripe ส่งให้ | 1 day |
| Welcome Email | 🟢 Nice | ❌ ต้องทำเอง | 0.5 day |
| Usage Warning | 🟢 Nice | ❌ ต้องทำเอง | 0.5 day |
| SMTP Setup | 🔴 Critical | ❌ ไม่ต้อง (ถ้าไม่ส่ง custom) | 0.5 day |

**ถ้าใช้ Firebase Auth + Stripe Auto Receipt = ไม่ต้องทำ email เลย!**

---

### 4. QUOTA/USAGE ✅ เสร็จแล้ว

- [x] Quota Service (`quota.py`)
- [x] Token Tracking (monthly)
- [x] Document Limit Check
- [x] Project Limit Check
- [x] Agent Limit Check
- [x] Warning Threshold (80%)
- [x] Plan-based Limits
- [x] Monthly Reset
- [x] Frontend Usage Display

---

### 5. ADMIN PANEL ✅ เสร็จแล้ว

- [x] User Management (list, view, edit, suspend)
- [x] Plan Management (CRUD)
- [x] Subscription Management (CRUD, cancel, upgrade)
- [x] Usage Statistics
- [x] System Health
- [x] Audit Logs
- [x] Settings
- [x] Frontend Admin Pages

---

### 6. FRONTEND

#### สิ่งที่มีแล้ว ✅
- [x] Auth Store (Svelte 5 runes)
- [x] Login Page
- [x] Register Page
- [x] Protected Routes
- [x] Token Management
- [x] Profile Page
- [x] Change Password Dialog
- [x] Delete Account Dialog
- [x] Usage Display
- [x] Admin Pages

#### สิ่งที่ขาด ❌

| Task | Priority | เวลา |
|------|:--------:|:----:|
| Pricing Page | 🟡 High | 1 day |
| Forgot Password Page | 🔴 Critical | 0.5 day (ถ้า Firebase = ง่ายมาก) |
| Email Verify Page | 🟡 High | 0.5 day (ถ้า Firebase = ง่ายมาก) |
| Checkout Success Page | 🟢 Nice | 0.5 day |
| Subscription Dashboard | 🟢 Nice | 1 day |

---

### 7. SECURITY

#### สิ่งที่มีแล้ว ✅
- [x] CORS Configuration
- [x] JWT Security (HMAC-SHA256)
- [x] Password Hashing (bcrypt)
- [x] Protected Route Dependencies
- [x] Admin Route Protection
- [x] Error Handling
- [x] SQL Injection Prevention (SQLAlchemy)

#### สิ่งที่ขาด ❌

| Task | Priority | เวลา |
|------|:--------:|:----:|
| Rate Limiting | 🟡 High | 1 day |
| HTTPS Redirect | 🟡 High | 0.5 day (deploy config) |
| Production CORS | 🔴 Critical | 0.5 day |
| CSP Headers | 🟢 Nice | 0.5 day |
| Request Size Limit | 🟢 Nice | 0.5 day |

---

### 8. TESTING

#### สิ่งที่มีแล้ว ✅
- [x] pytest setup
- [x] Test fixtures (conftest.py)
- [x] Basic auth tests
- [x] Health check tests

#### สิ่งที่ขาด ❌

| Task | Priority | เวลา |
|------|:--------:|:----:|
| Service Unit Tests | 🟡 High | 2-3 days |
| API Integration Tests | 🟡 High | 2-3 days |
| Billing Flow Tests | 🟡 High | 1 day |
| Test Coverage (>60%) | 🟢 Nice | ongoing |
| CI/CD Pipeline | 🟡 High | 1 day |

---

### 9. DEPLOYMENT

#### สิ่งที่มีแล้ว ✅
- [x] Docker Compose (dev)
- [x] PostgreSQL + pgvector
- [x] Redis
- [x] LiteLLM Proxy
- [x] Environment Configuration
- [x] Alembic Migrations

#### สิ่งที่ขาด ❌

| Task | Priority | เวลา |
|------|:--------:|:----:|
| Production .env | 🔴 Critical | 0.5 day |
| Secure Secrets | 🔴 Critical | 0.5 day |
| SSL/TLS Setup | 🔴 Critical | 0.5 day (Coolify auto) |
| Domain Setup | 🔴 Critical | 0.5 day |
| Database Backup | 🟡 High | 0.5 day |
| Health Check Endpoints | 🟢 Nice | 0.5 day |

---

### 10. LEGAL

| Task | Priority | เวลา |
|------|:--------:|:----:|
| Terms of Service | 🔴 Critical | 0.5 day (copy/modify) |
| Privacy Policy | 🔴 Critical | 0.5 day (copy/modify) |
| Cookie Policy | 🟢 Nice | 0.5 day |
| Refund Policy | 🟢 Nice | 0.5 day |

---

## สรุป: Minimum Path to Production

### ถ้าใช้ Firebase Auth + Stripe (แนะนำ)

```
┌─────────────────────────────────────────────────────────────────┐
│              MINIMUM PRODUCTION CHECKLIST                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Week 1: Auth + Payment                                         │
│  ──────────────────────────                                     │
│  [ ] Firebase Auth Integration              2-3 days            │
│      • Replace JWT auth with Firebase                           │
│      • Password reset = FREE                                    │
│      • Email verify = FREE                                      │
│  [ ] Pricing Page UI                        1 day               │
│  [ ] Forgot Password Page (Firebase)        0.5 day             │
│                                                                  │
│  Week 2: Deploy + Legal                                         │
│  ──────────────────────────                                     │
│  [ ] Production Environment                 1 day               │
│      • Secure .env                                              │
│      • CORS production domains                                  │
│      • SSL/HTTPS                                                │
│  [ ] Deploy to Hetzner/Coolify              1 day               │
│  [ ] Domain Setup                           0.5 day             │
│  [ ] Terms of Service Page                  0.5 day             │
│  [ ] Privacy Policy Page                    0.5 day             │
│                                                                  │
│  ──────────────────────────────────────────────────────────────│
│  Total: ~2 weeks                                                │
│                                                                  │
│  ได้:                                                           │
│  ✅ Login/Register (Firebase)                                   │
│  ✅ Password Reset (Firebase email)                             │
│  ✅ Payment (Stripe Checkout)                                   │
│  ✅ Receipt (Stripe auto email)                                 │
│  ✅ Subscription Management                                     │
│  ✅ Usage Tracking + Limits                                     │
│  ✅ Admin Panel                                                 │
│  ✅ Legal Pages                                                 │
│                                                                  │
│  ไม่ต้องทำ:                                                     │
│  ❌ Email System (Firebase + Stripe ทำให้)                      │
│  ❌ Password Reset Logic (Firebase ทำให้)                       │
│  ❌ Receipt Generation (Stripe ทำให้)                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### ถ้าไม่อยากเปลี่ยน Auth (ทำเอง)

```
┌─────────────────────────────────────────────────────────────────┐
│              SELF-HOSTED AUTH PATH                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Week 1-2: Email System                                         │
│  ──────────────────────────                                     │
│  [ ] Gmail SMTP Setup                       0.5 day             │
│  [ ] Email Service (send_email)             1 day               │
│  [ ] Email Templates                        1 day               │
│  [ ] Password Reset Flow                    2 days              │
│      • Generate reset token                                     │
│      • Send reset email                                         │
│      • Reset password endpoint                                  │
│      • Frontend reset pages                                     │
│  [ ] Email Verification Flow                1-2 days            │
│                                                                  │
│  Week 2-3: Same as above                                        │
│  [ ] Pricing Page UI                        1 day               │
│  [ ] Production Environment                 1 day               │
│  [ ] Deploy + Domain                        1 day               │
│  [ ] Legal Pages                            1 day               │
│                                                                  │
│  ──────────────────────────────────────────────────────────────│
│  Total: ~3-4 weeks                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Priority Matrix

```
                    IMPACT
                      ↑
           High │  Firebase Auth    Stripe Checkout
                │  (have already)   (have already)
                │
                │  Pricing Page     Production Deploy
                │
                │  Legal Pages      Rate Limiting
                │
            Low │  Tests            OAuth
                │
                └──────────────────────────────────→
                     Easy                    Hard
                              EFFORT
```

---

## Next Action

**คำถาม: อยากไปทาง Firebase Auth หรือทำ Auth เองครับ?**

| Path | เวลา | ความยาก | ได้อะไร |
|------|:----:|:-------:|--------|
| **Firebase** | ~2 weeks | ง่าย | Password reset, verify, OAuth ฟรี |
| **Self-hosted** | ~4 weeks | กลาง | Control เต็มที่ |

---

*Document Created: December 4, 2024*
