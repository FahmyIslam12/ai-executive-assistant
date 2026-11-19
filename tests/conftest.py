"""Shared setup for all tests. pytest reads this file automatically.

It builds a safe "fake world" for every test:
- fake API keys, so nothing can reach the real OpenAI, Telegram or Tavily
- a fresh, empty folder, so tests never touch your real database or files
- blockers that make a test FAIL if it tries to call a real outside service
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Set fake keys BEFORE any project file is imported. The project's
# load_dotenv() never overwrites values that already exist, so your real
# keys in .env are never used during tests.
os.environ["OPENAI_API_KEY"] = "sk-test-fake"
os.environ["TELEGRAM_BOT_TOKEN"] = "123:test-fake"
os.environ["TELEGRAM_OWNER_ID"] = "111"
os.environ["TAVILY_API_KEY"] = "tvly-test-fake"

# Let tests import the project's files (bot.py, assistant/...).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))



def pytest_sessionstart(session):
    """A pytest "hook": pytest calls it after finding the tests folder and
    BEFORE loading any test file.

    We move into an empty temporary folder here, because bot.py opens the
    database as soon as it's loaded; without this, the REAL data/ folder
    could be touched. (Doing it any earlier hides the tests folder from
    pytest.)
    """
    os.chdir(tempfile.mkdtemp(prefix="assistant-tests-"))


@pytest.fixture(autouse=True)
def fake_world(tmp_path, monkeypatch):
    """Runs automatically before EVERY test.

    monkeypatch swaps something for a fake during one test only; after the
    test, everything is put back automatically.
    """
    from assistant import database, gmail, llm, tools, websearch

    # 1. Work inside a brand-new empty folder. The project uses paths like
    #    data/assistant.db, so each test gets its own fresh database.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(database, "_ready", False)

    # 2. Block real outside services. If a test forgets to use a fake,
    #    it fails loudly instead of calling the real service.
    def no_real_gmail(*args, **kwargs):
        raise AssertionError("A test tried to use the real Gmail.")

    def no_real_internet(*args, **kwargs):
        raise AssertionError("A test tried to use the real internet (Tavily).")

    def no_real_openai(*args, **kwargs):
        raise AssertionError("A test tried to call the real OpenAI.")

    monkeypatch.setattr(gmail, "get_service", no_real_gmail)
    monkeypatch.setattr(websearch.httpx, "post", no_real_internet)

    monkeypatch.setattr(llm.client.chat.completions, "create", no_real_openai)

    # 3. Start every test with clean per-message counters.
    tools.reset_search_count()
    tools.pop_used_gmail()
    tools.pop_new_drafts()

    yield tmp_path
