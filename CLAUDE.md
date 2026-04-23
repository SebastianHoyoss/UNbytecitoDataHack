# CLAUDE.md — Reto 3: Asistente Inteligente para Artículos de Investigación

## Qué es este proyecto

MVP multiagente que permite al usuario escribir un tema o pregunta de investigación y recibe:
- Papers relevantes de ArXiv resumidos individualmente
- Análisis comparativo entre los papers seleccionados
- Síntesis del estado del arte alineada con la pregunta de investigación
- Chat RAG sobre cualquier paper encontrado (vectorizado en Pinecone)
- Todo en el idioma que el usuario elija (español / english)

---

## Cómo ejecutar

```bash
# Activar entorno virtual
source .venv/Scripts/activate   # Git Bash
# o
.venv\Scripts\activate           # cmd/PowerShell

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar app
streamlit run app.py
```

Requiere archivo `.env` en la raíz con:
```
GROQ_API_KEY=tu_api_key
PINECONE_API_KEY=tu_api_key
PINECONE_INDEX=papers-rag
```

---

## Estructura de archivos

```
├── app.py                      ← Interfaz Streamlit
├── agents/
│   ├── buscador.py             ← Busca papers en ArXiv (optimiza query con Groq antes)
│   ├── resumidor.py            ← Resume cada paper individualmente con Groq
│   ├── comparador.py           ← Compara papers seleccionados con Groq (2 llamadas)
│   ├── investigador.py         ← Genera síntesis del estado del arte con Groq (2 llamadas)
│   └── orquestador.py          ← Coordina buscador + resumidor
├── rag/
│   ├── loader.py               ← Descarga PDF de ArXiv y extrae texto
│   ├── chunker.py              ← Divide texto en chunks (500 chars, 100 overlap)
│   ├── embedder.py             ← Genera embeddings con sentence-transformers (384 dims)
│   ├── pinecone_db.py          ← Sube y consulta vectores en Pinecone
│   └── rag_agent.py            ← Responde preguntas usando contexto recuperado + Groq
├── requirements.txt
├── .env                        ← NO subir a git
├── .gitignore
└── CLAUDE.md
```

---

## Arquitectura y flujo

### Flujo principal (búsqueda)
```
Usuario escribe query (puede ser en español o inglés)
        ↓
buscador._optimize_query()   ← Groq traduce/optimiza el query a inglés técnico
        ↓
buscador.search_papers()     ← ArXiv API (delay_seconds=5, num_retries=5)
        ↓
resumidor.summary_paper()    ← Groq resume cada paper (llamada por paper)
        ↓
[Usuario selecciona papers y elige acción]
        ↓
comparador.compare_papers()          ← 2 llamadas a Groq (JSON + reporte)
investigador.state_of_the_art()      ← 2 llamadas a Groq (JSON + síntesis)
```

### Flujo RAG (chat con paper)
```
Usuario hace clic en "💬 Chatear con este paper"
        ↓
loader.download_and_extract()   ← Descarga PDF desde arxiv.org/pdf/{id}
        ↓
chunker.chunk_text()            ← Divide en chunks de 500 chars, 100 overlap
        ↓
embedder.embed()                ← sentence-transformers all-MiniLM-L6-v2 (384 dims)
        ↓
pinecone_db.upsert_paper()      ← Sube vectores a Pinecone (namespace = arxiv_id)
        ↓
[Usuario escribe pregunta]
        ↓
pinecone_db.query()             ← Recupera top-4 chunks más similares
        ↓
rag_agent.answer_question()     ← Groq genera respuesta con el contexto recuperado
```

---

## Stack tecnológico

