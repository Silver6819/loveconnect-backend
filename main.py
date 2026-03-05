import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# --- CONEXIÓN A BASE DE DATOS ---
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
    sqlalchemy.Column("super_likes", sqlalchemy.Integer, default=0),
    sqlalchemy.Column("es_premium", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("video_url", sqlalchemy.Text),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    # Forzar creación de columnas si no existen
    try:
        await database.execute("ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS es_premium BOOLEAN DEFAULT FALSE;")
        await database.execute("ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS super_likes INTEGER DEFAULT 0;")
        await database.execute("ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS video_url TEXT;")
    except: pass

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #ffeef2; position: relative; }
    .btn-main { background: #ff4b6e; color: white; border: none; padding: 15px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1.1em; }
    .modal-pago { display: none; position: fixed; top: 10%; left: 5%; width: 90%; background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 50px rgba(0,0,0,0.4); z-index: 1000; border: 3px solid gold; box-sizing: border-box; }
    .btn-pay { background: #0070ba; color: white; padding: 15px; border-radius: 12px; text-decoration: none; display: block; margin: 10px 0; font-weight: bold; }
    .btn-chivo { background: #161616; color: #00ffcc; padding: 15px; border-radius: 12px; text-decoration: none; display: block; margin: 10px 0; font-weight: bold; border: 2px solid #00ffcc; }
    .premium-badge { background: gold; color: #000; padding: 5px 12px; border-radius: 15px; font-weight: bold; font-size: 0.8em; position: absolute; top: 15px; left: 15px; }
    input, textarea { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #eee; border-radius: 10px; box-sizing: border-box; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div style="display:flex; justify-content: space-between; align-items: center; padding: 10px;">
                <h1 style="color:#ff4b6e; margin:0;">💖 LoveConnect</h1>
                <button onclick="document.getElementById('tienda').style.display='block'" style="background:gold; border:none; padding:10px; border-radius:50%; font-size:1.2em; cursor:pointer;">💎</button>
            </div>

            <div id="tienda" class="modal-pago">
                <h2 style="margin-top:0;">👑 Hazte Premium</h2>
                <p>Pago único para acceso total y 3 Diamantes Especiales.</p>
                <a href="https://www.paypal.me" class="btn-pay">🔵 Pagar con PayPal</a>
                <a href="https://chivowallet.com" class="btn-chivo">₿ Pagar con Chivo / Bitcoin</a>
                <button onclick="document.getElementById('tienda').style.display='none'" style="background:#eee; border:none; padding:10px; border-radius:10px; width:100%; margin-top:10px; cursor:pointer;">Cerrar</button>
            </div>

            <div class="card">
                <h3>Crear tu Perfil</h3>
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="number" id="e" placeholder="Edad">
                <input type="text" id="u" placeholder="Ubicación (Zacatecoluca)">
                <textarea id="q" placeholder="Cuéntanos sobre ti..."></textarea>
                <button class="btn-main" onclick="enviar()">🚀 Publicar Perfil</button>
            </div>
            
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">Ver Comunidad 🌍</a>

            <script>
                async function enviar() {{
                    const data = {{
                        nombre: document.getElementById('n').value,
                        edad: parseInt(document.getElementById('e').value),
                        ubicacion: document.getElementById('u').value,
                        quien_soy: document.getElementById('q').value
                    }};
                    if(!data.nombre) return alert("Por favor escribe tu nombre");
                    await fetch('/api/registrar', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    location.href = '/api/usuarios/ver';
                }}
            </script>
        </body>
    </html>
    """

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver():
    users = await database.fetch_all(usuarios_db.select())
    cartas = ""
    for u in users:
        vip = '<span class="premium-badge">PREMIUM 👑</span>' if u.es_premium else ""
        cartas += f'''
        <div class="card">
            {vip}
            <div style="text-align:left;">
                <strong style="font-size:1.3em;">{u.nombre} ({u.edad})</strong><br>
                <small style="color:#ff4b6e;">📍 {u.ubicacion}</small>
                <p style="background:#f9fafb; padding:15px; border-radius:12px; margin-top:10px; border-left:4px solid #ff4b6e;">{u.quien_soy}</p>
            </div>
            <div style="display:flex; gap:10px; justify-content:center;">
                <button style="background:#f0f7ff; border:2px solid #2196f3; color:#2196f3; padding:8px 15px; border-radius:20px; font-weight:bold;">💎 {u.super_likes}</button>
                <button style="background:#fff0f3; border:2px solid #ff4b6e; color:#ff4b6e; padding:8px 15px; border-radius:20px; font-weight:bold;">❤️ {u.corazones}</button>
            </div>
        </div>'''
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>👥 Comunidad Real</h1>
            {cartas or '<p style="color:#999;">No hay perfiles registrados aún.</p>'}
            <br><a href="/" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">⬅️ Volver a Registro</a>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: dict):
    await database.execute(usuarios_db.insert().values(
        nombre=data['nombre'], edad=data['edad'], ubicacion=data['ubicacion'], 
        quien_soy=data['quien_soy'], corazones=0, super_likes=0,
        ultima_conexion=datetime.now().strftime("%H:%M")
    ))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
