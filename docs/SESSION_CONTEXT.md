# AdPulseAI - AI Agent Context Document

## What This Project Is

AdPulseAI is a **multi-channel marketing automation platform** that uses an LLM to generate personalized advertising content across Facebook, Instagram, Twitter, WhatsApp, and SMS. **Prod backend:** `OLLAMA=true` → local Ollama via `client.generate()` (**OLLAMA_MODEL** in `.env`, e.g. `llama2`); otherwise **Gemini** (**gemini-2.5-flash**) with `GEMINI_API_KEY`. Shared prompts live in `services/prompt_service.py`. It extends the IEEE paper "Developing Personalized Marketing Service Using Generative AI" from SMS-only to multi-platform.

**Core Features:**
- AI-powered ad generation for 5 platforms (Facebook, Instagram, Twitter, WhatsApp, SMS)
- Personalized SMS campaigns using customer demographics and purchase history
- 3-tier role-based access: Super Admin (platform owner), Merchant Admin (business owner), Employee (staff)
- Multi-tenant architecture with merchant isolation
- AWS SNS integration for SMS delivery
- Mock mode without any LLM (ENV_MODE=test)

**Tech Stack:**
- Backend: FastAPI (Python 3.10+)
- Frontend: HTML5, CSS3, Vanilla JavaScript, Bootstrap 5
- AI: `OLLAMA=true` + **`OLLAMA_MODEL`** (required); optional `OLLAMA_HOST`; `client.generate()`; else `GEMINI_API_KEY` for **gemini-2.5-flash**; prompts in `services/prompt_service.py`
- SMS: AWS SNS
- Database: JSON file (schemas/db.json)
- Auth: JWT tokens with bcrypt password hashing

---

## Current System State

### Test Credentials
- **Super Admin**: admin / admin123
- **Merchant Admin**: merchant2 / user123 (MERCH002)
- **Employee**: emp2 / user123 (MERCH002)

### Database Contents (schemas/db.json)
- **4 users**: 1 super_admin, 2 merchant_admins, 1 employee
- **2 merchants**: MERCH002 (merchant2), MERCH003 (mer_amazon)
- **4 customers**: All belong to MERCH002 (Sneha Reddy, Vikram Singh, Arjun Mehta Karav, Blah)
- **12 ad_generation_history**: All belong to MERCH002
- **7 sms_campaigns**: Mixed across merchants

### Key Files
- `main.py` - FastAPI backend with all API endpoints
- `static/index.html` - Single-page application (SPA) with all frontend logic
- `schemas/db.json` - JSON database
- `services/prompt_service.py` - All LLM prompt templates and PMI context builders
- `services/llm_service.py` - LLM backends: mock (`ENV_MODE=test`), else Ollama if `OLLAMA=true` (or legacy `LLM_PROVIDER=ollama`), else Gemini
- `services/sns_service.py` - SMS delivery (mock mode available)
- `services/auth_service.py` - JWT authentication
- `services/db_service.py` - Database operations

---

## What Works (Completed Features)

### ✅ Authentication & Authorization
- JWT token-based login with role-based access control
- Password hashing with bcrypt
- Role-specific UI menus (super_admin, merchant_admin, employee)
- Merchant isolation (users only see their own data)

### ✅ Ad Generation
- Multi-platform content generation (Facebook, Instagram, Twitter, WhatsApp, SMS)
- Tabbed interface with copy-to-clipboard buttons
- Edit functionality for WhatsApp and SMS content
- Auto-highlights first platform with content

### ✅ SMS Campaigns (PMI Implementation)
- Personalized SMS generation using customer demographics
- Bulk SMS sending via AWS SNS
- Preview mode (generate without sending)
- Cost estimation
- Customer selection interface

### ✅ CRUD Operations
- **Merchants** (Super Admin): Create, Read, Update, Delete with cascade delete
- **Employees** (Merchant Admin): Create, Read, Update, Delete
- **Customers** (Merchant Admin): Create, Read, Update, Delete
- All operations update dashboard metrics dynamically

### ✅ UI/UX Features
- Notification ribbon system (success/error/info messages)
- Collapsible sidebar with hamburger/chevron icons
- Profile dropdown menu with logout
- Bootstrap modals for delete confirmations and edit forms
- Pagination (10 items per page) for all lists
- Tooltips on all action buttons
- Form validation with HTML5 patterns and constraints
- Indian state dropdown (30+ states)

### ✅ History System
- Unified history showing both ad generations and SMS campaigns
- Filtered by merchant_id and role
- Pagination support
- View historical content by clicking "View" button

---

## Known Issues & Debugging

### Current Issue: Data Not Displaying
**Symptom**: User reports not seeing employees or history data  
**Root Cause**: Browser cache holding old JavaScript  
**Solution**: Hard refresh browser (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)  
**Verification**: Check browser console for logs like "History loaded: 12 items", "Employees loaded: 1 employees"

