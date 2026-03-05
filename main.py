import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

# --- BASE DE DATOS ---
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
    sqlalchemy.Column("video_url", sqlalchemy.String, default=""),
    sqlalchemy.Column("verificado", sqlalchemy.Boolean, default=False)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; color: #333; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 5px 15px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #ffeef2; }
    .btn-main { background: #ff4b6e; color: white; border: none; padding: 15px; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; font-size: 1em; }
    .check-azul { color: #00a2ff; font-size: 1.1em; margin-left: 5px; }
    .btn-video { background: #ff4b6e; color: white; padding: 10px 20px; border-radius: 20px; text-decoration: none; display: inline-block; font-weight: bold; margin-top: 10px; }
    .modal { display: none; position: fixed; top: 5%; left: 5%; width: 90%; background: white; border-radius: 25px; padding: 20px; box-shadow: 0 10px 50px rgba(0,0,0,0.4); z-index: 100; border: 2px solid gold; box-sizing: border-box; max-height: 90vh; overflow-y: auto; }
    input, textarea { width: 100%; padding: 12px; margin: 5px 0; border-radius: 10px; border: 1px solid #ddd; box-sizing: border-box; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    num = "50378641712"
    link_v = f"https://wa.me/{num}?text=Hola%20Silver%20Breaker,%20envio%20mi%20foto%20para%20verificar%20mi%20perfil."
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div style="text-align:right;"><button onclick="document.getElementById('m').style.display='block'" style="background:gold; border:none; padding:12px; border-radius:50%; font-size:1.3em; cursor:pointer;">👑</button></div>
            <h1 style="color:#ff4b6e; margin-top:0;">💖 LoveConnect</h1>
            
            <div id="m" class="modal">
                <h2 style="margin:0;">🌟 Servicios VIP</h2>
                <a href="https://www.paypal.com/paypalme/silver676" target="_blank" style="background:#0070ba; color:white; padding:15px; border-radius:12px; display:block; text-decoration:none; margin-bottom:10px; font-weight:bold;">Pagar Membresía (PayPal)</a>
                <a href="{link_v}" target="_blank" style="background:#00a2ff; color:white; padding:15px; border-radius:12px; display:block; text-decoration:none; font-weight:bold;">🛡️ Solicitar Verificación ✅</a>
                <button onclick="document.getElementById('m').style.display='none'" style="background:#eee; border:none; padding:10px; width:100%; border-radius:10px; margin-top:15px;">Cerrar</button>
            </div>

            <div class="card">
                <h3>Registro de Usuario</h3>
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="text" id="u" placeholder="Zacatecoluca, La Paz">
                <input type="text" id="v" placeholder="Link de tu Video (YouTube/Drive)">
                <textarea id="q" placeholder="Cuéntanos sobre ti..."></textarea>
                <button class="btn-main" onclick="enviar()">🚀 Publicar Perfil</button>
            </div>
            
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">Explorar la Comunidad 🌍</a>

            <script>
                async function enviar() {{
                    const data = {{ 
                        nombre: document.getElementById('n').value, 
                        ubicacion: document.getElementById('u').value, 
                        video_url: document.getElementById('v').value,
                        quien_soy: document.getElementById('q').value 
                    }};
                    if(!data.nombre) return alert("Escribe tu nombre");
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
        # Si tiene video, mostramos el botón. Si está verificado, ponemos el check.
        check = '<span class="check-azul">✅</span>' if u.verificado else ""
        btn_v = f'<a href="{u.video_url}" target="_blank" class="btn-video">▶️ Ver Video de 10 min</a>' if u.video_url else ""
        
        cartas += f'''
        <div class="card" style="text-align:left;">
            <strong>{u.nombre} {check}</strong><br>
            <small style="color:#ff4b6e; font-weight:bold;">📍 {u.ubicacion}</small>
            <p style="color:#555; margin-top:10px;">{u.quien_soy}</p>
            {btn_v}
        </div>'''
    
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
    <body><h1>👥 Comunidad de Zacatecoluca</h1>{cartas or '<p>No hay perfiles.</p>'}
    <br><a href="/" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">⬅️ Regresar</a></body></html>
    """

@app.post("/api/registrar")
async def registrar(data: dict):
    await database.execute(usuarios_db.insert().values(
        nombre=data['nombre'], 
        ubicacion=data['ubicacion'], 
        video_url=data.get('video_url', ''),
        quien_soy=data['quien_soy'],
        verificado=False # Por defecto no están verificados hasta que tú los apruebes
    ))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
