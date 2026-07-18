from functools import lru_cache

from pinecone import Pinecone

from app.core.config import get_settings
from app.core.llm import build_embedding_model

TOP_K = 4
EXPECTED_DIMENSION = 1536


@lru_cache
def get_pinecone_client() -> Pinecone:
    return Pinecone(api_key=get_settings().pinecone_api_key)


@lru_cache
def get_pinecone_index():
    client = get_pinecone_client()
    return client.Index(get_settings().pinecone_index_name)


def verify_index_dimension(client=None, index_name=None):
    client = client or get_pinecone_client()
    index_name = index_name or get_settings().pinecone_index_name

    description = client.describe_index(index_name)
    if description.dimension != EXPECTED_DIMENSION:
        raise ValueError(
            f"Pinecone index '{index_name}' has dimension {description.dimension}, "
            f"but text-embedding-3-small produces {EXPECTED_DIMENSION}-dimensional "
            "vectors. Recreate the index with the correct dimension before ingesting."
        )


def retrieve_chunks(query: str, top_k: int = TOP_K, embedder=None, index=None) -> list[str]:
    embedder = embedder or build_embedding_model()
    index = index or get_pinecone_index()

    query_vector = embedder.embed_query(query)
    results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)

    return [match["metadata"]["text"] for match in results.get("matches", [])]
