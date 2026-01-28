"""Tests for watchlist endpoints."""

import pytest


class TestWatchlist:
    """Tests for watchlist functionality."""

    def test_get_empty_watchlist(self, authenticated_client):
        """Test getting empty watchlist."""
        response = authenticated_client.get("/watchlist")
        assert response.status_code == 200
        assert response.json() == []

    def test_add_to_watchlist(self, authenticated_client):
        """Test adding a stock to watchlist."""
        response = authenticated_client.post(
            "/watchlist",
            json={"symbol": "AAPL"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert "current_price" in data
        assert "id" in data

    def test_add_multiple_to_watchlist(self, authenticated_client):
        """Test adding multiple stocks to watchlist."""
        authenticated_client.post("/watchlist", json={"symbol": "AAPL"})
        authenticated_client.post("/watchlist", json={"symbol": "GOOGL"})
        authenticated_client.post("/watchlist", json={"symbol": "MSFT"})

        response = authenticated_client.get("/watchlist")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        symbols = [item["symbol"] for item in data]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols
        assert "MSFT" in symbols

    def test_add_duplicate_to_watchlist(self, authenticated_client):
        """Test adding duplicate stock to watchlist fails."""
        authenticated_client.post("/watchlist", json={"symbol": "AAPL"})

        response = authenticated_client.post(
            "/watchlist",
            json={"symbol": "AAPL"}
        )
        assert response.status_code == 400
        assert "already in your watchlist" in response.json()["detail"]

    def test_add_invalid_stock_to_watchlist(self, authenticated_client):
        """Test adding non-existent stock to watchlist fails."""
        response = authenticated_client.post(
            "/watchlist",
            json={"symbol": "INVALID"}
        )
        assert response.status_code == 404

    def test_remove_from_watchlist(self, authenticated_client):
        """Test removing a stock from watchlist."""
        # Add first
        authenticated_client.post("/watchlist", json={"symbol": "TSLA"})

        # Remove
        response = authenticated_client.delete("/watchlist/TSLA")
        assert response.status_code == 204

        # Verify removed
        watchlist = authenticated_client.get("/watchlist")
        symbols = [item["symbol"] for item in watchlist.json()]
        assert "TSLA" not in symbols

    def test_remove_nonexistent_from_watchlist(self, authenticated_client):
        """Test removing stock not in watchlist fails."""
        response = authenticated_client.delete("/watchlist/AAPL")
        assert response.status_code == 404

    def test_watchlist_case_insensitive(self, authenticated_client):
        """Test that watchlist symbols are case insensitive."""
        # Add with lowercase
        response = authenticated_client.post(
            "/watchlist",
            json={"symbol": "aapl"}
        )
        assert response.status_code == 201
        assert response.json()["symbol"] == "AAPL"

        # Try to add uppercase (should fail as duplicate)
        response = authenticated_client.post(
            "/watchlist",
            json={"symbol": "AAPL"}
        )
        assert response.status_code == 400

    def test_watchlist_shows_price_data(self, authenticated_client):
        """Test that watchlist includes price data."""
        authenticated_client.post("/watchlist", json={"symbol": "NVDA"})

        response = authenticated_client.get("/watchlist")
        data = response.json()[0]

        assert "current_price" in data
        assert "change" in data
        assert "change_percent" in data
        assert data["current_price"] > 0
