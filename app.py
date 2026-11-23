import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from services.nba_service import buscar_jogador_por_nome, buscar_stats_carreira_jogador, buscar_premios_jogador, construir_contexto_nba
from services.llm_service import stream_resposta_chat, gerar_veredito_comparacao, reescrever_pergunta
from services import conversas
from services.knowledge import construir_contexto, dados_prontos, entidades_visuais, _csv
from utils.texto import limpar
from utils.logos import logo_url, foto_url, times_do_jogador, IMAGENS_ATIVAS
from utils.theme import card_jogador

st.set_page_config(page_title="Hoops StatBot", page_icon="🏀", layout="wide")
st.markdown("""<style>
.block-container{max-width:1100px;padding-top:2rem}
[data-testid="stChatMessage"]{background:#1E2329;border:1px solid #2b323b;border-radius:14px;padding:.8rem 1rem}
.stButton>button{border-radius:12px;border:1px solid #2b323b}
.stButton>button:hover{border-color:#E56020;color:#E56020}
</style>""", unsafe_allow_html=True)
from utils.theme import aplicar_tema
aplicar_tema()

from utils.theme import cabecalho

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conv_id" not in st.session_state:
    st.session_state.conv_id = conversas.novo_id()
if "ctx_anterior" not in st.session_state:
    st.session_state.ctx_anterior = ""


def _nova():
    st.session_state.ctx_anterior = ""
    st.session_state.messages = []
    st.session_state.conv_id = conversas.novo_id()
    st.session_state.pagina = "💬 Chat Central"


def _abrir(cid, msgs):
    st.session_state.ctx_anterior = ""
    st.session_state.conv_id = cid
    st.session_state.messages = msgs
    st.session_state.pagina = "💬 Chat Central"


def _apagar(cid):
    conversas.apagar(cid)
    if cid == st.session_state.conv_id:
        st.session_state.messages = []
        st.session_state.conv_id = conversas.novo_id()


with st.sidebar:
    if IMAGENS_ATIVAS:
        st.image("https://cdn.nba.com/logos/nba/nba-logoman-word-white.svg", width=150)
    else:
        st.markdown('<div class="marca"><span>🏀</span><span class="marca-t">Hoops StatBot</span></div>', unsafe_allow_html=True)
    st.write("")
    pagina = st.radio("Navegação", ["💬 Chat Central", "🗓️ Explorador de Temporadas", "🏆 Rankings", "📈 Líderes", "📊 Comparador Avançado"],
                      key="pagina", label_visibility="collapsed")
    st.divider()
    st.button("➕ Nova conversa", on_click=_nova, width="stretch", key="nova_conv")
    hist = conversas.carregar()
    if hist:
        st.caption("CONVERSAS ANTERIORES")
    for cid, c in sorted(hist.items(), key=lambda x: -x[1]["atualizado"])[:25]:
        col_a, col_b = st.columns([5, 1])
        ativa = "● " if cid == st.session_state.conv_id else ""
        col_a.button(ativa + c["titulo"], key=f"c_{cid}", on_click=_abrir, args=(cid, c["messages"]), width="stretch")
        col_b.button("🗑️", key=f"d_{cid}", on_click=_apagar, args=(cid,))
    st.divider()
    detalhado = st.toggle("Respostas detalhadas", value=True)
    st.caption("Dados: NBA API · IA: Groq · Projeto educacional, sem vínculo com a NBA")

