from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class WatchlistAdd(BaseModel):
    symbol: str


class WatchlistResponse(BaseModel):
    id: int
    symbol: str
    added_at: datetime
    current_price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None

    class Config:
        from_attributes = True
