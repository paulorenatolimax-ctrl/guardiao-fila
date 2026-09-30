"""Sobe no YouTube Shorts os Reels já publicados no Instagram que ficaram sem Short.
Uso (GitHub Actions): NUMEROS="303,309,300" python3 youtube_atrasados.py
Cota do YouTube: ~6 envios por dia; mande no máximo 5 por vez."""
import json, os, time
import publicar_youtube

REPO = "paulorenatolimax-ctrl/guardiao-fila"
TAG = os.environ.get("RELEASE_TAG", "videos")
numeros = [int(x) for x in os.environ.get("NUMEROS", "").split(",") if x.strip()]
fila = json.load(open("fila.json", encoding="utf-8"))
feitos = []
for n in numeros:
    item = next((x for x in fila["fila"] if x.get("n") == n), None)
    if not item or not item.get("publicado") or item.get("youtube_publicado"):
        print(f"{n}: pulado (não publicado no Instagram ou já está no YouTube)")
        continue
    url = f"https://github.com/{REPO}/releases/download/{TAG}/{item['asset']}"
    try:
        yt_id = publicar_youtube.publicar_short(url, item)
        item["youtube_publicado"] = time.strftime("%Y-%m-%d %H:%M")
        item["youtube_id"] = yt_id
        feitos.append(n)
        print(f"{n}: no YouTube ({yt_id})")
    except Exception as e:
        print(f"{n}: FALHOU no YouTube: {e}")
    json.dump(fila, open("fila.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("Subidos:", feitos)
