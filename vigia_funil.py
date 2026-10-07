#!/usr/bin/env python3
"""Vigia do funil (07/10/2026): de 2 em 2 h, um navegador de verdade faz o caminho de quem compra.

Caminhos testados (todos precisam terminar em pay.hotmart.com):
  1. /trilha → botão "Liberar a Trilha inteira"
  2. /checkout?plano=annual&assinar=1 (link dos Stories/ManyChat)
  3. /checkout (página normal) → botão "Assinar Plano Anual"
Se algum falhar, sai com erro 1: o workflow abre uma issue no GitHub (vira e-mail para o Paulo).
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "https://jornadafilosofica.com"
falhas = []
with sync_playwright() as p:
    nav = p.chromium.launch()
    def caminho(nome, url, clicar=None):
        pg = nav.new_page(viewport={"width": 390, "height": 844},
                          user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) vigia-funil")
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            if clicar:
                pg.wait_for_timeout(2500)
                pg.get_by_text(clicar, exact=False).first.click(timeout=20000)
            pg.wait_for_url("**pay.hotmart.com/**", timeout=30000)
            print(f"OK  {nome}: {pg.url.split('?')[0]}")
        except Exception as e:
            falhas.append(f"{nome}: parou em {pg.url} ({str(e).splitlines()[0][:150]})")
            print("FALHA", falhas[-1])
        finally:
            pg.close()
    caminho("Trilha → Liberar a Trilha inteira", BASE + "/trilha?src=teste_bot", "Liberar a Trilha inteira")
    caminho("Link direto (Story/ManyChat)", BASE + "/checkout?plano=annual&src=teste_bot&assinar=1")
    caminho("Checkout → Assinar Plano Anual", BASE + "/checkout?plano=annual&src=teste_bot", "Assinar Plano Anual")
    nav.close()

if falhas:
    open("vigia_falhas.txt", "w").write("\n".join(falhas))
    sys.exit(1)
print("Funil inteiro chegando na Hotmart.")
