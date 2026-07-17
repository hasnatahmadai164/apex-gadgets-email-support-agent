from app.core.schemas import EmailMessage
from app.triage.sensitivity_classifier import SensitivityResult, classify_sensitivity
from tests.helpers import StubLLM


def test_classify_sensitivity_returns_stub_result():
    stub = StubLLM(SensitivityResult(is_sensitive=True))
    email = EmailMessage(
        sender="angry@example.com", subject="Talk to my lawyer", body="I will sue you"
    )

    result = classify_sensitivity(email, llm=stub)

    assert result.is_sensitive is True


def test_classify_sensitivity_includes_email_content_in_prompt():
    stub = StubLLM(SensitivityResult(is_sensitive=False))
    email = EmailMessage(
        sender="a@example.com",
        subject="Battery question",
        body="Does the phone support fast charging?",
    )

    classify_sensitivity(email, llm=stub)

    user_message = stub.received_messages[1].content
    assert "fast charging" in user_message
