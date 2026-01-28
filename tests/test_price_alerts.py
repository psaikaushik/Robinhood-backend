"""
Price Alerts Tests

CANDIDATE TASK: Make all these tests pass by implementing the
PriceAlertService and price alerts router.

Run tests with: pytest tests/test_price_alerts.py -v

These tests verify the price alert functionality:
- Creating alerts
- Getting alerts
- Deleting alerts
- Triggering alerts based on price conditions
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
        """Test creating alert for non-existent stock fails."""
        response = authenticated_client.post(
            "/alerts",
            json={
                "symbol": "INVALID",
                "target_price": 100.00,
                "condition": "above"
            }
        )
        assert response.status_code == 404

    def test_create_alert_invalid_condition(self, authenticated_client):
        """Test creating alert with invalid condition fails."""
        response = authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": 100.00,
                "condition": "invalid"
            }
        )
        assert response.status_code == 422  # Validation error

    def test_create_alert_invalid_price(self, authenticated_client):
        """Test creating alert with invalid price fails."""
        response = authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": -50.00,
                "condition": "above"
            }
        )
        assert response.status_code == 422

    def test_create_alert_requires_auth(self, client):
        """Test creating alert requires authentication."""
        response = client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": 200.00,
                "condition": "above"
            }
        )
        assert response.status_code == 401


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

    def test_get_alerts_active_only(self, authenticated_client):
        """Test filtering to only active alerts."""
        # Create an alert
        authenticated_client.post(
            "/alerts",
            json={"symbol": "AAPL", "target_price": 200.00, "condition": "above"}
        )

        response = authenticated_client.get("/alerts?active_only=true")
        assert response.status_code == 200
        data = response.json()
        for alert in data:
            assert alert["is_active"] == True
            assert alert["is_triggered"] == False

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
        """Test getting non-existent alert returns 404."""
        response = authenticated_client.get("/alerts/99999")
        assert response.status_code == 404

    def test_get_alerts_includes_current_price(self, authenticated_client):
        """Test that alerts include current stock price."""
        authenticated_client.post(
            "/alerts",
            json={"symbol": "NVDA", "target_price": 1000.00, "condition": "above"}
        )

        response = authenticated_client.get("/alerts")
        data = response.json()[0]
        assert "current_price" in data
        assert data["current_price"] > 0


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
        """Test deleting non-existent alert returns 404."""
        response = authenticated_client.delete("/alerts/99999")
        assert response.status_code == 404


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
        """Test alert doesn't trigger when conditions aren't met."""
        # Get current AAPL price
        stock_response = authenticated_client.get("/stocks/AAPL")
        current_price = stock_response.json()["current_price"]

        # Create alert with target way above current price
        authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": current_price + 1000,  # Way above
                "condition": "above"
            }
        )

        # Check alerts
        response = authenticated_client.post("/alerts/check")
        assert response.status_code == 200
        triggered = response.json()
        assert len(triggered) == 0

    def test_already_triggered_alert_not_triggered_again(self, authenticated_client):
        """Test that already triggered alerts aren't triggered again."""
        # Get current price
        stock_response = authenticated_client.get("/stocks/AAPL")
        current_price = stock_response.json()["current_price"]

        # Create alert that will trigger
        authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": current_price - 10,
                "condition": "above"
            }
        )

        # First check - should trigger
        response1 = authenticated_client.post("/alerts/check")
        assert len(response1.json()) == 1

        # Second check - should not trigger again
        response2 = authenticated_client.post("/alerts/check")
        assert len(response2.json()) == 0

    def test_triggered_alerts_visible_in_list(self, authenticated_client):
        """Test that triggered alerts appear in the alerts list."""
        # Get current price
        stock_response = authenticated_client.get("/stocks/AAPL")
        current_price = stock_response.json()["current_price"]

        # Create and trigger an alert
        authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": current_price - 10,
                "condition": "above"
            }
        )
        authenticated_client.post("/alerts/check")

        # Get all alerts (not just active)
        response = authenticated_client.get("/alerts")
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_triggered"] == True

    def test_active_only_excludes_triggered(self, authenticated_client):
        """Test that active_only=true excludes triggered alerts."""
        # Get current price
        stock_response = authenticated_client.get("/stocks/AAPL")
        current_price = stock_response.json()["current_price"]

        # Create one that will trigger and one that won't
        authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": current_price - 10,
                "condition": "above"
            }
        )
        authenticated_client.post(
            "/alerts",
            json={
                "symbol": "AAPL",
                "target_price": current_price + 1000,
                "condition": "above"
            }
        )

        # Trigger alerts
        authenticated_client.post("/alerts/check")

        # Get only active alerts
        response = authenticated_client.get("/alerts?active_only=true")
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_triggered"] == False
