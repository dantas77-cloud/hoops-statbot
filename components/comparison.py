import streamlit as st
from utils.charts import criar_grafico_comparativo_barras, criar_grafico_eficiencia, criar_grafico_radar_habilidades
from services.llm_service import enviar_mensagem_com_historico


def exibir_quadro_palmares_html(p1: str, pal1: dict, p2: str, pal2: dict):
    """Renderiza a tabela comparativa em HTML sem espaços iniciais para evitar o bloco de código."""
    categorias = [
        ("🏆 Títulos da NBA", "titulos"),
        ("🥇 MVPs da Temporada", "mvp"),
        ("🌟 MVPs das Finais", "fmvp"),
        ("👑 All-NBA First Team", "all_nba_1st"),
        ("⭐ All-Star Games", "all_star"),
        ("🛡️ Defensor do Ano (DPOY)", "dpoy"),
        ("🎯 Títulos de Cestinha", "cestinha")
    ]

    linhas_html = ""
    for label, key in categorias:
        v1 = pal1.get(key, 0)
        v2 = pal2.get(key, 0)

        c1_style = "color: #2ea44f; font-weight: bold;" if v1 > v2 else "color: #e6edf3;"
        c2_style = "color: #2ea44f; font-weight: bold;" if v2 > v1 else "color: #e6edf3;"

        v1_display = f"🟢 {v1}" if v1 > v2 else f"{v1}"
        v2_display = f"{v2} 🟢" if v2 > v1 else f"{v2}"

        linhas_html += f'<tr style="border-bottom: 1px solid #21262d;"><td style="padding: 12px; text-align: center; font-size: 16px; {c1_style}">{v1_display}</td><td style="padding: 12px; text-align: center; font-size: 14px; color: #8b949e; font-weight: 600;">{label}</td><td style="padding: 12px; text-align: center; font-size: 16px; {c2_style}">{v2_display}</td></tr>'

    tabela_html = f'<div style="background-color: #121721; border: 1px solid #30363d; border-radius: 12px; padding: 16px; margin-bottom: 24px;"><h3 style="text-align: center; color: #ffffff; margin-bottom: 16px;">🏆 Galeria de Títulos e Prêmios</h3><table style="width: 100%; border-collapse: collapse;"><thead><tr style="border-bottom: 2px solid #30363d; background-color: #161b22;"><th style="padding: 12px; text-align: center; color: #F58426; font-size: 18px; width: 35%;">{p1}</th><th style="padding: 12px; text-align: center; color: #8b949e; font-size: 13px; width: 30%;">CATEGORIA</th><th style="padding: 12px; text-align: center; color: #F58426; font-size: 18px; width: 35%;">{p2}</th></tr></thead><tbody>{linhas_html}</tbody></table></div>'

    st.markdown(tabela_html, unsafe_allow_html=True)


def exibe_cards_jogador(nome: str, stats: dict):
    st.markdown(f"### {nome}")
    st.caption(f"Jogos Disputados: {stats.get('Jogos', 0)}")

    c1, c2, c3 = st.columns(3)
    c1.metric("PPG", stats.get('PPG', 0))
    c2.metric("RPG", stats.get('RPG', 0))
    c3.metric("APG", stats.get('APG', 0))

    c4, c5, c6 = st.columns(3)
    c4.metric("FG%", f"{stats.get('FG%', 0)}%")
    c5.metric("3P%", f"{stats.get('3P%', 0)}%")
    c6.metric("FT%", f"{stats.get('FT%', 0)}%")


def renderizar_comparacao_completa(nome1: str, reg1: dict, play1: dict, pal1: dict, nome2: str, reg2: dict, play2: dict,
                                   pal2: dict):
    st.divider()

    # 1. Tabela Limpa de Prêmios em HTML
    exibir_quadro_palmares_html(nome1, pal1, nome2, pal2)

    # 2. Seletor do Período
    tipo_dado = st.radio(
        "Selecione o período de análise estatística:",
        ["Temporada Regular", "Playoffs"],
        horizontal=True,
        key="radio_periodo_comparacao"
    )

    stats1 = reg1 if tipo_dado == "Temporada Regular" else play1
    stats2 = reg2 if tipo_dado == "Temporada Regular" else play2

    col1, col2 = st.columns(2)
    with col1:
        exibe_cards_jogador(nome1, stats1)
    with col2:
        exibe_cards_jogador(nome2, stats2)

    st.divider()

    # 3. Gráficos em Abas
    tab_radar, tab_volume, tab_eficiencia = st.tabs([
        "🕸️ Perfil Radar",
        "📊 Volume de Jogo",
        "🎯 Eficiência de Arremesso"
    ])

    with tab_radar:
        st.plotly_chart(criar_grafico_radar_habilidades(stats1, stats2, nome1, nome2), use_container_width=True)
    with tab_volume:
        st.plotly_chart(criar_grafico_comparativo_barras(stats1, stats2, nome1, nome2), use_container_width=True)
    with tab_eficiencia:
        st.plotly_chart(criar_grafico_eficiencia(stats1, stats2, nome1, nome2), use_container_width=True)

    # 4. Análise Tática da IA
    chave_analise = f"analise_{nome1}_{nome2}_{tipo_dado}"
    if chave_analise not in st.session_state:
        prompt_analise = f"""
        Faça um veredito comparativo entre {nome1} e {nome2} no período de ({tipo_dado}).

        Dados de {nome1}: {stats1.get('PPG')} PPG, {stats1.get('RPG')} RPG, {stats1.get('APG')} APG, {stats1.get('FG%')}% FG. Prêmios: {pal1}
        Dados de {nome2}: {stats2.get('PPG')} PPG, {stats2.get('RPG')} RPG, {stats2.get('APG')} APG, {stats2.get('FG%')}% FG. Prêmios: {pal2}

        Escreva um texto analítico em português destacando:
        1. Diferenças no estilo de jogo e volume de pontuação/eficiência.
        2. Impacto tático nas equipes em que jogaram.
        3. Peso das conquistas e troféus individuais no legado de cada um.
        """
        with st.spinner("Gerando análise tática da IA..."):
            st.session_state[chave_analise] = enviar_mensagem_com_historico(
                [{"role": "user", "content": prompt_analise}])

    st.markdown("### 📊 Veredito do Analista AI")
    st.markdown(st.session_state[chave_analise])