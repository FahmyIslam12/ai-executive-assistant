import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY is missing from the .env file.")

client = OpenAI(api_key=api_key)

# How many recent messages to send to OpenAI. Older ones stay saved in
# memory.json but are not sent, which keeps requests fast and cheap.
MAX_RECENT_MESSAGES = 20


def get_ai_response(messages: list[dict[str, str]]) -> str:
    system_messages = [m for m in messages if m.get("role") == "system"]
    conversation = [m for m in messages if m.get("role") != "system"]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=system_messages + conversation[-MAX_RECENT_MESSAGES:],
    )

    return response.choices[0].message.content or ""