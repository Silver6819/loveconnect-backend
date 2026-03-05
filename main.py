import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

usuarios_db = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("video_url", sqlalchemy.String),
    sqlalchemy.Column("verificado", sqlalchemy.Boolean, default=False)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; padding: 20px; text-align: center; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 20px; }
    .btn-main { background: #ff4b6e; color: white; border: none; padding: 15px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; text-decoration: none; display: block; }
    .btn-borrar { background: #ff99aa; color: white; padding: 10px; border-radius: 10px; text-decoration: none; display: inline-block; margin-top: 50px; font-size: 0.8em; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>💖 LoveConnect</h1><div class='card'><h3>Registro</h3><input type='text' id='n' placeholder='Nombre'><br><br><button class='btn-main' onclick='enviar()'>Publicar</button></div><a href='/api/usuarios/ver'>Ir a la Comunidad 🌍</a><script>async function enviar() {{ const d={{nombre:document.getElementById('n').value, ubicacion:'Zacatecoluca', video_url:'', quien_soy:''}}; await fetch('/api/registrar', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(d)}}); location.href='/api/usuarios/ver'; }}</script></body></html>"

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver():
    try:
        users = await database.fetch_all(usuarios_db.select())
        if not users:
            return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>👥 Comunidad</h1><div class='card'><p>⚠️ No hay registro de perfiles aún.</p></div><a href='/' class='btn-main'>Registrar el primero</a></body></html>"
        
        cartas = ""
        for u in users:
            cartas += f"<div class='card'><strong>{u.nombre}</strong><br><small>📍 {u.ubicacion}</small></div>"
        
        return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>👥 Comunidad</h1>{cartas}<br><a href='/'>⬅️ Volver</a><br><a href='/api/limpiar' class='btn-borrar'>Limpiar Base de Datos</a></body></html>"
    except Exception as e:
        return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>Ocurrió un error</h1><p>La base de datos necesita actualizarse.</p><a href='/api/limpiar' class='btn-main'>Haz clic aquí para arreglarlo</a></body></html>"

@app.post("/api/registrar")
async def registrar(data: dict):
    await database.execute(usuarios_db.insert().values(nombre=data['nombre'], ubicacion=data['ubicacion'], quien_soy=data['quien_soy'], video_url=data['video_url'], verificado=False))

@app.get("/api/limpiar")
async def limpiar():
    try:
        await database.execute(usuarios_db.delete())
    except:
        pass
    return HTMLResponse("<script>alert('Base de datos reseteada'); location.href='/';</script>")
