# AI Executive Assistant

An AI-powered executive assistant built with Python, OpenAI, and Telegram, combining conversational AI, persistent memory, and task management in a modular application.

## Overview

AI Executive Assistant is a Python application designed to support everyday productivity through AI-powered conversations and structured task management.

The project provides a command-line interface for interacting with an AI assistant and managing tasks, alongside a Telegram bot for conversational access.

Its architecture separates user interfaces, AI integration, conversation memory, and task-management logic to support future expansion into more advanced automation workflows.

## Features

### AI-Powered Conversations

- Generates conversational responses using the OpenAI API.
- Maintains conversation context across messages.
- Saves conversation history locally in JSON format.
- Restores saved conversation history between sessions.
- Handles API errors in the command-line interface.

### Task Management

- Creates tasks with unique identifiers.
- Stores tasks persistently in JSON format.
- Lists tasks and their completion status.
- Supports task completion and deletion through the task-management module.
- Preserves saved tasks between application restarts.

### Command-Line Interface

| Command | Description |
|---|---|
| `/help` | Display available commands |
| `/history` | View saved conversation history |
| `/tasks` | Display saved tasks |
| `/addtask <title>` | Create a new task |
| `/clear` | Clear conversation memory |
| `/exit` | Exit the assistant |

Task completion and deletion commands are planned for the command-line interface.

### Telegram Bot

- Provides conversational AI responses through Telegram.
- Connects Telegram messages to the OpenAI API.
- Supports the `/start` command.
- Uses local conversation history.

The Telegram implementation currently uses shared conversation memory and is not intended for public multi-user deployment.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| OpenAI API | AI-powered conversations |
| python-telegram-bot | Telegram integration |
| python-dotenv | Environment variable configuration |
| JSON | Local data persistence |
| Git and GitHub | Version control and source hosting |

## Project Structure

```text
ai-executive-assistant/
├── assistant/
│   ├── __init__.py
│   ├── llm.py
│   ├── memory.py
│   └── tasks/
│       ├── __init__.py
│       ├── models.py
│       ├── manager.py
│       └── storage.py
├── data/
├── app.py
├── bot.py
├── requirements.txt
├── .gitignore
└── README.md
```

### Main Components

- **app.py:** Command-line interface and command handling.
- **bot.py:** Telegram bot integration.
- **assistant/llm.py:** OpenAI API communication.
- **assistant/memory.py:** Conversation history management.
- **assistant/tasks/models.py:** Task data model.
- **assistant/tasks/manager.py:** Task creation, listing, completion, and deletion logic.
- **assistant/tasks/storage.py:** JSON-based task persistence.

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/FahmyIslam12/ai-executive-assistant.git
cd ai-executive-assistant
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

For Windows:

```powershell
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key
```

To use Telegram, also provide your bot token:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Never commit real API keys, bot tokens, or other credentials to GitHub.

## Usage

### Command-Line Assistant

Start the assistant:

```bash
python app.py
```

Example interaction:

```text
AI Executive Assistant
Type /help to see commands.

You: /addtask Prepare project documentation
Assistant: Added task: Prepare project documentation

You: /tasks

Tasks:
[ ] Prepare project documentation (...)
```

You can also send ordinary messages to the assistant to receive AI-generated responses.

### Telegram Bot

Start the Telegram interface:

```bash
python bot.py
```

A valid Telegram bot token must be configured in your `.env` file.

## Current Limitations

- Task completion and deletion are implemented in the task-management module but are not yet exposed through CLI commands.
- Task management currently relies on explicit commands rather than natural-language instructions.
- Conversation history and tasks use local JSON files instead of a database.
- Telegram conversations are not isolated by individual user.
- Persistent storage needs stronger error handling and concurrency protection.
- Automated tests, continuous integration, and deployment configuration are not yet implemented.

## Development Roadmap

The following capabilities are planned:

- [ ] Complete CLI task-management commands.
- [ ] Add automated tests for task operations and persistence.
- [ ] Improve configuration and error handling.
- [ ] Implement user-specific Telegram conversation memory.
- [ ] Add AI tool calling for natural-language task management.
- [ ] Introduce database-backed storage.
- [ ] Set up continuous integration with GitHub Actions.
- [ ] Explore calendar and email integrations.
- [ ] Prepare a reproducible deployment and demonstration.

## Security

API keys and bot tokens are configured through environment variables rather than embedded directly in application source code.

Local configuration files and application data are excluded from version control through `.gitignore`.

The project is under active development and has not yet been hardened for production or public multi-user use.

## Project Status

The application currently supports OpenAI-powered conversations, persistent conversation memory, JSON-based task management, a command-line interface, and Telegram integration.

Additional functionality, reliability improvements, and automated testing are being developed incrementally.