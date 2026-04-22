from groq import Groq
from dotenv import load_dotenv
import os
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def answer_question(question, chunks, paper_title, language="español") -> str:
    context = "\n\n".join(chunks)

    prompt_system = (
        f"MANDATORY: Write your entire response in {language}.\n\n"
        f"You are an expert assistant for the research paper: '{paper_title}'.\n"
        "Answer ONLY based on the provided context from the paper.\n"
        "If the answer is not in the context, say so clearly."
    )
    
    response = client.chat.completions.create(
       model="llama-3.3-70b-versatile",
       messages=[
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": f"Contexto del paper:\n\n{context}\n\n---\n\nPregunta: {question}"}
        ]
    )
    
    return response.choices[0].message.content


    