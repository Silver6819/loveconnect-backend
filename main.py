import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()
usuarios = {}

ESTILOS = """
<style>
    body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #fdf2f4; color: #444; margin: 0; padding: 20px; }
    .container { max-width: 500px; margin: auto; }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 8px 20px rgba(255,75,110,0.15); margin-bottom: 20px; }
    h1 { color: #ff4b6e; text-align: center; font-weight: bold; }
    h2 { color: #333; margin-top: 0; }
    .info { font-size: 0.9em; color: #777; margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 10px; }
    .chat-box { background: #fff9fa; padding: 15px; border-radius: 12px; border: 1px solid #ffeef1; }
    .mensaje { background: white; padding: 10px; margin: 8px 0; border-radius: 10px; font-size: 0.9em; border: 1px solid #ffd1dc; color: #555; }
    .btn { display: inline-block; width: 100%; padding: 14px; background: #ff4b6e; color: white; text-decoration: none; border-radius: 10px; font-weight: bold; text-align: center; border: none; cursor: pointer; font-size: 16px; }
    .btn-secondary { background: #6c757d; margin-top: 10px; }
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; box-sizing: border-box; }
    label { font-weight: bold; font-size: 0.85em; color: #ff4b6e; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><title>LoveConnect</title>{ESTILOS}</head>
        <body>
            <div class="container">
                <h1>💖 LoveConnect</h1>
                <div class="card">
                    <h2>Crear Perfil</h2>
                    <label>Nombre Completo</label>
                    <input type="text" id="n" placeholder="Tu nombre">
                    <label>Edad</label>
                    <input type="number" id="e" placeholder="Tu edad">
                    <label>Ciudad</label>
                    <input type="text" id="u" placeholder="Tu ciudad">
                    <button class="btn" onclick="reg()">Registrarse Ahora</button>
                </div>
                <div class="card">
                    <h2>Enviar Mensaje</h2>
                    <input type="text" id="em" placeholder="De:">
                    <input type="text" id="re" placeholder="Para:">
                    <input type="text" id="me" placeholder="Mensaje...">
                    <button class="btn" style="background:#ff8da1;" onclick="env()">Enviar</button>
                </div>
                <a href="/api/usuarios/ver" class="btn btn-secondary">👥 Ver Directorio</a>
            </div>
            <script>
                function reg() {{
                    const n = document.getElementById('n').value;
                    const e = document.getElementById('e').value;
                    const u = document.getElementById('u').value;
                    if(n && e && u) {{
                        // Usamos encodeURIComponent para que acepte espacios en los nombres
                        window.location.href = `/api/registrar?nombre=${{encodeURIComponent(n)}}&edad=${{e}}&ubicacion=${{encodeURIComponent(u)}}`;
                    } else {{ alert('Completa todos los campos'); }}
                }}
                function env() {{
                    const em = document.getElementById('em').value;
                    const re = document.getElementById('re').value;
                    const me = document.getElementById('me').value;
                    if(em && re && me) {{
                        window.location.href = `/api/chatear?emisor=${{encodeURIComponent(em)}}&receptor=${{encodeURIComponent(re)}}&mensaje=${{encodeURIComponent(me)}}`;
                    }} else {{ alert('Completa el chat'); }}
                }}
            </script>
        </body>
    </html>
    """

# Cambiamos la forma de recibir datos a "Query Parameters" para evitar el error de "Not Found"
@app.get("/api/registrar")
async def registrar(nombre: str, edad: int, ubicacion: str):
    usuarios[nombre] = {"edad": edad, "ubicacion": ubicacion, "chats": []}
    return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='container'><div class='card'><h1>✅ Registrado</h1><p>Bienvenido, {nombre}.</p><a href='/' class='btn'>Volver</a></div></div></body></html>")

@app.get("/api/chatear")
async def chatear(emisor: str, receptor: str, mensaje: str):
    if receptor in usuarios:
        usuarios[receptor]["chats"].append(f"De {emisor}: {mensaje}")
        return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='container'><div class='card'><h1>✉️ Enviado</h1><a href='/' class='btn'>Volver</a></div></div></body></html>")
    return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='container'><div class='card'><h1>❌ Error</h1><p>El usuario {receptor} no existe.</p><a href='/' class='btn'>Volver</a></div></div></body></html>")

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver_usuarios():
    cartas = ""
    for nombre, datos in usuarios.items():
        mensajes = "".join([f"<div class='mensaje'>{m}</div>" for m in datos['chats']])
        cartas += f"""
        <div class="card">
            <h2>👤 {nombre}</h2>
            <div class="info">📍 {datos['ubicacion']} | 🎂 {datos['edad']} años</div>
            <div class="chat-box"><strong>Bandeja:</strong>{mensajes if datos['chats'] else '<p>Vacío</p>'}</div>
        </div>"""
    return f"<html><head>{ESTILOS}</head><body><div class='container'><h1>👥 Directorio</h1>{cartas}<center><a href='/' class='btn btn-secondary'>Volver</a></center></div></body></html>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
