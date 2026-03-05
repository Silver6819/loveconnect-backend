import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

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
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
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
    .btn-paypal { background: #0070ba; color: white; padding: 15px; border-radius: 12px; display: block; text-decoration: none; margin-bottom: 10px; font-weight: bold; }
    .btn-ver { color: #ff4b6e; font-weight: bold; text-decoration: none; border: 2px solid #ff4b6e; padding: 8px 15px; border-radius: 20px; display: inline-block; margin-top: 10px; }
    .modal { display: none; position: fixed; top: 15%; left: 5%; width: 90%; background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 50px rgba(0,0,0,0.4); z-index: 100; border: 2px solid gold; box-sizing: border-box; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div style="text-align:right;"><button onclick="document.getElementById('m').style.display='block'" style="background:gold; border:none; padding:10px; border-radius:50%; font-size:1.2em; cursor:pointer;">👑</button></div>
            <h1 style="color:#ff4b6e;">💖 LoveConnect</h1>
            
            <div id="m" class="modal">
                <h2 style="margin-top:0;">👑 Hazte Premium</h2>
                <p>Apoya la app y destaca tu perfil en Zacatecoluca.</p>
                <a href="https://www.paypal.com/paypalme/silver676" target="_blank" class="btn-paypal">Pagar con PayPal</a>
                <button onclick="document.getElementById('m').style.display='none'" style="background:#eee; border:none; padding:10px; width:100%; border-radius:10px;">Cerrar</button>
            </div>

            <div class="card">
                <h3>Crear tu Perfil</h3>
                <input type="text" id="n" placeholder="Nombre completo" style="width:100%; padding:12px; margin:5px 0; border-radius:10px; border:1px solid #ddd;">
                <input type="text" id="u" placeholder="Ubicación (Zacatecoluca)" style="width:100%; padding:12px; margin:5px 0; border-radius:10px; border:1px solid #ddd;">
                <textarea id="q" placeholder="Cuéntanos sobre ti..." style="width:100%; padding:12px; margin:5px 0; border-radius:10px; border:1px solid #ddd;"></textarea>
                <button class="btn-main" onclick="enviar()">🚀 Publicar en la Comunidad</button>
            </div>
            
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold; text-decoration:none; font-size:1.1em;">Ver Comunidad Real 🌍</a>

            <script>
                async function enviar() {{
                    const data = {{ nombre: document.getElementById('n').value, ubicacion: document.getElementById('u').value, quien_soy: document.getElementById('q').value }};
                    if(!data.nombre) return alert("Por favor escribe tu nombre");
                    await fetch('/api/registrar', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(data) }});
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
        cartas += f'''
        <div class="card" style="text-align:left;">
            <strong style="font-size:1.2em; color:#333;">{u.nombre}</strong><br>
            <small style="color:#ff4b6e;">📍 {u.ubicacion}</small>
            <p style="color:#666; margin-top:10px; border-left: 3px solid #ff4b6e; padding-left: 10px;">{u.quien_soy}</p>
            <a href="#" class="btn-ver">Ver perfil completo</a>
        </div>'''
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1 style="color:#ff4b6e;">👥 Comunidad Real</h1>
            {cartas or '<p style="color:#999;">Aún no hay perfiles. ¡Sé el primero!</p>'}
            <br><a href="/" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">⬅️ Volver al Registro</a>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: dict):
    await database.execute(usuarios_db.insert().values(
        nombre=data['nombre'], ubicacion=data['ubicacion'], quien_soy=data['quien_soy']
    ))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
