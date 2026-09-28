import os
import time
import urllib.parse
from pathlib import Path
import pyautogui
import pywhatkit
import webbrowser
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

# 1. Rutas exactas a los assets
BASE_DIR = Path(__file__).resolve().parent.parent
IMG_BOTON_VERDE = BASE_DIR / "assets" / "icons" / "play_verde.png"

# Procesos de reproductores y navegadores (donde corre YouTube)
PROCESOS_OBJETIVO = [
    "spotify.exe",
    "chrome.exe",
    "msedge.exe",
    "brave.exe",
    "firefox.exe",
    "opera.exe"
]

# Almacena tuplas de (control_volumen, volumen_original)
sesiones_atenuadas = []

def obtener_sesiones_audio():
    """Localiza todos los canales de audio activos de Spotify y navegadores web"""
    controles = []
    try:
        sesiones = AudioUtilities.GetAllSessions()
        for sesion in sesiones:
            if sesion.Process:
                nombre = sesion.Process.name().lower()
                if nombre in PROCESOS_OBJETIVO:
                    volumen = sesion._ctl.QueryInterface(ISimpleAudioVolume)
                    controles.append((nombre, volumen))
    except Exception as e:
        print(f"[Audio Ducking Error Scan]: {e}")
    return controles

def bajar_volumen_musica(nivel=0.15):
    """Baja el volumen al 15% tanto en Spotify como en el navegador (YouTube)"""
    global sesiones_atenuadas
    sesiones_atenuadas = []
    controles = obtener_sesiones_audio()
    
    for nombre, control in controles:
        try:
            vol_actual = control.GetMasterVolume()
            # Guardamos la referencia y su volumen previo
            sesiones_atenuadas.append((control, vol_actual))
            control.SetMasterVolume(nivel, None)
            print(f"[Audio Ducking]: {nombre} atenuado a {int(nivel * 100)}%")
        except Exception as e:
            print(f"[Audio Ducking Error en {nombre}]: {e}")

def restaurar_volumen_musica():
    """Restaura el volumen de todas las aplicaciones atenuadas a su nivel previo"""
    global sesiones_atenuadas
    for control, vol_original in sesiones_atenuadas:
        try:
            vol_target = max(vol_original, 0.8)
            control.SetMasterVolume(vol_target, None)
            print(f"[Audio Ducking]: Volumen restaurado a {int(vol_target * 100)}%")
        except Exception as e:
            print(f"[Audio Ducking Error Restore]: {e}")
    sesiones_atenuadas.clear()

def reproducir_spotify(termino):
    """Abre Spotify, ubica el botón verde de Play y minimiza"""
    try:
        query_codificada = urllib.parse.quote(termino)
        os.system(f"start spotify:search:{query_codificada}")
        
        # Margen para que la ventana cargue y pinte los resultados
        time.sleep(2.5)

        clic_exitoso = False

        # Verificación y clic visual por plantilla
        if IMG_BOTON_VERDE.exists():
            try:
                # Requiere opencv-python instalado (confidence=0.72 para permitir ligeras diferencias de brillo)
                ubicacion = pyautogui.locateCenterOnScreen(str(IMG_BOTON_VERDE), confidence=0.72)
                if ubicacion:
                    pyautogui.click(ubicacion)
                    clic_exitoso = True
                    print(f"[Spotify]: Clic en el botón verde en {ubicacion}")
            except Exception as err:
                print(f"[Aviso Visión]: No se pudo escanear pantalla ({err}). Usando teclado...")

        # Respaldo por teclado si no lo detectó por imagen
        if not clic_exitoso:
            pyautogui.press("enter")
            time.sleep(0.3)
            pyautogui.press("space")

        time.sleep(0.4)
        
        # Minimizar la ventana de Spotify para no estorbar
        cmd_minimizar = (
            'powershell -Command "$ws = New-Object -ComObject wscript.shell; '
            '$ws.AppActivate(\'Spotify\'); Start-Sleep -Milliseconds 150; '
            'Add-Type -MemberDefinition \'[DllImport(\\\"user32.dll\\\")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);\' -Name Win32 -Namespace Win32; '
            '$h = (Get-Process Spotify -ErrorAction SilentlyContinue | Where-Object {$_.MainWindowTitle -ne \'\'}).MainWindowHandle; '
            'if ($h) { [Win32.Win32]::ShowWindow($h, 2) }"'
        )
        os.system(cmd_minimizar)
        return True

    except Exception as e:
        print(f"[Error Spotify]: {e}")
        return False

def reproducir_cancion(termino_busqueda):
    """Reproduce canciones en YouTube si lo solicitas expresamente"""
    try:
        pywhatkit.playonyt(termino_busqueda)
        return True
    except Exception:
        query = urllib.parse.quote(termino_busqueda)
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return True