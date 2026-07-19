import logging
from datetime import datetime, timezone

from app.agents.supervisor import process_email
from app.core.config import get_settings
from app.core.schemas import EmailMessage
from app.db.models import EmailEvent
from app.db.session import get_session
from app.tools.gmail_tools import (
    LABEL_AI_HANDLED,
    LABEL_IRRELEVANT,
    LABEL_NEEDS_REVIEW,
    apply_label_and_mark_read,
    build_gmail_service,
    get_message,
    list_unread_message_ids,
    send_reply,
)

logger = logging.getLogger(__name__)

LABEL_BY_CATEGORY = {
    "irrelevant": LABEL_IRRELEVANT,
    "needs_review": LABEL_NEEDS_REVIEW,
    "handled": LABEL_AI_HANDLED,
}


def run_poll_cycle():
    service = build_gmail_service()
    message_ids = list_unread_message_ids(service)
    logger.info("found %d unread message(s)", len(message_ids))

    for message_id in message_ids:
        try:
            _process_message(service, message_id)
        except Exception:
            logger.exception("failed to process message %s", message_id)


def _process_message(service, message_id):
    session = next(get_session())
    try:
        if _already_processed(session, message_id):
            logger.info("message %s already logged, skipping", message_id)
            return

        email = get_message(service, message_id)
        result = process_email(email, session)
        category = result.get("category", "irrelevant")

        replied = False
        if category == "handled" and result.get("reply_text"):
            send_reply(service, email.thread_id, email.sender, email.subject, result["reply_text"])
            replied = True

        apply_label_and_mark_read(service, message_id, LABEL_BY_CATEGORY[category])

        _log_email_event(session, email, category, replied)
        session.commit()
    finally:
        session.close()


def _already_processed(session, message_id) -> bool:
    existing = (
        session.query(EmailEvent).filter(EmailEvent.gmail_message_id == message_id).first()
    )
    return existing is not None


def _log_email_event(session, email: EmailMessage, category: str, replied: bool):
    event = EmailEvent(
        gmail_message_id=email.gmail_message_id,
        thread_id=email.thread_id,
        received_at=email.received_at,
        category=category,
        replied=replied,
        replied_at=datetime.now(tz=timezone.utc) if replied else None,
    )
    session.add(event)


def main():
    logging.basicConfig(level=get_settings().log_level)
    run_poll_cycle()


if __name__ == "__main__":
    main()
