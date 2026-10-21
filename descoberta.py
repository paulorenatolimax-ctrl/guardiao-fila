#!/usr/bin/env python3
"""21/10/2026 — Modelagem de perfil concorrente pela Graph API (business_discovery), sem Chrome.
PERFIL=username -> grava descoberta_<username>.json com as mídias públicas e métricas."""
import json, os, urllib.parse, urllib.request, urllib.error
TOK, UID, P = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"], os.environ["PERFIL"]
campos = "id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink,media_url,thumbnail_url"
out, after = [], None
for base in ("https://graph.instagram.com/v21.0", "https://graph.facebook.com/v21.0"):
    try:
        while len(out) < 300:
            m = f"media.limit(50){{{campos}}}" if not after else f"media.after({after}).limit(50){{{campos}}}"
            q = {"fields": f"business_discovery.username({P}){{followers_count,media_count,{m}}}", "access_token": TOK}
            r = json.load(urllib.request.urlopen(f"{base}/{UID}?{urllib.parse.urlencode(q)}", timeout=60))
            bd = r["business_discovery"]; md = bd.get("media", {})
            out += md.get("data", [])
            after = md.get("paging", {}).get("cursors", {}).get("after")
            print(base, "seguidores", bd.get("followers_count"), "mídias lidas", len(out))
            if not after or not md.get("paging", {}).get("next"): break
        break
    except urllib.error.HTTPError as e:
        print("ERRO", base, e.code, e.read().decode()[:300])
json.dump(out, open(f"descoberta_{P}.json", "w"), ensure_ascii=False, indent=1)
