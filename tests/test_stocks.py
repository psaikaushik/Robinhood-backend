"""Tests for stock endpoints."""

import pytest


class TestGetStocks:
    """Tests for retrieving stock data."""

    def test_get_all_stocks(self, client):
        """Test getting all available stocks."""
        response = client.get("/stocks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check stock structure
        stock = data[0]
        assert "symbol" in stock
        assert "name" in stock
        assert "current_price" in stock
        assert "change" in stock
        assert "change_percent" in stock

    def test_get_stock_by_symbol(self, client):
        """Test getting a specific stock by symbol."""
        response = client.get("/stocks/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["name"] == "Apple Inc."
        assert data["current_price"] > 0

    def test_get_stock_case_insensitive(self, client):
        """Test that stock lookup is case insensitive."""
        response = client.get("/stocks/aapl")
        assert response.status_code == 200
        assert response.json()["symbol"] == "AAPL"

    def test_get_stock_not_found(self, client):
        """Test getting non-existent stock returns 404."""
        response = client.get("/stocks/INVALID")
        assert response.status_code == 404

    def test_get_stock_quote(self, client):
        """Test getting a quick quote for a stock."""
        response = client.get("/stocks/MSFT/quote")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "MSFT"
        assert "price" in data
        assert "change" in data
        assert "change_percent" in data


class TestSearchStocks:
    """Tests for stock search functionality."""

    def test_search_by_symbol(self, client):
        """Test searching stocks by symbol."""
        response = client.get("/stocks/search?q=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(s["symbol"] == "AAPL" for s in data)

    def test_search_by_name(self, client):
        """Test searching stocks by company name."""
        response = client.get("/stocks/search?q=Apple")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("Apple" in s["name"] for s in data)

    def test_search_partial_match(self, client):
        """Test searching with partial match."""
        response = client.get("/stocks/search?q=micro")
        assert response.status_code == 200
        data = response.json()
        # Should match Microsoft and/or AMD (Advanced Micro Devices)
        assert len(data) >= 1

    def test_search_no_results(self, client):
        """Test search with no results returns empty list."""
        response = client.get("/stocks/search?q=xyznotfound")
        assert response.status_code == 200
        assert response.json() == []


class TestPriceSimulation:
    """Tests for price simulation (requires authentication)."""

    def test_simulate_price_change(self, authenticated_client):
        """Test simulating price change for a stock."""
        # Get initial price
        initial = authenticated_client.get("/stocks/AAPL")
        initial_price = initial.json()["current_price"]

        # Simulate change
        response = authenticated_client.post("/stocks/AAPL/simulate")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "new_price" in data
        # Price should have changed (within +/- 2%)
        assert abs(data["new_price"] - initial_price) / initial_price <= 0.02

    def test_simulate_all_prices(self, authenticated_client):
        """Test simulating price changes for all stocks."""
        response = authenticated_client.post("/stocks/simulate-all")
        assert response.status_code == 200
        assert "Simulated" in response.json()["message"]

    def test_simulate_requires_auth(self, client):
        """Test that simulation requires authentication."""
        response = client.post("/stocks/AAPL/simulate")
        assert response.status_code == 401
