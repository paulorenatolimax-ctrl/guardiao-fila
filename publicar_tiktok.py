#!/usr/bin/env python3
"""Publica o Reel mais recente da fila no TikTok (@paulo1844x) pela Content Posting API.

Nunca derruba a fila: qualquer falha sai com código 0 e só avisa no log.
Pega o item mais recente de fila.json com "publicado" e sem "tt_id" (não despeja atrasados).

Modos (variável TIKTOK_MODO):
- "rascunho" (padrão enquanto o app não passou na auditoria do TikTok): o vídeo cai na
  caixa de entrada do app do TikTok; o Paulo abre e toca em Postar.
- "direto": posta direto no perfil. Antes da auditoria o TikTok só aceita SELF_ONLY (privado).

Secrets: TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET, TIKTOK_REFRESH_TOKEN (vale 365 dias, criado em 06/10/2026).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

KEY = os.environ.get("TIKTOK_CLIENT_KEY", "")
SECRET = os.environ.get("TIKTOK_CLIENT_SECRET", "")
REFRESH = os.environ.get("TIKTOK_REFRESH_TOKEN", "")
MODO = os.environ.get("TIKTOK_MODO", "rascunho")
PRIVACIDADE = os.environ.get("TIKTOK_PRIVACIDADE", "SELF_ONLY")
REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
TAG = os.environ.get("RELEASE_TAG", "videos")
API = "https://open.tiktokapis.com/v2"

if not (KEY and SECRET and REFRESH):
    print("TikTok: chaves ausentes nos secrets — pulando (a fila segue normal)."); sys.exit(0)


def chamar(url, corpo=None, headers=None, form=False, metodo=None):
    h = dict(headers or {})
    if corpo is not None and form:
        dados = urllib.parse.urlencode(corpo).encode(); h["Content-Type"] = "application/x-www-form-urlencoded"
    elif corpo is not None:
        dados = json.dumps(corpo).encode(); h["Content-Type"] = "application/json; charset=UTF-8"
    else:
        dados = None
    req = urllib.request.Request(url, data=dados, headers=h, method=metodo)
    try:
        return json.load(urllib.request.urlopen(req, timeout=180))
    except urllib.error.HTTPError as e:
        print("ERRO TikTok:", e.code, e.read().decode()[:500]); raise


def sair(msg):
    print("TikTok:", msg); sys.exit(0)


dados = json.load(open("fila.json"))
alvo = [i for i in dados["fila"] if i.get("publicado") and not i.get("tt_id") and not i.get("tt_pular")]
if not alvo:
    sair("nada novo para postar.")
item = alvo[-1]

try:
    tok = chamar(f"{API}/oauth/token/", {"client_key": KEY, "client_secret": SECRET,
                                         "grant_type": "refresh_token", "refresh_token": REFRESH}, form=True)
except Exception as e:
    sair(f"não consegui renovar o token ({str(e)[:120]}) — refazer a autorização (manual §10).")
ACESSO = tok.get("access_token")
if not ACESSO:
    sair(f"renovação sem access_token: {str(tok)[:200]}")
if tok.get("refresh_token") and tok["refresh_token"] != REFRESH:
    print("TikTok: AVISO — o refresh token mudou; atualizar o secret TIKTOK_REFRESH_TOKEN (manual §10).")
AUT = {"Authorization": f"Bearer {ACESSO}"}

url_video = f"https://github.com/{REPO}/releases/download/{TAG}/{urllib.parse.quote(item['asset'])}"
local = f"/tmp/tt_{item['n']}.mp4"
print(f"TikTok: baixando {url_video}")
urllib.request.urlretrieve(url_video, local)
tam = os.path.getsize(local)

# Pedaços: 5-64 MB cada; o último pode passar um pouco. Abaixo de 64 MB, um pedaço só.
PEDACO = tam if tam <= 64 * 1024 * 1024 else 10 * 1024 * 1024
n_pedacos = max(1, tam // PEDACO)
fonte = {"source": "FILE_UPLOAD", "video_size": tam, "chunk_size": PEDACO, "total_chunk_count": n_pedacos}

try:
    if MODO == "direto":
        info = chamar(f"{API}/post/publish/creator_info/query/", {}, AUT)
        opcoes = info.get("data", {}).get("privacy_level_options", [])
        priv = PRIVACIDADE if PRIVACIDADE in opcoes else (opcoes[0] if opcoes else "SELF_ONLY")
        titulo = (item.get("titulo_shorts") or item.get("legenda", ""))[:150]
        legenda = item.get("legenda", "")
        corpo = {"post_info": {"title": (titulo + "\n\n" + legenda)[:2200], "privacy_level": priv,
                               "disable_comment": False, "disable_duet": False, "disable_stitch": False},
                 "source_info": fonte}
        ini = chamar(f"{API}/post/publish/video/init/", corpo, AUT)
    else:
        ini = chamar(f"{API}/post/publish/inbox/video/init/", {"source_info": fonte}, AUT)
except Exception as e:
    sair(f"init falhou: {str(e)[:200]}")

d = ini.get("data", {})
up, pid = d.get("upload_url"), d.get("publish_id")
if not up:
    sair(f"init sem upload_url: {str(ini)[:300]}")

with open(local, "rb") as f:
    for k in range(n_pedacos):
        ini_b = k * PEDACO
        fim_b = tam - 1 if k == n_pedacos - 1 else ini_b + PEDACO - 1
        f.seek(ini_b); bloco = f.read(fim_b - ini_b + 1)
        req = urllib.request.Request(up, data=bloco, method="PUT", headers={
            "Content-Type": "video/mp4", "Content-Length": str(len(bloco)),
            "Content-Range": f"bytes {ini_b}-{fim_b}/{tam}"})
        try:
            urllib.request.urlopen(req, timeout=600)
        except urllib.error.HTTPError as e:
            if e.code not in (200, 201, 206):
                sair(f"upload do pedaço {k + 1}/{n_pedacos} falhou: {e.code} {e.read().decode()[:200]}")

item["tt_id"] = pid
item["tt_modo"] = MODO
json.dump(dados, open("fila.json", "w"), indent=2, ensure_ascii=False)
open("fila.json", "a").write("\n")
print(f"ENVIADO AO TIKTOK ({MODO}): publish_id {pid} — Reel {item['n']}")
