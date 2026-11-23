import json, os, time, uuid
import streamlit as st

CAMINHO = os.path.join(os.path.dirname(__file__), "..", "data", "conversas.json")
# NBA_HISTORICO=0 guarda as conversas só na sessão do navegador (use ao publicar o app, para visitantes não verem conversas uns dos outros)
PERSISTENTE = os.getenv("NBA_HISTORICO", "1") != "0"


def carregar():
    if not PERSISTENTE:
        return st.session_state.setdefault("_hist", {})
    try:
        with open(CAMINHO, encoding="utf8") as f:
            return json.load(f)
    except Exception:
        return {}


def _gravar(d):
    if not PERSISTENTE:
        st.session_state["_hist"] = d
        return
    os.makedirs(os.path.dirname(CAMINHO), exist_ok=True)
    with open(CAMINHO, "w", encoding="utf8") as f:
        json.dump(d, f, ensure_ascii=False)


def salvar(cid, messages):
    if not messages:
        return
    d = carregar()
    titulo = next((m["content"] for m in messages if m["role"] == "user"), "Conversa")[:45]
    d[cid] = {"titulo": titulo, "atualizado": time.time(), "messages": messages}
    _gravar(d)


def apagar(cid):
    d = carregar()
    if d.pop(cid, None) is not None:
        _gravar(d)


def novo_id():
    return uuid.uuid4().hex[:8]
