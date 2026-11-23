import os, re, unicodedata
import pandas as pd
import streamlit as st
from nba_api.stats.static import players, teams
from services.nba_service import buscar_stats_carreira_jogador, buscar_premios_jogador

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
ALIASES = {"lebron": "LeBron James", "bron": "LeBron James", "mj": "Michael Jordan", "jordan": "Michael Jordan",
           "kobe": "Kobe Bryant", "curry": "Stephen Curry", "shaq": "Shaquille O'Neal", "kd": "Kevin Durant",
           "durant": "Kevin Durant", "giannis": "Giannis Antetokounmpo", "jokic": "Nikola Jokic",
           "magic johnson": "Magic Johnson", "bird": "Larry Bird", "duncan": "Tim Duncan", "wilt": "Wilt Chamberlain",
           "kareem": "Kareem Abdul-Jabbar", "russell": "Bill Russell", "dirk": "Dirk Nowitzki", "harden": "James Harden",
           "luka": "Luka Doncic", "wemby": "Victor Wembanyama", "iverson": "Allen Iverson", "hakeem": "Hakeem Olajuwon"}
# Ordem importa: padrões mais específicos primeiro. A API da NBA só informa Guard/Forward/Center.
POSICOES = [(r"ala[- ]armador|shooting guard|\bsg\b", "SG"), (r"\barmador(?:es)?\b|point guard|\bpg\b", "PG"),
            (r"ala[- ]pivo|power forward|\bpf\b", "F"), (r"\balas?\b|small forward|\bsf\b", "F"),
            (r"\bpivos?\b|\bcenters?\b", "C")]
# chave -> (inclui, exclui)
AW = {"campeao": ("NBA Champion", ""),
      "mvp": ("Most Valuable Player", "Finals|All.?Star|Month|Week|Conference|Game|Rookie|Challenge|Voting|Cup|Tournament"),
      "fmvp": ("Finals Most Valuable", "Conference|Voting"),
      "cfmvp": ("Conference Finals", "Voting"), "dpoy": ("Defensive Player of the Year", "Month|Week|Voting"),
      "roy": ("Rookie of the Year", "Month|Week|Voting"), "6man": ("Sixth Man", "Voting"),
      "mip": ("Most Improved", "Voting"), "allnba": ("All-NBA", "Rookie|Voting"),
      "alldef": ("All-Defensive", "Voting"),
      "allstar": ("All-Star", "Most Valuable|Replacement|Rookie|Game|3-Point|Dunk|Skills|Challenge")}
PESOS = {"mvp": 10, "fmvp": 6, "campeao": 3, "dpoy": 3, "allnba": 2, "alldef": 1, "allstar": 0.5}
PESOS_PLAYOFFS = {"fmvp": 6, "campeao": 3}  # critério usado nos rankings 'nos playoffs'


def norm(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()


@st.cache_data
def _csv(nome):
    p = os.path.join(DATA, nome)
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p)
    return df.drop_duplicates() if nome == "awards.csv" else df


def dados_prontos():
    return _csv("awards.csv") is not None and _csv("team_seasons.csv") is not None


def _awd(df, k, seasons=None):
    inc, exc = AW[k]
    d = df[df.DESCRIPTION.fillna("").str.contains(inc, case=False, regex=False)]
    d = d[~d.DESCRIPTION.str.contains("Sporting News", case=False)]  # ignora prêmios que não são da NBA
    if exc:
        d = d[~d.DESCRIPTION.str.contains(exc, case=False, regex=True)]
    if seasons:
        d = d[d.SEASON.isin(seasons)]
    return d.drop_duplicates(["PERSON_ID", "SEASON"])  # 1 registro por jogador/temporada/prêmio


