import os
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI

from assistant.tasks.manager import TaskManager
from assistant.tools import TOOLS, run_tool

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is missing from the .env file.")

client = OpenAI(api_key=api_key)

MODEL = "gpt-4.1-mini"

# How many recent messages to send to OpenAI. Older ones stay saved in
# memory.json but are not sent, which keeps requests fast and cheap.
MAX_RECENT_MESSAGES = 20

# Safety limit: how many rounds of tool use are allowed for one message.
MAX_TOOL_ROUNDS = 5


def get_ai_response(
    messages: list[dict[str, str]],
    task_manager: TaskManager,
) -> str:
    system_messages = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]

    # The AI doesn't know today's date, so we tell it.
    # Without this, "Friday" or "tomorrow" can't become a real date.
    today = date.today()
    date_note = {
        "role": "system",
        "content": f"Today is {today.strftime('%A')}, {today.isoformat()}.",
    }

    # This list exists only for this one request. Tool steps are not
    # saved to memory.json; only the final answer is.
    request = system_messages + [date_note] + conversation[-MAX_RECENT_MESSAGES:]

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.chat.completions.create(
            model=MODEL,
            messages=request,
            tools=TOOLS,
        )
        reply = response.choices[0].message

        # No tool requested: this is the final answer for the user.
        if not reply.tool_calls:
            return reply.content or ""

        # The AI asked for one or more tools. Remember its request...
        request.append(reply.model_dump(exclude_none=True))

        # ...run each tool, and send the results back to the AI.
        for tool_call in reply.tool_calls:
            result = run_tool(
                tool_call.function.name,
                tool_call.function.arguments,
                task_manager,
            )
            request.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

    return "Sorry, that took too many steps. Please try again."