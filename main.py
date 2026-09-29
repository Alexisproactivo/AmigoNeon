import os
import sys

# Silenciar colisión de DPI de Qt antes de instanciar la aplicación
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

# 1. Interfaz de usuario (desde la carpeta ui/)
from ui.avatar import AvatarWidget
from ui.chat_panel import ChatPanel

# 2. Servicios y sentidos (desde services/)
from services.vision import capturar_pantalla_b64
from services.voz import hablar_amigo
from services.musica import (
    reproducir_cancion,
    reproducir_spotify,
    bajar_volumen_musica,
    restaurar_volumen_musica,
)

# 3. Cerebro y base de datos (desde core/)
from core.cerebro import consultar_amigo
from core.memoria import inicializar_tabla_neon

# =============================================================
# CONFIGURACIÓN DEL RECONOCIMIENTO DE VOZ
# =============================================================
recognizer = sr.Recognizer()
recognizer.dynamic_energy_threshold = False
recognizer.energy_threshold = 450
recognizer.pause_threshold = 0.8

en_conversacion = False
forzar_corte = False
dictando_en_chat = False

NOMBRES_ACTIVACION = ["amigo", "oye amigo", "causa", "oye causa", "alexa"]
PALABRAS_DESPEDIDA = [
    "eso es todo", "adios amigo", "adiós amigo", "chau", "adios", "adiós",
    "nada mas", "nada más", "ya no", "no gracias", "asi dejalo", "cortar", "listo", "nada"
]

def escuchar_microfono(timeout_seg=5, modo_centinela=False):
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=timeout_seg, phrase_time_limit=8)
            texto = recognizer.recognize_google(audio, language="es-PE").strip()
            if not modo_centinela:
                print(f"[Voz detectada]: '{texto}'")
            return texto
        except Exception:
            return ""

# =============================================================
# ORQUESTADOR CENTRAL DE ACCIONES DEL SISTEMA
# =============================================================
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
        r"^pon la cancion\s+", r"^pon el tema\s+", r"^ponte el tema\s+",
        r"^pon en youtube\s+", r"^pon en spotify\s+", r"^ponme\s+", 
        r"^reproduce\s+", r"^toca la cancion\s+", r"^pon\s+"
    ]
    for p in patrones:
        t = re.sub(p, "", t)
    return re.sub(r"\b(en youtube|de youtube|en spotify|de spotify|por favorcito|por favor|porfa|plis)\b", "", t).strip()

def procesar_orden(entrada, widget, panel=None):
    texto_limpio = entrada.lower().strip()

    # 1. Apagado del sistema
    if any(p in texto_limpio for p in ["apagate", "cerrar programa"]):
        widget.set_estado("quieto")
        hablar_amigo("Hasta luego, Jefe.", widget)
        time.sleep(0.3)
        widget.cerrar()
        sys.exit()

    # 2. Hora del sistema
    if any(p in texto_limpio for p in ["que hora es", "la hora", "dime la hora"]):
        hora_actual = datetime.datetime.now().strftime("%I:%M %p")
        msg = f"Son las {hora_actual}, Jefe."
        if panel: panel.agregar_mensaje("Causa", msg)
        widget.set_estado("quieto")
        hablar_amigo(msg, widget)
        return

    # 3. Control de volumen
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
        widget.set_estado("quieto")
        hablar_amigo(msg, widget)
        return

    # 4. Abrir programas locales
    if "abre" in texto_limpio or "abrir" in texto_limpio:
        app_detectada = abrir_programa_sistema(texto_limpio)
        if app_detectada:
            if panel: panel.agregar_mensaje("Causa", app_detectada)
            widget.set_estado("quieto")
            hablar_amigo(app_detectada, widget)
            return

    # 5. Búsqueda de archivos
    if "busca" in texto_limpio and ("archivo" in texto_limpio or "documento" in texto_limpio):
        widget.set_estado("pensando")
        termino = re.sub(r"\b(busca|el|archivo|documento)\b", "", texto_limpio).strip()
        msg = buscar_archivo_disco(termino) if termino else "Dime qué archivo busco."
        if panel: panel.agregar_mensaje("Causa", msg)
        if "No encontré" in msg:
            widget.set_estado("error")
        else:
            widget.set_estado("quieto")
        hablar_amigo(msg, widget)
        return

    # 6. YouTube
    if "youtube" in texto_limpio and any(k in texto_limpio for k in ["pon", "reproduce", "cancion", "tema"]):
        cancion = limpiar_nombre_cancion(entrada)
        if len(cancion) > 1:
            msg = f"Ahí te pongo {cancion} en YouTube, Causa."
            if panel: panel.agregar_mensaje("Causa", msg)
            widget.set_estado("quieto")
            hablar_amigo(msg, widget)
            widget.set_estado("alegre")
            reproducir_cancion(cancion)
            return

    # 7. Spotify
    if any(k in texto_limpio for k in ["spotify", "pon", "reproduce", "cancion", "tema"]):
        cancion = limpiar_nombre_cancion(entrada)
        if len(cancion) > 1:
            msg = f"Poniendo {cancion} en Spotify, Causa."
            if panel: panel.agregar_mensaje("Causa", msg)
            widget.set_estado("quieto")
            hablar_amigo(msg, widget)
            widget.set_estado("alegre")
            reproducir_spotify(cancion)
            return

    # 8. Visión de pantalla
    captura = None
    if any(p in texto_limpio for p in ["mira", "pantalla", "opinas", "ves"]):
        widget.set_estado("pensando")
        print("[Analizando pantalla...]")
        captura = capturar_pantalla_b64()

    # 9. Consulta al Cerebro (IA)
    widget.set_estado("pensando")
    print("[Pensando...]")
    respuesta = consultar_amigo(entrada, imagen_b64=captura)
    print(f"Amigo: {respuesta}\n")
    if panel: panel.agregar_mensaje("Causa", respuesta)

    # 10. Voz del avatar
    widget.set_estado("quieto")
    hablar_amigo(respuesta, widget)

