"""Aviso no WhatsApp via CallMeBot. Nunca quebra quem chama: sem secrets ou com falha, só loga."""
import os, urllib.parse, urllib.request

def avisar_whatsapp(texto):
    fone, chave = os.environ.get("CALLMEBOT_PHONE"), os.environ.get("CALLMEBOT_APIKEY")
    if not fone or not chave:
        print("aviso WhatsApp: secrets CALLMEBOT_* ausentes, pulando"); return False
    try:
        q = urllib.parse.urlencode({"phone": fone, "text": texto, "apikey": chave})
        urllib.request.urlopen("https://api.callmebot.com/whatsapp.php?" + q, timeout=10).read()
        print("aviso WhatsApp enviado"); return True
    except Exception as e:
        print("aviso WhatsApp falhou (ignorado):", type(e).__name__); return False

def avisar_publicado(titulo, permalink, tipo="Carrossel"):
    return avisar_whatsapp(f"🎵 {tipo} no ar agora: {titulo} — põe a música: {permalink}")
