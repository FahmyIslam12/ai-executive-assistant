from typing import Optional

from .models import Task
from .storage import load_tasks, save_tasks


class TaskManager:
    def __init__(self) -> None:
        self.tasks: list[Task] = load_tasks()

    def add_task(self, title: str) -> Task:
        task = Task(title=title)
        self.tasks.append(task)
        save_tasks(self.tasks)
        return task

    def list_tasks(self) -> list[Task]:
        return self.tasks.copy()

    def complete_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                task.completed = True
                save_tasks(self.tasks)
                return task

        return None

    def delete_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                self.tasks.remove(task)
                save_tasks(self.tasks)
                return task

        return None