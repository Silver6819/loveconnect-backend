import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()
usuarios = {}

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return """
    <html>
        <head>
            <title>LoveConnect - Registro</title>
            <style>
                body { font-family: sans-serif; text-align: center; background: #fff0f3; padding: 20px; }
                .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(255,75,110,0.2); max-width: 400px; margin: auto; }
                h1 { color: #ff4b6e; margin-bottom: 5px; }
                input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; }
                .btn { display: block; width: 100%; padding: 12px; margin: 10px 0; background: #ff4b6e; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; text-decoration: none; }
                .btn-view { background: #5d5d5d; }
                label { display: block; text-align: left; margin-left: 5%; font-weight: bold; color: #555; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>💖 LoveConnect</h1>
                <p>Crea tu perfil de citas</p>
                <hr style="border:0; border-top: 1px solid #eee; margin: 20px 0;">
                
                <label>Nombre:</label>
                <input type="text" id="nombre" placeholder="Ej: Silver">
                
                <label>Edad:</label>
                <input type="number" id="edad" placeholder="Ej: 25">
                
                <label>Ubicación:</label>
                <input type="text" id="ubicacion" placeholder="Ej: Ahuachapan">
                
                <button class="btn" onclick="registrar()">🚀 Registrarme Ahora</button>
                
                <a href="/api/usuarios/ver" class="btn btn-view">👥 Ver Comunidad</a>
            </div>

            <script>
                function registrar() {
                    const n = document.getElementById('nombre').value;
                    const e = document.getElementById('edad').value;
                    const u = document.getElementById('ubicacion').value;
                    if(n && e && u) {
                        window.location.href = `/api/registrar/${n}/${e}/${u}`;
                    } else {
                        alert('Por favor, llena todos los campos');
                    }
                }
            </script>
        </body>
    </html>
    """

@app.get("/api/registrar/{nombre}/{edad}/{ubicacion}")
async def registrar(nombre: str, edad: int, ubicacion: str):
    usuarios[nombre] = {"edad": edad, "ubicacion": ubicacion, "chats": []}
    return HTMLResponse(f"<html><body style='text-align:center;font-family:sans-serif;padding:50px;'><h1>✅ Registro Exitoso</h1><p>Bienvenido/a {nombre} de {ubicacion}.</p><a href='/' style='color:#ff4b6e;font-weight:bold;'>Volver al Inicio</a></body></html>")

@app.get("/api/usuarios/ver")
async def ver_usuarios():
    return {"comunidad": usuarios}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
