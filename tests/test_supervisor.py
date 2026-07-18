from app.agents.supervisor import _dispatch_specialist, _route_after_relevance, _route_after_sensitivity


def test_route_after_relevance_continues_when_relevant():
    assert _route_after_relevance({"is_relevant": True}) == "continue"


def test_route_after_relevance_marks_irrelevant_when_not_relevant():
    assert _route_after_relevance({"is_relevant": False}) == "irrelevant"


def test_route_after_sensitivity_marks_needs_review_when_sensitive():
    assert _route_after_sensitivity({"is_sensitive": True}) == "needs_review"


def test_route_after_sensitivity_continues_when_not_sensitive():
    assert _route_after_sensitivity({"is_sensitive": False}) == "continue"


def test_dispatch_specialist_reads_route_field():
    assert _dispatch_specialist({"route": "orders"}) == "orders"