### Debug Tools Added
- Console logging in `loadFullHistory()`, `loadEmployeesList()`, `loadCustomersList()`
- Browser console (F12) shows data loading status

---

## API Endpoints Reference

### Authentication
- `POST /token` - Login (returns JWT token, role, merchant_id)

### Ad Generation
- `POST /api/generate` - Generate multi-platform ads
- `GET /api/history` - Get user's generation history (filtered by merchant_id)

### SMS Campaigns
- `POST /api/sms/send` - Send single SMS
- `POST /api/sms/bulk` - Send bulk SMS
- `POST /api/sms/campaign` - Generate & send personalized campaign
- `GET /api/sms/cost-estimate` - Estimate SMS costs
- `GET /api/customers` - List customers (filtered by merchant_id)

### Merchant Management (Super Admin)
- `GET /api/admin/merchants` - List all merchants
- `POST /api/admin/merchants` - Create merchant
- `PUT /api/admin/merchants/{merchant_id}` - Update merchant
- `DELETE /api/admin/merchants/{merchant_id}` - Delete merchant (cascades)

### Employee Management (Merchant Admin)
- `GET /api/merchant/employees` - List employees
- `POST /api/merchant/employees` - Create employee
- `PUT /api/merchant/employees/{employee_id}` - Update employee
- `DELETE /api/merchant/employees/{employee_id}` - Delete employee

### Customer Management (Merchant Admin)
- `POST /api/merchant/customers` - Create customer
- `PUT /api/merchant/customers/{customer_id}` - Update customer
- `DELETE /api/merchant/customers/{customer_id}` - Delete customer

### Admin
- `GET /api/admin/telemetry` - System metrics
- `GET /api/admin/settings` - Get settings
- `POST /api/admin/settings` - Update settings

---

## Form Validation Rules

### Phone Numbers
- Pattern: `\+91[0-9]{10}` (exactly 13 characters)
- Example: +919876543210

### Names (Customer/Employee)
- Pattern: `[a-zA-Z\\s]+` (letters and spaces only)
- Length: 2-100 characters

### Usernames
- Pattern: `[a-zA-Z0-9_]+` (alphanumeric and underscore)
- Length: 3-50 characters

### Passwords
- Minimum: 6 characters
- Maximum: 100 characters

### Age
- Range: 1-120

### Product Info
- Length: 10-1000 characters

### States
- Dropdown with 30+ Indian states (Andhra Pradesh, Karnataka, Telangana, etc.)

---

## What to Do Next (For AI Agents)

### If User Reports Missing Data
1. Check browser console (F12) for JavaScript errors
2. Verify console.log output shows data loading
3. Instruct user to hard refresh (Cmd+Shift+R or Ctrl+Shift+R)
4. Verify server is running: `python -m uvicorn main:app --reload --port 8000`
5. Check database integrity: `python3 -c "import json; print(json.load(open('schemas/db.json'))['users'])"`

### If User Wants New Features
1. Check if feature requires backend endpoint (add to `main.py`)
2. Check if feature requires frontend UI (add to `static/index.html`)
3. Check if feature requires database schema changes (`schemas/db.json`)
4. Update this document after completing feature

### If User Reports Bugs
1. Check browser console for JavaScript errors
2. Check server logs for Python exceptions
3. Verify API endpoint returns correct data (use curl or Postman)
4. Check if issue is frontend (UI) or backend (API)

### Common Patterns
- **Add new CRUD entity**: Create endpoints in `main.py`, add UI in `static/index.html`, update `db.json` schema
- **Add new role**: Update `auth_service.py`, add role checks in endpoints, add UI menu items
- **Add new platform**: Update `parseAd()` function, add new tab in UI, update templates in `services/prompt_service.py`

---

## Important Notes for AI Agents

1. **Single-Page Application**: All frontend code is in `static/index.html` (no separate JS files)
2. **No Database Migrations**: Changes to `schemas/db.json` require manual updates
3. **Mock Mode**: Set `ENV_MODE=test` in `.env` to use mock LLM and mock SMS (no Ollama/Gemini/AWS needed)
4. **Phone Format**: Always use `+91XXXXXXXXXX` (13 digits total)
5. **Merchant Isolation**: Always filter by `merchant_id` for merchant_admin and employee roles
6. **Cascade Deletes**: Deleting merchant deletes all associated users and customers
7. **History Logging**: Both ad generation and SMS campaigns log to `ad_generation_history`
8. **Bootstrap 5**: Use Bootstrap classes and components (modals, cards, badges, etc.)
9. **No jQuery**: Pure vanilla JavaScript only
10. **Hard Refresh**: Always instruct users to hard refresh after code changes

---

## Last Updated
2026-02-21 - Added console logging for debugging data display issues
