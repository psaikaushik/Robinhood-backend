from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    previous_close = Column(Float)
    day_high = Column(Float)
    day_low = Column(Float)
    volume = Column(Integer, default=0)
    market_cap = Column(Float)
    sector = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
