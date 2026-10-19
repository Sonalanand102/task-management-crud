"""API tests for creating and listing tasks."""

from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.main import app


class FakeCursor:
    """Small in-memory cursor used to test routes without PostgreSQL."""

    def __init__(self, pool: "FakePool") -> None:
        self.pool = pool
        self.row: dict[str, Any] | None = None

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def execute(self, query: str, parameters: tuple[Any, ...] | None = None) -> None:
        if "INSERT INTO tasks" in query:
            title, description, priority = parameters or ()
            now = datetime.now(UTC)
            self.row = {
                "id": len(self.pool.tasks) + 1,
                "title": title,
                "description": description,
                "priority": priority,
                "is_completed": False,
                "created_at": now,
                "updated_at": now,
            }
            self.pool.tasks.append(self.row)
        elif "UPDATE tasks" in query:
            fields = [
                field_name
                for field_name in ("title", "description", "priority", "is_completed")
                if f"{field_name} = %s" in query
            ]
            values = parameters or ()
            task_id = values[-1]
            self.row = next((task for task in self.pool.tasks if task["id"] == task_id), None)
            if self.row is not None:
                self.row.update(dict(zip(fields, values[:-1], strict=True)))
                self.row["updated_at"] = datetime.now(UTC)
        elif "DELETE FROM tasks" in query:
            task_id = (parameters or (None,))[0]
            self.row = next((task for task in self.pool.tasks if task["id"] == task_id), None)
            if self.row is not None:
                self.pool.tasks.remove(self.row)
        elif "WHERE id = %s" in query:
            task_id = (parameters or (None,))[0]
            self.row = next((task for task in self.pool.tasks if task["id"] == task_id), None)

    def fetchone(self) -> dict[str, Any] | None:
        return self.row

    def fetchall(self) -> list[dict[str, Any]]:
        return self.pool.tasks


class FakeConnection:
    """Connection context manager that returns an in-memory cursor."""

    def __init__(self, pool: "FakePool") -> None:
        self.pool = pool

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None

    def cursor(self, **_: object) -> FakeCursor:
        return FakeCursor(self.pool)


class FakePool:
    """Pool-shaped object that stores task rows in memory for API tests."""

    def __init__(self) -> None:
        self.tasks: list[dict[str, Any]] = []

    def connection(self) -> FakeConnection:
        return FakeConnection(self)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Start the app and replace its PostgreSQL pool with a test double."""

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://task_user:task_password@localhost:5432/task_management",
    )

    with TestClient(app) as test_client:
        app.state.db_pool = FakePool()
        yield test_client


def test_create_task_returns_created_task(client: TestClient) -> None:
    """A valid task is stored and returned with a 201 response."""

    response = client.post(
        "/api/v1/tasks",
        json={"title": "Write workshop exercises", "description": "Create examples.", "priority": "high"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["title"] == "Write workshop exercises"
    assert body["description"] == "Create examples."
    assert body["priority"] == "high"
    assert body["is_completed"] is False
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "   "},
        {"title": "x" * 201},
        {"title": "Valid title", "priority": "urgent"},
    ],
)
def test_create_task_rejects_invalid_input(client: TestClient, payload: dict[str, str]) -> None:
    """Invalid title and priority values receive FastAPI validation errors."""

    response = client.post("/api/v1/tasks", json=payload)

    assert response.status_code == 422


def test_list_tasks_returns_empty_list_when_no_tasks_exist(client: TestClient) -> None:
    """Listing a new task collection returns an empty JSON list."""

    response = client.get("/api/v1/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_multiple_tasks(client: TestClient) -> None:
    """Tasks are listed in insertion order."""

    client.post("/api/v1/tasks", json={"title": "First task"})
    client.post("/api/v1/tasks", json={"title": "Second task", "priority": "low"})

    response = client.get("/api/v1/tasks")

    assert response.status_code == 200
    assert [task["title"] for task in response.json()] == ["First task", "Second task"]
    assert [task["priority"] for task in response.json()] == ["medium", "low"]


def test_get_task_returns_a_task(client: TestClient) -> None:
    """A task can be fetched by its identity value."""

    created = client.post("/api/v1/tasks", json={"title": "Read the guide"}).json()

    response = client.get(f"/api/v1/tasks/{created['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Read the guide"


@pytest.mark.parametrize("task_id", [999, 0])
def test_get_task_reports_missing_or_invalid_id(client: TestClient, task_id: int) -> None:
    """Unknown tasks return 404 and non-positive IDs fail validation."""

    response = client.get(f"/api/v1/tasks/{task_id}")

    assert response.status_code == (404 if task_id == 999 else 422)


def test_update_task_changes_only_supplied_fields(client: TestClient) -> None:
    """PATCH preserves fields that are not included in the request."""

    created = client.post(
        "/api/v1/tasks",
        json={"title": "Original title", "description": "Keep this", "priority": "low"},
    ).json()

    response = client.patch(
        f"/api/v1/tasks/{created['id']}",
        json={"title": "Updated title", "is_completed": True},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated title"
    assert updated["description"] == "Keep this"
    assert updated["priority"] == "low"
    assert updated["is_completed"] is True
    assert updated["updated_at"] != created["updated_at"]


@pytest.mark.parametrize(
    "payload",
    [{}, {"title": " "}, {"priority": "urgent"}, {"is_completed": None}],
)
def test_update_task_rejects_invalid_input(client: TestClient, payload: dict[str, Any]) -> None:
    """PATCH requires valid values and at least one supplied field."""

    created = client.post("/api/v1/tasks", json={"title": "Task"}).json()

    response = client.patch(f"/api/v1/tasks/{created['id']}", json=payload)

    assert response.status_code == 422


def test_update_task_reports_missing_task(client: TestClient) -> None:
    """PATCH returns 404 when the task does not exist."""

    response = client.patch("/api/v1/tasks/999", json={"title": "New title"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}


def test_delete_task_removes_a_task(client: TestClient) -> None:
    """DELETE returns 204 and the task can no longer be fetched."""

    created = client.post("/api/v1/tasks", json={"title": "Remove me"}).json()

    response = client.delete(f"/api/v1/tasks/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/api/v1/tasks/{created['id']}").status_code == 404


def test_delete_task_reports_missing_task(client: TestClient) -> None:
    """DELETE returns 404 when there is no matching task."""

    response = client.delete("/api/v1/tasks/999")

    assert response.status_code == 404
