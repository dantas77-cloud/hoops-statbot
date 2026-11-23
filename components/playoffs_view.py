import streamlit as st
from services.nba_service import buscar_playoffs_historico_jogador, buscar_jogos_playoffs_por_ano
from utils.charts import criar_grafico_evolucao_playoffs


def renderizar_painel_playoffs(nome_jogador: str):
    st.subheader(f"🏆 Histórico de Playoffs: {nome_jogador}")

    with st.spinner(f"Consultando dados de playoffs de {nome_jogador}..."):
        df_historico = buscar_playoffs_historico_jogador(nome_jogador)

    if df_historico.empty:
        st.warning(f"Nenhum registro de playoffs encontrado para {nome_jogador}.")
        return

    fig = criar_grafico_evolucao_playoffs(df_historico, nome_jogador)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### 📊 Médias por Temporada de Playoffs")
    st.dataframe(df_historico, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### 🔍 Detalhar Jogo a Jogo de uma Pós-Temporada")

    temporadas = df_historico['SEASON_ID'].tolist()
    temp_sel = st.selectbox("Selecione o ano do playoff:", options=temporadas)

    if temp_sel:
        df_jogos = buscar_jogos_playoffs_por_ano(nome_jogador, temp_sel)
        if not df_jogos.empty:
            st.dataframe(df_jogos, use_container_width=True, hide_index=True)
        else:
            st.info("Não foi possível carregar os jogos desta temporada.")