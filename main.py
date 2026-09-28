import os
import sys

# Silenciar colisión de DPI de Qt antes de instanciar la UI
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window.warning=false"

import re
import time
import datetime
import threading
import keyboard
import speech_recognition as sr
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from PyQt6.QtWidgets import QApplication

# 1. Imports modulares (incluyendo ChatPanel)
from ui.avatar import AvatarWidget
from ui.chat_panel import ChatPanel
from services.vision import capturar_pantalla_b64
from core.cerebro import consultar_amigo
from core.memoria import inicializar_tabla_neon
from services.voz import hablar_amigo
from services.musica import (
    reproducir_cancion,
    reproducir_spotify,
    bajar_volumen_musica,
    restaurar_volumen_musica,
)

# Inicializar Base de Datos en Neon
inicializar_tabla_neon()

# 2. Inicialización de la Interfaz Gráfica
app = QApplication(sys.argv)
avatar = AvatarWidget()
avatar.show()

# -------------------------------------------------------------
# AQUÍ VA EL BLOQUE DEL CHAT PANEL CONECTADO AL AVATAR
# -------------------------------------------------------------
panel_chat = ChatPanel()

def alternar_panel():
    if panel_chat.isVisible():
        panel_chat.hide()
    else:
        # Coloca la ventana de chat a la izquierda del avatar
        panel_chat.move(avatar.x() - panel_chat.width() - 10, avatar.y() - 200)
        panel_chat.show()

avatar.toggle_chat_callback = alternar_panel

def manejar_entrada_gui(texto):
    # Se ejecuta en hilo secundario para no congelar la ventana mientras piensa
    threading.Thread(target=procesar_orden, args=(texto, avatar, panel_chat), daemon=True).start()

panel_chat.mensaje_enviado.connect(manejar_entrada_gui)
panel_chat.solicitar_microfono.connect(lambda: threading.Thread(target=bucle_conversacion_activa, args=(avatar, panel_chat), daemon=True).start())
# -------------------------------------------------------------

# Configuración del Reconocedor de Voz Fifine
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 450
recognizer.pause_threshold = 0.8

en_conversacion = False
forzar_corte = False

NOMBRES_ACTIVACION = ["amigo", "oye amigo", "causa", "oye causa", "alexa"]
PALABRAS_DESPEDIDA = [
    "eso es todo", "adios amigo", "adiós amigo", "chau", "adios", "adiós",
    "nada mas", "nada más", "ya no", "no gracias", "asi dejalo", "cortar", "listo", "nada"
]

def ajustar_volumen_pc(nivel):
    try:
        dispositivos = AudioUtilities.GetSpeakers()
        interfaz = dispositivos.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        vol = cast(interfaz, POINTER(IAudioEndpointVolume))
        nivel = max(0, min(100, int(nivel)))
        vol.SetMasterVolumeLevelScalar(nivel / 100.0, None)
        return f"Volumen al {nivel} por ciento, Jefe."
    except Exception as e:
        return f"No pude cambiar el volumen: {e}"

def abrir_programa_sistema(app_nombre):
    a = app_nombre.lower().strip()
    if "word" in a: os.system("start winword"); return "Abriendo Word, Jefe."
    elif "excel" in a: os.system("start excel"); return "Abriendo Excel, Jefe."
    elif "bloc" in a or "notepad" in a: os.system("start notepad"); return "Abriendo el Bloc de notas, Jefe."
    elif "calculadora" in a or "calc" in a: os.system("start calc"); return "Abriendo la calculadora, Jefe."
    return None

def buscar_archivo_disco(nombre_archivo):
    rutas = [os.path.expanduser("~/Documents"), os.path.expanduser("~/Desktop"), os.path.expanduser("~/Downloads")]
    for ruta in rutas:
        for raiz, _, archivos in os.walk(ruta):
            for f in archivos:
                if nombre_archivo.lower() in f.lower():
                    os.startfile(os.path.join(raiz, f))
                    return f"Encontré y abrí {f}, Jefe."
    return f"No encontré ningún archivo llamado {nombre_archivo}."

def limpiar_nombre_cancion(texto):
    t = texto.lower()
    patrones = [
        r"^quiero que pongas\s+", r"^puedes poner\s+", r"^pon la cancion de\s+",
        r"^pon la cancion\s+", r"^pon el tema\s+", r"^pon en youtube\s+",
        r"^pon en spotify\s+", r"^ponme\s+", r"^reproduce\s+", r"^pon\s+"
    ]
    for p in patrones:
        t = re.sub(p, "", t)
    return re.sub(r"\b(en youtube|de youtube|en spotify|de spotify|por favorcito|por favor|porfa)\b", "", t).strip()

def escuchar_microfono(timeout_seg=5, modo_centinela=False):
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=timeout_seg, phrase_time_limit=8)
            texto = recognizer.recognize_google(audio, language="es-PE").strip()
            # En modo pasivo no mostramos la letra de las canciones en consola
            if not modo_centinela:
                print(f"[Voz detectada]: '{texto}'")
            return texto
        except Exception:
            return ""

