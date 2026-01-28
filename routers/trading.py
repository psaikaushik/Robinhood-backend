from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.order import OrderCreate, OrderResponse
from services.trading import TradingService
from services.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/orders", tags=["Trading"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Place a buy or sell order.

    - **symbol**: Stock ticker symbol (e.g., "AAPL")
    - **order_type**: "market" or "limit"
    - **side**: "buy" or "sell"
    - **quantity**: Number of shares
    - **limit_price**: Required for limit orders
    """
    return TradingService.place_order(db, current_user, order)


@router.get("", response_model=List[OrderResponse])
def get_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all orders for the current user.

    Optional filter by status: pending, filled, cancelled, rejected
    """
    return TradingService.get_orders(db, current_user, status)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific order."""
    return TradingService.get_order(db, current_user, order_id)


@router.delete("/{order_id}", response_model=OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending order."""
    return TradingService.cancel_order(db, current_user, order_id)
