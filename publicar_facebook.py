#!/usr/bin/env python3
"""Posta na Página do Facebook o que acabou de sair no Instagram. 04/10/2026.

Uso: python3 publicar_facebook.py reel|carrossel

O compartilhamento automático do app do Instagram não pega posts feitos pela API, por isso a
fila posta direto na Página. Sem FB_PAGE_TOKEN e FB_PAGE_ID nos secrets, só avisa e sai com
sucesso: nunca derruba a fila. Pega o item mais recente com "publicado" e sem "fb_id".
- reel: sobe o vídeo do release como Reel da Página (API video_reels, com file_url);
- carrossel: sobe as imagens sem publicar e cria um post com todas elas e a legenda.
"""
import json, os, sys, time, urllib.parse, urllib.request

TIPO = sys.argv[1] if len(sys.argv) > 1 else "reel"
TOK = os.environ.get("FB_PAGE_TOKEN", ""); PAGE = os.environ.get("FB_PAGE_ID", "")
if not (TOK and PAGE):
    print("Facebook: FB_PAGE_TOKEN/FB_PAGE_ID ausentes nos secrets — pulando (a fila segue normal)."); sys.exit(0)
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
TAG = os.environ.get("RELEASE_TAG", "videos")
API = "https://graph.facebook.com/v21.0"


def chamar(url, dados=None, headers=None):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode() if dados is not None else None,
                                 headers=headers or {})
    try: return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e: print("ERRO Facebook:", e.code, e.read().decode()[:400]); raise


arq, chave = ("fila.json", "fila") if TIPO == "reel" else ("carrosseis.json", "carrosseis")
dados = json.load(open(arq))
alvo = [i for i in dados[chave] if i.get("publicado") and not i.get("fb_id") and not i.get("fb_pular")]
if not alvo: print("Facebook: nada novo para postar."); sys.exit(0)
item = alvo[-1]   # só o mais recente: não despeja atrasados de uma vez
legenda = item.get("legenda", "")

if TIPO == "reel":
    url_video = f"https://github.com/{REPO}/releases/download/{TAG}/{urllib.parse.quote(item['asset'])}"
    ini = chamar(f"{API}/{PAGE}/video_reels", {"upload_phase": "start", "access_token": TOK})
    vid = ini["video_id"]
    chamar(f"https://rupload.facebook.com/video-upload/v21.0/{vid}", {},
           {"Authorization": f"OAuth {TOK}", "file_url": url_video})
    fim = chamar(f"{API}/{PAGE}/video_reels", {"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                              "description": legenda, "access_token": TOK})
    if not fim.get("success"): print("Facebook: finish sem sucesso", fim); sys.exit(1)
    item["fb_id"] = vid
else:
    base = f"https://raw.githubusercontent.com/{REPO}/main/carrosseis/"
    fotos = []
    for s in item["slides"]:
        r = chamar(f"{API}/{PAGE}/photos", {"url": base + urllib.parse.quote(s), "published": "false", "access_token": TOK})
        fotos.append(r["id"])
    campos = {"message": legenda, "access_token": TOK}
    for k, f in enumerate(fotos): campos[f"attached_media[{k}]"] = json.dumps({"media_fbid": f})
    p = chamar(f"{API}/{PAGE}/feed", campos)
    item["fb_id"] = p["id"]

item["fb_publicado"] = time.strftime("%Y-%m-%d %H:%M")
json.dump(dados, open(arq, "w"), ensure_ascii=False, indent=1 if TIPO == "reel" else 2)
print(f"PUBLICADO NO FACEBOOK ({TIPO}): {item['fb_id']}")
