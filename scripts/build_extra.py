"""Rode UMA vez, depois do build_data.py: python scripts/build_extra.py
Gera data/player_team_seasons.csv (jogadores por time e temporada), data/playoff_series.csv (séries de playoffs)
e data/player_playoffs.csv (estatísticas de playoffs por jogador),
e atualiza team_seasons.csv com TEAM_ID e conferência. É retomável (Ctrl+C salva o progresso)."""
import os, sys, time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from nba_api.stats.endpoints import playercareerstats, leaguegamefinder

sys.path.insert(0, os.path.dirname(__file__))
from build_data import OUT, SEASONS, retry, team_seasons


def player_team_seasons():
    aw = pd.read_csv(f"{OUT}/awards.csv").drop_duplicates()
    nomes = aw.drop_duplicates("PERSON_ID").set_index("PERSON_ID").PLAYER.to_dict()
    path = f"{OUT}/player_team_seasons.csv"
    done = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
    feitos = set(done.PERSON_ID) if len(done) else set()
    rows = [done] if len(done) else []
    todo = [p for p in nomes if p not in feitos]
    print(f"Jogadores a consultar: {len(todo)}")

    def buscar(pid):
        r = retry(lambda: playercareerstats.PlayerCareerStats(player_id=int(pid), per_mode36="Totals", timeout=30))
        time.sleep(0.6)
        return pid, r

    def salvar():
        if rows:
            pd.concat(rows).to_csv(path, index=False)

    ex = ThreadPoolExecutor(max_workers=3)
    try:
        for k, (pid, r) in enumerate(ex.map(buscar, todo), 1):
            if r is not None:
                d = r.get_data_frames()[0]
                d = d[d.TEAM_ABBREVIATION != "TOT"]
                cols = [c for c in ["SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK"] if c in d]
                d = d[cols].rename(columns={"SEASON_ID": "SEASON"})
                d.insert(0, "PERSON_ID", pid)
                d.insert(1, "PLAYER_NAME", nomes[pid])
                rows.append(d)
            if k % 100 == 0:
                salvar(); print(f"jogadores: {k}/{len(todo)}")
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        salvar(); print("Interrompido. Progresso salvo; rode de novo para continuar.")
        raise SystemExit
    ex.shutdown()
    salvar()


def playoff_series():
    out = []
    for s in SEASONS:
        r = retry(lambda: leaguegamefinder.LeagueGameFinder(player_or_team_abbreviation="T", season_nullable=s,
                  season_type_nullable="Playoffs", league_id_nullable="00", timeout=60))
        if r is None:
            print("sem playoffs", s); continue
        g = r.get_data_frames()[0]
        if g.empty:
            continue
        g["OPP"] = g.MATCHUP.str.split().str[-1]
        ab = g.drop_duplicates("TEAM_ABBREVIATION").set_index("TEAM_ABBREVIATION")[["TEAM_ID", "TEAM_NAME"]]
        ser = {}
        for x in g.itertuples():
            k = tuple(sorted([x.TEAM_ABBREVIATION, x.OPP]))
            e = ser.setdefault(k, {"w": {k[0]: 0, k[1]: 0}, "d": x.GAME_DATE})
            if x.WL == "W":
                e["w"][x.TEAM_ABBREVIATION] += 1
            e["d"] = min(e["d"], x.GAME_DATE)
        for (a, b), e in ser.items():
            if a in ab.index and b in ab.index:
                out.append(dict(SEASON=s, TEAM_A_ID=ab.loc[a, "TEAM_ID"], TEAM_A=ab.loc[a, "TEAM_NAME"], TEAM_B_ID=ab.loc[b, "TEAM_ID"],
                                TEAM_B=ab.loc[b, "TEAM_NAME"], WINS_A=e["w"][a], WINS_B=e["w"][b], FIRST_DATE=e["d"]))
        print("playoffs", s); time.sleep(0.6)
    pd.DataFrame(out).to_csv(f"{OUT}/playoff_series.csv", index=False)


def _tabela(r, nome):
    """Extrai uma tabela pelo nome do conjunto de resultados da API (mais robusto que usar a posição)."""
    for rs in r.get_dict()["resultSets"]:
        if rs["name"] == nome:
            return pd.DataFrame(rs["rowSet"], columns=rs["headers"])
    return pd.DataFrame()


def player_playoffs():
    """Estatísticas de playoffs por jogador e temporada. Quem tem prêmios maiores é consultado primeiro."""
    aw = pd.read_csv(f"{OUT}/awards.csv").drop_duplicates()
    nomes = aw.drop_duplicates("PERSON_ID").set_index("PERSON_ID").PLAYER.to_dict()
    grandes = aw[aw.DESCRIPTION.str.contains("Most Valuable Player|Defensive Player of the Year|All-NBA|Rookie of the Year", case=False)
                 & ~aw.DESCRIPTION.str.contains("Sporting News|Cup|Tournament|All-Star|Month|Week", case=False)]
    peso = grandes.groupby("PERSON_ID").size()
    path, sem = f"{OUT}/player_playoffs.csv", f"{OUT}/sem_playoffs.txt"
    done = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
    feitos = set(done.PERSON_ID) if len(done) else set()
    vazios = {int(x) for x in open(sem).read().split()} if os.path.exists(sem) else set()
    rows = [done] if len(done) else []
    todo = sorted((p for p in nomes if p not in feitos and p not in vazios), key=lambda p: -peso.get(p, 0))
    print(f"Jogadores a consultar (playoffs): {len(todo)}  (premiados maiores primeiro; Ctrl+C salva o progresso)")

    def buscar(pid):
        r = retry(lambda: playercareerstats.PlayerCareerStats(player_id=int(pid), per_mode36="Totals", timeout=30))
        time.sleep(0.6)
        return pid, r

    def salvar():
        if rows:
            pd.concat(rows).to_csv(path, index=False)
        open(sem, "w").write(" ".join(map(str, sorted(vazios))))

    ex = ThreadPoolExecutor(max_workers=3)
    try:
        for k, (pid, r) in enumerate(ex.map(buscar, todo), 1):
            if r is not None:
                d = _tabela(r, "SeasonTotalsPostSeason")
                if d.empty:
                    vazios.add(int(pid))
                else:
                    if "TEAM_ABBREVIATION" in d:
                        d = d[d.TEAM_ABBREVIATION != "TOT"]
                    cols = [c for c in ["SEASON_ID", "TEAM_ID", "TEAM_ABBREVIATION", "GP", "MIN", "PTS", "REB", "AST", "STL", "BLK"] if c in d]
                    d = d[cols].rename(columns={"SEASON_ID": "SEASON"})
                    d.insert(0, "PERSON_ID", pid)
                    d.insert(1, "PLAYER_NAME", nomes[pid])
                    rows.append(d)
            if k % 100 == 0:
                salvar(); print(f"playoffs: {k}/{len(todo)}")
    except KeyboardInterrupt:
        ex.shutdown(wait=False, cancel_futures=True)
        salvar(); print("Interrompido. Progresso salvo; rode de novo para continuar.")
        raise SystemExit
    ex.shutdown()
    salvar()


if __name__ == "__main__":
    tp = f"{OUT}/team_seasons.csv"
    if not os.path.exists(tp) or "TEAM_ID" not in pd.read_csv(tp, nrows=1).columns:
        team_seasons()
    player_team_seasons()
    if not os.path.exists(f"{OUT}/playoff_series.csv"):
        playoff_series()
    player_playoffs()
    print("Pronto! Dados extras em /data")
