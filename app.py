from assistant.llm import get_ai_response
from assistant.memory import messages


def main() -> None:
    print("AI Executive Assistant")
    print("Type 'exit' to stop.\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() == "exit":
            print("Assistant: Goodbye!")
            break

        if not user_input:
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
            print(f"Error: {error}\n")
            continue

        messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        print(f"Assistant: {answer}\n")


if __name__ == "__main__":
    main()