
# Librerias
import os
import sys
import streamlit as st

from src.clima import obtener_clima
from src.asistente import procesar_mensaje

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))


st.set_page_config(page_title="Chatbot del Clima 🌤️", page_icon="⛅")

st.title("Chatbot del Clima 🌤️")
st.header("¡Pregúntame sobre el clima de cualquier ciudad!")

# 🧠 Inicializar memoria de conversación
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []
if "ultima_ciudad" not in st.session_state:  # <-- Guarda la última ciudad mencionada
    st.session_state.ultima_ciudad = None

# Mostrar mensajes previos
for mensaje in st.session_state.mensajes:
    if mensaje["usuario"]:
        st.chat_message("user").write(mensaje["texto"])
    else:
        st.chat_message("assistant").write(mensaje["texto"])

# Input de usuario
entrada = st.chat_input("Escribe algo...")
if entrada:
    st.session_state.mensajes.append({"usuario": True, "texto": entrada})
    with st.chat_message("user"):
        st.write(entrada)

    with st.chat_message("assistant"):
        # 💬 Pasamos la memoria (última ciudad) al asistente
        respuesta, ciudad_detectada = procesar_mensaje(
            entrada, st.session_state.get("ultima_ciudad")
        )

        # 🧠 Guardamos la última ciudad si se detectó una nueva
        if ciudad_detectada:
            st.session_state.ultima_ciudad = ciudad_detectada

        # 💾 Guardamos el mensaje en el historial
        st.session_state.mensajes.append({"usuario": False, "texto": respuesta})

        # 🗨️ Mostramos la respuesta
        st.write(respuesta)
