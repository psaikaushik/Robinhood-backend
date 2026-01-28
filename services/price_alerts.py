"""
Price Alerts Service

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

        CANDIDATE TODO: Implement this method
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

        CANDIDATE TODO: Implement this method
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

        CANDIDATE TODO: Implement this method
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

        CANDIDATE TODO: Implement this method
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
        - Set triggered_at = current timestamp
        - Keep is_active = True (so user can see it was triggered)

        Args:
            db: Database session
            user: The user whose alerts to check

        Returns:
            List of alerts that were triggered in this check

        CANDIDATE TODO: Implement this method
        """
        # TODO: Implement this method
        raise NotImplementedError("Candidate must implement check_and_trigger_alerts")
