import streamlit as st
import plotly.express as px
from services.knowledge import _csv
from utils.logos import foto_url, logo_url, IMAGENS_ATIVAS
from utils.theme import cabecalho

M = {"Pontos": "PTS", "Rebotes": "REB", "Assistências": "AST", "Roubos de bola": "STL", "Tocos": "BLK"}
POR_JOGO = {"PTS": "PPG", "REB": "RPG", "AST": "APG", "STL": "SPG", "BLK": "BPG"}


def _time_mais_recente(d):
    x = d.sort_values(["SEASON", "GP"]).drop_duplicates("PERSON_ID", keep="last")
    return {int(p): int(t) for p, t in zip(x.PERSON_ID, x.TEAM_ID) if t == t}


def render():
    cabecalho("📈", "Líderes Estatísticos", "Pontos, rebotes, assistências, roubos e tocos: por temporada ou na carreira")
    pts = _csv("player_team_seasons.csv")
    if pts is None:
        st.warning("Rode `python scripts/build_extra.py` uma vez para habilitar esta aba.")
        return
    modo = st.radio("Visão", ["Por temporada (média por jogo)", "Carreira (total)"], horizontal=True)
    met = M[st.selectbox("Estatística", list(M))]
    n = st.slider("Quantos mostrar", 5, 25, 10)
    d = pts.dropna(subset=[met])
    por_jogo = modo.startswith("Por")
    if por_jogo:
        s = st.selectbox("Temporada", sorted(pts.SEASON.unique(), reverse=True))
        base = d[d.SEASON == s]
        g = base.groupby(["PERSON_ID", "PLAYER_NAME"], as_index=False).agg(GP=("GP", "sum"), T=(met, "sum"))
        g = g[g.GP >= 0.6 * g.GP.max()]
        g["Valor"] = (g["T"] / g.GP).round(1)
        unidade = POR_JOGO[met]
        g["Resultado"] = g.Valor.map(lambda v: f"{v:.1f} {unidade}")
    else:
        base = d
        g = d.groupby(["PERSON_ID", "PLAYER_NAME"], as_index=False).agg(GP=("GP", "sum"), T=(met, "sum"))
        g["Valor"] = g["T"].astype(int)
        unidade = met
        g["Resultado"] = g.Valor.map(lambda v: f"{v:,}".replace(",", ".") + f" {unidade}")
    g = g.sort_values("Valor", ascending=False).head(n)
    time_de = _time_mais_recente(base)
    cols_img = ["Foto", "Time"] if IMAGENS_ATIVAS else []
    if IMAGENS_ATIVAS:
        g["Foto"] = g.PERSON_ID.map(foto_url)
        g["Time"] = g.PERSON_ID.map(lambda p: logo_url(time_de[int(p)]) if int(p) in time_de else None)
    else:  # modo neutro: sigla do time em texto, sem logo
        x = base.sort_values(["SEASON", "GP"]).drop_duplicates("PERSON_ID", keep="last")
        sigla = dict(zip(x.PERSON_ID, x.TEAM_ABBREVIATION))
        g["Time"] = g.PERSON_ID.map(lambda p: sigla.get(p, ""))
        cols_img = ["Time"]
    fig = px.bar(g[::-1], x="Valor", y="PLAYER_NAME", orientation="h", color="Valor", text="Resultado",
                 color_continuous_scale=["#1D428A", "#E56020"], labels={"Valor": unidade, "PLAYER_NAME": ""})
    fig.update_traces(textposition="outside")
    if len(g):
        fig.update_xaxes(range=[0, float(g.Valor.max()) * 1.2])  # folga para o rótulo não ser cortado
    fig.update_layout(height=max(350, 34 * len(g)), coloraxis_showscale=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")
    tab = g[cols_img + ["PLAYER_NAME", "GP", "Resultado"]].rename(columns={"PLAYER_NAME": "Jogador", "GP": "Jogos", "Resultado": unidade})
    cfg = {"Foto": st.column_config.ImageColumn("", width="small"), "Time": st.column_config.ImageColumn("Time", width="small")} if IMAGENS_ATIVAS else {}
    st.dataframe(tab, width="stretch", hide_index=True, column_config=cfg)
    nota = "O logo mostra o time do jogador naquela temporada (na visão de carreira, o time mais recente). " if IMAGENS_ATIVAS else \
        "A sigla mostra o time do jogador naquela temporada (na visão de carreira, o time mais recente). "
    st.caption(nota + "Considera os jogadores da base de premiados. Tocos e roubos só existem desde 1973-74. "
               "Na visão por temporada, exige-se ao menos 60% dos jogos do maior número de partidas.")
