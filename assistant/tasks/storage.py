"""Save and load tasks in the SQLite database (previously data/tasks.json)."""

from datetime import date

from assistant.database import connect

from .models import Task


def save_tasks(tasks: list[Task]) -> None:
    """Make the tasks table match this list exactly."""
    connection = connect()

    with connection:  # one transaction: all changes, or none
        keep_ids = [task.id for task in tasks]

        # Delete tasks that are no longer in the list.
        placeholders = ",".join("?" for _ in keep_ids) or "''"
        connection.execute(
            f"DELETE FROM tasks WHERE id NOT IN ({placeholders})", keep_ids
        )

        for task in tasks:
            values = (
                task.title,
                int(task.completed),
                task.due_date.isoformat() if task.due_date else None,
                task.application_id,
                task.id,
            )
            # Update the task if it exists...
            updated = connection.execute(
                "UPDATE tasks SET title = ?, completed = ?, due_date = ?, "
                "application_id = ? WHERE id = ?",
                values,
            ).rowcount
            # ...otherwise add it as a new row.
            if updated == 0:
                connection.execute(
                    "INSERT INTO tasks (title, completed, due_date, application_id, id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    values,
                )

    connection.close()


def load_tasks() -> list[Task]:
    """Read all tasks, oldest first (so task numbers stay the same)."""
    connection = connect()
    rows = connection.execute(
        "SELECT id, title, completed, due_date, application_id "
        "FROM tasks ORDER BY rowid"
    ).fetchall()
    connection.close()

    return [
        Task(
            title=row["title"],
            completed=bool(row["completed"]),
            due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
            id=row["id"],
            application_id=row["application_id"],
        )
        for row in rows
    ]
