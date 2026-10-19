"""PostgreSQL connection-pool helpers."""

from psycopg_pool import ConnectionPool


def create_connection_pool(database_url: str) -> ConnectionPool:
    """Create a closed pool; FastAPI opens and closes it during its lifespan."""

    return ConnectionPool(
        conninfo=database_url,
        min_size=0,
        max_size=10,
        open=False,
    )
