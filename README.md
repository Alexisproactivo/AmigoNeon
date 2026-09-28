# 🤖 AmigoNeon - Asistente de Escritorio VTuber con IA Híbrida

Asistente de escritorio interactivo y multimodal (VTuber overlay) desarrollado en **Python y PyQt6**. Incorpora sincronización labial (*lipsync*) en tiempo real guiada por amplitud de audio (RMS), visión de monitor, interacción manos libres por voz, control multimedia automatizado (Spotify y YouTube), panel gráfico de chat y una arquitectura híbrida de doble motor (**Google Gemini 3.6 Flash + Qwen 2.5 Coder 14B local vía Ollama**) con memoria persistente en **PostgreSQL Serverless (Neon DB)**.

---

## ⚡ Características Principales

### 🎭 Overlay Flotante con Lipsync Real

Interfaz sin bordes ni fondo mediante `PyQt6` con:

* Arrastre libre.
* Acoplamiento dinámico a la esquina inferior derecha de Windows.
* Animación labial en tiempo real.
* Reacción de los labios a la amplitud del audio.
* Cálculo de amplitud mediante RMS.
* Procesamiento de datos PCM mediante FFmpeg.
* Cambio dinámico entre estados del avatar.

### 💬 Panel de Chat Gráfico Retráctil

Interfaz gráfica nativa que permite:

* Visualizar el historial de conversación.
* Escribir mensajes mediante teclado.
* Activar manualmente el micrófono.
* Acceder al panel mediante doble clic sobre el avatar.
* Contraer nuevamente la ventana.

### 🧠 Arquitectura LLM Híbrida con Fallback Inteligente

AmigoNeon utiliza una arquitectura de doble motor.

#### ☁️ Motor Primario

**Google Gemini 3.6 Flash**

Características:

* Procesamiento de lenguaje natural.
* Google Search Grounding.
* Búsquedas web.
* Análisis contextual en vivo.
* Procesamiento mediante servicios en la nube.

#### 💻 Motor Secundario / Offline

**Qwen 2.5 Coder 14B mediante Ollama**

Características:

* Ejecución local.
* Funcionamiento sin conexión a Internet.
* Aceleración mediante GPU.
* Sistema de respaldo en caso de:

  * Cuota excedida.
  * Fallos de red.
  * Fallos del servicio principal.

El flujo general es:

```text
Usuario
   │
   ▼
Gemini 3.6 Flash
   │
   ├── Respuesta correcta ──► Usuario
   │
   └── Error / Cuota / Red
              │
              ▼
       Qwen 2.5 Coder 14B
              │
              ▼
           Usuario
```

### 🧠 Memoria Persistente con Caché Local

Sistema de memoria basado en:

* PostgreSQL Serverless.
* Neon DB.
* Psycopg2.
* Caché local en RAM.
* Precarga de información al iniciar.
* Sincronización asíncrona con la base de datos.

La arquitectura permite reducir la latencia al consultar información previamente almacenada.

### 🎙️ Interacción Manos Libres y Wake Word

El asistente puede permanecer escuchando de forma pasiva para detectar palabras clave como:

> **"Amigo"**

o:

> **"Oye Causa"**

Incluye:

* Activación mediante voz.
* Wake Word.
* Corte forzado mediante `F9`.
* Detección de silencio.
* Reposo automático.

### 🎵 Automatización Multimedia y Audio Ducking

#### Spotify

AmigoNeon puede interactuar con Spotify mediante:

* Detección visual con OpenCV.
* Template Matching.
* Automatización de teclado como fallback.
* Reproducción de canciones.
* Control automático del volumen.

#### YouTube

Permite:

* Búsqueda semántica.
* Extracción de títulos.
* Apertura del navegador.
* Reproducción directa.

#### 🔊 Audio Ducking

Durante una conversación, el volumen de Spotify puede reducirse automáticamente.

```text
Inicio del diálogo
        │
        ▼
Volumen → 15%
        │
        ▼
Conversación
        │
        ▼
Fin del diálogo
        │
        ▼
Volumen → 80-100%
```

Esto permite que la voz del asistente se escuche claramente mientras la música continúa reproduciéndose.

### 👁️ Visión por Pantalla

AmigoNeon puede capturar y analizar el monitor cuando recibe comandos como:

> **"Mira mi pantalla"**

o:

> **"Opinas"**

La pantalla se captura y se procesa como una imagen codificada en Base64 para enviarla al sistema de visión artificial.

### 🖥️ Control del Sistema Operativo

El asistente permite realizar acciones sobre Windows:

