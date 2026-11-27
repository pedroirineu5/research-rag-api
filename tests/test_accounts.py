import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.accounts.models import User  # noqa: F401 - registers model in metadata
from app.db import Base, get_db
from main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-with-at-least-thirty-two-characters"
    )
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    def test_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_register_login_refresh_and_me(client: TestClient):
    data = {"email": "Player@example.com", "password": "strong-password"}
    register = client.post("/accounts/register", json=data)
    assert register.status_code == 201
    assert register.json() == {"id": 1, "email": "player@example.com"}

    login = client.post("/accounts/login", json=data)
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["token_type"] == "bearer"

    me = client.get(
        "/accounts/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json() == register.json()

    refresh = client.post(
        "/accounts/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_duplicate_email_and_wrong_password(client: TestClient):
    data = {"email": "player@example.com", "password": "strong-password"}
    assert client.post("/accounts/register", json=data).status_code == 201
    assert client.post("/accounts/register", json=data).status_code == 409
    assert (
        client.post("/accounts/login", json={**data, "password": "x"}).status_code
        == 401
    )


def test_refresh_token_cannot_access_me(client: TestClient):
    data = {"email": "player@example.com", "password": "strong-password"}
    client.post("/accounts/register", json=data)
    tokens = client.post("/accounts/login", json=data).json()

    assert client.get("/accounts/me").status_code == 401
    assert (
        client.get(
            "/accounts/me",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/accounts/refresh", json={"refresh_token": tokens["access_token"]}
        ).status_code
        == 401
    )


def test_password_validation(client: TestClient):
    response = client.post(
        "/accounts/register", json={"email": "player@example.com", "password": "short"}
    )
    assert response.status_code == 422
