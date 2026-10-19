"""Request and response schemas for tasks."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


Priority = Literal["low", "medium", "high"]


class TaskCreate(BaseModel):
    """Data accepted when creating a task."""

    title: str = Field(max_length=200)
    description: str | None = None
    priority: Priority = "medium"

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        """Reject titles containing only whitespace and store trimmed titles."""

        title = value.strip()
        if not title:
            raise ValueError("Title must not be blank.")
        return title


class TaskRead(BaseModel):
    """Task data returned by the API."""

    id: int
    title: str
    description: str | None
    priority: Priority
    is_completed: bool
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    """Fields that may be changed on an existing task."""

    title: str | None = Field(default=None, max_length=200)
    description: str | None = None
    priority: Priority | None = None
    is_completed: bool | None = None

    @field_validator("title")
    @classmethod
    def updated_title_must_not_be_blank(cls, value: str | None) -> str | None:
        """Reject blank titles while allowing the field to be omitted."""

        if value is None:
            return value

        title = value.strip()
        if not title:
            raise ValueError("Title must not be blank.")
        return title

    @model_validator(mode="after")
    def validate_supplied_fields(self) -> "TaskUpdate":
        """Require a change and reject nulls for non-nullable task fields."""

        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        for field_name in ("title", "priority", "is_completed"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} must not be null.")

        return self
