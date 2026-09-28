import asyncio
import os
import glob
import time
import math
import struct
import uuid
import edge_tts
import pygame
from pydub import AudioSegment
from config.settings import VOZ_NOMBRE

# 1. Localización automática de FFmpeg en rutas estándar de Windows / WinGet
def localizar_ffmpeg():
    rutas_posibles = [
        os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Packages\**\ffmpeg.exe"),
        r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe"
    ]
    for patron in rutas_posibles:
        hallazgos = glob.glob(patron, recursive=True)
        if hallazgos:
            carpeta_bin = os.path.dirname(hallazgos[0])
            os.environ["PATH"] += os.pathsep + carpeta_bin
            AudioSegment.converter = hallazgos[0]
            ffprobe_path = os.path.join(carpeta_bin, "ffprobe.exe")
            if os.path.exists(ffprobe_path):
                AudioSegment.ffprobe = ffprobe_path
            return True
    return False

localizar_ffmpeg()

pygame.mixer.init()

async def generar_audio(texto, ruta_mp3):
    """Genera la síntesis con la voz profunda configurada"""
    comunicador = edge_tts.Communicate(texto, VOZ_NOMBRE, pitch="-3Hz", rate="+15%")
    await comunicador.save(ruta_mp3)

def calcular_rms(data):
    """Calcula la energía de la onda para el lipsync del avatar"""
    count = len(data) // 2
    if count == 0:
        return 0
    shorts = struct.unpack(f"<{count}h", data)
    sum_squares = sum(s * s for s in shorts)
    return math.sqrt(sum_squares / count)

def hablar_amigo(texto, avatar_widget=None):
    if not texto:
        return

    # Usar un sufijo único por llamada para evitar colisiones y bloqueos de archivo
    id_unico = uuid.uuid4().hex[:6]
    audio_mp3 = f"temp_{id_unico}.mp3"
    audio_wav = f"temp_{id_unico}.wav"

    try:
        asyncio.run(generar_audio(texto, audio_mp3))

        # Conversión a WAV con FFmpeg para leer muestras PCM crudas
        sound = AudioSegment.from_mp3(audio_mp3)
        sound.export(audio_wav, format="wav")

        pygame.mixer.music.load(audio_wav)
        pygame.mixer.music.play()

        # Medición de RMS en tiempo real sincronizada con el avatar
        with open(audio_wav, "rb") as f:
            f.seek(44)  # Saltar encabezado del WAV
            while pygame.mixer.music.get_busy():
                raw = f.read(1024)
                if not raw:
                    break
                rms = calcular_rms(raw)

                # Umbral de fonema: abre la boca según la intensidad de la voz
                if avatar_widget:
                    avatar_widget.set_boca(rms > 380)
                time.sleep(0.02)

        if avatar_widget:
            avatar_widget.set_boca(False)

        # Descarga de Pygame antes de intentar eliminar los archivos
        pygame.mixer.music.unload()

    except Exception as e:
        print(f"Detalle en voz: {e}")
        if avatar_widget:
            avatar_widget.set_boca(False)

    finally:
        # Limpieza silenciosa de los temporales
        for f in [audio_mp3, audio_wav]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass