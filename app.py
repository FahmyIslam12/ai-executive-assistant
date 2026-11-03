from assistant.llm import get_ai_response
from assistant.memory import clear_messages, load_messages, save_messages
from assistant.tasks.manager import TaskManager


def show_help() -> None:
    print(
        "\nAvailable commands:\n"
        "/help              Show available commands\n"
        "/history           Show conversation history\n"
        "/tasks             Show saved tasks\n"
        "/addtask <title>   Add a new task\n"
        "/clear             Clear saved memory\n"
        "/exit              Close the assistant\n"
    )


def show_history(messages: list[dict[str, str]]) -> None:
    conversation = [
        message
        for message in messages
        if message.get("role") in {"user", "assistant"}
    ]

    if not conversation:
        print("\nNo conversation history yet.\n")
        return

    print("\nConversation history:")

    for message in conversation:
        speaker = "You" if message["role"] == "user" else "Assistant"
        print(f"{speaker}: {message['content']}")

    print()


def show_tasks(task_manager: TaskManager) -> None:
    tasks = task_manager.list_tasks()

    if not tasks:
        print("\nNo tasks yet.\n")
        return

    print("\nTasks:")

    for task in tasks:
        status = "✓" if task.completed else " "
        print(f"[{status}] {task.title} ({task.id})")

    print()


def main() -> None:
    messages = load_messages()
    task_manager = TaskManager()

    print("AI Executive Assistant")
    print("Type /help to see commands.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        command = user_input.lower()

        if command in {"exit", "/exit"}:
            print("Assistant: Goodbye!")
            break

        if command == "/help":
            show_help()
            continue

        if command == "/history":
            show_history(messages)
            continue

        if command == "/tasks":
            show_tasks(task_manager)
            continue

        if command.startswith("/addtask "):
            title = user_input[len("/addtask "):].strip()

            if not title:
                print("Assistant: Please provide a task title.\n")
                continue

            task = task_manager.add_task(title)
            print(f"Assistant: Added task: {task.title}\n")
            continue

        if command == "/clear":
            messages = clear_messages()
            print("Assistant: Memory cleared.\n")
            continue

        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )

        try:
            answer = get_ai_response(messages)
        except Exception as error:
            messages.pop()
            print(f"Error: {error}\n")
            continue

        messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        save_messages(messages)

        print(f"Assistant: {answer}\n")


if __name__ == "__main__":
    main()