"""
SQLAlchemy ORM models.

Three tables, matching the project spec exactly:
- orders
- support_tickets
- email_events

`email_events` is the dashboard's sole source of truth: one row per
processed email, written by the poller, read by the dashboard. Its
schema is shaped around that read pattern — the dashboard's query is
"WHERE received_at::date = CURRENT_DATE GROUP BY category", so
`received_at` and `category` are indexed together, and
`gmail_message_id` is unique so a poller retry can't double-count the
same email if it crashes mid-run and picks the message up again.
"""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Index, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False)
    home_address: Mapped[str] = mapped_column(String(500), nullable=False)
    product: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    issue: Mapped[str] = mapped_column(String, nullable=False)
    ticket_number: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class EmailCategory(str, enum.Enum):
    """Outcome of the two-stage triage for a given email."""

    IRRELEVANT = "irrelevant"
    NEEDS_REVIEW = "needs_review"
    HANDLED = "handled"


class EmailEvent(Base):
    """One row per processed email.

    Written once by the poller when it finishes with a message, and
    only ever touched again to flip `replied` / `replied_at` after a
    successful Gmail send. Never recomputed from Gmail at read time —
    the dashboard reads this table and nothing else.
    """

    __tablename__ = "email_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    gmail_message_id: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True, index=True
    )
    thread_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    category: Mapped[EmailCategory] = mapped_column(
        Enum(EmailCategory, name="email_category", native_enum=True), nullable=False
    )
    replied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_email_events_received_at_category", "received_at", "category"),
    )
