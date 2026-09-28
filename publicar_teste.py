#!/usr/bin/env python3
"""Publica 1 Reel de TESTE por dia (Trial Reel: só aparece para NÃO seguidores).

Fila própria em teste.json, separada de fila.json: o Reel normal (13h/19h) e a
trava anti-duplicação dele NÃO enxergam os testes, e vice-versa.

- Janela: 15h30 às 17h30 BRT (alvo 16h), a partir de 29/09/2026.
- 1 por dia: se já saiu um teste hoje (BRT), sai sem fazer nada.
- Sempre com trial_params (SS_PERFORMANCE) e capa (capas/<arquivo>).
- Só Instagram: sem YouTube, sem X. O vídeo é o mesmo asset do release 'videos'.

Disparo manual (workflow_dispatch) ignora a janela e a data de início,
mas continua respeitando o limite de 1 por dia.

Requer os secrets IG_TOKEN e IG_USER_ID.
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, date

ARQ    = "teste.json"
API    = "https://graph.instagram.com/v21.0"
INICIO = date(2026, 9, 29)             # primeiro dia com teste
JANELA = ((15, 30), (17, 30))          # BRT, início inclusivo, fim exclusivo


def brt(dt_utc):
    return dt_utc - timedelta(hours=3)


def saiu_hoje(fila, hoje_brt):
    """'publicado' é gravado em UTC (igual ao fila.json)."""
    for it in fila["fila"]:
        pub = it.get("publicado")
        if pub and brt(datetime.strptime(pub, "%Y-%m-%d %H:%M")).date() == hoje_brt:
            return True
    return False


def decidir(agora_brt, fila, manual=False):
    """Devolve (deve_publicar, motivo). Função pura, testável a seco."""
    if saiu_hoje(fila, agora_brt.date()):
        return False, f"{agora_brt:%d/%m %H:%M} BRT: já saiu um teste hoje"
    if not any(not x.get("publicado") for x in fila["fila"]):
        return False, "teste.json sem pendentes"
    if manual:
        return True, "disparo manual: ignorando janela"
    if agora_brt.date() < INICIO:
        return False, f"{agora_brt:%d/%m} BRT: antes do início ({INICIO:%d/%m})"
    m = agora_brt.hour * 60 + agora_brt.minute
    (sh, sm), (eh, em) = JANELA
    if not (sh * 60 + sm <= m < eh * 60 + em):
        return False, f"{agora_brt:%H:%M} BRT: fora da janela 15h30-17h30"
    return True, f"{agora_brt:%H:%M} BRT: dentro da janela e nenhum teste hoje"


def chamar(url, dados=None):
    corpo = urllib.parse.urlencode(dados).encode() if dados else None
    req = urllib.request.Request(url, corpo, method="POST" if dados else "GET")
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        raise SystemExit(f"ERRO HTTP {e.code}: {e.read().decode()[:500]}")


def main():
    tok, uid = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
    repo = os.environ.get("GITHUB_REPOSITORY", "paulorenatolimax-ctrl/guardiao-fila")
    tag  = os.environ.get("RELEASE_TAG", "videos")
    fila = json.load(open(ARQ))

    manual = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    ok, motivo = decidir(brt(datetime.utcnow()), fila, manual)
    print(motivo)
    if not ok:
        return

    item = next(x for x in fila["fila"] if not x.get("publicado"))
    if not item.get("capa"):
        raise SystemExit(f"teste {item['n']} sem capa — abortando")
    url_video = f"https://github.com/{repo}/releases/download/{tag}/{urllib.parse.quote(item['asset'])}"
    url_capa  = f"https://raw.githubusercontent.com/{repo}/main/capas/{urllib.parse.quote(item['capa'])}"
    for u in (url_video, url_capa):   # link morto = falha antes de criar container
        try:
            urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=45)
        except Exception as e:
            raise SystemExit(f"link inacessível: {u} ({e})")
    print(f"→ TESTE vídeo {item['n']} · {item['asset']} · capa {item['capa']}")

    print("1/3 criando container (trial)…")
    c = chamar(f"{API}/{uid}/media", {
        "media_type": "REELS",
        "video_url": url_video,
        "caption": item["legenda"],
        "share_to_feed": "true",
        "cover_url": url_capa,
        "trial_params": json.dumps({"graduation_strategy":
            item["trial"] if isinstance(item.get("trial"), str) else "SS_PERFORMANCE"}),
        "access_token": tok,
    })
    cid = c["id"]
    print(f"  container {cid}")

    print("2/3 aguardando processar…")
    for tentativa in range(30):          # até 15 min
        time.sleep(30)
        s = chamar(f"{API}/{cid}?fields=status_code,status&access_token={tok}")
        estado = s.get("status_code")
        print(f"  [{tentativa+1}] {estado}")
        if estado == "FINISHED":
            break
        if estado in ("ERROR", "EXPIRED"):
            raise SystemExit(f"container falhou: {s}")
    else:
        raise SystemExit("tempo esgotado esperando o processamento")

    print("3/3 publicando…")
    p = chamar(f"{API}/{uid}/media_publish", {"creation_id": cid, "access_token": tok})
    print(f"  TESTE PUBLICADO: media id {p['id']}")

    item["publicado"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    item["media_id"]  = p["id"]
    json.dump(fila, open(ARQ, "w"), ensure_ascii=False, indent=1)
    print(f"restam {sum(1 for x in fila['fila'] if not x.get('publicado'))} testes")


if __name__ == "__main__":
    main()
