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