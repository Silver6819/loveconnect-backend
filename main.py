import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()
usuarios = {}

# Estilos modernos estilo App de Android
ESTILOS = """
<style>
    body { font-family: 'Roboto', sans-serif; background: #fdf2f4; color: #444; margin: 0; padding: 10px; }
    .container { max-width: 500px; margin: auto; }
    .card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #fce4ec; position: relative; }
    .profile-header { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; }
    .avatar { width: 60px; height: 60px; background: #ffcbd5; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px; color: white; }
    h1 { color: #ff4b6e; text-align: center; font-size: 1.8em; }
    h2 { margin: 0; font-size: 1.2em; color: #333; }
    .status { font-size: 0.75em; color: #4caf50; font-weight: bold; }
    .tag { font-size: 0.8em; background: #f0f0f0; padding: 3px 8px; border-radius: 10px; color: #666; }
    .chat-box { background: #fef9fa; border-radius: 12px; padding: 10px; margin-top: 10px; border: 1px solid #fff0f3; }
    .mensaje { font-size: 0.85em; margin: 5px 0; padding: 8px; background: white; border-radius: 8px; border-left: 3px solid #ff4b6e; }
    .hora { font-size: 0.7em; color: #aaa; display: block; margin-top: 3px; }
    .btn { display: block; width: 100%; padding: 12px; background: #ff4b6e; color: white; border-radius: 12px; font-weight: bold; text-align: center; border: none; cursor: pointer; margin-top: 10px; text-decoration: none; }
    .btn-search { background: #5c6bc0; }
    input { width: 100%; padding: 12px; margin: 5px 0; border: 1px solid #eee; border-radius: 10px; box-sizing: border-box; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div class="container">
                <h1>💖 LoveConnect</h1>
                <div class="card">
                    <h3>Registrar Perfil</h3>
                    <input type="text" id="n" placeholder="Nombre completo">
                    <input type="number" id="e" placeholder="Edad">
                    <input type="text" id="u" placeholder="Tu Ciudad (Región)">
                    <button class="btn" onclick="reg()">Crear mi Perfil</button>
                </div>
                <div class="card">
                    <h3>Buscador por Región</h3>
                    <input type="text" id="busq" placeholder="Escribe una ciudad...">
                    <button class="btn btn-search" onclick="location.href='/api/usuarios/ver?region='+document.getElementById('busq').value">🔍 Buscar en mi región</button>
                </div>
                <div class="card">
                    <h3>Chat Rápido</h3>
                    <input type="text" id="em" placeholder="Tu nombre">
                    <input type="text" id="re" placeholder="Para quien">
                    <input type="text" id="me" placeholder="Mensaje">
                    <button class="btn" style="background:#5d5d5d;" onclick="env()">Enviar</button>
                </div>
                <button class="btn" style="background:#bbb;" onclick="location.href='/api/usuarios/ver'">👥 Ver todos los usuarios</button>
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
    hora_actual = datetime.now().strftime("%H:%M")
    usuarios[nombre] = {
        "edad": edad, 
        "ubicacion": ubicacion, 
        "chats": [], 
        "ultima_conexion": hora_actual
    }
    return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✅ Registrado a las {hora_actual}</h2><a href='/' class='btn'>Volver</a></div></body></html>")

@app.get("/api/chatear")
async def chatear(emisor: str, receptor: str, mensaje: str):
    hora_envio = datetime.now().strftime("%H:%M")
    if receptor in usuarios:
        usuarios[receptor]["chats"].append({"de": emisor, "msg": mensaje, "hora": hora_envio})
        usuarios[receptor]["ultima_conexion"] = hora_envio
        return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✉️ Enviado</h2><a href='/' class='btn'>Volver</a></div></body></html>")
    return "Error: Usuario no encontrado."

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver_usuarios(region: str = None):
    cartas = ""
    for nombre, datos in usuarios.items():
        # Filtro de región
        if region and region.lower() not in datos['ubicacion'].lower():
            continue
            
        burbujas = "".join([f"<div class='mensaje'><b>{c['de']}:</b> {c['msg']}<span class='hora'>{c['hora']}</span></div>" for c in datos['chats']])
        
        cartas += f"""
        <div class="card">
            <div class="profile-header">
                <div class="avatar">👤</div>
                <div>
                    <h2>{nombre}</h2>
                    <span class="status">● Conectado: {datos['ultima_conexion']}</span>
                </div>
            </div>
            <span class="tag">📍 {datos['ubicacion']}</span> <span class="tag">🎂 {datos['edad']} años</span>
            <div class="chat-box">
                <strong>Muro de Mensajes:</strong>
                {burbujas if burbujas else "<p style='font-size:0.8em; color:#bbb;'>Sin mensajes.</p>"}
            </div>
        </div>
        """
    
    titulo = f"Resultados en {region}" if region else "Comunidad Global"
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div class='container'><h1>{titulo}</h1>{cartas if cartas else 'No se encontraron usuarios.'}<a href='/' class='btn' style='background:#bbb;'>Volver</a></div></body></html>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
