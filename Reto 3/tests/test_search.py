import arxiv
from semanticscholar import SemanticScholar

# Crear un cliente de arXiv
client = arxiv.Client()

# Realizar una búsqueda en arXiv
search = arxiv.Search(
    query="large language models",
    max_results=3
)
# Imprimir los resultados de búsqueda en arXiv
print("Resultados de búsqueda en arXiv:")
for paper in client.results(search):
    print("Título:", paper.title)
    print("Abstract:", paper.summary[:300])
    print("URL:", paper.entry_id)
    print("---")


"""
# Crear un cliente de Semantic Scholar
sch = SemanticScholar()

# Realizar una búsqueda en Semantic Scholar
results = sch.search_paper("large language models", limit=3)

# Imprimir los resultados de búsqueda en Semantic Scholar
print("Resultados de búsqueda en Semantic Scholar:")
for paper in results:
    print("Título:", paper.title)
    print("Abstract:", paper.abstract[:300] if paper.abstract else "N/A")
    print("URL:", paper.url)
    print("---")
"""