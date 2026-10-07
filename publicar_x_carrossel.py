#!/usr/bin/env python3
"""Posta no X (@PauloLima1844) o carrossel que acabou de sair no Instagram. 06/10/2026.

O X aceita até 4 imagens por post, então o carrossel vira um fio: o 1º post leva o título e as
lâminas 1-4, as respostas levam as seguintes de 4 em 4. Nunca derruba a fila: falha só avisa.
Pega o último item de carrosseis.json com "publicado" e sem "x_id".
"""
import json, os, sys, urllib.parse, urllib.request
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
K = [os.environ.get(k, "") for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")]
if not all(K):
    print("X: chaves ausentes nos secrets — pulando (a fila segue normal)."); sys.exit(0)
from requests_oauthlib import OAuth1Session
x = OAuth1Session(K[0], client_secret=K[1], resource_owner_key=K[2], resource_owner_secret=K[3])

dados = json.load(open("carrosseis.json"))
alvo = [i for i in dados["carrosseis"] if i.get("publicado") and not i.get("x_id") and not i.get("x_pular")]
# 07/10/2026: só o que saiu nas últimas 6 h — sem isso, a cada execução (5 em 5 min) ele postava um antigo.
import datetime as _dt
_lim = (_dt.datetime.utcnow() - _dt.timedelta(hours=6)).strftime("%Y-%m-%d %H:%M")   # "publicado" é gravado em UTC
alvo = [i for i in alvo if str(i.get("publicado", "")) >= _lim]
if not alvo: print("X: nada novo para postar."); sys.exit(0)
item = alvo[-1]   # só o mais recente: não despeja atrasados de uma vez


def curto(t, n=270):
    t = " ".join(t.split())
    return t if len(t) <= n else t[:n - 3].rsplit(" ", 1)[0] + "…"


base = f"https://raw.githubusercontent.com/{REPO}/main/carrosseis/"
ids = []
for s in item["slides"]:
    img = urllib.request.urlopen(base + urllib.parse.quote(s), timeout=60).read()
    r = x.post("https://api.x.com/2/media/upload", data={"media_category": "tweet_image", "media_type": "image/jpeg"},
               files={"media": (s, img, "image/jpeg")})
    if r.status_code >= 300: print("X: erro ao subir lâmina", s, r.status_code, r.text[:300]); sys.exit(0)
    ids.append(r.json()["data"]["id"])

grupos = [ids[i:i + 4] for i in range(0, len(ids), 4)]
texto1 = curto(item.get("titulo") or item.get("legenda", "").split("\n\n")[0])
anterior, primeiro = None, None
for k, g in enumerate(grupos):
    txt = texto1 if k == 0 else f"{k + 1}/{len(grupos)}"
    corpo = {"text": txt, "media": {"media_ids": g}}
    if anterior: corpo["reply"] = {"in_reply_to_tweet_id": anterior}
    r = x.post("https://api.x.com/2/tweets", json=corpo)
    if r.status_code >= 300:
        print("X: erro ao postar parte", k + 1, r.status_code, r.text[:300])
        if not primeiro: sys.exit(0)
        break
    anterior = r.json()["data"]["id"]; primeiro = primeiro or anterior

print(f"  PUBLICADO NO X (carrossel {item.get('id')}): https://x.com/PauloLima1844/status/{primeiro}")
item["x_id"] = primeiro
json.dump(dados, open("carrosseis.json", "w"), ensure_ascii=False, indent=2); open("carrosseis.json", "a").write("\n")
