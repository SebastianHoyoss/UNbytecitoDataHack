import streamlit as st


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,700;1,400&family=JetBrains+Mono:wght@400;500&display=swap');

        /* ── Keyframes ───────────────────────────────────────────── */
        @keyframes fadeSlideUp {
          from { opacity:0; transform:translateY(18px); }
          to   { opacity:1; transform:translateY(0); }
        }
        @keyframes gradientShift {
          0%,100% { background-position:0% 60%; }
          50%      { background-position:100% 40%; }
        }
        @keyframes livePulse {
          0%,100% { box-shadow:0 0 0 0 rgba(74,222,128,0.55); }
          60%     { box-shadow:0 0 0 7px rgba(74,222,128,0); }
        }
        @keyframes borderGlow {
          0%,100% { border-color:rgba(99,102,241,0.18); }
          50%      { border-color:rgba(99,102,241,0.5); }
        }
        @keyframes soaGlow {
          0%,100% { border-color:rgba(20,184,166,0.18); }
          50%      { border-color:rgba(20,184,166,0.45); }
        }
        @keyframes chipIn {
          from { opacity:0; transform:scale(0.88); }
          to   { opacity:1; transform:scale(1); }
        }

        /* ── Global ──────────────────────────────────────────────── */
        html, body, [class*="css"] { font-family:'DM Sans',sans-serif !important; }
        [data-testid="stAppViewContainer"] { background:#080c14; }
        [data-testid="stSidebar"] { display:none; }
        .block-container { padding-top:2.5rem; max-width:1080px; }

        /* ── Header ──────────────────────────────────────────────── */
        .app-header { padding:0 0 1.75rem; }
        .app-header h1 {
            font-family:'DM Serif Display',serif; font-weight:400;
            font-size:2.5rem; letter-spacing:-0.01em;
            background:linear-gradient(130deg,#93c5fd 0%,#818cf8 45%,#c4b5fd 100%);
            background-size:250% 250%; animation:gradientShift 6s ease infinite;
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;
            margin:0 0 0.4rem;
        }
        .app-tagline { color:#374151; font-size:0.95rem; margin:0; }

        /* ── Welcome ─────────────────────────────────────────────── */
        .welcome-wrap {
            text-align:center; padding:4rem 2rem 3rem;
            animation:fadeSlideUp 0.55s ease both;
        }
        .welcome-wrap .icon { font-size:3.2rem; margin-bottom:1.1rem; }
        .welcome-wrap h2 {
            font-family:'DM Serif Display',serif; font-size:1.65rem;
            font-weight:400; color:#e2e8f0; margin:0 0 0.6rem;
        }
        .welcome-wrap p { color:#4b5563; font-size:0.93rem; max-width:460px; margin:0 auto 1.75rem; }
        .feat-chips { display:flex; flex-wrap:wrap; gap:0.5rem; justify-content:center; }
        .feat-chip {
            background:#0f1420; border:1px solid rgba(255,255,255,0.07);
            color:#64748b; font-size:0.78rem; padding:0.35rem 0.9rem;
            border-radius:999px; font-weight:500;
        }

        /* ── Metrics ─────────────────────────────────────────────── */
        .metrics-row { display:flex; gap:0.85rem; margin:1rem 0 1.6rem; }
        .metric-box {
            flex:1; background:#0f1420; border:1px solid rgba(255,255,255,0.06);
            border-top:2px solid; border-radius:10px; padding:0.9rem 1.15rem;
            animation:fadeSlideUp 0.4s ease both;
        }
        .metric-box:nth-child(1) { border-top-color:#3b82f6; }
        .metric-box:nth-child(2) { border-top-color:#818cf8; animation-delay:.07s; }
        .metric-box:nth-child(3) { border-top-color:#4ade80; animation-delay:.14s; }
        .metric-label {
            font-size:0.67rem; color:#374151; text-transform:uppercase;
            letter-spacing:0.09em; font-weight:600; margin-bottom:0.3rem;
        }
        .metric-value { font-family:'DM Serif Display',serif; font-size:1.2rem; color:#e2e8f0; }
        .live-dot {
            display:inline-block; width:8px; height:8px; background:#4ade80;
            border-radius:50%; margin-right:5px; vertical-align:middle;
            animation:livePulse 2s ease infinite;
        }

        /* ── Section title ───────────────────────────────────────── */
        .section-title {
            font-size:0.7rem; font-weight:700; color:#374151;
            text-transform:uppercase; letter-spacing:0.13em;
            margin:0.25rem 0 1.1rem; padding-bottom:0.5rem;
            border-bottom:1px solid rgba(255,255,255,0.05);
        }

        /* ── Keyword chips ───────────────────────────────────────── */
        .kw-chips { display:flex; flex-wrap:wrap; gap:0.4rem; margin-bottom:1.25rem; }
        .kw-chip {
            background:rgba(59,130,246,0.08); border:1px solid rgba(59,130,246,0.22);
            color:#60a5fa; font-size:0.74rem; padding:0.22rem 0.7rem;
            border-radius:999px; font-weight:500; animation:chipIn 0.3s ease both;
        }

        /* ── Paper card ──────────────────────────────────────────── */
        .paper-card {
            background:#0f1420; border:1px solid rgba(255,255,255,0.06);
            border-radius:14px; padding:1.35rem 1.6rem; margin-bottom:0.35rem;
            transition:border-color 0.2s,box-shadow 0.2s;
            animation:fadeSlideUp 0.45s ease both;
        }
        .paper-card:hover {
            border-color:rgba(96,165,250,0.3);
            box-shadow:0 4px 32px rgba(59,130,246,0.07);
        }
        .paper-card-top {
            display:flex; justify-content:space-between;
            align-items:flex-start; gap:1rem; margin-bottom:0.5rem;
        }
        .paper-title {
            font-family:'DM Serif Display',serif; font-weight:400;
            font-size:1.05rem; color:#dde5f0; line-height:1.5; flex:1;
        }
        .relevance-badge {
            font-size:0.67rem; font-weight:700; padding:0.22rem 0.65rem;
            border-radius:999px; white-space:nowrap; letter-spacing:0.04em; border:1px solid;
        }
        .paper-meta { font-size:0.78rem; color:#2d3748; margin-bottom:0.8rem; }
        .paper-meta a { color:#60a5fa; text-decoration:none; }
        .paper-meta a:hover { text-decoration:underline; }
        .reading-badge {
            font-family:'JetBrains Mono',monospace; font-size:0.67rem;
            color:#374151; background:rgba(255,255,255,0.03);
            padding:0.12rem 0.45rem; border-radius:4px; margin-left:0.35rem;
        }
        .paper-preview {
            font-size:0.85rem; color:#4b5563; line-height:1.7;
            border-left:2px solid rgba(59,130,246,0.35);
            padding:0.65rem 1rem; border-radius:0 8px 8px 0;
        }
        mark {
            background:rgba(59,130,246,0.18); color:#93c5fd;
            border-radius:3px; padding:0 2px;
        }

        /* ── Comparison box ──────────────────────────────────────── */
        .comparison-box {
            background:#0f1420; border:1px solid rgba(99,102,241,0.2);
            border-radius:14px; padding:0.5rem 1.6rem 1.25rem; margin-top:0.75rem;
            animation:borderGlow 3.5s ease infinite;
        }
        .comparison-label {
            font-size:0.67rem; color:#818cf8; text-transform:uppercase;
            letter-spacing:0.11em; font-weight:700;
            padding:0.6rem 0; border-bottom:1px solid rgba(255,255,255,0.04);
            margin-bottom:0.9rem;
        }

        /* ── Estado del Arte box ─────────────────────────────────── */
        .soa-box {
            background:#0f1420; border:1px solid rgba(20,184,166,0.2);
            border-radius:14px; padding:0.5rem 1.6rem 1.25rem; margin-top:0.75rem;
            animation:soaGlow 3.5s ease infinite;
        }
        .soa-label {
            font-size:0.67rem; color:#2dd4bf; text-transform:uppercase;
            letter-spacing:0.11em; font-weight:700;
            padding:0.6rem 0; border-bottom:1px solid rgba(255,255,255,0.04);
            margin-bottom:0.9rem;
        }

        /* ── Chat header ─────────────────────────────────────────── */
        .chat-header {
            background:#0f1420; border:1px solid rgba(255,255,255,0.06);
            border-radius:12px; padding:1rem 1.5rem; margin-bottom:1rem;
            animation:fadeSlideUp 0.4s ease both;
        }
        .chat-header-label {
            font-size:0.67rem; color:#60a5fa; text-transform:uppercase;
            letter-spacing:0.11em; font-weight:700; margin-bottom:0.3rem;
        }
        .chat-paper-title { font-family:'DM Serif Display',serif; font-size:1rem; color:#dde5f0; }

        /* ── Progress bar ────────────────────────────────────────── */
        [data-testid="stProgressBar"]>div>div {
            background:linear-gradient(90deg,#3b82f6,#818cf8) !important;
            border-radius:999px !important;
        }
        [data-testid="stProgressBar"] { border-radius:999px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )