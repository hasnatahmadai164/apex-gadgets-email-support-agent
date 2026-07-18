import argparse
import hashlib
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.config import get_settings
from app.core.llm import build_embedding_model
from app.tools.pinecone_tools import get_pinecone_client, get_pinecone_index, verify_index_dimension

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
BATCH_SIZE = 100


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    return splitter.split_text(text)


def chunk_id(source_name: str, index: int) -> str:
    digest = hashlib.sha1(source_name.encode("utf-8")).hexdigest()[:8]
    return f"{digest}-{index:05d}"


def load_pdf_into_pinecone(pdf_path: Path):
    settings = get_settings()
    verify_index_dimension(get_pinecone_client(), settings.pinecone_index_name)

    chunks = chunk_text(extract_text(pdf_path))
    if not chunks:
        raise ValueError(f"No extractable text found in {pdf_path}")

    embedder = build_embedding_model()
    index = get_pinecone_index()
   # index.delete(delete_all=True)

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        vectors = embedder.embed_documents(batch)
        records = [
            {
                "id": chunk_id(pdf_path.name, start + i),
                "values": vectors[i],
                "metadata": {"text": batch[i], "source": pdf_path.name},
            }
            for i in range(len(batch))
        ]
        index.upsert(vectors=records)

    print(f"Upserted {len(chunks)} chunks from {pdf_path.name} into {settings.pinecone_index_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default="data/knowledge_base.pdf")
    args = parser.parse_args()

    load_pdf_into_pinecone(Path(args.pdf))


if __name__ == "__main__":
    main()
