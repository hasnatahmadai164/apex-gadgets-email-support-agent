from app.agents.tickets_agent import ExtractedTicket, _handle_ticket_extraction, _missing_fields
from app.core.schemas import EmailMessage
from tests.helpers import StubLLM


def test_missing_fields_lists_only_empty_fields():
    ticket = ExtractedTicket(customer_name=None, issue="My laptop won't turn on")
    assert _missing_fields(ticket) == ["customer_name"]


def test_handle_ticket_extraction_sets_pending_ticket_when_complete():
    stub = StubLLM(ExtractedTicket(customer_name="Jane Doe", issue="My laptop won't turn on"))
    email = EmailMessage(
        sender="jane@example.com", subject="Broken laptop", body="My laptop won't turn on"
    )

    result = _handle_ticket_extraction(email, llm=stub)

    assert result.pending_ticket == {"customer_name": "Jane Doe", "issue": "My laptop won't turn on"}
    assert "confirm" in result.reply_text.lower()


def test_handle_ticket_extraction_asks_for_missing_fields():
    stub = StubLLM(ExtractedTicket(customer_name=None, issue="My laptop won't turn on"))
    email = EmailMessage(sender="jane@example.com", subject="Broken laptop", body="It won't turn on")

    result = _handle_ticket_extraction(email, llm=stub)

    assert result.pending_ticket is None
    assert "full name" in result.reply_text.lower()
