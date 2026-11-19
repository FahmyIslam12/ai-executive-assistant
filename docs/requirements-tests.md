# Stage 4 Requirements: Automated Tests

**Status:** Complete (20 Nov 2026) · **Date:** 20 Nov 2026 · **Owner:** Fahmy Islam

## 1. Problem

Every code change can break something that used to work, without anyone noticing. Until now, checks were done by hand before each update, which is slow and easy to forget.

## 2. Goal

One command (`pytest`) checks all the important behavior in about a second, using fakes instead of real outside services.

## 3. User stories

1. As the developer, I want one command that checks all the important behavior, so that I know a change didn't break anything.
2. As a business analyst, I want the tests to follow my acceptance criteria, so that requirements and checks stay connected.

## 4. What is tested (35 tests)

| File | Checks | Comes from |
|---|---|---|
| `test_tasks.py` | add, complete, delete, numbering, saved after restart | Version 1 |
| `test_cv_check.py` | exact CV phrases accepted; exaggerations ("proficient in Excel") rejected | Stage 1b test findings |
| `test_tracker.py` | recording, no duplicates, one row per company, status history, invalid statuses refused, labeled dates, all reports | Stage 2 requirements |
| `test_safety.py` | owner-only access, tracker locked after reading emails or web pages, no send tool, 3-search limit, email addresses blocked in searches | Stages 1-3 must-NOTs |
| `test_messages.py` | long answers split under Telegram's 4,096-character limit, nothing lost | Stage 3 test findings |
| `test_migration.py` | JSON data moved once, with a backup, never duplicated | Stage 2 safety rules |

## 5. How the tests stay safe (fakes)

- Fake API keys are set before any project file loads; the real keys in `.env` are never used.
- Every test runs in its own empty temporary folder, with a fresh database. The real `data/` folder is never touched.
- Gmail, Tavily (internet) and OpenAI are blocked: a test that tries to use a real service fails immediately. Tests that need them use fakes (`monkeypatch`), for example a fake OpenAI that asks for 4 searches in one message.

## 6. The tests must NOT

1. Call the real OpenAI, Gmail, Telegram or Tavily (cost money, could send real emails).
2. Touch the real database or files.

## 7. How we know it works (acceptance criteria)

- [x] `pytest` runs all tests and they pass (35 passed, under 1 second).
- [x] Breaking the code on purpose makes a test fail:
  - raising the search limit from 3 to 5 → 2 tests failed ✅
  - removing the status check when recording an application → **no test failed** at first. A missing test was added; now 1 test fails, and the database's own `CHECK` rule also refuses the bad status (defence in depth).

### Test findings

| Finding | Fix |
|---|---|
| Loading `bot.py` opens the database immediately, and pytest loads test files before the fake folder is set up, so the real `data/` folder could be touched | The test setup moves into an empty temporary folder before loading any project file |
| One test failed because the test itself was wrong (it joined message parts without spaces) | Fixed the test. Tests can have bugs too, so a failure needs investigating, not just fixing the code |
| Deliberately breaking a rule showed one rule had no test watching it | Added the missing test. "Break it on purpose" is now part of how tests are checked |

## 8. Known limitations

- Tests check my code's logic with fakes. They can't prove the real services behave the same way (for example, Telegram's real limits or Tavily's real replies), so real-world testing in Telegram is still needed for new features.
- The tests don't check the AI's judgment (for example, whether it writes a good email). Those are checked by people.
