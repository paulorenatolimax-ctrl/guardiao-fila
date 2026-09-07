#!/usr/bin/env python3
"""Decide se É hora de publicar, ou se o workflow deve só sair sem fazer nada.

Roda a cada ~17min o dia todo (ver publicar.yml). Existe porque o schedule
do GitHub Actions em repositório público, sob alta carga, não só atrasa —
em 07/09/2026 um dos três horários simplesmente não disparou, sem erro, sem
aviso. Rodando várias vezes dentro de cada janela (8h-9h, 13h-14h, 17h-18h
BRT), basta UMA tentativa emplacar pra o post sair; um pulo isolado do
GitHub deixa de ser um post perdido.

Escreve deve_publicar=true/false em $GITHUB_OUTPUT.
"""
import json, os
from datetime import datetime, timedelta

# BRT é UTC-3 fixo (Brasil não observa horário de verão desde 2019).
JANELAS = [(8, 0, 9, 0), (13, 0, 14, 0), (17, 0, 18, 0)]  # (h,m) início, (h,m) fim exclusivo


def brt_agora():
    return datetime.utcnow() - timedelta(hours=3)


def achar_janela(agora):
    minutos = agora.hour * 60 + agora.minute
    for i, (sh, sm, eh, em) in enumerate(JANELAS):
        if sh * 60 + sm <= minutos < eh * 60 + em:
            return i
    return None


def janela_ja_saiu_hoje(fila, idx, hoje):
    sh, sm, eh, em = JANELAS[idx]
    for item in fila["fila"]:
        pub = item.get("publicado")
        if not pub:
            continue
        # "publicado" é gravado em UTC pelo runner do GitHub Actions.
        dt_brt = datetime.strptime(pub, "%Y-%m-%d %H:%M") - timedelta(hours=3)
        if dt_brt.strftime("%Y-%m-%d") != hoje:
            continue
        minutos = dt_brt.hour * 60 + dt_brt.minute
        if sh * 60 + sm <= minutos < eh * 60 + em:
            return True
    return False


def escrever(valor):
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.write(f"deve_publicar={valor}\n")


def main():
    agora = brt_agora()
    idx = achar_janela(agora)

    if idx is None:
        print(f"{agora:%H:%M} BRT — fora de janela, nada a fazer")
        escrever("false")
        return

    fila = json.load(open("fila.json"))
    hoje = agora.strftime("%Y-%m-%d")
    if janela_ja_saiu_hoje(fila, idx, hoje):
        print(f"{agora:%H:%M} BRT — janela {idx} de hoje já publicou, nada a fazer")
        escrever("false")
        return

    print(f"{agora:%H:%M} BRT — dentro da janela {idx}, ainda não publicou hoje: seguindo")
    escrever("true")


main()
