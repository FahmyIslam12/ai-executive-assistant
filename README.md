# AI Executive Assistant

A personal AI assistant you talk to through **Telegram** or the **command line**. It holds context-aware conversations using the OpenAI API, remembers past messages, and keeps a simple task list.

<p>
  <img src="docs/telegram-tasks.png" alt="Managing tasks in Telegram" width="380">
  &nbsp;
  <img src="docs/telegram-help.png" alt="Bot commands in Telegram" width="300">
</p>

## Why I built this

I'm applying to many companies, and job searching means a lot of repeated work: writing emails, tracking applications and remembering what to do next. I wanted a personal assistant that I control, instead of giving my personal accounts to a public AI tool. I also wanted to learn how AI agents work by building one myself.

Version 1 handles AI conversation and task tracking through Telegram. Version 2 will connect Gmail and help with job applications.

## What it does

- **AI chat:** ask questions or get help writing, for example a thank-you email after an interview.
- **Memory:** conversation history is saved to a JSON file and restored on restart. Only the 20 most recent messages are sent to OpenAI, to keep responses fast and costs low.
- **Task tracking:** add, list, complete and delete tasks. Each task has a unique ID and is saved to a JSON file.
- **Two interfaces:** the same features work in Telegram (on your phone) and in the terminal.

![AI drafting an email in Telegram](docs/telegram-chat.png)

## Commands

| Command | What it does |
|---|---|
| `/tasks` | Show all tasks |
| `/addtask <title>` | Add a task |
| `/done <number>` | Mark a task as completed |
| `/delete <number>` | Delete a task |
| `/help` | Show the commands |
| any other message | Chat with the AI |

The terminal version also has `/history`, `/clear` and `/exit`.

## How it works

```text
You (Telegram or terminal)
        │
        ▼
 bot.py / app.py        ← receives your message, decides what to do
        │
        ├── a task command  → assistant/tasks/  → saved in data/tasks.json
        │
        └── a normal message → assistant/llm.py → OpenAI API
                               assistant/memory.py → saved in data/memory.json
```

| File | Role |
|---|---|
| `bot.py` | Telegram interface |
| `app.py` | Command-line interface |
| `assistant/llm.py` | Sends messages to OpenAI and returns the reply |
| `assistant/memory.py` | Saves and loads conversation history |
| `assistant/tasks/` | Task model, task logic and JSON storage |

## How to run it

**1. Download the project and install what it needs**

```bash
git clone https://github.com/FahmyIslam12/ai-executive-assistant.git
cd ai-executive-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Add your keys.** Create a file named `.env` in the project folder:

```env
OPENAI_API_KEY=your_openai_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram. The `.env` file is listed in `.gitignore`, so your keys are never uploaded.

**3. Start it**

```bash
python bot.py    # Telegram bot
python app.py    # terminal version
```

## Security

- API keys are stored in `.env`, not in the code.
- The bot hides request URLs from its logs, because Telegram URLs contain the bot token.
- Account access stays in this app. OpenAI only receives the text needed for each request.

## Current limitations

- Built for one user: all Telegram chats share the same memory and task list.
- Tasks are managed with commands, not natural language ("remind me to…").
- Data is stored in JSON files, not a database.
- No automated tests yet.

## Roadmap (version 2)

- [ ] Gmail integration: read, draft and send emails
- [ ] Help with job applications
- [ ] Natural-language task management (AI decides when to create a task)
- [ ] Separate memory for each Telegram user
- [ ] Automated tests
- [ ] Test a local AI model (Ollama) for more privacy

## Tech stack

Python · OpenAI API · python-telegram-bot · JSON · Git