def procesar_orden(entrada, widget, panel=None):
    texto_limpio = entrada.lower().strip()

    if any(p in texto_limpio for p in ["apagate", "cerrar programa"]):
        hablar_amigo("Hasta luego, Jefe.", widget)
        time.sleep(0.3)
        widget.cerrar()
        sys.exit()

    if any(p in texto_limpio for p in ["que hora es", "la hora", "dime la hora"]):
        hora_actual = datetime.datetime.now().strftime("%I:%M %p")
        msg = f"Son las {hora_actual}, Jefe."
        if panel: panel.agregar_mensaje("Causa", msg)
        hablar_amigo(msg, widget)
        return

    if "volumen" in texto_limpio or "mudo" in texto_limpio or "silencio" in texto_limpio:
        if any(x in texto_limpio for x in ["cero", "0", "mudo", "silencio"]):
            msg = ajustar_volumen_pc(0)
        elif any(x in texto_limpio for x in ["cien", "100", "todo"]):
            msg = ajustar_volumen_pc(100)
        elif "baja" in texto_limpio:
            msg = ajustar_volumen_pc(25)
        elif "sube" in texto_limpio:
            msg = ajustar_volumen_pc(80)
        else:
            nums = re.findall(r"\d+", texto_limpio)
            msg = ajustar_volumen_pc(int(nums[0])) if nums else "Dime qué porcentaje pongo."
        if panel: panel.agregar_mensaje("Causa", msg)
        hablar_amigo(msg, widget)
        return

    if "abre" in texto_limpio or "abrir" in texto_limpio:
        app_detectada = abrir_programa_sistema(texto_limpio)
        if app_detectada:
            if panel: panel.agregar_mensaje("Causa", app_detectada)
            hablar_amigo(app_detectada, widget)
            return

    if "busca" in texto_limpio and ("archivo" in texto_limpio or "documento" in texto_limpio):
        termino = re.sub(r"\b(busca|el|archivo|documento)\b", "", texto_limpio).strip()
        if termino:
            msg = buscar_archivo_disco(termino)
            if panel: panel.agregar_mensaje("Causa", msg)
            hablar_amigo(msg, widget)
            return

    if "youtube" in texto_limpio and any(k in texto_limpio for k in ["pon", "reproduce", "cancion", "tema"]):
        cancion = limpiar_nombre_cancion(entrada)
        if len(cancion) > 1:
            msg = f"Ahí te pongo {cancion} en YouTube, Causa."
            if panel: panel.agregar_mensaje("Causa", msg)
            hablar_amigo(msg, widget)
            reproducir_cancion(cancion)
            return

    if any(k in texto_limpio for k in ["spotify", "pon", "reproduce", "cancion", "tema"]):
        cancion = limpiar_nombre_cancion(entrada)
        if len(cancion) > 1:
            msg = f"Poniendo {cancion} en Spotify, Causa."
            if panel: panel.agregar_mensaje("Causa", msg)
            hablar_amigo(msg, widget)
            reproducir_spotify(cancion)
            return

    captura = None
    if any(p in texto_limpio for p in ["mira", "pantalla", "opinas", "ves"]):
        print("[Analizando pantalla...]")
        captura = capturar_pantalla_b64()

    print("[Pensando...]")
    respuesta = consultar_amigo(entrada, imagen_b64=captura)
    print(f"Amigo: {respuesta}\n")
    if panel: panel.agregar_mensaje("Causa", respuesta)
    hablar_amigo(respuesta, widget)

def bucle_conversacion_activa(widget, panel=None):
    global en_conversacion, forzar_corte
    en_conversacion = True
    forzar_corte = False

    bajar_volumen_musica(nivel=0.15)
    time.sleep(0.1)
    hablar_amigo("Dime, Causa.", widget)

    while en_conversacion and not forzar_corte:
        texto = escuchar_microfono(timeout_seg=6)

        if not texto:
            print("[Silencio detectado]: Volviendo a reposo.")
            hablar_amigo("Cualquier cosa me avisas, Causa.", widget)
            break

        if forzar_corte:
            break

        if panel: panel.agregar_mensaje("Tú (voz)", texto)

        if any(p in texto.lower() for p in PALABRAS_DESPEDIDA):
            hablar_amigo("De una, Jefe. Me quedo atento.", widget)
            break

        procesar_orden(texto, widget, panel)

        if forzar_corte:
            break

        hablar_amigo("¿Quieres algo más, Causa?", widget)

    en_conversacion = False
    restaurar_volumen_musica()

def centinela_wake_word(widget, panel):
    global en_conversacion
    while True:
        if not en_conversacion:
            # Escucha pasiva: no imprime letras de fondo en la consola
            audio = escuchar_microfono(timeout_seg=3, modo_centinela=True)
            if audio:
                frase = audio.lower()
                # SOLO se activa si la frase contiene tu palabra clave explícita
                if any(nombre in frase for nombre in NOMBRES_ACTIVACION):
                    print(f"\n[Palabra clave detectada]: '{frase}'")
                    bucle_conversacion_activa(widget, panel)
        time.sleep(0.3)

def cancelar_conversacion(widget):
    global forzar_corte, en_conversacion
    if en_conversacion:
        forzar_corte = True
        en_conversacion = False
        restaurar_volumen_musica()
        hablar_amigo("Listo, me callo.", widget)

def bucle_consola(widget, panel):
    while True:
        try:
            sys.stdout.flush()
            entrada = input().strip()
            if entrada:
                if entrada.lower() in ["salir", "chao", "apagate"]:
                    widget.cerrar()
                    break
                if panel: panel.agregar_mensaje("Tú (consola)", entrada)
                procesar_orden(entrada, widget, panel)
        except Exception:
            break

# Hilos en segundo plano
threading.Thread(target=centinela_wake_word, args=(avatar, panel_chat), daemon=True).start()
threading.Thread(target=bucle_consola, args=(avatar, panel_chat), daemon=True).start()

# Atajo de emergencia para callarlo
keyboard.add_hotkey("f9", lambda: cancelar_conversacion(avatar))

# Bucle principal de la interfaz
sys.exit(app.exec())