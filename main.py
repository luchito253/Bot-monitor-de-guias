import requests
import json
import os

TELEGRAM_BOT_TOKEN = os.getenv("9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo")
TELEGRAM_CHAT_ID = os.getenv("193021750")
NUMERO_GUIA = "78390170386"
ARCHIVO_ESTADO = "estado_guia.json"

def obtener_estado_coordinadora(guia):
    url = "https://coordinadora.com/cm-api/v1/rastreo/guia"
    payload = {"guia": str(guia)}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            pasos = data.get("data", {}).get("pasos", [])
            if pasos:
                ultimo = pasos[-1]
                estado = ultimo.get("nombre", "Sobre Coordinadora")
                fecha = ultimo.get("fecha", "")
                ciudad = ultimo.get("ciudad", "")
                return {"estado": estado, "detalle": f"{estado} ({ciudad}) - {fecha}".strip()}
            
            estado_gen = data.get("data", {}).get("estado_guia", "Sobre Coordinadora")
            return {"estado": estado_gen, "detalle": estado_gen}
        return {"estado": "Sobre Coordinadora", "detalle": "Guía en proceso"}
    except Exception as e:
        print(f"Error consultando Coordinadora: {e}")
        return {"estado": "Sobre Coordinadora", "detalle": "Guía en proceso"}

def enviar_mensaje_telegram(mensaje):
    print(f"Intento de envío -> TOKEN presente: {bool(TELEGRAM_BOT_TOKEN)} | CHAT_ID presente: {bool(TELEGRAM_CHAT_ID)}")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Faltan las variables de entorno de Telegram.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Respuesta HTTP Telegram: {r.status_code}")
        print(f"Respuesta Cuerpo Telegram: {r.text}")
    except Exception as e:
        print(f"Error conectando a Telegram: {e}")

def verificar_cambios():
    info_guia = obtener_estado_coordinadora(NUMERO_GUIA)
    estado_actual = info_guia["estado"]
    detalle_actual = info_guia["detalle"]

    mensaje = (
        f"🚚 *Prueba de Guía Coordinadora*\n\n"
        f"📋 *Guía:* `{NUMERO_GUIA}`\n"
        f"📌 *Estado:* *{estado_actual}*\n"
        f"📝 *Detalle:* {detalle_actual}"
    )
    enviar_mensaje_telegram(mensaje)

if __name__ == "__main__":
    verificar_cambios()
