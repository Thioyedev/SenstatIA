import os

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")


def render_chat():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_citations" not in st.session_state:
        st.session_state.last_citations = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Posez votre question sur les statistiques du Sénégal..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Recherche dans les sources officielles..."):
                try:
                    response = httpx.post(
                        f"{API_URL}/query",
                        json={"query": prompt},
                        timeout=60.0,
                    )
                    response.raise_for_status()
                    data = response.json()
                    answer = data["answer"]
                    st.session_state.last_citations = data.get("citations", [])
                except Exception as e:
                    answer = f"Erreur : {e}"
                    st.session_state.last_citations = []

            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
