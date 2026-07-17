import asyncio
import logging
import os

from assistant.llm import get_ai_response
from assistant.memory import load_messages, save_messages
from dotenv import load_dotenv
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

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing from the .env file.")


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Respond to the /start command."""
    del context

    if update.message:
        await update.message.reply_text(
            "Hello! I am your AI Executive Assistant.\n\n"
            "Send me a message and I'll do my best to help."
        )


def ask_openai(user_message: str) -> str:
    """Send a message to OpenAI using saved conversation history."""
    messages = load_messages()

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    ai_response = get_ai_response(messages)

    messages.append(
        {
            "role": "assistant",
            "content": ai_response,
        }
    )

    save_messages(messages)

    return ai_response


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
        # The OpenAI request is synchronous, so it runs in another thread
        # to avoid blocking the Telegram bot.
        ai_response = await asyncio.to_thread(
            ask_openai,
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

    print("AI Executive Assistant is running. Press Control+C to stop it.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()