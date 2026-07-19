from app.poller import LABEL_BY_CATEGORY


def test_label_by_category_covers_every_graph_category():
    assert set(LABEL_BY_CATEGORY.keys()) == {"irrelevant", "needs_review", "handled"}
