import pandas as pd
from services.knowledge import pontuar, detectar_posicao
from utils.texto import resumir

COLS = ["PERSON_ID", "PLAYER", "TEAM", "SEASON", "DESCRIPTION", "ALL_NBA_TEAM_NUMBER"]
# Jogadores FICTÍCIOS: Ícaro (ala-armador, 5,3 apg), Mateus (armador, 11,2 apg), Rafael (armador, 6,5 apg).
AW = pd.DataFrame([
    (1, "Ícaro Silva", "Time Alfa", "2030-31", "NBA Most Valuable Player", None),
    (1, "Ícaro Silva", "Time Alfa", "2031-32", "NBA Most Valuable Player", None),
    (2, "Mateus Prado", "Time Beta", "2030-31", "NBA Champion", None),
    (2, "Mateus Prado", "Time Beta", "2030-31", "NBA Finals Most Valuable Player", None),
    (3, "Rafael Lima", "Time Gama", "2032-33", "NBA Most Valuable Player", None),
], columns=COLS)
IDX = pd.DataFrame({"PERSON_ID": [1, 2, 3], "POSITION": ["G", "G", "G"]})
PTS = pd.DataFrame([
    (1, "Ícaro Silva", "2031-32", 1, "ALF", 1000, 0, 30000, 6000, 5300),
    (2, "Mateus Prado", "2030-31", 2, "BET", 900, 0, 17000, 6500, 10100),
    (3, "Rafael Lima", "2032-33", 3, "GAM", 950, 0, 24000, 4900, 6200),
], columns=["PERSON_ID", "PLAYER_NAME", "SEASON", "TEAM_ID", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST"])


def nomes(df):
    return list(df.Jogador) if len(df) else []


def test_armador_exclui_ala_armador():
    n = nomes(pontuar(AW, IDX, None, "PG", None, PTS))
    assert "Ícaro Silva" not in n and "Mateus Prado" in n and "Rafael Lima" in n


def test_ala_armador_exclui_armadores():
    assert nomes(pontuar(AW, IDX, None, "SG", None, PTS)) == ["Ícaro Silva"]


def test_ranking_segue_a_pontuacao():
    df = pontuar(AW, IDX, None, None, None, PTS)
    assert list(df.Pontos) == sorted(df.Pontos, reverse=True)
    assert df.Jogador.iloc[0] == "Ícaro Silva"  # 2 MVPs (20 pts) > Rafael (10) > Mateus (9)


def test_playoffs_usa_so_titulos_e_mvp_das_finais():
    df = pontuar(AW, IDX, None, None, None, PTS, so_playoffs=True)
    assert nomes(df) == ["Mateus Prado"] and df.Pontos.iloc[0] == 9


def test_detectar_posicao():
    assert detectar_posicao("top 5 armadores da historia") == "PG"
    assert detectar_posicao("melhores ala-armadores") == "SG"
    assert detectar_posicao("melhores pivos de todos os tempos") == "C"
    assert detectar_posicao("melhor ala da decada") == "F"
    assert detectar_posicao("melhor jogador da historia") is None


def test_resumir_preserva_o_fim():
    t = "inicio " + "x" * 2000 + " VEREDITO FINAL"
    assert resumir(t, 300).endswith("VEREDITO FINAL") and len(resumir(t, 300)) < 330
