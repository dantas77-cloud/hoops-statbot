import streamlit as st
import pandas as pd
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import playercareerstats, teamyearbyyearstats, playerawards


@st.cache_data(ttl=86400)
def buscar_jogador_por_nome(nome: str):
    nba_players = players.get_players()
    encontrados = [p for p in nba_players if nome.lower() in p['full_name'].lower()]
    return encontrados[0] if encontrados else None


@st.cache_data(ttl=86400)
def buscar_time_por_nome(nome: str):
    nba_teams = teams.get_teams()
    encontrados = [t for t in nba_teams if nome.lower() in t['full_name'].lower()]
    return encontrados[0] if encontrados else None


@st.cache_data(ttl=86400)
def buscar_stats_carreira_jogador(player_id: int):
    try:
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.get_data_frames()[0]

        # Mapeamento do histórico COMPLETO ano a ano para o contexto da IA
        historico_completo = []
        for _, row in df.iterrows():
            if row['GP'] > 0:
                pts = round(row['PTS'] / row['GP'], 1)
                ast = round(row['AST'] / row['GP'], 1)
                reb = round(row['REB'] / row['GP'], 1)
                historico_completo.append(
                    f"{row['SEASON_ID']} ({row['TEAM_ABBREVIATION']}): {pts} PTS, {reb} REB, {ast} AST")

        df_valid = df[df['GP'] > 10].copy()
        melhor_temp_str = "N/A"
        if not df_valid.empty:
            df_valid['TOTAL_IMPACT'] = (df_valid['PTS'] + df_valid['AST'] + df_valid['REB']) / df_valid['GP']
            melhor_idx = df_valid['TOTAL_IMPACT'].idxmax()
            melhor_row = df_valid.loc[melhor_idx]
            pts_m = round(melhor_row['PTS'] / melhor_row['GP'], 1)
            ast_m = round(melhor_row['AST'] / melhor_row['GP'], 1)
            reb_m = round(melhor_row['REB'] / melhor_row['GP'], 1)
            melhor_temp_str = f"{melhor_row['SEASON_ID']} ({pts_m} Pts, {reb_m} Reb, {ast_m} Ast)"

        medias = {
            "Jogos": int(df['GP'].sum()),
            "PTS": round(df['PTS'].sum() / df['GP'].sum(), 1) if df['GP'].sum() > 0 else 0,
            "AST": round(df['AST'].sum() / df['GP'].sum(), 1) if df['GP'].sum() > 0 else 0,
            "REB": round(df['REB'].sum() / df['GP'].sum(), 1) if df['GP'].sum() > 0 else 0,
            "STL": round(df['STL'].sum() / df['GP'].sum(), 1) if 'STL' in df and df['GP'].sum() > 0 else 0,
            "BLK": round(df['BLK'].sum() / df['GP'].sum(), 1) if 'BLK' in df and df['GP'].sum() > 0 else 0,
            "FG_PCT": round(df['FG_PCT'].mean() * 100, 1),
            "FG3_PCT": round(df['FG3_PCT'].mean() * 100, 1) if 'FG3_PCT' in df else 0,
            "FT_PCT": round(df['FT_PCT'].mean() * 100, 1) if 'FT_PCT' in df else 0,
            "Melhor_Temporada": melhor_temp_str
        }
        return medias, historico_completo
    except Exception:
        return None, []


@st.cache_data(ttl=86400)
def buscar_stats_time(team_id: int):
    try:
        stats = teamyearbyyearstats.TeamYearByYearStats(team_id=team_id)
        df = stats.get_data_frames()[0]

        # Envia todas as temporadas da história do time para consultas de décadas
        historico_time = []
        for _, row in df.iterrows():
            historico_time.append(
                f"{row['YEAR']}: {row['WINS']}V-{row['LOSSES']}D (Pts: {row['PTS']}, Reb: {row['REB']})")

        return historico_time
    except Exception:
        return []


@st.cache_data(ttl=86400)
def buscar_premios_jogador(player_id: int):
    try:
        awards = playerawards.PlayerAwards(player_id=player_id)
        df = awards.get_data_frames()[0]

        def extrair_anos(descricao):
            anos = df[df['DESCRIPTION'] == descricao]['SEASON'].astype(str).tolist()
            return ", ".join(anos) if anos else "Nenhum"

        def extrair_anos_contem(texto):
            anos = df[df['DESCRIPTION'].str.contains(texto, na=False)]['SEASON'].astype(str).tolist()
            return ", ".join(anos) if anos else "Nenhum"

        premios = {
            "Campeonatos_Anos": extrair_anos('NBA Champion'),
            "Campeonatos_Qtd": len(df[df['DESCRIPTION'] == 'NBA Champion']),

            "MVP_Anos": extrair_anos('NBA Most Valuable Player'),
            "MVP_Qtd": len(df[df['DESCRIPTION'] == 'NBA Most Valuable Player']),

            "FMVP_Anos": extrair_anos('NBA Finals Most Valuable Player'),
            "FMVP_Qtd": len(df[df['DESCRIPTION'] == 'NBA Finals Most Valuable Player']),

            "All-Star_Anos": extrair_anos('NBA All-Star'),
            "All-Star_Qtd": len(df[df['DESCRIPTION'] == 'NBA All-Star']),

            "All-NBA_Anos": extrair_anos_contem('All-NBA'),
            "All-NBA_Qtd": len(df[df['DESCRIPTION'].str.contains('All-NBA', na=False)])
        }
        return premios
    except Exception:
        return {"Campeonatos_Qtd": 0, "MVP_Qtd": 0, "FMVP_Qtd": 0, "All-Star_Qtd": 0, "All-NBA_Qtd": 0,
                "Campeonatos_Anos": "", "MVP_Anos": "", "FMVP_Anos": ""}


def construir_contexto_nba(pergunta: str) -> str:
    contexto = ""
    pergunta_lower = pergunta.lower()

    nba_players = players.get_players()
    for p in nba_players:
        if p['full_name'].lower() in pergunta_lower:
            medias, historico_ano_a_ano = buscar_stats_carreira_jogador(p['id'])
            premios = buscar_premios_jogador(p['id'])
            if medias:
                contexto += f"--- DADOS DE {p['full_name'].upper()} ---\n"
                contexto += f"Anos de Conquistas (Não inventar outros): MVPs ({premios.get('MVP_Anos')}), Títulos ({premios.get('Campeonatos_Anos')}), Finals MVPs ({premios.get('FMVP_Anos')})\n"
                contexto += f"Histórico Ano a Ano (PTS, REB, AST):\n" + "\n".join(historico_ano_a_ano) + "\n\n"
            if contexto.count("DADOS DE") >= 3:
                break

    nba_teams = teams.get_teams()
    for t in nba_teams:
        if t['full_name'].lower() in pergunta_lower or t['nickname'].lower() in pergunta_lower:
            historico_time = buscar_stats_time(t['id'])
            if historico_time:
                contexto += f"--- DADOS DO TIME: {t['full_name'].upper()} ---\n"
                contexto += f"Histórico de Desempenho por Ano:\n" + "\n".join(historico_time[-30:]) + "\n\n"
            break

    if not contexto:
        contexto = "AVISO AO MODELO: Nenhum jogador ou time específico foi identificado na pergunta para extração de banco de dados. Informe ao usuário que ele precisa citar os nomes ou responda usando conhecimentos gerais, mas NÃO invente estatísticas precisas."

    return contexto