def extrair_periodos(txt):
    t = norm(txt)
    seasons, decs = [], []
    for a, b in re.findall(r"\b((?:19|20)\d{2})\s*[-/]\s*(\d{2})\b", t):
        seasons.append(f"{a}-{b}")
    t = re.sub(r"\b(?:19|20)\d{2}\s*[-/]\s*\d{2}\b", " ", t)
    for m in re.finditer(r"(?:anos|decadas?(?: de)?)\s*(\d{4}|\d0)\b|\b((?:19|20)\d0)s\b", t):
        d = int(m.group(1) or m.group(2))
        decs.append(d if d >= 1000 else (1900 + d if d >= 40 else 2000 + d))
    t = re.sub(r"(?:anos|decadas?(?: de)?)\s*(\d{4}|\d0)\b|\b(?:19|20)\d0s\b", " ", t)
    for y in re.findall(r"\b((?:19[4-9]|20[0-3])\d)\b", t):
        y = int(y); seasons.append(f"{y-1}-{str(y)[2:]}")  # "1996" = temporada 1995-96
    return sorted(set(seasons)), sorted(set(decs))


def _seasons_decada(d):
    return [f"{y}-{str(y+1)[2:]}" for y in range(d, d + 10)]


def _times(df_t, seasons, n=5):
    d = df_t[df_t.SEASON.isin(seasons)]
    out = []
    col = "NRTG" if d["NRTG"].notna().any() else "DIFF"
    out.append(f"Melhores times por {col} (saldo por jogo/net rating): " + "; ".join(
        f"{r.SEASON} {r.TEAM} ({r.W}-{r.L}, {col} {r[col]:+.1f})" for _, r in d.sort_values(col, ascending=False).head(n).iterrows()))
    dc = "DRTG" if d["DRTG"].notna().any() else "OPP_PPG"
    asc = d.dropna(subset=[dc]).sort_values(dc, ascending=True).head(n)
    out.append(f"Melhores defesas por {dc} (menor = melhor): " + "; ".join(
        f"{r.SEASON} {r.TEAM} ({dc} {r[dc]:.1f})" for _, r in asc.iterrows()))
    return out


PREMIO_PALAVRAS = [(r"mvp das finais|fmvp", "fmvp"), (r"mvp", "mvp"), (r"dpoy|defensor", "dpoy"), (r"calouro|\broy\b", "roy"), (r"campeao|titulo|anel", "campeao")]


def _linha_stats(df):
    """Médias por jogo a partir de totais (soma as linhas, por exemplo jogador que trocou de time)."""
    gp = df["GP"].sum()
    if not gp:
        return None
    partes = [f"{int(gp)} jogos"]
    for c, n in (("MIN", "min"), ("PTS", "pts"), ("REB", "reb"), ("AST", "ast"), ("STL", "roubos"), ("BLK", "tocos")):
        if c in df and df[c].notna().any() and df[c].sum() > 0:
            partes.append(f"{df[c].sum() / gp:.1f} {n}")
    return ", ".join(partes) + " por jogo"


def series_time(ps, s, tid):
    """Séries de playoffs do time na temporada, em ordem, com a rodada de cada uma."""
    d = ps[ps.SEASON == s]
    if d.empty:
        return []
    n = int(pd.concat([d.TEAM_A_ID, d.TEAM_B_ID]).value_counts().max())
    final = d.FIRST_DATE.max()
    nomes4 = {1: "1ª rodada", 2: "semifinal de conferência", 3: "final de conferência"}
    mine = d[(d.TEAM_A_ID == tid) | (d.TEAM_B_ID == tid)].sort_values("FIRST_DATE")
    out = []
    for i, r in enumerate(mine.itertuples(), 1):
        a = r.TEAM_A_ID == tid
        w, l = (r.WINS_A, r.WINS_B) if a else (r.WINS_B, r.WINS_A)
        rod = "Finais da NBA" if r.FIRST_DATE == final else ((nomes4.get(i) if n == 4 else None) or f"rodada {i}")
        out.append(dict(rodada=rod, adv=r.TEAM_B if a else r.TEAM_A, res=f"{int(w)}-{int(l)}", venceu=bool(w > l)))
    return out


