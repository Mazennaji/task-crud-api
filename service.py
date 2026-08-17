from typing import List, Optional

from models import Task
from repository import TaskRepository


class TaskNotFoundError(Exception):
    def __init__(self, task_id: int):
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")


class ValidationError(Exception):
    pass


class TaskService:

    def __init__(self, repository: TaskRepository):
        self.repository = repository

    def list_tasks(self, done: Optional[bool] = None, search: Optional[str] = None) -> List[Task]:
        return self.repository.list(done=done, search=search)

    def get_task(self, task_id: int) -> Task:
        task = self.repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def create_task(self, title: Optional[str]) -> Task:
        if not title or not title.strip():
            raise ValidationError("title is required and cannot be empty")
        return self.repository.create(title=title)

    def update_task(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Task:
        if title is not None and not title.strip():
            raise ValidationError("title cannot be empty")
        updated = self.repository.update(task_id, title=title, done=done)
        if updated is None:
            raise TaskNotFoundError(task_id)
        return updated

    def delete_task(self, task_id: int) -> None:
        if not self.repository.delete(task_id):
            raise TaskNotFoundError(task_id)

    def get_stats(self) -> dict:
        return self.repository.stats()

    def reset_tasks(self) -> List[Task]:
        self.repository.reset()
        return self.repository.list()