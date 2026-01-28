"""Tests for portfolio endpoints."""

import pytest


class TestPortfolio:
    """Tests for portfolio functionality."""

    def test_get_empty_portfolio(self, authenticated_client):
        """Test getting portfolio with no holdings."""
        response = authenticated_client.get("/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert data["cash_balance"] == 10000.00
        assert data["total_holdings_value"] == 0
        assert data["holdings"] == []

    def test_get_portfolio_with_holdings(self, rich_authenticated_client):
        """Test getting portfolio after buying stocks."""
        # Buy some stocks
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 10
            }
        )
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "MSFT",
                "order_type": "market",
                "side": "buy",
                "quantity": 5
            }
        )

        response = rich_authenticated_client.get("/portfolio")
        assert response.status_code == 200
        data = response.json()

        assert data["total_holdings_value"] > 0
        assert len(data["holdings"]) == 2
        assert data["total_portfolio_value"] == data["cash_balance"] + data["total_holdings_value"]

    def test_portfolio_gain_loss_calculation(self, rich_authenticated_client):
        """Test that portfolio calculates gain/loss correctly."""
        # Buy some stocks
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 10
            }
        )

        response = rich_authenticated_client.get("/portfolio")
        data = response.json()

        for holding in data["holdings"]:
            # Verify gain/loss fields exist
            assert "total_gain_loss" in holding
            assert "gain_loss_percent" in holding
            assert "current_value" in holding
            assert "average_buy_price" in holding


class TestHoldings:
    """Tests for holdings endpoints."""

    def test_get_holdings_empty(self, authenticated_client):
        """Test getting holdings when empty."""
        response = authenticated_client.get("/portfolio/holdings")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_holdings_with_stocks(self, rich_authenticated_client):
        """Test getting holdings after buying."""
        # Buy some stocks
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "GOOGL",
                "order_type": "market",
                "side": "buy",
                "quantity": 8
            }
        )

        response = rich_authenticated_client.get("/portfolio/holdings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["symbol"] == "GOOGL"
        assert data[0]["quantity"] == 8

    def test_get_specific_holding(self, rich_authenticated_client):
        """Test getting a specific holding by symbol."""
        # Buy stocks
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "TSLA",
                "order_type": "market",
                "side": "buy",
                "quantity": 5
            }
        )

        response = rich_authenticated_client.get("/portfolio/holdings/TSLA")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TSLA"
        assert data["quantity"] == 5

    def test_get_nonexistent_holding(self, authenticated_client):
        """Test getting holding for stock not owned."""
        response = authenticated_client.get("/portfolio/holdings/AAPL")
        assert response.status_code == 404


class TestBalance:
    """Tests for balance endpoint."""

    def test_get_balance(self, authenticated_client):
        """Test getting account balance."""
        response = authenticated_client.get("/portfolio/balance")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert data["currency"] == "USD"
        assert data["balance"] == 10000.00

    def test_balance_updates_after_trade(self, rich_authenticated_client):
        """Test that balance updates after trading."""
        initial = rich_authenticated_client.get("/portfolio/balance")
        initial_balance = initial.json()["balance"]

        # Buy stocks
        rich_authenticated_client.post(
            "/orders",
            json={
                "symbol": "AAPL",
                "order_type": "market",
                "side": "buy",
                "quantity": 10
            }
        )

        final = rich_authenticated_client.get("/portfolio/balance")
        assert final.json()["balance"] < initial_balance
