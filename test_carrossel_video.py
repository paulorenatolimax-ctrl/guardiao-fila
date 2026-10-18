#!/usr/bin/env python3
"""Dry-run (sem rede, sem token, nada publicado) do carrossel com slide .mp4.
Rodar: python3 -m unittest test_carrossel_video -v"""
import unittest
from carrossel_midia import criar_filhos, url_slide, esperar, e_video

API, UID, TOK, REPO = "https://graph.instagram.com/v21.0", "UID", "TOK", "dono/repo"

class FakeAPI:
    def __init__(self, estados=("IN_PROGRESS", "IN_PROGRESS", "FINISHED")):
        self.posts, self.gets, self.estados, self.n = [], [], list(estados), 0
    def __call__(self, url, dados=None):
        if dados is None:
            self.gets.append(url); st = self.estados.pop(0) if self.estados else "FINISHED"
            return {"status_code": st, "status": st}
        self.posts.append(dados); self.n += 1
        return {"id": f"c{self.n}"}

class TestVideoNoCarrossel(unittest.TestCase):
    def test_urls(self):
        self.assertTrue(e_video("x.MP4")); self.assertFalse(e_video("x.jpg"))
        self.assertEqual(url_slide("car 1.jpg", REPO), "https://raw.githubusercontent.com/dono/repo/main/carrosseis/car%201.jpg")
        self.assertEqual(url_slide("car338_11.mp4", REPO), "https://github.com/dono/repo/releases/download/videos/car338_11.mp4")

    def test_misto_cria_video_e_espera_finished(self):
        api = FakeAPI()
        filhos = criar_filhos(["a.jpg", "b.mp4", "c.jpg"], api, API, UID, TOK, REPO, dormir=lambda s: None)
        self.assertEqual(filhos, ["c1", "c2", "c3"])  # ordem preservada
        img, vid = api.posts[0], api.posts[1]
        self.assertIn("image_url", img); self.assertNotIn("media_type", img)
        self.assertEqual(vid["media_type"], "VIDEO"); self.assertEqual(vid["is_carousel_item"], "true")
        self.assertTrue(vid["video_url"].endswith("/releases/download/videos/b.mp4"))
        self.assertEqual(len(api.gets), 3)  # consultou até FINISHED
        self.assertTrue(all("/c2?fields=status_code" in g for g in api.gets))

    def test_so_imagens_nao_consulta(self):
        api = FakeAPI(); criar_filhos(["a.jpg", "b.jpg"], api, API, UID, TOK, REPO, dormir=lambda s: None)
        self.assertEqual(api.gets, [])

    def test_erro_do_video_aborta(self):
        api = FakeAPI(estados=("IN_PROGRESS", "ERROR"))
        with self.assertRaises(RuntimeError):
            criar_filhos(["a.jpg", "b.mp4"], api, API, UID, TOK, REPO, dormir=lambda s: None)

    def test_tempo_esgotado_aborta(self):
        api = FakeAPI(estados=["IN_PROGRESS"] * 10)
        with self.assertRaises(RuntimeError):
            esperar(api, API, TOK, "c9", tentativas=3, dormir=lambda s: None)

if __name__ == "__main__":
    unittest.main()
