#!/usr/bin/env python3
"""Publica 3 carrosséis por dia: 8h, 11h e 20h BRT, com recuperação de horário perdido (ver decidir.py, 03/10/2026).
Fila própria: carrosseis.json (slides JPEG no release "videos"). A API não põe música."""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
API = "https://graph.instagram.com/v21.0"; TOK = os.environ["IG_TOKEN"]; UID = os.environ["IG_USER_ID"]
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila"); TAG = "videos"
def chamar(url, dados=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode() if dados else None)
    try: return json.load(urllib.request.urlopen(req, timeout=90))
    except urllib.error.HTTPError as e: print("ERRO:", e.code, e.read().decode()[:400]); raise
brt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)
fila = json.load(open("carrosseis.json"))
# 03/10/2026: regra de recuperação (catch-up) centralizada no decidir.py
from decidir import decidir, proximo_valido
forcar = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch" and os.environ.get("FORCAR", "false") == "true"
ok, motivo = decidir("carrossel", brt, fila["carrosseis"], forcar); print(motivo)
if not ok: sys.exit(0)
c, pulos = proximo_valido(fila["carrosseis"])  # trava: carrossel com mais de 10 slides nunca é tentado
for m in pulos: print(m)
if not c: print("fila de carrosséis vazia (ou só itens inválidos)"); sys.exit(0)
print("→ carrossel", c["id"], c["titulo"])
filhos = []
for s in c["slides"]:
    url = f"https://raw.githubusercontent.com/{REPO}/main/carrosseis/{urllib.parse.quote(s)}"  # raw serve image/jpeg
    r = chamar(f"{API}/{UID}/media", {"image_url": url, "is_carousel_item": "true", "access_token": TOK}); filhos.append(r["id"])
r = chamar(f"{API}/{UID}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": c["legenda"], "access_token": TOK})
cid = r["id"]
for _ in range(30):
    s = chamar(f"{API}/{cid}?fields=status_code&access_token={TOK}")
    if s.get("status_code") == "FINISHED": break
    if s.get("status_code") == "ERROR": print("container com erro", s); sys.exit(1)
    time.sleep(5)
p = chamar(f"{API}/{UID}/media_publish", {"creation_id": cid, "access_token": TOK})
c["publicado"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"); c["media_id"] = p["id"]
json.dump(fila, open("carrosseis.json", "w"), ensure_ascii=False, indent=2)
print("  PUBLICADO CARROSSEL NO INSTAGRAM:", p["id"])
