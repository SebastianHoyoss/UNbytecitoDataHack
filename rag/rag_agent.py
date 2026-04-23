from utils.groq_client import chat


def translate_to_english(question: str) -> str:
    return chat("llama-3.1-8b-instant", [{
        "role": "user",
        "content": (
            "Translate the following question to English for academic search. "
            "Return ONLY the translated question, no explanations.\n"
            f"Question: {question}"
        )
    }]).strip()

def answer_question(question, chunks, paper_title) -> str:
    context = "\n\n".join(chunks)

    prompt_system = (
        f"You are an expert assistant for the research paper: '{paper_title}'.\n"
        "Answer ONLY based on the provided context. If the answer is not there, say so.\n"
        "Respond in the same language the user used to ask the question.\n\n"
        "Response format:\n"
        "- Direct answer to the question (1-2 sentences)\n"
        "- Key evidence from the paper that supports it (1-2 sentences)\n"
        "- Relevant limitation or nuance, only if it adds value (1 sentence max)\n\n"
        "Be precise and academic. Do not repeat the question."
    )
    
    return chat("llama-3.1-8b-instant", [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": f"Contexto del paper:\n\n{context}\n\n---\n\nPregunta: {question}"}
    ])


    