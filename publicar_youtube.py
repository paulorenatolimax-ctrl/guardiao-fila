#!/usr/bin/env python3
"""Módulo de publicação no YouTube Shorts via YouTube Data API v3.
Usa as credenciais OAuth (Client ID, Client Secret e Refresh Token).
"""
import os
import sys
import json
import urllib.request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def obter_servico_youtube():
    client_id = os.environ.get("YOUTUBE_CLIENT_ID")
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.environ.get("YOUTUBE_REFRESH_TOKEN")

    # Fallback para arquivo local se estiver rodando na máquina do Paulo
    if not (client_id and client_secret and refresh_token):
        local_token = "/Users/paulo1844/Documents/7_TECNOLOGIA E IA/Tecnologia e IA/Sandeco/Mira/.mira/youtube_token.json"
        if os.path.exists(local_token):
            with open(local_token) as f:
                d = json.load(f)
                client_id = d.get("client_id")
                client_secret = d.get("client_secret")
                refresh_token = d.get("refresh_token")

    if not (client_id and client_secret and refresh_token):
        raise ValueError("Credenciais do YouTube não encontradas (variáveis de ambiente ou token local).")

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES
    )
    return build("youtube", "v3", credentials=creds)

def gerar_titulo_shorts(item):
    """Gera um título de alto impacto para o Shorts (máx 100 caracteres com #Shorts)."""
    # Pega primeira linha da legenda ou um título limpo
    linhas = [l.strip() for l in item["legenda"].split("\n") if l.strip()]
    primeira = linhas[0] if linhas else f"Vídeo {item['n']}"
    # Remove hashtags ou formatações da primeira linha se houver
    primeira = primeira.replace("#", "").strip()
    
    # Se passar de 90 chars, trunca
    if len(primeira) > 88:
        primeira = primeira[:85] + "..."
        
    return f"{primeira} #Shorts"

def publicar_short(caminho_ou_url_video, item, privacy="public"):
    """Baixa o vídeo se for URL e publica no canal do YouTube como Short."""
    youtube = obter_servico_youtube()
    arquivo_local = caminho_ou_url_video
    baixado = False

    if caminho_ou_url_video.startswith("http://") or caminho_ou_url_video.startswith("https://"):
        arquivo_local = f"temp_yt_{item['n']}.mp4"
        print(f"  [YouTube] Baixando vídeo da release: {caminho_ou_url_video}...")
        urllib.request.urlretrieve(caminho_ou_url_video, arquivo_local)
        baixado = True

    try:
        titulo = gerar_titulo_shorts(item)
        descricao = f"{item['legenda']}\n\nInscreva-se no canal para mais análises e defesa da família.\n\n#Shorts #ManifestoConservadorista #Educacao #Familia #Valores"
        tags = ["Shorts", "Manifesto Conservadorista", "Educação", "Família", "Valores", "Cultura", "Filosofia"]

        print(f"  [YouTube] Subindo Short: '{titulo}'...")
        corpo = {
            "snippet": {
                "title": titulo,
                "description": descricao,
                "tags": tags,
                "categoryId": "27"  # Educação
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(arquivo_local, chunksize=-1, resumable=True, mimetype="video/mp4")
        req = youtube.videos().insert(part="snippet,status", body=corpo, media_body=media)
        res = req.execute()

        video_id = res["id"]
        print(f"  [YouTube] SUCESSO! Vídeo publicado: https://youtube.com/shorts/{video_id}")
        return video_id
    finally:
        if baixado and os.path.exists(arquivo_local):
            os.remove(arquivo_local)

if __name__ == "__main__":
    # Teste de importação / conexão
    try:
        yt = obter_servico_youtube()
        ch = yt.channels().list(part="snippet", mine=True).execute()
        print(f"Conexão YouTube ativa com: {ch['items'][0]['snippet']['title']}")
    except Exception as e:
        print(f"Erro ao conectar: {e}")
