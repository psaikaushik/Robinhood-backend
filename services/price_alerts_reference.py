"""
REFERENCE IMPLEMENTATION - FOR INTERVIEWERS ONLY

This is a naive (intentionally slow) implementation for demoing chaos scenarios.
DO NOT show this to candidates during the interview.

To use for chaos demo:
1. Copy the contents of this file into services/price_alerts.py
2. Restart server with SCENARIO=chaos_stress or SCENARIO=chaos_race
3. Demo the performance issues or race conditions
4. Discuss with candidate how to fix

This implementation has these intentional problems:
- N+1 queries: Gets stock price individually for each alert
- Individual commits: Commits after each alert trigger
- No locking: Vulnerable to race conditions
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import time

from models.price_alert import PriceAlert
from models.user import User
from schemas.price_alert import PriceAlertCreate
from services.market import MarketService


class PriceAlertService:
    """
    Naive implementation with intentional performance issues.
    Used for demoing chaos_stress and chaos_race scenarios.
    """

    @staticmethod
    def create_alert(db: Session, user: User, alert_data: PriceAlertCreate) -> PriceAlert:
        """Create a new price alert."""
        symbol = alert_data.symbol.upper()

        # Verify stock exists
        stock = MarketService.get_stock(db, symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock {symbol} not found"
            )

        # Create the alert
        alert = PriceAlert(
            user_id=user.id,
            symbol=symbol,
            target_price=alert_data.target_price,
            condition=alert_data.condition,
            is_triggered=False,
            is_active=True
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_alerts(db: Session, user: User, active_only: bool = False) -> List[PriceAlert]:
        """Get all alerts for a user."""
        query = db.query(PriceAlert).filter(PriceAlert.user_id == user.id)

        if active_only:
            query = query.filter(
                PriceAlert.is_active == True,
                PriceAlert.is_triggered == False
            )

        return query.all()

    @staticmethod
    def get_alert(db: Session, user: User, alert_id: int) -> PriceAlert:
        """Get a specific alert by ID."""
        alert = db.query(PriceAlert).filter(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user.id
        ).first()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        return alert

    @staticmethod
    def delete_alert(db: Session, user: User, alert_id: int) -> None:
        """Delete an alert."""
        alert = PriceAlertService.get_alert(db, user, alert_id)
        db.delete(alert)
        db.commit()

    @staticmethod
    def check_and_trigger_alerts(db: Session, user: User) -> List[PriceAlert]:
        """
        NAIVE IMPLEMENTATION - Intentionally slow!

        Problems:
        1. N+1 queries: Calls get_stock() for EACH alert (500 alerts = 500 queries)
        2. Individual commits: Commits after EACH trigger (slow I/O)
        3. No locking: Race condition vulnerable
        """
        # Get all active, non-triggered alerts
        alerts = db.query(PriceAlert).filter(
            PriceAlert.user_id == user.id,
            PriceAlert.is_active == True,
            PriceAlert.is_triggered == False
        ).all()

        triggered = []

        for alert in alerts:
            # PROBLEM 1: N+1 query - gets stock price individually for each alert
            # With 500 alerts, this makes 500 separate database queries!
            stock = MarketService.get_stock(db, alert.symbol)

            if not stock:
                continue

            current_price = stock.current_price

            # Check trigger condition
            should_trigger = False
            if alert.condition == "above" and current_price >= alert.target_price:
                should_trigger = True
            elif alert.condition == "below" and current_price <= alert.target_price:
                should_trigger = True

            if should_trigger:
                # PROBLEM 3: Race condition - between checking is_triggered above
                # and setting it here, another thread could also trigger this alert

                alert.is_triggered = True
                alert.triggered_at = datetime.utcnow()

                # PROBLEM 2: Individual commit - commits after EACH alert
                # Much slower than batching all updates into one commit
                db.commit()

                triggered.append(alert)

        return triggered
