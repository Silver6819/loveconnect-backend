import os
import uvicorn
from fastapi import FastAPI

app = FastAPI()

# Tu función de salud que ya funciona
@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "LoveConnect Activo"}

# NUEVA FUNCIÓN: Recibe un nombre y responde
@app.get("/api/saludo/{nombre}")
async def saludar(nombre: str):
    return {"mensaje": f"Hola {nombre}, tu servidor está procesando datos"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
