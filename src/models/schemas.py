from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict, field_serializer
from enum import Enum
from datetime import date, datetime
from typing import Optional, Any
import re


class SubscriptionTier(str, Enum):
    BASIC = "Basic"
    PRO = "Pro"
    ENTERPRISE = "Enterprise"


class CustomerRecord(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            date: lambda v: v.isoformat()
        }
    )

    customer_name: str = Field(..., min_length=1, max_length=255)
    email: str
    subscription_tier: SubscriptionTier
    signup_date: date

    @field_serializer('signup_date')
    def serialize_signup_date(self, value: date) -> str:
        return value.isoformat()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v.strip().lower()):
            raise ValueError(f'Invalid email format: {v}')
        return v.strip().lower()

    @field_validator('customer_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Customer name cannot be empty')
        # Remove extra whitespace
        return ' '.join(v.strip().split())

    @field_validator('subscription_tier', mode='before')
    @classmethod
    def normalize_subscription_tier(cls, v: Any) -> SubscriptionTier:
        if isinstance(v, SubscriptionTier):
            return v

        if isinstance(v, str):
            tier_mapping = {
                'professional': SubscriptionTier.PRO,
                'prem': SubscriptionTier.PRO,
                'premium': SubscriptionTier.PRO,
                'pro': SubscriptionTier.PRO,
                'basic': SubscriptionTier.BASIC,
                'enterprise': SubscriptionTier.ENTERPRISE,
                'corp': SubscriptionTier.ENTERPRISE,
                'corporate': SubscriptionTier.ENTERPRISE,
            }

            normalized = v.strip().lower()
            return tier_mapping.get(normalized, SubscriptionTier.BASIC)

        # Default to Basic if type is unexpected
        return SubscriptionTier.BASIC

    @field_validator('signup_date', mode='before')
    @classmethod
    def parse_signup_date(cls, v: Any) -> date:
        if isinstance(v, date):
            return v

        if isinstance(v, str):
            v = v.strip()

            # Try various date formats
            date_formats = [
                '%Y-%m-%d',    # 2024-01-01
                '%m/%d/%Y',    # 01/01/2024
                '%d/%m/%Y',    # 01/01/2024 (European)
                '%B %d, %Y',   # January 1, 2024
                '%b %d, %Y',   # Jan 1, 2024
                '%d %b %Y',    # 1 Jan 2024
                '%d %b %y',    # 1 Jan 24
                '%b %d %y',    # Jan 1 24
                '%Y/%m/%d',    # 2024/01/01
                '%d-%m-%Y',    # 01-01-2024
                '%m-%d-%Y',    # 01-01-2024 (MM-DD-YYYY)
                '%Y.%m.%d',    # 2024.02.01
                '%d.%m.%Y',    # 01.02.2024
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue

            # Try to parse ordinal suffixes (1st, 2nd, 3rd, 4th)
            v_clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', v)
            for fmt in date_formats:
                try:
                    return datetime.strptime(v_clean, fmt).date()
                except ValueError:
                    continue

        raise ValueError(f'Unable to parse date: {v}')

    @model_validator(mode='before')
    @classmethod
    def validate_model(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Log warning for missing required fields
            required_fields = ['customer_name', 'email', 'subscription_tier', 'signup_date']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValueError(f'Missing required fields: {missing_fields}')
        return data

    

class FileUploadResponse(BaseModel):
    success: bool
    message: str
    processed_records: Optional[int] = None
    errors: Optional[list[str]] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
