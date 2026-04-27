from pydantic import BaseModel, Field, validator
from typing import List, Optional

class SMSRecipient(BaseModel):
    """Single SMS recipient with personalized message"""
    phone: str = Field(..., example="+919876543210")
    name: str = Field(..., example="Rahul")
    message: str = Field(..., example="Hi Rahul! Check out our new product...")
    
    @validator('phone')
    def validate_phone(cls, v):
        # Remove spaces and dashes
        v = v.replace(' ', '').replace('-', '')
        
        # Add +91 if not present and starts with digit
        if not v.startswith('+'):
            if v.startswith('91'):
                v = '+' + v
            elif v.startswith('0'):
                v = '+91' + v[1:]
            else:
                v = '+91' + v
        
        # Basic validation
        if len(v) < 10:
            raise ValueError('Phone number too short')
        
        return v


class SMSSendRequest(BaseModel):
    """Request to send SMS to a single recipient"""
    phone: str = Field(..., example="+919876543210")
    message: str = Field(..., example="Hi! Check out our new product...")


class BulkSMSRequest(BaseModel):
    """Request to send personalized SMS to multiple recipients"""
    recipients: List[SMSRecipient]


class CampaignSMSRequest(BaseModel):
    """
    Request to generate and send personalized SMS campaign.
    Implements PMI paper's personalized messaging approach.
    """
    product_info: str = Field(..., example="Wireless Earbuds Pro - ₹2,999")
    voice: str = Field(default="Professional", example="Professional")
    customer_ids: List[str] = Field(..., example=["CUST001", "CUST002"])
    send_immediately: bool = Field(default=False, description="Send SMS immediately or just generate")


class SMSResponse(BaseModel):
    """Response for single SMS send"""
    status: str
    message: str
    phone: Optional[str] = None
    message_id: Optional[str] = None


class BulkSMSResponse(BaseModel):
    """Response for bulk SMS send"""
    status: str
    total: int
    sent: int
    failed: int
    results: List[dict]


class CampaignSMSResponse(BaseModel):
    """Response for campaign SMS generation/send"""
    status: str
    campaign_id: str
    total_customers: int
    messages_generated: int
    messages_sent: Optional[int] = None
    preview: List[dict]  # Preview of generated messages
