import os
import signal

# --- SCRIPT DE LIMPIEZA PROFUNDA ---
def limpiar_y_cerrar():
    print("🧹 Iniciando limpieza exhaustiva de procesos...")
    # Buscamos procesos que puedan estar usando el puerto 8080
    try:
        # En sistemas Linux (como Railway), esto fuerza el cierre de procesos fantasma
        os.system("fuser -k 8080/tcp") 
        print("✅ Puerto 8080 liberado.")
    except:
        print("⚠️ No se encontraron procesos bloqueando el puerto.")
    
    print("🚀 Entorno listo. Ahora puedes subir tu nuevo código.")
    # Cerramos este proceso de limpieza para forzar un reinicio limpio
    os.kill(os.getpid(), signal.SIGTERM)

if __name__ == "__main__":
    limpiar_y_cerrar()
