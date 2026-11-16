import asyncio
import logging
import os
from datetime import date, time
from zoneinfo import ZoneInfo

from assistant import gmail
from assistant.llm import get_ai_response
from assistant.memory import load_messages, save_messages
from assistant.reminders import build_reminder, load_chat_id, save_chat_id
from assistant.tasks.manager import TaskManager, format_tasks
from assistant.tools import pop_new_drafts
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    TypeHandler,
    filters,
)


# Load variables stored inside the .env file.
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is missing from the .env file.")

# Only this Telegram user may use the bot. Anyone else could otherwise
# find the bot and ask it to read Fahmy's email.
OWNER_ID = os.getenv("TELEGRAM_OWNER_ID", "").strip()

task_manager = TaskManager()

# When the daily reminder is sent (Bangladesh time).
REMINDER_TIME = time(hour=9, minute=00, tzinfo=ZoneInfo("Asia/Dhaka"))

HELP_TEXT = (
    "Commands:\n"
    "/tasks - Show your tasks\n"
    "/addtask <title> - Add a task\n"
    "/done <number> - Mark a task as completed\n"
    "/delete <number> - Delete a task\n"
    "/remind - Show tasks due today or overdue\n"
    "/help - Show this message\n\n"
    "Or just send me a message to chat."
)


async def owner_only(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Runs before everything else and blocks anyone who isn't the owner."""
    del context
    user = update.effective_user

    if user and OWNER_ID and str(user.id) == OWNER_ID:
        return  # The owner: let the other handlers run.

    if update.message and not OWNER_ID and user:
        # First-time setup: tell the person their ID so they can add it.
        await update.message.reply_text(
            f"Setup needed. Your Telegram user ID is {user.id}.\n"
            f"Add this line to the .env file, then restart the bot:\n"
            f"TELEGRAM_OWNER_ID={user.id}"
        )

    # Stop here: no other handler runs for this update.
    raise ApplicationHandlerStop


async def remember_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Save the chat ID from every message, so reminders know where to go."""
    del context

    if update.effective_chat:
        save_chat_id(update.effective_chat.id)


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


async def remind_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Check for due tasks right now. Useful for testing."""
    del context

    if not update.message:
        return

    reminder = build_reminder(task_manager.list_tasks(), date.today())
    await update.message.reply_text(
        reminder or "Nothing is due today or overdue. 🎉"
    )


async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Runs automatically every day at REMINDER_TIME."""
    chat_id = load_chat_id()

    if chat_id is None:
        # Nobody has messaged the bot yet, so we don't know where to send.
        return

    reminder = build_reminder(task_manager.list_tasks(), date.today())

    if reminder:
        await context.bot.send_message(chat_id=chat_id, text=reminder)


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

        # Show every draft the AI created, with Send and Cancel buttons.
        for draft in pop_new_drafts():
            await show_draft(update, draft)

    except Exception:
        logging.exception("The AI request failed.")

        await update.message.reply_text(
            "Something went wrong while contacting the AI. "
            "Check the Terminal for the error."
        )


async def show_draft(update: Update, draft: dict[str, str]) -> None:
    """Send a draft preview with Send and Cancel buttons."""
    if not update.message:
        return

    body = draft["body"]
    if len(body) > 3000:  # Telegram messages have a size limit.
        body = body[:3000] + "\n[...see the full draft in Gmail...]"

    attachment = draft["attachment"] or "none"
    facts = draft.get("cv_facts_used") or "- (none listed)"
    preview = (
        "📝 DRAFT (not sent yet)\n\n"
        f"To: {draft['to']}\n"
        f"Subject: {draft['subject']}\n"
        f"Attachment: {attachment}\n\n"
        f"{body}\n\n"
        "🔎 Based on your CV (checked word for word by the code):\n"
        f"{facts}\n\n"
        "Check: every claim above should come from this list. "
        "You can edit it in the Gmail app (Drafts) before pressing Send."
    )

    # Each button carries the action and the draft's ID.
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Send", callback_data=f"send:{draft['draft_id']}"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{draft['draft_id']}"),
            ]
        ]
    )

    await update.message.reply_text(preview, reply_markup=buttons)


async def handle_draft_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Runs when Fahmy presses Send or Cancel. The ONLY place that sends."""
    del context
    query = update.callback_query

    if not query or not query.data:
        return

    await query.answer()  # Stops the button's loading spinner.
    action, _, draft_id = query.data.partition(":")

    try:
        if action == "send":
            await asyncio.to_thread(gmail.send_draft, draft_id)
            result = "✅ Sent."
        elif action == "cancel":
            await asyncio.to_thread(gmail.delete_draft, draft_id)
            result = "❌ Cancelled. The draft was deleted."
        else:
            return
    except Exception:
        logging.exception("Draft button failed.")
        result = (
            "⚠️ That didn't work. The draft may already be sent or deleted "
            "in Gmail, or the Gmail login expired."
        )

    # Replace the buttons with the result, so they can't be pressed twice.
    await query.edit_message_reply_markup(reply_markup=None)
    if query.message:
        await query.message.reply_text(result)


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

    # Lower group numbers run first. group=-2: block everyone except the
    # owner. group=-1: remember the owner's chat for reminders.
    application.add_handler(TypeHandler(Update, owner_only), group=-2)
    application.add_handler(TypeHandler(Update, remember_chat), group=-1)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("tasks", tasks_command))
    application.add_handler(CommandHandler("addtask", addtask_command))
    application.add_handler(CommandHandler("done", done_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("remind", remind_command))
    application.add_handler(CallbackQueryHandler(handle_draft_button))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message,
        )
    )

    # The JobQueue is the bot's built-in scheduler.
    if application.job_queue is None:
        raise RuntimeError(
            'Reminders need the scheduler. Run: pip install -r requirements.txt'
        )

    application.job_queue.run_daily(send_daily_reminder, time=REMINDER_TIME)

    print("AI Executive Assistant is running. Press Control+C to stop it.")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
    )


if __name__ == "__main__":
    main()