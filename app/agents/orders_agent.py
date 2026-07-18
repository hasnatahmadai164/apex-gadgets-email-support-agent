from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.shared import classify_confirmation
from app.core.config import get_settings
from app.core.email_utils import extract_email_address
from app.core.llm import build_chat_model
from app.core.schemas import EmailMessage
from app.tools.order_tools import create_order, find_orders_by_email

INTENT_SYSTEM_PROMPT = (
    "You classify what a customer wants from an email about an Apex Gadgets "
    "order. Choose new_order if they are asking to place or start a new order "
    "for a product. Choose status_check if they are asking about an existing "
    "order's status, tracking, or delivery."
)

EXTRACTION_SYSTEM_PROMPT = (
    "You extract order details from a customer email to Apex Gadgets, an online "
    "store selling phones and laptops. Extract the customer's full name, phone "
    "number, shipping address, and the exact product they want to order. Leave "
    "a field null if the email does not clearly state it, do not guess or "
    "invent values."
)

FIELD_LABELS = {
    "customer_name": "your full name",
    "phone_number": "a phone number",
    "home_address": "your shipping address",
    "product": "which product you'd like to order",
}


class OrderIntent(BaseModel):
    intent: Literal["new_order", "status_check"]


class ExtractedOrder(BaseModel):
    customer_name: str | None = None
    phone_number: str | None = None
    home_address: str | None = None
    product: str | None = None


class OrderAgentResult(BaseModel):
    reply_text: str
    pending_order: dict | None


def classify_order_intent(email: EmailMessage, llm=None) -> OrderIntent:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_specialist_deployment
    ).with_structured_output(OrderIntent)
    user_content = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    return structured_llm.invoke(
        [SystemMessage(content=INTENT_SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )


def extract_order_details(email: EmailMessage, llm=None) -> ExtractedOrder:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_specialist_deployment
    ).with_structured_output(ExtractedOrder)
    user_content = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    return structured_llm.invoke(
        [SystemMessage(content=EXTRACTION_SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )


def handle_order_request(
    email: EmailMessage, pending_order: dict | None, session: Session
) -> OrderAgentResult:
    if pending_order is not None:
        return _handle_confirmation(email, pending_order, session)
    return _handle_new_request(email, session)


def _handle_new_request(email: EmailMessage, session: Session) -> OrderAgentResult:
    intent = classify_order_intent(email)
    if intent.intent == "status_check":
        return _handle_status_check(email, session)
    return _handle_order_extraction(email)


def _handle_order_extraction(email: EmailMessage, llm=None) -> OrderAgentResult:
    extracted = extract_order_details(email, llm=llm)
    missing = _missing_fields(extracted)

    if missing:
        needed = ", ".join(FIELD_LABELS[field] for field in missing)
        reply = (
            f"Thanks for reaching out! To place this order we still need {needed}. "
            "Reply with those details and we'll get it ready for you."
        )
        return OrderAgentResult(reply_text=reply, pending_order=None)

    reply = (
        "Here's a summary of the order you'd like to place:\n\n"
        f"Name: {extracted.customer_name}\n"
        f"Phone: {extracted.phone_number}\n"
        f"Shipping address: {extracted.home_address}\n"
        f"Product: {extracted.product}\n\n"
        "Reply to this email to confirm and we'll place the order."
    )
    return OrderAgentResult(reply_text=reply, pending_order=extracted.model_dump())


def _handle_confirmation(email: EmailMessage, pending_order: dict, session: Session) -> OrderAgentResult:
    confirmation = classify_confirmation(email, pending_order)
    if not confirmation.is_confirmed:
        reply = (
            "No problem, we haven't placed the order. Reply with the correct "
            "details and we'll prepare a new summary for you to confirm."
        )
        return OrderAgentResult(reply_text=reply, pending_order=None)

    customer_email = extract_email_address(email.sender)
    order = create_order(session, customer_email, pending_order)
    reply = (
        f"Your order for {order.product} has been placed. Order reference: "
        f"{order.id}. We'll follow up with shipping details soon."
    )
    return OrderAgentResult(reply_text=reply, pending_order=None)


def _handle_status_check(email: EmailMessage, session: Session) -> OrderAgentResult:
    customer_email = extract_email_address(email.sender)
    orders = find_orders_by_email(session, customer_email)

    if not orders:
        reply = (
            "We couldn't find any orders under this email address. If you "
            "placed an order using a different email, let us know and we'll "
            "take a look."
        )
        return OrderAgentResult(reply_text=reply, pending_order=None)

    lines = [f"- {order.product}: {order.status} (placed {order.created_at.date()})" for order in orders]
    reply = "Here's the status of your orders:\n\n" + "\n".join(lines)
    return OrderAgentResult(reply_text=reply, pending_order=None)


def _missing_fields(extracted: ExtractedOrder) -> list[str]:
    return [field for field, value in extracted.model_dump().items() if not value]
