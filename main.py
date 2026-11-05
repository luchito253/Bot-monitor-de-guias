import requests
from bs4 import BeautifulSoup
import json
import os

TELEGRAM_BOT_TOKEN = os.getenv("9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo")
TELEGRAM_CHAT_ID = os.getenv("193021750")
NUMERO_GUIA = "78390170386"
ARCHIVO_ESTADO = "estado_guia.json"

def obtener_estado_coordinadora(guia):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html, */*"
    }
    
    # 1. Intentar vía API directa de rastreo
    try:
        url_api = f"https://coordinadora.com/cm-api/v1/rastreo/guia"
        payload = {"guia": str(guia)}
        res = requests.post(url_api, json=payload, headers=headers, timeout=12)
        
        if res.status_code == 200:
            data = res.json()
            # Si responde con la estructura de pasos
            pasos = data.get("data", {}).get("pasos", [])
            if pasos:
                ultimo = pasos[-1]
                estado = ultimo.get("nombre") or ultimo.get("descripcion") or "En Proceso"
                fecha = ultimo.get("fecha", "")
                ciudad = ultimo.get("ciudad", "")
                return {
                    "estado": estado,
                    "detalle": f"{estado} ({ciudad}) - {fecha}".strip()
                }
            
            # Si responde con estado principal
            estado_gen = data.get("data", {}).get("estado_guia") or data.get("data", {}).get("estado")
            if estado_gen:
                return {"estado": estado_gen, "detalle": estado_gen}
    except Exception as e:
        print(f"Petición API falló: {e}")

    # 2. Respaldo mediante Scraping Web si la API interna restringe el acceso
    try:
        url_web = f"https://coordinadora.com/rastreo/rastreo-de-guia/detalle-de-rastreo-de-guia/?guia={guia}"
        res_web = requests.get(url_web, headers=headers, timeout=12)
        if res_web.status_code == 200:
            soup = BeautifulSoup(res_web.text, "html.parser")
            # Buscar elementos comunes de estado en la página
            estado_element = soup.find(class_="estado") or soup.find("h3") or soup.find(class_="step-active")
            if estado_element:
                texto_estado = estado_element.text.strip()
                return {"estado": texto_estado, "detalle": texto_estado}
    except Exception as e:
        print(f"Petición HTML falló: {e}")

    return None

def enviar_mensaje_telegram(mensaje):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Error: No se encontraron los Secretos de Telegram en GitHub.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"Respuesta Telegram Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Error enviando a Telegram: {e}")

def verificar_cambios():
    info_guia = obtener_estado_coordinadora(NUMERO_GUIA)
    
    if not info_guia:
        print("No se pudo obtener la información de la guía.")
        return

    estado_actual = info_guia["estado"]
    detalle_actual = info_guia["detalle"]

    # FORZAMOS EL MENSAJE PARA LA PRUEBA (sin comparar si cambió)
    mensaje = (
        f"🚚 *Prueba de Guía Coordinadora*\n\n"
        f"📋 *Guía:* `{NUMERO_GUIA}`\n"
        f"📌 *Estado:* *{estado_actual}*\n"
        f"📝 *Detalle:* {detalle_actual}"
    )
    enviar_mensaje_telegram(mensaje)
    
    # Guardamos siempre para forzar la creación del archivo en GitHub
    with open(ARCHIVO_ESTADO, "w", encoding="utf-8") as f:
        json.dump({"estado": estado_actual, "detalle": detalle_actual}, f, ensure_ascii=False, indent=2)
    print(f"Mensaje enviado a Telegram. Estado actual: {estado_actual}")

if __name__ == "__main__":
    verificar_cambios()
