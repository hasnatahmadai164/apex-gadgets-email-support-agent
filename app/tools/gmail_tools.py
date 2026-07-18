import base64
from datetime import datetime, timezone
from email.mime.text import MIMEText
from functools import lru_cache

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.core.config import get_settings
from app.core.schemas import EmailMessage

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]

LABEL_AI_HANDLED = "AI-Handled"
LABEL_NEEDS_REVIEW = "Needs-Human-Review"
LABEL_IRRELEVANT = "Irrelevant"


@lru_cache
def build_gmail_service():
    settings = get_settings()
    if not settings.gmail_client_id or not settings.gmail_client_secret or not settings.gmail_refresh_token:
        raise RuntimeError(
            "Gmail OAuth credentials are missing. Run scripts/gmail_oauth_setup.py once "
            "to get a refresh token, then set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and "
            "GMAIL_REFRESH_TOKEN in .env."
        )

    credentials = Credentials(
        token=None,
        refresh_token=settings.gmail_refresh_token,
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=credentials)


def list_unread_message_ids(service, max_results=25):
    response = (
        service.users()
        .messages()
        .list(userId="me", q="is:unread", maxResults=max_results)
        .execute()
    )
    return [item["id"] for item in response.get("messages", [])]


def get_message(service, message_id) -> EmailMessage:
    raw = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    headers = raw["payload"].get("headers", [])

    return EmailMessage(
        sender=_extract_header(headers, "From"),
        subject=_extract_header(headers, "Subject"),
        body=_extract_body(raw["payload"]),
        gmail_message_id=raw["id"],
        thread_id=raw["threadId"],
        received_at=datetime.fromtimestamp(int(raw["internalDate"]) / 1000, tz=timezone.utc),
    )


def get_or_create_label_id(service, label_name):
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label["name"] == label_name:
            return label["id"]

    created = (
        service.users()
        .labels()
        .create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        .execute()
    )
    return created["id"]


def apply_label_and_mark_read(service, message_id, label_name):
    label_id = get_or_create_label_id(service, label_name)
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id], "removeLabelIds": ["UNREAD"]},
    ).execute()


def send_reply(service, thread_id, to_address, subject, body_text):
    settings = get_settings()
    message = MIMEText(body_text)
    message["to"] = to_address
    message["from"] = settings.gmail_support_address
    message["subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw, "threadId": thread_id})
        .execute()
    )


def _extract_header(headers, name):
    for header in headers:
        if header["name"].lower() == name.lower():
            return header["value"]
    return ""


def _extract_body(payload):
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode_base64url(payload["body"]["data"])

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return _decode_base64url(part["body"]["data"])

    for part in payload.get("parts", []):
        if part.get("parts"):
            nested = _extract_body(part)
            if nested:
                return nested

    return ""


def _decode_base64url(data):
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
