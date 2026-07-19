from datetime import date

from sqlalchemy import Date, case, cast, func
from sqlalchemy.orm import Session

from app.db.models import EmailCategory, EmailEvent


def get_today_stats(session: Session) -> dict:
    rows = (
        session.query(
            EmailEvent.category,
            func.count(EmailEvent.id),
            func.count(case((EmailEvent.replied.is_(True), 1))),
        )
        .filter(cast(EmailEvent.received_at, Date) == date.today())
        .group_by(EmailEvent.category)
        .all()
    )

    counts = {category.value: 0 for category in EmailCategory}
    replied = 0
    for category, count, replied_count in rows:
        counts[category.value] = count
        replied += replied_count

    return {
        "total": sum(counts.values()),
        "replied": replied,
        "handled": counts[EmailCategory.HANDLED.value],
        "needs_review": counts[EmailCategory.NEEDS_REVIEW.value],
        "irrelevant": counts[EmailCategory.IRRELEVANT.value],
    }
