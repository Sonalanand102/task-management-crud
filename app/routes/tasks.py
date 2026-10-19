"""Routes for creating and listing tasks."""

from fastapi import APIRouter, Path, Request, Response, status

from app.controllers.tasks import TaskController
from app.repositories.tasks import TaskRepository
from app.schemas.tasks import TaskCreate, TaskRead, TaskUpdate
from app.services.tasks import TaskService

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


def get_task_controller(request: Request) -> TaskController:
    """Build the task controller using the application's shared pool."""

    repository = TaskRepository(request.app.state.db_pool)
    service = TaskService(repository)
    return TaskController(service)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, request: Request) -> TaskRead:
    """Create a task."""

    return get_task_controller(request).create_task(task)


@router.get("", response_model=list[TaskRead])
def list_tasks(request: Request) -> list[TaskRead]:
    """List all tasks."""

    return get_task_controller(request).list_tasks()


@router.get("/{task_id}", response_model=TaskRead)
def get_task(
    request: Request, task_id: int = Path(ge=1)
) -> TaskRead:
    """Fetch one task."""

    return get_task_controller(request).get_task(task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task: TaskUpdate, request: Request, task_id: int = Path(ge=1)
) -> TaskRead:
    """Update only the supplied task fields."""

    return get_task_controller(request).update_task(task_id, task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    request: Request, task_id: int = Path(ge=1)
) -> Response:
    """Delete a task."""

    get_task_controller(request).delete_task(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
