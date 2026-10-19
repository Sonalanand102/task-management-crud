"""Business logic for tasks."""

from app.exceptions import TaskNotFoundError
from app.repositories.tasks import TaskRepository
from app.schemas.tasks import TaskCreate, TaskRead, TaskUpdate


class TaskService:
    """Coordinate task use cases."""

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(self, task: TaskCreate) -> TaskRead:
        """Create one task."""

        return TaskRead.model_validate(self.repository.create(task))

    def list_tasks(self) -> list[TaskRead]:
        """List all tasks."""

        return [TaskRead.model_validate(row) for row in self.repository.list_all()]

    def get_task(self, task_id: int) -> TaskRead:
        """Return a task or raise a not-found error."""

        task = self.repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError
        return TaskRead.model_validate(task)

    def update_task(self, task_id: int, task: TaskUpdate) -> TaskRead:
        """Update a task or raise a not-found error."""

        updated_task = self.repository.update(task_id, task)
        if updated_task is None:
            raise TaskNotFoundError
        return TaskRead.model_validate(updated_task)

    def delete_task(self, task_id: int) -> None:
        """Delete a task or raise a not-found error."""

        if not self.repository.delete(task_id):
            raise TaskNotFoundError
