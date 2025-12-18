# ISSUE 
- [] fix ui chat with documents page
- [x] fix cancle haderbar
- [x] หน้า login remember username last login, password สามารถ show/hide ได้
- [x] ปรับปรุง ปุ่มทุกปปุ้ม มี cursor pointer when hover
- [-] sidebar menu เมื่อ collapse แล้ว ให้มีชื่อเมนูแสดงเใต้ icon เมื่อ hover sub-menu
- [-] B auth firebase
- [x] B payement strip
    - [x] 1. สร้าง Pricing page (หน้าเลือก plan)
    - [x] 2. สร้าง Billing page (จัดการ subscription ของ user)
    - [x] 3. สร้างหน้า success/cancel หลัง checkout
    - [x] 4. สร้าง API client $lib/api/billing.ts
    - [] 5. ตั้งค่า Stripe config (env variables)
- [] C testing
    สิ่งที่ผมช่วยเขียน Tests ได้

    | หมวด        | Tests   | หมายเหตุ|
    |-------------------------------------------------------------------------------------|
    | Unit Tests  | Service functions, Utils, Helpers       | Logic ล้วนๆ ไม่ต้อง mock มาก |
    | API Tests   | Endpoints, Request/Response validation  | ใช้ TestClient               |
    | Model Tests | SQLAlchemy models, Pydantic schemas     | Validation, relationships    |
    | Auth Tests  | JWT creation/validation, password hashing| ไม่ต้องต่อ external          |
    | Quota Tests | Limit checking, Usage calculation       | Pure logic                   |
    | Admin Tests | CRUD operations| Database operations    |❌ สิ่งที่ต้องเทสเองหรือทำ Manual

    | หมวด                   | เหตุผล
            |
    |------------------------|-------------------------------
    -------|
    | Stripe Webhooks        | ต้องใช้ Stripe CLI + real events
        |
    | LiteLLM Integration    | ต้องมี API key จริง / mock ซับซ้อน
        |
    | Firebase Auth (ถ้าใช้) | ต้อง setup Firebase test project
        |
    | E2E Frontend           | ต้องรัน browser
    (Playwright/Cypress) |
    | Real Payment Flow      | ต้องใช้ Stripe test mode +
    browser   |
    | Email Delivery         | ต้อง verify ว่าส่งจริง
        |
- [x] A landing page for explain product and service
- [] C deployment github action -> coolify + vps
- [] D improve feature agent, tools,
- [] D improve feature chat with document
- [] F i18n support multi language(thai, eng, jp)
- [] E data-testid สำหรับ E2E testing
- [] F ai gen image


  1. โชว์ RAG Pipeline - Document chunking, embedding, retrieval
  2. โชว์ Multi-model - Switch ระหว่าง Gemini models (Pro/Flash)
  3. โชว์ AI Agent - Custom tools, function calling
  4. โชว์ Analytics - Token usage, model comparison
  5. ai gen image