from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def state_of_the_art(list_papers: list[dict], language: str, query: str = "") -> str:
    papers_text = ""
    for i, paper in enumerate(list_papers):
        papers_text = papers_text + (
            f"Paper {i + 1}. Title {paper['title']}.\n"
            f"Date {paper.get('date', 'Not specified')}.\n"
            f"Summary {paper['abstract']}.\n\n"
        )

    query_context = (
        f"The user's original research question is: \"{query}\". "
        "Use this as context to identify how the state of the art aligns with that question."
        if query
        else ""
    )

    prompt_extract = """
    You are an academic research analyst. Extract minimal evidence from the articles below.
    {query_context}

    For each article extract ONLY these 5 fields (max 18 words each):
        - id: A1, A2, A3...
        - title: exact title
        - year: publication year from date; if unavailable, "Not specified."
        - current_status: most relevant validated advance.
        - gap: principal unresolved limitation; if absent, "Not specified."

    Return ONLY a JSON array:
        [
            {{
                "id": "A1",
                "title": "...",
                "year": "...",
                "current_status": "...",
                "gap": "..."
            }}
        ]

    Rules:
        - No markdown, no explanations.
        - Do NOT invent information.
        - If uncertain, write: "Not specified."

    INPUT ARTICLES:
        {papers_text}""".format(papers_text=papers_text, query_context=query_context)

    response_extract = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt_extract}
        ]
    )

    prompt_output = """
    MANDATORY: Write your ENTIRE response in {language}. No exceptions.

    Role: senior academic writer.
    Task: transform the JSON into a concise state-of-the-art synthesis.
    Research question: "{query}"

    Output format:
    - First, write ONLY one paragraph for the state of the art.
    - Then add this line: "Referencias clave:" followed by 3 to 5 references.
    - Use this reference format: [A1] Title (Year).
    - No headings or markdown.

    Content requirements for the paragraph:
    - Explain the current situation of the topic based on the selected articles.
    - Explicitly identify the main research gaps.
    - Close with one brief sentence on immediate research priority.

    RULES:
    - Formal academic register, precise and objective.
    - Paragraph length: 130 to 170 words.
    - Include 3 to 5 references from the provided JSON only.
    - Do not invent titles, years, or findings.

    INPUT JSON:
        {response_extract}
    """.format(response_extract=response_extract.choices[0].message.content, language=language, query=query)

    response_output = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt_output}
        ]
    )

    return response_output.choices[0].message.content


if __name__ == "__main__":
    papers = [
        {
            "title": "AR-RAG: Autoregressive Retrieval Augmentation for Image Generation",
            "abstract": """This paper introduces AR-RAG, a method that incorporates nearest-neighbor retrieval at patch level during autoregressive image generation to improve visual consistency and controllability.""",
            "date": "2024-09-01"
        },
        {
            "title": "RAG-Diffusion: Retrieval-Augmented Diffusion Models",
            "abstract": """The work proposes conditioning diffusion models with retrieved external images to improve semantic alignment and generation quality in open-domain scenarios.""",
            "date": "2024-06-15"
        },
        {
            "title": "KNN-Guided Image Synthesis with Latent Diffusion",
            "abstract": """This study explores nearest-neighbor guidance in latent space, showing gains in fidelity compared with pixel-space retrieval baselines.""",
            "date": "2023-12-20"
        }
    ]

    result = state_of_the_art(papers, language="español", query="retrieval augmented image generation")
    print(result)
