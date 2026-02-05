# Interviewer Guide - Chaos Engineering Scenarios

This guide helps interviewers run the coding interview and progressively add complexity using chaos scenarios.

## Quick Start

```bash
# Start with default (clean) scenario
python main.py

# Or specify a chaos scenario
SCENARIO=chaos_data python main.py
SCENARIO=chaos_stress python main.py
SCENARIO=chaos_race python main.py
```

## Interview Flow

### Phase 1: Basic Implementation (30-45 min)

Use the **default** scenario. Candidate implements the Price Alerts feature.

```bash
python main.py
```

**What to evaluate:**
- Code structure and organization
- Understanding of FastAPI patterns
- Database operations with SQLAlchemy
- Basic error handling

**When complete:** All provided tests pass.

---

### Phase 2: Chaos Engineering (15-30 min)

Once the candidate completes Phase 1, introduce a chaos scenario.

---

## Available Scenarios

### 1. `chaos_data` - Data Inconsistencies

**Activate:**
```bash
SCENARIO=chaos_data python main.py
```

**What it introduces:**
- `GOOGL` has negative price (-50.25)
- `AMZN` has null price
- `TSLA` has price = 0
- `NVDA` has overflow price (999999999999.99)
- `BROKEN` stock has empty name and missing fields

**Interviewer Prompt:**
> "Great job implementing the basic feature! Now, we've discovered that our stock data feed sometimes has issues - negative prices, missing values, and data corruption. Can you update your implementation to handle these edge cases gracefully? The alerts should not crash or produce incorrect results when encountering bad data."

**Demo Steps:**
1. Start server with `SCENARIO=chaos_data python main.py`
2. Try to create an alert for GOOGL (negative price) or AMZN (null price)
3. Show candidate the error or unexpected behavior
4. Ask them to fix it

**What to evaluate:**
- Defensive programming
- Input validation
- Error handling for edge cases
- Graceful degradation

---

### 2. `chaos_stress` - High Volume (DEMO-ABLE!)

**Activate:**
```bash
SCENARIO=chaos_stress python main.py
```

**What it does:**
- Automatically creates **500 alerts** for user `stresstest` on startup
- Tests performance of check_and_trigger_alerts
- Exposes N+1 query issues and slow implementations

**Demo Steps:**
1. Start server: `SCENARIO=chaos_stress python main.py`
2. Watch the startup logs - you'll see "Creating 500 alerts..."
3. Login as stresstest user:
   ```bash
   curl -X POST http://localhost:8000/auth/login \
     -d "username=stresstest&password=stresstest123"
   ```
4. Call check alerts and time it:
   ```bash
   time curl -X POST http://localhost:8000/alerts/check \
     -H "Authorization: Bearer <token>"
   ```
5. If it's slow, ask candidate to optimize

**Interviewer Prompt:**
> "Your implementation works great for a few alerts. But look at this - we have a power user with 500 alerts. Let me call the check endpoint... [show slow response]. Can you optimize this?"

**What to evaluate:**
- Performance awareness
- Database query optimization (avoid N+1)
- Batch processing concepts

---

### 3. `chaos_race` - Race Conditions (DEMO-ABLE!)

**Activate:**
```bash
SCENARIO=chaos_race python main.py
```

**What it does:**
- Enables `/alerts/check-concurrent` endpoint
- Adds artificial delay (500ms) to make race conditions more likely
- Simulates multiple concurrent check calls

**Demo Steps:**
1. Start server: `SCENARIO=chaos_race python main.py`
2. Login and create a few alerts that will trigger
3. Call the concurrent test endpoint:
   ```bash
   curl -X POST "http://localhost:8000/alerts/check-concurrent?num_concurrent=5" \
     -H "Authorization: Bearer <token>"
   ```
4. Show the response - look for `"race_condition_detected": true`
5. If duplicates found, the same alert was triggered multiple times!

**Example Response (with bug):**
```json
{
  "concurrent_calls": 5,
  "results": [
    {"thread_id": 0, "triggered_count": 1, "triggered_ids": [1]},
    {"thread_id": 1, "triggered_count": 1, "triggered_ids": [1]},
    {"thread_id": 2, "triggered_count": 0, "triggered_ids": []},
    ...
  ],
  "race_condition_detected": true,
  "duplicate_triggers": [1],
  "message": "🐛 RACE CONDITION BUG!"
}
```

**Interviewer Prompt:**
> "I'm going to simulate 5 concurrent requests hitting your check_alerts endpoint. Watch what happens... [run curl]. See that? Alert ID 1 was triggered twice! How would you fix this race condition?"

**What to evaluate:**
- Understanding of concurrency issues
- Database transaction knowledge
- Solutions: SELECT FOR UPDATE, optimistic locking, idempotency

---

## API Endpoints for Interviewers

```bash
# Check current scenario
curl http://localhost:8000/scenario

# List all scenarios
curl http://localhost:8000/scenarios

# Race condition test (only in chaos_race scenario)
curl -X POST "http://localhost:8000/alerts/check-concurrent?num_concurrent=5" \
  -H "Authorization: Bearer <token>"
```

---

## Demo Script for Video

### 1. Show Default Flow
```bash
python main.py
# Show tests, show implementation stubs
pytest tests/test_price_alerts.py -v
```

### 2. Show Chaos Data
```bash
SCENARIO=chaos_data python main.py
curl http://localhost:8000/stocks/GOOGL  # Shows negative price!
```

### 3. Show Chaos Stress
```bash
SCENARIO=chaos_stress python main.py
# Watch 500 alerts being created
# Login as stresstest, call /alerts/check, show it's slow
```

### 4. Show Chaos Race
```bash
SCENARIO=chaos_race python main.py
# Create triggerable alert
# Call /alerts/check-concurrent
# Show race condition detection
```

---

## Evaluation Rubric

### Junior Level
- [ ] Basic implementation works
- [ ] Tests pass
- [ ] Code is readable

### Mid Level
- [ ] All above, plus:
- [ ] Handles basic edge cases
- [ ] Good error messages
- [ ] Writes meaningful tests

### Senior Level
- [ ] All above, plus:
- [ ] Handles chaos_data gracefully
- [ ] Discusses performance implications
- [ ] Understands race condition risks
- [ ] Proposes solutions for distributed scenarios

---

## Troubleshooting

**Tests not running?**
```bash
source .venv/bin/activate
pip uninstall pytest-asyncio -y
pytest tests/test_price_alerts.py -v
```

**Scenario not loading?**
- Make sure to restart the server after changing SCENARIO
- Check that scenario folder exists in `scenarios/`

**Need to reset data?**
- Delete `robinhood.db` and restart server
