#!/usr/bin/env python3
"""Relatório de desempenho dos Reels (só leitura). Gera relatorio.csv e relatorio.json."""
import json, os, urllib.request, urllib.parse, csv
API = "https://graph.instagram.com/v21.0"; TOK = os.environ["IG_TOKEN"]; UID = os.environ["IG_USER_ID"]
def get(url):
    return json.load(urllib.request.urlopen(url, timeout=60))
out, url = [], f"{API}/{UID}/media?fields=id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count&limit=50&access_token={TOK}"
while url and len(out) < 200:
    d = get(url)
    for m in d.get("data", []):
        row = {k: m.get(k) for k in ("id", "timestamp", "media_product_type", "like_count", "comments_count", "permalink")}
        row["caption"] = (m.get("caption") or "")[:90].replace("\n", " ")
        for metr in ("views,reach,saved,shares,total_interactions", "reach,saved,shares,total_interactions"):
            try:
                ins = get(f"{API}/{m['id']}/insights?metric={metr}&access_token={TOK}")
                for x in ins.get("data", []): row[x["name"]] = x["values"][0]["value"]
                break
            except Exception as e:
                row["erro"] = str(e)[:60]
        out.append(row)
    url = d.get("paging", {}).get("next")
json.dump(out, open("relatorio.json", "w"), ensure_ascii=False, indent=1)
cols = ["timestamp", "views", "reach", "like_count", "comments_count", "shares", "saved", "total_interactions", "caption", "permalink"]
with open("relatorio.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(out)
print(len(out), "posts")
