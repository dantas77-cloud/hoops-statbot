import re
from utils.config import flag

# Logos e fotos são marcas/imagens de terceiros (NBA e franquias). Por padrão o app NÃO as carrega.
# Uso pessoal e local: defina EXIBIR_IMAGENS_NBA=1 (veja AVISO_LEGAL.md).
IMAGENS_ATIVAS = flag("EXIBIR_IMAGENS_NBA", "0")


def logo_url(tid):
    return f"https://cdn.nba.com/logos/nba/{int(tid)}/global/L/logo.svg"


def foto_url(pid):
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{int(pid)}.png"


def times_do_jogador(pid, pts=None, hist=None):
    """IDs dos times por onde o jogador passou, em ordem. Usa a base local; se faltar, usa o histórico da API."""
    if pts is not None:
        d = pts[pts.PERSON_ID == pid].sort_values("SEASON")
        ids = list(dict.fromkeys(int(t) for t in d.TEAM_ID.dropna()))
        if ids:
            return ids
    out = []
    if hist:
        from nba_api.stats.static import teams
        ab = {t["abbreviation"]: t["id"] for t in teams.get_teams()}
        for h in hist:
            m = re.search(r"\((\w+)\)", h)
            if m and m.group(1) in ab and ab[m.group(1)] not in out:
                out.append(ab[m.group(1)])
    return out