* Ajustar el volumen.
* Silenciar completamente el audio.
* Consultar la hora.
* Buscar documentos.
* Abrir programas.
* Automatizar teclado y mouse.

Aplicaciones compatibles:

```text
Word
Excel
Calculadora
Bloc de notas
```

---

# 🛠️ Stack Tecnológico

| Componente                    | Tecnología                      |
| ----------------------------- | ------------------------------- |
| **Lenguaje**                  | Python 3.11                     |
| **Frontend / GUI**            | PyQt6                           |
| **Modelo LLM Principal**      | Google Gemini 3.6 Flash         |
| **Modelo LLM Local**          | Qwen 2.5 Coder 14B + Ollama     |
| **Base de Datos**             | Neon DB / PostgreSQL Serverless |
| **Driver PostgreSQL**         | Psycopg2                        |
| **Visión Computacional**      | OpenCV                          |
| **Captura de Pantalla**       | MSS                             |
| **Procesamiento de Imágenes** | Pillow                          |
| **Reconocimiento de Voz**     | SpeechRecognition               |
| **Audio de Entrada**          | PyAudio                         |
| **Síntesis de Voz**           | Edge-TTS                        |
| **Voz TTS**                   | `es-MX-JorgeNeural`             |
| **Procesamiento de Audio**    | FFmpeg / Pydub                  |
| **Reproducción de Audio**     | Pygame                          |
| **Control de Audio**          | PyCAW                           |
| **API Windows**               | Comtypes                        |
| **Automatización**            | PyAutoGUI / Keyboard            |

---

# 📁 Estructura del Proyecto

```text
AmigoNeon/
│
├── assets/
│   ├── sprites/
│   │   ├── quieto.png
│   │   └── hablando.png
│   │
│   └── icons/
│       └── play_verde.png
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── core/
│   ├── __init__.py
│   ├── cerebro.py
│   └── memoria.py
│
├── services/
│   ├── __init__.py
│   ├── voz.py
│   ├── vision.py
│   └── musica.py
│
├── ui/
│   ├── __init__.py
│   ├── avatar.py
│   └── chat_panel.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── main.py
```

---

# 📂 Descripción de Directorios

## `assets/`

Contiene los recursos gráficos y multimedia utilizados por el asistente.

```text
assets/
├── sprites/
└── icons/
```

### `assets/sprites/`

Contiene los sprites del avatar:

* `quieto.png` → Estado de reposo.
* `hablando.png` → Estado de conversación.

### `assets/icons/`

Contiene los iconos utilizados por la interfaz.

---

## `config/`

Contiene la configuración global del proyecto.

### `settings.py`

Centraliza:

* Variables de entorno.
* Rutas.
* Configuración de modelos.
* Parámetros generales del sistema.

---

## `core/`

Contiene el núcleo de inteligencia.

### `cerebro.py`

Gestiona:

* Google Gemini.
* Fallback hacia Ollama.
* Procesamiento de instrucciones.
* Selección del motor de IA.
* Contexto de conversación.

### `memoria.py`

Gestiona:

* Conexión con Neon DB.
* Lectura de memoria.
* Escritura de nuevos recuerdos.
* Sincronización.
* Caché local.

---

## `services/`

Contiene los servicios relacionados con hardware, audio, visión y multimedia.

### `voz.py`

Gestiona:

* Reconocimiento de voz.
* Wake Word.
* Edge-TTS.
* FFmpeg.
* Pydub.
* Cálculo RMS.
* Lipsync.
* Reproducción de audio.

### `vision.py`

Gestiona:

* Captura del monitor.
* Procesamiento de imágenes.
* Conversión a Base64.
* Preparación de imágenes para el modelo de visión.

### `musica.py`

Gestiona:

* Spotify.
* YouTube.
* Reproducción multimedia.
* Audio Ducking.
* Automatización de teclado.
* Control del volumen.

---

## `ui/`

Contiene los componentes gráficos.

### `avatar.py`

Gestiona:

* Ventana transparente.
* Overlay.
* Movimiento del avatar.
* Posicionamiento.
* Lipsync.
* Eventos del mouse.

### `chat_panel.py`

Gestiona:

* Historial de mensajes.
* Entrada de texto.
* Botón de micrófono.
* Interacción con el asistente.

---

# 🚀 Instalación y Despliegue

