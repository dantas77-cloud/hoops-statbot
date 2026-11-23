"""Confere a qualidade de data/awards.csv. Rode: python scripts/verificar_dados.py"""
import os
import pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "data")
CONHECIDOS = {"Kareem Abdul-Jabbar": 6, "Michael Jordan": 5, "Bill Russell": 5, "Wilt Chamberlain": 4, "LeBron James": 4,
              "Magic Johnson": 3, "Larry Bird": 3, "Nikola Jokic": 3, "Tim Duncan": 2, "Steve Nash": 2, "Stephen Curry": 2,
              "Giannis Antetokounmpo": 2, "Kevin Garnett": 1, "Kobe Bryant": 1, "Shaquille O'Neal": 1}


def verificar():
    aw = pd.read_csv(f"{D}/awards.csv")
    n0 = len(aw)
    aw = aw.drop_duplicates()
    aw = aw[~aw.DESCRIPTION.str.contains("Sporting News", case=False)]
    print(f"Linhas: {n0} | duplicadas removidas: {n0 - len(aw)} | jogadores com prêmios: {aw.PERSON_ID.nunique()}")
    print("\nDescrições mais comuns (útil para depurar):")
    print(aw.DESCRIPTION.value_counts().head(25).to_string())
    mvp = aw[aw.DESCRIPTION.str.contains("Most Valuable Player", case=False) & ~aw.DESCRIPTION.str.contains(
        "Finals|All.?Star|Month|Week|Conference|Game|Rookie|Challenge|Voting|Cup|Tournament", case=False)].drop_duplicates(["PERSON_ID", "SEASON"])
    c = mvp.groupby("PLAYER").size()
    print("\nMVPs (esperado vs encontrado):")
    for p, e in CONHECIDOS.items():
        print(f"  {p}: {e} vs {c.get(p, 0)}  {'OK' if c.get(p, 0) == e else '<-- DIVERGE'}")
    print(f"  Total de temporadas com MVP: {mvp.SEASON.nunique()} (esperado 71, de 1955-56 a 2025-26)")

    def contagem(chave, excl=""):
        d = aw[aw.DESCRIPTION.str.contains(chave, case=False)]
        if excl:
            d = d[~d.DESCRIPTION.str.contains(excl, case=False)]
        return d.drop_duplicates(["PERSON_ID", "SEASON"]).groupby("SEASON").size()

    problemas = []
    for nome, chave, excl, minimo, desde in [("All-NBA", "All-NBA", "Rookie|Voting", 15, 1988), ("All-NBA", "All-NBA", "Rookie|Voting", 10, 1946),
                                             ("All-Defensive", "All-Defensive", "Voting", 10, 1968), ("All-Star", "All-Star", "Most Valuable|Replacement|Rookie|Game|3-Point|Dunk|Skills|Challenge", 20, 1951)]:
        cont = contagem(chave, excl)
        for s in sorted(cont.index):
            ano = int(s[:4])
            if ano < desde:
                continue
            if nome == "All-NBA" and minimo == 10 and ano >= 1988:
                continue
            if cont[s] < minimo:
                problemas.append(f"{nome} {s}: {cont[s]} jogadores (esperado ≥ {minimo})")
    print("\nTemporadas possivelmente incompletas:")
    print("\n".join(problemas) if problemas else "  nenhuma")
    return problemas


if __name__ == "__main__":
    verificar()
