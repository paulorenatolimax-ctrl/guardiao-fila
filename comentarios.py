#!/usr/bin/env python3
"""13/10/2026 — Robô de comentários pela Graph API (substitui o robô do Chrome).
MODO=listar   -> grava pendentes.json: comentários dos últimos N posts sem resposta nossa.
MODO=responder-> lê respostas.json [{cid, txt}] e responde 1 a cada 60-120 s; pula o que já tem resposta nossa;
                 grava em respostas.json o campo 'feito'. Para no primeiro erro de limite.
Requer IG_TOKEN e IG_USER_ID."""
import json, os, random, time, urllib.parse, urllib.request, urllib.error
API = "https://graph.instagram.com/v21.0"
TOK, UID = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
EU = "prof.paulolima1844"

def get(path, **q):
    q["access_token"] = TOK
    try:
        return json.load(urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(q)}", timeout=60))
    except urllib.error.HTTPError as e:
        print("ERRO GET", path, e.code, e.read().decode()[:400]); raise

def post(path, **d):
    d["access_token"] = TOK
    req = urllib.request.Request(f"{API}/{path}", urllib.parse.urlencode(d).encode(), method="POST")
    return json.load(urllib.request.urlopen(req, timeout=60))

def ja_respondi(cid):
    r = get(f"{cid}/replies", fields="username", limit=50)
    return any(x.get("username") == EU for x in r.get("data", []))

def listar():
    n = int(os.environ.get("N_POSTS", "15"))
    media, u = [], None
    while len(media) < n:
        r = json.load(urllib.request.urlopen(u, timeout=60)) if u else get(f"{UID}/media", fields="id,caption,timestamp,comments_count", limit=min(n, 50))
        media += r.get("data", []); u = r.get("paging", {}).get("next")
        if not u: break
    media = [m for m in media[:n] if m.get("comments_count")]
    out = []
    for m in media:
        url = None; pagina = 0; brutos = 0
        while pagina < 5:
            r = json.load(urllib.request.urlopen(url, timeout=60)) if url else get(
                f"{m['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50)
            brutos += len(r.get("data", []))
            for c in r.get("data", []):
                if c.get("username") == EU: continue
                reps = (c.get("replies") or {}).get("data", [])
                if any(x.get("username") == EU for x in reps): continue
                out.append({"cid": c["id"], "u": c.get("username"), "t": c.get("text", "")[:200],
                            "post": (m.get("caption") or "")[:50], "ts": c.get("timestamp")})
            url = r.get("paging", {}).get("next"); pagina += 1
            if not url: break
        print(f"  {(m.get('caption') or '')[:40]!r}: {brutos} comentários lidos de {m.get('comments_count')} que o post tem")
    json.dump(out, open("pendentes.json", "w"), ensure_ascii=False, indent=1)
    print(f"{len(out)} comentários sem resposta em {len(media)} posts")

def responder():
    fila = json.load(open("respostas.json"))
    limite = int(os.environ.get("MAX", "40")); feitos = 0
    for it in fila:
        if it.get("feito") or feitos >= limite: continue
        try:
            if ja_respondi(it["cid"]):
                it["feito"] = "ja"; continue
            p = post(f"{it['cid']}/replies", message=it["txt"])
            it["feito"] = p.get("id", "ok"); feitos += 1
            print(f"ok {it.get('u')}: {it['txt'][:40]}")
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]; print("ERRO", e.code, msg)
            it["erro"] = f"{e.code}"
            if e.code in (429, 400) and ("limit" in msg.lower() or "spam" in msg.lower() or e.code == 429): break
        json.dump(fila, open("respostas.json", "w"), ensure_ascii=False, indent=1)
        time.sleep(60 + random.random() * 60)
    json.dump(fila, open("respostas.json", "w"), ensure_ascii=False, indent=1)
    print(f"respondidos agora: {feitos}; restam {sum(1 for x in fila if not x.get('feito'))}")

def direct():
    """27/10/2026: resposta privada (direct) a um comentário + resposta pública depois.
    Lê direct.json [{cid, dm, txt}]. O público só sai se o direct saiu (senão o "te mandei" seria mentira)."""
    fila = json.load(open("direct.json"))
    for it in fila:
        if it.get("feito"): continue
        try:
            body = json.dumps({"recipient": {"comment_id": it["cid"]}, "message": {"text": it["dm"]}}).encode()
            req = urllib.request.Request(f"{API}/{UID}/messages?access_token={TOK}", body, {"Content-Type": "application/json"}, method="POST")
            it["dm_ok"] = json.load(urllib.request.urlopen(req, timeout=60)).get("message_id", "ok")
            print("direct ok", it["cid"])
            if it.get("txt") and not ja_respondi(it["cid"]):
                it["feito"] = post(f"{it['cid']}/replies", message=it["txt"]).get("id", "ok"); print("público ok")
        except urllib.error.HTTPError as e:
            it["erro"] = f"{e.code} {e.read().decode()[:300]}"; print("ERRO", it["erro"])
    json.dump(fila, open("direct.json", "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    m = os.environ.get("MODO", "listar")
    listar() if m == "listar" else direct() if m == "direct" else responder()
