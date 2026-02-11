from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from services.gemini_service import get_gemini_service, BaseAdService
from services.settings_service import get_settings_service, SettingsService
from schemas.ad_schemas import AdRequest, AdResponse, SettingsUpdate

app = FastAPI(title="AdPulseAI", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/healthcheck")
async def healthcheck():
    return {"status": "ok"}

################
# User
################
@app.post("/api/generate", response_model=AdResponse)
async def generate_ad(
    request: AdRequest,
    service: BaseAdService = Depends(get_gemini_service)
):
    try:
        content = service.generate_response(request.product_info, request.voice)
        return AdResponse(status="success", content=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


################
# Admin
################
@app.get("/api/admin/settings")
def get_settings(svc: SettingsService = Depends(get_settings_service)):
    return svc.get_settings()

@app.post("/api/admin/settings")
def update_settings(data: SettingsUpdate, svc: SettingsService = Depends(get_settings_service)):
    svc.save_settings(data.dict())
    return {"message": "Settings updated successfully"}



app.mount("/", StaticFiles(directory="static", html=True), name="static")