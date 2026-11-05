import asyncio
import logging
import os

from assistant.llm import get_ai_response
from assistant.memory import load_messages, save_messages
from assistant.tasks.manager import TaskManager, format_tasks
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

task_manager = TaskManager()

HELP_TEXT = (
    "Commands:\n"
    "/tasks - Show your tasks\n"
    "/addtask <title> - Add a task\n"
    "/done <number> - Mark a task as completed\n"
    "/delete <number> - Delete a task\n"
    "/help - Show this message\n\n"
    "Or just send me a message to chat."
)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Respond to the /start command."""
    del context

    if update.message:
        await update.message.reply_text(
            "Hello! I am your AI Executive Assistant.\n\n"
            "Send me a message and I'll do my best to help.\n\n"
            + HELP_TEXT
        )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Respond to the /help command."""
    del context

    if update.message:
        await update.message.reply_text(HELP_TEXT)


async def tasks_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Show all saved tasks."""
    del context

    if update.message:
        await update.message.reply_text(
            "Tasks:\n" + format_tasks(task_manager.list_tasks())
        )


async def addtask_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Add a task. Usage: /addtask Prepare CV"""
    if not update.message:
        return

    # context.args holds the words typed after the command.
    title = " ".join(context.args).strip()

    if not title:
        await update.message.reply_text("Usage: /addtask <title>")
        return

    task = task_manager.add_task(title)
    await update.message.reply_text(f"Added task: {task.title}")


async def done_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Mark a task as completed. Usage: /done 2"""
    if not update.message:
        return

    task = task_manager.find_task(" ".join(context.args))

    if task is None:
        await update.message.reply_text(
            "Task not found. Use /tasks to see the numbers."
        )
        return

    task_manager.complete_task(task.id)
    await update.message.reply_text(f"Completed: {task.title}")


async def delete_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Delete a task. Usage: /delete 2"""
    if not update.message:
        return

    task = task_manager.find_task(" ".join(context.args))

    if task is None:
        await update.message.reply_text(
            "Task not found. Use /tasks to see the numbers."
        )
        return

    task_manager.delete_task(task.id)
    await update.message.reply_text(f"Deleted: {task.title}")


def ask_openai(user_message: str) -> str:
    """Send a message to OpenAI using saved conversation history."""
    messages = load_messages()

    messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    ai_response = get_ai_response(messages, task_manager)
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

    # httpx logs every request URL, and Telegram URLs contain the bot
    # token. Only show its warnings so the token never appears in logs.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("addtask", addtask_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("delete", delete_command))
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