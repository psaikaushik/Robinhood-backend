from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class HoldingResponse(BaseModel):
    id: int
    symbol: str
    quantity: float
    average_buy_price: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    total_gain_loss: Optional[float] = None
    gain_loss_percent: Optional[float] = None

    class Config:
        from_attributes = True


class PortfolioResponse(BaseModel):
    cash_balance: float
    total_holdings_value: float
    total_portfolio_value: float
    total_gain_loss: float
    holdings: List[HoldingResponse]
