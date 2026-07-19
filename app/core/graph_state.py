from typing import Literal, TypedDict

from app.core.schemas import EmailMessage


class GraphState(TypedDict, total=False):
    email: EmailMessage
    is_relevant: bool
    is_sensitive: bool
    route: Literal["rag", "orders", "tickets"]
    pending_order: dict | None
    pending_ticket: dict | None
    qa_history: list[dict]
    reply_text: str | None
    category: Literal["irrelevant", "needs_review", "handled"]
