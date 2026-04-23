import streamlit as st


def inject_css() -> None:
    """Inject custom CSS for the professional dashboard look."""
    st.markdown(
        """
        <style>
        /* ── Global ── */
        [data-testid="stAppViewContainer"] { background: #0d1117; }
        [data-testid="stSidebar"] { display: none; }
        .block-container { padding-top: 2rem; max-width: 1100px; }

        /* ── App Header ── */
        .app-header { padding: 0.5rem 0 1.25rem; margin-bottom: 0.5rem; }
        .app-header h1 {
            font-size: 2rem; font-weight: 800; letter-spacing: -0.03em;
            background: linear-gradient(120deg, #60a5fa 0%, #818cf8 60%, #a78bfa 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin: 0 0 0.3rem;
        }
        .app-tagline { color: #64748b; font-size: 0.95rem; margin: 0; }

        /* ── Metric Row ── */
        .metrics-row {
            display: flex; gap: 1rem; margin: 1rem 0 1.5rem;
        }
        .metric-box {
            flex: 1; background: #161b27; border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px; padding: 0.85rem 1.1rem;
        }
        .metric-label { font-size: 0.7rem; color: #475569; text-transform: uppercase;
                        letter-spacing: 0.08em; font-weight: 600; margin-bottom: 0.25rem; }
        .metric-value { font-size: 1.15rem; font-weight: 700; color: #e2e8f0; }

        /* ── Section Titles ── */
        .section-title {
            font-size: 1rem; font-weight: 700; color: #94a3b8;
            text-transform: uppercase; letter-spacing: 0.1em;
            margin: 0.25rem 0 1rem; padding-bottom: 0.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }

        /* ── Paper Card ── */
        .paper-card {
            background: #161b27; border: 1px solid rgba(255,255,255,0.07);
            border-radius: 12px; padding: 1.25rem 1.5rem;
            margin-bottom: 0.5rem; transition: border-color 0.18s ease;
        }
        .paper-card:hover { border-color: rgba(96, 165, 250, 0.3); }
        .paper-card-top {
            display: flex; justify-content: space-between;
            align-items: flex-start; gap: 1rem; margin-bottom: 0.55rem;
        }
        .paper-title {
            font-size: 1rem; font-weight: 700; color: #e2e8f0;
            line-height: 1.45; flex: 1;
        }
        .relevance-badge {
            font-size: 0.68rem; font-weight: 700; padding: 0.22rem 0.6rem;
            border-radius: 999px; white-space: nowrap; letter-spacing: 0.04em;
            border: 1px solid;
        }
        .paper-meta {
            font-size: 0.79rem; color: #475569; margin-bottom: 0.85rem;
        }
        .paper-meta a { color: #60a5fa; text-decoration: none; }
        .paper-meta a:hover { text-decoration: underline; }
        .paper-preview {
            font-size: 0.86rem; color: #94a3b8; line-height: 1.65;
            background: rgba(255,255,255,0.025);
            border-left: 3px solid #3b82f6;
            padding: 0.7rem 1rem; border-radius: 0 8px 8px 0;
        }

        /* ── Comparison Box ── */
        .comparison-box {
            background: #161b27;
            border: 1px solid rgba(99, 102, 241, 0.25);
            border-radius: 12px; padding: 0.6rem 1.5rem 1rem;
            margin-top: 0.75rem;
        }
        .comparison-label {
            font-size: 0.68rem; color: #818cf8; text-transform: uppercase;
            letter-spacing: 0.1em; font-weight: 700; padding: 0.75rem 0 0.5rem;
            border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 0.75rem;
        }

        /* ── Chat Header ── */
        .chat-header {
            background: #161b27; border: 1px solid rgba(255,255,255,0.07);
            border-radius: 10px; padding: 0.9rem 1.4rem; margin-bottom: 1rem;
        }
        .chat-header-label {
            font-size: 0.68rem; color: #60a5fa; text-transform: uppercase;
            letter-spacing: 0.1em; font-weight: 700; margin-bottom: 0.3rem;
        }
        .chat-paper-title { font-size: 0.97rem; font-weight: 700; color: #e2e8f0; }

        /* ── Progress bar tint ── */
        [data-testid="stProgressBar"] > div > div {
            background: linear-gradient(90deg, #3b82f6, #818cf8) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )