import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

# --- CONFIGURACIÓN DE BASE DE DATOS ---
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
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("corazones", sqlalchemy.Integer, default=0),
    sqlalchemy.Column("super_likes", sqlalchemy.Integer, default=0), # NUEVO: Likes especiales
    sqlalchemy.Column("es_premium", sqlalchemy.Boolean, default=False), # NUEVO: Estado VIP
    sqlalchemy.Column("video_url", sqlalchemy.Text),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    # Actualización automática de columnas para pagos
    try:
        await database.execute("ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS es_premium BOOLEAN DEFAULT FALSE;")
        await database.execute("ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS super_likes INTEGER DEFAULT 0;")
    except: pass

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fdf2f4; margin: 0; padding: 10px; text-align: center; }
    .card { background: white; border-radius: 20px; padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; position: relative; }
    .premium-tag { background: gold; color: #333; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 0.8em; }
    .btn-pay { background: #0070ba; color: white; padding: 10px; border-radius: 10px; text-decoration: none; display: block; margin: 5px 0; font-weight: bold; }
    .btn-chivo { background: #161616; color: #00ffcc; padding: 10px; border-radius: 10px; text-decoration: none; display: block; margin: 5px 0; font-weight: bold; border: 1px solid #00ffcc; }
    .diamond-btn { background: #e3f2fd; border: 2px solid #2196f3; color: #2196f3; padding: 5px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; }
    .modal-pago { display: none; position: fixed; top: 10%; left: 5%; width: 90%; background: white; border-radius: 20px; padding: 20px; box-shadow: 0 0 50px rgba(0,0,0,0.5); z-index: 1000; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div style="display:flex; justify-content: space-between; align-items: center;">
                <h1 style="color:#ff4b6e;">💖 LoveConnect</h1>
                <button onclick="abrirTienda()" style="background:gold; border:none; padding:10px; border-radius:50%; cursor:pointer;">💎</button>
            </div>

            <div id="tienda" class="modal-pago">
                <h2>👑 Hazte Premium</h2>
                <p>Un solo pago para acceso total y 3 Diamantes Especiales.</p>
                <a href="#" class="btn-pay">🔵 Pagar con PayPal</a>
                <a href="#" class="btn-chivo">₿ Pagar con Chivo / Bitcoin</a>
                <button onclick="cerrarTienda()" class="btn" style="background:#bbb;">Cerrar</button>
            </div>

            <div class="card">
                <h3>Crear Perfil</h3>
                <input type="text" id="n" placeholder="Nombre">
                <input type="text" id="u" placeholder="Ubicación (Zacatecoluca)">
                <textarea id="q" placeholder="Sobre mí..."></textarea>
                <button class="btn" onclick="enviar()">Publicar</button>
            </div>
            
            <a href="/api/usuarios/ver">Ver Comunidad</a>

            <script>
                function abrirTienda() {{ document.getElementById('tienda').style.display = "block"; }}
                function cerrarTienda() {{ document.getElementById('tienda').style.display = "none"; }}
                // ... (funciones de envío de datos) ...
            </script>
        </body>
    </html>
    """

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver():
    users = await database.fetch_all(usuarios_db.select())
    cartas = ""
    for u in users:
        vip = '<span class="premium-tag">VIP 👑</span>' if u.es_premium else ""
        cartas += f'''
        <div class="card">
            {vip}
            <strong style="font-size:1.2em;">{u.nombre}</strong><br>
            <p>{u.quien_soy}</p>
            <div style="display:flex; gap:10px; justify-content:center;">
                <button class="heart-btn" onclick="like({u.id})">❤️ {u.corazones}</button>
                <button class="diamond-btn" onclick="superLike({u.id})">💎 {u.super_likes}</button>
            </div>
        </div>'''
    return f"<html><head>{ESTILOS}</head><body><h1>Comunidad</h1>{cartas}<br><a href='/'>Volver</a></body></html>"

# --- LÓGICA DE API ---
@app.post("/api/usuarios/superlike/{{u_id}}")
async def superlike(u_id: int):
    # Aquí iría la lógica para restar de los 3 disponibles del comprador
    await database.execute(f"UPDATE usuarios_loveconnect SET super_likes = super_likes + 1 WHERE id = {u_id}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
