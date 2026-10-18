#!/bin/bash
# Sobe um slide de vídeo (.mp4) como asset do release "videos" (host do video_url). Não publica nada.
# Uso: ./subir_video_slide.sh car338_11.mp4   (o nome precisa ser igual ao que está em "slides" no carrosseis.json)
set -e; f="$1"; [ -f "$f" ] || { echo "arquivo não existe: $f"; exit 1; }
ffprobe -v error -show_entries format=duration,size -of compact "$f"
gh release upload videos "$f" --clobber -R "${REPO:-paulorenatolimax-ctrl/guardiao-fila}" && echo "OK: https://github.com/${REPO:-paulorenatolimax-ctrl/guardiao-fila}/releases/download/videos/$(basename "$f")"
