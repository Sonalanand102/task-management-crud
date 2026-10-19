"""Tests for the application health endpoint."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_check(monkeypatch) -> None:
    """The health endpoint confirms that the application is running."""

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://task_user:task_password@localhost:5432/task_management",
    )

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
