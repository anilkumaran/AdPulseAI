import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from schemas.ad_schemas import AdRequest, AdResponse, SettingsUpdate
from schemas.sms_schemas import (
    SMSSendRequest, BulkSMSRequest, CampaignSMSRequest,
    SMSResponse, BulkSMSResponse, CampaignSMSResponse
)
from services.auth_service import auth_svc
from services.db_service import db_svc
from services.gemini_service import get_gemini_service, BaseAdService
from services.settings_service import get_settings_service, SettingsService
from services.sns_service import sns_service

app = FastAPI(title="AdPulseAI - Personalization PMI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/token")
async def login(username: str = Form(...), password: str = Form(...)):
    db = db_svc.get_data()
    
    # Find user by username in the users array
    user = None
    for u in db.get("users", []):
        if u.get("username") == username:
            user = u
            break
    
    if not user or not auth_svc.verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    
    token_data = {"sub": username, "role": user["role"]}
    if user.get("merchant_id"):
        token_data["merchant_id"] = user["merchant_id"]
    
    return {
        "access_token": auth_svc.create_token(token_data),
        "role": user["role"],
        "merchant_id": user.get("merchant_id"),
        "name": user.get("name", username),
        "email": user.get("email", "")
    }

@app.post("/api/generate", response_model=AdResponse)
async def generate_personalized_ad(
    request: AdRequest,
    merchant=Depends(auth_svc.get_current_user),
    service: BaseAdService = Depends(get_gemini_service)
):
    db = db_svc.get_data()
    merchant_id = merchant.get("merchant_id")
    
    # Get first customer for this merchant (for demographic context only)
    customers = [c for c in db.get("customers", []) if c.get("merchant_id") == merchant_id]
    
    # Use generic demographic data if no customers
    if customers:
        target_user = customers[0]
        demographics = f"{target_user.get('gender', 'N/A')}, {target_user.get('age', 'N/A')}, {target_user.get('city', 'N/A')}"
        purchase_context = target_user.get('purchase_history', 'General audience')
    else:
        demographics = "General audience, 25-45 years, Urban"
        purchase_context = "General retail customers"

    # PMI Prompt logic - for social media platforms (not personalized to individual)
    pmi_prompt = f"""
    PRODUCT: {request.product_info}. TONE: {request.voice}.
    TARGET AUDIENCE: {demographics}, CONTEXT: {purchase_context}.

    PMI CONSTRAINTS:
    - Create engaging social media content for general audience
    - Use persuasive marketing language
    - Human-like persona (Don't reveal AI).
    - DO NOT use specific customer names - this is for social media platforms

    FORMAT HEADERS:
    FACEBOOK:
    INSTAGRAM:
    TWITTER:
    WHATSAPP:
    TEXTMESSAGE:
    """

    content = service.generate_response(pmi_prompt, request.voice)
    # Log without specific customer name - this is social media content
    db_svc.log_generation(merchant["sub"], request.product_info, "Social Media Campaign", content, merchant_id)
    return AdResponse(status="success", content=content)

@app.get("/api/history")
async def get_history(user=Depends(auth_svc.get_current_user)):
    merchant_id = user.get("merchant_id")
    return db_svc.get_user_history(user["sub"], user["role"], merchant_id)

@app.get("/api/admin/telemetry")
async def get_telemetry(user: dict = Depends(auth_svc.get_current_user)):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return db_svc.get_data()["telemetry"]

@app.get("/api/admin/settings")
def get_settings(user: dict = Depends(auth_svc.get_current_user), svc=Depends(get_settings_service)):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    return svc.get_settings()

@app.post("/api/admin/settings")
def update_settings(data: SettingsUpdate, user: dict = Depends(auth_svc.get_current_user), svc=Depends(get_settings_service)):
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    svc.save_settings(data.dict())
    return {"message": "Settings Updated"}

@app.get("/api/healthcheck")
def healthcheck(): return {"status": "online", "mode": "production", "time": str(datetime.now())}

# ============================================================================
# SMS ENDPOINTS (PMI Paper Implementation)
# ============================================================================

