#!/usr/bin/env python3
"""Registra os seguidores do perfil 1x por dia (23h55 BRT) em stats.json -> "diario". 04/10/2026, pedido do Paulo."""
import json, os, urllib.request
from datetime import datetime, timedelta, timezone
TOK, UID = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
d = json.load(urllib.request.urlopen(f"https://graph.instagram.com/v21.0/{UID}?fields=followers_count,media_count&access_token={TOK}", timeout=60))
brt = datetime.now(timezone.utc) - timedelta(hours=3)
stats = json.load(open("stats.json")) if os.path.exists("stats.json") else {"historico": []}
diario = stats.setdefault("diario", [])
diario = [x for x in diario if x["data"] != f"{brt:%Y-%m-%d}"]
ant = diario[-1]["seguidores"] if diario else None
diario.append({"data": f"{brt:%Y-%m-%d}", "hora_brt": f"{brt:%H:%M}", "seguidores": d["followers_count"], "posts": d.get("media_count"),
               "ganho_dia": (d["followers_count"] - ant) if ant is not None else None})
stats["diario"] = diario
json.dump(stats, open("stats.json", "w"), ensure_ascii=False, indent=1)
print(diario[-1])
