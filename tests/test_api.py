"""Tests for FastAPI endpoints."""
import os
import pytest
from fastapi.testclient import TestClient
from dotenv import dotenv_values

# Load .env before importing modules that use get_settings()
env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_file):
    env_vars = dotenv_values(env_file)
    os.environ.update({k: v for k, v in env_vars.items() if v is not None})

from risk_analyzer.api import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint returns API information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "Risk Analyzer API"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "risk-analyzer"


@pytest.mark.integration
def test_analyze_endpoint_real():
    """Test analyze endpoint with real Joget data."""
    folio_id = "34666095-2358-4109-a63d-abaf8c215e82"
    response = client.post(f"/analyze/{folio_id}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "folio_id" in data
    assert "folio" in data
    assert "signals" in data
    assert "risk" in data
    assert "report" in data
    
    # Verify folio data
    assert data["folio_id"] == folio_id
    assert data["folio"]["folio_id"] == "WFE-123"
    
    # Verify risk assessment
    assert "score" in data["risk"]
    assert "level" in data["risk"]
    assert "baseline_score" in data["risk"]
    assert "llm_delta" in data["risk"]
    assert data["risk"]["level"] in ["bajo", "medio", "alto"]
    
    # Verify report is generated
    assert isinstance(data["report"], str)
    assert len(data["report"]) > 0


@pytest.mark.integration
def test_analyze_endpoint_invalid_folio():
    """Test analyze endpoint with invalid folio ID."""
    folio_id = "nonexistent-folio-id"
    response = client.post(f"/analyze/{folio_id}")
    
    # Should return 500 error when folio not found
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
