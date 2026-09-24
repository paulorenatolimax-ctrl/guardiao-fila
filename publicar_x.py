#!/usr/bin/env python3
"""Posta no X (@PauloLima1844) o Reel que acabou de sair no Instagram. 24/09/2026.

Roda depois do publicar.py. Sem as 4 chaves (X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN,
X_ACCESS_SECRET) nos secrets do repositório, só avisa e sai com sucesso: nunca derruba a fila.
Pega o último item com "publicado" e sem "x_id", baixa o vídeo do release, sobe em partes
(API de mídia v2) e publica o post com o primeiro parágrafo da legenda (≤ 280 caracteres).
"""
import json, os, sys, time, math, urllib.parse, urllib.request
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
TAG = os.environ.get("RELEASE_TAG", "videos")
K = [os.environ.get(k, "") for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")]
if not all(K):
    print("X: chaves ausentes nos secrets — pulando (a fila segue normal)."); sys.exit(0)
from requests_oauthlib import OAuth1Session
x = OAuth1Session(K[0], client_secret=K[1], resource_owner_key=K[2], resource_owner_secret=K[3])

fila = json.load(open("fila.json"))
alvo = [i for i in fila["fila"] if i.get("publicado") and not i.get("x_id")]
if not alvo: print("X: nada novo para postar."); sys.exit(0)
item = alvo[-1]   # só o mais recente: não despeja atrasados de uma vez

leg = item.get("legenda", "").split("\n\n")[0].strip()
if len(leg) > 270: leg = leg[:267].rsplit(" ", 1)[0] + "…"

url = f"https://github.com/{REPO}/releases/download/{TAG}/{urllib.parse.quote(item['asset'])}"
path = "/tmp/x_video.mp4"; urllib.request.urlretrieve(url, path)
size = os.path.getsize(path); print(f"X: vídeo {item['n']} · {size/1e6:.0f} MB")

API = "https://api.x.com/2/media/upload"
r = x.post(f"{API}/initialize", json={"media_type": "video/mp4", "total_bytes": size, "media_category": "tweet_video"})
r.raise_for_status(); mid = r.json()["data"]["id"]
CH = 4 * 1024 * 1024
with open(path, "rb") as f:
    for seg in range(math.ceil(size / CH)):
        r = x.post(f"{API}/{mid}/append", data={"segment_index": seg}, files={"media": f.read(CH)})
        if r.status_code >= 300: print(r.text); r.raise_for_status()
r = x.post(f"{API}/{mid}/finalize"); r.raise_for_status()
info = r.json().get("data", {}).get("processing_info")
while info and info.get("state") in ("pending", "in_progress"):
    time.sleep(info.get("check_after_secs", 5))
    r = x.get(API, params={"command": "STATUS", "media_id": mid}); r.raise_for_status()
    info = r.json().get("data", {}).get("processing_info")
if info and info.get("state") == "failed":
    print("X: processamento falhou:", info); sys.exit(0)   # não derruba a fila

r = x.post("https://api.x.com/2/tweets", json={"text": leg, "media": {"media_ids": [mid]}})
if r.status_code >= 300: print("X: erro ao postar:", r.status_code, r.text); sys.exit(0)
tid = r.json()["data"]["id"]; print(f"  PUBLICADO NO X: https://x.com/PauloLima1844/status/{tid}")
item["x_id"] = tid
json.dump(fila, open("fila.json", "w"), ensure_ascii=False, indent=2); open("fila.json", "a").write("\n")
