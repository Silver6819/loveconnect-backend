import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# 1. Configuración de la Base de Datos Profesional
DATABASE_URL = os.environ.get("DATABASE_URL")
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Definimos la tabla de usuarios con todo lo que pediste (Horas, Región, Mensajes)
usuarios_db = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String, unique=True),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String),
    sqlalchemy.Column("chats_json", sqlalchemy.Text, default="[]") # Guardamos los chats como texto
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()
sesion_activa = False

ESTILOS = """
<style>
    body { font-family: 'Roboto', sans-serif; background: #fdf2f4; color: #444; margin: 0; padding: 10px; }
    .container { max-width: 500px; margin: auto; }
    .card { background: white; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #fce4ec; }
    .locked { opacity: 0.5; pointer-events: none; }
    h1 { color: #ff4b6e; text-align: center; }
    .btn { display: block; width: 100%; padding: 12px; background: #ff4b6e; color: white; border-radius: 12px; font-weight: bold; text-align: center; border: none; cursor: pointer; text-decoration: none; margin-top: 10px; }
    input { width: 100%; padding: 12px; margin: 5px 0; border: 1px solid #eee; border-radius: 10px; box-sizing: border-box; }
    .avatar { width: 50px; height: 50px; background: #eee; border-radius: 50%; display: inline-block; vertical-align: middle; margin-right: 10px; }
    .status { color: #4caf50; font-size: 0.8em; font-weight: bold; }
</style>
"""

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def inicio():
    global sesion_activa
    clase_bloqueo = "" if sesion_activa else "locked"
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div class="container">
                <h1>💖 LoveConnect Pro</h1>
                <div class="card">
                    <h3>Registrar Perfil</h3>
                    <input type="text" id="n" placeholder="Nombre completo">
                    <input type="number" id="e" placeholder="Edad">
                    <input type="text" id="u" placeholder="Ciudad (Región)">
                    <button class="btn" onclick="reg()">Crear mi Perfil</button>
                </div>
                <div class="{clase_bloqueo}">
                    <div class="card">
                        <h3>🔍 Buscar en Región</h3>
                        <input type="text" id="busq" placeholder="Ej: Santa Rosa">
                        <button class="btn" style="background:#5c6bc0;" onclick="location.href='/api/usuarios/ver?region='+document.getElementById('busq').value">Buscar Ahora</button>
                    </div>
                    <button class="btn" style="background:#bbb;" onclick="location.href='/api/usuarios/ver'">👥 Ver Comunidad</button>
                </div>
            </div>
            <script>
                function reg() {{
                    const n=document.getElementById('n').value, e=document.getElementById('e').value, u=document.getElementById('u').value;
                    if(n && e && u) location.href=`/api/registrar?nombre=${{encodeURIComponent(n)}}&edad=${{e}}&ubicacion=${{encodeURIComponent(u)}}`;
                }}
            </script>
        </body>
    </html>
    """

@app.get("/api/registrar")
async def registrar(nombre: str, edad: int, ubicacion: str):
    global sesion_activa
    hora = datetime.now().strftime("%H:%M")
    query = usuarios_db.insert().values(nombre=nombre, edad=edad, ubicacion=ubicacion, ultima_conexion=hora, chats_json="[]")
    try:
        await database.execute(query)
        sesion_activa = True
        return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✅ Guardado en la Nube</h2><a href='/' class='btn'>Entrar</a></div></body></html>")
    except:
        return "Error: El nombre ya existe o hay un problema con la base de datos."

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver_usuarios(region: str = None):
    query = usuarios_db.select()
    rows = await database.fetch_all(query)
    
    cartas = ""
    for row in rows:
        if region and region.lower() not in row['ubicacion'].lower(): continue
        
        cartas += f"""
        <div class="card">
            <div style="display:flex; align-items:center;">
                <div class="avatar" style="background: url('https://ui-avatars.com/api/?name={row['nombre']}&background=ff4b6e&color=fff'); background-size: cover;"></div>
                <div>
                    <h2>{row['nombre']}</h2>
                    <small>📍 {row['ubicacion']} | 🎂 {row['edad']} años</small><br>
                    <span class="status">● Conectado: {row['ultima_conexion']}</span>
                </div>
            </div>
        </div>"""
    
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div class='container'><h1>Comunidad</h1>{cartas if cartas else 'No hay resultados.'}<a href='/' class='btn'>Volver</a></div></body></html>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
