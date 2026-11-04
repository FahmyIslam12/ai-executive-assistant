# AI Executive Assistant

An AI-powered executive assistant built with Python, OpenAI, and Telegram. The project combines conversational AI, persistent memory, and task management in a modular application designed for further automation and integrations.

## Overview

AI Executive Assistant provides a foundation for managing conversations and tasks through a command-line interface, with additional conversational access through Telegram.

The project focuses on API integration, persistent data storage, modular software architecture, and practical AI application development.

## Features

### AI Conversation
- Generates conversational responses using the OpenAI API.
- Maintains conversation context across messages.
- Saves and loads conversation history using local JSON storage.
- Handles API errors in the terminal interface.

### Task Management
- Creates and stores tasks with unique identifiers.
- Lists saved tasks and their completion status.
- Provides task completion and deletion operations in the task-management module.
- Persists task data in JSON across application restarts.

### Command-Line Interface

| Command | Description |
|---|---|
| `/help` | Display available commands |
| `/history` | View conversation history |
| `/tasks` | List saved tasks |
| `/addtask <title>` | Create a task |
| `/clear` | Clear conversation memory |
| `/exit` | Exit the assistant |

### Telegram Integration
- Supports conversations through a Telegram bot.
- Connects Telegram messages to the OpenAI API.
- Provides a `/start` command.
- Uses local conversation memory.

## Technology Stack

- **Language:** Python
- **AI Integration:** OpenAI API
- **Telegram:** python-telegram-bot
- **Configuration:** python-dotenv
- **Data Storage:** JSON
- **Version Control:** Git and GitHub

## Project Structure

- `app.py` — Command-line application and command handling
- `bot.py` — Telegram bot interface
- `assistant/llm.py` — OpenAI API integration
- `assistant/memory.py` — Conversation memory management
- `assistant/tasks/models.py` — Task data model
- `assistant/tasks/manager.py` — Task management operations
- `assistant/tasks/storage.py` — Persistent task storage
- `requirements.txt` — Python dependencies

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/FahmyIslam12/ai-executive-assistant.git
cd ai-executive-assistant
```

To use the current task-management development branch:

```bash
git checkout phase-2
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and add your OpenAI API key:

```env
OPENAI_API_KEY=your_openai_api_key
```

For Telegram integration, also add:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
```

Never commit real API keys or tokens to Git.

## Usage

### Run the terminal assistant

```bash
python app.py
```

Example commands:

```text
You: /addtask Prepare project documentation
Assistant: Added task: Prepare project documentation

You: /tasks
```

The assistant can also respond to ordinary conversational messages using OpenAI.

### Run the Telegram bot

```bash
python bot.py
```

The Telegram bot requires a valid bot token in the `.env` file.

## Current Limitations

- Task completion and deletion are implemented internally but are not yet available as terminal commands.
- Terminal task management currently uses explicit commands rather than natural-language actions.
- Data is stored locally using JSON rather than a database.
- Telegram conversation history is not yet isolated by user and is unsuitable for public multi-user deployment without additional safeguards.
- Automated testing and deployment infrastructure are not yet implemented.

## Planned Improvements

- Complete task-management commands in the terminal interface.
- Enable natural-language task creation and management using AI tool calling.
- Introduce a database for more reliable persistent storage.
- Add automated testing and continuous integration.
- Implement secure, user-specific Telegram memory.
- Explore calendar and email integrations.
- Improve deployment and configuration management.

## Security

API credentials are loaded from environment variables. Local `.env` files and application data are excluded from version control through `.gitignore`.

This project is under active development and is not yet configured for production or public multi-user deployment.