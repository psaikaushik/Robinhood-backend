from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class PriceAlertCreate(BaseModel):
    """
    Schema for creating a price alert.

    CANDIDATE TODO: This schema is provided for you.
    """
    symbol: str
    target_price: float
    condition: str  # "above" or "below"

    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v):
        if v.lower() not in ['above', 'below']:
            raise ValueError('condition must be "above" or "below"')
        return v.lower()

    @field_validator('target_price')
    @classmethod
    def validate_target_price(cls, v):
        if v <= 0:
            raise ValueError('target_price must be greater than 0')
        return v


class PriceAlertResponse(BaseModel):
    """
    Schema for price alert response.

    CANDIDATE TODO: This schema is provided for you.
    """
    id: int
    symbol: str
    target_price: float
    condition: str
    is_triggered: bool
    is_active: bool
    created_at: datetime
    triggered_at: Optional[datetime]
    current_price: Optional[float] = None

    class Config:
        from_attributes = True
