import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = os.environ.get("DATABASE_URL")

# Corrección de protocolo para SQLAlchemy (VITAL para Railway)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Definición robusta de la tabla
usuarios_db = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String, unique=True),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("foto_b64", sqlalchemy.Text),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String),
    sqlalchemy.Column("es_premium", sqlalchemy.Boolean, default=False)
)

# Intentar crear las tablas físicamente al arranque
try:
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
except Exception as e:
    print(f"Error inicializando tablas: {e}")

app = FastAPI()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 15px; text-align: center; color: #333; }
    .card { background: white; border-radius: 25px; padding: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #ffeef2; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 14px; border-radius: 12px; width: 100%; font-weight: bold; font-size: 1.1em; cursor: pointer; margin-top: 10px; text-decoration: none; display: block; }
    .preview { width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 4px solid #ff4b6e; display: none; margin: 15px auto; }
    input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 12px; box-sizing: border-box; font-size: 16px; }
</style>
"""

class UserData(BaseModel):
    nombre: str; edad: int; ubicacion: str; foto: str

@app.on_event("startup")
async def startup():
    try:
        if not database.is_connected:
            await database.connect()
    except Exception as e:
        print(f"Error de conexión: {e}")

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>💖 LoveConnect Scan</h1>
            <div class="card">
                <h3>Registro de Usuario</h3>
                <input type="text" id="n" placeholder="Nombre">
                <input type="number" id="e" placeholder="Edad">
                <input type="text" id="u" placeholder="Ubicación">
                <img id="img_prev" class="preview">
                <button class="btn" style="background:#4b7bff;" onclick="document.getElementById('f').click()">📷 Foto</button>
                <input type="file" id="f" accept="image/*" style="display:none" onchange="processImage()">
                <button class="btn" id="btn_reg" onclick="enviarDatos()">Registrar</button>
            </div>
            <a href="/api/usuarios/ver" style="color:#888;">Ver Comunidad</a>
            <script>
                let b64 = "";
                function processImage() {{
                    const file = document.getElementById('f').files[0];
                    const reader = new FileReader();
                    reader.onload = (e) => {{
                        const img = new Image();
                        img.onload = () => {{
                            const canvas = document.createElement('canvas');
                            canvas.width = 400; canvas.height = (img.height * 400) / img.width;
                            canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                            b64 = canvas.toDataURL("image/jpeg", 0.7);
                            document.getElementById('img_prev').src = b64;
                            document.getElementById('img_prev').style.display = "block";
                        }};
                        img.src = e.target.result;
                    }};
                    reader.readAsDataURL(file);
                }}
                async function enviarDatos() {{
                    const n = document.getElementById('n').value;
                    const e = document.getElementById('e').value;
                    const u = document.getElementById('u').value;
                    if(!n || !b64) return alert("Faltan datos");
                    const res = await fetch('/api/registrar', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ nombre:n, edad:parseInt(e), ubicacion:u, foto:b64 }})
                    }});
                    if(res.ok) location.href = '/api/usuarios/ver';
                    else alert("Error al registrar");
                }}
            </script>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: UserData):
    hora = datetime.now().strftime("%H:%M")
    query = usuarios_db.insert().values(
        nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, 
        foto_b64=data.foto, ultima_conexion=hora
    )
    await database.execute(query)
    return {"status": "ok"}

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver():
    try:
        rows = await database.fetch_all(usuarios_db.select())
        cartas = ""
        for r in rows:
            # Cambio crítico: Acceso por nombre de columna para evitar Error 500
            nombre = getattr(r, 'nombre', 'Usuario')
            foto = getattr(r, 'foto_b64', '')
            ubi = getattr(r, 'ubicacion', 'N/A')
            edad = getattr(r, 'edad', '??')
            
            cartas += f"""
            <div class="card" style="display:flex; align-items:center; gap:15px; text-align:left;">
                <img src="{foto}" style="width:70px; height:70px; border-radius:50%; object-fit:cover;">
                <div>
                    <strong style="color:#ff4b6e;">{nombre}</strong><br>
                    <small>{ubi} | {edad} años</small>
                </div>
            </div>"""
        
        if not cartas: cartas = "<p>Aún no hay registros.</p>"
        
    except Exception as e:
        cartas = f"<p>Error al conectar con la base de datos: {e}</p>"

    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>💖 Comunidad</h1>{cartas}<br><a href='/' class='btn' style='background:#bbb;'>Volver</a></body></html>"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
