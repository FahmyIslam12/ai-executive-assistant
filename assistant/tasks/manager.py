from datetime import date
from typing import Optional

from .models import Task
from .storage import load_tasks, save_tasks


class TaskManager:
    def __init__(self) -> None:
        self.tasks: list[Task] = load_tasks()

    def add_task(self, title: str, due_date: Optional[date] = None) -> Task:
        task = Task(title=title, due_date=due_date)
        self.tasks.append(task)
        save_tasks(self.tasks)
        return task

    def list_tasks(self) -> list[Task]:
        return self.tasks.copy()

    def find_task(self, ref: str) -> Optional[Task]:
        """Find a task by its list number (e.g. "2") or the start of its ID."""
        ref = ref.strip()

        if not ref:
            return None

        if ref.isdigit():
            number = int(ref)
            if 1 <= number <= len(self.tasks):
                return self.tasks[number - 1]
            return None

        matches = [task for task in self.tasks if task.id.startswith(ref)]
        return matches[0] if len(matches) == 1 else None

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


def format_tasks(tasks: list[Task]) -> str:
    """Turn a list of tasks into readable numbered lines."""
    if not tasks:
        return "No tasks yet."

    lines = []

    for number, task in enumerate(tasks, start=1):
        status = "✓" if task.completed else " "
        due = f" (due {task.due_date.strftime('%a %d %b')})" if task.due_date else ""
        lines.append(f"{number}. [{status}] {task.title}{due}")

    return "\n".join(lines)