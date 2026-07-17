import json
from pathlib import Path
from typing import Any


MEMORY_FILE = Path("data/memory.json")

SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are Fahmy's AI Executive Assistant. "
        "Be practical, organized, concise, and helpful. "
        "Help with planning, writing, research, job applications, "
        "emails, documents, and productivity."
    ),
}


def load_messages() -> list[dict[str, Any]]:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists() or MEMORY_FILE.stat().st_size == 0:
        return [SYSTEM_MESSAGE.copy()]

    try:
        with MEMORY_FILE.open("r", encoding="utf-8") as file:
            messages = json.load(file)

        if not isinstance(messages, list):
            raise ValueError("Memory must contain a list.")

        return messages

    except (json.JSONDecodeError, OSError, ValueError):
        return [SYSTEM_MESSAGE.copy()]


def save_messages(messages: list[dict[str, Any]]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with MEMORY_FILE.open("w", encoding="utf-8") as file:
        json.dump(messages, file, indent=2, ensure_ascii=False)


def clear_messages() -> list[dict[str, Any]]:
    messages = [SYSTEM_MESSAGE.copy()]
    save_messages(messages)
    return messages