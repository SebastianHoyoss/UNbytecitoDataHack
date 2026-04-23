import re
import streamlit as st


# ── Text utilities ────────────────────────────────────────────────────────────

def highlight_keywords(text: str, query: str) -> str:
    words = sorted({w for w in query.lower().split() if len(w) > 3}, key=len, reverse=True)
    for w in words:
        text = re.sub(f"(?i)({re.escape(w)})", r"<mark>\1</mark>", text)
    return text


def reading_time(summary: str) -> str:
    return f"~{max(1, len(summary.split()) // 200)} min"


def relevance_score(paper: dict, query: str) -> int:
    words = {w for w in query.lower().split() if len(w) > 2}
    if not words:
        return 50
    text = f"{paper.get('title','')} {paper.get('summary','')}".lower()
    return min(100, int(sum(1 for w in words if w in text) / len(words) * 100))


def _badge(score: int) -> tuple[str, str, str]:
    if score >= 70:
        return "🟢 Alta", "#4ade80", "rgba(74,222,128,0.09)"
    if score >= 40:
        return "🟡 Media", "#facc15", "rgba(250,204,21,0.09)"
    return "🔴 Baja", "#f87171", "rgba(248,113,113,0.09)"


# ── Header ────────────────────────────────────────────────────────────────────

def render_header() -> None:
    st.markdown(
        """
        <div class="app-header">
            <h1>🔬 UNasistente</h1>
            <p class="app-tagline">
                Explora, compara y conversa con la literatura científica más reciente
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Welcome / empty state ─────────────────────────────────────────────────────

def render_welcome() -> None:
    st.markdown(
        """
        <div class="welcome-wrap">
            <div class="icon">🔭</div>
            <h2>¿Qué quieres investigar hoy?</h2>
            <p>Escribe un tema y UNasistente buscará, resumirá y comparará
               los papers más relevantes de ArXiv en segundos.</p>
            <div class="feat-chips">
                <span class="feat-chip">🔍 Búsqueda semántica</span>
                <span class="feat-chip">📊 Análisis comparativo</span>
                <span class="feat-chip">🗺️ Estado del Arte</span>
                <span class="feat-chip">💬 Chat con papers (RAG)</span>
                <span class="feat-chip">🏷️ Score de relevancia</span>
                <span class="feat-chip">📥 Exportar informe</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Keyword chips ─────────────────────────────────────────────────────────────

def render_keyword_chips(query: str) -> None:
    words = [w for w in query.split() if len(w) > 3]
    if not words:
        return
    chips = "".join(f'<span class="kw-chip">{w}</span>' for w in words)
    st.markdown(f'<div class="kw-chips">{chips}</div>', unsafe_allow_html=True)


# ── Recent searches ───────────────────────────────────────────────────────────

def render_recent_searches(searches: list[str]) -> str | None:
    if not searches:
        return None
    st.caption("Búsquedas recientes")
    cols = st.columns(len(searches))
    for col, q in zip(cols, searches):
        label = f"↩ {q[:22]}…" if len(q) > 22 else f"↩ {q}"
        if col.button(label, key=f"recent_{q}", use_container_width=True):
            return q
    return None


# ── Metrics ───────────────────────────────────────────────────────────────────

def render_metrics(n_papers: int, query: str) -> None:
    q = f'"{query[:32]}…"' if len(query) > 32 else f'"{query}"'
    st.markdown(
        f"""
        <div class="metrics-row">
            <div class="metric-box">
                <div class="metric-label">📄 Papers encontrados</div>
                <div class="metric-value">{n_papers}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">🔍 Query</div>
                <div class="metric-value" style="font-size:0.9rem">{q}</div>
            </div>
            <div class="metric-box">
                <div class="metric-label">Estado</div>
                <div class="metric-value" style="color:#4ade80;font-size:0.95rem">
                    <span class="live-dot"></span>Completo
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Paper card ────────────────────────────────────────────────────────────────

def render_paper_card(paper: dict, query: str, idx: int) -> None:
    score = relevance_score(paper, query)
    badge_label, badge_color, badge_bg = _badge(score)

    authors      = ", ".join(paper.get("authors", [])[:3])
    title        = paper.get("title", "Sin título")
    date         = paper.get("date", "N/A")
    url          = paper.get("url", "#")
    summary      = paper.get("summary", "")
    rt           = reading_time(summary)
    raw_preview  = summary[:300] + "…" if len(summary) > 300 else summary
    preview_html = highlight_keywords(raw_preview, query)
    delay        = f"{idx * 0.07:.2f}s"

    st.markdown(
        f"""
        <div class="paper-card" style="animation-delay:{delay}">
            <div class="paper-card-top">
                <div class="paper-title">{title}</div>
                <span class="relevance-badge"
                      style="color:{badge_color};background:{badge_bg};border-color:{badge_color}">
                    {badge_label} · {score}%
                </span>
            </div>
            <div class="paper-meta">
                👤 {authors} &nbsp;·&nbsp; 📅 {date}
                <span class="reading-badge">⏱ {rt}</span>
                &nbsp;·&nbsp; <a href="{url}" target="_blank">🔗 Ver paper</a>
            </div>
            <div class="paper-preview">{preview_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(score / 100)
    with st.expander("📖 Ver resumen completo"):
        st.markdown(summary)


# ── Comparison ────────────────────────────────────────────────────────────────

def render_comparison(text: str) -> None:
    st.markdown(
        '<div class="comparison-box">'
        '<div class="comparison-label">⚖️ Análisis comparativo · generado por IA</div>',
        unsafe_allow_html=True,
    )
    st.markdown(text)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Estado del Arte ───────────────────────────────────────────────────────────

def render_state_of_art(text: str) -> None:
    st.markdown(
        '<div class="soa-box">'
        '<div class="soa-label">Estado del Arte · generado por IA</div>',
        unsafe_allow_html=True,
    )
    st.markdown(text)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Chat header ───────────────────────────────────────────────────────────────

def render_chat_header(title: str) -> None:
    short = title[:90] + "…" if len(title) > 90 else title
    st.markdown(
        f"""
        <div class="chat-header">
            <div class="chat-header-label">💬 Chat con el paper · RAG</div>
            <div class="chat-paper-title">{short}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Section label ─────────────────────────────────────────────────────────────

def section_title(text: str) -> None:
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


# ── Markdown export ───────────────────────────────────────────────────────────

def build_export_markdown(result: dict, comparison: str = "", state_of_art: str = "") -> str:
    lines = [
        "# Informe de Investigación\n",
        f"**Query:** {result['query']}\n",
        f"**Papers analizados:** {len(result['papers'])}\n",
        "---\n",
    ]
    for i, p in enumerate(result["papers"], 1):
        authors = ", ".join(p.get("authors", [])[:3])
        lines += [
            f"## {i}. {p.get('title', 'Sin título')}",
            f"- **Autores:** {authors}",
            f"- **Fecha:** {p.get('date', 'N/A')}",
            f"- **URL:** {p.get('url', '')}",
            f"\n### Resumen\n{p.get('summary', '')}\n",
            "---\n",
        ]
    if comparison:
        lines += ["## Análisis Comparativo\n", comparison, "\n---\n"]
    if state_of_art:
        lines += ["## Estado del Arte\n", state_of_art, "\n---\n"]
    return "\n".join(lines)