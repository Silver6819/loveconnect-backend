import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# --- CONEXIÓN ---
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
    sqlalchemy.Column("es_premium", sqlalchemy.Boolean, default=False)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #ffeef2; }
    .btn-main { background: #ff4b6e; color: white; border: none; padding: 15px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; }
    .btn-see-more { color: #ff4b6e; font-weight: bold; text-decoration: none; font-size: 0.9em; display: inline-block; margin-top: 10px; cursor: pointer; border: 1px solid #ff4b6e; padding: 5px 15px; border-radius: 15px; }
    .btn-see-more:hover { background: #ff4b6e; color: white; }
    input, textarea { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #eee; border-radius: 10px; box-sizing: border-box; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1 style="color:#ff4b6e;">💖 LoveConnect</h1>
            <div class="card">
                <h3>Crear tu Perfil</h3>
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="text" id="u" placeholder="Zacatecoluca, El Salvador">
                <textarea id="q" placeholder="Cuéntanos un poco sobre ti..."></textarea>
                <button class="btn-main" onclick="enviar()">🚀 Publicar Perfil</button>
            </div>
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">Explorar Comunidad 🌍</a>
            <br>
            <button onclick="limpiar()" style="background:none; border:none; color:#ccc; margin-top:20px; cursor:pointer;">Limpiar registros anteriores</button>

            <script>
                async function enviar() {{
                    const data = {{ 
                        nombre: document.getElementById('n').value, 
                        ubicacion: document.getElementById('u').value, 
                        quien_soy: document.getElementById('q').value 
                    }};
                    if(!data.nombre) return alert("Escribe tu nombre");
                    await fetch('/api/registrar', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(data) }});
                    location.href = '/api/usuarios/ver';
                }}
                async function limpiar() {{
                    if(confirm("¿Borrar todos los perfiles de prueba?")) {{
                        await fetch('/api/limpiar', {{ method: 'POST' }});
                        location.reload();
                    }}
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
        # Aquí cambiamos "See More" por "Ver Detalles"
        cartas += f'''
        <div class="card">
            <div style="text-align:left;">
                <strong style="font-size:1.2em;">{u.nombre}</strong><br>
                <small style="color:#ff4b6e;">📍 {u.ubicacion}</small>
                <p style="margin-top:10px; color:#555;">{u.quien_soy[:100]}...</p>
                <div class="btn-see-more">Ver Perfil Completo</div>
            </div>
        </div>'''
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>👥 Comunidad de Zacatecoluca</h1>
            {cartas or '<p style="color:#999;">Aún no hay perfiles registrados.</p>'}
            <br><a href="/" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">⬅️ Volver a Registro</a>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: dict):
    await database.execute(usuarios_db.insert().values(
        nombre=data['nombre'], 
        edad=25, 
        ubicacion=data['ubicacion'], 
        quien_soy=data['quien_soy']
    ))

@app.post("/api/limpiar")
async def limpiar_db():
    await database.execute(usuarios_db.delete())
    return {{"status": "ok"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
