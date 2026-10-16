#!/usr/bin/env python3
"""Coleta completa SÓ LEITURA (16/10/2026, pedido do Paulo). Não publica nada, não mexe na fila.
Grava metricas_full.json (vai para o branch `metricas`)."""
import json, os, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone
API = "https://graph.instagram.com/v21.0"
TOK, UID = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
DESDE = datetime(2026, 8, 1, tzinfo=timezone.utc)
erros = []
def get(url, tag=""):
    sep = "&" if "?" in url else "?"
    try:
        return json.load(urllib.request.urlopen(f"{url}{sep}access_token={TOK}", timeout=60))
    except urllib.error.HTTPError as e:
        erros.append({"tag": tag, "erro": e.read().decode()[:300]}); return None
    except Exception as e:
        erros.append({"tag": tag, "erro": str(e)[:300]}); return None
agora = datetime.now(timezone.utc)
out = {"gerado_em": agora.strftime("%Y-%m-%dT%H:%MZ")}
out["conta"] = get(f"{API}/{UID}?fields=username,followers_count,follows_count,media_count", "conta")
# follower_count por dia: API aceita só últimos 30 dias, janelas de até 30 dias
fc = []
for ini in (30, 15):
    s, u = int((agora - timedelta(days=ini)).timestamp()), int((agora - timedelta(days=ini - 15)).timestamp())
    d = get(f"{API}/{UID}/insights?metric=follower_count&period=day&since={s}&until={u}", f"follower_count_{ini}")
    if d:
        for x in d.get("data", []): fc += x.get("values", [])
out["follower_count_dia"] = fc
# métricas de conta por dia (total_value), janelas diárias dos últimos 30 dias
diario = []
for i in range(30, 0, -1):
    s = int((agora - timedelta(days=i)).replace(hour=3, minute=0, second=0).timestamp()); u = s + 86400
    d = get(f"{API}/{UID}/insights?metric=reach,profile_views,accounts_engaged,website_clicks,total_interactions,likes,comments,shares,saves,follows_and_unfollows,views&period=day&metric_type=total_value&since={s}&until={u}", f"conta_dia_{i}")
    if not d:
        d = get(f"{API}/{UID}/insights?metric=reach,profile_views,accounts_engaged,total_interactions,likes,comments,shares,saves&period=day&metric_type=total_value&since={s}&until={u}", f"conta_dia_b_{i}")
    row = {"since": s}
    for x in (d or {}).get("data", []):
        tv = x.get("total_value", {}); row[x["name"]] = tv.get("value"); 
        if tv.get("breakdowns"): row[x["name"] + "_bd"] = tv["breakdowns"]
    diario.append(row)
out["conta_dia"] = diario
demo = {}
for bd in ("city", "age", "gender", "country"):
    for metr in ("follower_demographics", "engaged_audience_demographics"):
        d = get(f"{API}/{UID}/insights?metric={metr}&period=lifetime&timeframe=this_month&breakdown={bd}&metric_type=total_value", f"{metr}_{bd}")
        if d: demo[f"{metr}_{bd}"] = d.get("data")
d = get(f"{API}/{UID}/insights?metric=online_followers&period=lifetime", "online_followers")
demo["online_followers"] = d.get("data") if d else None
out["demografia"] = demo
# mídias
midias, url = [], f"{API}/{UID}/media?fields=id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count,children{{id}}&limit=50"
fim = False
while url and not fim:
    d = get(url, "media_list")
    if not d: break
    for m in d.get("data", []):
        ts = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z")
        if ts < DESDE: fim = True; break
        m["n_slides"] = len((m.pop("children", None) or {}).get("data", [])) or None
        reels = m.get("media_product_type") == "REELS"
        cands = (["reach,views,likes,comments,saved,shares,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time", "reach,likes,comments,saved,shares,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time", "reach,saved,shares"]
                 if reels else ["reach,views,likes,comments,saved,shares,total_interactions,follows,profile_visits,profile_activity", "reach,views,likes,comments,saved,shares,total_interactions,follows,profile_visits", "reach,views,likes,comments,saved,shares,total_interactions", "reach,saved,shares"])
        ins = {}
        for c in cands:
            r = get(f"{API}/{m['id']}/insights?metric={c}", f"ins_{m['id']}")
            if r:
                for x in r.get("data", []):
                    v = x.get("values", [{}])[0].get("value") if x.get("values") else x.get("total_value", {}).get("value")
                    ins[x["name"]] = v
                break
        if reels and "follows" not in ins:
            r = get(f"{API}/{m['id']}/insights?metric=follows,profile_visits", f"insf_{m['id']}")
            for x in (r or {}).get("data", []): ins[x["name"]] = x.get("values", [{}])[0].get("value")
        m["insights"] = ins; midias.append(m)
    url = d.get("paging", {}).get("next")
out["midias"] = midias
out["erros"] = erros[:200]; out["n_erros"] = len(erros)
json.dump(out, open("metricas_full.json", "w"), ensure_ascii=False, indent=0)
print(len(midias), "midias;", len(erros), "erros")
