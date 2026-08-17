from typing import Optional

from pydantic import BaseModel


class Task(BaseModel):
    id: int
    title: str
    done: bool = False


class NewTask(BaseModel):
    title: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None