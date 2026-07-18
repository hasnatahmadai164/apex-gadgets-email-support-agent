from app.agents.rag_agent import _should_retry


def test_should_retry_answers_when_sufficient():
    assert _should_retry({"is_sufficient": True, "retry_count": 0}) == "answer"


def test_should_retry_rewrites_when_insufficient_and_under_limit():
    assert _should_retry({"is_sufficient": False, "retry_count": 0}) == "rewrite"


def test_should_retry_answers_when_retry_limit_reached():
    assert _should_retry({"is_sufficient": False, "retry_count": 2}) == "answer"
