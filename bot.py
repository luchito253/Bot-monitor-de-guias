import json
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = "9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo"
CHAT_ID = "193021750"
SCRAPERAPI_KEY = "cb35454830fc0ca5951258af8e2ae8ac"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
    print(f"[Telegram] Mensaje enviado.")

def consultar_coordinadora(guia):
    target_url = f"https://coordinadora.com/rastreo/rastreo-de-guia/?guia={guia}"
    payload = {
        'api_key': SCRAPERAPI_KEY,
        'url': target_url,
        'render': 'true', 
        'country_code': 'co'
    }
    print("  -> Conectando a Coordinadora vía ScraperAPI...")
    try:
        response = requests.get('http://api.scraperapi.com/', params=payload, timeout=90)
        print(f"  -> Código HTTP ScraperAPI: {response.status_code}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        texto_limpio = soup.get_text(separator=" | ", strip=True)
        print(f"  -> TEXTO PANTALLA: {texto_limpio[:400]}")
        
        # Buscamos posibles estados en el texto renderizado
        estados = ["Entregado", "En reparto", "En terminal", "Recogido", "En tránsito", "Novedad"]
        for est in estados:
            if est.lower() in texto_limpio.lower():
                return est
                
        return "Estado actualizado (revisa el log de texto)"
    except Exception as e:
        print(f"  -> Error: {e}")
    return None

def consultar_servientrega(guia):
    url = f"https://www.servientrega.com/wps/portal/Colombia/transacciones-personas/rastreo-envios/detalle?guia={guia}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    print("  -> Conectando a Servientrega...")
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        estado_div = soup.find('div', class_='estado-guia')
        if estado_div:
            return estado_div.text.strip()
    except Exception as e:
        print(f"  -> Error consultando Servientrega: {e}")
    return None

def main():
    print("Iniciando bot con ScraperAPI...")
    with open('guias.json', 'r') as f: guias = json.load(f)
    try:
        with open('estado_guias.json', 'r') as f: estados_previos = json.load(f)
    except: estados_previos = {}

    cambios_detectados = False

    for guia, transportadora in guias.items():
        print(f"\n[*] Revisando: {guia} ({transportadora})")
        estado_actual = None
        
        if transportadora.lower() == 'coordinadora':
            estado_actual = consultar_coordinadora(guia)
        elif transportadora.lower() == 'servientrega':
            estado_actual = consultar_servientrega(guia)
            
        if not estado_actual: continue
        
        estado_previo = estados_previos.get(guia)
        print(f"[+] Actual: {estado_actual} | [-] Previo: {estado_previo}")

        if estado_actual != estado_previo:
            print("[!] Cambio detectado. Enviando a Telegram...")
            mensaje = f"📦 *Actualización*\n\n*Transportadora:* {transportadora.capitalize()}\n*Guía:* `{guia}`\n*Estado:* {estado_actual}"
            enviar_mensaje_telegram(mensaje)
            estados_previos[guia] = estado_actual
            cambios_detectados = True

    if cambios_detectados:
        with open('estado_guias.json', 'w') as f: json.dump(estados_previos, f, indent=4)

if __name__ == "__main__":
    main()
