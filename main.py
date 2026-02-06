import random
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, SessionLocal, get_db
from routers import auth_router, stocks_router, trading_router, portfolio_router, watchlist_router, price_alerts_router
from routers.admin import router as admin_router
from services.market import MarketService
from services.scenario import get_scenario_manager, ScenarioManager
from services.auth import AuthService, get_current_user
from models.user import User
from models.price_alert import PriceAlert
from schemas.user import UserCreate

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Robinhood Clone API",
    description="A lightweight Robinhood-style trading platform backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(stocks_router)
app.include_router(trading_router)
app.include_router(portfolio_router)
app.include_router(watchlist_router)
app.include_router(price_alerts_router)
app.include_router(admin_router, prefix="/admin", tags=["Admin"])


@app.on_event("startup")
def startup_event():
    """Initialize database with mock stock data on startup."""
    db = SessionLocal()
    try:
        MarketService.initialize_stocks(db)

        # Scenario-specific setup
        scenario_mgr = get_scenario_manager()

        # Chaos Stress: Pre-populate alerts
        if scenario_mgr.should_pre_populate_alerts():
            _setup_stress_test_alerts(db, scenario_mgr.get_pre_populate_alert_count())

    finally:
        db.close()


def _setup_stress_test_alerts(db: Session, count: int):
    """Pre-populate database with many alerts for stress testing."""
    # Create a test user if not exists
    test_user = AuthService.get_user_by_username(db, "stresstest")
    if not test_user:
        user_data = UserCreate(
            email="stress@test.com",
            username="stresstest",
            password="stresstest123",
            full_name="Stress Test User"
        )
        test_user = AuthService.create_user(db, user_data)

    # Check if alerts already exist
    existing = db.query(PriceAlert).filter(PriceAlert.user_id == test_user.id).count()
    if existing >= count:
        print(f"⚡ Stress test: {existing} alerts already exist")
        return

    # Get all stocks
    stocks = MarketService.get_all_stocks(db)
    stock_symbols = [s.symbol for s in stocks]

    # Create alerts
    print(f"⚡ Stress test: Creating {count} alerts...")
    for i in range(count):
        symbol = random.choice(stock_symbols)
        stock = MarketService.get_stock(db, symbol)

        # Random target price around current price
        price_variation = random.uniform(0.8, 1.2)
        target_price = round(stock.current_price * price_variation, 2)
        condition = random.choice(["above", "below"])

        alert = PriceAlert(
            user_id=test_user.id,
            symbol=symbol,
            target_price=target_price,
            condition=condition,
            is_triggered=False,
            is_active=True
        )
        db.add(alert)

        if (i + 1) % 100 == 0:
            db.commit()
            print(f"  Created {i + 1}/{count} alerts...")

    db.commit()
    print(f"✅ Stress test: Created {count} alerts for user 'stresstest'")


@app.get("/", tags=["Root"])
def root():
    """API root endpoint."""
    return {
        "message": "Welcome to Robinhood Clone API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth",
            "stocks": "/stocks",
            "orders": "/orders",
            "portfolio": "/portfolio",
            "watchlist": "/watchlist",
            "alerts": "/alerts"
        }
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============== INTERVIEWER ENDPOINTS (Chaos Engineering) ==============

@app.get("/scenario", tags=["Interviewer"])
def get_current_scenario():
    """Get current chaos scenario info. FOR INTERVIEWERS ONLY."""
    scenario_mgr = get_scenario_manager()
    return scenario_mgr.get_scenario_info()


@app.get("/scenarios", tags=["Interviewer"])
def list_scenarios():
    """List all available chaos scenarios. FOR INTERVIEWERS ONLY."""
    return {
        "scenarios": ScenarioManager.list_scenarios(),
        "usage": "Set SCENARIO=<id> environment variable and restart server"
    }


@app.post("/alerts/check-concurrent", tags=["Interviewer"])
def check_alerts_concurrent(
    num_concurrent: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Simulate concurrent check_alerts calls to expose race conditions.
    FOR INTERVIEWERS ONLY - used to demo race condition bugs.
    """
    scenario_mgr = get_scenario_manager()
    if not scenario_mgr.is_concurrent_test_enabled():
        return {
            "error": "Concurrent test not enabled",
            "hint": "Start server with SCENARIO=chaos_race"
        }

    from services.price_alerts import PriceAlertService

    results = []
    errors = []

    def run_check(thread_id: int):
        """Run a single check in a thread."""
        thread_db = SessionLocal()
        try:
            # Add artificial delay to increase race condition likelihood
            delay_ms = scenario_mgr.get_artificial_delay_ms()
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0 * random.random())

            triggered = PriceAlertService.check_and_trigger_alerts(thread_db, current_user)
            return {
                "thread_id": thread_id,
                "triggered_count": len(triggered),
                "triggered_ids": [a.id for a in triggered]
            }
        except Exception as e:
            return {"thread_id": thread_id, "error": str(e)}
        finally:
            thread_db.close()

    # Run concurrent checks
    with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [executor.submit(run_check, i) for i in range(num_concurrent)]
        for future in futures:
            results.append(future.result())

    # Analyze results for race conditions
    all_triggered_ids = []
    for r in results:
        all_triggered_ids.extend(r.get("triggered_ids", []))

    duplicates = [id for id in all_triggered_ids if all_triggered_ids.count(id) > 1]

    return {
        "concurrent_calls": num_concurrent,
        "results": results,
        "race_condition_detected": len(duplicates) > 0,
        "duplicate_triggers": list(set(duplicates)),
        "message": "🐛 RACE CONDITION BUG!" if duplicates else "No race condition detected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
