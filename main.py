import os, uvicorn, databases, sqlalchemy, json
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# --- CONFIGURACIÓN DE BASE DE DATOS CON CORRECCIÓN ---
DATABASE_URL = os.environ.get("DATABASE_URL")

# Esto corrige el error de "driver" si la URL viene como postgres://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

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

# Intentar crear las tablas al iniciar
try:
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
except Exception as e:
    print(f"Error creando tablas: {e}")

app = FastAPI()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 15px; text-align: center; color: #333; }
    .card { background: white; border-radius: 25px; padding: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.08); margin-bottom: 20px; border: 1px solid #ffeef2; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 14px; border-radius: 12px; width: 100%; font-weight: bold; font-size: 1.1em; cursor: pointer; margin-top: 10px; transition: 0.3s; }
    .btn:disabled { background: #ccc; }
    .btn-camera { background: #4b7bff; margin-bottom: 10px; }
    .preview { width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 4px solid #ff4b6e; display: none; margin: 15px auto; }
    input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 12px; box-sizing: border-box; font-size: 16px; }
    .status-dot { height: 10px; width: 10px; background-color: #2ecc71; border-radius: 50%; display: inline-block; margin-right: 5px; }
</style>
"""

class UserData(BaseModel):
    nombre: str; edad: int; ubicacion: str; foto: str

@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>💖 LoveConnect Scan</h1>
            <div class="card">
                <h3>Verificación Facial</h3>
                <input type="text" id="n" placeholder="Tu nombre artístico">
                <input type="number" id="e" placeholder="Tu edad">
                <input type="text" id="u" placeholder="Región">
                <canvas id="canvas" style="display:none;"></canvas>
                <img id="img_prev" class="preview">
                <button class="btn btn-camera" onclick="document.getElementById('f').click()">📷 Tomar Foto Real</button>
                <input type="file" id="f" accept="image/*" style="display:none" onchange="processImage()">
                <button class="btn" id="btn_reg" onclick="enviarDatos()">Verificar y Registrar</button>
            </div>
            <a href="/api/usuarios/ver" style="text-decoration:none; color:#888;">Ver Comunidad Registrada</a>
            <script>
                let compressedBase64 = "";
                function processImage() {{
                    const file = document.getElementById('f').files[0];
                    const reader = new FileReader();
                    reader.onload = function(e) {{
                        const img = new Image();
                        img.onload = function() {{
                            const canvas = document.getElementById('canvas');
                            const MAX_WIDTH = 400;
                            let width = img.width;
                            let height = img.height;
                            if (width > height) {{
                                if (width > MAX_WIDTH) {{ height *= MAX_WIDTH / width; width = MAX_WIDTH; }}
                            }} else {{
                                if (height > MAX_WIDTH) {{ width *= MAX_WIDTH / height; height = MAX_WIDTH; }}
                            }}
                            canvas.width = width; canvas.height = height;
                            const ctx = canvas.getContext("2d");
                            ctx.drawImage(img, 0, 0, width, height);
                            compressedBase64 = canvas.toDataURL("image/jpeg", 0.7);
                            document.getElementById('img_prev').src = compressedBase64;
                            document.getElementById('img_prev').style.display = "block";
                        }}
                        img.src = e.target.result;
                    }}
                    reader.readAsDataURL(file);
                }}
                async function enviarDatos() {{
                    const n = document.getElementById('n').value;
                    const e = document.getElementById('e').value;
                    const u = document.getElementById('u').value;
                    const btn = document.getElementById('btn_reg');
                    if(!n || !compressedBase64) {{ alert("Falta nombre o foto"); return; }}
                    btn.innerHTML = "Subiendo..."; btn.disabled = true;
                    try {{
                        const res = await fetch('/api/registrar', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ nombre:n, edad:parseInt(e), ubicacion:u, foto:compressedBase64 }})
                        }});
                        if(res.ok) {{ location.href = '/api/usuarios/ver'; }}
                        else {{ alert("Error al registrar"); btn.disabled = false; }}
                    }} catch(err) {{ alert("Error de conexión"); btn.disabled = false; }}
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
    rows = await database.fetch_all(usuarios_db.select())
    cartas = ""
    for r in rows:
        cartas += f"""
        <div class="card" style="display:flex; align-items:center; gap:15px; text-align:left;">
            <img src="{r['foto_b64']}" style="width:75px; height:75px; border-radius:50%; object-fit:cover; border: 2px solid #ff4b6e;">
            <div>
                <strong style="color:#ff4b6e;">{r['nombre']}</strong> <br>
                <small>📍 {r['ubicacion']} | {r['edad']} años</small>
            </div>
        </div>"""
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>💖 Comunidad</h1>{cartas}<a href='/' class='btn' style='background:#bbb;'>Volver</a></body></html>"
