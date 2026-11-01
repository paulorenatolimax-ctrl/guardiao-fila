#!/usr/bin/env python3
"""01/11/2026 — Robô de palavras-chave pela API oficial (substitui o ManyChat, que parou no plano grátis).
Varre os comentários dos últimos N_POSTS posts feitos nas últimas HORAS horas. Comentário que é UMA palavra
(só letras, em caixa alta) ou está em palavras_dm.json -> resposta privada ao comentário (DM) com o texto do
modelo + resposta pública curta. Guarda os cids feitos em palavras_feitas.json para nunca repetir.
MODO=listar -> só mostra o que faria. MODO=enviar -> manda. Requer IG_TOKEN e IG_USER_ID."""
import json, os, random, re, time, unicodedata, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

API = "https://graph.instagram.com/v21.0"
TOK, UID = os.environ["IG_TOKEN"], os.environ["IG_USER_ID"]
EU = "prof.paulolima1844"
MODO = os.environ.get("MODO", "listar")
N_POSTS = int(os.environ.get("N_POSTS", "8"))
HORAS = int(os.environ.get("HORAS", "48"))
MAX = int(os.environ.get("MAX", "30"))

CFG = json.load(open("palavras_dm.json", encoding="utf-8"))
FEITAS_ARQ = "palavras_feitas.json"
try:
    FEITAS = json.load(open(FEITAS_ARQ, encoding="utf-8"))
except Exception:
    FEITAS = {}

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

EXTRA = {sem_acento(p).upper() for p in CFG.get("palavras_extra", [])}
ESTACOES = {sem_acento(k).upper(): v for k, v in CFG.get("estacoes", {}).items()}

def get(path, **q):
    q["access_token"] = TOK
    return json.load(urllib.request.urlopen(f"{API}/{path}?{urllib.parse.urlencode(q)}", timeout=60))

def post(path, **d):
    d["access_token"] = TOK
    req = urllib.request.Request(f"{API}/{path}", urllib.parse.urlencode(d).encode(), method="POST")
    return json.load(urllib.request.urlopen(req, timeout=60))

def dm_privada(cid, texto):
    body = json.dumps({"recipient": {"comment_id": cid}, "message": {"text": texto}}).encode()
    req = urllib.request.Request(f"{API}/{UID}/messages?access_token={TOK}", body,
                                 {"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(req, timeout=60))

def palavra_chave(texto):
    """Devolve a palavra normalizada se o comentário for uma palavra-chave; senão None."""
    t = re.sub(r"[^\wÀ-ú]", " ", texto or "").strip()
    toks = t.split()
    if not toks or len(toks) > 2:
        return None
    pal = sem_acento(toks[0]).upper()
    if len(toks) == 2:  # "EU QUERO", "QUERO LIVRO"
        pal2 = sem_acento(toks[1]).upper()
        if pal in EXTRA or pal in ESTACOES: return pal
        if pal2 in EXTRA or pal2 in ESTACOES: return pal2
        return None
    if pal in EXTRA or pal in ESTACOES:
        return pal
    if toks[0].isupper() and toks[0].isalpha() and len(toks[0]) >= 3:
        return pal
    return None

def montar_dm(pal, username):
    nome = ""  # o username não é nome; não usar
    abertura = (ESTACOES.get(pal) or CFG["abertura_padrao"]).replace("{guia}", CFG["guia"])
    return CFG["modelo"].format(nome=nome, abertura=abertura, trilha=CFG["trilha"], guia=CFG["guia"],
                                whatsapp=CFG["whatsapp"])

def main():
    corte = datetime.now(timezone.utc) - timedelta(hours=HORAS)
    media = get(f"{UID}/media", fields="id,caption,timestamp,comments_count", limit=N_POSTS).get("data", [])
    candidatos = []
    for m in media:
        if not m.get("comments_count"): continue
        url = None; pagina = 0
        while pagina < 4:
            r = json.load(urllib.request.urlopen(url, timeout=60)) if url else get(
                f"{m['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50)
            for c in r.get("data", []):
                if c.get("username") == EU or c["id"] in FEITAS: continue
                try:
                    if datetime.strptime(c["timestamp"], "%Y-%m-%dT%H:%M:%S%z") < corte: continue
                except Exception:
                    continue
                reps = (c.get("replies") or {}).get("data", [])
                if any(x.get("username") == EU for x in reps): continue
                pal = palavra_chave(c.get("text", ""))
                if pal:
                    candidatos.append({"cid": c["id"], "u": c.get("username"), "t": c.get("text", "")[:80],
                                       "pal": pal, "post": (m.get("caption") or "")[:40]})
            url = r.get("paging", {}).get("next"); pagina += 1
            if not url: break
    print(f"{len(candidatos)} comentários com palavra-chave em {len(media)} posts (últimas {HORAS} h)")
    for c in candidatos: print(f"  {c['pal']:<12} @{c['u']}: {c['t']!r}  [{c['post']!r}]")
    if MODO != "enviar":
        return
    feitos = 0
    for c in candidatos:
        if feitos >= MAX: break
        try:
            r = dm_privada(c["cid"], montar_dm(c["pal"], c["u"]))
            FEITAS[c["cid"]] = {"u": c["u"], "pal": c["pal"], "dm": r.get("message_id", "ok"),
                                "quando": datetime.now(timezone.utc).isoformat(timespec="minutes")}
            try:
                post(f"{c['cid']}/replies", message=random.choice(CFG["publico"]))
            except urllib.error.HTTPError as e:
                FEITAS[c["cid"]]["publico_erro"] = f"{e.code}"
            feitos += 1; print("dm ok", c["pal"], "@" + str(c["u"]))
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:300]; print("ERRO", e.code, msg)
            FEITAS[c["cid"]] = {"u": c["u"], "pal": c["pal"], "erro": f"{e.code} {msg[:120]}",
                                "quando": datetime.now(timezone.utc).isoformat(timespec="minutes")}
            if e.code == 429 or "limit" in msg.lower() or "spam" in msg.lower(): break
        finally:
            json.dump(FEITAS, open(FEITAS_ARQ, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        time.sleep(8 + random.random() * 8)
    print(f"DMs enviadas agora: {feitos}")

if __name__ == "__main__":
    main()
