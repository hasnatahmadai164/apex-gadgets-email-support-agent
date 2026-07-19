from app.agents.rag_agent import _should_retry, contextualize_node


def test_should_retry_answers_when_sufficient():
    assert _should_retry({"is_sufficient": True, "retry_count": 0}) == "answer"


def test_should_retry_rewrites_when_insufficient_and_under_limit():
    assert _should_retry({"is_sufficient": False, "retry_count": 0}) == "rewrite"


def test_should_retry_answers_when_retry_limit_reached():
    assert _should_retry({"is_sufficient": False, "retry_count": 2}) == "answer"


def test_contextualize_node_is_noop_without_history():
    state = {"original_query": "Does it support fast charging?", "history": []}
    assert contextualize_node(state) == {}
