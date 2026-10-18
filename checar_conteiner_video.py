#!/usr/bin/env python3
"""Checa de verdade o caminho do vídeo no carrossel SEM PUBLICAR: cria os filhos (1 imagem já no main + o .mp4 do
release), espera o VÍDEO ficar FINISHED, cria o contêiner CAROUSEL e espera FINISHED. NUNCA chama media_publish
(contêiner não publicado expira sozinho em 24 h; nada aparece no perfil). 17/10/2026."""
import os, sys, json, urllib.parse, urllib.request
from carrossel_midia import criar_filhos, esperar
API = "https://graph.instagram.com/v21.0"; TOK = os.environ["IG_TOKEN"]; UID = os.environ["IG_USER_ID"]
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
SLIDES = (os.environ.get("SLIDES") or "car2409B_01.jpg,car294V_03.mp4,car2409B_02.jpg").split(",")
def chamar(url, dados=None):
    assert "media_publish" not in url, "proibido publicar neste teste"
    req = urllib.request.Request(url, data=urllib.parse.urlencode(dados).encode() if dados else None)
    try: return json.load(urllib.request.urlopen(req, timeout=90))
    except urllib.error.HTTPError as e: print("ERRO:", e.code, e.read().decode()[:400]); raise
filhos = criar_filhos(SLIDES, chamar, API, UID, TOK, REPO)
print("filhos FINISHED/OK:", filhos)
r = chamar(f"{API}/{UID}/media", {"media_type": "CAROUSEL", "children": ",".join(filhos), "caption": "teste de contêiner (não publicado)", "access_token": TOK})
s = esperar(chamar, API, TOK, r["id"])
print("RESULTADO: CAROUSEL", r["id"], s.get("status_code"), "| media_publish NÃO chamado")
