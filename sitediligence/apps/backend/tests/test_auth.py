"""Auth endpoint tests — register, login, refresh, me."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from config.database import get_db
from models.base import Base

# ── Test DB (SQLite in-memory) ────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_auth.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

VALID_USER = {
    "email": "test@sitediligence.com",
    "password": "SecurePass123",
    "full_name": "Test User",
}


def register_and_login(client: TestClient) -> str:
    """Register (idempotent) and return a valid access token."""
    client.post("/api/v1/auth/register", json=VALID_USER)
    resp = client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"],
        "password": VALID_USER["password"],
    })
    return resp.json()["access_token"]


# ── Tests: POST /auth/register ────────────────────────────────────────────────

def test_register_success(client: TestClient):
    resp = client.post("/api/v1/auth/register", json=VALID_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == VALID_USER["email"]
    assert body["full_name"] == VALID_USER["full_name"]
    assert body["role"] == "user"
    assert body["plan"] == "free"
    assert "hashed_password" not in body


def test_register_duplicate_email(client: TestClient):
    resp = client.post("/api/v1/auth/register", json=VALID_USER)
    assert resp.status_code == 409


def test_register_weak_password(client: TestClient):
    resp = client.post("/api/v1/auth/register", json={
        "email": "weak@test.com", "password": "short", "full_name": "Weak"
    })
    assert resp.status_code == 422


def test_register_invalid_email(client: TestClient):
    resp = client.post("/api/v1/auth/register", json={
        "email": "not-an-email", "password": "ValidPass1", "full_name": "Bad Email"
    })
    assert resp.status_code == 422


# ── Tests: POST /auth/login ───────────────────────────────────────────────────

def test_login_success(client: TestClient):
    resp = client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"],
        "password": VALID_USER["password"],
    })
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    resp = client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"],
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient):
    resp = client.post("/api/v1/auth/login", json={
        "email": "nobody@nowhere.com",
        "password": "SomePass123",
    })
    assert resp.status_code == 401


# ── Tests: POST /auth/refresh ─────────────────────────────────────────────────

def test_refresh_success(client: TestClient):
    login_resp = client.post("/api/v1/auth/login", json={
        "email": VALID_USER["email"],
        "password": VALID_USER["password"],
    })
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_refresh_with_access_token_fails(client: TestClient):
    """An access token must not be accepted as a refresh token."""
    access_token = register_and_login(client)
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


def test_refresh_invalid_token(client: TestClient):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage.token.here"})
    assert resp.status_code == 401


# ── Tests: GET /auth/me ───────────────────────────────────────────────────────

def test_me_authenticated(client: TestClient):
    token = register_and_login(client)
    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == VALID_USER["email"]
    assert body["full_name"] == VALID_USER["full_name"]


def test_me_no_token(client: TestClient):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


def test_me_invalid_token(client: TestClient):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert resp.status_code == 401


# ── Tests: middleware protection ──────────────────────────────────────────────

def test_protected_route_no_auth(client: TestClient):
    resp = client.get("/api/v1/projects/")
    assert resp.status_code == 401


def test_protected_route_with_auth(client: TestClient):
    token = register_and_login(client)
    resp = client.get("/api/v1/projects/", headers={"Authorization": f"Bearer {token}"})
    # 200 (empty list) — the route is implemented and returns []
    assert resp.status_code == 200


def test_health_is_public(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_docs_is_public(client: TestClient):
    resp = client.get("/docs")
    assert resp.status_code == 200
