import json
import requests
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = "9253803566:AAHqNxUJHpnRW0Wl2tkZJmeOI6nsJ5uChIo"
CHAT_ID = "193021750"
PROXY_COLOMBIA = "http://190.71.72.85:2525"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "Markdown"}
    requests.post(url, json=payload)
    print(f"[Telegram] Mensaje enviado.")

def main():
    print("Iniciando bot con Playwright + Proxy Colombiano...")
    
    with open('guias.json', 'r') as f:
        guias = json.load(f)

    try:
        with open('estado_guias.json', 'r') as f:
            estados_previos = json.load(f)
    except FileNotFoundError:
        estados_previos = {}

    cambios_detectados = False

    with sync_playwright() as p:
        # Aquí inyectamos el proxy al navegador invisible
        browser = p.chromium.launch(
            headless=True,
            proxy={"server": PROXY_COLOMBIA}
        )
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        for guia, transportadora in guias.items():
            print(f"\n[*] Revisando guía: {guia} ({transportadora})")
            estado_actual = None

            if transportadora.lower() == 'coordinadora':
                try:
                    # Usamos la ventana lateral directa
                    page.goto(f"https://coordinadora.com/rastreo/rastreo-de-guia/detalle-de-rastreo-de-guia/?guia={guia}", timeout=60000)
                    print("  -> Página cargada. Esperando 10 segundos a que JavaScript procese los datos...")
                    page.wait_for_timeout(10000)
                    
                    texto_pantalla = page.locator("body").inner_text()
                    
                    if "Estado de la guía:" in texto_pantalla:
                        partes = texto_pantalla.split("Estado de la guía:")
                        estado_bruto = partes[1].split("\n")[0].strip()
                        estado_actual = estado_bruto.replace("Destino:", "").strip()
                    else:
                        print(f"  -> TEXTO INCOMPLETO: {texto_pantalla[:150]}")
                except Exception as e:
                    print(f"  -> Error Coordinadora: {e}")

            elif transportadora.lower() == 'servientrega':
                try:
                    # Servientrega no suele necesitar proxy, pero aprovechará la conexión
                    page.goto(f"https://www.servientrega.com/wps/portal/Colombia/transacciones-personas/rastreo-envios/detalle?guia={guia}", timeout=60000)
                    page.wait_for_timeout(8000)
                    elemento = page.query_selector('.estado-guia')
                    if elemento:
                        estado_actual = elemento.inner_text().strip()
                except Exception as e:
                     print(f"  -> Error Servientrega: {e}")

            if estado_actual:
                print(f"[+] Estado extraído: {estado_actual}")
                estado_previo = estados_previos.get(guia)

                if estado_actual != estado_previo:
                    print("[!] CAMBIO DETECTADO. Enviando mensaje...")
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
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
