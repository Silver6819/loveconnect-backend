import os
import uvicorn
import databases
import sqlalchemy
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
    
    .modal { display: none; position: fixed; top: 5%; left: 5%; width: 90%; background: white; border-radius: 25px; padding: 20px; box-shadow: 0 10px 50px rgba(0,0,0,0.4); z-index: 100; border: 2px solid gold; box-sizing: border-box; max-height: 90vh; overflow-y: auto; }
    .btn-paypal { background: #0070ba; color: white; padding: 15px; border-radius: 12px; display: block; text-decoration: none; margin-bottom: 10px; font-weight: bold; }
    .seccion-chivo { background: #161616; color: #00ffcc; padding: 15px; border-radius: 15px; border: 1px solid #00ffcc; margin-top: 10px; }
    .btn-wsp { background: #25d366; color: white; padding: 15px; border-radius: 12px; display: block; text-decoration: none; margin-top: 15px; font-weight: bold; }
    
    .btn-ver { color: #ff4b6e; font-weight: bold; text-decoration: none; border: 2px solid #ff4b6e; padding: 8px 15px; border-radius: 20px; display: inline-block; margin-top: 10px; }
    input, textarea { width: 100%; padding: 12px; margin: 5px 0; border-radius: 10px; border: 1px solid #ddd; box-sizing: border-box; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    # DATOS DE CONTACTO ACTUALIZADOS
    mi_whatsapp = "50378641712" 
    mensaje = "Hola Silver Breaker, acabo de pagar mi membresía VIP en LoveConnect. Envío mi comprobante."
    link_wsp = f"https://wa.me/{mi_whatsapp}?text={mensaje.replace(' ', '%20')}"

    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <div style="text-align:right;"><button onclick="document.getElementById('m').style.display='block'" style="background:gold; border:none; padding:12px; border-radius:50%; font-size:1.3em; cursor:pointer;">👑</button></div>
            <h1 style="color:#ff4b6e; margin-top:0;">💖 LoveConnect</h1>
            
            <div id="m" class="modal">
                <h2 style="margin:0;">👑 Membresía VIP</h2>
                <p style="color:#666;">Destaca tu perfil en Zacatecoluca.</p>
                
                <a href="https://www.paypal.com/paypalme/silver676" target="_blank" class="btn-paypal">🔵 Pagar con PayPal</a>
                
                <div class="seccion-chivo">
                    <p style="margin:0;">⚡ Chivo Wallet / Bitcoin</p>
                    <div style="background:white; width:140px; height:140px; margin:10px auto; border-radius:10px; display:flex; align-items:center; justify-content:center;">
                        <span style="color:#333; font-size:0.8em;">(Pega tu QR aquí)</span>
                    </div>
                    <p style="margin:5px 0; font-weight:bold;">Usuario: @silver676</p>
                </div>

                <a href="{link_wsp}" target="_blank" class="btn-wsp">✅ Enviar Comprobante</a>

                <button onclick="document.getElementById('m').style.display='none'" style="background:#eee; border:none; padding:10px; width:100%; border-radius:10px; margin-top:15px; font-weight:bold;">Cerrar</button>
            </div>

            <div class="card">
                <h3>Crear tu Perfil</h3>
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="text" id="u" placeholder="Zacatecoluca, El Salvador">
                <textarea id="q" placeholder="Cuéntanos un poco sobre ti..."></textarea>
                <button class="btn-main" onclick="enviar()">🚀 Publicar Perfil</button>
            </div>
            
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">Explorar Comunidad 🌍</a>

            <script>
                async function enviar() {{
                    const data = {{ nombre: document.getElementById('n').value, ubicacion: document.getElementById('u').value, quien_soy: document.getElementById('q').value }};
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
        cartas += f'''
        <div class="card" style="text-align:left;">
            <strong>{u.nombre}</strong><br>
            <small style="color:#ff4b6e; font-weight:bold;">📍 {u.ubicacion}</small>
            <p style="color:#666; margin-top:10px; border-left:3px solid #ff4b6e; padding-left:10px;">{u.quien_soy}</p>
            <a href="#" class="btn-ver">Ver perfil completo</a>
        </div>'''
    
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
    <body><h1>👥 Comunidad Real</h1>{cartas or '<p>No hay perfiles aún.</p>'}
    <br><a href="/" style="color:#ff4b6e; font-weight:bold; text-decoration:none;">⬅️ Volver al Inicio</a></body></html>
    """

@app.post("/api/registrar")
async def registrar(data: dict):
    await database.execute(usuarios_db.insert().values(nombre=data['nombre'], ubicacion=data['ubicacion'], quien_soy=data['quien_soy']))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
