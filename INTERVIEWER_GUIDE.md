# Interviewer Guide - Chaos Engineering Scenarios

This guide helps interviewers run the coding interview and progressively add complexity using chaos scenarios.

## Quick Start

```bash
# Start with default (clean) scenario
python main.py

# Or specify a chaos scenario
SCENARIO=chaos_data python main.py
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

**What to evaluate:**
- Defensive programming
- Input validation
- Error handling for edge cases
- Graceful degradation

**Good answers include:**
- Validate price > 0 before creating alert
- Skip stocks with null/invalid prices during check
- Return meaningful errors for invalid data
- Log warnings for data issues

---

### 2. `chaos_stress` - High Volume

**Activate:**
```bash
SCENARIO=chaos_stress python main.py
```

**Interviewer Prompt:**
> "Your implementation works great for a few alerts. But we have power users with hundreds of alerts. How would you optimize `check_and_trigger_alerts` to handle this efficiently? Think about database query optimization."

**What to evaluate:**
- Performance awareness
- Database query optimization
- Batch processing concepts

**Good answers include:**
- Batch database updates instead of one-by-one
- Efficient queries (avoid N+1)
- Discussion of pagination for large result sets
- Consider async processing for very large volumes

---

### 3. `chaos_race` - Race Conditions (Discussion)

**Activate:**
```bash
SCENARIO=chaos_race python main.py
```

**Interviewer Prompt:**
> "Imagine two instances of our service call `check_alerts` at the exact same time for the same user. Could an alert be triggered twice? How would you prevent this?"

**What to evaluate:**
- Understanding of concurrency issues
- Database transaction knowledge
- Distributed systems awareness

**Good answers include:**
- Database transactions with proper isolation
- Optimistic locking (check is_triggered before update)
- SELECT FOR UPDATE pattern
- Idempotency discussion
- Distributed locks for multi-instance scenarios

---

## API Endpoints for Interviewers

Check current scenario:
```bash
curl http://localhost:8000/scenario
```

List all scenarios:
```bash
curl http://localhost:8000/scenarios
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
