import os
from pathlib import Path
from dotenv import load_dotenv

# Ruta raíz del proyecto (AmigoNeon/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde el archivo .env de la raíz
load_dotenv(BASE_DIR / ".env")

# API Keys y Conexiones
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", os.getenv("NEON_DB_URL", ""))

# Rutas centralizadas de Assets
SPRITES_DIR = BASE_DIR / "assets" / "sprites"
ICONS_DIR = BASE_DIR / "assets" / "icons"
QUIETO_PATH = SPRITES_DIR / "quieto.png"
HABLANDO_PATH = SPRITES_DIR / "hablando.png"

# Parámetros del Asistente
VOZ_NOMBRE = "es-MX-JorgeNeural"
OLLAMA_MODEL = "qwen2.5-coder:14b"