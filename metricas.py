#!/usr/bin/env python3
"""Lê as métricas de posts pelo media id (inclusive Trial Reels, que o pulso não lista). Só imprime."""
import json, os, urllib.request, urllib.error
API = "https://graph.instagram.com/v21.0"
TOK = os.environ["IG_TOKEN"]
for mid in os.environ.get("IDS", "").split(","):
    mid = mid.strip()
    if not mid: continue
    def get(u):
        try: return json.load(urllib.request.urlopen(u, timeout=60))
        except urllib.error.HTTPError as e: return {"erro": e.read().decode()[:300]}
    b = get(f"{API}/{mid}?fields=timestamp,like_count,comments_count,media_product_type&access_token={TOK}")
    i = get(f"{API}/{mid}/insights?metric=views,reach,likes,comments,shares,saved,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time&access_token={TOK}")
    vals = {x["name"]: x["values"][0]["value"] for x in i.get("data", [])} if "data" in i else i
    print("MID", mid, b.get("timestamp"), json.dumps(vals, ensure_ascii=False))
