# Reto 3 — Asistente Inteligente para Artículos de Investigación

## 1. Activar el entorno virtual

**Windows (cmd/PowerShell):**
```bash
venv\Scripts\activate
```

**Windows (Git Bash):**
```bash
source venv/Scripts/activate
```

## 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

## 3. Configurar API key de Groq

Crea un archivo `.env` en la raíz del proyecto:
```
GROQ_API_KEY=tu_api_key_aqui
PINECONE_API_KEY=api_key
PINECONE_INDEX=papers-rag
```

## 4. Ejecutar la aplicación

```bash
streamlit run app.py
```
