"""
Price Alerts Router

CANDIDATE TASK: Implement the API endpoints for price alerts.

Endpoints to implement:
- POST /alerts - Create a new price alert
- GET /alerts - Get all alerts for current user (with optional active_only filter)
- GET /alerts/{alert_id} - Get a specific alert
- DELETE /alerts/{alert_id} - Delete an alert
- POST /alerts/check - Check and trigger any alerts that meet conditions

See tests/test_price_alerts.py for expected behavior.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.price_alert import PriceAlertCreate, PriceAlertResponse
from services.price_alerts import PriceAlertService
from services.market import MarketService
from services.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/alerts", tags=["Price Alerts"])


# CANDIDATE TODO: Implement all endpoints below


@router.post("", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    alert: PriceAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new price alert.

    - **symbol**: Stock ticker symbol (e.g., "AAPL")
    - **target_price**: The price that triggers the alert
    - **condition**: "above" or "below"
    """
    created_alert = PriceAlertService.create_alert(db, current_user, alert)

    # Get current stock price
    stock = MarketService.get_stock(db, created_alert.symbol)
    current_price = stock.current_price if stock else None

    return PriceAlertResponse(
        id=created_alert.id,
        symbol=created_alert.symbol,
        target_price=created_alert.target_price,
        condition=created_alert.condition,
        is_triggered=created_alert.is_triggered,
        is_active=created_alert.is_active,
        created_at=created_alert.created_at,
        triggered_at=created_alert.triggered_at,
        current_price=current_price
    )


@router.get("", response_model=List[PriceAlertResponse])
def get_alerts(
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all price alerts for the current user.

    - **active_only**: If true, only return non-triggered active alerts
    """
    alerts = PriceAlertService.get_alerts(db, current_user, active_only)

    result = []
    for alert in alerts:
        stock = MarketService.get_stock(db, alert.symbol)
        current_price = stock.current_price if stock else None

        result.append(PriceAlertResponse(
            id=alert.id,
            symbol=alert.symbol,
            target_price=alert.target_price,
            condition=alert.condition,
            is_triggered=alert.is_triggered,
            is_active=alert.is_active,
            created_at=alert.created_at,
            triggered_at=alert.triggered_at,
            current_price=current_price
        ))

    return result


@router.get("/{alert_id}", response_model=PriceAlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific price alert by ID.
    """
    alert = PriceAlertService.get_alert(db, current_user, alert_id)

    stock = MarketService.get_stock(db, alert.symbol)
    current_price = stock.current_price if stock else None

    return PriceAlertResponse(
        id=alert.id,
        symbol=alert.symbol,
        target_price=alert.target_price,
        condition=alert.condition,
        is_triggered=alert.is_triggered,
        is_active=alert.is_active,
        created_at=alert.created_at,
        triggered_at=alert.triggered_at,
        current_price=current_price
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a price alert.
    """
    PriceAlertService.delete_alert(db, current_user, alert_id)
    return None


@router.post("/check", response_model=List[PriceAlertResponse])
def check_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check all active alerts and trigger any that meet their conditions.

    Returns the list of alerts that were triggered.
    """
    triggered_alerts = PriceAlertService.check_and_trigger_alerts(db, current_user)

    result = []
    for alert in triggered_alerts:
        stock = MarketService.get_stock(db, alert.symbol)
        current_price = stock.current_price if stock else None

        result.append(PriceAlertResponse(
            id=alert.id,
            symbol=alert.symbol,
            target_price=alert.target_price,
            condition=alert.condition,
            is_triggered=alert.is_triggered,
            is_active=alert.is_active,
            created_at=alert.created_at,
            triggered_at=alert.triggered_at,
            current_price=current_price
        ))

    return result
