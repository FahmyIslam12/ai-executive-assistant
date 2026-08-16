import json
from pathlib import Path
from .models import Task
from datetime import date


TASKS_FILE = Path("data/tasks.json")

def ensure_tasks_file() -> None:
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")

def save_tasks(tasks: list[Task]) -> None:
    ensure_tasks_file()

    data = [
        {
            "title": task.title,
            "completed": task.completed,
            "due_date": task.due_date.isoformat() if task.due_date else None,
        }
        for task in tasks
    ]

    TASKS_FILE.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

def load_tasks() -> list[Task]:
    ensure_tasks_file()

    data = json.loads(
        TASKS_FILE.read_text(encoding="utf-8")
    )

    tasks = []

    for item in data:
        due_date = (
            date.fromisoformat(item["due_date"])
            if item["due_date"]
            else None
        )

        tasks.append(
            Task(
                title=item["title"],
                completed=item["completed"],
                due_date=due_date,
            )
        )

    return tasks