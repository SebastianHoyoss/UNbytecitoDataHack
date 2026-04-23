from utils.groq_client import chat

# Función para resumir un paper dado su título y abstract
def summary_paper(title:str, abstract:str, language:str)-> str:
    
    # Definir el prompt para la consulta a Groq
    prompt="""
        MANDATORY: Write your entire response in {language}. Every word must be in {language}.

        Role:
            You are a research assistant specialized in bibliometric analysis.
            Your task is to generate a technical, dense, and brief summary based exclusively on the Title and Abstract provided.
        Parámetros de entrada:
            Título: {title}
            Abstract: {abstract}
            Idioma: {language}
        
        Directrices de Redacción:
            Extensión: Máximo 120 palabras. Sé directo; evita frases de relleno como "En este artículo se analiza...".
            Precisión: Mantén datos numéricos, porcentajes, métricas de rendimiento y fechas exactas, ya que son críticos para la validez científica.
            
        Estructura Obligatoria: El resumen debe responder a los siguientes puntos de forma fluida:
            Problema: ¿Cuál es el vacío o desafío identificado?
            Acción y Metodología: ¿Qué hicieron y bajo qué procedimiento?
            Herramientas: Tecnologías, lenguajes, frameworks o modelos específicos utilizados.
            Resultado/Valor: ¿Cuál fue el hallazgo principal o la mejora cuantitativa lograda?
        
        Configuración de salida:
            Idioma de respuesta: {language}
            Extensión: Máximo 150 palabras.
            Tono: Profesional y técnico.

        Formato de Salida (usa exactamente este formato markdown, con línea en blanco entre secciones):
            **Idea Principal:** [una sola frase aquí]

            **Resumen:** [párrafo único aquí]
        """.format(title=title, abstract=abstract, language=language)
 

    # Realizar una consulta de chat a Groq
    return chat("llama-3.3-70b-versatile", [{"role": "user", "content": prompt}])

if __name__ == "__main__":
    abstract = "We introduce Autoregressive Retrieval Augmentation (AR-RAG), a novel paradigm that enhances image generation by autoregressively incorporating knearest neighbor retrievals at the patch level. Unlike prior methods that perform a single, static retrieval before generation and condition the entire gene"
    title = "AR-RAG: Autoregressive Retrieval Augmentation for Image Generation"
    language = "español"
    print(summary_paper(title, abstract, language))