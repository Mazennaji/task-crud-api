from typing import List, Optional

from models import Task
from repository import TaskRepository

SEED_TASKS = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Write README", "done": False},
    {"id": 3, "title": "Walk the dog", "done": True},
]


class InMemoryTaskRepository(TaskRepository):

    def __init__(self):
        self._tasks: List[Task] = [Task(**t) for t in SEED_TASKS]
        self._next_id = 4

    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> List[Task]:
        result = self._tasks
        if done is not None:
            result = [t for t in result if t.done == done]
        if search:
            result = [t for t in result if search.lower() in t.title.lower()]
        return result

    def get(self, task_id: int) -> Optional[Task]:
        return next((t for t in self._tasks if t.id == task_id), None)

    def create(self, title: str) -> Task:
        task = Task(id=self._next_id, title=title, done=False)
        self._tasks.append(task)
        self._next_id += 1
        return task

    def update(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[Task]:
        for i, t in enumerate(self._tasks):
            if t.id == task_id:
                updates = {}
                if title is not None:
                    updates["title"] = title
                if done is not None:
                    updates["done"] = done
                updated = t.model_copy(update=updates)
                self._tasks[i] = updated
                return updated
        return None

    def delete(self, task_id: int) -> bool:
        for i, t in enumerate(self._tasks):
            if t.id == task_id:
                self._tasks.pop(i)
                return True
        return False

    def stats(self) -> dict:
        total = len(self._tasks)
        done_count = sum(1 for t in self._tasks if t.done)
        return {"total": total, "done": done_count, "open": total - done_count}

    def reset(self) -> None:
        self._tasks = [Task(**t) for t in SEED_TASKS]
        self._next_id = 4