from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class StockCreate(BaseModel):
    symbol: str
    name: str
    current_price: float
    previous_close: Optional[float] = None
    sector: Optional[str] = None
    market_cap: Optional[float] = None


class StockResponse(BaseModel):
    id: int
    symbol: str
    name: str
    current_price: float
    previous_close: Optional[float]
    day_high: Optional[float]
    day_low: Optional[float]
    volume: int
    market_cap: Optional[float]
    sector: Optional[str]
    change: Optional[float] = None
    change_percent: Optional[float] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class StockQuote(BaseModel):
    symbol: str
    price: float
    change: float
    change_percent: float
