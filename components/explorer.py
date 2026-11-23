import streamlit as st
import pandas as pd
import plotly.express as px
from services.knowledge import _csv, _awd, dados_prontos, caminho
from utils.theme import card, chips, cabecalho
from utils.logos import logo_url, IMAGENS_ATIVAS


def _conf(x):
    x = str(x)
    return "Leste" if x.startswith("E") else "Oeste" if x.startswith("W") else None


def render():
    cabecalho("🗓️", "Explorador de Temporadas", "Campeões, prêmios, classificação e o caminho de cada título, ano a ano")
    if not dados_prontos():
        st.warning("Base local não encontrada. Rode `python scripts/build_data.py` uma vez.")
        return
    aw, ts = _csv("awards.csv"), _csv("team_seasons.csv")
    pts, ps = _csv("player_team_seasons.csv"), _csv("playoff_series.csv")
    tem_id = "TEAM_ID" in ts.columns
    seasons = sorted(ts.SEASON.unique())
    if "sel_temp" not in st.session_state:
        st.session_state.sel_temp = seasons[-1]

    def _mv(d):
        i = seasons.index(st.session_state.sel_temp) + d
        st.session_state.sel_temp = seasons[max(0, min(len(seasons) - 1, i))]

    c1, c2, c3 = st.columns([1, 10, 1])
    c1.button("◀", on_click=_mv, args=(-1,), key="prev_t")
    c3.button("▶", on_click=_mv, args=(1,), key="next_t")
    s = c2.select_slider("Temporada", options=seasons, key="sel_temp")
    d = ts[ts.SEASON == s].copy()

    def nomes(k):
        x = _awd(aw, k, [s])
        return ", ".join(x.PLAYER.unique()) or "—"

    camp = _awd(aw, "campeao", [s])
    nome_c = camp.TEAM.mode().iat[0] if len(camp) else None
    img = ""
    if IMAGENS_ATIVAS and tem_id and nome_c in set(d.TEAM) and pd.notna(d[d.TEAM == nome_c].TEAM_ID.iat[0]):
        img = f'<img src="{logo_url(d[d.TEAM == nome_c].TEAM_ID.iat[0])}">'
    c = st.columns(4)
    c[0].markdown(card("🏆 Campeão", nome_c or "—", s, "ouro", img), unsafe_allow_html=True)
    c[1].markdown(card("MVP da temporada", nomes("mvp"), s), unsafe_allow_html=True)
    c[2].markdown(card("Defensor do Ano", nomes("dpoy"), s), unsafe_allow_html=True)
    c[3].markdown(card("Calouro do Ano", nomes("roy"), s), unsafe_allow_html=True)
    st.write("")

    t1, t2, t3, t4 = st.tabs(["Times do ano e prêmios", "Classificação", "Ataque × Defesa", "Caminho do título"])
    with t1:
        a, b = st.columns(2)
        for col, k, titulo in [(a, "allnba", "All-NBA"), (b, "alldef", "All-Defensive")]:
            x = _awd(aw, k, [s])
            with col:
                st.subheader(titulo)
                if x.empty:
                    st.caption("Sem dados para esta temporada.")
                for n, g in x.groupby("ALL_NBA_TEAM_NUMBER"):
                    st.markdown(f"**{int(n)}º time**")
                    st.markdown(chips(g.PLAYER), unsafe_allow_html=True)
        st.subheader("All-Stars")
        asr = _awd(aw, "allstar", [s]).copy()
        asr["C"] = None
        if pts is not None and tem_id and "CONF" in d:
            base = pts[pts.SEASON == s].sort_values("GP", ascending=False).drop_duplicates("PERSON_ID")
            base = {int(p): int(t) for p, t in zip(base.PERSON_ID, base.TEAM_ID)}
            conf = {int(t): _conf(cf) for t, cf in zip(d.TEAM_ID, d.CONF) if pd.notna(t)}
            asr["C"] = asr.PERSON_ID.map(lambda p: conf.get(base.get(int(p))))
        if asr.empty:
            st.caption("Sem dados para esta temporada.")
        grupos = [("Leste", "Leste"), ("Oeste", "Oeste"), (None, "Conferência não identificada")]
        if asr.C.notna().any():
            cols = st.columns(2)
            for col, (cf, tit) in zip(cols, grupos[:2]):
                with col:
                    st.markdown(f"**{tit}** ({(asr.C == cf).sum()})")
                    st.markdown(chips(asr[asr.C == cf].PLAYER), unsafe_allow_html=True)
            sem = asr[asr.C.isna()]
            if len(sem):
                with st.expander(f"Conferência não identificada ({len(sem)})"):
                    st.markdown(chips(sem.PLAYER), unsafe_allow_html=True)
        elif len(asr):
            st.markdown(chips(asr.PLAYER), unsafe_allow_html=True)
            st.caption("Rode `python scripts/build_extra.py` para separar por conferência.")
        st.subheader("Prêmios dos playoffs")
        st.markdown(f"**MVP das Finais da NBA:** {nomes('fmvp')}")
        cf = _awd(aw, "cfmvp", [s])
        for tag, nome in [("East", "Leste"), ("West", "Oeste")]:
            x = cf[cf.DESCRIPTION.str.contains(tag, case=False)]
            st.markdown(f"**MVP das Finais da Conferência {nome}:** {', '.join(x.PLAYER.unique()) or '—'}")
        st.subheader("Outros prêmios")
        for k, nome in [("6man", "Sexto Homem"), ("mip", "Jogador que Mais Evoluiu")]:
            st.markdown(f"**{nome}:** {nomes(k)}")

    with t2:
        d["Aproveit. %"] = (d.W / (d.W + d.L) * 100).round(1)
        d["Conf."] = d.CONF.map(_conf) if "CONF" in d else None
        if tem_id and IMAGENS_ATIVAS:
            d["Logo"] = d.TEAM_ID.map(lambda t: logo_url(t) if pd.notna(t) else None)
        cols = [c for c in ["Logo", "TEAM", "Conf.", "W", "L", "Aproveit. %", "PPG", "OPP_PPG", "DIFF", "ORTG", "DRTG", "NRTG"] if c in d]
        cfg = {"Logo": st.column_config.ImageColumn("", width="small")}

        def tabela(x):
            st.dataframe(x.sort_values("W", ascending=False)[cols].rename(columns={"TEAM": "Time", "W": "V", "L": "D"}),
                         width="stretch", hide_index=True, column_config=cfg)
        a, b, c_ = st.tabs(["Geral", "Leste", "Oeste"])
        with a:
            tabela(d)
        for tab, nome in [(b, "Leste"), (c_, "Oeste")]:
            with tab:
                x = d[d["Conf."] == nome]
                tabela(x) if len(x) else st.caption("Conferência não disponível para esta temporada.")

    with t3:
        if d.ORTG.notna().any():
            fig = px.scatter(d, x="DRTG", y="ORTG", text="TEAM", color="NRTG", color_continuous_scale="RdYlGn",
                             labels={"DRTG": "Defesa (menor = melhor)", "ORTG": "Ataque"})
        else:
            st.info("Net rating só existe a partir de 1996-97; mostrando pontos por jogo.")
            fig = px.scatter(d, x="OPP_PPG", y="PPG", text="TEAM", color="DIFF", color_continuous_scale="RdYlGn")
        fig.update_xaxes(autorange="reversed")
        fig.update_traces(textposition="top center")
        fig.update_layout(height=600, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, width="stretch")

    with t4:
        if ps is None or not tem_id:
            st.info("Rode `python scripts/build_extra.py` para habilitar o caminho do título.")
        else:
            cm = caminho(aw, ts, ps, s)
            if not cm:
                st.caption("Sem dados de playoffs para esta temporada.")
            for i, x in enumerate(cm, 1):
                a, b = st.columns([1, 6])
                if IMAGENS_ATIVAS:
                    a.image(logo_url(x["adv_id"]), width=60)
                pct = f"{x['pct'] * 100:.0f}% de vitórias" if x["pct"] == x["pct"] else "sem dados"
                b.markdown(f"**Série {i}: {nome_c} {x['res']} {x['adv']}**  \n{pct} na temporada regular")
            ok = [x for x in cm if x["pct"] == x["pct"]]
            if ok:
                st.metric("Força média dos adversários (vitórias na temporada)", f"{sum(x['pct'] for x in ok) / len(ok) * 100:.0f}%")
