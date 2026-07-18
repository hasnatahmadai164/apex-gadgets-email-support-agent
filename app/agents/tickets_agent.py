from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents.shared import classify_confirmation
from app.core.config import get_settings
from app.core.email_utils import extract_email_address
from app.core.llm import build_chat_model
from app.core.schemas import EmailMessage
from app.tools.ticket_tools import create_ticket, find_tickets_by_email

INTENT_SYSTEM_PROMPT = (
    "You classify what a customer wants from an email about Apex Gadgets "
    "support. Choose new_ticket if they are reporting a problem or requesting "
    "help that should be tracked as a support ticket. Choose status_check if "
    "they are asking about the status of a ticket they already opened."
)

EXTRACTION_SYSTEM_PROMPT = (
    "You extract support ticket details from a customer email to Apex Gadgets, "
    "an online store selling phones and laptops. Extract the customer's full "
    "name and a clear one or two sentence summary of their issue. Leave a "
    "field null if the email does not clearly state it, do not guess or invent "
    "values."
)

FIELD_LABELS = {
    "customer_name": "your full name",
    "issue": "a description of the issue you're experiencing",
}


class TicketIntent(BaseModel):
    intent: Literal["new_ticket", "status_check"]


class ExtractedTicket(BaseModel):
    customer_name: str | None = None
    issue: str | None = None


class TicketAgentResult(BaseModel):
    reply_text: str
    pending_ticket: dict | None


def classify_ticket_intent(email: EmailMessage, llm=None) -> TicketIntent:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_specialist_deployment
    ).with_structured_output(TicketIntent)
    user_content = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    return structured_llm.invoke(
        [SystemMessage(content=INTENT_SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )


def extract_ticket_details(email: EmailMessage, llm=None) -> ExtractedTicket:
    structured_llm = llm or build_chat_model(
        get_settings().azure_openai_specialist_deployment
    ).with_structured_output(ExtractedTicket)
    user_content = f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}"
    return structured_llm.invoke(
        [SystemMessage(content=EXTRACTION_SYSTEM_PROMPT), HumanMessage(content=user_content)]
    )


def handle_ticket_request(
    email: EmailMessage, pending_ticket: dict | None, session: Session
) -> TicketAgentResult:
    if pending_ticket is not None:
        return _handle_confirmation(email, pending_ticket, session)
    return _handle_new_request(email, session)


def _handle_new_request(email: EmailMessage, session: Session) -> TicketAgentResult:
    intent = classify_ticket_intent(email)
    if intent.intent == "status_check":
        return _handle_status_check(email, session)
    return _handle_ticket_extraction(email)


def _handle_ticket_extraction(email: EmailMessage, llm=None) -> TicketAgentResult:
    extracted = extract_ticket_details(email, llm=llm)
    missing = _missing_fields(extracted)

    if missing:
        needed = ", ".join(FIELD_LABELS[field] for field in missing)
        reply = (
            f"Thanks for reaching out! To open a ticket we still need {needed}. "
            "Reply with those details and we'll get it opened for you."
        )
        return TicketAgentResult(reply_text=reply, pending_ticket=None)

    reply = (
        "Here's a summary of the support ticket we'll open:\n\n"
        f"Name: {extracted.customer_name}\n"
        f"Issue: {extracted.issue}\n\n"
        "Reply to this email to confirm and we'll open the ticket."
    )
    return TicketAgentResult(reply_text=reply, pending_ticket=extracted.model_dump())


def _handle_confirmation(email: EmailMessage, pending_ticket: dict, session: Session) -> TicketAgentResult:
    confirmation = classify_confirmation(email, pending_ticket)
    if not confirmation.is_confirmed:
        reply = (
            "No problem, we haven't opened the ticket. Reply with the correct "
            "details and we'll prepare a new summary for you to confirm."
        )
        return TicketAgentResult(reply_text=reply, pending_ticket=None)

    customer_email = extract_email_address(email.sender)
    ticket = create_ticket(session, customer_email, pending_ticket)
    reply = (
        f"Your support ticket has been opened. Ticket number: "
        f"{ticket.ticket_number}. We'll follow up as soon as possible."
    )
    return TicketAgentResult(reply_text=reply, pending_ticket=None)


def _handle_status_check(email: EmailMessage, session: Session) -> TicketAgentResult:
    customer_email = extract_email_address(email.sender)
    tickets = find_tickets_by_email(session, customer_email)

    if not tickets:
        reply = (
            "We couldn't find any tickets under this email address. If you "
            "opened a ticket using a different email, let us know and we'll "
            "take a look."
        )
        return TicketAgentResult(reply_text=reply, pending_ticket=None)

    lines = [
        f"- {ticket.ticket_number}: {ticket.issue} — {ticket.status} (opened {ticket.created_at.date()})"
        for ticket in tickets
    ]
    reply = "Here's the status of your tickets:\n\n" + "\n".join(lines)
    return TicketAgentResult(reply_text=reply, pending_ticket=None)


def _missing_fields(extracted: ExtractedTicket) -> list[str]:
    return [field for field, value in extracted.model_dump().items() if not value]
