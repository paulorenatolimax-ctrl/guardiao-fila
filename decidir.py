#!/usr/bin/env python3
"""Decide se é hora de publicar, ou se o workflow deve só sair sem fazer nada.

Roda dentro das 3 janelas com tolerância total para eventuais atrasos do runner do GitHub Actions:
- Manhã:  08:00 às 10:00 BRT
- Tarde:  13:00 às 15:00 BRT (cobre 13h e 14h em cheio)
- Noite:  17:00 às 19:00 BRT (cobre 17h e 18h em cheio)

Basta UMA tentativa dentro da janela dar certo; assim que o post sai, a janela é marcada como cumprida para aquele dia.
"""
import json, os
from datetime import datetime, timedelta, timezone

# Janelas ampliadas para absorver atrasos normais de fila do GitHub Actions:
# Janela 0 (Manhã): 07:30 às 11:30 BRT (alvo 08h-09h)
# Janela 1 (Tarde): 12:30 às 16:30 BRT (alvo 13h-14h)
# Janela 2 (Noite): 17:00 às 21:30 BRT (alvo 18h-19h)
JANELAS = [(7, 30, 11, 30), (12, 30, 16, 30), (17, 0, 21, 30)]  # (h,m) início, (h,m) fim exclusivo


def brt_agora():
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)


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
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        print("disparo manual — ignorando filtro de janela")
        escrever("true")
        return

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