@app.post("/api/sms/send", response_model=SMSResponse)
async def send_single_sms(
    request: SMSSendRequest,
    user=Depends(auth_svc.get_current_user)
):
    """
    Send SMS to a single recipient.
    Simple SMS delivery without personalization.
    """
    result = sns_service.send_sms(request.phone, request.message)
    
    # Log the SMS send
    db_svc.log_sms_send(user["sub"], request.phone, request.message, result["status"])
    
    return SMSResponse(**result)


@app.post("/api/sms/bulk", response_model=BulkSMSResponse)
async def send_bulk_sms(
    request: BulkSMSRequest,
    user=Depends(auth_svc.get_current_user)
):
    """
    Send personalized SMS to multiple recipients.
    Each recipient gets their own personalized message.
    """
    # Prepare recipients for SNS
    recipients = [
        {"phone": r.phone, "message": r.message}
        for r in request.recipients
    ]
    
    result = sns_service.send_bulk_sms(recipients)
    
    # Log bulk send
    db_svc.log_bulk_sms_send(user["sub"], len(recipients), result["sent"], result["failed"])
    
    return BulkSMSResponse(**result)


@app.post("/api/sms/campaign", response_model=CampaignSMSResponse)
async def create_sms_campaign(
    request: CampaignSMSRequest,
    user=Depends(auth_svc.get_current_user),
    service: BaseAdService = Depends(get_gemini_service)
):
    """
    Generate and optionally send personalized SMS campaign.
    Implements the PMI paper's personalized messaging approach:
    - Retrieves customer data (demographics, purchase history)
    - Generates personalized messages using AI
    - Optionally sends via AWS SNS
    """
    db = db_svc.get_data()
    
    # Get customers by IDs
    customers = [c for c in db.get("customers", []) if c["id"] in request.customer_ids]
    
    if not customers:
        raise HTTPException(status_code=404, detail="No customers found with provided IDs")
    
    # Generate personalized messages for each customer
    generated_messages = []
    
    for customer in customers:
        # Build demographics string
        demographics = f"Name={customer['name']}, Gender={customer.get('gender', 'N/A')}, Age={customer.get('age', 'N/A')}, City={customer.get('city', 'N/A')}"
        
        # PMI Prompt Engineering (from the paper)
        pmi_prompt = f"""
        PRODUCT: {request.product_info}. TONE: {request.voice}.
        USER: {demographics}, Purchase History={customer.get('purchase_history', 'No history')}.
        
        PMI CONSTRAINTS (Based on IEEE Paper):
        1. Personalize with customer name: {customer['name']}
        2. Reference purchase history naturally (don't be invasive)
        3. Provide specific reason for recommending this product
        4. Use human-like, conversational tone (Don't reveal AI generation)
        5. Keep it under 160 characters for single SMS
        6. Include emojis if appropriate for the tone
        
        Generate ONLY the SMS text message. No headers, no labels, just the message.
        """
        
        message_content = service.generate_response(pmi_prompt, request.voice)
        
        generated_messages.append({
            "customer_id": customer["id"],
            "name": customer["name"],
            "phone": customer.get("phone", "+91XXXXXXXXXX"),
            "message": message_content.strip()
        })
    
    # Create campaign ID
    campaign_id = f"CAMP{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Send SMS if requested
    messages_sent = None
    if request.send_immediately:
        recipients = [
            {"phone": msg["phone"], "message": msg["message"]}
            for msg in generated_messages
            if msg["phone"] != "+91XXXXXXXXXX"
        ]
        
        if recipients:
            send_result = sns_service.send_bulk_sms(recipients)
            messages_sent = send_result["sent"]
    
    # Log campaign to both sms_campaigns and ad_generation_history
    merchant_id = user.get("merchant_id")
    
    # Log to sms_campaigns table
    db_svc.log_sms_campaign(
        user["sub"],
        campaign_id,
        request.product_info,
        len(generated_messages),
        messages_sent,
        merchant_id
    )
    
    # Also log to ad_generation_history for unified history view
    # Create a summary of the SMS campaign
    sms_summary = f"SMS Campaign: {campaign_id}\n"
    sms_summary += f"Product: {request.product_info}\n"
    sms_summary += f"Customers: {len(customers)}\n"
    sms_summary += f"Messages: {len(generated_messages)}\n\n"
    sms_summary += "Sample Messages:\n"
    for msg in generated_messages[:3]:
        sms_summary += f"- {msg['name']}: {msg['message'][:50]}...\n"
    
    db_svc.log_generation(
        user["sub"],
        request.product_info,
        f"SMS Campaign ({len(customers)} customers)",
        sms_summary,
        merchant_id
    )
    
    return CampaignSMSResponse(
        status="success",
        campaign_id=campaign_id,
        total_customers=len(customers),
        messages_generated=len(generated_messages),
        messages_sent=messages_sent,
        preview=generated_messages[:5]
    )


