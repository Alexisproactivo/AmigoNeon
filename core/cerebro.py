import os
import threading
import requests
from config.settings import GEMINI_API_KEY
from core.memoria import cargar_memoria_completa, guardar_recuerdo

# Caché en RAM para no sumar latencia de base de datos
MEMORIA_LOCAL = cargar_memoria_completa()

def actualizar_memoria_async(cat, clav, val):
    global MEMORIA_LOCAL
    guardar_recuerdo(cat, clav, val)
    MEMORIA_LOCAL = cargar_memoria_completa()

def procesar_recuerdos(texto):
    if "[APRENDER:" in texto:
        partes = texto.split("[APRENDER:")
        texto_limpio = partes[0].strip()
        try:
            datos = partes[1].replace("]", "").strip()
            cat, clav, val = [x.strip() for x in datos.split("|")]
            threading.Thread(target=actualizar_memoria_async, args=(cat, clav, val), daemon=True).start()
        except Exception as e:
            print(f"[Memoria]: Error: {e}")
        return texto_limpio
    return texto

def consultar_qwen_local(mensaje_usuario):
    """Fallback local optimizado para respuesta rápida en GPU"""
    print("[Cerebro]: Usando Qwen local (RTX)...")
    
    prompt = f"""Eres un asistente de escritorio amigable y leal llamado Causa. Hablas en español peruano casual y directo.
Trata al usuario como 'Causa' o 'Jefe'.
{MEMORIA_LOCAL}
INSTRUCCIÓN: Responde de forma precisa y directa en 1 o máximo 2 oraciones (menos de 25 palabras).
Usuario: {mensaje_usuario}
Causa:"""

    payload = {
        "model": "qwen2.5-coder:14b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 60,
            "temperature": 0.5
        }
    }
    try:
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=25)
        respuesta = res.json().get("response", "Listo, Jefe.").strip()
        return procesar_recuerdos(respuesta)
    except Exception as e:
        return f"Error en modelo local: {e}"

def consultar_amigo(mensaje_usuario, imagen_b64=None):
    prompt_sistema = f"""Eres un compañero de escritorio llamado Causa. Hablas en español peruano casual.
Trata al usuario como 'Causa' o 'Jefe'.
{MEMORIA_LOCAL}
INSTRUCCIÓN: Responde en máximo 2 oraciones breves y claras.
Si el usuario te enseña algo nuevo sobre él, añade al final: [APRENDER: categoria | clave | valor]"""

    partes = [{"text": f"{prompt_sistema}\n\nUsuario: {mensaje_usuario}\nCausa:"}]
    if imagen_b64:
        partes.append({"inline_data": {"mime_type": "image/jpeg", "data": imagen_b64}})

    # Endpoint estándar sin búsqueda web externa activa
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": partes}]
    }

    try:
        res = requests.post(url, json=payload, timeout=5)
        data = res.json()
        
        # Salto a Qwen local si la API de Google reporta saturación o cuota
        if "error" in data:
            print("[Aviso API]: Cuota o saturación en Google. Pasando a GPU local...")
            return consultar_qwen_local(mensaje_usuario)

        if "candidates" in data and len(data["candidates"]) > 0:
            candidato = data["candidates"][0]
            texto = candidato["content"]["parts"][0]["text"].strip()
            return procesar_recuerdos(texto)

    except Exception:
        # Si ocurre timeout o fallo de red con Google, responde la GPU
        pass

    return consultar_qwen_local(mensaje_usuario)