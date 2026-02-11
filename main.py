import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from schemas.ad_schemas import AdRequest, AdResponse, SettingsUpdate
from services.auth_service import auth_svc
from services.db_service import db_svc
from services.gemini_service import get_gemini_service, BaseAdService
from services.settings_service import get_settings_service, SettingsService

app = FastAPI(title="AdPulseAI Framework")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/healthcheck")
def healthcheck():
    return {"status": "online", "mode": os.getenv("ENV_MODE", "production"), "time": str(datetime.now())}

@app.post("/token")
async def login(username: str = Form(...), password: str = Form(...)):
    db = db_svc.get_data()
    user = db["users"].get(username)
    if not user or not auth_svc.verify_password(password, user["pw"]):
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    token = auth_svc.create_token({"sub": username, "role": user["role"]})
    return {"access_token": token, "role": user["role"]}

@app.post("/api/generate", response_model=AdResponse)
async def generate_ad(request: AdRequest, user=Depends(auth_svc.get_current_user), service=Depends(get_gemini_service)):
    prompt = f"Product: {request.product_info}. Tone: {request.voice}. Output EXACTLY in this format: FACEBOOK: [copy] INSTAGRAM: [copy] TWITTER: [copy] WHATSAPP: [copy]"
    content = service.generate_response(prompt, request.voice)
    db_svc.log_generation(user["sub"], request.product_info, content)
    return AdResponse(status="success", content=content)

@app.get("/api/history")
async def history(user=Depends(auth_svc.get_current_user)):
    return db_svc.get_user_history(user["sub"], user["role"])

@app.get("/api/admin/telemetry")
async def telemetry(user=Depends(auth_svc.get_current_user)):
    if user["role"] != "admin": raise HTTPException(status_code=403)
    return db_svc.get_data()["telemetry"]

@app.get("/api/admin/settings")
def get_settings(user=Depends(auth_svc.get_current_user), svc: SettingsService = Depends(get_settings_service)):
    if user["role"] != "admin": raise HTTPException(status_code=403)
    return svc.get_settings()

@app.post("/api/admin/settings")
def update_settings(data: SettingsUpdate, user=Depends(auth_svc.get_current_user), svc: SettingsService = Depends(get_settings_service)):
    if user["role"] != "admin": raise HTTPException(status_code=403)
    svc.save_settings(data.dict())
    return {"message": "Settings Updated"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")