import streamlit as st
from agents.orquestador import orchestrate
from agents.comparador import compare_papers

st.title("Asistente de Investigación Académica")

if "results" not in st.session_state:
    st.session_state.results = None
if "comparison" not in st.session_state:
    st.session_state.comparison = None
if "language" not in st.session_state:
    st.session_state.language = "español"
if "comparison_language" not in st.session_state:
    st.session_state.comparison_language = "español"

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
    st.session_state.language = language
    with st.spinner("Buscando y resumiendo papers..."):
        st.session_state.results = orchestrate(query, language=language, max_results=max_results, compare=False)

if st.session_state.results:
    result = st.session_state.results

    st.subheader(f"Resultados para: *{result['query']}*")

    for paper in result["papers"]:
        with st.expander(f"📄 {paper['title']}"):
            st.markdown(f"**Autores:** {', '.join(paper['authors'][:3])}")
            st.markdown(f"**Fecha:** {paper['date']}")
            st.markdown(f"**URL:** [Ver paper]({paper['url']})")
            st.markdown(paper["summary"])

    st.divider()

    paper_titles = [p["title"] for p in result["papers"]]
    selected_titles = st.multiselect(
        "Selecciona los papers a comparar:",
        options=paper_titles,
        default=paper_titles
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        comparison_language = st.selectbox(
            "Idioma del análisis comparativo:",
            ["español", "english"],
            index=["español", "english"].index(st.session_state.comparison_language)
        )
    with col2:
        st.write("")
        st.write("")
        compare_clicked = st.button("Comparar papers seleccionados")

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

if st.session_state.comparison:
    st.subheader("Análisis Comparativo")
    st.markdown(st.session_state.comparison)
