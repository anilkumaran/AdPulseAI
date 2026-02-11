from pydantic import BaseModel, Field

class AdRequest(BaseModel):
    product_info: str = Field(..., example="A minimalist leather wallet")
    voice: str = Field(default="Professional", description="The tone of the ad, e.g., Professional, Casual, Humorous")


class AdResponse(BaseModel):
    status: str
    content: str

class SettingsUpdate(BaseModel):
    system_persona: str
    default_voice: str