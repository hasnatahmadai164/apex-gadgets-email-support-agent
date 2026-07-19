"""initial schema: orders, support_tickets, email_events

Revision ID: 0001
Revises:
Create Date: 2026-07-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone_number", sa.String(length=32), nullable=False),
        sa.Column("home_address", sa.String(length=500), nullable=False),
        sa.Column("product", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_orders_email", "orders", ["email"])

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("issue", sa.String(), nullable=False),
        sa.Column("ticket_number", sa.String(length=32), nullable=False, unique=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_support_tickets_email", "support_tickets", ["email"])
    op.create_index(
        "ix_support_tickets_ticket_number", "support_tickets", ["ticket_number"], unique=True
    )

    email_category = sa.Enum(
        "irrelevant", "needs_review", "handled", name="email_category"
    )

    op.create_table(
        "email_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("gmail_message_id", sa.String(length=128), nullable=False, unique=True),
        sa.Column("thread_id", sa.String(length=128), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("category", email_category, nullable=False),
        sa.Column("replied", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_email_events_gmail_message_id", "email_events", ["gmail_message_id"], unique=True
    )
    op.create_index("ix_email_events_thread_id", "email_events", ["thread_id"])
    op.create_index(
        "ix_email_events_received_at_category", "email_events", ["received_at", "category"]
    )


def downgrade() -> None:
    op.drop_index("ix_email_events_received_at_category", table_name="email_events")
    op.drop_index("ix_email_events_thread_id", table_name="email_events")
    op.drop_index("ix_email_events_gmail_message_id", table_name="email_events")
    op.drop_table("email_events")

    email_category = sa.Enum(name="email_category")
    email_category.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_support_tickets_ticket_number", table_name="support_tickets")
    op.drop_index("ix_support_tickets_email", table_name="support_tickets")
    op.drop_table("support_tickets")

    op.drop_index("ix_orders_email", table_name="orders")
    op.drop_table("orders")
