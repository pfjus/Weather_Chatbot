import requests
import os
import re
import spacy
from dotenv import load_dotenv
from requests.exceptions import RequestException, HTTPError

load_dotenv()  # Cargar variables de .env

API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Cargar modelo NLP en español
nlp = spacy.load("es_core_news_sm")

def extraer_ciudad(texto_usuario: str) -> str:
    #Extrae un nombre de ciudad del texto usando regex + spaCy como respaldo.
    palabras_no_ciudad = r"\b(hoy|mañana|ayer|esta noche|esta mañana|esta tarde)\b"

    # Regex principal
    coincidencia = re.search(
        rf"(?:en|de)\s+([A-Za-záéíóúÁÉÍÓÚñÑ]+(?:\s[A-Za-záéíóúÁÉÍÓÚñÑ]+){{0,2}})(?=\s|[?.!,]|$)",
        texto_usuario,
        re.IGNORECASE
    )
    if coincidencia:
        ciudad = coincidencia.group(1).strip()
        # Eliminar si termina con palabra no ciudad
        ciudad = re.sub(palabras_no_ciudad, "", ciudad, flags=re.IGNORECASE).strip()
        return ciudad if ciudad else None

    # SpaCy como respaldo
    doc = nlp(texto_usuario)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            return ent.text.strip()

    return None

def obtener_clima(texto_usuario: str) -> str:
    # Obtiene el clima de la ciudad detectada en el texto del usuario usando OpenWeather API.
    
    ciudad = extraer_ciudad(texto_usuario)
    if not ciudad:
        return "No pude detectar la ciudad en tu mensaje. Intenta escribir algo como 'en Madrid'."

    url = f"http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={API_KEY}&units=metric&lang=es"

    try:
        respuesta = requests.get(url, timeout=5)
        respuesta.raise_for_status()  # Puede lanzar HTTPError
        datos = respuesta.json()

        if datos.get("cod") != 200:
            return f"No pude obtener el clima para {ciudad}. Revisa el nombre de la ciudad."

        temp = datos['main']['temp']
        desc = datos['weather'][0]['description']
        humedad = datos['main']['humidity']
        viento = datos['wind']['speed']

        recomendaciones = recomendacion_ropa(temp, desc)

        return (f"En {ciudad} hace {temp}°C, clima {desc}, humedad {humedad}% y viento {viento} m/s."
                f"{recomendaciones}")

    except RequestException:
        # Atrapa errores de conexión y HTTP
        return "Error de conexión. Intenta de nuevo más tarde."
    
def recomendacion_ropa(temp: float, descripcion: str) -> str:
    # Devuelve recomendaciones según la temperatura y descripción del clima.

    recomendaciones = []

    if temp <= 10:
        recomendaciones.append(" Abrígate, hace bastante frío 🧥")
    elif temp <= 20:
        recomendaciones.append(" Quizá necesites una chaqueta ligera 🧥")
    elif temp <= 25:
        recomendaciones.append(" Ropa cómoda y ligera está bien 👕")
    else:
        recomendaciones.append(" Hace calor, ropa fresca y protección solar ☀️")

    # Basado en la descripción
    if "lluvia" in descripcion.lower():
        recomendaciones.append("lleva paraguas o impermeable ☔")
    if "nieve" in descripcion.lower():
        recomendaciones.append("usa ropa abrigada y calzado adecuado ❄️")
    if "viento" in descripcion.lower():
        recomendaciones.append("cuidado con el viento, quizás un cortavientos 🌬️")

    return " ".join(recomendaciones)

