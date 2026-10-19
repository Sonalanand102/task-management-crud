"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.config import Settings
from app.database import create_connection_pool
from app.exceptions import DatabaseOperationError, TaskNotFoundError
from app.routes.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start and stop the PostgreSQL connection pool with the application."""

    settings = Settings()
    pool = create_connection_pool(settings.database_url)
    pool.open()
    app.state.db_pool = pool

    try:
        yield
    finally:
        pool.close()


app = FastAPI(
    title="Task Management API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(DatabaseOperationError)
async def database_operation_error_handler(
    request: Request, error: DatabaseOperationError
) -> JSONResponse:
    """Return a safe response without exposing database implementation details."""

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A database error occurred. Please try again later."},
    )


@app.exception_handler(TaskNotFoundError)
async def task_not_found_error_handler(
    request: Request, error: TaskNotFoundError
) -> JSONResponse:
    """Return a consistent response for missing tasks."""

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Task not found."},
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is running."""

    return {"status": "ok"}


app.include_router(tasks_router)
