"""Job-application tracker: record applications, update statuses, and answer
questions with FIXED SQL queries.

Safety: the AI never writes SQL. It can only choose one of the reports in
REPORTS below. Every value from outside is passed with "?" placeholders,
never pasted into the SQL text, which prevents SQL injection.
"""

from datetime import date, timedelta
from typing import Optional

from assistant.database import connect, now

STATUSES = ["saved", "applied", "interview", "offer", "rejected", "no response"]
SOURCES = ["Email", "BDJobs", "LinkedIn", "Other"]


def _company_id(connection, name: str) -> int:
    """Return the company's ID, adding the company the first time we see it."""
    name = name.strip()
    row = connection.execute(
        "SELECT id FROM companies WHERE name = ?", (name,)
    ).fetchone()
    if row:
        return row["id"]
    return connection.execute(
        "INSERT INTO companies (name) VALUES (?)", (name,)
    ).lastrowid


def record_application(
    company: str,
    role: str,
    source: str,
    status: str = "applied",
    applied_date: Optional[str] = None,
    contact_email: Optional[str] = None,
    job_link: Optional[str] = None,
    notes: Optional[str] = None,
    follow_up_date: Optional[str] = None,
) -> str:
    """Add an application and its first status-history row."""
    if status not in STATUSES:
        return f"Unknown status '{status}'. Use one of: {', '.join(STATUSES)}."
    if source not in SOURCES:
        source = "Other"

    if status != "saved" and not applied_date:
        applied_date = date.today().isoformat()

    connection = connect()

    # Avoid recording the same application twice.
    existing = connection.execute(
        "SELECT a.id FROM applications a JOIN companies c ON c.id = a.company_id "
        "WHERE c.name = ? AND a.role = ? COLLATE NOCASE",
        (company.strip(), role.strip()),
    ).fetchone()
    if existing:
        connection.close()
        return f"Already recorded: {role} at {company}."

    with connection:
        company_id = _company_id(connection, company)

        application_id = connection.execute(
            "INSERT INTO applications (company_id, role, status, source, "
            "applied_date, contact_email, job_link, notes, follow_up_date, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (company_id, role.strip(), status, source, applied_date,
             contact_email, job_link, notes, follow_up_date, now()),
        ).lastrowid

        connection.execute(
            "INSERT INTO status_history (application_id, old_status, new_status, "
            "changed_at) VALUES (?, NULL, ?, ?)",
            (application_id, status, now()),
        )

    connection.close()
    return f"Recorded: {role} at {company} ({status}, via {source})."


def update_status(
    company: str,
    new_status: str,
    role: Optional[str] = None,
    follow_up_date: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    """Change an application's status and add a status-history row.
    Applications are never deleted: only their status changes."""
    if new_status not in STATUSES:
        return f"Unknown status '{new_status}'. Use one of: {', '.join(STATUSES)}."

    connection = connect()

    # JOIN: combine each application with its company's name.
    sql = (
        "SELECT a.id, a.role, a.status, c.name AS company "
        "FROM applications a JOIN companies c ON c.id = a.company_id "
        "WHERE c.name LIKE ?"
    )
    params: list = [f"%{company.strip()}%"]
    if role:
        sql += " AND a.role LIKE ?"
        params.append(f"%{role.strip()}%")

    matches = connection.execute(sql, params).fetchall()

    if not matches:
        connection.close()
        return f"No application found for '{company}'. Record it first."
    if len(matches) > 1:
        connection.close()
        options = "; ".join(f"{m['role']} at {m['company']}" for m in matches)
        return f"Several applications match: {options}. Ask Fahmy which role."

    app = matches[0]
    with connection:
        connection.execute(
            "UPDATE applications SET status = ?, "
            "follow_up_date = COALESCE(?, follow_up_date), "
            "notes = COALESCE(?, notes) WHERE id = ?",
            (new_status, follow_up_date, notes, app["id"]),
        )
        connection.execute(
            "INSERT INTO status_history (application_id, old_status, new_status, "
            "changed_at) VALUES (?, ?, ?, ?)",
            (app["id"], app["status"], new_status, now()),
        )
    connection.close()
    return (
        f"Updated: {app['role']} at {app['company']}: "
        f"{app['status']} → {new_status}."
    )


# ---------------------------------------------------------------------------
# Draft links: remember which Gmail draft is a job application.
# ---------------------------------------------------------------------------

def save_draft_link(draft_id: str, company: str, role: str,
                    contact_email: Optional[str], job_link: Optional[str]) -> None:
    connection = connect()
    with connection:
        connection.execute(
            "INSERT OR REPLACE INTO draft_links "
            "(draft_id, company, role, contact_email, job_link) VALUES (?, ?, ?, ?, ?)",
            (draft_id, company, role, contact_email, job_link),
        )
    connection.close()


def pop_draft_link(draft_id: str) -> Optional[dict]:
    """Return and remove the job linked to a draft (None if it isn't one)."""
    connection = connect()
    row = connection.execute(
        "SELECT * FROM draft_links WHERE draft_id = ?", (draft_id,)
    ).fetchone()
    with connection:
        connection.execute("DELETE FROM draft_links WHERE draft_id = ?", (draft_id,))
    connection.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Reports: the ONLY queries the AI can run. Each one is fixed SQL.
# ---------------------------------------------------------------------------

def _rows(sql: str, params: tuple = ()) -> list:
    connection = connect()
    rows = connection.execute(sql, params).fetchall()
    connection.close()
    return rows


def report_this_week() -> str:
    """How many jobs did I apply to in the last 7 days?"""
    since = (date.today() - timedelta(days=6)).isoformat()
    rows = _rows(
        "SELECT c.name AS company, a.role, a.source FROM applications a "
        "JOIN companies c ON c.id = a.company_id "
        "WHERE a.applied_date >= ? ORDER BY a.applied_date",
        (since,),
    )
    lines = [f"Applications in the last 7 days: {len(rows)}"]
    lines += [f"- {r['role']} at {r['company']} ({r['source']})" for r in rows]
    return "\n".join(lines)


def report_no_reply(days: int = 7) -> str:
    """Which companies haven't replied in 7 days? (still 'applied')"""
    before = (date.today() - timedelta(days=days)).isoformat()
    rows = _rows(
        "SELECT c.name AS company, a.role, a.applied_date, a.contact_email "
        "FROM applications a JOIN companies c ON c.id = a.company_id "
        "WHERE a.status = 'applied' AND a.applied_date <= ? "
        "ORDER BY a.applied_date",
        (before,),
    )
    if not rows:
        return f"No applications waiting more than {days} days."
    lines = [f"No reply after {days}+ days ({len(rows)}):"]
    lines += [
        f"- {r['role']} at {r['company']}, applied {r['applied_date']}"
        + (f" ({r['contact_email']})" if r["contact_email"] else "")
        for r in rows
    ]
    return "\n".join(lines)


def report_by_status() -> str:
    """Show my applications grouped by status."""
    rows = _rows(
        "SELECT status, COUNT(*) AS total FROM applications "
        "GROUP BY status ORDER BY total DESC"
    )
    if not rows:
        return "No applications recorded yet."
    return "Applications by status:\n" + "\n".join(
        f"- {r['status']}: {r['total']}" for r in rows
    )


def report_by_source() -> str:
    """Which platform gets me the most interviews?"""
    # LEFT JOIN keeps applications even if they have no interview row.
    rows = _rows(
        "SELECT a.source, COUNT(DISTINCT a.id) AS applied, "
        "COUNT(DISTINCT CASE WHEN h.new_status = 'interview' THEN a.id END) "
        "AS interviews "
        "FROM applications a "
        "LEFT JOIN status_history h ON h.application_id = a.id "
        "GROUP BY a.source ORDER BY interviews DESC, applied DESC"
    )
    if not rows:
        return "No applications recorded yet."
    return "Interviews by platform:\n" + "\n".join(
        f"- {r['source']}: {r['interviews']} interview(s) from {r['applied']} application(s)"
        for r in rows
    )


def report_upcoming_interviews() -> str:
    """What interviews do I have coming up?"""
    rows = _rows(
        "SELECT c.name AS company, a.role, a.follow_up_date FROM applications a "
        "JOIN companies c ON c.id = a.company_id "
        "WHERE a.status = 'interview' "
        "ORDER BY a.follow_up_date IS NULL, a.follow_up_date"
    )
    if not rows:
        return "No interviews scheduled."
    return "Interviews:\n" + "\n".join(
        f"- {r['role']} at {r['company']}"
        + (f" | interview date: {r['follow_up_date']}" if r["follow_up_date"]
           else " | interview date: not set")
        for r in rows
    )


def report_all() -> str:
    """List every application with its status and clearly labeled dates."""
    rows = _rows(
        "SELECT c.name AS company, a.role, a.status, a.source, a.applied_date, "
        "a.follow_up_date FROM applications a "
        "JOIN companies c ON c.id = a.company_id "
        "ORDER BY a.applied_date DESC"
    )
    if not rows:
        return "No applications recorded yet."

    lines = [f"All applications ({len(rows)}):"]
    for r in rows:
        # Every date gets a label, so the AI can't mix them up.
        line = (
            f"- {r['role']} at {r['company']} | status: {r['status']} "
            f"| via {r['source']} | applied: {r['applied_date'] or 'not yet'}"
        )
        if r["follow_up_date"]:
            label = "interview date" if r["status"] == "interview" else "follow-up date"
            line += f" | {label}: {r['follow_up_date']}"
        lines.append(line)
    return "\n".join(lines)


REPORTS = {
    "this_week": report_this_week,
    "no_reply": report_no_reply,
    "by_status": report_by_status,
    "by_source": report_by_source,
    "upcoming_interviews": report_upcoming_interviews,
    "all": report_all,
}


def follow_ups_due(today: date) -> list[str]:
    """Applications whose follow-up date is today or earlier (for reminders)."""
    rows = _rows(
        "SELECT c.name AS company, a.role, a.status, a.follow_up_date "
        "FROM applications a JOIN companies c ON c.id = a.company_id "
        "WHERE a.follow_up_date IS NOT NULL AND a.follow_up_date <= ? "
        "AND a.status IN ('applied', 'interview') ORDER BY a.follow_up_date",
        (today.isoformat(),),
    )
    return [
        f"{r['role']} at {r['company']} ({r['status']}, {r['follow_up_date']})"
        for r in rows
    ]