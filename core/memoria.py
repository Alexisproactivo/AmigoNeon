import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("NEON_DB_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def inicializar_tabla_neon():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memoria_amigo (
                        id SERIAL PRIMARY KEY,
                        categoria VARCHAR(50),
                        clave VARCHAR(100) UNIQUE,
                        valor TEXT,
                        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                print("[Neon DB]: Tabla de memoria sincronizada correctamente.")
    except Exception as e:
        print(f"[Error al conectar con Neon]: {e}")

def guardar_recuerdo(categoria, clave, valor):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memoria_amigo (categoria, clave, valor)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (clave) 
                    DO UPDATE SET valor = EXCLUDED.valor;
                """, (categoria, clave.lower().strip(), valor.strip()))
                conn.commit()
    except Exception as e:
        print(f"[Error guardando en Neon]: {e}")

def cargar_memoria_completa():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT clave, valor FROM memoria_amigo ORDER BY id ASC;")
                filas = cur.fetchall()
                if not filas:
                    return ""
                recuerdos = "\n".join([f"- {k}: {v}" for k, v in filas])
                return f"\nLO QUE RECUERDAS SOBRE EL JEFE:\n{recuerdos}\n"
    except Exception:
        return ""

# Inicializa la tabla en cuanto se ejecuta
if __name__ == "__main__":
    inicializar_tabla_neon()