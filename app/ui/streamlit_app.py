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
        .stApp {
            background: linear-gradient(135deg, #f7fafc 0%, #eef6ff 45%, #fdfdfd 100%);
        }
        .block-container {
            padding-top: 1.5rem;
        }
        .hero-card {
            background: rgba(255,255,255,0.8);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 24px;
            padding: 1.2rem 1.4rem;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.06);
            backdrop-filter: blur(8px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    apply_custom_style()
    manifest = load_manifest()

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
        render_dashboard(manifest)


if __name__ == "__main__":
    main()