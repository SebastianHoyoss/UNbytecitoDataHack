from __future__ import annotations

import json
import os
from pathlib import Path

import requests
import streamlit as st

from app.core.config import get_settings


st.set_page_config(
    page_title="BravoBot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

settings = get_settings()
API_URL = os.getenv("BRAVOBOT_API_URL", settings.api_base_url).rstrip("/")


def load_manifest() -> dict[str, object]:
    manifest_path = Path(settings.processed_dir / settings.processed_manifest_name)
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def post_question(question: str, session_id: str | None) -> dict[str, object]:
    response = requests.post(
        f"{API_URL}/chat",
        json={"question": question, "session_id": session_id},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def fetch_health() -> dict[str, object]:
    try:
        response = requests.get(f"{API_URL}/health", timeout=10)
        response.raise_for_status()
        payload = response.json()
        payload["reachable"] = True
        return payload
    except Exception:
        return {"reachable": False}


def render_active_config(health: dict[str, object]) -> None:
    st.markdown("### Configuración activa")
    cols = st.columns(3)
    cols[0].metric("Modelo LLM", settings.llm_model)
    cols[1].metric("Embeddings RAG", settings.embedding_model.replace("sentence-transformers/", ""))
    cols[2].metric("Top-K", settings.top_k)

    backend_status = "Conectado" if health.get("reachable") else "Sin conexión"
    backend_vector_store = str(health.get("vector_store", "desconocido"))
    st.markdown(
        f"""
        <div class="info-card">
            <strong>Backend:</strong> {backend_status}<br/>
            <strong>API URL:</strong> {API_URL}<br/>
            <strong>Vector store:</strong> {backend_vector_store}<br/>
            <strong>Namespace Pinecone:</strong> {settings.pinecone_namespace}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard(manifest: dict[str, object]) -> None:
    st.subheader("Panel general")
    columns = st.columns(3)
    columns[0].metric("Documentos indexados", manifest.get("documents_indexed", 0))
    columns[1].metric("Chunks indexados", manifest.get("chunks_indexed", 0))
    columns[2].metric("Categorías detectadas", len(manifest.get("categories", [])))

    st.markdown("### Categorías más consultadas")
    category_counts = manifest.get("category_counts", {}) or {}
    if category_counts:
        st.bar_chart(category_counts)
    else:
        st.info("Todavía no hay telemetría real. Este espacio muestra una simulación basada en las categorías indexadas.")

    st.markdown("### Últimas fuentes indexadas")
    latest_sources = manifest.get("latest_sources", []) or []
    if latest_sources:
        for source in latest_sources[:10]:
            st.write(f"- {source}")
    else:
        st.caption("Aún no hay fuentes indexadas.")


def render_chat() -> None:
    st.subheader("Chat BravoBot")
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Pregunta por admisiones, costos, fechas o oferta académica")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Consultando información oficial..."):
                try:
                    payload = post_question(question, st.session_state.session_id)
                    st.session_state.session_id = payload.get("session_id", st.session_state.session_id)
                    answer = payload.get("answer", "")
                    st.markdown(answer)
                    sources = payload.get("sources", []) or []
                    if sources:
                        st.markdown("**Fuentes utilizadas**")
                        for source in sources[:5]:
                            st.write(f"- {source.get('url', '')}")
                    confidence = payload.get("confidence", 0.0)
                    st.caption(f"Confianza aproximada: {confidence:.2f}")
                    if payload.get("warning"):
                        st.warning(payload["warning"])
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as exc:
                    error_message = (
                        "No pude conectar con la API de BravoBot. Verifica que el backend esté ejecutándose "
                        f"en {API_URL}. Detalle: {exc}"
                    )
                    st.error(error_message)


def apply_custom_style() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap');

        :root {
            --bb-bg-1: #f5f7fb;
            --bb-bg-2: #eaf2ff;
            --bb-text: #0f172a;
            --bb-muted: #334155;
            --bb-surface: rgba(255, 255, 255, 0.9);
            --bb-border: rgba(15, 23, 42, 0.12);
            --bb-accent: #0b5fff;
        }

        .stApp {
            font-family: 'Manrope', sans-serif;
            color: var(--bb-text);
            background:
                radial-gradient(circle at 0% 0%, rgba(11, 95, 255, 0.08), transparent 30%),
                radial-gradient(circle at 100% 20%, rgba(14, 165, 233, 0.10), transparent 25%),
                linear-gradient(135deg, var(--bb-bg-1) 0%, var(--bb-bg-2) 50%, #ffffff 100%);
        }

        .stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp div,
        .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
            color: var(--bb-text);
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }

        .hero-card {
            background: var(--bb-surface);
            border: 1px solid var(--bb-border);
            border-radius: 24px;
            padding: 1.2rem 1.4rem;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
            backdrop-filter: blur(8px);
        }

        .hero-card h1 {
            margin: 0 0 0.3rem 0;
            font-weight: 800;
            letter-spacing: -0.02em;
        }

        .hero-card p {
            margin: 0;
            color: var(--bb-muted);
            font-size: 1rem;
        }

        .info-card {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--bb-border);
            border-radius: 14px;
            padding: 0.9rem 1rem;
            color: var(--bb-text);
            margin-bottom: 0.9rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--bb-border);
            border-radius: 12px;
            padding: 0.35rem 0.85rem;
            color: var(--bb-text);
        }

        .stTabs [aria-selected="true"] {
            background: rgba(11, 95, 255, 0.14);
            border-color: rgba(11, 95, 255, 0.35);
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--bb-border);
            border-radius: 14px;
            padding: 0.7rem;
        }

        [data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid var(--bb-border);
            border-radius: 14px;
        }

        [data-testid="stChatInputTextArea"] textarea {
            background: #ffffff;
            color: var(--bb-text);
            border: 1px solid var(--bb-border);
            border-radius: 12px;
        }

        .stButton button {
            background: var(--bb-accent);
            color: #ffffff;
            border: none;
            border-radius: 10px;
        }

        .stCaption {
            color: var(--bb-muted);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    apply_custom_style()
    manifest = load_manifest()
    health = fetch_health()

    st.markdown(
        """
        <div class="hero-card">
        <h1>BravoBot</h1>
        <p>Asistente universitario 24/7 para aspirantes de la I.U. Pascual Bravo, conectado solo a contenido oficial.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_chat, tab_dashboard = st.tabs(["Chat BravoBot", "Dashboard general"])
    with tab_chat:
        render_chat()
    with tab_dashboard:
        render_active_config(health)
        render_dashboard(manifest)


if __name__ == "__main__":
    main()