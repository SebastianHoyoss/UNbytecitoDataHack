from utils.groq_client import chat

def compare_papers(list_papers: list[dict], language: str, query: str = "") ->str:

    papers_text=""
    for i, paper in enumerate(list_papers):
        abstract = paper['abstract'][:400]
        papers_text=papers_text+f"Paper {i+1}. Title {paper['title']}.\nSummary {abstract}.\n\n"

    query_context = f"The user's original research question is: \"{query}\". Use this to assess how relevant each article's value proposition is to this specific question." if query else ""

    prompt_compare = """
    You are an academic research analyst. Extract key attributes from the articles below.
    {query_context}

    For each article extract ONLY these 3 fields (max 40 words each):
        - technologies: Tools, frameworks, algorithms, or methods used.
        - value_proposition: Main contribution AND how directly it addresses the user's research question.
        - primary_contribution: One word only — Theoretical, Practical, or Methodological — plus one short sentence.

    Return ONLY a JSON array, no markdown, no explanations:
        [
            {{
                "id": "A1",
                "title": "...",
                "technologies": "...",
                "value_proposition": "...",
                "primary_contribution": "..."
            }}
        ]

    Rules:
        - Do NOT invent information not in the abstract.
        - If a field cannot be determined, write: "Not specified."
        - Respond ONLY with the JSON array.

    INPUT ARTICLES:
        {papers_text}""".format(papers_text=papers_text, query_context=query_context)
    

    response_compare = chat("llama-3.3-70b-versatile", [{"role": "user", "content": prompt_compare}])
    
    prompt_output ="""
    MANDATORY: Write your ENTIRE response in {language}. Every word, heading, and table cell must be in {language}. No exceptions.

    You are an academic analyst. Transform the JSON into a concise comparative report.
    User's research question: "{query}"

    Write ONLY these 3 sections. No introduction. Start directly with ##.

    ## [Translate "Comparative Analysis" to {language}]

    ### 1. [Translate "Technologies Used" to {language}]
    Per article: compact bullet list of its tools, frameworks, and methods. Max 15 words per article.

    ### 2. [Translate "Value Proposition vs. Research Question" to {language}]
    Per article: one sentence — how directly and effectively does it answer the research question?
    Last line: rank articles from most to least relevant (e.g., A2 > A1 > A3) with a one-line reason.

    ### 3. [Translate "Final Verdict" to {language}]
    Table with columns: Article | [Translate: Contribution Type] | [Translate: Description]
    Contribution type options (translate to {language}): Theoretical / Practical / Methodological
    Then 2-3 sentences: which article(s) to prioritize for the research question and why.

    RULES:
    - Everything in {language}. This is mandatory.
    - No text before ##.
    - Maximum 280 words total.

    INPUT JSON:
        {response_compare}
    """.format(response_compare=response_compare, language=language, query=query)

    return chat("llama-3.3-70b-versatile", [{"role": "user", "content": prompt_output}])


if __name__ == "__main__":
    papers = [
        {
            "title": "AR-RAG: Autoregressive Retrieval Augmentation for Image Generation",
            "abstract": """Se presenta AR-RAG, un enfoque
    innovador para la generación de imágenes que incorpora
recuperación autoregresiva de vecinos más cercanos a nivel de
parches. El vacío identificado es la limitación de los métodos
anteriores que realizan una recuperación estática antes de la
generación."""
        },
        {
            "title": "RAG-Diffusion: Retrieval-Augmented Diffusion Models",
            "abstract": """Se propone un modelo de difusión
aumentado con recuperación de imágenes externas para mejorar la
coherencia semántica. El método recupera imágenes similares de
una base de datos y las utiliza como condición adicional
durante el proceso de difusión."""
        },
        {
            "title": "KNN-Guided Image Synthesis with Latent Diffusion",
            "abstract": """Este trabajo explora el uso de vecinos
más cercanos en el espacio latente para guiar la síntesis de
imágenes. Se demuestra que la recuperación en espacio latente
mejora la fidelidad visual respecto a métodos basados en
píxeles."""
        }
    ]

    resultado = compare_papers(papers, language="español")
    print(resultado)


