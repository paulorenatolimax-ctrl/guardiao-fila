#!/usr/bin/env python3
"""Dry-run de um carrossel com vídeo, sem token e sem chamar a Meta: confere se cada URL pública responde 200,
se o .mp4 local está dentro das specs de vídeo em carrossel e simula a criação dos contêineres até FINISHED.
Uso: python3 dryrun_video.py car294V_01.jpg ... car294V_03.mp4=/caminho/local.mp4 ..."""
import sys, json, subprocess, urllib.request
from carrossel_midia import criar_filhos, url_slide, e_video
REPO = "paulorenatolimax-ctrl/guardiao-fila"
def specs(path):
    j = json.loads(subprocess.check_output(["ffprobe","-v","error","-show_streams","-show_format","-of","json",path]))
    v = [s for s in j["streams"] if s["codec_type"]=="video"][0]; a = [s for s in j["streams"] if s["codec_type"]=="audio"]
    fps = eval(v["avg_frame_rate"]); dur = float(j["format"]["duration"]); mb = int(j["format"]["size"])/1e6
    probs = []
    if v["codec_name"] not in ("h264","hevc"): probs.append("codec")
    if v.get("pix_fmt") != "yuv420p": probs.append("pix_fmt")
    if not 23 <= fps <= 60: probs.append("fps")
    if int(v["width"]) > 1920: probs.append("largura")
    if not 3 <= dur <= 60: probs.append("duração")
    if mb > 100: probs.append("tamanho")
    if a and (a[0]["codec_name"]!="aac" or int(a[0]["sample_rate"])>48000): probs.append("áudio")
    return f'{v["codec_name"]} {v["width"]}x{v["height"]} {fps:.0f}fps {dur:.1f}s {mb:.1f}MB áudio={a[0]["codec_name"] if a else "—"}', probs
slides, locais = [], {}
for x in sys.argv[1:]:
    n, _, loc = x.partition("="); slides.append(n)
    if loc: locais[n] = loc
erros = 0
for s in slides:
    u = url_slide(s, REPO)
    try: code = urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=30).status
    except Exception as e: code = getattr(e, "code", str(e))
    linha = f"{s:22s} {code}"
    if code != 200: erros += 1
    if e_video(s) and s in locais:
        info, probs = specs(locais[s]); linha += f"  {info}  {'OK specs' if not probs else 'FORA: '+','.join(probs)}"; erros += len(probs)
    print(linha)
n = [0]
def fake(url, dados=None):
    if dados is None: return {"status_code": "FINISHED"}
    n[0] += 1; return {"id": f"dry{n[0]}"}
filhos = criar_filhos(slides, fake, "https://graph.instagram.com/v21.0", "UID", "TOK", REPO, dormir=lambda s: None)
print("contêineres simulados:", len(filhos), "| erros:", erros); sys.exit(1 if erros or len(filhos) > 10 else 0)
