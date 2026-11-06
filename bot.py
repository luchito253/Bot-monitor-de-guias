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
        'country_code': 'co',
        'premium': 'true'
    }
    print("  -> Conectando a Coordinadora vía ScraperAPI...")
    try:
        response = requests.get('http://api.scraperapi.com/', params=payload, timeout=90)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraemos todo el texto separándolo con barras " | "
        texto_limpio = soup.get_text(separator=" | ", strip=True)
        
        # Buscamos la frase exacta que muestra la página web
        if "Estado de la guía:" in texto_limpio:
            partes = texto_limpio.split("Estado de la guía:")
            # El estado estará inmediatamente después, tomamos el texto hasta la siguiente barra " | "
            estado_bruto = partes[1].split("|")[0].strip()
            
            # Limpiamos palabras adicionales por si el texto se pegó a la siguiente sección
            estado_final = estado_bruto.replace("Destino:", "").strip()
            
            if estado_final:
                return estado_final
                
        # Si no encuentra el estado, imprimimos en el log para diagnosticar y retornamos None
        # Retornar None evita que el bot envíe mensajes falsos o guarde errores en el archivo JSON
        print(f"  -> TEXTO PANTALLA INCOMPLETO: {texto_limpio[:200]}")
        return None
        
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
