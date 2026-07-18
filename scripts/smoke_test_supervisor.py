from datetime import datetime, timezone

from app.agents.supervisor import process_email
from app.core.schemas import EmailMessage
from app.db.session import get_session

SAMPLE_EMAIL = EmailMessage(
    sender="jane@example.com",
    subject="Return policy question",
    body="Hi, what is your return policy for laptops?",
    gmail_message_id="smoke-test-message-1",
    thread_id="smoke-test-thread-1",
    received_at=datetime.now(tz=timezone.utc),
)


def main():
    session = next(get_session())
    try:
        result = process_email(SAMPLE_EMAIL, session)
        print("category:", result.get("category"))
        print("reply:", result.get("reply_text"))
    finally:
        session.close()


if __name__ == "__main__":
    main()
