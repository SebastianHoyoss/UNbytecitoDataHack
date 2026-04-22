import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.buscador import search_papers
from agents.resumidor import summary_paper
from agents.comparador import compare_papers


def orchestrate(query: str, language: str, max_results: int = 5, compare: bool = False) -> dict:
    papers = search_papers(query, max_results)

    for paper in papers:
        paper["summary"] = summary_paper(paper["title"], paper["abstract"], language)

    comparison = None
    if compare and len(papers) > 1:
        comparison = compare_papers(papers, language, query)

    return {
        "query": query,
        "papers": papers,
        "comparison": comparison
    }


if __name__ == "__main__":
    result = orchestrate("retrieval augmented generation", language="español", max_results=3, compare=True)

    for p in result["papers"]:
        print(f"Título: {p['title']}")
        print(f"URL: {p['url']}")
        print(f"Resumen: {p['summary']}")
        print("---")

    if result["comparison"]:
        print("\n=== COMPARACIÓN ===\n")
        print(result["comparison"])
