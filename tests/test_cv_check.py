"""Job applications must be honest: every CV fact is checked word for word."""

from assistant.tools import find_unverified_facts

CV = """SKILLS
- Analysis & Tools: Problem analysis, requirements thinking, Microsoft Excel (basic), SQL and Jira (learning)
EDUCATION
- BSc in Computer Science and Engineering, University of Asia Pacific, Dhaka
"""


def test_exact_cv_phrases_are_accepted():
    facts = ["Microsoft Excel (basic)", "SQL and Jira (learning)", "University of Asia Pacific"]
    assert find_unverified_facts(facts, CV) == []


def test_exaggerated_skills_are_rejected():
    # The real exaggerations the AI made during testing.
    facts = ["Proficient in Microsoft Excel", "basic knowledge of SQL", "requirements gathering"]
    assert find_unverified_facts(facts, CV) == facts


def test_same_meaning_but_different_words_is_rejected():
    # Too strict on purpose: the AI must quote, not paraphrase.
    assert find_unverified_facts(["Bachelor of Science in Computer Science"], CV) != []


def test_capital_letters_and_punctuation_are_ignored():
    assert find_unverified_facts(["microsoft excel basic"], CV) == []


def test_facts_from_the_chat_are_allowed():
    assert find_unverified_facts(["Fahmy said: I can start immediately"], CV) == []
