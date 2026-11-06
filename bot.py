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
    print("Iniciando bot con Navegador Simulado y Anti-Detección...")
    
    with open('guias.json', 'r') as f:
        guias = json.load(f)

    try:
        with open('estado_guias.json', 'r') as f:
            estados_previos = json.load(f)
    except FileNotFoundError:
        estados_previos = {}

    cambios_detectados = False

    with sync_playwright() as p:
        # Banderas para ocultar que somos un bot automático
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        for guia, transportadora in guias.items():
            print(f"\n[*] Revisando guía: {guia} ({transportadora})")
            estado_actual = None

            if transportadora.lower() == 'coordinadora':
                datos_capturados = {"estado": None}
                
                # Función espía mejorada
                def interceptar_respuesta(response):
                    if "detail_tracking" in response.url:
                        print(f"    [API] Petición interceptada. Código HTTP: {response.status}")
                        try:
                            datos = response.json()
                            print(f"    [API] JSON: {str(datos)[:200]}")
                            if "data" in datos and "estado" in datos["data"]:
                                datos_capturados["estado"] = datos["data"]["estado"]
                            elif "estado_actual" in datos:
                                datos_capturados["estado"] = datos["estado_actual"]
                        except:
                            print("    [API] Error leyendo la respuesta.")

                page.on("response", interceptar_respuesta)
                
                try:
                    print("  -> Abriendo página de Coordinadora...")
                    page.goto(f"https://coordinadora.com/rastreo/rastreo-de-guia/?guia={guia}", timeout=30000)
                    print(f"  -> Título de la página: {page.title()}")
                    print("  -> Esperando 8 segundos...")
                    page.wait_for_timeout(8000) 
                    
                    estado_actual = datos_capturados["estado"]
                    
                    # Si no atrapó la respuesta, leeremos lo que dice la pantalla para diagnosticar
                    if not estado_actual:
                        print("  -> La API interna no respondió. Leyendo la pantalla del navegador...")
                        texto_pantalla = page.locator("body").inner_text()
                        print(f"  -> TEXTO VISIBLE: {texto_pantalla[:400].replace(chr(10), ' | ')}")
                        
                except Exception as e:
                    print(f"  -> Error cargando la página: {e}")
                
                page.remove_listener("response", interceptar_respuesta)

            elif transportadora.lower() == 'servientrega':
                try:
                    print("  -> Abriendo página de Servientrega...")
                    page.goto(f"https://www.servientrega.com/wps/portal/Colombia/transacciones-personas/rastreo-envios/detalle?guia={guia}", timeout=30000)
                    print(f"  -> Título de la página: {page.title()}")
                    page.wait_for_timeout(6000)
                    
                    elemento = page.query_selector('.estado-guia')
                    if elemento:
                        estado_actual = elemento.inner_text().strip()
                    else:
                        print("  -> No se encontró el recuadro. Leyendo pantalla...")
                        texto_pantalla = page.locator("body").inner_text()
                        print(f"  -> TEXTO VISIBLE: {texto_pantalla[:400].replace(chr(10), ' | ')}")
                except Exception as e:
                     print(f"  -> Error con Servientrega: {e}")

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

        browser.close()

    if cambios_detectados:
        print("\nGuardando nuevos estados en el archivo...")
        with open('estado_guias.json', 'w') as f:
            json.dump(estados_previos, f, indent=4)
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
