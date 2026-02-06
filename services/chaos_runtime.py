"""Runtime chaos injection service.

This service allows activating chaos scenarios without restarting the server.
Changes take effect immediately for the next request.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import random

from models.stock import Stock
from models.price_alert import PriceAlert
from models.user import User


class ChaosRuntime:
    """Runtime chaos management."""

    _active_scenario: Optional[str] = None
    _race_delay_enabled: bool = False
    _race_delay_ms: int = 500

    @classmethod
    def get_active_scenario(cls) -> Optional[str]:
        """Get the currently active chaos scenario."""
        return cls._active_scenario

    @classmethod
    def is_race_delay_enabled(cls) -> bool:
        """Check if artificial race delay is enabled."""
        return cls._race_delay_enabled

    @classmethod
    def get_race_delay_ms(cls) -> int:
        """Get the artificial delay in milliseconds."""
        return cls._race_delay_ms

    @classmethod
    def activate(cls, db: Session, scenario: str) -> Dict[str, Any]:
        """Activate a chaos scenario."""

        # Reset any previous chaos first
        cls.reset(db)

        if scenario == "chaos_data":
            return cls._activate_chaos_data(db)
        elif scenario == "chaos_stress":
            return cls._activate_chaos_stress(db)
        elif scenario == "chaos_race":
            return cls._activate_chaos_race(db)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

    @classmethod
    def reset(cls, db: Session) -> Dict[str, Any]:
        """Reset to clean state."""

        result = {"actions": []}

        # Reset race delay flag
        if cls._race_delay_enabled:
            cls._race_delay_enabled = False
            result["actions"].append("Disabled race delay")

        # Reset stock prices to normal values
        stocks_reset = cls._reset_stock_prices(db)
        if stocks_reset > 0:
            result["actions"].append(f"Reset {stocks_reset} stock prices")

        # Delete stress test alerts
        alerts_deleted = cls._delete_stress_alerts(db)
        if alerts_deleted > 0:
            result["actions"].append(f"Deleted {alerts_deleted} stress test alerts")

        cls._active_scenario = None
        result["scenario"] = None

        return result

    @classmethod
    def _activate_chaos_data(cls, db: Session) -> Dict[str, Any]:
        """Inject corrupted data into stocks."""

        result = {"actions": [], "corrupted_stocks": []}

        # Corrupt GOOGL - negative price
        googl = db.query(Stock).filter(Stock.symbol == "GOOGL").first()
        if googl:
            googl.price = -50.25
            result["corrupted_stocks"].append({"symbol": "GOOGL", "issue": "negative price"})

        # Corrupt AMZN - null price (set to 0 as SQLite doesn't support null for this)
        amzn = db.query(Stock).filter(Stock.symbol == "AMZN").first()
        if amzn:
            amzn.price = 0
            result["corrupted_stocks"].append({"symbol": "AMZN", "issue": "zero price"})

        # Corrupt TSLA - extremely high price (overflow-like)
        tsla = db.query(Stock).filter(Stock.symbol == "TSLA").first()
        if tsla:
            tsla.price = 999999999999.99
            result["corrupted_stocks"].append({"symbol": "TSLA", "issue": "overflow price"})

        # Corrupt NVDA - NaN-like value (negative zero situation)
        nvda = db.query(Stock).filter(Stock.symbol == "NVDA").first()
        if nvda:
            nvda.price = -0.0001
            result["corrupted_stocks"].append({"symbol": "NVDA", "issue": "near-zero negative"})

        db.commit()

        cls._active_scenario = "chaos_data"
        result["scenario"] = "chaos_data"
        result["actions"].append(f"Corrupted {len(result['corrupted_stocks'])} stocks")

        return result

    @classmethod
    def _activate_chaos_stress(cls, db: Session) -> Dict[str, Any]:
        """Create 500 alerts for stress testing."""

        result = {"actions": []}

        # Find or create stress test user
        stress_user = db.query(User).filter(User.username == "stresstest").first()

        if not stress_user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

            stress_user = User(
                username="stresstest",
                email="stresstest@example.com",
                hashed_password=pwd_context.hash("stresstest123"),
                balance=100000.0
            )
            db.add(stress_user)
            db.commit()
            db.refresh(stress_user)
            result["actions"].append("Created stresstest user")

        # Get all stocks
        stocks = db.query(Stock).all()
        if not stocks:
            raise ValueError("No stocks in database")

        # Create 500 alerts
        alerts_created = 0
        for i in range(500):
            stock = random.choice(stocks)
            target_price = stock.price * random.uniform(0.8, 1.2)
            condition = random.choice(["above", "below"])

            alert = PriceAlert(
                user_id=stress_user.id,
                symbol=stock.symbol,
                target_price=target_price,
                condition=condition,
                is_active=True,
                is_triggered=False
            )
            db.add(alert)
            alerts_created += 1

        db.commit()

        cls._active_scenario = "chaos_stress"
        result["scenario"] = "chaos_stress"
        result["actions"].append(f"Created {alerts_created} alerts for stresstest user")
        result["stress_user"] = {
            "username": "stresstest",
            "password": "stresstest123"
        }

        return result

    @classmethod
    def _activate_chaos_race(cls, db: Session) -> Dict[str, Any]:
        """Enable race condition testing mode."""

        result = {"actions": []}

        # Enable artificial delay
        cls._race_delay_enabled = True
        cls._race_delay_ms = 500

        cls._active_scenario = "chaos_race"
        result["scenario"] = "chaos_race"
        result["actions"].append(f"Enabled {cls._race_delay_ms}ms artificial delay")
        result["actions"].append("Race condition testing mode active")

        return result

    @classmethod
    def _reset_stock_prices(cls, db: Session) -> int:
        """Reset stock prices to reasonable values."""

        # Original prices (approximate)
        original_prices = {
            "AAPL": 178.50,
            "GOOGL": 141.25,
            "MSFT": 378.90,
            "AMZN": 178.25,
            "TSLA": 248.50,
            "META": 505.75,
            "NVDA": 875.25,
            "JPM": 198.45,
            "V": 279.80,
            "JNJ": 156.30
        }

        count = 0
        for symbol, price in original_prices.items():
            stock = db.query(Stock).filter(Stock.symbol == symbol).first()
            if stock and (stock.price < 0 or stock.price > 10000 or stock.price == 0):
                stock.price = price
                count += 1

        if count > 0:
            db.commit()

        return count

    @classmethod
    def _delete_stress_alerts(cls, db: Session) -> int:
        """Delete alerts created for stress testing."""

        stress_user = db.query(User).filter(User.username == "stresstest").first()
        if not stress_user:
            return 0

        count = db.query(PriceAlert).filter(
            PriceAlert.user_id == stress_user.id
        ).delete()

        db.commit()
        return count
