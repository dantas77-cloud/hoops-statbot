# Pasta de dados

Esta pasta fica **vazia no repositório de propósito**: os dados da NBA não são redistribuídos aqui.
Gere-os localmente (uma vez):

```bash
python scripts/build_data.py
python scripts/build_extra.py
python scripts/verificar_dados.py   # opcional: relatório de qualidade
```

Arquivos gerados (todos ignorados pelo Git): `awards.csv`, `team_seasons.csv`, `players_index.csv`,
`player_team_seasons.csv`, `player_playoffs.csv`, `playoff_series.csv` e `conversas.json` (histórico do chat).
Os dados vêm de NBA.com via `nba_api` e estão sujeitos aos Termos de Uso do NBA.com (veja `AVISO_LEGAL.md`).
