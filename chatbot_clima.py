import streamlit as st
from src.clima import obtener_clima

st.set_page_config(page_title="Chatbot del Clima 🌤️", page_icon="⛅")

st.title("Chatbot del Clima 🌤️")
st.header("¡Pregúntame sobre el clima de cualquier ciudad!")

# Contenedor de chat
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mostrar mensajes anteriores
for mensaje in st.session_state.mensajes:
    if mensaje["usuario"]:
        st.chat_message("user").write(mensaje["texto"])
    else:
        st.chat_message("assistant").write(mensaje["texto"])

# Input de usuario
entrada = st.chat_input("Escribe tu pregunta sobre el clima...")
if entrada:
    st.session_state.mensajes.append({"usuario": True, "texto": entrada})

    # Aquí detectamos si el usuario mencionó una ciudad
    ciudad = entrada.strip()  # Podrías mejorar con NLP o regex
    # Por simplicidad, asumimos que el usuario escribe el nombre exacto de la ciudad
    respuesta = obtener_clima(ciudad)
    
    st.session_state.mensajes.append({"usuario": False, "texto": respuesta})
    st.chat_message("assistant").write(respuesta)
