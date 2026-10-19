"""HTTP-facing task operations."""

from app.schemas.tasks import TaskCreate, TaskRead, TaskUpdate
from app.services.tasks import TaskService


class TaskController:
    """Expose task use cases to API routes."""

    def __init__(self, service: TaskService) -> None:
        self.service = service

    def create_task(self, task: TaskCreate) -> TaskRead:
        """Create a task from validated request data."""

        return self.service.create_task(task)

    def list_tasks(self) -> list[TaskRead]:
        """List tasks for the HTTP response."""

        return self.service.list_tasks()

    def get_task(self, task_id: int) -> TaskRead:
        """Fetch one task for the HTTP response."""

        return self.service.get_task(task_id)

    def update_task(self, task_id: int, task: TaskUpdate) -> TaskRead:
        """Update a task from validated request data."""

        return self.service.update_task(task_id, task)

    def delete_task(self, task_id: int) -> None:
        """Delete a task."""

        self.service.delete_task(task_id)