| Componente | Tecnología | Motivo |
|---|---|---|
| LLM principal | Groq — `llama-3.3-70b-versatile` | Open source, API gratuita, 100K tokens/día |
| LLM RAG | Groq — `llama-3.1-8b-instant` | 500K tokens/día, suficiente para QA con contexto |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`) | Gratis, local, 384 dims |
| Vector DB | Pinecone (free tier) | 1 index, namespace por paper |
| Búsqueda papers | `arxiv` (API oficial) | Estable, sin bloqueos, sin auth |
| Interfaz | Streamlit | UI web rápida sin frontend |
| Variables de entorno | `python-dotenv` | Proteger API keys |

---

## Decisiones de diseño importantes

### Fuentes de datos descartadas
- **`scholarly`** (Google Scholar): bloqueado por CAPTCHA — descartado
- **`semanticscholar`**: sin conexión en el entorno — descartado
- Solo se usa **ArXiv**, que es suficiente para IA/ML

### Por qué `_optimize_query()` en buscador.py
ArXiv está en inglés. Queries en español devuelven resultados irrelevantes. Groq traduce y mejora el query antes de enviarlo a ArXiv.

### Por qué 2 llamadas en comparador.py e investigador.py
- **Llamada 1**: extrae JSON estructurado (datos crudos, confiables)
- **Llamada 2**: convierte el JSON en reporte/síntesis legible con formato markdown
Separar extracción de presentación mejora la calidad y control del output.

### Por qué `st.session_state` en app.py
Streamlit re-ejecuta el script completo en cada interacción. Sin session_state, los resultados se borran al hacer clic en cualquier botón.

### Por qué namespace por paper en Pinecone
Cada paper se vectoriza bajo su arxiv_id como namespace. Esto permite:
- Buscar solo dentro del paper seleccionado (sin mezclar contenido)
- Detectar si ya fue indexado antes (evita re-descargar y re-vectorizar)

### Gestión de tokens (API gratuita)
- Abstract truncado a 400 chars en comparador e investigador
- RAG usa modelo 8B (límite propio de 500K/día) para no consumir cuota del 70B
- top_k=4 en Pinecone para reducir contexto enviado al LLM

### Idiomas independientes
El usuario elige idioma del resumen, del análisis y del chat por separado. Todos aceptan `"español"` o `"english"`. Instrucción `MANDATORY` al inicio de cada prompt para forzar el idioma sin que el cuerpo del prompt biasee el output.

---

## Formato de datos internos

Un paper en el sistema tiene esta estructura:
```python
{
    "title": str,
    "abstract": str,       # texto completo del abstract de ArXiv
    "url": str,            # entry_id de ArXiv → "http://arxiv.org/abs/XXXX.XXXXX"
    "authors": list[str],
    "date": str,           # formato "YYYY-MM-DD"
    "summary": str         # añadido por resumidor — formato markdown con Idea Principal + Resumen
}
```

El `arxiv_id` se extrae de `url` con regex en `rag/loader.py` y se usa como namespace en Pinecone.

---

## Prompts — notas clave

### resumidor.py
- Instrucción `MANDATORY: Write in {language}` al inicio para forzar el idioma
- Formato de salida: `**Idea Principal:** / **Resumen:**`

### comparador.py — prompt 1
- Extrae 3 campos: `technologies`, `value_proposition`, `primary_contribution`
- Abstract truncado a 400 chars para ahorrar tokens
- Devuelve JSON puro (sin markdown)

### comparador.py — prompt 2
- 3 secciones: Tecnologías | Propuesta de valor vs query | Veredicto final
- Límite de 280 palabras

### investigador.py — prompt 1
- Extrae 5 campos: `id`, `title`, `year`, `current_status`, `gap`
- Abstract truncado a 400 chars
- Devuelve JSON puro

### investigador.py — prompt 2
- 1 párrafo académico (130-170 palabras) + referencias clave
- Alineado con la pregunta de investigación del usuario

### rag_agent.py
- Modelo: `llama-3.1-8b-instant`
- Formato de respuesta estructurado en 3 partes: respuesta directa + evidencia + limitación
- Contexto: top-4 chunks de Pinecone unidos con separadores

---

## Problemas conocidos y soluciones

| Problema | Causa | Solución aplicada |
|---|---|---|
| HTTP 429 de ArXiv | Rate limiting por muchas peticiones seguidas | `delay_seconds=5, num_retries=5` + mensaje de error amigable en UI |
| HTTP 429 de Groq | Límite diario de 100K tokens (70B) | RAG usa modelo 8B con límite propio; abstracts truncados |
| Papers irrelevantes | Query en español no coincide con papers en inglés | `_optimize_query()` traduce antes de buscar |
| Botones reinician la app | Streamlit re-ejecuta el script completo | `st.session_state` persiste todos los resultados |
| Mezcla de idiomas en output | Prompt en español biasea hacia español | Instrucción `MANDATORY` al inicio + cuerpo del prompt en inglés |
| Chat con paper diferente | Historial del chat anterior persiste | Al seleccionar nuevo paper se limpia `chat_history` automáticamente |

---

## Estado del proyecto

- [x] Fase 1 — Entorno y búsqueda (ArXiv funcionando)
- [x] Fase 2 — Agentes (buscador, resumidor, comparador, orquestador, investigador)
- [x] Fase 3 — Interfaz Streamlit
- [x] Fase 3.5 — Sistema RAG con Pinecone (chat por paper)
- [ ] Fase 4 — Pruebas completas y ajuste de prompts

## Pendiente / posibles mejoras

- Añadir segunda fuente de datos (Semantic Scholar o PubMed) al buscador sin tocar el resto
- Unificar el prompt de `resumidor.py` a inglés (cuerpo mezclado español/inglés)
- Rotación de API keys de Groq para mayor cuota diaria