@app.get("/api/sms/cost-estimate")
async def get_sms_cost_estimate(
    num_messages: int,
    region: str = "India",
    user=Depends(auth_svc.get_current_user)
):
    """
    Estimate SMS campaign costs.
    Helps businesses plan their marketing budget.
    """
    return sns_service.get_sms_cost_estimate(num_messages, region)


@app.get("/api/customers")
async def get_customers(user=Depends(auth_svc.get_current_user)):
    """
    Get list of customers for SMS targeting.
    Filtered by merchant_id for merchant_admin and employee roles.
    """
    db = db_svc.get_data()
    
    if user["role"] == "super_admin":
        # Super admin sees all customers
        return {"customers": db.get("customers", [])}
    else:
        # Merchant admin and employees see only their merchant's customers
        merchant_id = user.get("merchant_id")
        if not merchant_id:
            return {"customers": []}
        customers = [c for c in db.get("customers", []) if c.get("merchant_id") == merchant_id]
        return {"customers": customers}


@app.get("/api/admin/merchants")
async def get_merchants(user=Depends(auth_svc.get_current_user)):
    """Get all merchants (Super Admin only)"""
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    db = db_svc.get_data()
    merchants = db.get("merchants", [])
    users = db.get("users", [])
    
    # Enrich merchant data with admin user info
    for merchant in merchants:
        admin_user = next((u for u in users if u["id"] == merchant["admin_user_id"]), None)
        if admin_user:
            merchant["admin_username"] = admin_user["username"]
            merchant["admin_name"] = admin_user["name"]
    
    return {"merchants": merchants}


@app.post("/api/admin/merchants")
async def create_merchant(
    business_name: str = Form(...),
    industry: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    admin_username: str = Form(...),
    admin_password: str = Form(...),
    admin_name: str = Form(...),
    admin_email: str = Form(...),
    user=Depends(auth_svc.get_current_user)
):
    """Create new merchant (Super Admin only)"""
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin access required")
    
    db = db_svc.get_data()
    
    # Check if username already exists
    if any(u["username"] == admin_username for u in db.get("users", [])):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Generate new IDs
    next_user_id = max([u["id"] for u in db["users"]], default=0) + 1
    next_merchant_num = max([int(m["id"].replace("MERCH", "")) for m in db.get("merchants", [])], default=0) + 1
    merchant_id = f"MERCH{next_merchant_num:03d}"
    
    # Create admin user
    new_user = {
        "id": next_user_id,
        "username": admin_username,
        "password_hash": auth_svc.hash_password(admin_password),
        "role": "merchant_admin",
        "merchant_id": merchant_id,
        "name": admin_name,
        "email": admin_email,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Create merchant
    new_merchant = {
        "id": merchant_id,
        "business_name": business_name,
        "admin_user_id": next_user_id,
        "industry": industry,
        "phone": phone,
        "address": address,
        "is_active": True,
        "subscription_plan": "basic",
        "subscription_expires_at": (datetime.now().replace(year=datetime.now().year + 1)).isoformat(),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    db["users"].append(new_user)
    db["merchants"].append(new_merchant)
    db["telemetry"]["total_merchants"] += 1
    db["telemetry"]["total_users"] += 1
    
    db_svc._write_db(db)
    
    return {"message": "Merchant created successfully", "merchant_id": merchant_id}


@app.get("/api/merchant/employees")
async def get_employees(user=Depends(auth_svc.get_current_user)):
    """Get employees for merchant (Merchant Admin only)"""
    if user["role"] != "merchant_admin":
        raise HTTPException(status_code=403, detail="Merchant Admin access required")
    
    merchant_id = user.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=400, detail="No merchant associated with user")
    
    db = db_svc.get_data()
    employees = [u for u in db.get("users", []) if u.get("merchant_id") == merchant_id and u["role"] == "employee"]
    
    return {"employees": employees}


@app.post("/api/merchant/employees")
async def create_employee(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    user=Depends(auth_svc.get_current_user)
):
    """Create new employee (Merchant Admin only)"""
    if user["role"] != "merchant_admin":
        raise HTTPException(status_code=403, detail="Merchant Admin access required")
    
    merchant_id = user.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=400, detail="No merchant associated with user")
    
    db = db_svc.get_data()
    
    # Check if username already exists
    if any(u["username"] == username for u in db.get("users", [])):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Generate new user ID
    next_user_id = max([u["id"] for u in db["users"]], default=0) + 1
    
    # Create employee user
    new_employee = {
        "id": next_user_id,
        "username": username,
        "password_hash": auth_svc.hash_password(password),
        "role": "employee",
        "merchant_id": merchant_id,
        "name": name,
        "email": email,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    db["users"].append(new_employee)
    db["telemetry"]["total_users"] += 1
    
    db_svc._write_db(db)
    
    return {"message": "Employee created successfully", "user_id": next_user_id}


@app.put("/api/merchant/employees/{employee_id}")
async def update_employee(
    employee_id: int,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    user=Depends(auth_svc.get_current_user)
):
    """Update employee (Merchant Admin only)"""
    if user["role"] != "merchant_admin":
        raise HTTPException(status_code=403, detail="Merchant Admin access required")
    
    merchant_id = user.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=400, detail="No merchant associated with user")
    
    db = db_svc.get_data()
    
    # Find employee
    employee = next((u for u in db["users"] if u["id"] == employee_id and u["role"] == "employee"), None)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Verify employee belongs to this merchant
    if employee.get("merchant_id") != merchant_id:
        raise HTTPException(status_code=403, detail="Cannot modify employee from another merchant")
    
    # Update employee
    employee["name"] = name
    employee["email"] = email
    if password:
        employee["password_hash"] = auth_svc.hash_password(password)
    employee["updated_at"] = datetime.now().isoformat()
    
    db_svc._write_db(db)
    
    return {"message": "Employee updated successfully"}


@app.delete("/api/merchant/employees/{employee_id}")
async def delete_employee(
    employee_id: int,
    user=Depends(auth_svc.get_current_user)
):
    """Delete employee (Merchant Admin only)"""
    if user["role"] != "merchant_admin":
        raise HTTPException(status_code=403, detail="Merchant Admin access required")
    
    merchant_id = user.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=400, detail="No merchant associated with user")
    
    db = db_svc.get_data()
    
    # Find employee
    employee_index = next((i for i, u in enumerate(db["users"]) if u["id"] == employee_id and u["role"] == "employee"), None)
    if employee_index is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    employee = db["users"][employee_index]
    
    # Verify employee belongs to this merchant
    if employee.get("merchant_id") != merchant_id:
        raise HTTPException(status_code=403, detail="Cannot delete employee from another merchant")
    
    # Delete employee
    db["users"].pop(employee_index)
    db["telemetry"]["total_users"] -= 1
    
    db_svc._write_db(db)
    
    return {"message": "Employee deleted successfully"}


