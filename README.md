# Task CRUD API

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)
![Postgres](https://img.shields.io/badge/database-PostgreSQL_16-336791.svg)
![Docker](https://img.shields.io/badge/container-Docker-2496ED.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

A to-do list API demonstrating the four CRUD operations (**C**reate, **R**ead, **U**pdate, **D**elete), with a layered architecture — routes, a service, and a swappable storage repository — backed by real Postgres running in Docker. Data survives app restarts *and* container restarts.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Example Usage](#example-usage)
- [Error Format](#error-format)
- [Database](#database)
- [Interactive Docs (Swagger UI)](#interactive-docs-swagger-ui)
- [How Persistence Was Verified](#how-persistence-was-verified)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

This API manages a to-do list. Every task is stored as a row in Postgres:

```json
{ "id": 1, "title": "Buy milk", "done": false }
```

The API surface is identical to the original in-memory version — same URLs, same request bodies, same status codes. Only the storage layer changed, which is the whole point: **the API describes what the app does; the database describes where it keeps its data.**

That claim was verified directly, not just asserted: swapping the storage backend from an in-memory Python list to real Postgres changed exactly one file — `main.py`, and only the three lines that choose which repository to construct. The service layer and every route were never touched.

## Architecture

```
routes (main.py) → service (service.py) → repository (in_memory_repository.py or postgres_repository.py)
```

| File                      | Responsibility                                                          |
|---------------------------|---------------------------------------------------------------------------|
| `models.py`                | Shared `Task`, `NewTask`, `TaskUpdate` data shapes                       |
| `repository.py`            | Abstract `TaskRepository` interface — the contract both backends implement |
| `in_memory_repository.py`  | Storage backend: a plain Python list, gone on restart                    |
| `postgres_repository.py`   | Storage backend: real SQL queries against Postgres                       |
| `service.py`                | Business logic and validation; depends only on the interface             |
| `main.py`                  | FastAPI routes, plus the one place the storage backend is chosen         |
| `db.py`                     | Reads `DATABASE_URL` from the environment and opens a connection         |
| `init.sql`                  | Creates the `tasks` table and seeds it                                   |

## Tech Stack

| Layer            | Choice                                    |
|-------------------|--------------------------------------------|
| Language          | Python 3.10+                              |
| Framework         | [FastAPI](https://fastapi.tiangolo.com/)  |
| Server            | Uvicorn                                   |
| Docs              | Swagger UI (auto-generated at `/docs`)    |
| Database          | PostgreSQL 16                             |
| Driver            | `psycopg2`                                |
| Containers        | Docker + Docker Compose                   |

## Getting Started

### With Docker (recommended)

Starts Postgres and the app together, with a volume so data survives restarts.

```bash
cp .env.example .env
docker compose up
```

| URL                              | What you'll see          |
|-----------------------------------|---------------------------|
| http://localhost:8000/            | API info                  |
| http://localhost:8000/health      | Health check              |
| http://localhost:8000/docs        | Interactive Swagger UI    |

Stop the stack with `docker compose down`. Data persists in the `pgdata` volume — add `-v` only if you want to wipe it.

### Without Docker

Useful for quick local iteration. Falls back to the in-memory backend automatically if `DATABASE_URL` isn't set.

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

> Windows users: if `uvicorn` isn't recognized as a command, run `python -m uvicorn main:app --reload` instead.

To point a locally-run app at a locally-run Postgres instead of the in-memory store, export `DATABASE_URL` (see `.env.example`, swapping the host `db` for `localhost`) before starting uvicorn.

## Environment Variables

Real values live in `.env`, which is gitignored. `.env.example` is committed as the template.

| Variable            | Purpose                                       |
|---------------------|------------------------------------------------|
| `POSTGRES_USER`      | Database user, used by the `db` container       |
| `POSTGRES_PASSWORD`  | Database password                               |
| `POSTGRES_DB`        | Database name                                   |
| `DATABASE_URL`       | Full connection string the app uses to connect  |

## API Reference

| Method   | Path            | Description                             | Success | Errors       |
|----------|-----------------|--------------------------------------------|---------|--------------|
| `GET`    | `/`             | API info                                 | `200`   | —            |
| `GET`    | `/health`       | Health check                             | `200`   | —            |
| `GET`    | `/tasks`        | List tasks (`?done=`, `?search=` supported) | `200`   | —            |
| `GET`    | `/tasks/{id}`   | Get a single task                        | `200`   | `404`        |
| `POST`   | `/tasks`        | Create a task (`title` required)         | `201`   | `400`        |
| `PUT`    | `/tasks/{id}`   | Update a task's `title` and/or `done`    | `200`   | `400`, `404` |
| `DELETE` | `/tasks/{id}`   | Delete a task                            | `204`   | `404`        |
| `GET`    | `/stats`        | Counts: total, done, open                | `200`   | —            |
| `POST`   | `/reset`        | Restore the three seed tasks             | `200`   | —            |

## Example Usage

**Create a task**

```bash
curl -i -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy milk"}'
```

```http
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

**Mark it done**

```bash
curl -i -X PUT http://localhost:8000/tasks/4 \
  -H "Content-Type: application/json" \
  -d '{"done":true}'
```

**Delete it**

```bash
curl -i -X DELETE http://localhost:8000/tasks/4
```

```http
HTTP/1.1 204 No Content
```

**Restart the whole stack** (`docker compose down` then `docker compose up`) and check `GET /tasks` again — everything you created is still there. That's the upgrade this assignment is about.

## Error Format

Every error returns a JSON body with a single `error` key:

```json
{ "error": "Task 99 not found" }
```

| Status | Meaning         | When it happens                           |
|--------|-----------------|----------------------------------------------|
| `400`  | Bad Request     | Missing or empty `title` on create/update      |
| `404`  | Not Found       | No task exists with that `id`                  |

## Database

**Why Postgres in Docker?** It's the same production-grade database used in real backend systems, runs identically on any machine via Docker, and — with a named volume — keeps data across both app restarts and full container restarts, which an in-memory list or a local SQLite file tied to the container filesystem would not survive as cleanly in a multi-container setup.

**Where it's stored:** a Docker-managed volume named `pgdata`, defined in `docker-compose.yml`. It's created automatically the first time you run `docker compose up` and is untouched by `docker compose down` (only `docker compose down -v` removes it).

**Schema** (`init.sql`, applied automatically on first container start):

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);
```

**Exploring it manually:** with the stack running,

```bash
docker compose exec db psql -U taskuser -d taskdb -c "SELECT * FROM tasks;"
```

(swap `taskuser` / `taskdb` for whatever you set in `.env`). Try updating a row directly in `psql`, then call `GET /tasks` — the change shows up immediately, proof the API reads live from Postgres rather than any cached copy.

## Interactive Docs (Swagger UI)

FastAPI generates a full interactive spec automatically — no extra setup required.

Screenshot placeholder — replace with your own image of `http://localhost:8000/docs`.

Every endpoint above is listed with a **Try it out** button that sends real requests and shows real responses, directly in the browser.

## How Persistence Was Verified

1. Started the stack with `docker compose up`.
2. Created a task via `POST /tasks`.
3. Confirmed it in the response and in a follow-up `GET /tasks`.
4. Ran `docker compose down` then `docker compose up` again — a full restart of both the app container and the database container.
5. Called `GET /tasks` again: the task from step 2 was still there, because it lived in the `pgdata` volume, not in the app's memory.

This is the opposite of the in-memory backend's behavior, where the same restart would reset the list back to the three seed tasks.

## Roadmap

- [ ] Add Redis to `docker-compose.yml` and ping it from the app
- [ ] Add an index and compare `EXPLAIN ANALYZE` before/after on a seeded table
- [ ] Pagination (`?limit=2&offset=2`)
- [ ] `created_at` / `updated_at` timestamps

## License

MIT.