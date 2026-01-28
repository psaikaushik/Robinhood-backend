from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class OrderCreate(BaseModel):
    symbol: str
    order_type: str  # "market" or "limit"
    side: str  # "buy" or "sell"
    quantity: float
    limit_price: Optional[float] = None

    @field_validator('order_type')
    @classmethod
    def validate_order_type(cls, v):
        if v.lower() not in ['market', 'limit']:
            raise ValueError('order_type must be "market" or "limit"')
        return v.lower()

    @field_validator('side')
    @classmethod
    def validate_side(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError('side must be "buy" or "sell"')
        return v.lower()

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('quantity must be greater than 0')
        return v


class OrderResponse(BaseModel):
    id: int
    symbol: str
    order_type: str
    side: str
    quantity: float
    limit_price: Optional[float]
    filled_quantity: float
    filled_price: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
