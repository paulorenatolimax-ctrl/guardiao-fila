#!/usr/bin/env python3
"""Publica o próximo Reel da fila no Instagram, pela API oficial.

Roda no GitHub Actions. Pega o primeiro item não publicado de fila.json,
monta o container com a URL pública do asset da release, espera processar
e publica. Marca a fila e commita.

Requer os secrets IG_TOKEN e IG_USER_ID.
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta

TOK  = os.environ["IG_TOKEN"]
UID  = os.environ["IG_USER_ID"]
REPO = os.environ.get("GITHUB_REPOSITORY", "")
TAG  = os.environ.get("RELEASE_TAG", "videos")
API  = "https://graph.instagram.com/v21.0"

# Trava anti-post-duplicado: nenhum disparo (agendado ou manual) publica se o
# último post real saiu há menos disso. Protege contra reprocessar a fila
# duas vezes seguidas por engano, mesmo que alguém rode o workflow na mão.
INTERVALO_MINIMO = timedelta(hours=3)

def ultimo_publicado(fila):
    datas = [x["publicado"] for x in fila["fila"] if x.get("publicado")]
    if not datas:
        return None
    return max(datetime.strptime(d, "%Y-%m-%d %H:%M") for d in datas)

def chamar(url, dados=None):
    corpo = urllib.parse.urlencode(dados).encode() if dados else None
    req = urllib.request.Request(url, corpo, method="POST" if dados else "GET")
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode()[:500]
        raise SystemExit(f"ERRO HTTP {e.code}: {detalhe}")

def main():
    fila = json.load(open("fila.json"))

    ultimo = ultimo_publicado(fila)
    if ultimo and (datetime.utcnow() - ultimo) < INTERVALO_MINIMO:
        faltam = INTERVALO_MINIMO - (datetime.utcnow() - ultimo)
        print(f"último post foi às {ultimo} UTC, há menos de {INTERVALO_MINIMO}. "
              f"Faltam {faltam} pro próximo poder sair — abortando pra não duplicar.")
        return

    pendentes = [x for x in fila["fila"] if not x["publicado"]]
    if not pendentes:
        print("fila vazia — nada a publicar"); return

    item = pendentes[0]
    url_video = f"https://github.com/{REPO}/releases/download/{TAG}/{urllib.parse.quote(item['asset'])}"
    print(f"→ vídeo {item['n']} · {item['asset']}")
    print(f"  url: {url_video}")

    print("1/3 criando container…")
    c = chamar(f"{API}/{UID}/media", {
        "media_type": "REELS",
        "video_url": url_video,
        "caption": item["legenda"],
        "share_to_feed": "true",
        "access_token": TOK,
    })
    cid = c["id"]
    print(f"  container {cid}")

    print("2/3 aguardando processar…")
    for tentativa in range(30):          # até 15 min
        time.sleep(30)
        s = chamar(f"{API}/{cid}?fields=status_code,status&access_token={TOK}")
        estado = s.get("status_code")
        print(f"  [{tentativa+1}] {estado}")
        if estado == "FINISHED":
            break
        if estado in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container falhou: {s}")
    else:
        raise SystemExit("tempo esgotado esperando o processamento")

    print("3/3 publicando…")
    p = chamar(f"{API}/{UID}/media_publish", {"creation_id": cid, "access_token": TOK})
    print(f"  PUBLICADO: media id {p['id']}")

    item["publicado"] = time.strftime("%Y-%m-%d %H:%M")
    item["media_id"]  = p["id"]
    json.dump(fila, open("fila.json", "w"), ensure_ascii=False, indent=1)
    restam = sum(1 for x in fila["fila"] if not x["publicado"])
    print(f"restam {restam} na fila")

main()