def desempenho_jogador(pts, pp, ts, ps, pid, s):
    """Temporada regular, playoffs e campanha do time de um jogador numa temporada."""
    L, tid = [], None
    if pts is not None:
        reg = pts[(pts.PERSON_ID == pid) & (pts.SEASON == s)]
        if len(reg):
            linha = _linha_stats(reg)
            if linha:
                L.append("temporada regular: " + linha)
            tid = int(reg.sort_values("GP", ascending=False).TEAM_ID.iat[0])
    if tid is not None and ts is not None and "TEAM_ID" in ts:
        t = ts[(ts.SEASON == s) & (ts.TEAM_ID == tid)]
        if len(t):
            L.append(f"time: {t.TEAM.iat[0]} ({int(t.W.iat[0])}-{int(t.L.iat[0])} na temporada regular)")
    if pp is not None:
        q = pp[(pp.PERSON_ID == pid) & (pp.SEASON == s)]
        linha = _linha_stats(q) if len(q) else None
        L.append("playoffs: " + (linha or "sem jogos de playoffs registrados nesta temporada"))
    if tid is not None and ps is not None:
        sr = series_time(ps, s, tid)
        if sr:
            txt = "; ".join(f"{x['rodada']}: {'venceu' if x['venceu'] else 'perdeu para'} {x['adv']} ({x['res']})" for x in sr)
            fim = " (campeão)" if sr[-1]["venceu"] and sr[-1]["rodada"] == "Finais da NBA" else ("" if sr[-1]["venceu"] else " (eliminado nessa série)")
            L.append("campanha do time nos playoffs: " + txt + fim)
        elif (ps.SEASON == s).any():
            L.append("o time não disputou os playoffs")
    return L


def pacote_temporada(aw, tm, s, ps=None, compacto=False, pts=None, pp=None):
    L = [f"=== TEMPORADA {s} ==="]
    camp = _awd(aw, "campeao", [s])
    if len(camp):
        L.append(f"Campeão = {camp.TEAM.mode().iat[0]} (jogadores campeões na base: {', '.join(camp.PLAYER)})")
    for k, nome in [("mvp", "MVP"), ("fmvp", "MVP das Finais"), ("dpoy", "DPOY"), ("roy", "Calouro do Ano"),
                    ("6man", "Sexto Homem"), ("mip", "Jogador que Mais Evoluiu")]:
        d = _awd(aw, k, [s])
        if len(d): L.append(f"{nome}: {', '.join(d.PLAYER.unique())}")
    for k, nome in [("allnba", "All-NBA"), ("alldef", "All-Defensive")]:
        d = _awd(aw, k, [s])
        for n, g in d.groupby("ALL_NBA_TEAM_NUMBER"):
            L.append(f"{nome} {int(n)}º time: {', '.join(g.PLAYER)}")
    asr = _awd(aw, "allstar", [s])
    if len(asr): L.append(f"All-Stars ({len(asr)}): {', '.join(asr.PLAYER)}")
    if not compacto:
        for k, nome in [("mvp", "MVP da temporada"), ("dpoy", "Defensor do Ano"), ("roy", "Calouro do Ano"), ("fmvp", "MVP das Finais")]:
            for r in _awd(aw, k, [s]).itertuples():
                dl = desempenho_jogador(pts, pp, tm, ps, int(r.PERSON_ID), s)
                if dl:
                    L.append(f"Desempenho de {r.PLAYER} ({nome}, {s}): " + " | ".join(dl))
    if not compacto:
        L += _times(tm, [s])
    if ps is not None:
        cm = [c for c in caminho(aw, tm, ps, s) if c["pct"] == c["pct"]]
        if cm:
            L.append("Caminho do campeão nos playoffs: " + "; ".join(f"{c['adv']} ({c['res']}, adversário com {c['pct']*100:.0f}% de vitórias na temporada)" for c in cm))
    return "\n".join(L)


def ranking_jogadores(aw, idx, seasons, pos=None, time_id=None, pts=None, n=15):
    df = pontuar(aw, idx, seasons, pos, time_id, pts).head(n)
    return "Ranking por pontos de legado (MVP×10, FMVP×6, títulos×3, DPOY×3, All-NBA, All-Def, All-Star; com time: + temporadas e pontos no time): " + "; ".join(
        f"{r.Jogador} ({r.Pontos:.1f} | MVP {r.MVP}, títulos {r['Títulos']}, All-NBA {r['All-NBA']}, All-Star {r['All-Star']})" for _, r in df.iterrows())


