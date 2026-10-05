#!/usr/bin/env python3
"""Mostra a cota de publicação pela API (janela móvel de 24 h). 05/10/2026."""
import json, os, urllib.request
TOK, UID = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
for v in ("v21.0",):
    try:
        d = json.load(urllib.request.urlopen(f"https://graph.instagram.com/{v}/{UID}/content_publishing_limit?fields=config,quota_usage&access_token={TOK}", timeout=60))
        print("COTA:", json.dumps(d))
    except urllib.error.HTTPError as e: print("ERRO", e.code, e.read().decode()[:300])
