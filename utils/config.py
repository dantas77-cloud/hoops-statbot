import os
import streamlit as st


def flag(nome, padrao="0"):
    """Lê uma opção liga/desliga de st.secrets ou variável de ambiente."""
    try:
        valor = st.secrets[nome]
    except Exception:
        valor = os.getenv(nome, padrao)
    return str(valor).strip().lower() in ("1", "true", "sim", "yes")
