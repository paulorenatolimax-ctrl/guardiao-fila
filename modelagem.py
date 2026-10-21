#!/usr/bin/env python3
"""21/10/2026 — Modelagem de perfil público SEM login (roda no GitHub, não usa a conta do Paulo).
PERFIL=username, TOP=100 -> modelagem/<perfil>/dados.json, ganchos.json e quadros/*.jpg"""
import json, os, subprocess, time, pathlib
import instaloader
P, TOP = os.environ["PERFIL"], int(os.environ.get("TOP", "100"))
out = pathlib.Path(f"modelagem/{P}"); (out / "quadros").mkdir(parents=True, exist_ok=True)
L = instaloader.Instaloader(download_pictures=False, download_videos=False, save_metadata=False, quiet=True)
import urllib.request as _u
def _pid():
    for host in ("https://i.instagram.com", "https://www.instagram.com"):
        try:
            rq = _u.Request(f"{host}/api/v1/users/web_profile_info/?username={P}", headers={"X-IG-App-ID": "936619743392459",
                 "User-Agent": "Instagram 219.0.0.12.117 Android (31/12; 420dpi; 1080x2210; samsung; SM-G991B; o1s; exynos2100; pt_BR; 346138365)"})
            return int(json.load(_u.urlopen(rq, timeout=30))["data"]["user"]["id"])
        except Exception as e:
            print("web_profile_info falhou em", host, repr(e)[:120])
    return None
prof = None
if os.environ.get("CODES"):
    pass
else:
  try:
    prof = instaloader.Profile.from_username(L.context, P)
  except Exception as e:
    print("from_username falhou:", repr(e)[:120]); pid = _pid(); print("id", pid)
    prof = instaloader.Profile.from_id(L.context, pid)
  print("seguidores", prof.followers, "posts", prof.mediacount)
itens = []
def _posts():
    cods = [c for c in os.environ.get("CODES", "").split(",") if c]
    if cods:
        for c in cods:
            try:
                yield instaloader.Post.from_shortcode(L.context, c)
            except Exception as e:
                print("falhou", c, repr(e)[:100])
            time.sleep(3)
    else:
        yield from prof.get_posts()
try:
    for i, p in enumerate(_posts()):
        itens.append({"code": p.shortcode, "data": p.date_utc.isoformat(), "video": p.is_video,
                      "views": p.video_view_count if p.is_video else None,
                      "likes": p.likes, "comentarios": p.comments,
                      "duracao": getattr(p, "video_duration", None),
                      "legenda": p.caption or "", "video_url": p.video_url if p.is_video else None,
                      "capa": p.url})
        if i % 12 == 11: time.sleep(4)
        if len(itens) >= 450: break
except Exception as e:
    print("parou na coleta:", repr(e)[:200])
print("coletados", len(itens))
json.dump(itens, open(out / "dados.json", "w"), ensure_ascii=False, indent=1)
vids = sorted([x for x in itens if x["video"] and x["video_url"]], key=lambda x: x["views"] or 0, reverse=True)[:TOP]
from faster_whisper import WhisperModel
m = WhisperModel("small", compute_type="int8")
ganchos = []
for k, x in enumerate(vids):
    a = f"/tmp/{x['code']}.wav"
    try:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", "10", "-i", x["video_url"], "-vn", "-ac", "1", "-ar", "16000", a], check=True, timeout=120)
        for t in ("0.5", "2.5"):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", x["video_url"], "-frames:v", "1", "-vf", "scale=360:-2",
                            str(out / "quadros" / f"{k+1:03d}_{x['code']}_{t}.jpg")], timeout=120)
        segs, _ = m.transcribe(a, language="pt")
        fala = " ".join(s.text.strip() for s in segs)
    except Exception as e:
        fala = f"[erro: {repr(e)[:80]}]"
    ganchos.append({**{k2: x[k2] for k2 in ("code", "data", "views", "likes", "comentarios", "duracao")},
                    "posicao": k + 1, "fala_10s": fala, "legenda_1a_linha": (x["legenda"] or "").split("\n")[0][:200]})
    print(k + 1, x["views"], fala[:80])
    time.sleep(1)
json.dump(ganchos, open(out / "ganchos.json", "w"), ensure_ascii=False, indent=1)
