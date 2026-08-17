import os
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from in_memory_repository import InMemoryTaskRepository
from models import NewTask, TaskUpdate
from service import TaskNotFoundError, TaskService, ValidationError

app = FastAPI(title="Task API", version="1.0")

if os.environ.get("DATABASE_URL"):
    from postgres_repository import PostgresTaskRepository
    repository = PostgresTaskRepository()
else:
    repository = InMemoryTaskRepository()

service = TaskService(repository)


@app.exception_handler(TaskNotFoundError)
async def not_found_handler(request: Request, exc: TaskNotFoundError):
    return JSONResponse(status_code=404, content={"error": str(exc)})


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.get("/", description="Describes this API: name, version, and available endpoints.")
def root():
    return {"name": "Task API", "version": "1.0", "endpoints": ["/tasks"]}


@app.get("/health", description="Health check — confirms the server is alive.")
def health():
    return {"status": "ok"}


@app.get("/tasks", description="List tasks. Optional query params: done=true/false, search=<word in title>.")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    return service.list_tasks(done=done, search=search)


@app.get("/tasks/{task_id}", description="Get a single task by its id. Returns 404 if it doesn't exist.")
def get_task(task_id: int):
    return service.get_task(task_id)


@app.post("/tasks", status_code=201, description="Create a new task. Requires a non-empty title. Returns 400 if invalid.")
def create_task(new_task: NewTask):
    return service.create_task(new_task.title)


@app.put("/tasks/{task_id}", description="Update a task's title and/or done status. Returns 404 if unknown, 400 if invalid.")
def update_task(task_id: int, update: TaskUpdate):
    return service.update_task(task_id, title=update.title, done=update.done)


@app.delete("/tasks/{task_id}", status_code=204, description="Delete a task by id. Returns 204 with no body, or 404 if unknown.")
def delete_task(task_id: int):
    service.delete_task(task_id)


@app.get("/stats", description="Quick counts: total tasks, how many done, how many still open.")
def stats():
    return service.get_stats()


@app.post("/reset", description="Restore the 3 example tasks. Handy for demos.")
def reset_tasks():
    return service.reset_tasks()