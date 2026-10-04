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
# Reels de TESTE (trial, só para não seguidores) não aparecem em /media: busca pelo media_id do teste.json
vistos = {r["id"] for r in out}
for it in json.load(open("teste.json")).get("fila", []):
    mid = it.get("media_id")
    if not mid or mid in vistos: continue
    row = {"id": mid, "timestamp": it.get("publicado"), "media_product_type": "TRIAL_REEL", "caption": f"[TESTE n={it.get('n')}] " + (it.get("legenda") or "")[:70].replace("\n", " ")}
    try:
        m = get(f"{API}/{mid}?fields=like_count,comments_count,permalink&access_token={TOK}")
        row.update({k: m.get(k) for k in ("like_count", "comments_count", "permalink")})
        ins = get(f"{API}/{mid}/insights?metric=views,reach,saved,shares,total_interactions&access_token={TOK}")
        for x in ins.get("data", []): row[x["name"]] = x["values"][0]["value"]
    except Exception as e:
        row["erro"] = str(e)[:60]
    out.append(row)
json.dump(out, open("relatorio.json", "w"), ensure_ascii=False, indent=1)
cols = ["media_product_type", "timestamp", "views", "reach", "like_count", "comments_count", "shares", "saved", "total_interactions", "caption", "permalink"]
with open("relatorio.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(out)
print(len(out), "posts")
