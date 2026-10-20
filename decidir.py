#!/usr/bin/env python3
"""03/10/2026: regra de RECUPERAÇÃO (catch-up) para os 3 tipos de post.

O cron do GitHub atrasa e pula execuções; a regra antiga de "janela" fazia o post
atrasado ser PULADO. Agora, a cada execução (cron a cada 5 min, 7h-23h59 BRT):

  1. conta quantos horários do dia já venceram (ex.: carrossel às 14h -> 8h e 11h = 2);
  2. conta quantos posts daquele tipo saíram HOJE (BRT; "publicado" é gravado em UTC);
  3. se publicados < vencidos, publica o próximo da fila, desde que:
       - o último post daquele tipo tenha saído há pelo menos INTERVALO (90 min / 4 h);
       - agora esteja entre 7h00 e 23h59 BRT;
       - não passe do MÁXIMO do dia;
     e nunca mais de 1 por execução (cada execução publica no máximo 1 item).

'forcar' (disparo manual com a caixa marcada) publica sem regra nenhuma.
Disparo manual SEM 'forcar' segue a mesma regra do cron (é o que o Mac usa).

Uso no workflow:  python3 decidir.py reel|carrossel|teste   -> grava deve_publicar=true/false
"""
import json, os, sys
from datetime import date, datetime, timedelta, timezone

TIPOS = {
    # tipo:      arquivo,            chave,        horários BRT,  intervalo mínimo,      máximo/dia
    # 06/10/2026: Paulo reduziu para 1 Reel por dia, às 13h. 10/10/2026: Paulo moveu o Reel para 17h.
    "reel":      ("fila.json",       "fila",       [17],          timedelta(hours=4),    1),
    # 05/10/2026: Paulo fixou a estratégia em 2 Reels + 5 carrosséis por dia ("está funcionando").
    # 08/10/2026: Paulo pediu 6 por dia: 8, 11, 14, 17, 19 e 21h.
    # 10/10/2026: Paulo aprovou a ESTRATEGIA_EXPLOSAO: a partir de 11/10, 4 por dia às 7h30, 14h, 18h30 e 20h30
    # (horário fracionado: 7.5 = 7h30). Corta a faixa 10h-13h, a mais fraca.
    # 12/10/2026: Paulo achou 18h30 e 20h30 colados e o buraco de manhã sem sentido; grade harmonizada a cada ~4 h
    # (7h30, 11h30, 15h30, 20h), com o Reel das 17h no meio da tarde.
    "carrossel": ("carrosseis.json", "carrosseis", [7.5, 11.5, 15.5, 20], timedelta(minutes=90), 4),
    "teste":     ("teste.json",      "fila",       [8, 14, 18],   timedelta(minutes=90), 3),
}
# MODO ELEIÇÃO: grade especial por data (BRT), por tipo. Fora dessas datas vale TIPOS.
ESPECIAIS = {
    "reel": {
        date(2026, 10, 19): ([13], timedelta(hours=4), 1),  # 19/10: Paulo aprovou o R54 (Gramsci, folclore) para as 13h
    },
    "carrossel": {
        # 03/10/2026: modo eleição (6/dia) cancelado pelo Paulo; volta à grade normal de 3 por dia.
        # 04/10/2026: Paulo pediu 4 carrosséis no dia (carrossel ganha tração com os dias).
        # 05/10/2026: Paulo aprovou tudo e pediu 5 no dia (8h saiu atrasado pelo bloqueio da API).
        # 06/10/2026: Reel do Millett saiu às 10h42; carrossel das 11h passa para 12h (pedido do Paulo).
        # 06/10/2026: o voto feminino saiu forçado às 12h15 (conta como o horário das 13h); Gramsci às 20h = 6 no dia.
        # (14h16: o socialista de iPhone saiu no lugar do Peirce corrigido, barrado pela trava de título; Peirce às 17h, Gramsci às 20h)
        # 19h14: Gramsci forçado a pedido do Paulo; 21h: mais um (DIR1).
        # 07/10/2026: Paulo pediu o carrossel da democracia (DEM1) às 19h; CPV1 segue às 20h (intervalo do dia: 55 min).
        date(2026, 10, 13): ([7.5, 11.5, 15.5, 21], timedelta(minutes=90), 4),
        date(2026, 10, 21): ([7.5, 11.5, 14, 18.5, 20.5], timedelta(minutes=90), 5),  # validado 20/10: G276 Mao, G273 Fidel, G318 Stalin, G296 Picasso, G314 Identitarismo
        date(2026, 10, 20): ([7.5, 14, 14.25, 18.5, 20.5], timedelta(minutes=90), 5),  # G345 7h24, G333+G298 14h, G198 Livros 18h30, G315 Marx/Bolsa 20h30 (Paulo 20/10)
        date(2026, 10, 19): ([7.5, 14, 18.5, 20.5], timedelta(minutes=90), 4),  # lote validado 18/10: G299, G322, G329, G337
        date(2026, 10, 18): ([7.5, 10, 14, 18.5], timedelta(minutes=90), 4),  # 18/10: G294 (vídeo) 07h30, G338 Obama antecipado (saiu 10h21), G280 Rivera 14h, G265 Aristóteles×Freire 18h30 (lote validado pelo Paulo 18/10)
        date(2026, 10, 17): ([7, 12, 15, 17.5, 21.25], timedelta(minutes=90), 5),  # 17/10: Paulo pediu extras às 15h e 17h30  # ULTRA_ESTRATEGIA: 07h00, 12h30, 18h00, 21h15
        date(2026, 10, 16): ([7, 11.5, 15.5, 20], timedelta(minutes=90), 4),  # Paulo: 6x1 (SEIS1) às 7h00 em ponto  # Paulo: último carrossel às 21h (Reel R52 às 19h45)
        date(2026, 10, 12): ([7.5, 9, 14, 18, 21], timedelta(minutes=90), 5),  # JAN1 extra às 9h; Paulo quer o próximo às 14h
        date(2026, 10, 10): ([8, 11, 14, 17, 19, 21], timedelta(minutes=55), 6),  # grade antiga até o fim de 10/10
        date(2026, 10, 8): ([8, 11, 14, 17, 18, 20], timedelta(minutes=55), 6),  # ONU1 "já sobe" às 18h45
        date(2026, 10, 7): ([8, 11, 14, 17, 19, 20], timedelta(minutes=55), 6),
        date(2026, 10, 6): ([8, 12, 13, 14, 15, 17, 19, 21], timedelta(minutes=90), 8),
        date(2026, 10, 5): ([8, 11, 14, 17, 20], timedelta(minutes=90), 5),
        date(2026, 10, 4): ([8, 11, 15, 16, 20], timedelta(minutes=90), 5),  # 5: Gramsci extra às 17h, a pedido
    },
}
INICIO_DIA = 7  # nada sai antes das 7h BRT (e o cron vai até 23h59 BRT)


