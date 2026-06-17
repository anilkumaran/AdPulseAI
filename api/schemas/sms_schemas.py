from pydantic import AliasChoices, BaseModel, Field, field_validator, validator
from typing import Any, List, Optional

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
    send_immediately: bool = Field(
        default=False,
        validation_alias=AliasChoices("send_immediately", "sendImmediately"),
        description="Send SMS immediately or just generate",
    )

    @field_validator("send_immediately", mode="before")
    @classmethod
    def coerce_send_immediately(cls, v: Any) -> bool:
        if isinstance(v, str):
            return v.strip().lower() in ("1", "true", "yes", "on")
        return bool(v)


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
    skipped: int = 0
    results: List[dict]


class SNSDeliveryLine(BaseModel):
    """One SNS attempt outcome (phone masked for logs/UI)."""
    status: str = Field(..., description="success | error | skipped_allowlist")
    phone_tail: str = Field(default="", description="Last digits of E.164 (no full number)")
    detail: Optional[str] = Field(None, description="AWS/allowlist error text or mock note")
    message_id: Optional[str] = Field(None, description="SNS MessageId when status is success")


class CampaignSMSResponse(BaseModel):
    """Response for campaign SMS generation/send"""
    status: str
    campaign_id: str
    total_customers: int
    messages_generated: int
    send_requested: bool = Field(
        default=False,
        description="True if the client requested immediate SNS delivery (same as send_immediately on the request).",
    )
    messages_sent: Optional[int] = None
    messages_skipped: Optional[int] = None
    messages_failed: Optional[int] = None
    from_cache: bool = Field(
        default=False,
        description="True when bodies were reused from cache (same normalized campaign text + same customer ids).",
    )
    sns_dispatch: Optional[str] = Field(
        default=None,
        description=(
            "not_requested | no_valid_phones | mock_test_env | mock_no_aws_client | live. "
            "Mock modes do not call AWS; phones still receive nothing."
        ),
    )
    sns_delivery_results: Optional[List[SNSDeliveryLine]] = Field(
        default=None,
        description="Per-recipient SNS outcome when send_immediately ran (status, masked phone, error/detail).",
    )
    preview: List[dict]  # Preview of generated messages
