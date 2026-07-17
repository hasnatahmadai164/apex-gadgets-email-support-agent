from app.core.schemas import EmailMessage
from app.triage.relevance_classifier import RelevanceResult, classify_relevance
from tests.helpers import StubLLM


def test_classify_relevance_returns_stub_result():
    stub = StubLLM(RelevanceResult(is_relevant=True))
    email = EmailMessage(
        sender="a@example.com", subject="Order question", body="Where is my laptop?"
    )

    result = classify_relevance(email, llm=stub)

    assert result.is_relevant is True


def test_classify_relevance_includes_email_content_in_prompt():
    stub = StubLLM(RelevanceResult(is_relevant=False))
    email = EmailMessage(
        sender="spammer@example.com", subject="Buy crypto now", body="Click here"
    )

    classify_relevance(email, llm=stub)

    user_message = stub.received_messages[1].content
    assert "Buy crypto now" in user_message
    assert "Click here" in user_message
