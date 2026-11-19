"""Tasks: add, complete, delete, and numbering."""

from datetime import date

from assistant.tasks.manager import TaskManager, format_tasks


def test_added_task_is_saved_and_survives_a_restart():
    TaskManager().add_task("Apply to BJIT", date(2026, 11, 25))

    # A new TaskManager reads from the database again, like after a restart.
    tasks = TaskManager().list_tasks()

    assert len(tasks) == 1
    assert tasks[0].title == "Apply to BJIT"
    assert tasks[0].due_date == date(2026, 11, 25)
    assert tasks[0].completed is False


def test_complete_and_delete_by_list_number():
    manager = TaskManager()
    for title in ["First", "Second", "Third"]:
        manager.add_task(title)

    manager.complete_task(manager.find_task("2").id)
    manager.delete_task(manager.find_task("1").id)

    tasks = TaskManager().list_tasks()
    assert [t.title for t in tasks] == ["Second", "Third"]  # order kept
    assert tasks[0].completed is True


def test_unknown_task_number_finds_nothing():
    manager = TaskManager()
    manager.add_task("Only task")

    assert manager.find_task("9") is None
    assert manager.find_task("0") is None
    assert manager.find_task("") is None


def test_task_list_shows_done_marks_and_due_dates():
    manager = TaskManager()
    manager.add_task("Send CV", date(2026, 11, 6))
    manager.complete_task(manager.find_task("1").id)

    assert format_tasks(manager.list_tasks()) == "1. [✓] Send CV (due Fri 06 Nov)"
    assert format_tasks([]) == "No tasks yet."
