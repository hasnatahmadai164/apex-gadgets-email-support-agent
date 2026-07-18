from app.tools.pinecone_tools import retrieve_chunks


class _StubEmbedder:
    def embed_query(self, text):
        return [0.1, 0.2, 0.3]


class _StubIndex:
    def query(self, vector, top_k, include_metadata):
        return {
            "matches": [
                {"metadata": {"text": "Apex Pro 14 has a 14 inch display."}},
                {"metadata": {"text": "Returns are accepted within 30 days."}},
            ]
        }


def test_retrieve_chunks_returns_matched_texts():
    chunks = retrieve_chunks(
        "What is the return policy?", embedder=_StubEmbedder(), index=_StubIndex()
    )

    assert chunks == [
        "Apex Pro 14 has a 14 inch display.",
        "Returns are accepted within 30 days.",
    ]
