from assistant.llm import get_ai_response
from assistant.memory import clear_messages, load_messages, save_messages


def show_help() -> None:
    print(
        "\nAvailable commands:\n"
        "/help     Show available commands\n"
        "/history  Show conversation history\n"
        "/clear    Clear saved memory\n"
        "/exit     Close the assistant\n"
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


def main() -> None:
    messages = load_messages()

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