#!/usr/bin/env python3
"""Demografia dos seguidores e do público engajado (só leitura). Gera demografia.json."""
import json, os, urllib.request
API = "https://graph.instagram.com/v21.0"; TOK = os.environ["IG_TOKEN"]; UID = os.environ["IG_USER_ID"]
out = {}
for metr in ("follower_demographics", "engaged_audience_demographics"):
    for br in ("gender", "age", "city"):
        url = f"{API}/{UID}/insights?metric={metr}&period=lifetime&timeframe=this_month&metric_type=total_value&breakdown={br}&access_token={TOK}"
        if metr == "follower_demographics": url = url.replace("&timeframe=this_month", "")
        try:
            d = json.load(urllib.request.urlopen(url, timeout=60))
            res = d["data"][0]["total_value"]["breakdowns"][0]["results"]
            out[f"{metr}.{br}"] = sorted(((r["dimension_values"][0], r["value"]) for r in res), key=lambda x: -x[1])[:15]
        except Exception as e:
            out[f"{metr}.{br}"] = f"erro: {str(e)[:120]}"
json.dump(out, open("demografia.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False)[:1500])
