import json
import requests
from bs4 import BeautifulSoup

# Credenciales configuradas directamente
TELEGRAM_TOKEN = "9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo"
CHAT_ID = "193021750"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def consultar_coordinadora(guia):
    url = f"https://api.coordinadora.com/cm-control-estado-guias/api/v1/guias/{guia}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            datos = response.json()
            return datos.get("estado_actual", "Estado desconocido")
    except Exception as e:
        print(f"Error consultando Coordinadora: {e}")
    return None

def consultar_servientrega(guia):
    url = f"https://www.servientrega.com/wps/portal/Colombia/transacciones-personas/rastreo-envios/detalle?guia={guia}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        estado_div = soup.find('div', class_='estado-guia')
        if estado_div:
            return estado_div.text.strip()
    except Exception as e:
        print(f"Error consultando Servientrega: {e}")
    return None

def main():
    with open('guias.json', 'r') as f:
        guias = json.load(f)

    try:
        with open('estado_guias.json', 'r') as f:
            estados_previos = json.load(f)
    except FileNotFoundError:
        estados_previos = {}

    cambios_detectados = False

    for guia, transportadora in guias.items():
        estado_actual = None
        
        if transportadora.lower() == 'coordinadora':
            estado_actual = consultar_coordinadora(guia)
        elif transportadora.lower() == 'servientrega':
            estado_actual = consultar_servientrega(guia)
            
        if not estado_actual:
            continue

        estado_previo = estados_previos.get(guia)

        if estado_actual != estado_previo:
            mensaje = f"📦 *Actualización de Envío*\n\n*Transportadora:* {transportadora.capitalize()}\n*Guía:* `{guia}`\n*Nuevo Estado:* {estado_actual}"
            enviar_mensaje_telegram(mensaje)
            
            estados_previos[guia] = estado_actual
            cambios_detectados = True

    if cambios_detectados:
        with open('estado_guias.json', 'w') as f:
            json.dump(estados_previos, f, indent=4)

if __name__ == "__main__":
    main()