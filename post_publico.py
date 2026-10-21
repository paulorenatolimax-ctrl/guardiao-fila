#!/usr/bin/env python3
"""21/10/2026 — baixa um post público SEM login (slides, legenda, métricas) para modelagem."""
import json, os, pathlib, urllib.request, instaloader
C = os.environ["CODE"]
out = pathlib.Path(f"modelagem/post_{C}"); out.mkdir(parents=True, exist_ok=True)
L = instaloader.Instaloader(quiet=True)
p = instaloader.Post.from_shortcode(L.context, C)
info = {"code": C, "dono": p.owner_username, "data": p.date_utc.isoformat(), "tipo": p.typename,
        "likes": p.likes, "comentarios": p.comments, "views": p.video_view_count if p.is_video else None,
        "legenda": p.caption or ""}
nodes = list(p.get_sidecar_nodes()) if p.typename == "GraphSidecar" else []
urls = [(n.video_url if n.is_video else n.display_url) for n in nodes] or [p.video_url if p.is_video else p.url]
for i, u in enumerate(urls, 1):
    ext = "mp4" if ".mp4" in u.split("?")[0] else "jpg"
    urllib.request.urlretrieve(u, out / f"{i:02d}.{ext}")
info["n_midias"] = len(urls)
json.dump(info, open(out / "info.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in info.items() if k != "legenda"}, ensure_ascii=False))
