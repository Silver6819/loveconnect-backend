import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
usuarios = {}

# Estilos mejorados para que carguen rápido y no fallen
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #fdf2f4; color: #444; margin: 0; padding: 20px; }
    .container { max-width: 500px; margin: auto; }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); margin-bottom: 20px; border: 1px solid #eee; }
    h1 { color: #ff4b6e; text-align: center; }
    .btn { display: block; width: 100%; padding: 14px; background: #ff4b6e; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; text-align: center; border: none; cursor: pointer; transition: 0.2s; }
    .btn:active { transform: scale(0.98); }
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; }
    .mensaje { background: #fff9fa; padding: 10px; margin: 5px 0; border-radius: 8px; border-left: 4px solid #ff4b6e; font-size: 0.9em; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1"><title>LoveConnect Pro</title>{ESTILOS}</head>
        <body>
            <div class="container">
                <h1>💖 LoveConnect</h1>
                <div class="card">
                    <h3>Registro</h3>
                    <input type="text" id="n" placeholder="Nombre">
                    <input type="number" id="e" placeholder="Edad">
                    <input type="text" id="u" placeholder="Ciudad">
                    <button class="btn" onclick="reg()">Registrarse</button>
                </div>
                <div class="card">
                    <h3>Chat Directo</h3>
                    <input type="text" id="em" placeholder="Tu nombre">
                    <input type="text" id="re" placeholder="Para quien">
                    <input type="text" id="me" placeholder="Mensaje">
                    <button class="btn" style="background:#5d5d5d;" onclick="env()">Enviar Mensaje</button>
                </div>
                <button class="btn" style="background:#bbb;" onclick="location.href='/api/usuarios/ver'">Ver Directorio</button>
            </div>
            <script>
                function reg() {{
                    const n=document.getElementById('n').value, e=document.getElementById('e').value, u=document.getElementById('u').value;
                    if(n && e && u) location.href=`/api/registrar?nombre=${{encodeURIComponent(n)}}&edad=${{e}}&ubicacion=${{encodeURIComponent(u)}}`;
                }}
                function env() {{
                    const em=document.getElementById('em').value, re=document.getElementById('re').value, me=document.getElementById('me').value;
                    if(em && re && me) location.href=`/api/chatear?emisor=${{encodeURIComponent(em)}}&receptor=${{encodeURIComponent(re)}}&mensaje=${{encodeURIComponent(me)}}`;
                }}
            </script>
        </body>
    </html>
    """

@app.get("/api/registrar")
async def registrar(nombre: str, edad: int, ubicacion: str):
    try:
        usuarios[nombre] = {"edad": edad, "ubicacion": ubicacion, "chats": []}
        return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✅ Guardado</h2><a href='/' class='btn'>Volver</a></div></body></html>")
    except Exception as e:
        return HTMLResponse("<h2>Error al registrar. Intenta de nuevo.</h2>")

@app.get("/api/chatear")
async def chatear(emisor: str, receptor: str, mensaje: str):
    if receptor in usuarios:
        usuarios[receptor]["chats"].append(f"{emisor}: {mensaje}")
        return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✉️ Enviado</h2><a href='/' class='btn'>Volver</a></div></body></html>")
    return HTMLResponse("<h2>El usuario no existe.</h2><a href='/'>Volver</a>")

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver_usuarios():
    cartas = ""
    for nombre, datos in usuarios.items():
        mensajes = "".join([f"<div class='mensaje'>{m}</div>" for m in datos['chats']])
        cartas += f"<div class='card'><h2>{nombre}</h2><p>{datos['ubicacion']} | {datos['edad']} años</p><div>{mensajes if mensajes else 'Sin mensajes'}</div></div>"
    return f"<html><head>{ESTILOS}</head><body><div class='container'><h1>Directorio</h1>{cartas}<a href='/' class='btn'>Cerrar</a></div></body></html>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
