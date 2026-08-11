from .models import Task


class TaskManager:
    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def add_task(self, title: str) -> Task:
        task = Task(title=title)
        self.tasks.append(task)
        return task
    
    def list_tasks(self) -> list[Task]:
        return self.tasks.copy()