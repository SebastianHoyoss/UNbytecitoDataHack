"""
ui/components.py – Reusable rendering helpers for the Research Assistant UI.
All functions emit only Streamlit / HTML-markdown; no business logic here.
"""

import streamlit as st


# ── Relevance helpers ──────────────────────────────────────────────────────────

def relevance_score(paper: dict, query: str) -> int:
    """Heuristic 0-100 relevance score based on query-word overlap."""
    words = {w for w in query.lower().split() if len(w) > 2}
    if not words:
        return 50
    text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
    hits = sum(1 for w in words if w in text)
    return min(100, int(hits / len(words) * 100))


def _badge_style(score: int) -> tuple[str, str, str]:
    """Return (label, text_color, bg_color) for a relevance score."""
    if score >= 70:
        return "🟢 Alta", "#4ade80", "rgba(74,222,128,0.1)"
    if score >= 40:
        return "🟡 Media", "#facc15", "rgba(250,204,21,0.1)"
    return "🔴 Baja", "#f87171", "rgba(248,113,113,0.1)"


# ── Header & Metrics ───────────────────────────────────────────────────────────

def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
            <h1>🔬 Asistente de Investigación</h1>
            <p class="app-tagline">
                Explora, compara y conversa con la literatura científica más reciente
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(n_papers: int, query: str) -> None:
    query_display = f'"{query[:35]}…"' if len(query) > 35 else f'"{query}"'
    st.markdown(
        f"""
        <div class="metrics-row">
            <div class="metric-box">
                <div class="metric-label">📄 Papers encontrados</div>
                <div class="metric-value">{n_papers}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">🔍 Query analizada</div>
                <div class="metric-value" style="font-size:0.92rem">{query_display}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">✅ Estado</div>
                <div class="metric-value" style="color:#4ade80">Análisis completo</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Paper Card ─────────────────────────────────────────────────────────────────

def render_paper_card(paper: dict, query: str, idx: int) -> None:
    """Render a visual paper card (info only – buttons rendered by caller)."""
    score = relevance_score(paper, query)
    badge_label, badge_color, badge_bg = _badge_style(score)

    authors = ", ".join(paper.get("authors", [])[:3])
    title   = paper.get("title", "Sin título")
    date    = paper.get("date", "N/A")
    url     = paper.get("url", "#")
    summary = paper.get("summary", "")
    preview = summary[:320] + "…" if len(summary) > 320 else summary

    st.markdown(
        f"""
        <div class="paper-card">
            <div class="paper-card-top">
                <div class="paper-title">📄 {title}</div>
                <span class="relevance-badge"
                      style="color:{badge_color}; background:{badge_bg};
                             border-color:{badge_color};">
                    {badge_label} · {score}%
                </span>
            </div>
            <div class="paper-meta">
                👤 {authors} &nbsp;·&nbsp; 📅 {date} &nbsp;·&nbsp;
                <a href="{url}" target="_blank">🔗 Ver paper</a>
            </div>
            <div class="paper-preview">{preview}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(score / 100)

    with st.expander("📖 Ver resumen completo"):
        st.markdown(summary)


# ── Comparison ─────────────────────────────────────────────────────────────────

def render_comparison(text: str) -> None:
    """Render the comparative analysis inside a styled highlight box."""
    st.markdown(
        '<div class="comparison-box">'
        '<div class="comparison-label">⚖️ Análisis comparativo · generado por IA</div>',
        unsafe_allow_html=True,
    )
    st.markdown(text)          # renders markdown properly
    st.markdown("</div>", unsafe_allow_html=True)


# ── Chat Header ────────────────────────────────────────────────────────────────

def render_chat_header(title: str) -> None:
    short = title[:90] + "…" if len(title) > 90 else title
    st.markdown(
        f"""
        <div class="chat-header">
            <div class="chat-header-label">💬 Chat con el paper</div>
            <div class="chat-paper-title">{short}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Section label ──────────────────────────────────────────────────────────────

def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)