"""Gmail access: log in with OAuth, search emails, and read one email.

Stage 1a is READ-ONLY. This file never sends, deletes or changes emails.

First-time login (run once on your computer, opens your browser):
    python -m assistant.gmail
"""

import base64
from pathlib import Path
from typing import Any, Optional

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# The permissions (scopes) we ask Google for. Read-only: least privilege.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Your app's ID card, downloaded from Google Cloud. Never commit it.
CREDENTIALS_FILE = Path("credentials.json")

# The key card Google gives us after you click "Allow". Never commit it.
TOKEN_FILE = Path("token.json")

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


if __name__ == "__main__":
    # One-time login, and a quick test: show your 3 latest email subjects.
    get_service(allow_browser_login=True)
    print("Gmail connected. Your 3 latest emails:")

    for email in search_emails("in:inbox", max_results=3):
        print(f"- {email['subject']}  (from {email['from']})")