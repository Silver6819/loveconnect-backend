import os, uvicorn, databases, sqlalchemy, json, base64
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# 1. Base de Datos
DATABASE_URL = os.environ.get("DATABASE_URL")
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

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)
app = FastAPI()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 15px; text-align: center; }
    .card { background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 15px; border-radius: 15px; width: 100%; font-weight: bold; font-size: 1.1em; cursor: pointer; margin-top: 10px; }
    .btn-camera { background: #4b7bff; margin-bottom: 10px; }
    .preview { width: 150px; height: 150px; border-radius: 50%; object-fit: cover; border: 4px solid #ff4b6e; display: none; margin: 15px auto; }
    input { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 12px; font-size: 16px; }
</style>
"""

class UserData(BaseModel):
    nombre: str; edad: int; ubicacion: str; foto: str

@app.on_event("startup")
async def startup(): await database.connect()

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>📸 LoveConnect Scan</h1>
            <div class="card">
                <h3>Verificación de Rostro</h3>
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="number" id="e" placeholder="Edad">
                <input type="text" id="u" placeholder="Región/Ciudad">
                
                <img id="img_prev" class="preview">
                <button class="btn btn-camera" onclick="document.getElementById('f').click()">📷 Tomar/Subir Foto</button>
                <input type="file" id="f" accept="image/*" style="display:none" onchange="previewFile()">
                
                <button class="btn" id="btn_reg" onclick="enviarDatos()">Verificar y Registrar</button>
            </div>
            <a href="/api/usuarios/ver" style="text-decoration:none; color:#777;">Ver Comunidad</a>

            <script>
                let base64String = "";
                function previewFile() {{
                    const file = document.getElementById('f').files[0];
                    const reader = new FileReader();
                    reader.onloadend = function() {{
                        document.getElementById('img_prev').src = reader.result;
                        document.getElementById('img_prev').style.display = "block";
                        base64String = reader.result;
                    }}
                    if (file) reader.readAsDataURL(file);
                }}

                async function enviarDatos() {{
                    const n = document.getElementById('n').value;
                    const e = document.getElementById('e').value;
                    const u = document.getElementById('u').value;
                    const btn = document.getElementById('btn_reg');

                    if(!n || !base64String) {{ alert("Por favor, completa tu nombre y tómate una foto."); return; }}
                    
                    btn.innerHTML = "Procesando...";
                    btn.disabled = true;

                    try {{
                        const res = await fetch('/api/registrar', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ nombre:n, edad:parseInt(e), ubicacion:u, foto:base64String }})
                        }});
                        if(res.ok) {{ location.href = '/api/usuarios/ver'; }}
                        else {{ alert("Error al registrar. Quizás el nombre ya existe."); btn.disabled = false; btn.innerHTML = "Verificar y Registrar"; }}
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
            <img src="{r['foto_b64']}" style="width:80px; height:80px; border-radius:50%; object-fit:cover; border: 2px solid #ff4b6e;">
            <div>
                <strong style="font-size:1.2em;">{r['nombre']}</strong> <br>
                <small>📍 {r['ubicacion']} | {r['edad']} años</small><br>
                <small style="color:green;">● Activo hoy</small>
            </div>
        </div>"""
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div style='max-width:500px; margin:auto;'><h1>Comunidad</h1>{cartas}<a href='/' class='btn' style='background:#bbb;'>Volver</a></div></body></html>"
