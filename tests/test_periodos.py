from services.knowledge import extrair_periodos, _seasons_decada


def test_ano_vira_temporada_que_termina_nele():
    assert extrair_periodos("campeão de 1996") == (["1995-96"], [])


def test_temporada_explicita_e_virada_de_seculo():
    assert extrair_periodos("MVP da 2015-16") == (["2015-16"], [])
    assert extrair_periodos("temporada 1999-00") == (["1999-00"], [])


def test_decada_curta_e_longa():
    assert extrair_periodos("melhores dos anos 90") == ([], [1990])
    assert extrair_periodos("década de 2010") == ([], [2010])
    assert extrair_periodos("anos 2000") == ([], [2000])


def test_decada_tem_dez_temporadas():
    ss = _seasons_decada(2010)
    assert len(ss) == 10 and ss[0] == "2010-11" and ss[-1] == "2019-20"
