# Librerias 
import re
import logging
import requests

from pathlib import Path
from dotenv import load_dotenv
from typing import Tuple, Optional
from datetime import datetime, timedelta
from src.ollama_client import generar_respuesta_ollama
from src.clima import extraer_ciudad, recomendacion_ropa  

# logging
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# cargar env (si no se hizo ya)
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)
import os
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Helpers de OpenWeather
def fetch_current(ciudad: str) -> Optional[dict]:
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": ciudad, "appid": API_KEY, "units": "metric", "lang": "es"}
    try:
        r = requests.get(url, params=params, timeout=6)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.error(f"fetch_current error: {e}")
        return None

def fetch_forecast(ciudad: str) -> Optional[dict]:
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": ciudad, "appid": API_KEY, "units": "metric", "lang": "es"}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logging.error(f"fetch_forecast error: {e}")
        return None

def resumen_actual_desde_json(datos: dict) -> str:
    if not datos:
        return "No hay datos actuales."
    try:
        temp = datos["main"]["temp"]
        desc = datos["weather"][0]["description"]
        humedad = datos["main"]["humidity"]
        viento = datos["wind"]["speed"]
        recom = recomendacion_ropa(temp, desc)
        return f"{datos.get('name')}: {temp}°C, {desc}, humedad {humedad}%, viento {viento} m/s. {recom}"
    except Exception:
        return "No se pudieron parsear los datos actuales."

def resumen_manana_from_forecast(datos: dict) -> Optional[str]:
    if not datos or "list" not in datos:
        return None

    # calcular fecha de mañana en UTC offset simple: usamos la fecha local (sin convertir zonas)
    hoy = datetime.utcnow().date()
    manana = hoy + timedelta(days=1)

    # buscaremos el primer bloque cuya fecha sea 'mañana' y hora cercana a 12:00
    candidatos = []
    for item in datos["list"]:
        dt_txt = item.get("dt_txt")  # ejemplo: '2025-10-28 12:00:00'
        if not dt_txt:
            continue
        try:
            dt = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if dt.date() == manana:
            candidatos.append((abs(dt.hour - 12), item))  # preferir hora 12
    if not candidatos:
        return None
    candidatos.sort(key=lambda x: x[0])
    mejor = candidatos[0][1]
    try:
        temp = mejor["main"]["temp"]
        desc = mejor["weather"][0]["description"]
        humedad = mejor["main"]["humidity"]
        viento = mejor["wind"]["speed"]
        return f"Mañana: {temp}°C, {desc}, humedad {humedad}%, viento {viento} m/s."
    except Exception:
        return None

# Intent detection helpers
def es_saludo(texto: str) -> bool:
    return bool(re.search(r"\b(hola|buenas|buen día|buenas tardes|qué tal)\b", texto, re.I))

def es_consulta_clima(texto: str) -> bool:
    return bool(re.search(r"\b(clima|tiempo|temperatura|lluvia|nev(a|e)|viento|hoy|mañana)\b", texto, re.I))

def menciona_futuro(texto: str) -> bool:
    return bool(re.search(r"\b(mañana|pasado mañana|próximo|próxima|semana)\b", texto, re.I))

# Main: procesa mensaje y devuelve (respuesta_texto, ciudad_usada)
def procesar_mensaje(texto_usuario: str, ultima_ciudad: Optional[str] = None) -> Tuple[str, Optional[str]]:
    texto = texto_usuario.strip()
    texto_low = texto.lower()

    # 1) Extraer ciudad explícita
    ciudad_detectada = extraer_ciudad(texto)

    # 2) Si no hay ciudad explícita y existe memoria, y texto parece referencia temporal, asignar memoria
    if not ciudad_detectada and ultima_ciudad and (menciona_futuro(texto_low) or re.search(r"\b(hoy|ahora|ahí)\b", texto_low)):
        ciudad_detectada = ultima_ciudad

    # 3) Si no es consulta de clima => usar Ollama para conversación general
    if not es_consulta_clima(texto_low) and not ciudad_detectada:
        # saludo/charla general
        if es_saludo(texto_low):
            prompt = f"Eres Avir, un asistente amable. Responde a este saludo en español de forma breve y natural: '{texto_usuario}'"
            resp = generar_respuesta_ollama(prompt)
            if resp:
                return resp, ultima_ciudad
            else:
                return "¡Hola! ¿En qué ciudad te gustaría saber el clima?", ultima_ciudad

    # 4) Si menciona futuro (mañana...) -> intentar forecast
    if menciona_futuro(texto_low):
        ciudad = ciudad_detectada or ultima_ciudad
        if not ciudad:
            # pedir ciudad
            return "¿Para qué ciudad quieres el pronóstico de mañana?", None

        # obtener forecast
        forecast_json = fetch_forecast(ciudad)
        resumen_manana = resumen_manana_from_forecast(forecast_json)
        current_json = fetch_current(ciudad)
        resumen_actual = resumen_actual_desde_json(current_json)

        # construir prompt para Ollama (si disponible)
        prompt = (
            f"Eres un asistente del clima. El usuario preguntó: '{texto_usuario}'.\n"
            f"Ciudad: {ciudad}\n"
            f"Datos actuales: {resumen_actual}\n"
            f"Pronóstico (mañana): {resumen_manana or 'No disponible'}\n"
            "Responde de forma natural y útil en español, explicando diferencia entre ahora y mañana."
        )
        resp = generar_respuesta_ollama(prompt)
        if resp:
            return resp, ciudad
        # fallback: respuesta construida localmente
        fallback = f"{resumen_actual} {resumen_manana or ''}".strip()
        return fallback, ciudad

    # 5) Consulta de clima actual
    ciudad = ciudad_detectada or ultima_ciudad
    if not ciudad:
        return "¿Para qué ciudad quieres saber el clima?", None

    current_json = fetch_current(ciudad)
    resumen_actual = resumen_actual_desde_json(current_json)

    # enviar a Ollama para naturalidad
    prompt = (
        f"Eres un asistente del clima. Usuario: '{texto_usuario}'.\n"
        f"Datos actuales: {resumen_actual}\n"
        "Responde brevemente y con tono amable."
    )
    resp = generar_respuesta_ollama(prompt)
    if resp:
        return resp, ciudad

    # fallback si Ollama falla
    return resumen_actual, ciudad
