from datetime import datetime, timezone

from app.agents.supervisor import process_email
from app.core.schemas import EmailMessage
from app.db.session import get_session

FIRST_EMAIL = EmailMessage(
    sender="jane@example.com",
    subject="Product question",
    body="Does the Apex Pro 14 support fast charging?",
    gmail_message_id="smoke-test-message-1",
    thread_id="smoke-test-thread-1",
    received_at=datetime.now(tz=timezone.utc),
)

FOLLOW_UP_EMAIL = EmailMessage(
    sender="jane@example.com",
    subject="Re: Product question",
    body="What about the 16 inch version?",
    gmail_message_id="smoke-test-message-2",
    thread_id="smoke-test-thread-1",
    received_at=datetime.now(tz=timezone.utc),
)


def main():
    session = next(get_session())
    try:
        first = process_email(FIRST_EMAIL, session)
        print("Q1:", FIRST_EMAIL.body)
        print("A1:", first.get("reply_text"))
        print()

        second = process_email(FOLLOW_UP_EMAIL, session)
        print("Q2:", FOLLOW_UP_EMAIL.body)
        print("A2:", second.get("reply_text"))
    finally:
        session.close()


if __name__ == "__main__":
    main()
