# src/ollama_client.py
import subprocess
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def generar_respuesta_ollama(prompt: str, modelo: str = "llama3") -> str:
    """
    Llama a Ollama localmente pasando `prompt` por stdin.
    Devuelve la salida como texto.
    Si falla, devuelve una cadena vacía para que el caller haga fallback.
    """
    try:
        logging.info("Enviando prompt a Ollama...")
        # Usamos Popen y comunicamos por stdin; forzamos encoding utf-8
        proc = subprocess.Popen(
            ["ollama", "run", modelo],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        stdout, stderr = proc.communicate(prompt, timeout=30)

        if proc.returncode != 0:
            logging.error(f"Ollama error: {stderr.strip()}")
            return ""  # fallback in caller

        return (stdout or "").strip()

    except subprocess.TimeoutExpired:
        logging.error("Ollama: timeout expired")
        return ""
    except FileNotFoundError:
        logging.error("Ollama no está instalado o no se encuentra en PATH")
        return ""
    except Exception as e:
        logging.error(f"Error inesperado al llamar a Ollama: {e}")
        return ""
