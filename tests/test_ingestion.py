from ingestion.load_to_pinecone import chunk_id


def test_chunk_id_is_deterministic_and_unique_per_index():
    first = chunk_id("knowledge_base.pdf", 3)
    second = chunk_id("knowledge_base.pdf", 3)

    assert first == second
    assert chunk_id("knowledge_base.pdf", 3) != chunk_id("knowledge_base.pdf", 4)
