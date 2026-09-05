#!/usr/bin/env python3
"""Confere que TODO vídeo pendente tem asset acessível no GitHub.

Roda antes de publicar. Se algum link estiver quebrado, falha ANTES de tentar
publicar — e diz exatamente qual. Existe porque em 05/09/2026 os 23 vídeos da
fila apontavam para URLs inexistentes e o sistema ficou dois dias falhando em
silêncio, com o dono achando que estava publicando.
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error

REPO = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
TAG  = os.environ.get("RELEASE_TAG", "videos")
fila = json.load(open("fila.json"))["fila"]
pend = [x for x in fila if not x.get("publicado")]

print(f"conferindo {len(pend)} vídeos pendentes…")
quebrados = []
for it in pend:
    url = f"https://github.com/{REPO}/releases/download/{TAG}/{urllib.parse.quote(it['asset'])}"
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=45)
        mb = int(r.headers.get("content-length", 0)) / 1e6
        if mb < 1: quebrados.append((it["n"], it["asset"], f"tamanho suspeito: {mb:.1f} MB"))
    except urllib.error.HTTPError as e:
        quebrados.append((it["n"], it["asset"], f"HTTP {e.code}"))
    except Exception as e:
        quebrados.append((it["n"], it["asset"], str(e)[:60]))

if quebrados:
    print(f"\n❌ {len(quebrados)} VÍDEO(S) COM LINK QUEBRADO:")
    for n, a, m in quebrados:
        print(f"   vídeo {n}: {a} → {m}")
    print("\nA fila NÃO vai publicar até isso ser corrigido.")
    sys.exit(1)

print(f"✅ os {len(pend)} pendentes estão acessíveis")
print(f"   próximo: vídeo {pend[0]['n']} · autonomia {len(pend)/3:.1f} dias")
