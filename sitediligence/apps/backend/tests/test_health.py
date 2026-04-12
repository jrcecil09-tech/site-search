"""Tests for the /health endpoint."""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_schema():
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "environment" in body


def test_root_returns_200():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "docs" in body


def test_docs_available():
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_json():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "SiteDiligence API"