ALIASES.update({"lbj": "LeBron James", "kg": "Kevin Garnett", "ai": "Allen Iverson", "cp3": "Chris Paul", "pg13": "Paul George",
                "tmac": "Tracy McGrady", "wade": "Dwyane Wade", "rose": "Derrick Rose", "kyrie": "Kyrie Irving", "kawhi": "Kawhi Leonard",
                "dame": "Damian Lillard", "melo": "Carmelo Anthony", "shai": "Shai Gilgeous-Alexander", "ant": "Anthony Edwards",
                "embiid": "Joel Embiid", "tatum": "Jayson Tatum", "booker": "Devin Booker", "morant": "Ja Morant", "kidd": "Jason Kidd",
                "nash": "Steve Nash", "pippen": "Scottie Pippen", "malone": "Karl Malone", "stockton": "John Stockton",
                "barkley": "Charles Barkley", "ewing": "Patrick Ewing", "robinson": "David Robinson", "thomas": "Isiah Thomas"})
SUFIXOS = {"jr", "sr", "ii", "iii", "iv"}


@st.cache_data
def _por_sobrenome():
    """Sobrenome -> jogador com mais prêmios (permite 'westbrook', 'durant', 'giannis' sem o nome completo)."""
    aw = _csv("awards.csv")
    if aw is None:
        return {}
    g = aw.groupby(["PERSON_ID", "PLAYER"]).size().reset_index(name="n")
    g = g[g.n >= 3].sort_values("n", ascending=False)
    out = {}
    for r in g.itertuples():
        toks = [t for t in norm(r.PLAYER).replace("-", " ").replace("'", " ").split() if t not in SUFIXOS]
        if toks and len(toks[-1]) >= 5 and toks[-1] not in out:
            out[toks[-1]] = {"id": int(r.PERSON_ID), "full_name": r.PLAYER}
    return out


def reconhecer(texto):
    """Jogadores citados (nome completo, apelido ou sobrenome) e o texto restante, sem os nomes."""
    nq = norm(texto)
    todos = players.get_players()
    achados, ids = [], set()
    for p in sorted(todos, key=lambda p: -len(p["full_name"])):
        n = norm(p["full_name"])
        if n in nq:
            achados.append(p); ids.add(p["id"]); nq = nq.replace(n, " ")
    for a, nome in ALIASES.items():
        if re.search(rf"\b{re.escape(a)}\b", nq):
            p = next((q for q in todos if q["full_name"] == nome), None)
            if p and p["id"] not in ids:
                achados.append(p); ids.add(p["id"])
            nq = re.sub(rf"\b{re.escape(a)}\b", " ", nq)
    for tok, p in _por_sobrenome().items():
        if re.search(rf"\b{re.escape(tok)}\b", nq):
            if p["id"] not in ids:
                achados.append(p); ids.add(p["id"])
            nq = re.sub(rf"\b{re.escape(tok)}\b", " ", nq)
    return achados, nq


def _i(x):
    try:
        return int(float(x))
    except Exception:
        return "?"


def _cronologia(p):
    por = p.sort_values(["SEASON", "GP"], ascending=[True, False]).groupby("SEASON", sort=True).TEAM_ABBREVIATION.agg(lambda x: "/".join(x))
    out, ult = [], None
    for s, t in por.items():
        if ult and t == ult[0]:
            ult[2] = s
        else:
            ult = [t, s, s]; out.append(ult)
    return "; ".join(f"{t} {a}" if a == b else f"{t} {a}→{b}" for t, a, b in out)


def _fmt(r, k):
    t = str(r.SEASON)
    if k == "campeao" and pd.notna(r.TEAM):
        t += f" ({r.TEAM})"
    if k in ("allnba", "alldef") and pd.notna(r.ALL_NBA_TEAM_NUMBER):
        t += f" ({_i(r.ALL_NBA_TEAM_NUMBER)}º time)"
    return t


