# src/clima.py
import os
import re
import requests
import spacy
import logging
from dotenv import load_dotenv
from functools import lru_cache
from requests.exceptions import RequestException, HTTPError

# ---------------------------
# CONFIGURACIÓN INICIAL
# ---------------------------

# Cargar variables de entorno (.env)
load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "⚠️ No se encontró la variable 'OPENWEATHER_API_KEY' en el archivo .env."
    )

# Cargar modelo de lenguaje español de spaCy
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    raise RuntimeError(
        "El modelo 'es_core_news_sm' de spaCy no está instalado. "
        "Instálalo con: python -m spacy download es_core_news_sm"
    )

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
)


# ---------------------------
# EXTRACCIÓN DE CIUDAD
# ---------------------------

def extraer_ciudad(texto_usuario: str) -> str:
    """
    Extrae el nombre de una ciudad del texto del usuario.
    Usa expresiones regulares y spaCy como respaldo.
    """
    texto_usuario = texto_usuario.strip()
    palabras_no_ciudad = r"\b(hoy|mañana|ayer|esta noche|esta mañana|esta tarde|tiempo|clima|dime|hace|que)\b"

    # Buscar ciudad tras preposiciones comunes
    coincidencia = re.search(
        r"\b(?:en|de|para|sobre)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s[A-ZÁÉÍÓÚÑa-záéíóúñ]+){0,2})",
        texto_usuario,
        re.IGNORECASE
    )

    if coincidencia:
        posible_ciudad = coincidencia.group(1).strip()
        if not re.search(palabras_no_ciudad, posible_ciudad, re.IGNORECASE):
            logging.info(f"Ciudad detectada (regex): {posible_ciudad}")
            return posible_ciudad.capitalize()

    # Respaldo con spaCy
    doc = nlp(texto_usuario)
    for ent in doc.ents:
        if ent.label_ in ["GPE", "LOC"]:
            logging.info(f"Ciudad detectada (spaCy): {ent.text}")
            return ent.text.strip().capitalize()

    logging.warning("No se detectó ninguna ciudad.")
    return None

# ---------------------------
# CONSULTA DE CLIMA
# ---------------------------

@lru_cache(maxsize=64)
def consultar_clima_api(ciudad: str) -> dict:
    """
    Consulta la API de OpenWeather y devuelve el resultado en formato JSON.
    """
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": ciudad, "appid": API_KEY, "units": "metric", "lang": "es"}

    try:
        logging.info(f"Consultando API de OpenWeather para: {ciudad}")
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()

    except HTTPError as e:
        logging.error(f"Error HTTP ({ciudad}): {e}")
        raise RuntimeError(f"No pude obtener el clima para {ciudad}. (Error HTTP)")

    except RequestException:
        logging.error(f"Error de conexión con la API al consultar {ciudad}.")
        raise RuntimeError("Error de conexión con el servicio de clima.")


# ---------------------------
# RESPUESTA DE CLIMA
# ---------------------------

def obtener_clima(texto_usuario: str, tono: str = "neutro") -> str:
    """
    Procesa el texto del usuario, obtiene el clima y devuelve una respuesta natural.
    """
    ciudad = extraer_ciudad(texto_usuario)
    if not ciudad:
        return "No logré reconocer la ciudad 😅. Prueba con algo como '¿Qué clima hace en Madrid?'"

    try:
        datos = consultar_clima_api(ciudad)
        if datos.get("cod") != 200:
            return f"No pude encontrar información sobre {ciudad} 🌍."

        temp = datos["main"]["temp"]
        desc = datos["weather"][0]["description"]
        humedad = datos["main"]["humidity"]
        viento = datos["wind"]["speed"]

        recomendaciones = recomendacion_ropa(temp, desc)
        return formatear_respuesta(ciudad, temp, desc, humedad, viento, recomendaciones, tono)

    except RuntimeError as e:
        return f"Lo siento 😔, ocurrió un problema: {str(e)}"


# ---------------------------
# FORMATO DE RESPUESTA
# ---------------------------

def formatear_respuesta(ciudad, temp, desc, humedad, viento, recomendaciones, tono):
    """
    Devuelve un texto adaptado según el tono del asistente.
    """
    if tono == "amigable":
        return (f"En {ciudad} hay unos {temp}°C ☁️. El clima está {desc}, "
                f"con {humedad}% de humedad y viento de {viento} m/s. {recomendaciones}")
    elif tono == "profesional":
        return (f"Temperatura actual en {ciudad}: {temp} °C. "
                f"Condiciones: {desc}. Humedad: {humedad} %. Viento: {viento} m/s. {recomendaciones}")
    else:
        return (f"{ciudad}: {temp}°C, {desc}, humedad {humedad}%, viento {viento} m/s. {recomendaciones}")


# ---------------------------
# RECOMENDACIONES DE ROPA
# ---------------------------

def recomendacion_ropa(temp: float, descripcion: str) -> str:
    """
    Sugiere ropa según temperatura y condiciones del clima.
    """
    sugerencias = []

    if temp <= 10:
        sugerencias.append("Abrígate bien 🧥")
    elif temp <= 20:
        sugerencias.append("Una chaqueta ligera te irá bien 🧢")
    elif temp <= 25:
        sugerencias.append("Ropa cómoda y ligera está perfecta 👕")
    else:
        sugerencias.append("Hace calor, usa ropa fresca ☀️")

    if "lluvia" in descripcion.lower():
        sugerencias.append("No olvides el paraguas ☔")
    if "nieve" in descripcion.lower():
        sugerencias.append("Usa abrigo y calzado adecuado ❄️")
    if "viento" in descripcion.lower():
        sugerencias.append("Quizás un cortavientos te ayude 🌬️")

    return " ".join(sugerencias)