if pagina == "💬 Chat Central":
    cabecalho("🏀", "Hoops StatBot", "Pergunte do seu jeito: fatos com dados oficiais e debates com opinião e argumentos")
    if not dados_prontos():
        st.warning("Base local não encontrada. Rode `python scripts/build_data.py` uma vez para habilitar All-NBA, DPOY, campeões e times por ano.")

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "🤖"):
            st.markdown(limpar(m["content"]))

    escolhida = None
    if not st.session_state.messages:
        st.markdown('<div class="boasvindas">Escolha uma pergunta para começar ou escreva do seu jeito, até com gírias e abreviações (KD, Bron, MJ...).</div>',
                    unsafe_allow_html=True)
        grupos = {"📜 Fatos e história": ["Quem foram os times All-NBA de 2016?", "Quem foi MVP em 2005?", "Melhores defesas dos anos 2000"],
                  "🔥 Debates": ["LeBron ou Jordan: quem é o GOAT?", "Top 5 armadores da história", "Melhor jogador do Lakers na história"],
                  "👤 Jogadores": ["Quantos títulos o KD ganhou nos anos 2010?", "Dados do Curry nos anos 2010", "Trajetória mais difícil até um título"]}
        for col, (tit, qs) in zip(st.columns(3), grupos.items()):
            with col:
                st.markdown(f'<div class="grupo-t">{tit}</div>', unsafe_allow_html=True)
                for i, q in enumerate(qs):
                    if st.button(q, key=f"sug_{tit}_{i}", width="stretch"):
                        escolhida = q
    elif st.session_state.messages[-1]["role"] == "assistant":
        st.caption("Continue a conversa:")
        for col, q in zip(st.columns(3), ["Resuma em poucas linhas", "Explique melhor os critérios", "E se fosse nos playoffs?"]):
            if col.button(q, key=f"seg_{len(st.session_state.messages)}_{q}", width="stretch"):
                escolhida = q

    prompt = st.chat_input("Pergunte qualquer coisa sobre a NBA...") or escolhida
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Entendendo a pergunta e consultando a base..."):
                reescrita = reescrever_pergunta(prompt, st.session_state.messages)
                igual = reescrita.strip().lower() == prompt.strip().lower()
                texto = prompt if igual else f"{reescrita} | {prompt}"
                try:
                    contexto, modo = construir_contexto(texto, st.session_state.ctx_anterior)
                except Exception as e:
                    contexto, modo = f"SEM DADOS ESPECÍFICOS (erro ao consultar a base: {e}).", "fato"
            if not igual:
                st.caption(f"🔎 Entendi: {reescrita}")
            ps_, ts_ = entidades_visuais(texto)
            itens = [(foto_url(p["id"]), p["full_name"]) for p in ps_] + [(logo_url(t["id"]), t["full_name"]) for t in ts_]
            if itens and IMAGENS_ATIVAS:
                for col, (u, nm) in zip(st.columns(max(len(itens), 4)), itens):
                    col.image(u, width=90, caption=nm)
            ph = st.empty()
            ph.markdown('<span class="pensando">Pensando<i>.</i><i>.</i><i>.</i></span>', unsafe_allow_html=True)
            acc = ""
            for pedaco in stream_resposta_chat(reescrita, contexto, modo, st.session_state.messages, detalhado):
                acc += pedaco
                ph.markdown(limpar(acc) + " ▌")
            resposta = limpar(acc).strip() or "Não consegui gerar uma resposta agora. Tente reformular a pergunta ou aguarde alguns segundos."
            ph.markdown(resposta)
            with st.expander("Dados usados na resposta"):
                st.code(contexto[:8000])
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.session_state.ctx_anterior = contexto[:5000]
        conversas.salvar(st.session_state.conv_id, st.session_state.messages)
        st.rerun()

elif pagina == "🗓️ Explorador de Temporadas":
    from components.explorer import render as render_explorer
    render_explorer()

elif pagina == "🏆 Rankings":
    from components.rankings import render as render_rankings
    render_rankings()

elif pagina == "📈 Líderes":
    from components.leaders import render as render_leaders
    render_leaders()