def ficha_jogador(aw, pts, idx, pid, seasons=None, curta=False, pp=None, ts=None, ps=None):
    """Ficha completa e rotulada de um jogador: tudo que o chat pode afirmar sobre ele."""
    a = aw[aw.PERSON_ID == pid]
    nome = a.PLAYER.iat[0] if len(a) else str(pid)
    L = [f"--- FICHA: {nome.upper()} (só afirme sobre este jogador o que está nesta ficha) ---"]
    if idx is not None:
        r = idx[idx.PERSON_ID == pid]
        if len(r):
            L.append(f"Posição: {r.POSITION.iat[0]} | Carreira: {_i(r.FROM_YEAR.iat[0])}–{_i(r.TO_YEAR.iat[0])}")
    per = ""
    if seasons:
        per = f" em {seasons[0]}" if len(seasons) == 1 else f" no período {min(seasons)} a {max(seasons)}"
    for k, tit in [("campeao", "Campeão da NBA"), ("mvp", "MVP da temporada"), ("fmvp", "MVP das Finais"), ("dpoy", "Defensor do Ano"),
                   ("allnba", "All-NBA"), ("alldef", "All-Defensive"), ("allstar", "All-Star")]:
        d, tot = _awd(a, k, seasons), len(_awd(a, k))
        detalhe = ""
        if len(d) and not (curta and k in ("alldef", "allstar")):
            detalhe = " — " + ", ".join(_fmt(r, k) for r in d.itertuples())
        L.append(f"{tit}{per}: {len(d)}x{detalhe} [carreira: {tot}x]")
    if pts is not None:
        p = pts[pts.PERSON_ID == pid]
        if len(p):
            L.append("Times por temporada (carreira inteira): " + _cronologia(p))
            q = p[p.SEASON.isin(seasons)] if seasons else p
            gp = q.GP.sum()
            if gp:
                L.append(f"Estatísticas{per or ' na carreira'}: {int(gp)} jogos | {q.PTS.sum() / gp:.1f} pts, {q.REB.sum() / gp:.1f} reb, {q.AST.sum() / gp:.1f} ast por jogo")
            elif seasons:
                L.append(f"Sem jogos registrados{per}.")
    if pp is not None and not curta:
        q = pp[pp.PERSON_ID == pid]
        if seasons:
            q = q[q.SEASON.isin(seasons)]
        L.append(f"Playoffs{per or ' na carreira'}: " + ((_linha_stats(q) if len(q) else None) or "sem jogos de playoffs registrados"))
    if seasons and len(seasons) <= 3 and not curta:
        for s_ in seasons:
            dl = desempenho_jogador(pts, pp, ts, ps, pid, s_)
            if dl:
                L.append(f"Detalhe de {s_}: " + " | ".join(dl))
    return "\n".join(L)


def pacote_time(aw, ts, tid, nome):
    if "TEAM_ID" not in ts:
        return ""
    t = ts[ts.TEAM_ID == tid]
    camp = _awd(aw, "campeao").groupby("SEASON").TEAM.agg(lambda x: x.mode().iat[0])
    titulos = [s for s, n in camp.items() if ((t.SEASON == s) & (t.TEAM == n)).any()]
    melhores = t.assign(S=t.NRTG.fillna(t.DIFF)).sort_values("S", ascending=False).head(6)
    return (f"--- FRANQUIA {nome.upper()} ---\nTítulos ({len(titulos)}): {', '.join(titulos) or 'nenhum'}\n"
            "Melhores temporadas (saldo de pontos/net rating): " + "; ".join(f"{r.SEASON} ({r.W}-{r.L}, {r.S:+.1f})" for r in melhores.itertuples()))


