import streamlit as st
import plotly.express as px
from nba_api.stats.static import teams
from utils.theme import card, cabecalho
from utils.logos import logo_url, foto_url, IMAGENS_ATIVAS
from services.knowledge import _csv, dados_prontos, pontuar, caminhos_campeoes, _seasons_decada

POS = {"Todas": None, "Armador": "G", "Ala": "F", "Pivô": "C"}
DECADAS = list(range(1950, 2030, 10))
EST = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")


def _periodo(ts, chave):
    modo = st.radio("Período", ["Todos os tempos", "Década", "Temporada"], horizontal=True, key=chave + "m")
    if modo == "Década":
        return _seasons_decada(st.selectbox("Década", DECADAS[::-1], index=2, key=chave + "d"))
    if modo == "Temporada":
        return [st.selectbox("Temporada", sorted(ts.SEASON.unique(), reverse=True), key=chave + "s")]
    return None


def render():
    cabecalho("🏆", "Rankings", "Os maiores jogadores e times da história, por época, posição e franquia")
    if not dados_prontos():
        st.warning("Base local não encontrada. Rode `python scripts/build_data.py` uma vez.")
        return
    aw, ts, idx = _csv("awards.csv"), _csv("team_seasons.csv"), _csv("players_index.csv")
    pts, ps = _csv("player_team_seasons.csv"), _csv("playoff_series.csv")
    tj, tt, tc = st.tabs(["Jogadores", "Times", "Caminhos de título"])

    with tj:
        seasons = _periodo(ts, "j")
        c1, c2, c3 = st.columns(3)
        pos = POS[c1.selectbox("Posição", list(POS))]
        tms = {t["full_name"]: t["id"] for t in teams.get_teams()}
        time = c2.selectbox("Time (toda a história da franquia)", ["Todos"] + sorted(tms))
        n = c3.slider("Quantos mostrar", 5, 30, 15)
        tid = None if time == "Todos" else tms[time]
        if tid and pts is None:
            st.warning("Para filtrar por time, rode `python scripts/build_extra.py` uma vez.")
        df = pontuar(aw, idx, seasons, pos, tid, pts).head(n)
        if df.empty:
            st.info("Nenhum jogador encontrado com esses filtros.")
        else:
            if tid and IMAGENS_ATIVAS:
                st.markdown(f'<img src="{logo_url(tid)}" height="70">', unsafe_allow_html=True)
            pc = st.columns(3)
            for col, i, med, cl in [(pc[0], 1, "🥈", "prata"), (pc[1], 0, "🥇", "ouro"), (pc[2], 2, "🥉", "bronze")]:
                if i < len(df):
                    r = df.iloc[i]
                    col.markdown(card(f"{med} #{i + 1}", r.Jogador, f"{r.Pontos:.1f} pts · {int(r['MVP'])} MVP · {int(r['Títulos'])} títulos",
                                      "podio " + cl, f'<img src="{foto_url(r.ID)}" style="height:70px;border-radius:50%">' if IMAGENS_ATIVAS else ""), unsafe_allow_html=True)
            st.write("")
            fig = px.bar(df[::-1], x="Pontos", y="Jogador", orientation="h", color="Pontos", color_continuous_scale=["#1D428A", "#E56020"])
            fig.update_layout(height=max(350, 28 * len(df)), coloraxis_showscale=False, **EST)
            st.plotly_chart(fig, width="stretch")
            if IMAGENS_ATIVAS:
                df["Foto"] = df.ID.map(foto_url)
            cols = (["Foto"] if IMAGENS_ATIVAS else []) + ["Jogador", "Pontos", "MVP", "FMVP", "Títulos", "DPOY", "All-NBA", "All-Def", "All-Star"]
            cols += [c for c in ["Temporadas", "PTS", "REB", "AST"] if c in df]
            st.dataframe(df[cols], width="stretch", hide_index=True, column_config={"Foto": st.column_config.ImageColumn("", width="small")})
        st.caption("Pontos de legado: MVP×10, MVP das Finais×6, título×3, DPOY×3, All-NBA 1º/2º/3º = 4/2,5/1,5, All-Def×1, All-Star×0,5. "
                   "Ao filtrar por time, os prêmios contam só no time em que o jogador atuou naquela temporada, e somam-se 0,5 por temporada no time e 1 ponto a cada 2.000 pontos marcados nele.")

    with tt:
        seasons = _periodo(ts, "t")
        metrica = st.selectbox("Métrica", ["Net rating / saldo de pontos", "Melhor defesa", "Melhor ataque", "Vitórias"])
        n = st.slider("Quantos mostrar", 5, 30, 15, key="nt")
        d = ts[ts.SEASON.isin(seasons)].copy() if seasons else ts.copy()
        d["SALDO"] = d.NRTG.fillna(d.DIFF)
        col, asc = {"Net rating / saldo de pontos": ("SALDO", False), "Melhor defesa": ("DRTG", True),
                    "Melhor ataque": ("ORTG", False), "Vitórias": ("W", False)}[metrica]
        d = d.dropna(subset=[col]).sort_values(col, ascending=asc).head(n)
        d["Time/Temporada"] = d.SEASON + " " + d.TEAM
        fig = px.bar(d[::-1], x=col, y="Time/Temporada", orientation="h", color=col, color_continuous_scale=["#1D428A", "#E56020"])
        fig.update_layout(height=max(350, 28 * len(d)), coloraxis_showscale=False, **EST)
        st.plotly_chart(fig, width="stretch")
        cols = ["SEASON", "TEAM", "W", "L", "PPG", "OPP_PPG", "ORTG", "DRTG", "NRTG"]
        if "TEAM_ID" in d and IMAGENS_ATIVAS:
            d["Logo"] = d.TEAM_ID.map(lambda t: logo_url(t) if t == t else None)
            cols = ["Logo"] + cols
        st.dataframe(d[cols], width="stretch", hide_index=True, column_config={"Logo": st.column_config.ImageColumn("", width="small")})
        st.caption("Ataque, defesa e net rating só existem desde 1996-97; antes disso a comparação usa o saldo de pontos por jogo.")

    with tc:
        if ps is None or "TEAM_ID" not in ts.columns:
            st.info("Rode `python scripts/build_extra.py` uma vez para habilitar esta aba.")
        else:
            seasons = _periodo(ts, "c")
            ordem = st.radio("Ordenar por", ["Mais difíceis", "Mais fáceis"], horizontal=True)
            cc = caminhos_campeoes(aw, ts, ps)
            if seasons:
                cc = cc[cc.Temporada.isin(seasons)]
            cc = cc.sort_values("Saldo médio adv.", ascending=(ordem == "Mais fáceis")).head(20)
            cc["Time/Temporada"] = cc.Temporada + " " + cc["Campeão"]
            fig = px.bar(cc[::-1], x="Saldo médio adv.", y="Time/Temporada", orientation="h", color="Saldo médio adv.",
                         color_continuous_scale=["#1D428A", "#E56020"])
            fig.update_layout(height=max(350, 28 * len(cc)), coloraxis_showscale=False, **EST)
            st.plotly_chart(fig, width="stretch")
            st.dataframe(cc[["Temporada", "Campeão", "Win% médio adv.", "Saldo médio adv.", "Caminho"]].round(1), width="stretch", hide_index=True)
            st.caption("Dificuldade = força média dos adversários na temporada regular (saldo de pontos ou net rating e % de vitórias). É uma aproximação: não considera mando de quadra nem lesões.")
