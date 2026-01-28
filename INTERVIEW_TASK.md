# Robinhood Backend - Interview Coding Task

## Overview

This is a lightweight Robinhood-style stock trading backend built with Python and FastAPI. Your task is to implement a new feature: **Price Alerts**.

---

## Getting Started with GitHub Codespaces (Recommended)

No local setup required! Everything runs in your browser.

### Step 1: Open in Codespaces

1. Click the green **Code** button at the top of this repo
2. Click the **Codespaces** tab
3. Click **Create codespace on main**
4. Wait ~1 minute for the environment to build

You'll see VS Code in your browser with everything pre-configured!

### Step 2: Verify Setup

Once the Codespace loads, open a terminal (`Ctrl+`` ` or `Cmd+`` `) and run:

```bash
pytest tests/test_price_alerts.py -v
```

You should see tests failing - that's expected! Your job is to make them pass.

### Step 3: Run the Server (Optional)

To explore the API interactively:

```bash
python main.py
```

Then click the **Ports** tab at the bottom, find port 8000, and click the globe icon to open the API docs.

### Using AI Assistance

- **GitHub Copilot** is available for code suggestions
- **Copilot Chat** (left sidebar) can answer questions about the codebase
- Feel free to use these tools!

---

## Alternative: Local Setup

If you prefer to run locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_price_alerts.py -v

# Run server
python main.py
# API docs at http://localhost:8000/docs
```

---

## Your Task: Implement Price Alerts

Users want to be notified when a stock reaches a certain price. You need to implement the Price Alerts feature.

### Requirements

1. Users can create price alerts with:
   - A stock symbol (must exist in the system)
   - A target price
   - A condition: "above" or "below"

2. Users can:
   - Create new alerts
   - View all their alerts
   - View a specific alert by ID
   - Delete alerts
   - Check/trigger alerts based on current prices

3. Alert triggering logic:
   - An alert with condition "above" triggers when `current_price >= target_price`
   - An alert with condition "below" triggers when `current_price <= target_price`
   - When triggered, set `is_triggered = True` and `triggered_at = current timestamp`
   - Already triggered alerts should not trigger again

### Files to Modify

1. **`services/price_alerts.py`** - Implement the `PriceAlertService` class methods:
   - `create_alert()` - Create a new price alert
   - `get_alerts()` - Get all alerts for a user
   - `get_alert()` - Get a specific alert by ID
   - `delete_alert()` - Delete an alert
   - `check_and_trigger_alerts()` - Check and trigger alerts based on current prices

2. **`routers/price_alerts.py`** - Implement the API endpoints:
   - `POST /alerts` - Create a new alert
   - `GET /alerts` - Get all alerts (with optional `active_only` filter)
   - `GET /alerts/{alert_id}` - Get a specific alert
   - `DELETE /alerts/{alert_id}` - Delete an alert
   - `POST /alerts/check` - Check and trigger alerts

### Files Provided (Do Not Modify)

- `models/price_alert.py` - The SQLAlchemy model
- `schemas/price_alert.py` - The Pydantic schemas
- `tests/test_price_alerts.py` - The tests you need to pass

### Hints

- Look at existing services (`services/trading.py`, `services/market.py`) for patterns
- Look at existing routers (`routers/watchlist.py`) for API patterns
- Use `MarketService.get_stock()` to get current stock prices
- Use `HTTPException` from FastAPI for error responses
- The response should include `current_price` - get it from `MarketService.get_stock()`

### Success Criteria

All tests in `tests/test_price_alerts.py` should pass:

```bash
pytest tests/test_price_alerts.py -v
```

---

## Project Structure

```
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration settings
├── database.py             # Database setup
├── data/                   # JSON data files
│   ├── stocks.json         # Stock data
│   ├── users.json          # Sample users
│   ├── holdings.json       # Sample holdings
│   ├── orders.json         # Sample orders
│   └── watchlists.json     # Sample watchlists
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── stock.py
│   ├── portfolio.py
│   ├── order.py
│   ├── watchlist.py
│   └── price_alert.py      # Provided for you
├── schemas/                # Pydantic schemas
│   ├── user.py
│   ├── stock.py
│   ├── portfolio.py
│   ├── order.py
│   ├── watchlist.py
│   └── price_alert.py      # Provided for you
├── services/               # Business logic
│   ├── auth.py
│   ├── market.py
│   ├── trading.py
│   ├── data_loader.py
│   └── price_alerts.py     # TODO: Implement this
├── routers/                # API endpoints
│   ├── auth.py
│   ├── stocks.py
│   ├── trading.py
│   ├── portfolio.py
│   ├── watchlist.py
│   └── price_alerts.py     # TODO: Implement this
└── tests/                  # Tests
    ├── conftest.py         # Test fixtures
    ├── test_auth.py
    ├── test_stocks.py
    ├── test_trading.py
    ├── test_portfolio.py
    ├── test_watchlist.py
    └── test_price_alerts.py  # Tests you need to pass
```

## API Overview

### Existing Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login and get token |
| GET | /auth/me | Get current user |
| GET | /stocks | List all stocks |
| GET | /stocks/{symbol} | Get stock details |
| POST | /orders | Place an order |
| GET | /orders | List orders |
| GET | /portfolio | Get portfolio |
| GET | /watchlist | Get watchlist |

### Endpoints to Implement

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /alerts | Create price alert |
| GET | /alerts | List all alerts |
| GET | /alerts/{id} | Get specific alert |
| DELETE | /alerts/{id} | Delete alert |
| POST | /alerts/check | Check & trigger alerts |

## Testing Your Implementation

```bash
# Quick test
pytest tests/test_price_alerts.py -v

# With coverage
pytest tests/test_price_alerts.py -v --cov=services.price_alerts --cov=routers.price_alerts

# Run a specific test
pytest tests/test_price_alerts.py::TestCreateAlert::test_create_alert_above -v
```

Good luck!
