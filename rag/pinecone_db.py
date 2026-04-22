import os
from pinecone import Pinecone
from dotenv import load_dotenv
from rag.embedder import embed

load_dotenv()

_pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
_index = _pc.Index(os.getenv("PINECONE_INDEX"))


def is_indexed(arxiv_id: str) -> bool:
    stats = _index.describe_index_stats()
    return arxiv_id in stats.namespaces


def upsert_paper(arxiv_id: str, chunks: list[str]):
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


def query(arxiv_id: str, question: str, top_k: int = 7) -> list[str]:
    q_embedding = embed([question])[0]
    results = _index.query(
        vector=q_embedding,
        top_k=top_k,
        namespace=arxiv_id,
        include_metadata=True
    )
    return [match.metadata["text"] for match in results.matches]
