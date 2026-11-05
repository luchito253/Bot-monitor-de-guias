import requests
import json
import os

# Lee automáticamente de GitHub Secrets o del entorno local
TELEGRAM_BOT_TOKEN = os.getenv("9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo")
TELEGRAM_CHAT_ID = os.getenv("193021750")
NUMERO_GUIA = "78390170386"
ARCHIVO_ESTADO = "estado_guia.json"

def obtener_estado_coordinadora(guia):
    url = "https://coordinadora.com/cm-api/v1/rastreo/guia"
    payload = {"guia": str(guia)}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "pasos" in data["data"]:
                pasos = data["data"]["pasos"]
                if pasos:
                    ultimo_paso = pasos[-1]
                    estado = ultimo_paso.get("nombre", "Estado no identificado")
                    fecha = ultimo_paso.get("fecha", "")
                    ubicacion = ultimo_paso.get("ciudad", "")
                    return {
                        "estado": estado,
                        "detalle": f"{estado} ({ubicacion}) - {fecha}".strip()
                    }
            
            estado_general = data.get("data", {}).get("estado_guia")
            if estado_general:
                return {"estado": estado_general, "detalle": estado_general}

        return None
    except Exception as e:
        print(f"Error al consultar la guía en Coordinadora: {e}")
        return None

def enviar_mensaje_telegram(mensaje):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: No se encontraron TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error al enviar mensaje a Telegram: {e}")

def verificar_cambios():
    info_guia = obtener_estado_coordinadora(NUMERO_GUIA)
    
    if not info_guia:
        print("No se pudo obtener la información de la guía.")
        return

    estado_actual = info_guia["estado"]
    detalle_actual = info_guia["detalle"]

    ultimo_estado = None
    if os.path.exists(ARCHIVO_ESTADO):
        with open(ARCHIVO_ESTADO, "r", encoding="utf-8") as f:
            datos = json.load(f)
            ultimo_estado = datos.get("estado")

    if estado_actual != ultimo_estado:
        mensaje = (
            f"🚚 *Actualización de Guía Coordinadora*\n\n"
            f"📋 *Guía:* `{NUMERO_GUIA}`\n"
            f"📌 *Nuevo Estado:* *{estado_actual}*\n"
            f"📝 *Detalle:* {detalle_actual}"
        )
        enviar_mensaje_telegram(mensaje)
        
        with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
            json.dump({"estado": estado_actual, "detalle": detalle_actual}, f, ensure_ascii=False, indent=2)
        print(f"Cambio detectado. Estado actualizado a: {estado_actual}")
    else:
        print("Sin novedades. La guía sigue en el mismo estado.")

if __name__ == "__main__":
    verificar_cambios()