@app.post("/api/merchant/customers")
async def create_customer(
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    gender: str = Form("Male"),
    age: int = Form(None),
    city: str = Form(""),
    state: str = Form(""),
    purchase_history: str = Form(""),
    opt_in_sms: bool = Form(True),
    opt_in_whatsapp: bool = Form(True),
    opt_in_email: bool = Form(True),
    user=Depends(auth_svc.get_current_user)
):
    """Create new customer (Merchant Admin only)"""
    if user["role"] != "merchant_admin":
        raise HTTPException(status_code=403, detail="Merchant Admin access required")
    
    merchant_id = user.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=400, detail="No merchant associated with user")
    
    db = db_svc.get_data()
    
    # Generate new customer ID
    existing_ids = [int(c["id"].replace("CUST", "")) for c in db.get("customers", []) if c["id"].startswith("CUST")]
    next_cust_num = max(existing_ids, default=0) + 1
    customer_id = f"CUST{next_cust_num:03d}"
    
    # Create customer
    new_customer = {
        "id": customer_id,
        "merchant_id": merchant_id,
        "name": name,
        "phone": phone,
        "email": email,
        "gender": gender,
        "age": age,
        "city": city,
        "state": state,
        "purchase_history": purchase_history,
        "total_purchases": 0,
        "total_spent": 0,
        "last_purchase_date": None,
        "preferences_categories": [],
        "opt_in_sms": opt_in_sms,
        "opt_in_whatsapp": opt_in_whatsapp,
        "opt_in_email": opt_in_email,
        "is_active": True,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    db["customers"].append(new_customer)
    db["telemetry"]["total_customers"] += 1
    
    db_svc._write_db(db)
    
    return {"message": "Customer created successfully", "customer_id": customer_id}


@app.put("/api/merchant/customers/{customer_id}")
async def update_customer(
    customer_id: str,
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    gender: str = Form("Male"),
    age: int = Form(None),
    city: str = Form(""),
    state: str = Form(""),
    purchase_history: str = Form(""),
    opt_in_sms: bool = Form(True),
    opt_in_whatsapp: bool = Form(True),
    opt_in_email: bool = Form(True),
    user=Depends(auth_svc.get_current_user)
):
    """Update customer (Merchant Admin only)"""
    if user["role"] != "merchant_admin":
        raise HTTPException(status_code=403, detail="Merchant Admin access required")
    
    merchant_id = user.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=400, detail="No merchant associated with user")
    
    db = db_svc.get_data()
    
    # Find customer
    customer = next((c for c in db.get("customers", []) if c["id"] == customer_id), None)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Verify customer belongs to this merchant
    if customer.get("merchant_id") != merchant_id:
        raise HTTPException(status_code=403, detail="Cannot modify customer from another merchant")
    
    # Update customer
    customer["name"] = name
    customer["phone"] = phone
    customer["email"] = email
    customer["gender"] = gender
    customer["age"] = age
    customer["city"] = city
    customer["state"] = state
    customer["purchase_history"] = purchase_history
    customer["opt_in_sms"] = opt_in_sms
    customer["opt_in_whatsapp"] = opt_in_whatsapp
    customer["opt_in_email"] = opt_in_email
    customer["updated_at"] = datetime.now().isoformat()
    
    db_svc._write_db(db)
    
    return {"message": "Customer updated successfully"}


@app.delete("/api/merchant/customers/{customer_id}")
async def delete_customer(
    customer_id: str,
    user=Depends(auth_svc.get_current_user)
):
    """Delete customer (Merchant Admin only)"""
    if user["role"] != "merchant_admin":
        raise HTTPException(status_code=403, detail="Merchant Admin access required")
    
    merchant_id = user.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=400, detail="No merchant associated with user")
    
    db = db_svc.get_data()
    
    # Find customer
    customer_index = next((i for i, c in enumerate(db.get("customers", [])) if c["id"] == customer_id), None)
    if customer_index is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = db["customers"][customer_index]
    
    # Verify customer belongs to this merchant
    if customer.get("merchant_id") != merchant_id:
        raise HTTPException(status_code=403, detail="Cannot delete customer from another merchant")
    
    # Delete customer
    db["customers"].pop(customer_index)
    db["telemetry"]["total_customers"] -= 1
    
    db_svc._write_db(db)
    
    return {"message": "Customer deleted successfully"}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