## 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/AmigoNeon.git
cd AmigoNeon
```

---

## 2. Crear el entorno virtual

```bash
python -m venv venv
```

Activar el entorno virtual en Windows:

```powershell
venv\Scripts\activate
```

---

## 3. Instalar dependencias

Ejecuta:

```bash
pip install -r requirements.txt
```

---

## 4. Instalar FFmpeg

AmigoNeon requiere **FFmpeg** para procesar la síntesis de voz y calcular las métricas PCM utilizadas para el lipsync.

En Windows puedes instalarlo mediante:

```powershell
winget install Gyan.FFmpeg
```

Después puedes comprobar la instalación:

```powershell
ffmpeg -version
```

---

# 🔐 5. Configurar Variables de Entorno

Crea un archivo:

```text
.env
```

en la raíz del proyecto.

Puedes utilizar `.env.example` como plantilla.

Ejemplo:

```env
GEMINI_API_KEY=tu_gemini_api_key_aqui

DATABASE_URL=postgresql://usuario:password@ep-ejemplo.neon.tech/neondb?sslmode=require
```

> ⚠️ **Importante:** Nunca publiques tu archivo `.env` ni compartas públicamente tus claves API o credenciales de base de datos.

El archivo `.env` debe estar incluido en `.gitignore`.

---

# ▶️ 6. Iniciar AmigoNeon

Una vez configurado el entorno:

```bash
python main.py
```

Si todo está correctamente configurado, se iniciará el avatar VTuber y el sistema quedará listo para recibir comandos.

---

# 🎮 Guía de Uso

## 🎙️ Activación por Voz

Puedes activar el asistente pronunciando:

```text
"Amigo"
```

o:

```text
"Oye Causa"
```

Después de detectar la palabra clave, AmigoNeon comenzará a escuchar tu solicitud.

---

## 😴 Auto-Reposo

Si el sistema detecta aproximadamente **6 segundos de silencio**, el asistente:

1. Finaliza el turno.
2. Detiene la interacción de voz.
3. Regresa al estado de reposo.
4. Restaura el volumen de la música.

---

# 💬 Panel de Chat Gráfico

Haz:

```text
Doble clic sobre el avatar
```

para abrir o contraer el panel de chat.

Desde este panel puedes:

* Escribir mensajes.
* Consultar respuestas.
* Ver el historial.
* Activar el micrófono manualmente.

---

# ⌨️ Atajos Rápidos

| Tecla / Acción | Función                                           |
| -------------- | ------------------------------------------------- |
| `F9`           | Silenciar inmediatamente / forzar corte del turno |
| `Enter` vacío  | Activar el micrófono                              |
| `Doble clic`   | Abrir / cerrar panel de chat                      |

---

# 🤖 Comandos de Ejemplo

## 🎵 Spotify

Puedes decir:

```text
Pon rock clásico en Spotify
```

El asistente puede:

1. Interpretar la solicitud.
2. Buscar la canción.
3. Detectar la interfaz de Spotify.
4. Ejecutar la reproducción.
5. Reducir el volumen durante la conversación.

---

## ▶️ YouTube

Ejemplo:

```text
Pon la canción de lomo saltado en YouTube
```

El asistente buscará el contenido y abrirá la reproducción en el navegador web.

---

## 👁️ Analizar la Pantalla

Ejemplo:

```text
Mira mi pantalla y dime qué opinas de este error
```

AmigoNeon:

1. Captura el monitor.
2. Procesa la imagen.
3. Envía la captura al sistema de visión.
4. Analiza el contenido.
5. Responde mediante voz.

---

## 🔊 Controlar el Volumen

Ejemplo:

```text
Pon el volumen al 50%
```

También:

```text
Silencio total
```

El sistema utiliza **PyCAW** para controlar el volumen del sistema operativo.

---

## 🖥️ Abrir Aplicaciones

Ejemplos:

```text
Abre Word
```

```text
Abre la calculadora
```

```text
Abre Excel
```

```text
Abre el bloc de notas
```

El asistente puede lanzar determinadas aplicaciones de Windows mediante comandos del sistema.

---

# 🧠 Memoria Persistente

AmigoNeon puede aprender información proporcionada explícitamente por el usuario.

Por ejemplo:

```text
Aprende que mi lenguaje favorito es Python
```

El sistema puede almacenar este dato en **Neon DB** para recuperarlo posteriormente.

La arquitectura utiliza:

```text
Usuario
   │
   ▼
AmigoNeon
   │
   ├── Caché RAM
   │
   └── PostgreSQL
          │
          ▼
       Neon DB
```

Esto permite mantener determinados recuerdos incluso después de cerrar y volver a iniciar el programa.

---

# 🏗️ Arquitectura General

```text
                         ┌─────────────────────┐
                         │      USUARIO        │
                         └──────────┬──────────┘
                                    │
                         Voz / Texto / Acciones
                                    │
                                    ▼
                    ┌─────────────────────────────┐
                    │         AMIGONEON           │
                    │      Orquestador GUI        │
                    └─────────────┬───────────────┘
                                  │
               ┌──────────────────┼──────────────────┐
               │                  │                  │
               ▼                  ▼                  ▼
        ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
        │     Voz     │    │   Visión    │    │   Música    │
        │ Edge-TTS    │    │   OpenCV    │    │ Spotify     │
        │ SpeechRec.  │    │    MSS      │    │ YouTube     │
        └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
               │                  │                  │
               └──────────────────┼──────────────────┘
                                  │
                                  ▼
                       ┌────────────────────┐
                       │    CEREBRO IA      │
                       └─────────┬──────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
          ┌─────────────────┐       ┌──────────────────┐
          │ Gemini 3.6      │       │ Qwen 2.5 Coder   │
          │ Flash           │       │ 14B + Ollama     │
          │                 │       │                  │
          │ Cloud + Search  │       │ Local / Offline  │
          └─────────────────┘       └──────────────────┘
                    │                         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                       ┌──────────────────┐
                       │     MEMORIA      │
                       │                  │
                       │ RAM + Neon DB    │
                       └──────────────────┘
```

---

# 🔄 Flujo de Funcionamiento

```text
1. Inicio de AmigoNeon
        │
        ▼
2. Carga de configuración
        │
        ▼
3. Carga de memoria desde Neon DB
        │
        ▼
4. Inicio del avatar VTuber
        │
        ▼
5. Espera de Wake Word
        │
        ▼
6. "Amigo" / "Oye Causa"
        │
        ▼
7. Captura de voz
        │
        ▼
8. Interpretación de la solicitud
        │
        ▼
9. Selección del motor IA
        │
        ├───────────────┐
        ▼               ▼
     Gemini          Ollama
        │               │
        └───────┬───────┘
                │
                ▼
10. Ejecución de acciones
                │
        ┌───────┼────────┐
        ▼       ▼        ▼
      Música  Visión   Sistema
        │       │        │
        └───────┼────────┘
                ▼
11. Generación de respuesta
                │
                ▼
12. Síntesis de voz
                │
                ▼
13. Lipsync del avatar
                │
                ▼
14. Respuesta al usuario
                │
                ▼
15. Auto-reposo
```

---

# 🔒 Seguridad

Por seguridad, nunca debes subir al repositorio:

```text
.env
```

ni ningún archivo que contenga:

* API Keys.
* Contraseñas.
* Tokens.
* Credenciales de PostgreSQL.
* Información privada.

Ejemplo de `.gitignore`:

```gitignore
# Entorno virtual
venv/
.venv/

# Variables de entorno
.env

# Caché de Python
__pycache__/
*.pyc

# IDE
.vscode/
.idea/

# Archivos temporales
*.tmp
*.log
```

---

# 📦 Dependencias Principales

Las principales dependencias utilizadas por el proyecto incluyen:

```text
PyQt6
google-generativeai
ollama
psycopg2
opencv-python
Pillow
mss
SpeechRecognition
PyAudio
edge-tts
pydub
pygame
pycaw
comtypes
pyautogui
keyboard
python-dotenv
```

Las versiones concretas deben mantenerse en:

```text
requirements.txt
```

---

# 🌟 Objetivo del Proyecto

**AmigoNeon** busca combinar inteligencia artificial, automatización, visión computacional y una interfaz VTuber en una única aplicación de escritorio.

La idea es convertir al asistente en una especie de **compañero digital interactivo**, capaz de:

* Escuchar.
* Hablar.
* Ver la pantalla.
* Recordar información.
* Ejecutar acciones.
* Controlar multimedia.
* Automatizar tareas.
* Responder mediante IA.
* Funcionar parcialmente de manera local.

La arquitectura híbrida permite combinar las ventajas de los modelos en la nube con la privacidad, disponibilidad y autonomía de un modelo local.

---

# 🚧 Estado del Proyecto

**En desarrollo 🚀**

AmigoNeon continúa evolucionando con nuevas capacidades de:

* Inteligencia artificial.
* Automatización.
* Visión computacional.
* Interacción por voz.
* Personalización del avatar.
* Memoria persistente.
* Integración con aplicaciones de escritorio.

---

# 👨‍💻 Autor

**AmigoNeon**

Proyecto experimental de asistente de escritorio VTuber desarrollado con Python, PyQt6, inteligencia artificial y automatización para Windows.
