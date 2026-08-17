from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from uuid import uuid4


@dataclass
class Task:
    title: str
    completed: bool = False
    due_date: Optional[date] = None
    id: str = field(default_factory=lambda: str(uuid4()))