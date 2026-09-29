import sys
import time
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CARPETA_PROYECTO = Path(__file__).resolve().parent

class RecargadorAutomatico(FileSystemEventHandler):
    def __init__(self):
        self.proceso = None
        self.ultimo_reinicio = 0
        self.arrancar_bot()

    def arrancar_bot(self):
        if self.proceso:
            print("\n[Auto-Reload] Cambio detectado. Reiniciando AmigoNeon...")
            self.proceso.terminate()
            try:
                self.proceso.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.proceso.kill()
        
        print("[Auto-Reload] Iniciando main.py...")
        # Lanza main.py con el mismo intérprete de Python activo
        self.proceso = subprocess.Popen([sys.executable, "main.py"])

    def on_modified(self, event):
        # Solo reacciona a cambios en archivos de código o interfaces
        if event.src_path.endswith((".py", ".json", ".qss")):
            # Evita reinicios dobles si el editor guarda muy rápido
            ahora = time.time()
            if ahora - self.ultimo_reinicio > 1.2:
                self.ultimo_reinicio = ahora
                self.arrancar_bot()

if __name__ == "__main__":
    manejador = RecargadorAutomatico()
    observador = Observer()
    observador.schedule(manejador, path=str(CARPETA_PROYECTO), recursive=True)
    observador.start()

    print("=== MODO DESARROLLADOR ACTIVO ===")
    print("Modifica cualquier archivo y presiona Ctrl + S: el bot se reiniciará solo.")
    print("Presiona Ctrl + C en esta consola para detenerlo.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observador.stop()
        if manejador.proceso:
            manejador.proceso.terminate()
    observador.join()