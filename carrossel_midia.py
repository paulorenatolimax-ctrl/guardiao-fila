"""Filhos do carrossel: imagem (.jpg/.png) ou VÍDEO (.mp4). 17/10/2026.
- Imagem: image_url no raw.githubusercontent (como sempre foi).
- Vídeo: media_type=VIDEO + video_url apontando para o asset no release "videos"
  (mesmo host que os Reels já usam em publicar.py). Suba antes: ./subir_video_slide.sh arquivo.mp4
- Cada filho de vídeo é consultado (status_code) até FINISHED antes de montar o carrossel.
Specs Meta p/ vídeo em carrossel: MP4/MOV, H.264/HEVC, AAC <=48 kHz, 23-60 fps, até 1920 px de largura,
3 s a 60 s, até 100 MB (ver VIDEO_NO_CARROSSEL_17OUT.md). Reels NÃO entram em carrossel: o tipo é VIDEO."""
import time, urllib.parse

VIDEO_EXT = (".mp4", ".mov")

def e_video(nome):
    return nome.lower().endswith(VIDEO_EXT)

def url_slide(nome, repo, tag="videos"):
    q = urllib.parse.quote(nome)
    if e_video(nome):
        return f"https://github.com/{repo}/releases/download/{tag}/{q}"
    return f"https://raw.githubusercontent.com/{repo}/main/carrosseis/{q}"

def esperar(chamar, api, tok, cid, tentativas=60, pausa=5, dormir=time.sleep):
    """Consulta o contêiner até FINISHED. ERROR/EXPIRED ou tempo esgotado = exceção (o post não sai)."""
    for _ in range(tentativas):
        s = chamar(f"{api}/{cid}?fields=status_code,status&access_token={tok}")
        st = s.get("status_code")
        if st == "FINISHED": return s
        if st in ("ERROR", "EXPIRED"): raise RuntimeError(f"contêiner {cid} com {st}: {s.get('status')}")
        dormir(pausa)
    raise RuntimeError(f"contêiner {cid} não ficou FINISHED a tempo")

def criar_filhos(slides, chamar, api, uid, tok, repo, tag="videos", dormir=time.sleep):
    filhos, videos = [], []
    for s in slides:
        url = url_slide(s, repo, tag)
        if e_video(s):
            r = chamar(f"{api}/{uid}/media", {"media_type": "VIDEO", "video_url": url, "is_carousel_item": "true", "access_token": tok})
            videos.append(r["id"]); print("  filho VÍDEO", s, "→", r["id"])
        else:
            r = chamar(f"{api}/{uid}/media", {"image_url": url, "is_carousel_item": "true", "access_token": tok})
        filhos.append(r["id"])
    for vid in videos:  # vídeo precisa terminar de processar antes do contêiner CAROUSEL
        esperar(chamar, api, tok, vid, dormir=dormir)
    return filhos
