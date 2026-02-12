# AdPulseAI - Session Context

## Project Overview
AdPulseAI is a multi-channel marketing platform that extends the IEEE paper "Developing Personalized Marketing Service Using Generative AI" from SMS-only to multi-platform (Facebook, Instagram, Twitter, WhatsApp, SMS). It implements a 3-tier role-based access control system with Super Admin, Merchant Admin, and Employee roles.

## Current Status: ACTIVE DEVELOPMENT

### Last Updated: 2026-02-13

---

## COMPLETED TASKS

### TASK 1: Initial Project Setup and IEEE Paper Analysis
- **STATUS**: ✅ DONE
- **DETAILS**: 
  - Fetched and analyzed IEEE paper on "Developing Personalized Marketing Service Using Generative AI"
  - Compared paper with `abstract.md` - project extends PMI from SMS-only to multi-channel
  - Added comparison table to `README.md` showing evolution from research to production
- **FILES**: `README.md`, `abstract.md`, `bin/paper_overview.txt`

### TASK 2: SMS Feature Implementation
- **STATUS**: ✅ DONE
- **DETAILS**:
  - Created SMS delivery system with AWS SNS integration
  - Added 5 SMS endpoints: send, bulk, campaign, cost-estimate, customers
  - Implemented mock mode for testing (ENV_MODE=test)
  - SMS campaigns now log to both `sms_campaigns` and `ad_generation_history` for unified history
- **FILES**: `services/sns_service.py`, `schemas/sms_schemas.py`, `main.py`, `services/db_service.py`

### TASK 3: 3-Tier Role-Based Access Control System
- **STATUS**: ✅ DONE
- **DETAILS**:
  - Implemented 3 roles: Super Admin (platform owner), Merchant Admin (business owner), Employee (staff)
  - Updated database schema with users, merchants, customers separation
  - Removed merchant1, kept only merchant2 (MERCH002) with id=2
  - Updated phone numbers to pattern: +91XXXXXXXXXX
  - Added collapsible sidebar (Jira-style horizontal toggle button)
  - Moved logout to profile dropdown menu
  - Created role-specific UI menus and access controls
- **FILES**: `db.json`, `main.py`, `services/db_service.py`, `services/auth_service.py`, `static/index.html`

### TASK 4: CRUD Operations for Merchants, Employees, and Customers
- **STATUS**: ✅ DONE
- **DETAILS**:
  - Added API endpoints for creating merchants (Super Admin)
  - Added API endpoints for creating/updating/deleting employees (Merchant Admin)
  - Added API endpoints for creating/updating/deleting customers (Merchant Admin)
  - Implemented forms with proper validation
  - Auto-generates IDs (MERCH003, CUST004, etc.)
- **FILES**: `main.py`, `static/index.html`

### TASK 5: UI/UX Improvements - Notifications, Copy Buttons, Edit Features
- **STATUS**: ✅ DONE
- **DETAILS**:
  - Replaced all alert() calls with notification ribbon system (showError, showSuccess, showInfo)
  - Added copy buttons to all social media tabs
  - Simplified edit buttons to icon-only (pencil, checkmark, X)
  - Fixed ad generation to show "Social Media Campaign" instead of specific customer names
  - Added edit/delete capabilities for customers and employees
  - Fixed SMS campaign checkbox errors with proper event handling
  - Implemented double-click confirmation for delete operations (button turns red)
- **FILES**: `static/index.html`, `main.py`, `services/db_service.py`

### TASK 6: Pagination Implementation
- **STATUS**: ✅ DONE
- **DETAILS**:
  - Implemented pagination for customers list (10 items per page)
  - Implemented pagination for employees list (10 items per page)
  - Implemented pagination for merchants list (10 items per page)
  - Implemented pagination for history list (10 items per page)
  - Updated `log_generation` in `db_service.py` to use `prompt_preview` with first 10 chars
  - Added focus management - cursor returns to input field on errors
  - Cleaned up old history entries in `db.json`
- **FILES**: `static/index.html`, `services/db_service.py`, `db.json`

### TASK 7: History System Overhaul
- **STATUS**: ✅ DONE
- **DETAILS**:
  - Removed "Recent History" section from sidebar completely
  - Created dedicated "History" section with full pagination (10 items per page)
  - History now shows user-specific data (filtered by merchant_id and role on backend)
  - Added `loadFullHistory()` function with pagination support
  - SMS campaigns now appear in unified history alongside ad generations
  - Updated `main.py` to log SMS campaigns to `ad_generation_history` table
  - Removed `fetchHistory()` function and all its calls
  - History displays product name (first 10 chars) and type badge (Ad Generation or SMS Campaign)
