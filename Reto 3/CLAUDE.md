# CLAUDE.md — Reto 3: Asistente Inteligente para Artículos de Investigación

## Qué es este proyecto

MVP multiagente que permite al usuario escribir un tema o pregunta de investigación y recibe:
- Papers relevantes de ArXiv resumidos individualmente
- Análisis comparativo entre los papers seleccionados
- Todo en el idioma que el usuario elija (español / english), de forma independiente para resúmenes y comparación

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
```

---

## Estructura de archivos

```
Reto_3/
├── app.py                  ← Interfaz Streamlit
├── agents/
│   ├── buscador.py         ← Busca papers en ArXiv (optimiza query con Groq antes)
│   ├── resumidor.py        ← Resume cada paper individualmente con Groq
│   ├── comparador.py       ← Compara papers seleccionados con Groq (2 llamadas)
│   └── orquestador.py      ← Coordina buscador + resumidor + comparador
├── requirements.txt
├── .env                    ← NO subir a git
├── .gitignore
└── CLAUDE.md
```

---

## Arquitectura y flujo

```
Usuario escribe query (puede ser en español o inglés)
        ↓
buscador._optimize_query()   ← Groq traduce/optimiza el query a inglés técnico
        ↓
buscador.search_papers()     ← ArXiv API (delay_seconds=3, num_retries=3)
        ↓
resumidor.summary_paper()    ← Groq resume cada paper (llamada por paper)
        ↓
[Usuario selecciona qué papers comparar via multiselect]
        ↓
comparador.compare_papers()  ← 2 llamadas a Groq:
    1. Extrae JSON con: technologies, value_proposition, primary_contribution
    2. Genera reporte formateado en 3 secciones
        ↓
Streamlit muestra resultados
```

---

## Stack tecnológico

| Componente | Tecnología | Motivo |
|---|---|---|
| LLM | Groq API — `llama-3.3-70b-versatile` | Open source, API gratuita |
| Búsqueda papers | `arxiv` (API oficial) | Estable, sin bloqueos, sin auth |
| Interfaz | Streamlit | UI web rápida sin frontend |
| Variables de entorno | `python-dotenv` | Proteger API key |

---

## Decisiones de diseño importantes

### Fuentes de datos descartadas
- **`scholarly`** (Google Scholar): bloqueado por CAPTCHA — descartado
- **`semanticscholar`**: sin conexión en el entorno — descartado
- Solo se usa **ArXiv**, que es suficiente para IA/ML

### Por qué `_optimize_query()` en buscador.py
ArXiv está en inglés. Queries en español devuelven resultados irrelevantes. Groq traduce y mejora el query antes de enviarlo a ArXiv.

### Por qué 2 llamadas en comparador.py
- **Llamada 1**: extrae JSON estructurado (datos crudos, confiables)
- **Llamada 2**: convierte el JSON en reporte legible con formato markdown
Separar extracción de presentación mejora la calidad y control del output.

### Por qué `st.session_state` en app.py
Streamlit re-ejecuta el script completo en cada interacción. Sin session_state, los resultados se borran al hacer clic en cualquier botón.

### Idiomas independientes
El usuario elige idioma del resumen y idioma del análisis comparativo por separado. Ambos aceptan `"español"` o `"english"`.

---

## Formato de datos internos

Un paper en el sistema tiene esta estructura:
```python
{
    "title": str,
    "abstract": str,       # texto completo del abstract de ArXiv
    "url": str,            # enlace directo al paper
    "authors": list[str],
    "date": str,           # formato "YYYY-MM-DD"
    "summary": str         # añadido por resumidor — formato markdown con Idea Principal + Resumen
}
```

---

## Prompts — notas clave

### resumidor.py
- El prompt tiene instrucción `MANDATORY: Write in {language}` al inicio para forzar el idioma
- Formato de salida esperado:
  ```
  **Idea Principal:** [frase]

  **Resumen:** [párrafo]
  ```
- El cuerpo del prompt está en español/inglés mezclado — no afecta el output porque el modelo sigue la instrucción de idioma

### comparador.py — prompt 1
- Extrae solo 3 campos: `technologies`, `value_proposition`, `primary_contribution`
- Incluye el query del usuario en `query_context` para que `value_proposition` se evalúe contra la pregunta real
- Devuelve JSON puro (sin markdown)

### comparador.py — prompt 2
- 3 secciones: Tecnologías | Propuesta de valor vs query | Veredicto final
- Límite de 280 palabras para ahorrar tokens (API gratuita)
- Instrucción `MANDATORY: Write in {language}` al inicio

---

## Problemas conocidos y soluciones

| Problema | Causa | Solución aplicada |
|---|---|---|
| HTTP 429 de ArXiv | Rate limiting por muchas peticiones seguidas | `delay_seconds=3, num_retries=3` en el cliente |
| Papers irrelevantes | Query en español no coincide con papers en inglés | `_optimize_query()` traduce antes de buscar |
| Botones reinician la app | Streamlit re-ejecuta el script completo | `st.session_state` persiste resultados |
| Mezcla de idiomas en output | Prompt en español biasea hacia español | Instrucción `MANDATORY` al inicio de cada prompt |

---

## Estado del proyecto

- [x] Fase 1 — Entorno y búsqueda (ArXiv funcionando)
- [x] Fase 2 — Agentes (buscador, resumidor, comparador, orquestador)
- [x] Fase 3 — Interfaz Streamlit
- [ ] Fase 4 — Pruebas completas y ajuste de prompts

## Pendiente / posibles mejoras

- Añadir segunda fuente de datos (Semantic Scholar o PubMed) al buscador sin tocar el resto
- Limpiar `requirements.txt` (tiene `semanticscholar` y `requests` que no se usan)
- El prompt de `resumidor.py` tiene cuerpo mezclado español/inglés — se puede unificar a inglés
