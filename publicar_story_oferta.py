#!/usr/bin/env python3
"""Story de oferta diario (19h BRT). 14/10/2026. Reposta stories/<arquivo> 1x por dia.
Desligado por padrao: so publica se story_oferta.json tiver ativo=true e pendente_ok_do_paulo=false.
A API de stories nao aceita link sticker; a imagem diz 'link na bio'."""
import json, os, time, urllib.parse, urllib.request
cfg = json.load(open("story_oferta.json"))
if not cfg.get("ativo") or cfg.get("pendente_ok_do_paulo"):
    print("story de oferta DESLIGADO (pendente de OK do Paulo); nada publicado"); raise SystemExit(0)
hoje = time.strftime("%Y-%m-%d")
if (cfg.get("ultimo_publicado") or "").startswith(hoje):
    print("ja publicado hoje"); raise SystemExit(0)
API = "https://graph.instagram.com/v21.0"; TOK = os.environ["IG_TOKEN"]; UID = os.environ["IG_USER_ID"]
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
def chamar(url, dados=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode() if dados else None)
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: print("ERRO:", e.code, e.read().decode()[:400]); raise
url = f"https://raw.githubusercontent.com/{REPO}/main/stories/{urllib.parse.quote(cfg['arquivo'])}"
c = chamar(f"{API}/{UID}/media", {"image_url": url, "media_type": "STORIES", "access_token": TOK})
for _ in range(60):
    if chamar(f"{API}/{c['id']}?fields=status_code&access_token={TOK}").get("status_code") == "FINISHED": break
    time.sleep(3)
p = chamar(f"{API}/{UID}/media_publish", {"creation_id": c["id"], "access_token": TOK})
cfg["ultimo_publicado"] = time.strftime("%Y-%m-%d %H:%M"); cfg["media_id"] = p["id"]
json.dump(cfg, open("story_oferta.json", "w"), ensure_ascii=False, indent=1)
print("STORY OFERTA", p["id"])
