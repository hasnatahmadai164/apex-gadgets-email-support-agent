from datetime import datetime

from pydantic import BaseModel


class EmailMessage(BaseModel):
    sender: str
    subject: str
    body: str
    gmail_message_id: str | None = None
    thread_id: str | None = None
    received_at: datetime | None = None
