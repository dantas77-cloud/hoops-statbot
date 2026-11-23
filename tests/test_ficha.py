import pandas as pd
from services.knowledge import ficha_jogador

COLS = ["PERSON_ID", "PLAYER", "TEAM", "SEASON", "DESCRIPTION", "ALL_NBA_TEAM_NUMBER"]
# Jogadores e times FICTÍCIOS: os testes não usam dados reais da NBA.
AW = pd.DataFrame([
    (1, "Alex Rivera", "Falcões da Cidade Alfa", "2030-31", "NBA Champion", None),
    (2, "Bruno Costa", "Tubarões da Cidade Beta", "2030-31", "NBA Most Valuable Player", None),
    (2, "Bruno Costa", "Tubarões da Cidade Beta", "2029-30", "NBA Sporting News Most Valuable Player of the Year", None),
    (3, "Caio Mendes", "Lobos da Cidade Gama", "2031-32", "NBA Cup Most Valuable Player", None),
    (3, "Caio Mendes", "Lobos da Cidade Gama", "2031-32", "All-NBA", 2),
], columns=COLS)
PTS = pd.DataFrame([
    (1, "Alex Rivera", "2030-31", 101, "FAL", 62, 33.4, 25.1, 8.3, 4.8),
    (2, "Bruno Costa", "2030-31", 102, "TUB", 81, 34.6, 31.6, 10.7, 10.4),
], columns=["PERSON_ID", "PLAYER_NAME", "SEASON", "TEAM_ID", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST"])


def test_titulo_fica_com_quem_ganhou():
    assert "Campeão da NBA: 1x — 2030-31 (Falcões da Cidade Alfa)" in ficha_jogador(AW, PTS, None, 1)


def test_titulo_nao_vaza_para_jogador_do_mesmo_ano():
    assert "Campeão da NBA: 0x" in ficha_jogador(AW, PTS, None, 2)


def test_mvp_ignora_sporting_news():
    assert "MVP da temporada: 1x — 2030-31" in ficha_jogador(AW, PTS, None, 2)


def test_mvp_ignora_nba_cup():
    f = ficha_jogador(AW, PTS, None, 3)
    assert "MVP da temporada: 0x" in f and "All-NBA: 1x — 2031-32 (2º time)" in f


def test_ficha_mostra_times_por_temporada():
    assert "FAL 2030-31" in ficha_jogador(AW, PTS, None, 1)
