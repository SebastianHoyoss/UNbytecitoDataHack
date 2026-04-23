"""
app.py – UNasistente · Asistente de Investigación Académica
UI layer only; business logic in agents/ and rag/ is untouched.
"""

import streamlit as st

# ── Backend ───────────────────────────────────────────────────────────────────
from agents.orquestador import orchestrate
from agents.comparador import compare_papers
from agents.investigador import state_of_the_art
from rag.loader import get_arxiv_id, download_and_extract
from rag.chunker import chunk_text
from rag.pinecone_db import is_indexed, upsert_paper, query as pinecone_query, pinecone_ready, pinecone_config_error
from rag.rag_agent import answer_question, translate_to_english

# ── UI helpers ────────────────────────────────────────────────────────────────
from ui.styles import inject_css
from ui.components import (
    render_header, render_welcome, render_metrics,
    render_keyword_chips, render_recent_searches,
    render_paper_card, render_comparison, render_state_of_art,
    render_chat_header, section_title, build_export_markdown,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="UNasistente", page_icon="🔬", layout="wide")
inject_css()

# ── Session state ─────────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "results": None, "comparison": None, "state_of_art": None,
    "language": "español", "comparison_language": "español",
    "chat_paper": None, "chat_history": [], "chat_indexed": set(),
    "recent_searches": [],
}
for _k, _v in _DEFAULTS.items():
    st.session_state.setdefault(_k, _v)


# ── Search runner ─────────────────────────────────────────────────────────────
def _run_search(q: str, lang: str, n: int) -> None:
    st.session_state.update(
        comparison=None, state_of_art=None, language=lang,
        chat_paper=None, chat_history=[],
    )
    with st.spinner("🧠 Analizando literatura científica…"):
        try:
            st.session_state.results = orchestrate(q, language=lang, max_results=n, compare=False)
            recents = st.session_state.recent_searches
            if q not in recents:
                st.session_state.recent_searches = ([q] + recents)[:5]
        except Exception as e:
            if "429" in str(e):
                st.error("⏳ ArXiv está limitando las peticiones. Espera 2-3 minutos e intenta de nuevo.")
            else:
                st.error(f"❌ Error al buscar papers: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
render_header()

# ─────────────────────────────────────────────────────────────────────────────
# SEARCH FORM
# ─────────────────────────────────────────────────────────────────────────────
with st.form("search_form"):
    query = st.text_input(
        "¿Qué tema quieres investigar?",
        placeholder="Ej: retrieval augmented generation, vision transformers, LLM alignment…",
    )
    col_a, col_b, col_c = st.columns([2, 2, 1])
    with col_a:
        max_results = st.slider("Número de papers", 2, 10, 5)
    with col_b:
        language = st.selectbox("Idioma del resumen", ["español", "english"])
    with col_c:
        st.write("")
        st.write("")
        submitted = st.form_submit_button("🔍 Buscar", use_container_width=True)

if submitted and query:
    _run_search(query, language, max_results)

# Recent searches
chosen_recent = render_recent_searches(st.session_state.recent_searches)
if chosen_recent:
    _run_search(chosen_recent, st.session_state.language, 5)
    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.results:
    render_welcome()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 – PAPERS
# ─────────────────────────────────────────────────────────────────────────────
result = st.session_state.results

st.divider()
render_metrics(len(result["papers"]), result["query"])
render_keyword_chips(result["query"])

st.download_button(
    label="📥 Exportar informe (.md)",
    data=build_export_markdown(
        result,
        st.session_state.comparison or "",
        st.session_state.state_of_art or "",
    ),
    file_name="informe_investigacion.md",
    mime="text/markdown",
)

st.write("")
section_title("🔎 Exploración de papers")

for i, paper in enumerate(result["papers"]):
    render_paper_card(paper, result["query"], i)
    if st.button("💬 Chatear con este paper", key=f"chat_btn_{i}"):
        if st.session_state.chat_paper is None or st.session_state.chat_paper["url"] != paper["url"]:
            st.session_state.chat_paper = paper
            st.session_state.chat_history = []
        st.rerun()
    st.write("")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 – COMPARISON & ESTADO DEL ARTE
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
section_title("Análisis avanzado")

paper_titles   = [p["title"] for p in result["papers"]]
selected_titles = st.multiselect(
    "Selecciona los papers para el análisis:",
    options=paper_titles,
    default=paper_titles,
)

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    comparison_language = st.selectbox(
        "Idioma del análisis:",
        ["español", "english"],
        index=["español", "english"].index(st.session_state.comparison_language),
    )
with col2:
    st.write("")
    compare_clicked = st.button("Comparar", use_container_width=True)
with col3:
    st.write("")
    soa_clicked = st.button("Estado del Arte", use_container_width=True)

# Run comparison
if compare_clicked:
    st.session_state.comparison_language = comparison_language
    selected = [p for p in result["papers"] if p["title"] in selected_titles]
    if len(selected) < 2:
        st.warning("⚠️ Selecciona al menos 2 papers para comparar.")
    else:
        with st.spinner("Generando análisis comparativo…"):
            st.session_state.comparison = compare_papers(selected, comparison_language, result["query"])

# Run estado del arte
if soa_clicked:
    selected = [p for p in result["papers"] if p["title"] in selected_titles]
    if len(selected) < 2:
        st.warning("⚠️ Selecciona al menos 2 papers para generar el estado del arte.")
    else:
        with st.spinner("Sintetizando estado del arte…"):
            st.session_state.state_of_art = state_of_the_art(selected, comparison_language, result["query"])

if st.session_state.comparison:
    render_comparison(st.session_state.comparison)

if st.session_state.state_of_art:
    render_state_of_art(st.session_state.state_of_art)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 – CHAT RAG
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.chat_paper:
    paper    = st.session_state.chat_paper
    arxiv_id = get_arxiv_id(paper["url"])

    st.divider()
    render_chat_header(paper["title"])

    # Pinecone gate
    if not pinecone_ready():
        st.error(f"❌ Pinecone no está configurado. {pinecone_config_error()}")
        st.stop()

    # Index once per session
    if arxiv_id not in st.session_state.chat_indexed:
        try:
            if not is_indexed(arxiv_id):
                with st.spinner("📥 Indexando paper… (solo la primera vez)"):
                    text   = download_and_extract(paper["url"])
                    chunks = chunk_text(text)
                    upsert_paper(arxiv_id, chunks)
            st.session_state.chat_indexed.add(arxiv_id)
        except Exception as e:
            st.error(f"❌ No se pudo indexar el paper. Verifica tu conexión o prueba con otro. ({e})")
            st.stop()

    # Chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # New message
    if user_input := st.chat_input("Haz una pregunta sobre el paper…"):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            try:
                with st.spinner("Buscando en el paper…"):
                    search_query   = translate_to_english(user_input)
                    context_chunks = pinecone_query(arxiv_id, search_query)
                    answer         = answer_question(user_input, context_chunks, paper["title"])
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"❌ Error al generar la respuesta. Intenta de nuevo. ({e})")