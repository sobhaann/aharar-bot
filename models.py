"""Pydantic models for data validation."""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class UserModel(BaseModel):
    """User model."""

    id: Optional[int] = None
    pin_code: str = Field(..., min_length=1, max_length=10)
    full_name: str = Field(..., min_length=1, max_length=255)
    telegram_id: Optional[int] = None
    donation_amount: str = Field(..., max_length=50)
    donation_link: str = Field(..., max_length=500)
    status: str = Field(default="unverified")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        """Model configuration."""

        from_attributes = True


class PaymentModel(BaseModel):
    """Payment model."""

    id: Optional[int] = None
    user_id: int
    jalali_month: int = Field(..., ge=1, le=12)
    jalali_year: int = Field(..., ge=1300, le=2000)
    status: str = Field(default="pending")
    image_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @validator("jalali_month")
    def validate_month(cls, v: int) -> int:
        """Validate Jalali month."""
        if not (1 <= v <= 12):
            raise ValueError("Month must be between 1 and 12")
        return v

    class Config:
        """Model configuration."""

        from_attributes = True


class PendingApprovalModel(BaseModel):
    """Pending approval model."""

    id: Optional[int] = None
    user_id: int
    status: str = Field(default="pending")
    created_at: Optional[datetime] = None

    class Config:
        """Model configuration."""

        from_attributes = True
