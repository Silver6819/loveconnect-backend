import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

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
    sqlalchemy.Column("super_likes", sqlalchemy.Integer, default=0),
    sqlalchemy.Column("es_premium", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("video_url", sqlalchemy.Text)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()

# --- TRADUCCIÓN RÁPIDA ---
def traducir(request: Request):
    # Detecta el idioma del navegador
    lang = request.headers.get("accept-language", "es")
    if "en" in lang.lower():
        return {
            "titulo": "Community",
            "ver_mas": "View Full Profile",
            "volver": "Back",
            "vacio": "No profiles yet."
        }
    else:
        return {
            "titulo": "Comunidad Real",
            "ver_mas": "Ver perfil completo",
            "volver": "Volver al inicio",
            "vacio": "Aún no hay perfiles."
        }

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #ffeef2; position: relative; }
    .btn-detalles { 
        display: inline-block; 
        margin-top: 10px; 
        color: #ff4b6e; 
        font-weight: bold; 
        text-decoration: none; 
        border: 2px solid #ff4b6e; 
        padding: 8px 15px; 
        border-radius: 20px; 
        transition: 0.3s;
    }
    .btn-detalles:hover { background: #ff4b6e; color: white; }
    .info-user { text-align: left; margin-bottom: 10px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    # Mantenemos tu formulario de registro igual para que no falle
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1 style="color:#ff4b6e;">💖 LoveConnect</h1>
            <div class="card">
                <h3>Crear tu Perfil</h3>
                <input type="text" id="n" placeholder="Tu Nombre" style="width:100%; padding:10px; margin:5px 0;">
                <input type="text" id="u" placeholder="Zacatecoluca" style="width:100%; padding:10px; margin:5px 0;">
                <textarea id="q" placeholder="Sobre mí..." style="width:100%; padding:10px; margin:5px 0;"></textarea>
                <button onclick="enviar()" style="background:#ff4b6e; color:white; border:none; padding:15px; border-radius:10px; width:100%; font-weight:bold;">Publicar</button>
            </div>
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold;">Explorar Comunidad 🌍</a>
            <script>
                async function enviar() {{
                    const data = {{ nombre: document.getElementById('n').value, ubicacion: document.getElementById('u').value, quien_soy: document.getElementById('q').value }};
                    await fetch('/api/registrar', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(data) }});
                    location.href = '/api/usuarios/ver';
                }}
            </script>
        </body>
    </html>
    """

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver(request: Request):
    t = traducir(request)
    users = await database.fetch_all(usuarios_db.select())
    cartas = ""
    for u in users:
        # Aquí cambiamos el "See More" por la variable traducida
        cartas += f'''
        <div class="card">
            <div class="info-user">
                <strong style="font-size:1.2em; color:#333;">{u.nombre}</strong><br>
                <small style="color:#ff4b6e; font-weight:bold;">📍 {u.ubicacion}</small>
                <p style="color:#666; font-size:0.95em; margin-top:8px;">{u.quien_soy}</p>
            </div>
            <a href="#" class="btn-detalles">{t['ver_mas']}</a>
        </div>'''
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1 style="color:#ff4b6e;">👥 {t['titulo']}</h1>
            {cartas or f'<p style="color:#999;">{t["vacio"]}</p>'}
            <br>
            <a href="/" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">⬅️ {t['volver']}</a>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: dict):
    await database.execute(usuarios_db.insert().values(
        nombre=data['nombre'], edad=25, ubicacion=data['ubicacion'], 
        quien_soy=data['quien_soy']
    ))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
