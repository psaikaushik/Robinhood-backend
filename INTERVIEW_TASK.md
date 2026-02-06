# Robinhood Backend - Interview Coding Task

## Welcome!

This is a lightweight Robinhood-style stock trading backend built with Python and FastAPI. Your task is to implement a new feature: **Price Alerts**.

---

## Getting Started

Your coding environment is already set up in the browser - no local installation needed!

### The Interface

- **Left Panel**: VS Code editor with the codebase
- **Right Panel**: Claude AI assistant (feel free to ask questions!)
- **Terminal**: Click `Terminal > New Terminal` in VS Code to run commands

### Step 1: Verify Setup

Open a terminal in VS Code (press `` Ctrl+` ``) and run:

```bash
pytest tests/test_price_alerts.py -v
```

You should see tests failing - that's expected! Your job is to make them pass.

### Step 2: Run the Server (Optional)

To explore the API interactively:

```bash
python main.py
```

Then open http://localhost:8000/docs to see the API documentation.

### Using AI Assistance

The **Claude AI** assistant is available in the right sidebar. You can:
- Ask questions about the codebase
- Get help debugging errors
- Discuss your approach

Feel free to use it as a resource!

---

## Your Task

You have **two objectives**:

### Part 1: Implement the Price Alerts Feature

Users want to be notified when a stock reaches a certain price. Implement the feature to make the **provided tests pass**.

### Part 2: Write Missing Tests

Some tests in `test_price_alerts.py` are marked as **TODO**. You need to write these tests yourself. Look for:

```python
def test_something(self, authenticated_client):
    """
    TODO: Candidate should write this test
    ...
    """
    pass  # Remove pass and implement the test
```

---

## Part 1 Requirements

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

1. **All provided tests pass** (tests without TODO comments)
2. **All TODO tests are implemented** and pass

```bash
pytest tests/test_price_alerts.py -v
```

You should see **0 failed, 0 skipped** when complete.

---

## Project Structure

```
├── main.py                 # FastAPI application entry point
├── database.py             # Database setup
├── data/                   # JSON data files
│   ├── stocks.json         # Stock data
│   ├── users.json          # Sample users
│   └── ...
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── stock.py
│   └── price_alert.py      # Provided for you
├── schemas/                # Pydantic schemas
│   └── price_alert.py      # Provided for you
├── services/               # Business logic
│   ├── market.py           # Reference implementation
│   ├── trading.py          # Reference implementation
│   └── price_alerts.py     # TODO: Implement this
├── routers/                # API endpoints
│   ├── watchlist.py        # Reference implementation
│   └── price_alerts.py     # TODO: Implement this
└── tests/
    └── test_price_alerts.py  # Tests you need to pass
```

## API Overview

### Existing Endpoints (for reference)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Register new user |
| POST | /auth/login | Login and get token |
| GET | /stocks | List all stocks |
| GET | /stocks/{symbol} | Get stock details |
| POST | /orders | Place an order |
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

## Quick Reference

```bash
# Run tests
pytest tests/test_price_alerts.py -v

# Run specific test
pytest tests/test_price_alerts.py::TestCreateAlert::test_create_alert_above -v

# Start server
python main.py

# API docs
http://localhost:8000/docs
```

---

Good luck! Ask the AI assistant if you get stuck.