- **FILES**: `static/index.html`, `main.py`

### TASK 8: Sidebar Toggle Button Improvements
- **STATUS**: ✅ DONE
- **DETAILS**:
  - First iteration: Removed text, made icon-only, changed to blue color for better visibility
  - Second iteration: Made less visible - changed to dark gray (#333) background with subtle border
  - Added hover effect (lighter gray #444)
  - Icon size increased to 1.2rem
  - Added title attribute for accessibility
- **FILES**: `static/index.html`

### TASK 9: Admin Dashboard and "All Activity" Section
- **STATUS**: ✅ DONE
- **DETAILS**:
  - Removed "All Activity" section from admin dashboard
  - Removed "All Activity" menu item from super admin navigation
  - Updated `loadAdminDashboard()` to only load telemetry and settings
  - Dashboard now shows: Total API Calls, SMS Sent, Total Campaigns, Active Users
  - System Settings section with persona and voice configuration
- **FILES**: `static/index.html`

### TASK 10: Merchant Edit/Delete Options
- **STATUS**: ✅ DONE (placeholder implementation)
- **DETAILS**:
  - Added edit and delete buttons to merchant cards
  - Added `editMerchant()` function (placeholder - shows "coming soon" message)
  - Added `deleteMerchant()` function (placeholder - shows "coming soon" message)
  - Buttons styled consistently with employees/customers sections
  - Full implementation would require additional backend endpoints
- **FILES**: `static/index.html`

### TASK 11: Comprehensive Form Validation
- **STATUS**: ✅ DONE
- **DETAILS**:
  - **COMPLETED**:
    - Phone validation: pattern="\+91[0-9]{10}", maxlength="13" for all phone inputs
    - Customer name: minlength="2", maxlength="100"
    - Customer city/state: maxlength="50"
    - Customer purchase history: maxlength="500"
    - Employee username: minlength="3", maxlength="50", pattern="[a-zA-Z0-9_]+"
    - Employee password: minlength="6", maxlength="100"
    - Employee name: minlength="2", maxlength="100"
    - Merchant business name: minlength="2", maxlength="100"
    - Merchant industry: maxlength="50"
    - Merchant address: maxlength="200"
    - Merchant admin username: minlength="3", maxlength="50", pattern="[a-zA-Z0-9_]+"
    - Merchant admin password: minlength="6", maxlength="100"
    - Merchant admin name: minlength="2", maxlength="100"
    - Product info textareas: minlength="10", maxlength="1000"
    - Edit customer form validation added
    - Edit employee form validation added (name, email, password fields)
  - **NOTE**: Email validation exists (type="email") but no additional pattern constraints
- **FILES**: `static/index.html`

---

## IN-PROGRESS TASKS

### TASK 12: Mock Data Generation (20+ Records)
- **STATUS**: 🔄 IN PROGRESS (PAUSED)
- **DETAILS**:
  - User requested at least 20 records for each entity type (customers, employees, merchants, history)
  - **COMPLETED SO FAR**:
    - Users: 11 records (1 super_admin, 3 merchant_admins, 7 employees)
    - Merchants: 3 records (MERCH002, MERCH003, MERCH004)
    - Fixed merchant phone numbers to proper format (+91XXXXXXXXXX)
  - **REMAINING WORK**:
    - Add 17+ more customers (currently 3, need 20+) with varied merchant_ids
    - Add 17+ more merchants (currently 3, need 20+) with admin users
    - Add 14+ more ad_generation_history entries (currently 6, need 20+)
    - Add 17+ more SMS campaigns (currently 3, need 20+)
    - Update telemetry counts to match new totals
  - **REQUIREMENTS**:
    - Mock data should only be visible when ENV_MODE=test
    - Phone numbers must follow +91XXXXXXXXXX pattern (13 digits total)
    - Realistic data: varied names, cities, ages, purchase histories
    - Customers distributed across all merchants
    - Employees distributed across all merchants
- **NEXT STEPS**:
  - Complete db.json rewrite with all 20+ records for each entity
  - Update telemetry to reflect new counts
- **FILES**: `db.json`

---

## PENDING TASKS

None currently identified.

---

## TECHNICAL SPECIFICATIONS

### Database Schema (db.json)
- **users**: id, username, password_hash, role, merchant_id, name, email, is_active, created_at, updated_at
- **merchants**: id, business_name, admin_user_id, industry, phone, address, is_active, subscription_plan, subscription_expires_at, created_at, updated_at
- **customers**: id, merchant_id, name, phone, email, gender, age, city, state, purchase_history, total_purchases, total_spent, last_purchase_date, preferences_categories, opt_in_sms, opt_in_whatsapp, opt_in_email, is_active, created_at, updated_at
- **ad_generation_history**: id, user_id, merchant_id, target_customer, product_info, prompt_preview, full_content, created_at, timestamp
- **sms_history**: id, user_id, phone, message_preview, status, created_at, timestamp
- **sms_campaigns**: id, campaign_id, user_id, merchant_id, type, product, total_generated, messages_sent, created_at, timestamp
- **system_settings**: id, system_persona, default_voice, updated_at
- **telemetry**: total_api_calls, total_sms_sent, total_campaigns, total_merchants, total_customers, total_users, last_api_call_timestamp, last_updated

### Roles & Permissions
1. **Super Admin**: Platform owner, manages all merchants, views all data
2. **Merchant Admin**: Business owner, manages employees and customers for their merchant
3. **Employee**: Staff member, can generate ads and SMS campaigns for their merchant

### API Endpoints
- **Auth**: POST /token
- **Ad Generation**: POST /api/generate, GET /api/history
- **SMS**: POST /api/sms/send, POST /api/sms/bulk, POST /api/sms/campaign, GET /api/sms/cost-estimate
- **Customers**: GET /api/customers, POST /api/merchant/customers, PUT /api/merchant/customers/{id}, DELETE /api/merchant/customers/{id}
- **Employees**: GET /api/merchant/employees, POST /api/merchant/employees, PUT /api/merchant/employees/{id}, DELETE /api/merchant/employees/{id}
- **Merchants**: GET /api/admin/merchants, POST /api/admin/merchants
- **Admin**: GET /api/admin/telemetry, GET /api/admin/settings, POST /api/admin/settings

### Default Credentials
- **Super Admin**: admin/admin123
- **Merchant Admin**: merchant2/user123
- **Employee**: emp2/user123

### Phone Number Format
- Pattern: +91XXXXXXXXXX (13 digits total)
- Example: +919000000001

### Environment Modes
- **test**: Mock mode, no API keys needed, uses mock data
- **production**: Real mode, requires API keys

---

## USER CORRECTIONS AND INSTRUCTIONS

1. Use test mode (ENV_MODE=test) for development - no API keys needed
2. Default credentials: admin/admin123 (Super Admin), merchant2/user123 (Merchant Admin), emp2/user123 (Employee)
3. Phone numbers must follow pattern: +91XXXXXXXXXX (13 digits total)
4. NEVER use alert() or confirm() - always use notification ribbon system
5. History should show first 10 characters of product name, not customer names
6. Ad generation is for social media platforms, not individual customers
7. Cursor must return to input field when validation errors occur
8. Implement pagination wherever lists can grow large (10 items per page)
9. Delete operations require double-click confirmation (button turns red on first click)
10. Sidebar toggle button should be less visible than primary actions
11. Remove redundant sections (Recent History in sidebar, All Activity in admin dashboard)
12. Add comprehensive validation to ALL form fields, not just phone numbers
13. Add at least 20 mock records for each entity type (customers, employees, merchants, history)
14. Mock data should only be visible when ENV_MODE=test

---

## KNOWN ISSUES

None currently identified.

---

## NEXT SESSION PRIORITIES

1. **HIGH PRIORITY**: Complete mock data generation (20+ records for each entity)
   - Add 17+ more customers with realistic data
   - Add 17+ more merchants with admin users
   - Add 14+ more history entries
   - Add 17+ more SMS campaigns
   - Update telemetry counts

2. **MEDIUM PRIORITY**: Test all features with mock data
   - Verify pagination works correctly with 20+ records
   - Test role-based access control with multiple merchants
   - Verify history filtering by merchant_id

3. **LOW PRIORITY**: Performance optimization
   - Consider database indexing for large datasets
   - Optimize frontend rendering for large lists

---

## FILES MODIFIED IN THIS SESSION

1. `db.json` - Started adding mock data (users and merchants updated, customers in progress)
2. `static/index.html` - All form validations completed, edit employee form validation added
3. `SESSION_CONTEXT.md` - This file (updated with current status)

---

## DEVELOPMENT NOTES

- The project uses FastAPI for backend and vanilla JavaScript for frontend
- No framework dependencies for frontend (Bootstrap for styling only)
- All state management is client-side using localStorage
- JWT tokens for authentication
- Mock mode allows testing without external API dependencies
- Pagination implemented client-side for simplicity
- Form validation uses HTML5 native validation attributes
