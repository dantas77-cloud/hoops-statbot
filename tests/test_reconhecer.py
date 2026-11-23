from services.knowledge import reconhecer


def nomes(texto):
    return {p["full_name"] for p in reconhecer(texto)[0]}


def test_apelido():
    assert "Kevin Durant" in nomes("quantos títulos o KD tem?")


def test_nome_completo():
    assert "LeBron James" in nomes("dados do LeBron James")
