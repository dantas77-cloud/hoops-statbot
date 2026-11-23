"""Rode UMA vez (precisa de internet): python scripts/build_data.py
Gera data/awards.csv, data/team_seasons.csv, data/players_index.csv a partir da nba_api.
O download de prêmios é retomável: se parar, rode de novo e ele continua."""
import os, time
import pandas as pd
from nba_api.stats.endpoints import playerawards, playerindex, leaguestandingsv3, leaguedashteamstats

OUT = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(OUT, exist_ok=True)
SEASONS = [f"{y}-{str(y+1)[2:]}" for y in range(1946, 2026)]

def retry(fn, n=3):
    for i in range(n):
        try:
            return fn()
        except Exception as e:
            print(f"  falha ({type(e).__name__}): {str(e)[:80]}")
            time.sleep(2 * (i + 1))
    return None

def players_index():
    r = retry(lambda: playerindex.PlayerIndex(historical_nullable=1, timeout=60))
    df = r.get_data_frames()[0]
    df["NAME"] = df["PLAYER_FIRST_NAME"] + " " + df["PLAYER_LAST_NAME"]
    keep = [c for c in ["PERSON_ID", "NAME", "POSITION", "FROM_YEAR", "TO_YEAR"] if c in df]
    df[keep].to_csv(f"{OUT}/players_index.csv", index=False)
    return df

def team_seasons():
    rows = []
    for s in SEASONS:
        st = retry(lambda: leaguestandingsv3.LeagueStandingsV3(season=s, timeout=60))
        if st is None:
            print("sem standings", s); continue
        d = st.get_data_frames()[0]
        adv = {}
        if int(s[:4]) >= 1996:
            a = retry(lambda: leaguedashteamstats.LeagueDashTeamStats(
                season=s, measure_type_detailed_defense="Advanced", per_mode_detailed="PerGame", timeout=60))
            if a is not None:
                for _, r in a.get_data_frames()[0].iterrows():
                    adv[r["TEAM_NAME"]] = (r.get("OFF_RATING"), r.get("DEF_RATING"), r.get("NET_RATING"))
        for _, r in d.iterrows():
            nome = f"{r['TeamCity']} {r['TeamName']}".strip()
            o, df_, n = adv.get(nome, (None, None, None))
            rows.append(dict(SEASON=s, TEAM=nome, TEAM_ID=r.get("TeamID"), CONF=r.get("Conference"), W=r.get("WINS"), L=r.get("LOSSES"),
                             PPG=r.get("PointsPG"), OPP_PPG=r.get("OppPointsPG"), DIFF=r.get("DiffPointsPG"),
                             ORTG=o, DRTG=df_, NRTG=n))
        print("time-temporada", s); time.sleep(0.6)
    pd.DataFrame(rows).to_csv(f"{OUT}/team_seasons.csv", index=False)

def awards(idx):
    import sys
    from concurrent.futures import ThreadPoolExecutor
    from nba_api.stats.static import players as estatico
    minimo = int(sys.argv[sys.argv.index("--min-anos") + 1]) if "--min-anos" in sys.argv else 0
    ids = {int(i) for i in idx["PERSON_ID"]} | {p["id"] for p in estatico.get_players()}
    path, vpath = f"{OUT}/awards.csv", f"{OUT}/sem_premios.txt"
    done = pd.read_csv(path).drop_duplicates() if os.path.exists(path) else pd.DataFrame()
    feitos = {int(i) for i in done["PERSON_ID"]} if len(done) else set()
    vazios = {int(x) for x in open(vpath).read().split()} if os.path.exists(vpath) else set()
    rows = [done] if len(done) else []
    todo = sorted(ids - feitos - vazios)
    dur = {}
    if {"FROM_YEAR", "TO_YEAR"} <= set(idx.columns):
        t = idx.assign(F=pd.to_numeric(idx.FROM_YEAR, errors="coerce"), T=pd.to_numeric(idx.TO_YEAR, errors="coerce")).dropna(subset=["F", "T"])
        dur = {int(r.PERSON_ID): r.T - r.F for r in t.itertuples()}
    todo.sort(key=lambda i: -dur.get(i, 0))  # carreiras longas primeiro: os prêmios importantes chegam antes
    if minimo:
        todo = [i for i in todo if dur.get(i, minimo) >= minimo]
    print(f"Jogadores a consultar: {len(todo)} (3 consultas em paralelo; pode parar com Ctrl+C a qualquer momento)")

    def salvar():
        if rows:
            pd.concat(rows).drop_duplicates().to_csv(path, index=False)
        open(vpath, "w").write(" ".join(map(str, sorted(vazios))))

    def buscar(pid):
        r = retry(lambda: playerawards.PlayerAwards(player_id=int(pid), timeout=30))
        time.sleep(0.6)
        return pid, r

    for passada in range(1, 4):
        falhas, k = [], 0
        ex = ThreadPoolExecutor(max_workers=3)
        try:
            for pid, r in ex.map(buscar, todo):
                k += 1
                if r is None:
                    falhas.append(pid)
                else:
                    a = r.get_data_frames()[0]
                    if len(a):
                        nome = (a["FIRST_NAME"].fillna("") + " " + a["LAST_NAME"].fillna("")).str.strip()
                        rows.append(pd.DataFrame(dict(PERSON_ID=pid, PLAYER=nome, TEAM=a.get("TEAM"), SEASON=a["SEASON"],
                            DESCRIPTION=a["DESCRIPTION"], ALL_NBA_TEAM_NUMBER=a.get("ALL_NBA_TEAM_NUMBER"))))
                    else:
                        vazios.add(int(pid))
                if k % 100 == 0:
                    salvar(); print(f"passada {passada}: {k}/{len(todo)} (falhas: {len(falhas)})")
        except KeyboardInterrupt:
            ex.shutdown(wait=False, cancel_futures=True)
            salvar(); print("Interrompido. Progresso salvo; rode de novo para continuar.")
            raise SystemExit
        ex.shutdown()
        salvar()
        todo = falhas
        if not todo:
            break
        print(f"{len(todo)} consultas falharam; nova tentativa em 30s...")
        time.sleep(30)
    open(f"{OUT}/falhas.txt", "w").write(" ".join(map(str, todo)))
    if todo:
        print(f"ATENÇÃO: {len(todo)} jogadores sem resposta. Rode o script de novo mais tarde.")


if __name__ == "__main__":
    ip = f"{OUT}/players_index.csv"
    idx = pd.read_csv(ip) if os.path.exists(ip) else players_index()
    if not os.path.exists(f"{OUT}/team_seasons.csv"):
        team_seasons()
    awards(idx)
    from verificar_dados import verificar
    verificar()
    print("Pronto! Dados em /data")
