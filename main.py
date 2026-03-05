import os
import uvicorn
import databases
import sqlalchemy
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# 1. Configuración de Base de Datos
DATABASE_URL = os.environ.get("DATABASE_URL")
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

usuarios_db = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String, unique=True),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("foto_url", sqlalchemy.String, default="https://via.placeholder.com/150"),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String),
    sqlalchemy.Column("es_premium", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("chats_json", sqlalchemy.Text, default="[]")
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
    .avatar-real { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #ff4b6e; }
    .btn { display: block; width: 100%; padding: 12px; background: #ff4b6e; color: white; border-radius: 12px; font-weight: bold; text-align: center; border: none; cursor: pointer; text-decoration: none; margin-top: 10px; }
    .btn-premium { background: linear-gradient(45deg, #ffd700, #ffa500); color: #000; }
    input { width: 100%; padding: 12px; margin: 5px 0; border: 1px solid #eee; border-radius: 10px; box-sizing: border-box; }
    .badge { background: gold; font-size: 0.7em; padding: 2px 5px; border-radius: 5px; font-weight: bold; }
</style>
"""

@app.on_event("startup")
async def startup(): await database.connect()

@app.on_event("shutdown")
async def shutdown(): await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div class="container">
                <h1>💖 LoveConnect Pro</h1>
                <div class="card">
                    <h3>Registro con Foto</h3>
                    <input type="text" id="n" placeholder="Nombre completo">
                    <input type="number" id="e" placeholder="Edad">
                    <input type="text" id="u" placeholder="Ciudad">
                    <input type="text" id="f" placeholder="Link de tu foto real (URL)">
                    <button class="btn" onclick="reg()">Crear Perfil Verificado</button>
                </div>
                <button class="btn" style="background:#bbb;" onclick="location.href='/api/usuarios/ver'">👥 Ver Comunidad</button>
            </div>
            <script>
                function reg() {{
                    const n=document.getElementById('n').value, e=document.getElementById('e').value, 
                          u=document.getElementById('u').value, f=document.getElementById('f').value;
                    if(n && e && u) location.href=`/api/registrar?nombre=${{encodeURIComponent(n)}}&edad=${{e}}&ubicacion=${{encodeURIComponent(u)}}&foto=${{encodeURIComponent(f)}}`;
                }}
            </script>
        </body>
    </html>
    """

@app.get("/api/registrar")
async def registrar(nombre: str, edad: int, ubicacion: str, foto: str = None):
    global sesion_activa
    hora = datetime.now().strftime("%H:%M")
    foto_final = foto if (foto and foto.strip() != "") else f"https://ui-avatars.com/api/?name={nombre}&background=ff4b6e&color=fff"
    query = usuarios_db.insert().values(nombre=nombre, edad=edad, ubicacion=ubicacion, foto_url=foto_final, ultima_conexion=hora)
    try:
        await database.execute(query)
        sesion_activa = True
        return HTMLResponse(f"<html><head>{ESTILOS}</head><body style='text-align:center;'><div class='card'><h2>✅ Perfil Creado</h2><a href='/' class='btn'>Ir al Inicio</a></div></body></html>")
    except: return "Error: El usuario ya existe."

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver_usuarios():
    query = usuarios_db.select()
    rows = await database.fetch_all(query)
    cartas = ""
    for row in rows:
        premium_tag = "<span class='badge'>PREMIUM ⭐</span>" if row['es_premium'] else ""
        cartas += f"""
        <div class="card">
            <div style="display:flex; align-items:center; gap:15px;">
                <img src="{row['foto_url']}" class="avatar-real">
                <div>
                    <h2>{row['nombre']} {premium_tag}</h2>
                    <small>📍 {row['ubicacion']} | 🎂 {row['edad']} años</small><br>
                    <small style="color:green;">● Activo: {row['ultima_conexion']}</small>
                </div>
            </div>
            <button class="btn btn-premium" onclick="alert('Redirigiendo a Pago seguro...')">💎 Hacerse Premium</button>
        </div>"""
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div class='container'><h1>Comunidad</h1>{cartas}<a href='/' class='btn' style='background:#bbb;'>Volver</a></div></body></html>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
