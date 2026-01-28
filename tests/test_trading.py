"""Tests for trading endpoints."""

import pytest


class TestPlaceOrder:
    """Tests for placing buy/sell orders."""

    def test_buy_market_order(self, rich_authenticated_client):
        """Test placing a market buy order."""
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 5
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["side"] == "buy"
        assert data["quantity"] == 5
        assert data["status"] == "filled"
        assert data["filled_quantity"] == 5
        assert data["filled_price"] > 0

    def test_buy_limit_order(self, rich_authenticated_client):
        """Test placing a limit buy order."""
        # Get current price
        stock_response = rich_authenticated_client.get("/stocks/AAPL")
        current_price = stock_response.json()["current_price"]

        # Place limit order above current price (should fill immediately)
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "limit",
                "side": "buy",
                "quantity": 3,
                "limit_price": current_price + 10
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "filled"

    def test_buy_limit_order_pending(self, rich_authenticated_client):
        """Test limit order stays pending when price not met."""
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "limit",
                "side": "buy",
                "quantity": 2,
                "limit_price": 1.00  # Way below market price
            }
        )
        assert response.status_code == 201
        assert response.json()["status"] == "pending"

    def test_sell_order(self, rich_authenticated_client):
        """Test selling shares after buying."""
        # First buy some shares
        buy_response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "GOOGL",
                "order_type": "market",
                "side": "buy",
                "quantity": 10
            }
        )
        assert buy_response.status_code == 201

        # Now sell some
        sell_response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "GOOGL",
                "order_type": "market",
                "side": "sell",
                "quantity": 5
            }
        )
        assert sell_response.status_code == 201
        assert sell_response.json()["status"] == "filled"

    def test_sell_insufficient_shares(self, rich_authenticated_client):
        """Test selling more shares than owned fails."""
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "NVDA",
                "order_type": "market",
                "side": "sell",
                "quantity": 1000  # Don't own any
            }
        )
        assert response.status_code == 400
        assert "Insufficient shares" in response.json()["detail"]

    def test_buy_insufficient_funds(self, authenticated_client):
        """Test buying with insufficient funds fails."""
        response = authenticated_client.post(
            "/orders",
            json={
                "symbol": "NVDA",
                "order_type": "market",
                "side": "buy",
                "quantity": 1000  # NVDA is expensive, this will exceed balance
            }
        )
        assert response.status_code == 400
        assert "Insufficient funds" in response.json()["detail"]

    def test_buy_invalid_stock(self, rich_authenticated_client):
        """Test buying non-existent stock fails."""
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "INVALID",
                "order_type": "market",
                "side": "buy",
                "quantity": 1
            }
        )
        assert response.status_code == 404

    def test_invalid_order_type(self, rich_authenticated_client):
        """Test invalid order type fails validation."""
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "invalid",
                "side": "buy",
                "quantity": 1
            }
        )
        assert response.status_code == 422  # Validation error

    def test_invalid_side(self, rich_authenticated_client):
        """Test invalid side fails validation."""
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "invalid",
                "quantity": 1
            }
        )
        assert response.status_code == 422

    def test_negative_quantity(self, rich_authenticated_client):
        """Test negative quantity fails validation."""
        response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": -5
            }
        )
        assert response.status_code == 422


class TestGetOrders:
    """Tests for retrieving orders."""

    def test_get_all_orders(self, rich_authenticated_client):
        """Test getting all orders for user."""
        # Place an order first
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 1
            }
        )

        response = rich_authenticated_client.get("/orders")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_orders_by_status(self, rich_authenticated_client):
        """Test filtering orders by status."""
        # Place a limit order that will be pending
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "limit",
                "side": "buy",
                "quantity": 1,
                "limit_price": 1.00
            }
        )

        response = rich_authenticated_client.get("/orders?status=pending")
        assert response.status_code == 200
        data = response.json()
        for order in data:
            assert order["status"] == "pending"

    def test_get_order_by_id(self, rich_authenticated_client):
        """Test getting a specific order by ID."""
        # Place an order
        create_response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "MSFT",
                "order_type": "market",
                "side": "buy",
                "quantity": 2
            }
        )
        order_id = create_response.json()["id"]

        response = rich_authenticated_client.get(f"/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["id"] == order_id


class TestCancelOrder:
    """Tests for cancelling orders."""

    def test_cancel_pending_order(self, rich_authenticated_client):
        """Test cancelling a pending limit order."""
        # Place a limit order that will be pending
        create_response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "limit",
                "side": "buy",
                "quantity": 1,
                "limit_price": 1.00
            }
        )
        order_id = create_response.json()["id"]

        # Cancel the order
        response = rich_authenticated_client.delete(f"/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cancel_filled_order_fails(self, rich_authenticated_client):
        """Test that cancelling a filled order fails."""
        # Place a market order (immediately filled)
        create_response = rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 1
            }
        )
        order_id = create_response.json()["id"]

        # Try to cancel
        response = rich_authenticated_client.delete(f"/orders/{order_id}")
        assert response.status_code == 400
        assert "Cannot cancel" in response.json()["detail"]

    def test_cancel_nonexistent_order(self, rich_authenticated_client):
        """Test cancelling non-existent order fails."""
        response = rich_authenticated_client.delete("/orders/99999")
        assert response.status_code == 404
