# Arquitectura de BravoBot

BravoBot se organiza en cuatro capas principales:

1. Ingesta: descubre URLs relevantes, respeta robots.txt, extrae contenido principal y guarda artefactos crudos.
2. Procesamiento: limpia texto, normaliza ruido y genera chunks configurables.
3. RAG: crea embeddings, persiste en Pinecone o en el modo local de desarrollo y recupera evidencia para el chat.
4. Presentación: expone una API FastAPI y una interfaz Streamlit para aspirantes.

El objetivo es responder únicamente con evidencia oficial recuperada del dominio institucional.