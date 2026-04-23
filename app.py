import streamlit as st
from agents.orquestador import orchestrate
from agents.comparador import compare_papers
from agents.investigador import state_of_the_art
from rag.loader import get_arxiv_id, download_and_extract
from rag.chunker import chunk_text
from rag.pinecone_db import (
    is_indexed,
    upsert_paper,
    query as pinecone_query,
    pinecone_ready,
    pinecone_config_error,
)
from rag.rag_agent import answer_question, translate_to_english

st.title("Asistente de Investigación Académica")

if "results" not in st.session_state:
    st.session_state.results = None
if "comparison" not in st.session_state:
    st.session_state.comparison = None
if "language" not in st.session_state:
    st.session_state.language = "español"
if "comparison_language" not in st.session_state:
    st.session_state.comparison_language = "español"
if "chat_paper" not in st.session_state:
    st.session_state.chat_paper = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat_indexed" not in st.session_state:
    st.session_state.chat_indexed = set()
if "state_of_art" not in st.session_state:
    st.session_state.state_of_art = None

with st.form("search_form"):
    query = st.text_input("¿Qué tema quieres investigar?", placeholder="Ej: retrieval augmented generation")
    col1, col2 = st.columns(2)
    with col1:
        max_results = st.slider("Número de papers", min_value=2, max_value=10, value=5)
    with col2:
        language = st.selectbox("Idioma del resumen", ["español", "english"])
    submitted = st.form_submit_button("Buscar")

if submitted and query:
    st.session_state.comparison = None
    st.session_state.state_of_art = None
    st.session_state.language = language
    st.session_state.chat_paper = None
    st.session_state.chat_history = []
    with st.spinner("Buscando y resumiendo papers..."):
        try:
            st.session_state.results = orchestrate(query, language=language, max_results=max_results, compare=False)
        except Exception as e:
            if "429" in str(e):
                st.error("ArXiv está limitando las peticiones. Espera 2-3 minutos e intenta de nuevo.")
            else:
                st.error(f"Error al buscar papers: {e}")

if st.session_state.results:
    result = st.session_state.results
    st.subheader(f"Resultados para: *{result['query']}*")

    for paper in result["papers"]:
        with st.expander(f"📄 {paper['title']}"):
            st.markdown(f"**Autores:** {', '.join(paper['authors'][:3])}")
            st.markdown(f"**Fecha:** {paper['date']}")
            st.markdown(f"**URL:** [Ver paper]({paper['url']})")
            st.markdown(paper["summary"])

            if st.button("💬 Chatear con este paper", key=f"chat_{paper['url']}"):
                if st.session_state.chat_paper is None or st.session_state.chat_paper["url"] != paper["url"]:
                    st.session_state.chat_paper = paper
                    st.session_state.chat_history = []
                st.rerun()

    st.divider()

    paper_titles = [p["title"] for p in result["papers"]]
    selected_titles = st.multiselect(
        "Selecciona los papers a comparar:",
        options=paper_titles,
        default=paper_titles
    )

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        comparison_language = st.selectbox(
            "Idioma del análisis:",
            ["español", "english"],
            index=["español", "english"].index(st.session_state.comparison_language)
        )
    with col2:
        st.write("")
        st.write("")
        compare_clicked = st.button("Comparar papers")
    with col3:
        st.write("")
        st.write("")
        soa_clicked = st.button("Estado del Arte")

    if compare_clicked:
        st.session_state.comparison_language = comparison_language
        selected_papers = [p for p in result["papers"] if p["title"] in selected_titles]
        if len(selected_papers) < 2:
            st.warning("Selecciona al menos 2 papers para comparar.")
        else:
            with st.spinner("Generando análisis comparativo..."):
                st.session_state.comparison = compare_papers(
                    selected_papers,
                    comparison_language,
                    result["query"]
                )

    if soa_clicked:
        selected_papers = [p for p in result["papers"] if p["title"] in selected_titles]
        if len(selected_papers) < 2:
            st.warning("Selecciona al menos 2 papers para generar el estado del arte.")
        else:
            with st.spinner("Generando estado del arte..."):
                st.session_state.state_of_art = state_of_the_art(
                    selected_papers,
                    comparison_language,
                    result["query"]
                )

if st.session_state.comparison:
    st.subheader("Análisis Comparativo")
    st.markdown(st.session_state.comparison)

if st.session_state.state_of_art:
    st.subheader("Estado del Arte")
    st.markdown(st.session_state.state_of_art)

# --- Sección de chat RAG ---
if st.session_state.chat_paper:
    paper = st.session_state.chat_paper
    arxiv_id = get_arxiv_id(paper["url"])

    st.divider()
    st.subheader(f"💬 Chat: {paper['title'][:70]}...")

    if not pinecone_ready():
        st.error(
            "No se puede usar el chat RAG porque Pinecone no está configurado. "
            f"{pinecone_config_error()}"
        )
        st.stop()

    if arxiv_id not in st.session_state.chat_indexed:
        try:
            if not is_indexed(arxiv_id):
                with st.spinner("Descargando e indexando el paper en Pinecone... (solo la primera vez)"):
                    text = download_and_extract(paper["url"])
                    chunks = chunk_text(text)
                    upsert_paper(arxiv_id, chunks)
            st.session_state.chat_indexed.add(arxiv_id)
        except Exception as e:
            st.error(f"No se pudo indexar el paper. Verifica tu conexión o intenta con otro paper. ({e})")
            st.stop()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Haz una pregunta sobre el paper..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Buscando en el paper..."):
                    search_query = translate_to_english(user_input)
                    context_chunks = pinecone_query(arxiv_id, search_query)
                    answer = answer_question(user_input, context_chunks, paper["title"])
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Error al generar la respuesta. Intenta de nuevo. ({e})")
