#!/usr/bin/env python3
"""Publica como STORY, em ordem, os itens de stories.json sem "publicado". 04/10/2026 (destaques do perfil).
Só por disparo manual (workflow "Publicar stories"). O Paulo vê a folha antes."""
import json, os, time, urllib.parse, urllib.request
API = "https://graph.instagram.com/v21.0"; TOK = os.environ["IG_TOKEN"]; UID = os.environ["IG_USER_ID"]
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
def chamar(url, dados=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode() if dados else None)
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: print("ERRO:", e.code, e.read().decode()[:400]); raise
d = json.load(open("stories.json"))
for it in d["stories"]:
    if it.get("publicado"): continue
    if it.get("release"):  # vídeo: fica no release "videos"
        url = f"https://github.com/{REPO}/releases/download/videos/{urllib.parse.quote(it['arquivo'])}"
        c = chamar(f"{API}/{UID}/media", {"video_url": url, "media_type": "STORIES", "access_token": TOK})
    else:
        url = f"https://raw.githubusercontent.com/{REPO}/main/stories/{urllib.parse.quote(it['arquivo'])}"
        c = chamar(f"{API}/{UID}/media", {"image_url": url, "media_type": "STORIES", "access_token": TOK})
    for _ in range(60):
        st = chamar(f"{API}/{c['id']}?fields=status_code&access_token={TOK}").get("status_code")
        if st == "FINISHED": break
        time.sleep(3)
    time.sleep(3)
    p = chamar(f"{API}/{UID}/media_publish", {"creation_id": c["id"], "access_token": TOK})
    it["publicado"] = time.strftime("%Y-%m-%d %H:%M"); it["media_id"] = p["id"]
    json.dump(d, open("stories.json", "w"), ensure_ascii=False, indent=1)
    print("STORY", it["arquivo"], p["id"]); time.sleep(4)