def brt_agora():
    return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=3)


def utc_para_brt(texto):
    return datetime.strptime(texto, "%Y-%m-%d %H:%M") - timedelta(hours=3)


def decidir(tipo, agora_brt, itens, forcar=False):
    """Função pura. Devolve (deve_publicar, motivo).
    itens = lista do JSON (cada um com "publicado" em UTC 'AAAA-MM-DD HH:MM' ou vazio)."""
    _, _, horarios, intervalo, maximo = TIPOS[tipo]
    horarios, intervalo, maximo = ESPECIAIS.get(tipo, {}).get(agora_brt.date(), (horarios, intervalo, maximo))
    if not any(not x.get("publicado") for x in itens):
        return False, f"[{tipo}] fila vazia"
    if forcar:
        return True, f"[{tipo}] FORCAR: publicando sem regras"

    if agora_brt.hour < INICIO_DIA:
        return False, f"[{tipo}] {agora_brt:%H:%M} BRT: antes das {INICIO_DIA}h, nada sai"

    pubs = [utc_para_brt(x["publicado"]) for x in itens if x.get("publicado")]
    hoje = agora_brt.date()
    feitos = sum(1 for p in pubs if p.date() == hoje)
    vencidos = sum(1 for h in horarios if h * 60 <= agora_brt.hour * 60 + agora_brt.minute)

    if feitos >= maximo:
        return False, f"[{tipo}] já saíram {feitos} hoje (máximo {maximo})"
    if feitos >= vencidos:
        return False, f"[{tipo}] {agora_brt:%H:%M} BRT: {feitos} publicados / {vencidos} horários vencidos: em dia"
    ultimo = max(pubs) if pubs else None
    if ultimo and agora_brt - ultimo < intervalo:
        falta = intervalo - (agora_brt - ultimo)
        return False, (f"[{tipo}] atrasado ({feitos}/{vencidos}), mas o último saiu às {ultimo:%d/%m %H:%M} BRT; "
                       f"espera mais {int(falta.total_seconds() // 60)} min")
    return True, f"[{tipo}] {agora_brt:%H:%M} BRT: {feitos} publicados / {vencidos} vencidos: publicando 1"


MAX_SLIDES = 10  # limite da API do Instagram para carrossel


def proximo_valido(itens, max_slides=MAX_SLIDES):
    """Primeiro item não publicado com <= max_slides slides. Retorna (item|None, [mensagens de pulo])."""
    logs = []
    # trava contra duplicata (04/10/2026: o carrossel de dados saiu 2x porque foi recolocado na fila
    # já publicado): mesmas imagens ou mesmo título de um item já publicado = pula
    ja = [x for x in itens if x.get("publicado")]
    ja_slides = {tuple(x.get("slides", [])) for x in ja}
    ja_titulos = {(x.get("titulo") or "").strip().lower() for x in ja}
    for c in itens:
        if c.get("publicado"):
            continue
        if tuple(c.get("slides", [])) in ja_slides or (c.get("titulo") or "").strip().lower() in ja_titulos:
            logs.append(f"PULADO {c.get('id')}: já publicado antes (mesmas imagens ou mesmo título)")
            continue
        # trava do OK (04/10/2026): o Paulo vê cada carrossel antes. Sem "aprovado": true, nunca sai (nem com forcar).
        if "slides" in c and not c.get("aprovado"):
            logs.append(f"PULADO {c.get('id')}: ainda sem o OK do Paulo (falta \"aprovado\": true)")
            continue
        n = len(c.get("slides", []))
        if n > max_slides:
            logs.append(f"PULADO {c.get('id')}: {n} slides (máximo {max_slides} no Instagram)")
            continue
        return c, logs
    return None, logs


def main():
    tipo = sys.argv[1] if len(sys.argv) > 1 else "reel"
    arquivo, chave = TIPOS[tipo][0], TIPOS[tipo][1]
    itens = json.load(open(arquivo))[chave]
    forcar = (os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
              and os.environ.get("FORCAR", "false") == "true")
    ok, motivo = decidir(tipo, brt_agora(), itens, forcar)
    print(motivo)
    saida = os.environ.get("GITHUB_OUTPUT")
    if saida:
        with open(saida, "a") as f:
            f.write(f"deve_publicar={'true' if ok else 'false'}\n")


if __name__ == "__main__":
    main()
