import os
from pinecone import Pinecone
from dotenv import load_dotenv
from rag.embedder import embed

load_dotenv()

_api_key = os.getenv("PINECONE_API_KEY")
_index_name = os.getenv("PINECONE_INDEX")
_pc = Pinecone(api_key=_api_key) if _api_key else None
_index = _pc.Index(_index_name) if _pc and _index_name else None


def pinecone_ready() -> bool:
    return _index is not None


def pinecone_config_error() -> str:
    missing = []
    if not _api_key:
        missing.append("PINECONE_API_KEY")
    if not _index_name:
        missing.append("PINECONE_INDEX")
    if not missing:
        return "Pinecone no está disponible por una configuración inválida."
    return f"Faltan variables de entorno para Pinecone: {', '.join(missing)}"


def _require_index():
    if not pinecone_ready():
        raise RuntimeError(pinecone_config_error())


def is_indexed(arxiv_id: str) -> bool:
    _require_index()
    stats = _index.describe_index_stats()
    return arxiv_id in stats.namespaces


def upsert_paper(arxiv_id: str, chunks: list[str]):
    _require_index()
    embeddings = embed(chunks)
    vectors = [
        {
            "id": f"{arxiv_id}_chunk_{i}",
            "values": embedding,
            "metadata": {"text": chunk}
        }
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    _index.upsert(vectors=vectors, namespace=arxiv_id)


def query(arxiv_id: str, question: str, top_k: int = 4) -> list[str]:
    _require_index()
    q_embedding = embed([question])[0]
    results = _index.query(
        vector=q_embedding,
        top_k=top_k,
        namespace=arxiv_id,
        include_metadata=True
    )
    return [match.metadata["text"] for match in results.matches]
