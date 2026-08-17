from abc import ABC, abstractmethod
from typing import List, Optional

from models import Task


class TaskRepository(ABC):

    @abstractmethod
    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> List[Task]:
        ...

    @abstractmethod
    def get(self, task_id: int) -> Optional[Task]:
        ...

    @abstractmethod
    def create(self, title: str) -> Task:
        ...

    @abstractmethod
    def update(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[Task]:
        ...

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        ...

    @abstractmethod
    def stats(self) -> dict:
        ...

    @abstractmethod
    def reset(self) -> None:
        ...