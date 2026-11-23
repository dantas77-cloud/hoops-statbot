from utils.texto import limpar


def test_br_em_tabela_vira_separador():
    saida = limpar("| Título | Ana – 1.<br>Bia – 4. |")
    assert "<br>" not in saida
    assert "Bia – 4." in saida and saida.startswith("|") and saida.endswith("|")


def test_br_fora_de_tabela_vira_quebra_de_linha():
    assert limpar("linha 1<br>linha 2") == "linha 1\nlinha 2"


def test_remove_tags_comuns():
    assert limpar("<b>oi</b> <i>mundo</i>") == "oi mundo"


def test_preserva_sinais_de_comparacao():
    assert limpar("pontos a < b e c > d") == "pontos a < b e c > d"
