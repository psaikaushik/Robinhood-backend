from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class PriceAlert(Base):
    """
    Price Alert model - allows users to set alerts for when a stock
    reaches a certain price.

    CANDIDATE TODO: This model is provided. You need to implement the
    service and router to make the tests pass.
    """
    __tablename__ = "price_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String, index=True, nullable=False)
    target_price = Column(Float, nullable=False)
    condition = Column(String, nullable=False)  # "above" or "below"
    is_triggered = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")