# =============================================================
# BUCLES DE CONVERSACIÓN, CENTINELA Y MODO DICTADO
# =============================================================
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
    global en_conversacion, dictando_en_chat
    while True:
        # Solo escucha si no está en conversación activa Y no estás dictando en el chat
        if not en_conversacion and not dictando_en_chat:
            audio = escuchar_microfono(timeout_seg=3, modo_centinela=True)
            if audio:
                frase = audio.lower()
                if any(nombre in frase for nombre in NOMBRES_ACTIVACION):
                    print(f"\n[Palabra clave detectada]: '{frase}'")
                    widget.set_estado("sorprendido")
                    bucle_conversacion_activa(widget, panel)
        else:
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

def ejecutar_dictado(panel):
    """Escucha la voz del usuario y la escribe en el cuadro de texto del chat"""
    texto = escuchar_microfono()
    if texto:
        panel.input_texto.setText(texto)
    panel.ocultar_barra_escucha()

# ==============================================================
# ARRANQUE DE LA APLICACIÓN Y LOOP DE EVENTOS
# ==============================================================
if __name__ == "__main__":
    # 1. Base de datos
    inicializar_tabla_neon()

    # 2. Crear instancia gráfica de Qt
    app = QApplication(sys.argv)

    # 3. Widgets flotantes
    avatar = AvatarWidget()
    avatar.show()

    panel = ChatPanel()

  # 4. Alternar panel con doble clic en el avatar
    def alternar_panel():
        if panel.isVisible():
            panel.hide()
        else:
            # Misma coordenada X e Y de referencia
            pos_x = avatar.x() - panel.width() - 15
            pos_y = avatar.y() - panel.height() + 80
            
            panel.move(max(10, pos_x), max(10, pos_y))
            panel.show()

    avatar.toggle_chat_callback = alternar_panel
# 5. Conexiones de señales del ChatPanel
    panel.mensaje_enviado.connect(
        lambda texto: threading.Thread(target=procesar_orden, args=(texto, avatar, panel), daemon=True).start()
    )
   # Opción de hablar con el bot por voz desde el menú del micro
    panel.solicitar_conversacion.connect(
        lambda: threading.Thread(target=bucle_conversacion_activa, args=(avatar, panel), daemon=True).start()
    )
def pausar_centinela_dictado():
        global dictando_en_chat
        dictando_en_chat = True

def reanudar_centinela_dictado():
        global dictando_en_chat
        dictando_en_chat = False

panel.inicio_dictado_signal.connect(pausar_centinela_dictado)
panel.fin_dictado_signal.connect(reanudar_centinela_dictado)
    
# 6. Atajo de teclado de emergencia (F9)
keyboard.add_hotkey("f9", lambda: cancelar_conversacion(avatar))

# 7. Hilos en segundo plano
threading.Thread(target=centinela_wake_word, args=(avatar, panel), daemon=True).start()
threading.Thread(target=bucle_consola, args=(avatar, panel), daemon=True).start()

# 8. Loop principal de eventos de PyQt6
sys.exit(app.exec())