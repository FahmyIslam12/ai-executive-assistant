"""Gmail access: log in with OAuth, search emails, and read one email.

Stage 1a: search and read emails.
Stage 1b: create drafts. Sending happens ONLY through send_draft(), which is
called by the Telegram "Send" button, never by the AI.

First-time login (run once on your computer, opens your browser):
    python -m assistant.gmail
"""

import base64
import mimetypes
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Optional

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# The permissions (scopes) we ask Google for, and nothing more.
# readonly: search and read emails. compose: create drafts and send them.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]

# Your app's ID card, downloaded from Google Cloud. Never commit it.
CREDENTIALS_FILE = Path("credentials.json")

# The key card Google gives us after you click "Allow". Never commit it.
TOKEN_FILE = Path("token.json")

# Your CV. The AI reads cv.txt; the PDF (or Word file) is attached.
CV_FOLDER = Path("data/cv")
CV_TEXT_FILE = CV_FOLDER / "cv.txt"
CV_ATTACHMENTS = [CV_FOLDER / "cv.pdf", CV_FOLDER / "cv.docx"]

# Long emails are cut to this many characters before going to the AI.
# This keeps cost down and limits how much private text is shared.
MAX_BODY_CHARACTERS = 4000


class GmailNotConnected(Exception):
    """Raised when there is no valid login and the user must log in again."""


def get_service(allow_browser_login: bool = False) -> Any:
    """Return a connected Gmail API client.

    With allow_browser_login=True (only when run from the terminal), this
    opens the browser so you can log in. The bot never does that by itself.
    """
    creds: Optional[Credentials] = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # The access token expires after about 1 hour. Use the refresh token
    # to get a new one quietly, without asking you to log in again.
    # If the saved login is missing a permission we now need (for example
    # after adding "compose"), you must log in again to approve it.
    if creds and not creds.has_scopes(SCOPES):
        creds = None

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        except RefreshError:
            # In "testing" mode Google ends the login after 7 days.
            creds = None

    if not creds or not creds.valid:
        if not allow_browser_login:
            raise GmailNotConnected(
                "Gmail is not connected (or the weekly login expired). "
                "On the computer, run: python -m assistant.gmail"
            )

        if not CREDENTIALS_FILE.exists():
            raise GmailNotConnected("credentials.json is missing.")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE), SCOPES
        )
        # Opens your browser at Google's "Allow" page.
        creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _header(message: dict, name: str) -> str:
    """Pick one header (like From or Subject) out of a Gmail message."""
    for header in message.get("payload", {}).get("headers", []):
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def search_emails(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search Gmail using Gmail's own search words, e.g. "from:bjit is:unread".

    Returns a short summary of each email, not the full text.
    """
    service = get_service()
    max_results = max(1, min(max_results, 10))

    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    emails = []

    for item in result.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            )
            .execute()
        )
        emails.append(
            {
                "id": message["id"],
                "from": _header(message, "From"),
                "subject": _header(message, "Subject"),
                "date": _header(message, "Date"),
                "preview": message.get("snippet", ""),
            }
        )

    return emails


def _find_plain_text(part: dict) -> str:
    """Emails are built from nested parts. Find the plain-text part."""
    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
        data = part["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for child in part.get("parts", []):
        text = _find_plain_text(child)
        if text:
            return text

    return ""


def read_email(email_id: str) -> dict[str, str]:
    """Read one email by its ID and return its main details and text."""
    service = get_service()

    message = (
        service.users()
        .messages()
        .get(userId="me", id=email_id, format="full")
        .execute()
    )

    body = _find_plain_text(message.get("payload", {}))

    if not body:
        # Some emails only have an HTML version; fall back to the preview.
        body = message.get("snippet", "")

    if len(body) > MAX_BODY_CHARACTERS:
        body = body[:MAX_BODY_CHARACTERS] + "\n[...email shortened...]"

    return {
        "from": _header(message, "From"),
        "to": _header(message, "To"),
        "subject": _header(message, "Subject"),
        "date": _header(message, "Date"),
        "body": body,
    }


def read_cv() -> str:
    """Return the CV text the AI uses to write applications."""
    if not CV_TEXT_FILE.exists():
        return "No CV found. Put a text version of the CV in data/cv/cv.txt."
    return CV_TEXT_FILE.read_text(encoding="utf-8")


def find_cv_attachment() -> Optional[Path]:
    """Return the CV file to attach (PDF first, then Word), if there is one."""
    for path in CV_ATTACHMENTS:
        if path.exists():
            return path
    return None


def create_draft(
    to: str,
    subject: str,
    body: str,
    attach_cv: bool = False,
    reply_to_email_id: Optional[str] = None,
) -> dict[str, str]:
    """Save an email as a draft in Gmail. Nothing is sent."""
    service = get_service()

    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    thread_id = None

    if reply_to_email_id:
        # Link the reply to the original email so Gmail shows one thread.
        original = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=reply_to_email_id,
                format="metadata",
                metadataHeaders=["Message-ID"],
            )
            .execute()
        )
        thread_id = original.get("threadId")
        original_id = _header(original, "Message-ID")
        if original_id:
            message["In-Reply-To"] = original_id
            message["References"] = original_id

    attachment_name = ""

    if attach_cv:
        cv_file = find_cv_attachment()
        if cv_file is None:
            raise FileNotFoundError("No CV file found in data/cv/ to attach.")

        mime_type, _ = mimetypes.guess_type(cv_file.name)
        maintype, subtype = (mime_type or "application/octet-stream").split("/")
        attachment_name = cv_file.name
        message.add_attachment(
            cv_file.read_bytes(),
            maintype=maintype,
            subtype=subtype,
            filename="Fahmy_Islam_CV" + cv_file.suffix,
        )

    # Gmail wants the whole email as base64 text.
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    draft_message: dict[str, Any] = {"raw": raw}
    if thread_id:
        draft_message["threadId"] = thread_id

    draft = (
        service.users()
        .drafts()
        .create(userId="me", body={"message": draft_message})
        .execute()
    )

    return {
        "draft_id": draft["id"],
        "to": to,
        "subject": subject,
        "body": body,
        "attachment": attachment_name,
    }


def send_draft(draft_id: str) -> None:
    """Send a draft. Called ONLY by the Telegram Send button.

    Gmail sends the draft's latest version, including edits you made in the
    Gmail app after it was created.
    """
    service = get_service()
    service.users().drafts().send(userId="me", body={"id": draft_id}).execute()


def delete_draft(draft_id: str) -> None:
    """Delete a draft this assistant created (used by the Cancel button)."""
    service = get_service()
    service.users().drafts().delete(userId="me", id=draft_id).execute()


if __name__ == "__main__":
    # One-time login, and a quick test: show your 3 latest email subjects.
    get_service(allow_browser_login=True)
    profile = get_service().users().getProfile(userId="me").execute()
    print(f"Gmail connected as: {profile['emailAddress']}")
    print("Your 3 latest emails:")

    for email in search_emails("in:inbox", max_results=3):
        print(f"- {email['subject']}  (from {email['from']})")