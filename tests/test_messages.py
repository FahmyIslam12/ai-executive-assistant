"""Long answers must fit Telegram's limit of 4,096 characters per message."""

import bot


def test_short_answer_stays_one_message():
    assert bot.split_message("15 × 4 = 60") == ["15 × 4 = 60"]


def test_long_answer_is_split_under_the_limit_without_losing_text():
    long_answer = "\n\n".join(
        f"## Company {i}\n" + "Details about pay and culture. " * 25 for i in range(1, 8)
    )
    parts = bot.split_message(long_answer)

    assert len(parts) >= 2
    assert all(len(part) <= 4096 for part in parts)
    # Nothing lost: the same words, in the same order. (Join with a space,
    # because the cuts happen at the spaces and blank lines between parts.)
    assert " ".join(parts).split() == long_answer.split()


def test_split_happens_between_paragraphs():
    long_answer = "\n\n".join(
        f"## Company {i}\n" + "Details about pay and culture. " * 25 for i in range(1, 8)
    )
    for part in bot.split_message(long_answer)[1:]:
        assert part.startswith("## Company")  # headings stay with their text


def test_one_huge_line_is_still_split_safely():
    parts = bot.split_message("word " * 2000)
    assert all(len(part) <= 4096 for part in parts)
