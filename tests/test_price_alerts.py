"""
Price Alerts Tests

CANDIDATE TASK:
1. Implement the PriceAlertService and router to make the PROVIDED tests pass
2. Write the MISSING tests marked with "TODO: Candidate should write this test"

Run tests with: pytest tests/test_price_alerts.py -v
"""

import pytest


class TestCreateAlert:
    """Tests for creating price alerts."""

    def test_create_alert_above(self, authenticated_client):
        """Test creating an alert for when price goes above target."""
        response = authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": 200.00,
                "condition": "above"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["target_price"] == 200.00
        assert data["condition"] == "above"
        assert data["is_triggered"] == False
        assert data["is_active"] == True
        assert "id" in data
        assert "current_price" in data

    def test_create_alert_below(self, authenticated_client):
        """Test creating an alert for when price goes below target."""
        response = authenticated_client.post(
            "/alerts",
            json={
                "symbol": "TSLA",
                "target_price": 200.00,
                "condition": "below"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["condition"] == "below"

    def test_create_alert_invalid_symbol(self, authenticated_client):
        """
        TODO: Candidate should write this test

        Test that creating an alert for a non-existent stock symbol
        returns a 404 error.

        Hint: Try creating an alert with symbol "INVALID"
        """
        pass  # Remove pass and implement the test

    def test_create_alert_requires_auth(self, client):
        """
        TODO: Candidate should write this test

        Test that creating an alert without authentication
        returns a 401 error.

        Hint: Use 'client' fixture (not 'authenticated_client')
        """
        pass  # Remove pass and implement the test


class TestGetAlerts:
    """Tests for retrieving price alerts."""

    def test_get_alerts_empty(self, authenticated_client):
        """Test getting alerts when none exist."""
        response = authenticated_client.get("/alerts")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_alerts_with_data(self, authenticated_client):
        """Test getting alerts after creating some."""
        # Create alerts
        authenticated_client.post(
            "/alerts",
            json={"symbol": "AAPL", "target_price": 200.00, "condition": "above"}
        )
        authenticated_client.post(
            "/alerts",
            json={"symbol": "GOOGL", "target_price": 100.00, "condition": "below"}
        )

        response = authenticated_client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_alert_by_id(self, authenticated_client):
        """Test getting a specific alert by ID."""
        # Create alert
        create_response = authenticated_client.post(
            "/alerts",
            json={"symbol": "MSFT", "target_price": 400.00, "condition": "above"}
        )
        alert_id = create_response.json()["id"]

        response = authenticated_client.get(f"/alerts/{alert_id}")
        assert response.status_code == 200
        assert response.json()["id"] == alert_id
        assert response.json()["symbol"] == "MSFT"

    def test_get_alert_not_found(self, authenticated_client):
        """
        TODO: Candidate should write this test

        Test that getting a non-existent alert (e.g., ID 99999)
        returns a 404 error.
        """
        pass  # Remove pass and implement the test

    def test_get_alerts_includes_current_price(self, authenticated_client):
        """
        TODO: Candidate should write this test

        Test that when retrieving alerts, each alert includes
        the current stock price (current_price field > 0).

        Hint: Create an alert, then GET /alerts and check the response
        """
        pass  # Remove pass and implement the test


class TestDeleteAlert:
    """Tests for deleting price alerts."""

    def test_delete_alert(self, authenticated_client):
        """Test deleting an alert."""
        # Create alert
        create_response = authenticated_client.post(
            "/alerts",
            json={"symbol": "AAPL", "target_price": 200.00, "condition": "above"}
        )
        alert_id = create_response.json()["id"]

        # Delete it
        response = authenticated_client.delete(f"/alerts/{alert_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = authenticated_client.get(f"/alerts/{alert_id}")
        assert get_response.status_code == 404

    def test_delete_alert_not_found(self, authenticated_client):
        """
        TODO: Candidate should write this test

        Test that deleting a non-existent alert returns 404.
        """
        pass  # Remove pass and implement the test


class TestTriggerAlerts:
    """Tests for triggering price alerts."""

    def test_trigger_alert_above(self, authenticated_client):
        """Test alert triggers when price is above target."""
        # Get current AAPL price
        stock_response = authenticated_client.get("/stocks/AAPL")
        current_price = stock_response.json()["current_price"]

        # Create alert with target below current price (should trigger)
        authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": current_price - 10,  # Below current
                "condition": "above"
            }
        )

        # Check alerts
        response = authenticated_client.post("/alerts/check")
        assert response.status_code == 200
        triggered = response.json()
        assert len(triggered) == 1
        assert triggered[0]["is_triggered"] == True
        assert triggered[0]["triggered_at"] is not None

    def test_trigger_alert_below(self, authenticated_client):
        """Test alert triggers when price is below target."""
        # Get current AAPL price
        stock_response = authenticated_client.get("/stocks/AAPL")
        current_price = stock_response.json()["current_price"]

        # Create alert with target above current price (should trigger for "below")
        authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": current_price + 10,  # Above current
                "condition": "below"
            }
        )

        # Check alerts
        response = authenticated_client.post("/alerts/check")
        assert response.status_code == 200
        triggered = response.json()
        assert len(triggered) == 1
        assert triggered[0]["is_triggered"] == True

    def test_alert_not_triggered_when_condition_not_met(self, authenticated_client):
        """
        TODO: Candidate should write this test

        Test that an alert does NOT trigger when the condition is not met.

        Example: Create an alert for AAPL to trigger when price goes ABOVE
        (current_price + 1000). Since price is below target, it should NOT trigger.

        Hint: POST /alerts/check should return an empty list
        """
        pass  # Remove pass and implement the test

    def test_already_triggered_alert_not_triggered_again(self, authenticated_client):
        """
        TODO: Candidate should write this test

        Test that an alert that has already been triggered
        is NOT triggered again on subsequent checks.

        Steps:
        1. Create an alert that will trigger immediately
        2. Call POST /alerts/check - should return 1 triggered alert
        3. Call POST /alerts/check again - should return 0 (already triggered)
        """
        pass  # Remove pass and implement the test

    def test_active_only_excludes_triggered(self, authenticated_client):
        """
        TODO: Candidate should write this test

        Test that GET /alerts?active_only=true excludes triggered alerts.

        Steps:
        1. Create two alerts - one that will trigger, one that won't
        2. Call POST /alerts/check to trigger one
        3. Call GET /alerts?active_only=true
        4. Verify only the non-triggered alert is returned
        """
        pass  # Remove pass and implement the test
