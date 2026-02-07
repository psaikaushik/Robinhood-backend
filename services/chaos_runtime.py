"""Runtime chaos injection service.

This service allows activating chaos scenarios without restarting the server.
Changes take effect immediately for the next request.
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from models.stock import Stock
from models.price_alert import PriceAlert
from models.user import User


class ChaosRuntime:
    """Runtime chaos management."""

    _active_scenario: Optional[str] = None
    _race_delay_enabled: bool = False
    _race_delay_ms: int = 500
    _precision_mode: bool = False
    _boundary_mode: bool = False
    _inconsistent_mode: bool = False

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
        elif scenario == "chaos_boundary":
            return cls._activate_chaos_boundary(db)
        elif scenario == "chaos_precision":
            return cls._activate_chaos_precision(db)
        elif scenario == "chaos_inconsistent":
            return cls._activate_chaos_inconsistent(db)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

    @classmethod
    def reset(cls, db: Session) -> Dict[str, Any]:
        """Reset to clean state."""

        result = {"actions": []}

        # Reset all chaos flags
        if cls._race_delay_enabled:
            cls._race_delay_enabled = False
            result["actions"].append("Disabled race delay")
        if cls._precision_mode:
            cls._precision_mode = False
            result["actions"].append("Disabled precision mode")
        if cls._boundary_mode:
            cls._boundary_mode = False
            result["actions"].append("Disabled boundary mode")
        if cls._inconsistent_mode:
            cls._inconsistent_mode = False
            result["actions"].append("Disabled inconsistent mode")

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
            googl.current_price = -50.25
            result["corrupted_stocks"].append({"symbol": "GOOGL", "issue": "negative price"})

        # Corrupt AMZN - null price (set to 0 as SQLite doesn't support null for this)
        amzn = db.query(Stock).filter(Stock.symbol == "AMZN").first()
        if amzn:
            amzn.current_price = 0
            result["corrupted_stocks"].append({"symbol": "AMZN", "issue": "zero price"})

        # Corrupt TSLA - extremely high price (overflow-like)
        tsla = db.query(Stock).filter(Stock.symbol == "TSLA").first()
        if tsla:
            tsla.current_price = 999999999999.99
            result["corrupted_stocks"].append({"symbol": "TSLA", "issue": "overflow price"})

        # Corrupt NVDA - NaN-like value (negative zero situation)
        nvda = db.query(Stock).filter(Stock.symbol == "NVDA").first()
        if nvda:
            nvda.current_price = -0.0001
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
            target_price = stock.current_price * random.uniform(0.8, 1.2)
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
            if stock and (stock.current_price < 0 or stock.current_price > 10000 or stock.current_price == 0):
                stock.current_price = price
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

    # =========================================================================
    # NEW SUBTLE CHAOS SCENARIOS - Require investigation to find
    # =========================================================================

    @classmethod
    def _activate_chaos_boundary(cls, db: Session) -> Dict[str, Any]:
        """
        Create alerts at exact price boundaries - exposes >= vs > logic bugs.

        The candidate needs to:
        1. Notice some alerts trigger unexpectedly (or don't trigger when expected)
        2. Investigate the exact values
        3. Realize the boundary condition logic is the issue
        """
        result = {"actions": [], "hints": []}
        cls._boundary_mode = True

        # Find or create a test user
        test_user = cls._get_or_create_boundary_user(db)

        # Get current stock prices
        aapl = db.query(Stock).filter(Stock.symbol == "AAPL").first()
        msft = db.query(Stock).filter(Stock.symbol == "MSFT").first()

        if aapl:
            # Create alert where target_price == current_price EXACTLY
            # This tests if >= or > is used
            alert1 = PriceAlert(
                user_id=test_user.id,
                symbol="AAPL",
                target_price=aapl.current_price,  # Exactly equal!
                condition="above",
                is_active=True,
                is_triggered=False
            )
            db.add(alert1)
            result["actions"].append(f"Created AAPL alert at exact price ${aapl.current_price}")

            # Create alert just barely below (0.01 difference)
            alert2 = PriceAlert(
                user_id=test_user.id,
                symbol="AAPL",
                target_price=aapl.current_price - 0.01,
                condition="above",
                is_active=True,
                is_triggered=False
            )
            db.add(alert2)

        if msft:
            # Similar for "below" condition
            alert3 = PriceAlert(
                user_id=test_user.id,
                symbol="MSFT",
                target_price=msft.current_price,  # Exactly equal!
                condition="below",
                is_active=True,
                is_triggered=False
            )
            db.add(alert3)
            result["actions"].append(f"Created MSFT alert at exact price ${msft.current_price}")

        db.commit()

        cls._active_scenario = "chaos_boundary"
        result["scenario"] = "chaos_boundary"
        result["test_user"] = {"username": "boundarytest", "password": "boundary123"}
        result["hints"].append("Login as boundarytest and run POST /alerts/check")
        result["hints"].append("Compare which alerts triggered vs. which you expected")

        return result

    @classmethod
    def _activate_chaos_precision(cls, db: Session) -> Dict[str, Any]:
        """
        Create floating point precision edge cases.

        The candidate needs to:
        1. Notice alerts behaving inconsistently
        2. Investigate the actual values (may need to print/log)
        3. Discover float comparison issues (0.1 + 0.2 != 0.3)
        """
        result = {"actions": [], "hints": []}
        cls._precision_mode = True

        test_user = cls._get_or_create_precision_user(db)

        # Set stock prices to values that cause float precision issues
        googl = db.query(Stock).filter(Stock.symbol == "GOOGL").first()
        if googl:
            # Set to a value that has precision issues
            googl.current_price = 100.0 + 0.1 + 0.1 + 0.1  # = 100.30000000000001

            # Alert at "100.30" - direct comparison may fail!
            alert = PriceAlert(
                user_id=test_user.id,
                symbol="GOOGL",
                target_price=100.30,  # Looks equal but isn't!
                condition="above",
                is_active=True,
                is_triggered=False
            )
            db.add(alert)
            result["actions"].append(f"Created GOOGL precision trap (price: {googl.current_price})")

        meta = db.query(Stock).filter(Stock.symbol == "META").first()
        if meta:
            # Another precision trap
            meta.current_price = 0.1 + 0.2  # = 0.30000000000000004

            alert = PriceAlert(
                user_id=test_user.id,
                symbol="META",
                target_price=0.3,  # Should be equal but...
                condition="below",
                is_active=True,
                is_triggered=False
            )
            db.add(alert)
            result["actions"].append(f"Created META precision trap (price: {meta.current_price})")

        db.commit()

        cls._active_scenario = "chaos_precision"
        result["scenario"] = "chaos_precision"
        result["test_user"] = {"username": "precisiontest", "password": "precision123"}
        result["hints"].append("Why do some alerts trigger when they shouldn't (or vice versa)?")
        result["hints"].append("Try printing the actual values being compared")

        return result

    @classmethod
    def _activate_chaos_inconsistent(cls, db: Session) -> Dict[str, Any]:
        """
        Create data inconsistencies that cause silent failures.

        The candidate needs to:
        1. Notice that some operations succeed but data looks wrong
        2. Investigate the relationships between objects
        3. Find the data integrity issue
        """
        result = {"actions": [], "hints": []}
        cls._inconsistent_mode = True

        test_user = cls._get_or_create_inconsistent_user(db)

        # Create alerts with timestamps that are logically impossible
        aapl = db.query(Stock).filter(Stock.symbol == "AAPL").first()
        if aapl:
            # Alert that was "triggered" BEFORE it was created (time travel!)
            alert = PriceAlert(
                user_id=test_user.id,
                symbol="AAPL",
                target_price=100.00,
                condition="above",
                is_active=True,
                is_triggered=True,
                triggered_at=datetime.utcnow() - timedelta(days=1),
                created_at=datetime.utcnow()  # Created AFTER triggered!
            )
            db.add(alert)
            result["actions"].append("Created AAPL alert with impossible timestamps")

        # Create duplicate alerts (same user, same stock, same condition)
        # This can cause double-triggering or confusion
        nvda = db.query(Stock).filter(Stock.symbol == "NVDA").first()
        if nvda:
            for i in range(3):
                alert = PriceAlert(
                    user_id=test_user.id,
                    symbol="NVDA",
                    target_price=nvda.current_price - 10,  # Will trigger
                    condition="above",
                    is_active=True,
                    is_triggered=False
                )
                db.add(alert)
            result["actions"].append("Created 3 duplicate NVDA alerts (same conditions)")

        db.commit()

        cls._active_scenario = "chaos_inconsistent"
        result["scenario"] = "chaos_inconsistent"
        result["test_user"] = {"username": "inconsistenttest", "password": "inconsistent123"}
        result["hints"].append("Run GET /alerts and examine the data carefully")
        result["hints"].append("Do the timestamps make sense? Are there duplicates?")
        result["hints"].append("What happens when you trigger alerts with duplicates?")

        return result

    @classmethod
    def _get_or_create_boundary_user(cls, db: Session) -> User:
        """Get or create the boundary test user."""
        user = db.query(User).filter(User.username == "boundarytest").first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                username="boundarytest",
                email="boundary@test.com",
                hashed_password=pwd_context.hash("boundary123"),
                balance=100000.0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @classmethod
    def _get_or_create_precision_user(cls, db: Session) -> User:
        """Get or create the precision test user."""
        user = db.query(User).filter(User.username == "precisiontest").first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                username="precisiontest",
                email="precision@test.com",
                hashed_password=pwd_context.hash("precision123"),
                balance=100000.0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    @classmethod
    def _get_or_create_inconsistent_user(cls, db: Session) -> User:
        """Get or create the inconsistent test user."""
        user = db.query(User).filter(User.username == "inconsistenttest").first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                username="inconsistenttest",
                email="inconsistent@test.com",
                hashed_password=pwd_context.hash("inconsistent123"),
                balance=100000.0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
