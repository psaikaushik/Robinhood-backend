"""
Price Alerts Service - CANDIDATE STUB VERSION

INTERVIEWER NOTE:
This is the stub version for candidates to implement.
To use this version:
  1. Rename price_alerts.py -> price_alerts_impl.py
  2. Rename price_alerts_stub.py -> price_alerts.py
  3. Restart the target-app container

To switch back to working implementation (for chaos demo):
  1. Rename price_alerts.py -> price_alerts_stub.py
  2. Rename price_alerts_impl.py -> price_alerts.py
  3. Restart the target-app container

CANDIDATE TASK: Implement the methods in this service class.

The PriceAlertService should handle:
1. Creating price alerts for users
2. Getting all alerts for a user
3. Getting a specific alert
4. Deleting/deactivating alerts
5. Checking if alerts should be triggered based on current prices

Requirements:
- Users can set alerts to trigger when a stock goes ABOVE or BELOW a target price
- Alerts should be marked as triggered (is_triggered=True) when conditions are met
- Triggered alerts should have their triggered_at timestamp set
- Users should only be able to manage their own alerts
- Stock symbol should be validated (must exist in our system)

See tests/test_price_alerts.py for expected behavior.
Run tests with: pytest tests/test_price_alerts.py -v
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.price_alert import PriceAlert
from models.user import User
from schemas.price_alert import PriceAlertCreate
from services.market import MarketService


class PriceAlertService:
    """
    Service for managing price alerts.

    CANDIDATE TODO: Implement all methods below.
    """

    @staticmethod
    def create_alert(db: Session, user: User, alert_data: PriceAlertCreate) -> PriceAlert:
        """
        Create a new price alert for a user.

        Args:
            db: Database session
            user: The user creating the alert
            alert_data: The alert details (symbol, target_price, condition)

        Returns:
            The created PriceAlert object

        Raises:
            HTTPException(404): If the stock symbol doesn't exist
            HTTPException(400): If there's a validation error

        Hints:
        - Use alert_data.symbol.upper() to normalize the symbol
        - Use MarketService.get_stock(db, symbol) to verify the stock exists
        - Create a PriceAlert object with user_id, symbol, target_price, condition
        - Don't forget to db.add(), db.commit(), db.refresh()
        """
        # TODO: Implement this method
        raise NotImplementedError("Candidate must implement create_alert")

    @staticmethod
    def get_alerts(db: Session, user: User, active_only: bool = False) -> List[PriceAlert]:
        """
        Get all price alerts for a user.

        Args:
            db: Database session
            user: The user whose alerts to retrieve
            active_only: If True, only return non-triggered active alerts

        Returns:
            List of PriceAlert objects

        Hints:
        - Filter by user_id
        - If active_only, also filter by is_active=True AND is_triggered=False
        - Order by created_at descending
        """
        # TODO: Implement this method
        raise NotImplementedError("Candidate must implement get_alerts")

    @staticmethod
    def get_alert(db: Session, user: User, alert_id: int) -> PriceAlert:
        """
        Get a specific price alert by ID.

        Args:
            db: Database session
            user: The user (for ownership verification)
            alert_id: The alert ID to retrieve

        Returns:
            The PriceAlert object

        Raises:
            HTTPException(404): If alert not found or doesn't belong to user

        Hints:
        - Filter by both id AND user_id (security!)
        - Raise 404 if not found
        """
        # TODO: Implement this method
        raise NotImplementedError("Candidate must implement get_alert")

    @staticmethod
    def delete_alert(db: Session, user: User, alert_id: int) -> None:
        """
        Delete a price alert.

        Args:
            db: Database session
            user: The user (for ownership verification)
            alert_id: The alert ID to delete

        Raises:
            HTTPException(404): If alert not found or doesn't belong to user

        Hints:
        - Use get_alert() to find and verify ownership
        - Then db.delete() and db.commit()
        """
        # TODO: Implement this method
        raise NotImplementedError("Candidate must implement delete_alert")

    @staticmethod
    def check_and_trigger_alerts(db: Session, user: User) -> List[PriceAlert]:
        """
        Check all active alerts for a user and trigger any that meet conditions.

        An alert should be triggered when:
        - condition is "above" and current_price >= target_price
        - condition is "below" and current_price <= target_price

        When triggered:
        - Set is_triggered = True
        - Set triggered_at = current timestamp (datetime.utcnow())
        - Keep is_active = True (so user can see it was triggered)

        Args:
            db: Database session
            user: The user whose alerts to check

        Returns:
            List of alerts that were triggered in this check

        Hints:
        - Get all alerts where is_active=True AND is_triggered=False
        - For each alert, get current stock price with MarketService.get_stock()
        - Check if condition is met
        - If triggered, update is_triggered and triggered_at
        - Commit once at the end
        """
        # TODO: Implement this method
        raise NotImplementedError("Candidate must implement check_and_trigger_alerts")