def pacote_decada(aw, ts, d, compacto=False):
    ss = _seasons_decada(d)
    linhas = []
    for s in ss:
        c = _awd(aw, "campeao", [s])
        camp = c.TEAM.mode().iat[0] if len(c) else "?"
        mvp = ", ".join(_awd(aw, "mvp", [s]).PLAYER.unique()) or "?"
        linhas.append(f"{s}: Campeão = {camp} (jogadores campeões na base: {', '.join(c.PLAYER.head(6))}) | MVP da temporada = {mvp}")
    out = f"=== DÉCADA {d}s (temporadas {ss[0]} a {ss[-1]}) ===\n" + "\n".join(linhas)
    return out if compacto else out + "\n" + "\n".join(_times(ts, ss, 8))


def ranking_texto(df, pos=None, so_playoffs=False):
    crit = ("critério de playoffs: SOMENTE títulos (×3) e MVP das Finais (×6)" if so_playoffs else
            "critério: pontos de legado (MVP×10, MVP das Finais×6, títulos×3, Defensor do Ano×3, All-NBA 1º/2º/3º time ×4/2,5/1,5, All-Defensive×1, All-Star×0,5)")
    filtro = {"PG": " Lista já filtrada: apenas armadores (guards com perfil de armador: ao menos 5,5 assistências por jogo na carreira; a base só informa 'Guard', então é uma aproximação).",
              "SG": " Lista já filtrada: guards sem perfil de armador (ala-armadores).",
              "F": " Lista já filtrada: alas e ala-pivôs.", "C": " Lista já filtrada: pivôs."}.get(pos, "")
    linhas = [f"{i}. {r.Jogador}: {r.Pontos:.1f} pts (títulos {r['Títulos']}, MVP {r.MVP}, MVP das Finais {r.FMVP}, DPOY {r.DPOY}, All-NBA {r['All-NBA']}, All-Star {r['All-Star']})"
              for i, (_, r) in enumerate(df.iterrows(), 1)]
    return f"RANKING CALCULADO (ordem obrigatória; {crit}).{filtro}\n" + "\n".join(linhas)


def construir_contexto(pergunta, ctx_anterior=""):
    """Retorna (contexto, modo) com modo 'fato' ou 'debate'."""
    modo = "debate" if re.search(r"\b(melhor|melhores|maior|maiores|mais forte|top|ranking|goat|dificil|vs|x|quem foi|quinteto|ideal|dominante)\b", norm(pergunta)) else "fato"
    seasons, decs = extrair_periodos(pergunta)
    alvo = seasons + [s for d in decs for s in _seasons_decada(d)]
    achados, nq = reconhecer(pergunta)
    pos = detectar_posicao(nq)
    so_po = bool(re.search(r"playoff|finais|mata mata|mata-mata", nq))
    tm = next((t for t in teams.get_teams() if re.search(rf"\b{norm(t['nickname'])}\b", nq)), None)
    aw, ts, idx = _csv("awards.csv"), _csv("team_seasons.csv"), _csv("players_index.csv")
    pts, ps, pp = _csv("player_team_seasons.csv"), _csv("playoff_series.csv"), _csv("player_playoffs.csv")
    if aw is not None and achados and not alvo and re.search(r"ano em que|temporada em que|quando (?:foi|ganhou|venceu|conquistou)|naquele ano|nessa temporada|naquela temporada", nq):
        for rx, k in PREMIO_PALAVRAS:  # "no ano em que foi MVP" -> temporadas em que o jogador ganhou o prêmio
            if re.search(rx, nq):
                ss = sorted(set(_awd(aw[aw.PERSON_ID == achados[0]["id"]], k).SEASON))[-3:]
                if ss:
                    seasons, alvo = ss, ss
                break
    partes = []
    if aw is None or ts is None:
        if seasons or decs or achados:
            partes.append("AVISO: base local ausente (rode scripts/build_data.py). Não invente dados de prêmios.")
    else:
        compacto = bool(achados)
        if seasons and not decs:
            partes += [pacote_temporada(aw, ts, s, ps, compacto, pts, pp) for s in seasons[:3]]
        for d in decs[:2]:
            partes.append(pacote_decada(aw, ts, d, compacto))
        for p in achados[:4]:
            partes.append(ficha_jogador(aw, pts, idx, p["id"], alvo or None, pp=pp, ts=ts, ps=ps))
        if tm:
            partes.append(pacote_time(aw, ts, tm["id"], tm["full_name"]))
        if modo == "debate" and (pos or tm or decs or seasons or not achados):
            df = pontuar(aw, idx, alvo or None, pos, tm["id"] if tm else None, pts, so_po).head(10)
            if len(df):
                partes.append(ranking_texto(df, pos, so_po))
                partes += [ficha_jogador(aw, pts, idx, int(i), alvo or None, curta=True) for i in df.ID.head(8) if i not in {p["id"] for p in achados}]
            if ps is not None and re.search(r"dificil|trajetoria|caminho", nq):
                cc = caminhos_campeoes(aw, ts, ps)
                cc = cc[cc["Temporada"].isin(alvo)] if alvo else cc
                partes.append("Caminhos de título mais difíceis (força média dos adversários nos playoffs): " + "; ".join(
                    f"{r.Temporada} {r['Campeão']} (adv. {r['Win% médio adv.']:.0f}% vitórias, saldo médio {r['Saldo médio adv.']:+.1f}; {r['Caminho']})" for _, r in cc.head(8).iterrows()))
    if ctx_anterior and (not partes or re.search(r"ordem|ranking|criterio|pontos|lista|esses|essas|acima|anterior|resum", nq)):
        partes.append("[CONTEXTO DA PERGUNTA ANTERIOR, para acompanhamento]\n" + ctx_anterior[:2500])
    return "\n\n".join(partes) or "SEM DADOS ESPECÍFICOS: responda só com conhecimento geral seguro e avise que não há dados verificados.", modo


