import arxiv
from utils.groq_client import chat


def _optimize_query(query: str) -> str:
    return chat("llama-3.3-70b-versatile", [{
        "role": "user",
        "content": (
            "Convert this search query into an optimized English academic search query for ArXiv. "
            "Return ONLY the query string, no explanations, no quotes. "
            "If already in English and well-formed, return it improved with relevant technical synonyms.\n"
            f"Query: {query}"
        )
    }]).strip()


def search_papers(query: str, max_results: int = 5) -> list[dict]:
    optimized_query = _optimize_query(query)

    client = arxiv.Client(delay_seconds=3, num_retries=3)
    search = arxiv.Search(query=optimized_query, max_results=max_results)

    papers = []
    for paper in client.results(search):
        papers.append({
            "title": paper.title,
            "abstract": paper.summary,
            "url": paper.entry_id,
            "authors": [a.name for a in paper.authors],
            "date": str(paper.published.date())
        })
    return papers


if __name__ == "__main__":
    results = search_papers("sistemas de agentes inteligentes", 3)
    for p in results:
        print(p["title"])
        print(p["abstract"][:300])
        print("---")
