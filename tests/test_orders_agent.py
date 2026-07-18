from app.agents.orders_agent import ExtractedOrder, _handle_order_extraction, _missing_fields
from app.core.email_utils import extract_email_address
from app.core.schemas import EmailMessage
from tests.helpers import StubLLM


def test_missing_fields_lists_only_empty_fields():
    order = ExtractedOrder(
        customer_name="Jane Doe", phone_number=None, home_address="123 Main St", product=None
    )
    assert _missing_fields(order) == ["phone_number", "product"]


def test_extract_email_address_handles_display_name():
    assert extract_email_address("Jane Doe <jane@example.com>") == "jane@example.com"


def test_extract_email_address_handles_bare_address():
    assert extract_email_address("jane@example.com") == "jane@example.com"


def test_handle_order_extraction_sets_pending_order_when_complete():
    stub = StubLLM(
        ExtractedOrder(
            customer_name="Jane Doe",
            phone_number="555-1234",
            home_address="123 Main St",
            product="Apex Pro 14",
        )
    )
    email = EmailMessage(
        sender="jane@example.com", subject="New order", body="I'd like to order an Apex Pro 14"
    )

    result = _handle_order_extraction(email, llm=stub)

    assert result.pending_order == {
        "customer_name": "Jane Doe",
        "phone_number": "555-1234",
        "home_address": "123 Main St",
        "product": "Apex Pro 14",
    }
    assert "confirm" in result.reply_text.lower()


def test_handle_order_extraction_asks_for_missing_fields():
    stub = StubLLM(
        ExtractedOrder(customer_name="Jane Doe", phone_number=None, home_address=None, product="Apex Pro 14")
    )
    email = EmailMessage(sender="jane@example.com", subject="New order", body="I want an Apex Pro 14")

    result = _handle_order_extraction(email, llm=stub)

    assert result.pending_order is None
    assert "phone number" in result.reply_text.lower()
