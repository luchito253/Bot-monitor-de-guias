import json
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = "9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo"
CHAT_ID = "193021750"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    respuesta = requests.post(url, json=payload)
    print(f"[Telegram] Mensaje enviado. Respuesta: {respuesta.status_code}")

def consultar_coordinadora(guia):
    url = f"https://coordinadora.com/wp-json/rgc/v1/detail_tracking?remission_code={guia}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    print(f"  -> Conectando a Coordinadora...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  -> Código HTTP: {response.status_code}")
        if response.status_code == 200:
            datos = response.json()
            return datos.get("estado_actual", "Estado desconocido")
    except Exception as e:
        print(f"  -> Error consultando Coordinadora: {e}")
    return None

def consultar_servientrega(guia):
    url = f"https://www.servientrega.com/wps/portal/Colombia/transacciones-personas/rastreo-envios/detalle?guia={guia}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    print(f"  -> Conectando a Servientrega...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  -> Código HTTP: {response.status_code}")
        soup = BeautifulSoup(response.text, 'html.parser')
        estado_div = soup.find('div', class_='estado-guia')
        if estado_div:
            return estado_div.text.strip()
        else:
            print("  -> No se encontró el recuadro del estado en el HTML.")
    except Exception as e:
        print(f"  -> Error consultando Servientrega: {e}")
    return None

def main():
    print("Iniciando bot de rastreo...")
    with open('guias.json', 'r') as f:
        guias = json.load(f)
    
    print(f"Guías a rastrear: {guias}")

    try:
        with open('estado_guias.json', 'r') as f:
            estados_previos = json.load(f)
    except FileNotFoundError:
        estados_previos = {}

    cambios_detectados = False

    for guia, transportadora in guias.items():
        print(f"\n[*] Revisando guía: {guia} ({transportadora})")
        estado_actual = None
        
        if transportadora.lower() == 'coordinadora':
            estado_actual = consultar_coordinadora(guia)
        elif transportadora.lower() == 'servientrega':
            estado_actual = consultar_servientrega(guia)
            
        if not estado_actual:
            print(f"[!] No se pudo extraer el estado de {guia}. Se omitirá.")
            continue

        print(f"[+] Estado extraído: {estado_actual}")
        estado_previo = estados_previos.get(guia)
        print(f"[-] Estado anterior guardado: {estado_previo}")

        if estado_actual != estado_previo:
            print("[!] ¡HAY UN CAMBIO! Preparando envío a Telegram...")
            mensaje = f"📦 *Actualización de Envío*\n\n*Transportadora:* {transportadora.capitalize()}\n*Guía:* `{guia}`\n*Nuevo Estado:* {estado_actual}"
            enviar_mensaje_telegram(mensaje)
            
            estados_previos[guia] = estado_actual
            cambios_detectados = True
        else:
            print("[=] El estado no ha cambiado.")

    if cambios_detectados:
        print("\nGuardando nuevos estados en el archivo...")
        with open('estado_guias.json', 'w') as f:
            json.dump(estados_previos, f, indent=4)
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
