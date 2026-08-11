from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Task:
    title: str
    completed: bool = False
    due_date: Optional[date] = None