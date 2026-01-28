import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from services.market import MarketService
from services.auth import AuthService
from models.user import User


# Test database - in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Initialize stocks in test database
    MarketService.initialize_stocks(db_session)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    from schemas.user import UserCreate

    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="testpassword123",
        full_name="Test User"
    )
    user = AuthService.create_user(db_session, user_data)
    return user


@pytest.fixture(scope="function")
def authenticated_client(client, test_user):
    """Create a test client with authentication."""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture(scope="function")
def rich_user(db_session):
    """Create a test user with more money for trading tests."""
    from schemas.user import UserCreate

    user_data = UserCreate(
        email="rich@example.com",
        username="richuser",
        password="richpassword123",
        full_name="Rich User"
    )
    user = AuthService.create_user(db_session, user_data)
    user.balance = 100000.00  # $100k for testing
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def rich_authenticated_client(client, rich_user):
    """Create a test client with authentication for rich user."""
    response = client.post(
        "/auth/login",
        data={"username": "richuser", "password": "richpassword123"}
    )
    token = response.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
