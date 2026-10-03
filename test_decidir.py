#!/usr/bin/env python3
"""Testes da regra de recuperação (decidir.py). Rodar: python3 -m unittest test_decidir -v"""
import unittest
from datetime import datetime, timedelta
from decidir import decidir


def brt(h, m=0, dia=5):  # 05/10 = dia normal (03 e 04 são eleição)
    return datetime(2026, 10, dia, h, m)


def pub_utc(dt_brt):
    """'publicado' no JSON é UTC."""
    return {"publicado": (dt_brt + timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")}


PEND = [{"publicado": ""}, {}]  # sempre há pendentes na fila


class TestCarrossel(unittest.TestCase):
    def test_dia_normal_no_horario(self):
        ok, _ = decidir("carrossel", brt(8, 5), PEND)
        self.assertTrue(ok)
        # já saiu o das 8h: às 9h nada a fazer
        ok, _ = decidir("carrossel", brt(9, 0), [pub_utc(brt(8, 5))] + PEND)
        self.assertFalse(ok)

    def test_antes_do_horario_nao_publica(self):
        ok, _ = decidir("carrossel", brt(7, 55), PEND)
        self.assertFalse(ok)

    def test_cron_atrasado_2h_publica_o_atrasado(self):
        ok, _ = decidir("carrossel", brt(10, 0), PEND)  # 8h perdido
        self.assertTrue(ok)

    def test_dois_horarios_perdidos_um_por_vez_com_90min(self):
        # 12h: 8h e 11h vencidos, nada publicado -> publica 1
        ok, _ = decidir("carrossel", brt(12, 0), PEND)
        self.assertTrue(ok)
        itens = [pub_utc(brt(12, 0))] + PEND
        # 5 min depois: ainda 1/2, mas último há 5 min -> espera
        self.assertFalse(decidir("carrossel", brt(12, 5), itens)[0])
        self.assertFalse(decidir("carrossel", brt(13, 29), itens)[0])
        # 90 min depois -> publica o segundo
        self.assertTrue(decidir("carrossel", brt(13, 30), itens)[0])
        itens = [pub_utc(brt(12, 0)), pub_utc(brt(13, 30))] + PEND
        self.assertFalse(decidir("carrossel", brt(15, 0), itens)[0])  # 2/2 em dia

    def test_todos_do_dia_ja_publicados(self):
        itens = [pub_utc(brt(8, 5)), pub_utc(brt(11, 5)), pub_utc(brt(20, 5))] + PEND
        self.assertFalse(decidir("carrossel", brt(22, 0), itens)[0])

    def test_maximo_do_dia_mesmo_com_forcados_antes(self):
        itens = [pub_utc(brt(7, 10)), pub_utc(brt(9, 0)), pub_utc(brt(11, 0))] + PEND
        self.assertFalse(decidir("carrossel", brt(21, 0), itens)[0])

    def test_antes_das_7h_nao_publica(self):
        # 20h de ontem perdido não é recuperado de madrugada; e de madrugada nada sai
        itens = [pub_utc(brt(8, 0, dia=2)), pub_utc(brt(11, 0, dia=2))] + PEND
        self.assertFalse(decidir("carrossel", brt(6, 55), itens)[0])
        self.assertFalse(decidir("carrossel", brt(2, 0), PEND)[0])

    def test_post_de_ontem_23h_utc_conta_como_ontem(self):
        # 22h BRT de ontem = 01:00 UTC de hoje: não pode contar como post de hoje
        itens = [pub_utc(brt(22, 0, dia=2))] + PEND
        self.assertTrue(decidir("carrossel", brt(8, 5), itens)[0])

    def test_forcar(self):
        itens = [pub_utc(brt(8, 0)), pub_utc(brt(11, 0)), pub_utc(brt(20, 0))] + PEND
        self.assertTrue(decidir("carrossel", brt(3, 0), itens, forcar=True)[0])
        self.assertTrue(decidir("carrossel", brt(20, 1), itens, forcar=True)[0])

    def test_fila_vazia(self):
        self.assertFalse(decidir("carrossel", brt(9, 0), [pub_utc(brt(8, 0, dia=2))])[0])
        self.assertFalse(decidir("carrossel", brt(9, 0), [pub_utc(brt(8, 0, dia=2))], forcar=True)[0])


class TestEleicao(unittest.TestCase):
    @unittest.skip('modo eleição cancelado pelo Paulo em 03/10/2026')
    def test_dia_especial_grade_2h(self):
        self.assertTrue(decidir("carrossel", brt(10, 0, dia=4), PEND)[0])
        itens = [pub_utc(brt(10, 0, dia=4))] + PEND
        self.assertTrue(decidir("carrossel", brt(11, 40, dia=4), itens)[0])   # 8h vencido, 100 min ok
        self.assertFalse(decidir("carrossel", brt(11, 39, dia=4), itens)[0])  # só 99 min
        itens = [pub_utc(brt(8 + 2 * i, 0, dia=4)) for i in range(6)] + PEND
        self.assertFalse(decidir("carrossel", brt(22, 30, dia=4), itens)[0])  # máximo 6
        self.assertTrue(decidir("carrossel", brt(22, 0, dia=3), [pub_utc(brt(20, 0, dia=3))] + PEND)[0])

    def test_dia_normal_volta(self):
        itens = [pub_utc(brt(8, 0, dia=5)), pub_utc(brt(11, 0, dia=5))] + PEND
        self.assertFalse(decidir("carrossel", brt(12, 0, dia=5), itens)[0])   # 2/2 em dia
        self.assertFalse(decidir("carrossel", brt(10, 0, dia=5), [pub_utc(brt(8, 0, dia=5))] + PEND)[0])
        itens = [pub_utc(brt(h, 0, dia=5)) for h in (8, 11, 20)] + PEND
        self.assertFalse(decidir("carrossel", brt(22, 0, dia=5), itens)[0])   # máx 3


class TestReel(unittest.TestCase):
    def test_dia_normal(self):
        self.assertFalse(decidir("reel", brt(12, 55), PEND)[0])
        self.assertTrue(decidir("reel", brt(13, 0), PEND)[0])

    def test_atrasado_2h(self):
        self.assertTrue(decidir("reel", brt(15, 0), PEND)[0])

    def test_dois_perdidos_intervalo_4h(self):
        itens = [pub_utc(brt(20, 0))] + PEND  # 13h saiu às 20h (atrasado)
        self.assertFalse(decidir("reel", brt(23, 0), itens)[0])   # 19h ainda pendente, mas só 3h
        self.assertTrue(decidir("reel", brt(23, 59), [pub_utc(brt(19, 50))] + PEND)[0])

    def test_dois_publicados(self):
        itens = [pub_utc(brt(13, 0)), pub_utc(brt(19, 0))] + PEND
        self.assertFalse(decidir("reel", brt(23, 30), itens)[0])


class TestTeste(unittest.TestCase):
    def test_situacao_de_hoje_03_10(self):
        # teste das 8h saiu 09:23 BRT; às 14h53 o das 14h ainda não saiu -> recupera
        itens = [pub_utc(brt(21, 26, dia=2)), pub_utc(brt(9, 23))] + PEND
        self.assertTrue(decidir("teste", brt(14, 55), itens)[0])
        itens.append(pub_utc(brt(14, 55)))
        self.assertFalse(decidir("teste", brt(16, 0), itens)[0])   # em dia (2/2)
        self.assertTrue(decidir("teste", brt(18, 0), itens)[0])    # 18h, e 3h05 desde o último

    def test_tres_no_dia(self):
        itens = [pub_utc(brt(8, 0)), pub_utc(brt(14, 0)), pub_utc(brt(18, 0))] + PEND
        self.assertFalse(decidir("teste", brt(23, 0), itens)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