def _atribuir(d, pts):
    """Liga cada prêmio ao time em que o jogador mais atuou na temporada."""
    base = pts.sort_values("GP", ascending=False).drop_duplicates(["PERSON_ID", "SEASON"])[["PERSON_ID", "SEASON", "TEAM_ID"]]
    return d.merge(base, on=["PERSON_ID", "SEASON"], how="left")


def detectar_posicao(nq):
    for rx, cod in POSICOES:
        if re.search(rx, nq):
            return cod
    return None


def ids_posicao(idx, pts, pos):
    """Jogadores da posição pedida. Armador vs ala-armador é inferido pelo perfil de assistências na carreira."""
    if idx is None or not pos:
        return None
    pp = idx.POSITION.fillna("")
    if pos in ("PG", "SG"):
        guards = set(idx[pp.str.contains("G")].PERSON_ID.astype(int))
        if pts is None:
            return guards
        c = pts.groupby("PERSON_ID").agg(GP=("GP", "sum"), PTS=("PTS", "sum"), AST=("AST", "sum"))
        c = c[c.GP >= 200]
        pg = {int(i) for i in c[(c.AST / c.GP >= 5.5) & (c.AST / c.PTS >= 0.22)].index}
        return (guards & pg) if pos == "PG" else (guards - pg)
    return set(idx[pp.str.contains("C" if pos == "C" else "F")].PERSON_ID.astype(int))


