"""Tools the AI is allowed to ask for.

The AI never runs these itself. It sends back a request like
"run add_task with title='Apply to jobs'", and run_tool() below
does the real work. Our code always stays in control.
"""

import json
from datetime import date

from assistant.tasks.manager import TaskManager, format_tasks


# PART 1: The "menu" we show the AI.
# Each tool has a name, a description (so the AI knows WHEN to use it),
# and parameters (what information it must give us).
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": (
                "Add a task to the user's task list. Use this when the user "
                "asks to be reminded of something or to add something to do."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short task title, e.g. 'Apply to Brain Station'",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Optional due date in YYYY-MM-DD format",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "Show the user's tasks, with numbers and due dates.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": (
                "Mark a task as done. If you don't know the task's number, "
                "call list_tasks first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "number": {
                        "type": "integer",
                        "description": "The task's number from list_tasks",
                    },
                },
                "required": ["number"],
            },
        },
    },
]


# PART 2: The code that actually runs a tool when the AI asks for it.
def run_tool(name: str, arguments_json: str, task_manager: TaskManager) -> str:
    """Run the tool the AI asked for and return the result as text."""
    try:
        # The AI sends its arguments as JSON text, e.g. '{"title": "Study"}'.
        args = json.loads(arguments_json or "{}")

        if name == "add_task":
            due_date = None
            if args.get("due_date"):
                due_date = date.fromisoformat(args["due_date"])

            task = task_manager.add_task(args["title"], due_date)
            return f"Added task: {task.title}"

        if name == "list_tasks":
            return format_tasks(task_manager.list_tasks())

        if name == "complete_task":
            task = task_manager.find_task(str(args["number"]))
            if task is None:
                return "No task with that number."
            task_manager.complete_task(task.id)
            return f"Completed: {task.title}"

        return f"Unknown tool: {name}"

    except Exception as error:
        # Tell the AI what went wrong instead of crashing the bot.
        return f"Tool error: {error}"