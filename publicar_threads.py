#!/usr/bin/env python3
"""Posta no Threads (@prof.paulolima1844) o Reel ou o carrossel que acabou de sair no Instagram. 07/10/2026.

Uso: python3 publicar_threads.py reel|carrossel
Nunca derruba a fila: qualquer falha só avisa e sai com 0.
Pega o item mais recente com "publicado" (UTC) nas últimas 6 h e sem "th_id".
Secret: THREADS_TOKEN (token de longa duração, 60 dias; renovar — manual §12).
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

TIPO = sys.argv[1] if len(sys.argv) > 1 else "reel"
TOK = os.environ.get("THREADS_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
TAG = os.environ.get("RELEASE_TAG", "videos")
API = "https://graph.threads.net/v1.0"
if not TOK:
    print("Threads: THREADS_TOKEN ausente nos secrets — pulando (a fila segue normal)."); sys.exit(0)


def sair(msg):
    print("Threads:", msg); sys.exit(0)


def chamar(caminho, dados=None, metodo="POST"):
    dados = dict(dados or {}, access_token=TOK)
    if metodo == "GET":
        req = urllib.request.Request(f"{API}/{caminho}?{urllib.parse.urlencode(dados)}")
    else:
        req = urllib.request.Request(f"{API}/{caminho}", data=urllib.parse.urlencode(dados).encode())
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sair(f"erro {e.code} em {caminho}: {e.read().decode()[:400]}")


def esperar(cid, limite=600):
    t0 = time.time()
    while time.time() - t0 < limite:
        st = chamar(cid, {"fields": "status,error_message"}, "GET")
        if st.get("status") == "FINISHED": return
        if st.get("status") in ("ERROR", "EXPIRED"): sair(f"container {cid} falhou: {st}")
        time.sleep(10)
    sair(f"container {cid} não terminou em {limite} s")


def texto(item):
    t = (item.get("legenda") or item.get("titulo") or "").strip()
    return t if len(t) <= 500 else t[:497].rsplit(" ", 1)[0] + "…"


arq, chave = ("fila.json", "fila") if TIPO == "reel" else ("carrosseis.json", "carrosseis")
dados = json.load(open(arq))
lim = (dt.datetime.utcnow() - dt.timedelta(hours=6)).strftime("%Y-%m-%d %H:%M")
alvo = [i for i in dados[chave] if i.get("publicado") and str(i["publicado"]) >= lim
        and not i.get("th_id") and not i.get("th_pular")]
if not alvo: sair("nada novo para postar.")
item = alvo[-1]

if TIPO == "reel":
    url = f"https://github.com/{REPO}/releases/download/{TAG}/{urllib.parse.quote(item['asset'])}"
    cid = chamar("me/threads", {"media_type": "VIDEO", "video_url": url, "text": texto(item)})["id"]
    esperar(cid)
else:
    base = f"https://raw.githubusercontent.com/{REPO}/main/carrosseis/"
    filhos = []
    for s in item["slides"][:20]:
        f = chamar("me/threads", {"media_type": "IMAGE", "image_url": base + urllib.parse.quote(s), "is_carousel_item": "true"})["id"]
        filhos.append(f)
    for f in filhos: esperar(f, 180)
    cid = chamar("me/threads", {"media_type": "CAROUSEL", "children": ",".join(filhos), "text": texto(item)})["id"]
    esperar(cid, 180)

pub = chamar("me/threads_publish", {"creation_id": cid})
item["th_id"] = pub.get("id")
json.dump(dados, open(arq, "w"), ensure_ascii=False, indent=2); open(arq, "a").write("\n")
print(f"PUBLICADO NO THREADS ({TIPO}): {item['th_id']}")
