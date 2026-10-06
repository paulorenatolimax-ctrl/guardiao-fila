#!/usr/bin/env python3
"""Pulso do Instagram, de hora em hora (06/10/2026, pedido do Paulo: o Studio analisa os dados SEMPRE em tempo real).

Leve de propósito: só os posts dos últimos 10 dias (+ seguidores). Guarda uma série por post
(hora, views, shares, saved...) para medir VELOCIDADE (views/hora), que é o que importa
(regra do Paulo: ranquear por velocidade, não por total).

Lê o pulso anterior de pulso_prev.json (o workflow baixa do branch `pulso`) e grava pulso.json.
Só leitura na API do Instagram.
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.instagram.com/v21.0"
TOK, UID = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
DIAS = 10
PONTOS = 60          # pontos guardados por post (60 horas de série fina; o resto fica no total)


def get(url):
    return json.load(urllib.request.urlopen(url, timeout=60))


def main():
    agora = datetime.now(timezone.utc)
    corte = agora - timedelta(days=DIAS)
    prev = {}
    if os.path.exists("pulso_prev.json"):
        try:
            prev = {p["id"]: p for p in json.load(open("pulso_prev.json")).get("posts", [])}
        except Exception:
            prev = {}
    conta = get(f"{API}/{UID}?fields=followers_count,media_count&access_token={TOK}")
    posts, url = [], (f"{API}/{UID}/media?fields=id,caption,media_product_type,timestamp,permalink,like_count,comments_count"
                      f"&limit=50&access_token={TOK}")
    fim = False
    while url and not fim:
        d = get(url)
        for m in d.get("data", []):
            ts = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
            if ts < corte:
                fim = True
                break
            ponto = {"t": agora.strftime("%Y-%m-%dT%H:%MZ"), "likes": m.get("like_count"), "comentarios": m.get("comments_count")}
            for metr in ("views,reach,saved,shares,total_interactions", "reach,saved,shares,total_interactions"):
                try:
                    ins = get(f"{API}/{m['id']}/insights?metric={metr}&access_token={TOK}")
                    for x in ins.get("data", []):
                        ponto[x["name"]] = x["values"][0]["value"]
                    break
                except Exception as e:
                    ponto["erro"] = str(e)[:60]
            serie = (prev.get(m["id"], {}).get("serie") or [])[-(PONTOS - 1):] + [ponto]
            posts.append({"id": m["id"], "timestamp": m["timestamp"], "tipo": m.get("media_product_type"),
                          "permalink": m.get("permalink"), "legenda": (m.get("caption") or "")[:220],
                          "serie": serie})
        url = d.get("paging", {}).get("next")
    hist = []
    if os.path.exists("pulso_prev.json"):
        try:
            hist = json.load(open("pulso_prev.json")).get("seguidores_hora", [])
        except Exception:
            hist = []
    hist = (hist + [{"t": agora.strftime("%Y-%m-%dT%H:%MZ"), "seguidores": conta.get("followers_count")}])[-24 * 14:]
    json.dump({"gerado_em": agora.strftime("%Y-%m-%dT%H:%MZ"), "seguidores": conta.get("followers_count"),
               "total_posts": conta.get("media_count"), "seguidores_hora": hist, "posts": posts},
              open("pulso.json", "w"), ensure_ascii=False, indent=0)
    print(len(posts), "posts no pulso;", conta.get("followers_count"), "seguidores")


if __name__ == "__main__":
    main()
