"""PostgreSQL queries for tasks."""

from collections.abc import Mapping
from typing import Any

from psycopg import Error
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

from app.exceptions import DatabaseOperationError
from app.schemas.tasks import TaskCreate, TaskUpdate


class TaskRepository:
    """Run task SQL queries through the shared connection pool."""

    def __init__(self, pool: ConnectionPool) -> None:
        self.pool = pool

    def create(self, task: TaskCreate) -> Mapping[str, Any]:
        """Insert a task and return the row created by PostgreSQL."""

        query = """
            INSERT INTO tasks (title, description, priority)
            VALUES (%s, %s, %s)
            RETURNING id, title, description, priority, is_completed, created_at, updated_at;
        """

        try:
            # A successful connection context commits; an exception rolls back.
            with self.pool.connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(query, (task.title, task.description, task.priority))
                    row = cursor.fetchone()
        except (Error, PoolTimeout) as error:
            raise DatabaseOperationError from error

        if row is None:
            raise DatabaseOperationError

        return row

    def list_all(self) -> list[Mapping[str, Any]]:
        """Return all tasks ordered by their identity value."""

        query = """
            SELECT id, title, description, priority, is_completed, created_at, updated_at
            FROM tasks
            ORDER BY id;
        """

        try:
            with self.pool.connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(query)
                    rows = cursor.fetchall()
        except (Error, PoolTimeout) as error:
            raise DatabaseOperationError from error

        return rows

    def get_by_id(self, task_id: int) -> Mapping[str, Any] | None:
        """Return one task by its identity value, if it exists."""

        query = """
            SELECT id, title, description, priority, is_completed, created_at, updated_at
            FROM tasks
            WHERE id = %s;
        """

        try:
            with self.pool.connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(query, (task_id,))
                    return cursor.fetchone()
        except (Error, PoolTimeout) as error:
            raise DatabaseOperationError from error

    def update(self, task_id: int, task: TaskUpdate) -> Mapping[str, Any] | None:
        """Update supplied fields, refresh ``updated_at``, and return the task."""

        changes = task.model_dump(exclude_unset=True)
        allowed_fields = ("title", "description", "priority", "is_completed")
        assignments = [f"{field_name} = %s" for field_name in allowed_fields if field_name in changes]
        values = [changes[field_name] for field_name in allowed_fields if field_name in changes]

        query = f"""
            UPDATE tasks
            SET {", ".join(assignments)}, updated_at = NOW()
            WHERE id = %s
            RETURNING id, title, description, priority, is_completed, created_at, updated_at;
        """

        try:
            with self.pool.connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(query, (*values, task_id))
                    return cursor.fetchone()
        except (Error, PoolTimeout) as error:
            raise DatabaseOperationError from error

    def delete(self, task_id: int) -> bool:
        """Delete a task and report whether a row was removed."""

        query = "DELETE FROM tasks WHERE id = %s RETURNING id;"

        try:
            with self.pool.connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(query, (task_id,))
                    return cursor.fetchone() is not None
        except (Error, PoolTimeout) as error:
            raise DatabaseOperationError from error
