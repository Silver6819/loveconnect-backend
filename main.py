import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()
tareas = []

@app.get("/", response_class=HTMLResponse)
async def inicio():
return """
<html>
<head>
<title>LoveConnect - Panel</title>
<style>
body { font-family: sans-serif; text-align: center; background: #eef2f3; padding: 40px; }
.card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); max-width: 450px; margin: auto; }
.btn { display: block; width: 100%; padding: 12px; margin: 15px 0; background: #3498db; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; }
.btn-green { background: #27ae60; }
</style>
</head>
<body>
<div class="card">
<h1>🚀 LoveConnect</h1>
<p>Servidor de Silver Breaker Activo</p>
<a href="/api/health" class="btn">📡 Revisar Estado</a>
<a href="/api/sumar/10/5" class="btn">🧮 Calculadora (10+5)</a>
<a href="/api/tareas/ver" class="btn btn-green">📝 Ver Mis Tareas</a>
</div>
</body>
</html>
"""

@app.get("/api/health")
async def health():
return {"status": "ok", "message": "Servidor Activo"}

@app.get("/api/sumar/{num1}/{num2}")
async def sumar(num1: int, num2: int):
return {"resultado": num1 + num2}

@app.get("/api/tareas/agregar/{texto}")
async def agregar_tarea(texto: str):
tareas.append(texto)
return {"mensaje": "Guardada", "lista": tareas}

@app.get("/api/tareas/ver")
async def ver_tareas():
return {"tus_tareas": tareas}

if name == "main":
port = int(os.environ.get("PORT", 8080))
uvicorn.run(app, host="0.0.0.0", port=port)
