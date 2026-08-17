from typing import List, Optional

from db import get_connection
from models import Task
from repository import TaskRepository


class PostgresTaskRepository(TaskRepository):

    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> List[Task]:
        query = "SELECT id, title, done FROM tasks WHERE TRUE"
        params: list = []
        if done is not None:
            query += " AND done = %s"
            params.append(done)
        if search:
            query += " AND title ILIKE %s"
            params.append(f"%{search}%")
        query += " ORDER BY id"

        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            return [Task(**row) for row in cur.fetchall()]

    def get(self, task_id: int) -> Optional[Task]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
            return Task(**row) if row else None

    def create(self, title: str) -> Task:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, FALSE) RETURNING id, title, done",
                (title,),
            )
            return Task(**cur.fetchone())

    def update(self, task_id: int, title: Optional[str] = None, done: Optional[bool] = None) -> Optional[Task]:
        fields, params = [], []
        if title is not None:
            fields.append("title = %s")
            params.append(title)
        if done is not None:
            fields.append("done = %s")
            params.append(done)
        if not fields:
            return self.get(task_id)

        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = %s RETURNING id, title, done"

        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return Task(**row) if row else None

    def delete(self, task_id: int) -> bool:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            return cur.rowcount > 0

    def stats(self) -> dict:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE done) AS done FROM tasks"
            )
            row = cur.fetchone()
            total, done_count = row["total"], row["done"]
            return {"total": total, "done": done_count, "open": total - done_count}

    def reset(self) -> None:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("TRUNCATE tasks RESTART IDENTITY")
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s), (%s, %s), (%s, %s)",
                ("Buy milk", False, "Write README", False, "Walk the dog", True),
            )