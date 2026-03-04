import os
import uvicorn
from fastapi import FastAPI

app = FastAPI()

# Memoria temporal para las tareas
tareas = []

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Servidor Multitarea Activo"}

# --- FUNCIÓN 1: CALCULADORA ---
@app.get("/api/sumar/{num1}/{num2}")
async def sumar(num1: int, num2: int):
    resultado = num1 + num2
    return {"operacion": "suma", "resultado": resultado}

# --- FUNCIÓN 2: LISTA DE TAREAS ---
@app.get("/api/tareas/agregar/{texto}")
async def agregar_tarea(texto: str):
    tareas.append(texto)
    return {"mensaje": "Tarea guardada", "lista_actual": tareas}

@app.get("/api/tareas/ver")
async def ver_tareas():
    return {"tus_tareas": tareas}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
