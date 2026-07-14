import asyncio
import logging
import os

from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# Load variables stored inside the .env file.
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing from the .env file.")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from the .env file.")


# Create the Gemini client.
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
You are JobPilot, a personal AI job-application assistant.

For now, you may:
- Answer questions.
- Help write professional job-application emails.
- Suggest improvements to CV content.
- Explain AI and programming concepts simply.

You must not claim that an email has been sent.
You must not claim that a job application has been submitted.
Those capabilities will be connected later.

Keep your replies clear, practical, and concise.
"""


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Respond to the /start command."""
    del context

    if update.message:
        await update.message.reply_text(
            "Hello! I am JobPilot.\n\n"
            "Send me a question or ask me to draft a job-application email."
        )


def ask_gemini(user_message: str) -> str:
    """Send a message to Gemini and return its answer."""
    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"{SYSTEM_INSTRUCTION}\n\nUser message:\n{user_message}",
    )

    return response.text or "I could not generate a response."

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle ordinary Telegram messages."""
    del context

    if not update.message or not update.message.text:
        return

    user_message = update.message.text.strip()

    if not user_message:
        return

    await update.message.reply_text("Thinking...")

    try:
        # The Gemini SDK call is synchronous, so it runs in another thread
        # to avoid freezing the Telegram bot.
        ai_response = await asyncio.to_thread(
            ask_gemini,
            user_message,
        )

        await update.message.reply_text(ai_response)

    except Exception:
        logging.exception("The AI request failed.")

        await update.message.reply_text(
            "Something went wrong while contacting the AI. "
            "Check the Terminal for the error."
        )


def main() -> None:
    """Create and run the Telegram application."""
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    print("JobPilot is running. Press Control+C to stop it.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()