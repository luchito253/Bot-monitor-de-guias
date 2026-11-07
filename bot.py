import json
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = "9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo"
CHAT_ID = "193021750"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
    print(f"[Telegram] Mensaje enviado.")

def main():
    print("Iniciando bot (Estrategia de Agregador Global)...")
    
    with open('guias.json', 'r') as f:
        guias = json.load(f)

    try:
        with open('estado_guias.json', 'r') as f:
            estados_previos = json.load(f)
    except FileNotFoundError:
        estados_previos = {}

    cambios_detectados = False

    with sync_playwright() as p:
        # Lanzamos el navegador en GitHub normalmente (sin proxies, no los necesitamos aquí)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        for guia, transportadora in guias.items():
            print(f"\n[*] Revisando guía: {guia} ({transportadora})")
            estado_actual = None

            if transportadora.lower() == 'coordinadora':
                try:
                    print("  -> Usando ParcelsApp para evadir el reCAPTCHA de Coordinadora...")
                    # Entramos al agregador internacional que ya resolvió el bloqueo
                    page.goto(f"https://parcelsapp.com/es/tracking/{guia}", timeout=60000)
                    print("  -> Esperando 12 segundos a que el agregador obtenga los datos...")
                    
                    # ParcelsApp hace la búsqueda automáticamente al cargar la URL
                    page.wait_for_timeout(12000)
                    
                    # Leemos toda la pantalla renderizada
                    texto_pantalla = page.locator("body").inner_text()
                    
                    # Lista de palabras clave basadas en los estados de Coordinadora
                    estados = ["En terminal destino", "En reparto", "Entregado", "Recogido", "En tránsito", "Novedad", "Despachado"]
                    
                    # Buscamos si alguno de los estados aparece en la respuesta del agregador
                    for est in estados:
                        if est.lower() in texto_pantalla.lower():
                            estado_actual = est
                            break
                            
                    if not estado_actual:
                        print("  -> No se detectó un estado claro en la pantalla del agregador.")
                        
                except Exception as e:
                    print(f"  -> Error con ParcelsApp: {e}")

            elif transportadora.lower() == 'servientrega':
                try:
                    page.goto(f"https://www.servientrega.com/wps/portal/Colombia/transacciones-personas/rastreo-envios/detalle?guia={guia}", timeout=60000)
                    page.wait_for_selector('.estado-guia', timeout=15000)
                    estado_actual = page.locator('.estado-guia').inner_text().strip()
                except Exception as e:
                     print(f"  -> Error Servientrega: {e}")

            if estado_actual:
                print(f"[+] Estado extraído: {estado_actual}")
                estado_previo = estados_previos.get(guia)

                if estado_actual != estado_previo:
                    print("[!] CAMBIO DETECTADO. Enviando mensaje a Telegram...")
                    mensaje = f"📦 *Actualización de Envío*\n\n*Transportadora:* {transportadora.capitalize()}\n*Guía:* `{guia}`\n*Estado:* {estado_actual}"
                    enviar_mensaje_telegram(mensaje)
                    estados_previos[guia] = estado_actual
                    cambios_detectados = True
                else:
                    print("[=] Sin cambios.")
            else:
                print("[!] No se pudo extraer el estado.")

        browser.close()

    if cambios_detectados:
        with open('estado_guias.json', 'w') as f:
            json.dump(estados_previos, f, indent=4)
    print("\nProceso finalizado.")

if __name__ == "__main__":
    main()
