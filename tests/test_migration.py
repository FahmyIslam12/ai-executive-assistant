"""Moving from JSON files to the database: once, nothing lost, with a backup."""

import json
from pathlib import Path

from assistant import database
from assistant.tasks.manager import TaskManager


def write_old_tasks_file():
    Path("data").mkdir()
    tasks = [
        {"id": "a1", "title": "Study Python", "completed": True, "due_date": None},
        {"id": "a2", "title": "Send CV to Rahim", "completed": False, "due_date": "2026-11-05"},
    ]
    Path("data/tasks.json").write_text(json.dumps(tasks))


def test_tasks_move_once_with_backup(monkeypatch):
    write_old_tasks_file()

    tasks = TaskManager().list_tasks()
    assert [t.title for t in tasks] == ["Study Python", "Send CV to Rahim"]
    assert not Path("data/tasks.json").exists()
    assert Path("data/tasks.json.migrated").exists()  # backup kept

    # Simulate restarting the bot: the move must not run again.
    monkeypatch.setattr(database, "_ready", False)
    assert len(TaskManager().list_tasks()) == 2  # no duplicates


def test_nothing_to_move_on_a_fresh_install():
    assert TaskManager().list_tasks() == []