def pontuar(aw, idx, seasons=None, pos=None, time_id=None, pts=None, so_playoffs=False):
    """Tabela de pontos de legado por jogador (aba Rankings e chat)."""
    d = aw[aw.SEASON.isin(seasons)] if seasons else aw
    com_time = time_id is not None and pts is not None
    if com_time:
        d = _atribuir(d, pts)
        d = d[d.TEAM_ID == time_id]
    rows = {}
    for k, w in (PESOS_PLAYOFFS if so_playoffs else PESOS).items():
        for _, r in _awd(d, k).iterrows():
            v = rows.setdefault(int(r.PERSON_ID), {"Jogador": r.PLAYER, "pontos": 0.0, **{c: 0 for c in PESOS}})
            v[k] += 1
            if k == "allnba":
                n = int(r.ALL_NBA_TEAM_NUMBER) if pd.notna(r.ALL_NBA_TEAM_NUMBER) else 3
                v["pontos"] += {1: 4, 2: 2.5}.get(n, 1.5)
            else:
                v["pontos"] += w
    if com_time:  # todos os jogadores que passaram pelo time, não só quem tem prêmio
        t = pts[pts.TEAM_ID == time_id]
        if seasons:
            t = t[t.SEASON.isin(seasons)]
        g = t.groupby("PERSON_ID").agg(Nome=("PLAYER_NAME", "first"), Temporadas=("SEASON", "nunique"),
                                       PTS=("PTS", "sum"), REB=("REB", "sum"), AST=("AST", "sum"))
        for pid, r in g.iterrows():
            v = rows.setdefault(int(pid), {"Jogador": r.Nome, "pontos": 0.0, **{c: 0 for c in PESOS}})
            v["pontos"] += r.Temporadas * 0.5 + (r.PTS or 0) / 2000
            v.update(Temporadas=int(r.Temporadas), PTS=int(r.PTS or 0), REB=int(r.REB or 0), AST=int(r.AST or 0))
    df = pd.DataFrame.from_dict(rows, orient="index")
    if df.empty:
        return df
    ids = ids_posicao(idx, pts, pos)
    if ids is not None:
        df = df[df.index.isin(ids)]
    df = df.sort_values("pontos", ascending=False).rename_axis("ID").reset_index().rename(columns={
        "pontos": "Pontos", "mvp": "MVP", "fmvp": "FMVP", "campeao": "Títulos", "dpoy": "DPOY",
        "allnba": "All-NBA", "alldef": "All-Def", "allstar": "All-Star"})
    return df


def caminho(aw, ts, ps, s):
    """Séries de playoffs do campeão da temporada s, em ordem."""
    camp = _awd(aw, "campeao", [s])
    if camp.empty or "TEAM_ID" not in ts:
        return []
    d = ts[ts.SEASON == s].assign(PCT=lambda x: x.W / (x.W + x.L), SALDO=lambda x: x.NRTG.fillna(x.DIFF))
    t = d[d.TEAM == camp.TEAM.mode().iat[0]]
    if t.empty:
        return []
    tid = int(t.TEAM_ID.iat[0])
    m = ps[(ps.SEASON == s) & ((ps.TEAM_A_ID == tid) | (ps.TEAM_B_ID == tid))].sort_values("FIRST_DATE")
    out = []
    for r in m.itertuples():
        a = r.TEAM_A_ID == tid
        oid = int(r.TEAM_B_ID if a else r.TEAM_A_ID)
        o = d[d.TEAM_ID == oid]
        out.append(dict(adv=r.TEAM_B if a else r.TEAM_A, adv_id=oid, res=f"{r.WINS_A if a else r.WINS_B}-{r.WINS_B if a else r.WINS_A}",
                        pct=float(o.PCT.iat[0]) if len(o) else float("nan"), saldo=float(o.SALDO.iat[0]) if len(o) else float("nan"),
                        camp_id=tid))
    return out


def caminhos_campeoes(aw, ts, ps):
    linhas = []
    for s in sorted(_awd(aw, "campeao").SEASON.unique()):
        cm = [c for c in caminho(aw, ts, ps, s) if c["pct"] == c["pct"]]
        if not cm:
            continue
        camp = _awd(aw, "campeao", [s]).TEAM.mode().iat[0]
        linhas.append({"Temporada": s, "Campeão": camp, "Séries": len(cm),
                       "Win% médio adv.": sum(c["pct"] for c in cm) / len(cm) * 100,
                       "Saldo médio adv.": sum(c["saldo"] for c in cm) / len(cm),
                       "Caminho": " → ".join(f"{c['adv']} {c['res']}" for c in cm)})
    return pd.DataFrame(linhas).sort_values("Saldo médio adv.", ascending=False)


def entidades_visuais(pergunta):
    """Jogadores e times citados na pergunta (para mostrar foto e logo no chat)."""
    achados, nq = reconhecer(pergunta)
    tms = [t for t in teams.get_teams() if re.search(rf"\b{norm(t['nickname'])}\b", nq)]
    return achados[:3], tms[:3]
