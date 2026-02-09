"""
Tests for api/main.py

Covers:
- Health check endpoint
- Analysis retrieval endpoint (404 case)
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app, analyses_cache


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_cache():
    analyses_cache.clear()
    yield
    analyses_cache.clear()


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_body(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["version"] == "4.0"
        assert data["name"] == "Digital Smarty"


class TestAnalysisEndpoint:
    def test_missing_analysis_returns_404(self, client):
        response = client.get("/api/analysis/nonexistent")
        assert response.status_code == 404

    def test_existing_analysis_returns_data(self, client):
        analyses_cache["test-id"] = {"summary": "Test analysis"}
        response = client.get("/api/analysis/test-id")
        assert response.status_code == 200
        assert response.json()["summary"] == "Test analysis"
