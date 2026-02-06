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
        """
        symbol = alert_data.symbol.upper()

        # Verify stock exists
        stock = MarketService.get_stock(db, symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock {symbol} not found"
            )

        alert = PriceAlert(
            user_id=user.id,
            symbol=symbol,
            target_price=alert_data.target_price,
            condition=alert_data.condition.lower(),
            is_triggered=False,
            is_active=True
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

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
        """
        query = db.query(PriceAlert).filter(PriceAlert.user_id == user.id)

        if active_only:
            query = query.filter(
                PriceAlert.is_active == True,
                PriceAlert.is_triggered == False
            )

        return query.order_by(PriceAlert.created_at.desc()).all()

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
        """
        alert = db.query(PriceAlert).filter(
            PriceAlert.id == alert_id,
            PriceAlert.user_id == user.id
        ).first()

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found"
            )

        return alert

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
        """
        alert = PriceAlertService.get_alert(db, user, alert_id)
        db.delete(alert)
        db.commit()

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
        """
        # Get active, non-triggered alerts
        alerts = db.query(PriceAlert).filter(
            PriceAlert.user_id == user.id,
            PriceAlert.is_active == True,
            PriceAlert.is_triggered == False
        ).all()

        triggered = []

        for alert in alerts:
            stock = MarketService.get_stock(db, alert.symbol)
            if not stock:
                continue

            current_price = stock.current_price
            should_trigger = False

            if alert.condition == "above" and current_price >= alert.target_price:
                should_trigger = True
            elif alert.condition == "below" and current_price <= alert.target_price:
                should_trigger = True

            if should_trigger:
                alert.is_triggered = True
                alert.triggered_at = datetime.utcnow()
                triggered.append(alert)

        if triggered:
            db.commit()

        return triggered


# =============================================================================
# STUB VERSION FOR CANDIDATES (Comment out above implementation, uncomment below)
# =============================================================================
#
# class PriceAlertService:
#     """
#     Service for managing price alerts.
#
#     CANDIDATE TODO: Implement all methods below.
#     """
#
#     @staticmethod
#     def create_alert(db: Session, user: User, alert_data: PriceAlertCreate) -> PriceAlert:
#         """
#         Create a new price alert for a user.
#
#         Args:
#             db: Database session
#             user: The user creating the alert
#             alert_data: The alert details (symbol, target_price, condition)
#
#         Returns:
#             The created PriceAlert object
#
#         Raises:
#             HTTPException(404): If the stock symbol doesn't exist
#         """
#         # TODO: Implement this method
#         raise NotImplementedError("Candidate must implement create_alert")
#
#     @staticmethod
#     def get_alerts(db: Session, user: User, active_only: bool = False) -> List[PriceAlert]:
#         """
#         Get all price alerts for a user.
#
#         Args:
#             db: Database session
#             user: The user whose alerts to retrieve
#             active_only: If True, only return non-triggered active alerts
#
#         Returns:
#             List of PriceAlert objects
#         """
#         # TODO: Implement this method
#         raise NotImplementedError("Candidate must implement get_alerts")
#
#     @staticmethod
#     def get_alert(db: Session, user: User, alert_id: int) -> PriceAlert:
#         """
#         Get a specific price alert by ID.
#
#         Args:
#             db: Database session
#             user: The user (for ownership verification)
#             alert_id: The alert ID to retrieve
#
#         Returns:
#             The PriceAlert object
#
#         Raises:
#             HTTPException(404): If alert not found or doesn't belong to user
#         """
#         # TODO: Implement this method
#         raise NotImplementedError("Candidate must implement get_alert")
#
#     @staticmethod
#     def delete_alert(db: Session, user: User, alert_id: int) -> None:
#         """
#         Delete a price alert.
#
#         Args:
#             db: Database session
#             user: The user (for ownership verification)
#             alert_id: The alert ID to delete
#
#         Raises:
#             HTTPException(404): If alert not found or doesn't belong to user
#         """
#         # TODO: Implement this method
#         raise NotImplementedError("Candidate must implement delete_alert")
#
#     @staticmethod
#     def check_and_trigger_alerts(db: Session, user: User) -> List[PriceAlert]:
#         """
#         Check all active alerts for a user and trigger any that meet conditions.
#
#         An alert should be triggered when:
#         - condition is "above" and current_price >= target_price
#         - condition is "below" and current_price <= target_price
#
#         When triggered:
#         - Set is_triggered = True
#         - Set triggered_at = current timestamp
#
#         Args:
#             db: Database session
#             user: The user whose alerts to check
#
#         Returns:
#             List of alerts that were triggered in this check
#         """
#         # TODO: Implement this method
#         raise NotImplementedError("Candidate must implement check_and_trigger_alerts")
