"""Safety rules: owner-only access, prompt-injection locks, search limits.

These tests use FAKES (stand-ins) for Telegram, Gmail, Tavily and OpenAI,
so they're free, fast, and can never send a real email.
"""

import asyncio
import json
from types import SimpleNamespace

import pytest
from openai.types.chat import ChatCompletion
from telegram.ext import ApplicationHandlerStop

import bot
from assistant import applications, gmail, llm, tools, websearch
from assistant.tasks.manager import TaskManager


# ---------- Fakes ----------

class FakeTavilyReply:
    """Pretends to be Tavily's answer to an HTTP request."""

    status_code = 200

    def json(self):
        return {"results": [{"title": "BJIT", "url": "https://example.com", "content": "A company."}]}


def fake_tavily(monkeypatch):
    """Replace the real internet call with a fake one; count the calls."""
    calls = []

    def fake_post(url, headers, json, timeout):
        calls.append(json["query"])
        return FakeTavilyReply()

    monkeypatch.setattr(websearch.httpx, "post", fake_post)
    return calls


def fake_telegram_update(user_id):
    """A pretend Telegram message from a given user."""
    replies = []

    async def reply_text(text, reply_markup=None):
        replies.append(text)

    update = SimpleNamespace(
        effective_user=SimpleNamespace(id=user_id),
        message=SimpleNamespace(reply_text=reply_text),
    )
    return update, replies


def run(tool_name, arguments):
    return tools.run_tool(tool_name, json.dumps(arguments), TaskManager())


# ---------- Owner-only access ----------

def test_owner_is_allowed():
    update, replies = fake_telegram_update(111)  # 111 = fake owner ID (conftest)
    asyncio.run(bot.owner_only(update, None))  # no exception = allowed
    assert replies == []


def test_stranger_is_blocked_and_gets_no_reply():
    update, replies = fake_telegram_update(999)
    with pytest.raises(ApplicationHandlerStop):  # stop: nothing else runs
        asyncio.run(bot.owner_only(update, None))
    assert replies == []


# ---------- Prompt-injection locks ----------

def test_tracker_is_locked_after_reading_emails(monkeypatch):
    monkeypatch.setattr(gmail, "search_emails", lambda query, max_results=5: [])
    run("search_emails", {"query": "in:inbox"})

    result = run("record_application", {"company": "Scam Corp", "role": "X", "source": "Email"})

    assert result.startswith("Not changed")
    assert "Scam Corp" not in applications.report_all()


def test_tracker_is_locked_after_reading_web_pages(monkeypatch):
    fake_tavily(monkeypatch)
    applications.record_application("BJIT", "Junior BA", "BDJobs")
    run("web_search", {"query": "BJIT news"})

    result = run("update_application_status", {"company": "BJIT", "new_status": "rejected"})

    assert result.startswith("Not changed")
    assert "status: applied" in applications.report_all()


def test_tracker_unlocks_in_a_new_message():
    # A new message starts with clean counters (done in conftest).
    result = run("record_application", {"company": "BJIT", "role": "Junior BA", "source": "BDJobs"})
    assert result.startswith("Recorded")


def test_email_and_web_text_are_labelled_as_data(monkeypatch):
    fake_tavily(monkeypatch)
    monkeypatch.setattr(gmail, "search_emails", lambda query, max_results=5: [{"id": "1"}])

    assert run("web_search", {"query": "BJIT"}).startswith("The following are WEB SEARCH RESULTS")
    assert run("search_emails", {"query": "in:inbox"}).startswith("The following is EMAIL CONTENT")


def test_the_ai_has_no_send_tool():
    names = [tool["function"]["name"] for tool in tools.TOOLS]
    assert not any("send" in name for name in names)


# ---------- Web search limits ----------

def test_at_most_three_searches_per_message(monkeypatch):
    calls = fake_tavily(monkeypatch)
    for query in ["a", "b", "c"]:
        run("web_search", {"query": query})

    fourth = run("web_search", {"query": "d"})

    assert fourth.startswith("Search limit reached")
    assert calls == ["a", "b", "c"]  # the 4th never reached Tavily


def test_search_with_an_email_address_is_blocked(monkeypatch):
    calls = fake_tavily(monkeypatch)
    result = run("web_search", {"query": "hr@bjit.com salary"})

    assert result.startswith("Blocked")
    assert calls == []  # private data never left the computer


def test_search_limit_resets_for_each_message(monkeypatch):
    """Uses a FAKE OpenAI that asks for 4 searches in one message."""
    calls = fake_tavily(monkeypatch)
    rounds = []

    def reply(message):
        return ChatCompletion.model_validate({
            "id": "x", "object": "chat.completion", "created": 0, "model": "fake",
            "choices": [{"index": 0, "finish_reason": "stop", "message": message}],
        })

    def fake_openai(**kwargs):
        rounds.append(1)
        if len(rounds) % 2 == 1:  # first round of each message: ask for 4 searches
            return reply({"role": "assistant", "content": None, "tool_calls": [
                {"id": f"c{i}", "type": "function",
                 "function": {"name": "web_search", "arguments": json.dumps({"query": f"q{i}"})}}
                for i in range(4)
            ]})
        return reply({"role": "assistant", "content": "Done."})

    monkeypatch.setattr(llm.client.chat.completions, "create", fake_openai)
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "compare"}]

    llm.get_ai_response(messages, TaskManager())
    assert len(calls) == 3  # first message: stopped at 3

    llm.get_ai_response(messages, TaskManager())
    assert len(calls) == 6  # second message: 3 more allowed
