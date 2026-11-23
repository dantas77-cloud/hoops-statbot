import pandas as pd
from services.knowledge import series_time, desempenho_jogador, _linha_stats

C = ["SEASON", "TEAM_A_ID", "TEAM_A", "TEAM_B_ID", "TEAM_B", "WINS_A", "WINS_B", "FIRST_DATE"]
S = "2030-31"
# Times e jogador FICTÍCIOS.
PS = pd.DataFrame([
    (S, 10, "Alfa Falcões", 20, "Beta Tubarões", 4, 0, "2031-04-24"),
    (S, 10, "Alfa Falcões", 30, "Gama Lobos", 4, 2, "2031-05-08"),
    (S, 40, "Delta Águias", 10, "Alfa Falcões", 4, 1, "2031-05-22"),
    (S, 40, "Delta Águias", 60, "Zeta Raposas", 4, 1, "2031-04-24"),
    (S, 40, "Delta Águias", 70, "Eta Leões", 4, 2, "2031-05-08"),
    (S, 40, "Delta Águias", 50, "Épsilon Ursos", 4, 3, "2031-06-09"),
], columns=C)
TS = pd.DataFrame([(S, "Alfa Falcões", 10, 62, 20)], columns=["SEASON", "TEAM", "TEAM_ID", "W", "L"])
BASE = ["PERSON_ID", "PLAYER_NAME", "SEASON", "TEAM_ID", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST"]
PTS = pd.DataFrame([(3, "Diego Ramos", S, 10, "ALF", 75, 2573, 1165, 266, 861)], columns=BASE)
PP = pd.DataFrame([(3, "Diego Ramos", S, 10, "ALF", 15, 575, 340, 50, 164)], columns=BASE)


def test_series_do_time_eliminado_na_final_de_conferencia():
    s = series_time(PS, S, 10)
    assert [x["rodada"] for x in s] == ["1ª rodada", "semifinal de conferência", "final de conferência"]
    assert s[-1]["venceu"] is False and s[-1]["adv"] == "Delta Águias" and s[-1]["res"] == "1-4"


def test_series_do_campeao_termina_nas_finais():
    s = series_time(PS, S, 40)
    assert s[-1]["rodada"] == "Finais da NBA" and s[-1]["venceu"] is True


def test_desempenho_junta_temporada_regular_playoffs_e_campanha():
    txt = " | ".join(desempenho_jogador(PTS, PP, TS, PS, 3, S))
    assert "temporada regular: 75 jogos" in txt and "15.5 pts" in txt and "11.5 ast" in txt
    assert "Alfa Falcões (62-20" in txt
    assert "playoffs: 15 jogos" in txt and "22.7 pts" in txt
    assert "final de conferência: perdeu para Delta Águias (1-4)" in txt and "eliminado" in txt


def test_sem_dados_de_playoffs_nao_inventa():
    vazio = PP.iloc[0:0]
    assert "sem jogos de playoffs registrados" in " | ".join(desempenho_jogador(PTS, vazio, TS, PS, 3, S))


def test_linha_stats_ignora_colunas_vazias():
    df = PTS.assign(STL=float("nan"))
    assert "roubos" not in _linha_stats(df)
