import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()
usuarios = {}
# Esta variable controlará si hay alguien logueado en la sesión actual
sesion_activa = False 

ESTILOS = """
<style>
    body { font-family: 'Roboto', sans-serif; background: #fdf2f4; color: #444; margin: 0; padding: 10px; }
    .container { max-width: 500px; margin: auto; }
    .card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #fce4ec; }
    .locked { opacity: 0.5; pointer-events: none; user-select: none; }
    .lock-msg { color: #ff4b6e; font-size: 0.8em; font-weight: bold; margin-bottom: 10px; display: block; }
    h1 { color: #ff4b6e; text-align: center; }
    .btn { display: block; width: 100%; padding: 12px; background: #ff4b6e; color: white; border-radius: 12px; font-weight: bold; text-align: center; border: none; cursor: pointer; text-decoration: none; margin-top: 10px; }
    .btn-search { background: #5c6bc0; }
    input { width: 100%; padding: 12px; margin: 5px 0; border: 1px solid #eee; border-radius: 10px; box-sizing: border-box; }
    .avatar { width: 50px; height: 50px; background: #eee; border-radius: 50%; display: inline-block; vertical-align: middle; margin-right: 10px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    global sesion_activa
    # Si no hay sesión, aplicamos la clase 'locked' a las funciones avanzadas
    clase_bloqueo = "" if sesion_activa else "locked"
    mensaje_alerta = "" if sesion_activa else "<span class='lock-msg'>🔒 Regístrate para desbloquear la búsqueda</span>"
    
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
                    <input type="text" id="u" placeholder="Tu Ciudad">
                    <button class="btn" onclick="reg()">Crear mi Perfil</button>
                </div>

                <div class="card {clase_bloqueo}">
                    <h3>Buscador por Región</h3>
                    {mensaje_alerta}
                    <input type="text" id="busq" placeholder="Escribe una ciudad...">
                    <button class="btn btn-search" onclick="buscar()">🔍 Buscar en mi región</button>
                </div>

                <div class="card {clase_bloqueo}">
                    <h3>Chat Rápido</h3>
                    {mensaje_alerta}
                    <input type="text" id="em" placeholder="Tu nombre">
                    <input type="text" id="re" placeholder="Para quien">
                    <input type="text" id="me" placeholder="Mensaje">
                    <button class="btn" style="background:#5d5d5d;" onclick="env()">Enviar</button>
                </div>
                
                <button class="btn {clase_bloqueo}" style="background:#bbb;" onclick="location.href='/api/usuarios/ver'">👥 Ver Comunidad</button>
            </div>
            <script>
                function reg() {{
                    const n=document.getElementById('n').value, e=document.getElementById('e').value, u=document.getElementById('u').value;
                    if(n && e && u) location.href=`/api/registrar?nombre=${{encodeURIComponent(n)}}&edad=${{e}}&ubicacion=${{encodeURIComponent(u)}}`;
                }}
                function buscar() {{
                    const b = document.getElementById('busq').value;
                    location.href='/api/usuarios/ver?region='+encodeURIComponent(b);
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
    global sesion_activa
    hora = datetime.now().strftime("%H:%M")
    usuarios[nombre] = {"edad": edad, "ubicacion": ubicacion, "chats": [], "online": hora}
    sesion_activa = True # ¡Desbloqueado!
    return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✅ Perfil Creado</h2><p>Ya puedes buscar y chatear.</p><a href='/' class='btn'>Entrar a LoveConnect</a></div></body></html>")

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver_usuarios(region: str = None):
    if not sesion_activa:
        return "Acceso denegado. Regístrate primero."
    
    cartas = ""
    for nombre, datos in usuarios.items():
        if region and region.lower() not in datos['ubicacion'].lower(): continue
        
        burbujas = "".join([f"<div style='background:#f9f9f9; padding:5px; margin-top:5px; border-radius:5px; font-size:0.8em;'><b>{c['de']}:</b> {c['msg']} <small style='color:#999;'>{c['hora']}</small></div>" for c in datos['chats']])
        
        cartas += f"""
        <div class="card">
            <div style="display:flex; align-items:center;">
                <div class="avatar" style="background: url('https://ui-avatars.com/api/?name={nombre}&background=ff4b6e&color=fff'); background-size: cover;"></div>
                <div>
                    <h2>{nombre}</h2>
                    <small>📍 {datos['ubicacion']} | 🎂 {datos['edad']} años</small><br>
                    <small style="color:green;">● Activo: {datos['online']}</small>
                </div>
            </div>
            <div style="margin-top:10px; border-top:1px solid #eee; padding-top:10px;">
                {burbujas if burbujas else '<small>No hay mensajes</small>'}
            </div>
        </div>"""
    
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div class='container'><h1>Resultados</h1>{cartas}<a href='/' class='btn'>Volver</a></div></body></html>"

@app.get("/api/chatear")
async def chatear(emisor: str, receptor: str, mensaje: str):
    if receptor in usuarios:
        hora = datetime.now().strftime("%H:%M")
        usuarios[receptor]["chats"].append({"de": emisor, "msg": mensaje, "hora": hora})
        return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✉️ Enviado</h2><a href='/' class='btn'>Volver</a></div></body></html>")
    return "Usuario no encontrado."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