elif pagina == "📊 Comparador Avançado":
    st.title("📊 Análise Head-to-Head Profunda")
    
    col1, col2 = st.columns(2)
    with col1:
        jogador1 = st.text_input("Jogador 1", placeholder="Ex: Stephen Curry")
    with col2:
        jogador2 = st.text_input("Jogador 2", placeholder="Ex: Magic Johnson")
        
    if st.button("Executar Análise Estatística", type="primary", width="stretch"):
        if jogador1 and jogador2:
            p1_info = buscar_jogador_por_nome(jogador1)
            p2_info = buscar_jogador_por_nome(jogador2)
            
            if p1_info and p2_info:
                with st.spinner("Processando histórico completo e gerando veredito..."):
                    m1, h1 = buscar_stats_carreira_jogador(p1_info['id'])
                    m2, h2 = buscar_stats_carreira_jogador(p2_info['id'])
                    
                    p1_premios = buscar_premios_jogador(p1_info['id'])
                    p2_premios = buscar_premios_jogador(p2_info['id'])
                    
                    if m1 and m2:
                        _pts = _csv("player_team_seasons.csv")
                        cj1, cj2 = st.columns(2)
                        cj1.markdown(card_jogador(p1_info["full_name"], p1_info["id"], times_do_jogador(p1_info["id"], _pts, h1), "#E56020"), unsafe_allow_html=True)
                        cj2.markdown(card_jogador(p2_info["full_name"], p2_info["id"], times_do_jogador(p2_info["id"], _pts, h2), "#1D428A"), unsafe_allow_html=True)
                        st.subheader("Radar de Perfil de Jogo")
                        categorias = ['PTS', 'AST', 'REB', 'STL', 'BLK', 'FG%']
                        fig = go.Figure()

                        fg_radar_1 = m1['FG_PCT'] / 2 
                        fg_radar_2 = m2['FG_PCT'] / 2

                        fig.add_trace(go.Scatterpolar(
                            r=[m1['PTS'], m1['AST'], m1['REB'], m1['STL']*5, m1['BLK']*5, fg_radar_1],
                            theta=categorias, fill='toself', name=p1_info['full_name'],
                            line_color='#E56020'
                        ))
                        fig.add_trace(go.Scatterpolar(
                            r=[m2['PTS'], m2['AST'], m2['REB'], m2['STL']*5, m2['BLK']*5, fg_radar_2],
                            theta=categorias, fill='toself', name=p2_info['full_name'],
                            line_color='#1D428A'
                        ))

                        fig.update_layout(
                            polar=dict(radialaxis=dict(visible=False)),
                            showlegend=True,
                            paper_bgcolor='rgba(0,0,0,0)',
                            plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='white')
                        )
                        st.plotly_chart(fig, width="stretch")
                        
                        st.subheader("Comparação de Eficiência e Volume")
                        c1, c2 = st.columns(2)
                        
                        with c1:
                            st.markdown(f"### 🔵 {p1_info['full_name']}")
                            col_a, col_b, col_c = st.columns(3)
                            col_a.metric("Pontos", m1['PTS'])
                            col_b.metric("Rebotes", m1['REB'])
                            col_c.metric("Assist.", m1['AST'])
                            
                        with c2:
                            st.markdown(f"### 🔴 {p2_info['full_name']}")
                            col_x, col_y, col_z = st.columns(3)
                            col_x.metric("Pontos", m2['PTS'], delta=round(m2['PTS']-m1['PTS'], 1))
                            col_y.metric("Rebotes", m2['REB'], delta=round(m2['REB']-m1['REB'], 1))
                            col_z.metric("Assist.", m2['AST'], delta=round(m2['AST']-m1['AST'], 1))

                        st.write("### ⭐ Melhor Temporada da Carreira (Maior Impacto Médio)")
                        df_melhor_temp = pd.DataFrame([
                            {"Atleta": p1_info['full_name'], "Temporada de Maior Impacto (PTS+REB+AST)": m1.get('Melhor_Temporada', 'N/A')},
                            {"Atleta": p2_info['full_name'], "Temporada de Maior Impacto (PTS+REB+AST)": m2.get('Melhor_Temporada', 'N/A')}
                        ])
                        st.dataframe(df_melhor_temp, width="stretch", hide_index=True)

                        st.write("### 🏆 Sala de Troféus (Conquistas da Carreira)")
                        df_premios = pd.DataFrame([
                            {"Atleta": p1_info['full_name'], "Anéis (Títulos)": p1_premios['Campeonatos_Qtd'], "MVP": p1_premios['MVP_Qtd'], "Finals MVP": p1_premios['FMVP_Qtd'], "All-NBA": p1_premios['All-NBA_Qtd'], "All-Star": p1_premios['All-Star_Qtd']},
                            {"Atleta": p2_info['full_name'], "Anéis (Títulos)": p2_premios['Campeonatos_Qtd'], "MVP": p2_premios['MVP_Qtd'], "Finals MVP": p2_premios['FMVP_Qtd'], "All-NBA": p2_premios['All-NBA_Qtd'], "All-Star": p2_premios['All-Star_Qtd']}
                        ])
                        st.dataframe(df_premios, width="stretch", hide_index=True)

                        st.write("### Tabela Detalhada de Estatísticas")
                        df_comp = pd.DataFrame([
                            {"Atleta": p1_info['full_name'], "Jogos": m1['Jogos'], "PTS": m1['PTS'], "AST": m1['AST'], "REB": m1['REB'], "STL": m1['STL'], "BLK": m1['BLK'], "FG%": f"{m1['FG_PCT']}%", "3P%": f"{m1['FG3_PCT']}%", "FT%": f"{m1['FT_PCT']}%"},
                            {"Atleta": p2_info['full_name'], "Jogos": m2['Jogos'], "PTS": m2['PTS'], "AST": m2['AST'], "REB": m2['REB'], "STL": m2['STL'], "BLK": m2['BLK'], "FG%": f"{m2['FG_PCT']}%", "3P%": f"{m2['FG3_PCT']}%", "FT%": f"{m2['FT_PCT']}%"}
                        ])
                        st.dataframe(df_comp, width="stretch", hide_index=True)

                        st.divider()
                        st.write("### 🤖 Veredito Final da IA")
                        
                        dados_p1 = {"nome": p1_info['full_name'], "premios": p1_premios, "medias": m1}
                        dados_p2 = {"nome": p2_info['full_name'], "premios": p2_premios, "medias": m2}
                        
                        veredito = gerar_veredito_comparacao(dados_p1, dados_p2)
                        st.info(veredito)
            else:
                st.error("Jogadores não encontrados. Verifique a ortografia.")
