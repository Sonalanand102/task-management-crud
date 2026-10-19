# Task Management REST API

A beginner-friendly CRUD backend workshop project built with Python 3.12+, FastAPI, PostgreSQL, psycopg 3, and Pydantic v2.

The project deliberately uses explicit, parameterized SQL instead of an ORM.

## Current progress

Milestone 1 provides the application foundation:

- environment-based configuration;
- a psycopg connection pool managed by the FastAPI lifespan;
- a `GET /health` endpoint; and
- a basic automated test.

Milestone 2 adds the initial PostgreSQL schema as a versioned SQL file. Task CRUD endpoints are not implemented yet.

## Prerequisites

- Python 3.12 or newer
- PostgreSQL (needed once database work begins)

## Setup

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the application and development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Create your local environment file and set a PostgreSQL connection URL:

```bash
cp .env.example .env
```

Update `DATABASE_URL` in `.env` with your local database credentials. `.env` is ignored by Git and must not be committed.

## Database setup

The migration at `sql/001_create_tasks.sql` creates the single `tasks` table used by this introductory CRUD project. It defines the task fields, their default values, and database constraints for valid titles and priorities.

Load `DATABASE_URL` from your local `.env` file, then execute the migration:

```bash
set -a
source .env
set +a
psql "$DATABASE_URL" -f sql/001_create_tasks.sql
```

Inspect the table definition:

```bash
psql "$DATABASE_URL" -c '\d tasks'
```

Inspect the table records:

```bash
psql "$DATABASE_URL" -c 'SELECT * FROM tasks;'
```

## Run the API

```bash
uvicorn app.main:app --reload
```

The health check is available at [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

FastAPI automatically serves interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Run tests

```bash
pytest
```

## Connection pool lifecycle

When FastAPI starts, the lifespan function reads `DATABASE_URL`, creates a psycopg `ConnectionPool`, opens it, and stores it at `app.state.db_pool`. When the API stops, it closes the pool. Future repository code will borrow connections from this pool and use parameterized psycopg queries.
