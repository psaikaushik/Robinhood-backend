"""Tests for authentication endpoints."""

import pytest


class TestRegistration:
    """Tests for user registration."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepassword123",
                "full_name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["balance"] == 10000.00  # Initial balance
        assert "id" in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",  # Same as test_user
                "username": "differentuser",
                "password": "password123",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "different@example.com",
                "username": "testuser",  # Same as test_user
                "password": "password123",
                "full_name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "already taken" in response.json()["detail"]


class TestLogin:
    """Tests for user login."""

    def test_login_success(self, client, test_user):
        """Test successful login returns token."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails."""
        response = client.post(
            "/auth/login",
            data={"username": "nobody", "password": "password"}
        )
        assert response.status_code == 401


class TestGetCurrentUser:
    """Tests for getting current user info."""

    def test_get_current_user_authenticated(self, authenticated_client):
        """Test getting current user when authenticated."""
        response = authenticated_client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_unauthenticated(self, client):
        """Test getting current user without authentication fails."""
        response = client.get("/auth/me")
        assert response.status_code == 401


class TestAccountOperations:
    """Tests for deposit and withdraw operations."""

    def test_deposit_funds(self, authenticated_client):
        """Test depositing funds to account."""
        initial_response = authenticated_client.get("/auth/me")
        initial_balance = initial_response.json()["balance"]

        response = authenticated_client.post("/auth/deposit?amount=500.00")
        assert response.status_code == 200
        assert response.json()["new_balance"] == initial_balance + 500.00

    def test_deposit_invalid_amount(self, authenticated_client):
        """Test depositing invalid amount fails."""
        response = authenticated_client.post("/auth/deposit?amount=-100")
        assert response.status_code == 400

    def test_withdraw_funds(self, authenticated_client):
        """Test withdrawing funds from account."""
        initial_response = authenticated_client.get("/auth/me")
        initial_balance = initial_response.json()["balance"]

        response = authenticated_client.post("/auth/withdraw?amount=500.00")
        assert response.status_code == 200
        assert response.json()["new_balance"] == initial_balance - 500.00

    def test_withdraw_insufficient_funds(self, authenticated_client):
        """Test withdrawing more than balance fails."""
        response = authenticated_client.post("/auth/withdraw?amount=999999.00")
        assert response.status_code == 400
        assert "Insufficient funds" in response.json()["detail"]
