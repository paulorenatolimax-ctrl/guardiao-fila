#!/usr/bin/env python3
"""Vigia do funil: um navegador de verdade (celular, sem login) faz o caminho de quem compra.

07/10/2026: criado. 27/10/2026: reescrito. Por 19 dias o botão da Trilha só abria o MENSAL e o vigia
dava verde, porque só conferia "chegou na Hotmart". Agora confere O PLANO e O PREÇO de cada caminho:

  1. /trilha → "Liberar a Trilha inteira" → para no /checkout com os 2 planos → Anual → Hotmart ANUAL
  2. /trilha → "Liberar a Trilha inteira" → escolhe Mensal → Hotmart MENSAL
  3. link dos Stories/ManyChat (/checkout?plano=annual&assinar=1) → para no /checkout → Hotmart ANUAL
  4. /checkout?plano=monthly → Hotmart MENSAL
  5. home → botão de assinar → /checkout com os 2 planos
  6. /guia → oferta → /checkout com os 2 planos

Falhou qualquer um: sai com erro 1, grava vigia_falhas.txt; o workflow apita no celular (ntfy) e abre issue.
"""
import os
import re
import sys
from playwright.sync_api import sync_playwright

BASE = "https://jornadafilosofica.com"
# Ofertas da Hotmart (src/lib/support.ts do jornada-scriptorium). Fundador até 31/10; depois, o cheio.
ANUAL = {"euyb5ohj": "Fundador R$ 147", "5im4vxfy": "cheio R$ 197"}
MENSAL = {"i6nt77qm": "Fundador R$ 19,90", "qzbuosxy": "cheio"}
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) vigia-funil"

falhas, oks = [], []


def oferta(url):
    m = re.search(r"[?&]off=([A-Za-z0-9]+)", url)
    return m.group(1) if m else None


with sync_playwright() as p:
    nav = p.chromium.launch(channel=os.environ.get("PW_CHANNEL") or None)

    def pagina():
        ctx = nav.new_context(viewport={"width": 390, "height": 844}, user_agent=UA)
        return ctx, ctx.new_page()

    def ficou_no_checkout(pg, nome):
        """O cliente precisa VER a escolha: nada de pular sozinho para a Hotmart."""
        pg.wait_for_url("**/checkout**", timeout=30000)
        pg.wait_for_timeout(5000)
        if "hotmart.com" in pg.url:
            raise AssertionError(f"pulou sozinho para a Hotmart sem mostrar os planos (off={oferta(pg.url)})")
        for t in ("Plano Anual", "Plano Mensal"):
            if not pg.get_by_text(t, exact=False).first.is_visible():
                raise AssertionError(f"checkout sem '{t}' visível")

    def pagar(pg, plano):
        """Escolhe o plano, clica em Assinar e confere a oferta e o preço na Hotmart."""
        nome_plano = "Plano Anual" if plano == "anual" else "Plano Mensal"
        if plano == "mensal":
            pg.get_by_text("Plano Mensal", exact=False).first.click(timeout=15000)
            pg.wait_for_timeout(500)
        pg.get_by_role("button", name=re.compile(f"Assinar {nome_plano}", re.I)).first.click(timeout=15000)
        pg.wait_for_url("**pay.hotmart.com/**", timeout=30000)
        off = oferta(pg.url)
        esperado = ANUAL if plano == "anual" else MENSAL
        if off not in esperado:
            errado = "MENSAL" if off in MENSAL else ("ANUAL" if off in ANUAL else "desconhecida")
            raise AssertionError(f"pediu {plano.upper()} e a Hotmart abriu a oferta {off} ({errado})")
        pg.wait_for_timeout(4000)
        texto = pg.inner_text("body")
        marca = "/ ano" if plano == "anual" else "/ mês"
        if marca not in texto.replace("/ano", "/ ano").replace("/mês", "/ mês"):
            raise AssertionError(f"Hotmart abriu {off} mas a página não mostra '{marca}' (oferta desativada?)")
        preco = re.search(r"R\$\s?[\d.,]+\s?/\s?(ano|mês)", texto)
        return f"{esperado[off]} ({preco.group(0) if preco else off})"

    def caminho(nome, url, passos):
        ctx, pg = pagina()
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            resultado = passos(pg)
            oks.append(f"OK  {nome}: {resultado}")
            print(oks[-1])
        except Exception as e:
            falhas.append(f"{nome}: {str(e).splitlines()[0][:220]} | parou em {pg.url[:120]}")
            print("FALHA", falhas[-1])
        finally:
            ctx.close()

    def botao_trilha(pg):
        pg.wait_for_timeout(2500)
        pg.get_by_text("Liberar a Trilha inteira", exact=False).first.click(timeout=20000)

    def trilha_anual(pg):
        botao_trilha(pg); ficou_no_checkout(pg, "trilha"); return pagar(pg, "anual")

    def trilha_mensal(pg):
        botao_trilha(pg); ficou_no_checkout(pg, "trilha"); return pagar(pg, "mensal")

    def link_direto(pg):
        ficou_no_checkout(pg, "link"); return pagar(pg, "anual")

    def checkout_mensal(pg):
        ficou_no_checkout(pg, "mensal"); return pagar(pg, "mensal")

    def home(pg):
        pg.wait_for_timeout(2500)
        pg.locator("a.js-assinar, a[href*='/checkout']").first.click(timeout=20000)
        ficou_no_checkout(pg, "home"); return "para no checkout com os 2 planos"

    def guia(pg):
        pg.wait_for_timeout(2500)
        href = pg.locator("a[href*='/checkout']").first.get_attribute("href")
        pg.goto(href if href.startswith("http") else BASE + href, wait_until="domcontentloaded")
        ficou_no_checkout(pg, "guia"); return "para no checkout com os 2 planos"

    caminho("Trilha → Liberar → ANUAL", BASE + "/trilha?src=teste_bot", trilha_anual)
    caminho("Trilha → Liberar → MENSAL", BASE + "/trilha?src=teste_bot", trilha_mensal)
    caminho("Link Story/ManyChat → ANUAL", BASE + "/checkout?plano=annual&src=teste_bot&assinar=1", link_direto)
    caminho("Checkout mensal → MENSAL", BASE + "/checkout?plano=monthly&src=teste_bot", checkout_mensal)
    caminho("Home → assinar", BASE + "/?src=teste_bot", home)
    caminho("Guia → oferta", BASE + "/guia?src=teste_bot", guia)
    nav.close()

if falhas:
    open("vigia_falhas.txt", "w").write("\n".join(falhas))
    print(f"\n{len(falhas)} caminho(s) quebrado(s).")
    sys.exit(1)
print("\nFunil inteiro certo: os 2 planos aparecem e cada um chega à oferta certa na Hotmart.")
