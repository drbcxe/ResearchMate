import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


@pytest.fixture
def client():
    settings = Settings(
        _env_file=None,
        app_env="test",
        model_base_url="",
        model_name="",
        model_api_key="",
    )
    app.dependency_overrides[get_settings] = lambda: settings

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_settings, None)


def test_health_returns_service_status(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "version": "0.1.0",
    }


def test_settings_status_without_configuration(client):
    response = client.get("/api/settings/status")

    assert response.status_code == 200
    assert response.json() == {
        "model_configured": False,
        "model_name": "",
        "base_url_host": "",
    }


def test_settings_status_does_not_expose_api_key(client):
    fake_key = "test-only-not-a-real-key"
    settings = Settings(
        _env_file=None,
        model_base_url="https://models.example/v1",
        model_name="test-model",
        model_api_key=fake_key,
    )
    app.dependency_overrides[get_settings] = lambda: settings

    response = client.get("/api/settings/status")

    assert response.status_code == 200
    assert response.json() == {
        "model_configured": True,
        "model_name": "test-model",
        "base_url_host": "models.example",
    }
    assert fake_key not in response.text
    assert "model_api_key" not in response.json()
