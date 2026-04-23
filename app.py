import streamlit as st

from agents.orquestador import orchestrate
from agents.comparador import compare_papers
from rag.loader import get_arxiv_id, download_and_extract
from rag.chunker import chunk_text
from rag.pinecone_db import is_indexed, upsert_paper, query as pinecone_query
from rag.rag_agent import answer_question

from ui.styles import inject_css
from ui.components import (
    render_header,
    render_metrics,
    render_paper_card,
    render_comparison,
    render_chat_header,
    section_title,
)

st.set_page_config(
    page_title="Asistente de Investigación",
    page_icon="🔬",
    layout="wide",
)
inject_css()

_DEFAULTS = {
    "results": None,
    "comparison": None,
    "language": "español",
    "comparison_language": "español",
    "chat_paper": None,
    "chat_history": [],
    "chat_indexed": set(),
    "chat_lang": "español",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


render_header()

with st.form("search_form"):
    query = st.text_input(
        "¿Qué tema quieres investigar?",
        placeholder="Ej: retrieval augmented generation, vision transformers…",
    )
    col_a, col_b, col_c = st.columns([2, 2, 1])
    with col_a:
        max_results = st.slider("Número de papers", min_value=2, max_value=10, value=5)
    with col_b:
        language = st.selectbox("Idioma del resumen", ["español", "english"])
    with col_c:
        st.write("")
        st.write("")
        submitted = st.form_submit_button("🔍 Buscar", use_container_width=True)

if submitted and query:
    # Reset dependent state on new search
    st.session_state.update(
        comparison=None,
        language=language,
        chat_paper=None,
        chat_history=[],
    )
    with st.spinner("Analizando literatura científica…"):
        st.session_state.results = orchestrate(
            query, language=language, max_results=max_results, compare=False
        )

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 – EXPLORATION
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.results:
    result = st.session_state.results

    st.divider()
    render_metrics(len(result["papers"]), result["query"])
    section_title("Exploración de Papers")

    for i, paper in enumerate(result["papers"]):
        render_paper_card(paper, result["query"], i)

        # Chat button lives outside the HTML card so Streamlit can handle it
        if st.button("💬 Chatear con este paper", key=f"chat_btn_{i}"):
            if (
                st.session_state.chat_paper is None
                or st.session_state.chat_paper["url"] != paper["url"]
            ):
                st.session_state.chat_paper = paper
                st.session_state.chat_history = []
            st.rerun()

        st.write("")  # breathing room between cards

    # ─────────────────────────────────────────────────────────────────────────
    # SECTION 2 – COMPARISON
    # ─────────────────────────────────────────────────────────────────────────
    st.divider()
    section_title("Comparación de Papers")

    paper_titles = [p["title"] for p in result["papers"]]
    selected_titles = st.multiselect(
        "Selecciona los papers a comparar:",
        options=paper_titles,
        default=paper_titles,
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        comparison_language = st.selectbox(
            "Idioma del análisis comparativo:",
            ["español", "english"],
            index=["español", "english"].index(st.session_state.comparison_language),
        )
    with col2:
        st.write("")
        compare_clicked = st.button("Comparar seleccionados", use_container_width=True)

    if compare_clicked:
        st.session_state.comparison_language = comparison_language
        selected_papers = [p for p in result["papers"] if p["title"] in selected_titles]
        if len(selected_papers) < 2:
            st.warning("⚠️ Selecciona al menos 2 papers para comparar.")
        else:
            with st.spinner("Generando análisis comparativo…"):
                st.session_state.comparison = compare_papers(
                    selected_papers, comparison_language, result["query"]
                )

if st.session_state.comparison:
    render_comparison(st.session_state.comparison)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 – CHAT WITH PAPER
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.chat_paper:
    paper = st.session_state.chat_paper
    arxiv_id = get_arxiv_id(paper["url"])

    st.divider()
    render_chat_header(paper["title"])
    st.selectbox("Idioma del chat", ["español", "english"], key="chat_lang")

    # Index paper once per session
    if arxiv_id not in st.session_state.chat_indexed:
        if not is_indexed(arxiv_id):
            with st.spinner("📥 Indexando paper en base de conocimiento… (solo la primera vez)"):
                text = download_and_extract(paper["url"])
                chunks = chunk_text(text)
                upsert_paper(arxiv_id, chunks)
        st.session_state.chat_indexed.add(arxiv_id)

    # Render history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # New user message
    if user_input := st.chat_input("Haz una pregunta sobre el paper…"):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("🔍 Buscando respuesta en el paper…"):
                context_chunks = pinecone_query(arxiv_id, user_input)
                answer = answer_question(
                    user_input, context_chunks, paper["title"], st.session_state.chat_lang
                )
            st.markdown(answer)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})