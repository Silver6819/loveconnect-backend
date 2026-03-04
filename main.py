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
            <title>LoveConnect - Home</title>
            <style>
                body { font-family: 'Segoe UI', sans-serif; text-align: center; background: #fff0f3; padding: 20px; color: #333; }
                .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(255,75,110,0.2); max-width: 450px; margin: 15px auto; }
                h1 { color: #ff4b6e; margin-bottom: 5px; }
                input, select { width: 90%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; font-size: 16px; }
                .btn { display: block; width: 100%; padding: 12px; margin: 10px 0; background: #ff4b6e; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; text-decoration: none; font-size: 16px; }
                .btn-chat { background: #4b7bff; }
                .btn-view { background: #5d5d5d; }
                label { display: block; text-align: left; margin-left: 5%; font-weight: bold; color: #555; }
                hr { border: 0; border-top: 1px solid #eee; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>💖 LoveConnect</h1>
                <p>Crea tu perfil y busca pareja</p>
                <hr>
                <label>Tu Nombre:</label>
                <input type="text" id="n_reg" placeholder="Ej: Silver">
                <label>Tu Edad:</label>
                <input type="number" id="e_reg" placeholder="Ej: 25">
                <label>Tu Ubicación:</label>
                <input type="text" id="u_reg" placeholder="Ej: Ahuachapan">
                <button class="btn" onclick="registrar()">🚀 Registrarme Ahora</button>
            </div>

            <div class="card">
                <h3>💬 Enviar Mensaje</h3>
                <label>De (Tu nombre):</label>
                <input type="text" id="emisor" placeholder="Tu nombre">
                <label>Para (Nombre del destino):</label>
                <input type="text" id="receptor" placeholder="Nombre de la persona">
                <label>Mensaje:</label>
                <input type="text" id="mensaje" placeholder="Escribe algo lindo...">
                <button class="btn btn-chat" onclick="enviar()">✉️ Enviar Mensaje</button>
                <hr>
                <a href="/api/usuarios/ver" class="btn btn-view">👥 Ver Comunidad y Chats</a>
            </div>

            <script>
                function registrar() {
                    const n = document.getElementById('n_reg').value;
                    const e = document.getElementById('e_reg').value;
                    const u = document.getElementById('u_reg').value;
                    if(n && e && u) window.location.href = `/api/registrar/${n}/${e}/${u}`;
                    else alert('Llena los datos de registro');
                }

                function enviar() {
                    const em = document.getElementById('emisor').value;
                    const re = document.getElementById('receptor').value;
                    const me = document.getElementById('mensaje').value;
                    if(em && re && me) window.location.href = `/api/chatear/${em}/${re}/${me}`;
                    else alert('Completa los campos del chat');
                }
            </script>
        </body>
    </html>
    """

@app.get("/api/registrar/{nombre}/{edad}/{ubicacion}")
async def registrar(nombre: str, edad: int, ubicacion: str):
    usuarios[nombre] = {"edad": edad, "ubicacion": ubicacion, "chats": []}
    return HTMLResponse(f"<html><body style='text-align:center;font-family:sans-serif;padding:50px;'><h1>✅ Perfil Creado</h1><p>Bienvenido {nombre}.</p><a href='/'>Volver al Inicio</a></body></html>")

@app.get("/api/chatear/{emisor}/{receptor}/{mensaje}")
async def chatear(emisor: str, receptor: str, mensaje: str):
    if receptor in usuarios:
        usuarios[receptor]["chats"].append(f"{emisor}: {mensaje}")
        return HTMLResponse(f"<html><body style='text-align:center;font-family:sans-serif;padding:50px;'><h1>✉️ Mensaje Enviado</h1><p>Enviaste: '{mensaje}' a {receptor}.</p><a href='/'>Volver al Inicio</a></body></html>")
    return HTMLResponse("<html><body style='text-align:center;padding:50px;'><h1>❌ Error</h1><p>Esa persona no existe.</p><a href='/'>Volver</a></body></html>")

@app.get("/api/usuarios/ver")
async def ver_usuarios():
    return {"comunidad": usuarios}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
