"""Job-application tracker: recording, status changes, and reports."""

import sqlite3
from datetime import date, timedelta

from assistant import applications as tracker


def days_ago(n):
    return (date.today() - timedelta(days=n)).isoformat()


def test_record_application():
    result = tracker.record_application("BJIT", "Junior BA", "BDJobs", applied_date=days_ago(1))
    assert result.startswith("Recorded")
    assert "BJIT" in tracker.report_all()


def test_same_application_is_not_recorded_twice():
    tracker.record_application("BJIT", "Junior BA", "BDJobs")
    second = tracker.record_application("bjit", "junior ba", "BDJobs")  # different capitals
    assert second.startswith("Already recorded")
    assert tracker.report_all().startswith("All applications (1)")


def test_company_is_stored_once():
    tracker.record_application("BJIT", "Junior BA", "BDJobs")
    tracker.record_application("bjit", "Support Engineer", "Email")

    connection = sqlite3.connect("data/assistant.db")
    companies = connection.execute("SELECT name FROM companies").fetchall()
    connection.close()
    assert companies == [("BJIT",)]  # normalization: one row, two applications


def test_status_change_is_saved_with_history():
    tracker.record_application("BJIT", "Junior BA", "BDJobs")
    result = tracker.update_status("BJIT", "interview", follow_up_date="2026-11-25")
    assert "applied → interview" in result

    connection = sqlite3.connect("data/assistant.db")
    history = connection.execute(
        "SELECT old_status, new_status FROM status_history ORDER BY id"
    ).fetchall()
    connection.close()
    assert history == [(None, "applied"), ("applied", "interview")]


def test_invalid_status_is_refused_when_updating():
    tracker.record_application("BJIT", "Junior BA", "BDJobs")
    assert tracker.update_status("BJIT", "hacked").startswith("Unknown status")


def test_invalid_status_is_refused_when_recording():
    # Added after deliberately breaking this rule showed no test caught it.
    result = tracker.record_application("BJIT", "Junior BA", "BDJobs", status="hacked")
    assert result.startswith("Unknown status")
    assert tracker.report_all() == "No applications recorded yet."


def test_ambiguous_company_asks_which_role():
    tracker.record_application("BJIT", "Junior BA", "BDJobs")
    tracker.record_application("BJIT", "Support Engineer", "Email")
    assert tracker.update_status("BJIT", "rejected").startswith("Several applications match")


def test_report_dates_are_labeled():
    # Regression test for the bug where the AI read the applied date as
    # the interview date: every date in the report must have a label.
    tracker.record_application("BJIT", "Junior BA", "BDJobs", applied_date="2026-11-18")
    tracker.update_status("BJIT", "interview", follow_up_date="2026-11-25")

    report = tracker.report_all()
    assert "applied: 2026-11-18" in report
    assert "interview date: 2026-11-25" in report


def test_reports_answer_the_job_search_questions():
    tracker.record_application("BJIT", "Junior BA", "BDJobs", applied_date=days_ago(10))
    tracker.record_application("Brain Station 23", "Coordinator", "LinkedIn", applied_date=days_ago(9))
    tracker.record_application("DataSoft", "Junior BA", "Email", applied_date=days_ago(1))
    tracker.update_status("BJIT", "interview")

    assert tracker.report_this_week().startswith("Applications in the last 7 days: 1")
    no_reply = tracker.report_no_reply()
    assert "Brain Station 23" in no_reply and "BJIT" not in no_reply
    assert "- applied: 2" in tracker.report_by_status()
    assert tracker.report_by_source().splitlines()[1].startswith("- BDJobs: 1 interview(s)")
    assert "BJIT" in tracker.report_upcoming_interviews()


def test_follow_ups_due_appear_for_reminders():
    tracker.record_application("BJIT", "Junior BA", "BDJobs", follow_up_date=days_ago(1))
    assert len(tracker.follow_ups_due(date.today())) == 1
