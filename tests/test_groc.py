from groq import Groq
from dotenv import load_dotenv
import os
# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Crear un cliente de Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Realizar una consulta de chat a Groq
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "Di hola en una sola frase"}
    ]
)

# Imprimir la respuesta de Groq
print(response.choices[0].message.content)