"""Application-specific exception types."""


class DatabaseOperationError(Exception):
    """Raised when a database operation cannot be completed safely."""


class TaskNotFoundError(Exception):
    """Raised when a requested task does not exist."""
