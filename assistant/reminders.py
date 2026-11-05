"""Reminder logic: which tasks need a reminder, and who to send it to."""

import json
from datetime import date
from pathlib import Path
from typing import Optional

from assistant.tasks.models import Task


CHAT_FILE = Path("data/chat.json")


def save_chat_id(chat_id: int) -> None:
    """Remember which Telegram chat to send reminders to."""
    CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_FILE.write_text(json.dumps({"chat_id": chat_id}), encoding="utf-8")


def load_chat_id() -> Optional[int]:
    """Return the saved chat ID, or None if nobody has messaged the bot yet."""
    try:
        return json.loads(CHAT_FILE.read_text(encoding="utf-8"))["chat_id"]
    except (OSError, ValueError, KeyError):
        return None


def build_reminder(tasks: list[Task], today: date) -> Optional[str]:
    """Build a reminder message, or return None if nothing is due."""
    # Only unfinished tasks that have a due date.
    open_tasks = [t for t in tasks if not t.completed and t.due_date]

    overdue = [t for t in open_tasks if t.due_date < today]
    due_today = [t for t in open_tasks if t.due_date == today]

    if not overdue and not due_today:
        return None

    lines = ["⏰ Reminder"]

    if due_today:
        lines.append("\nDue today:")
        lines += [f"• {t.title}" for t in due_today]

    if overdue:
        lines.append("\nOverdue:")
        lines += [
            f"• {t.title} (was due {t.due_date.strftime('%a %d %b')})"
            for t in overdue
        ]

    lines.append("\nTell me when you finish one, and I'll mark it done.")
    return "\n".join(lines)