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

# Definición de la tabla
usuarios_db = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("corazones", sqlalchemy.Integer, default=0),
    sqlalchemy.Column("foto_url", sqlalchemy.Text),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String)
)

app = FastAPI()

# --- FUNCIÓN AUTOCORREGIBLE (Arregla el error de columnas) ---
@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()
    
    # Este bloque de código crea las columnas si no existen automáticamente
    try:
        query1 = "ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS quien_soy TEXT;"
        query2 = "ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS corazones INTEGER DEFAULT 0;"
        await database.execute(query1)
        await database.execute(query2)
        print("✅ Base de datos actualizada correctamente.")
    except Exception as e:
        print(f"Nota: Las columnas ya existen o se están creando: {e}")

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; color: #333; }
    .card { background: white; border-radius: 15px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; position: relative; border: 1px solid #ffeef2; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 10px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 5px; text-decoration: none; display: block; box-sizing: border-box; }
    .btn-like { background: #fff; border: 1px solid #ff4b6e; color: #ff4b6e; padding: 5px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; }
    .preview { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #ff4b6e; display: none; margin: 10px auto; }
    input, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
    .filtro { background: white; padding: 10px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #ff4b6e; }
</style>
"""

class UserData(BaseModel):
    id: Optional[int] = None
    nombre: str; edad: int; ubicacion: str; quien_soy: str; foto: str

@app.get("/", response_class=HTMLResponse)
async def inicio(edit: Optional[bool] = None, id: Optional[int] = None, n: str = "", e: int = 0, u: str = "", q: str = ""):
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>💖 LoveConnect</h1>
            <div class="card">
                <h3>{ "Editar Perfil" if edit else "Crear Perfil" }</h3>
                <input type="hidden" id="user_id" value="{id or ''}">
                <input type="text" id="n" placeholder="Nombre completo" value="{n}">
                <input type="number" id="e" placeholder="Edad" value="{e or ''}">
                <input type="text" id="u" placeholder="Ubicación (Ej: Zacatecoluca)" value="{u}">
                <textarea id="q" placeholder="¿Quién soy? Cuéntanos de ti...">{q}</textarea>
                <img id="img_prev" class="preview">
                <button class="btn" style="background:#4b7bff;" onclick="document.getElementById('f').click()">📷 Foto</button>
                <input type="file" id="f" accept="image/*" style="display:none" onchange="processImage()">
                <button class="btn" id="btn_reg" onclick="enviarDatos()">{ "Actualizar" if edit else "Registrarme" }</button>
            </div>
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold;">Ver Comunidad</a>
            <script>
                let b64 = localStorage.getItem('temp_foto') || "";
                if(b64) {{ document.getElementById('img_prev').src = b64; document.getElementById('img_prev').style.display = "block"; }}
                
                function processImage() {{
                    const file = document.getElementById('f').files[0];
                    const reader = new FileReader();
                    reader.onload = (e) => {{
                        const img = new Image();
                        img.onload = () => {{
                            const canvas = document.createElement('canvas');
                            canvas.width = 400; canvas.height = (img.height * 400) / img.width;
                            canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                            b64 = canvas.toDataURL("image/jpeg", 0.6);
                            document.getElementById('img_prev').src = b64; document.getElementById('img_prev').style.display = "block";
                        }};
                        img.src = e.target.result;
                    }};
                    reader.readAsDataURL(file);
                }}
                async function enviarDatos() {{
                    const id = document.getElementById('user_id').value;
                    const data = {{
                        id: id ? parseInt(id) : null,
                        nombre: document.getElementById('n').value,
                        edad: parseInt(document.getElementById('e').value),
                        ubicacion: document.getElementById('u').value,
                        quien_soy: document.getElementById('q').value,
                        foto: b64
                    }};
                    const res = await fetch('/api/registrar', {{
                        method: id ? 'PUT' : 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
                    if(res.ok) {{ localStorage.removeItem('temp_foto'); location.href = '/api/usuarios/ver'; }}
                }}
            </script>
        </body>
    </html>
    """

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver(ciudad: Optional[str] = None):
    query = usuarios_db.select()
    if ciudad: query = query.where(usuarios_db.c.ubicacion.ilike(f"%{ciudad}%"))
    users = await database.fetch_all(query)
    
    cartas = ""
    for u in users:
        cartas += f'''
        <div class="card">
            <div style="display:flex; align-items:center; gap:15px; text-align:left;">
                <img src="{u.foto_url}" style="width:70px; height:70px; border-radius:50%; object-fit:cover;">
                <div style="flex:1">
                    <strong>{u.nombre}</strong> ({u.edad})<br>
                    <small>📍 {u.ubicacion}</small><br>
                    <button class="btn-like" onclick="darLike({u.id})">❤️ <span id="like-{u.id}">{u.corazones}</span></button>
                </div>
                <button onclick="prepararEdicion({{id:{u.id}, n:'{u.nombre}', e:{u.edad}, u:'{u.ubicacion}', q:'{u.quien_soy}', f:'{u.foto_url}'}})" style="border:none; background:none; cursor:pointer; font-size:1.2em;">✏️</button>
            </div>
            <p style="text-align:left; font-size:0.9em; background:#fdfdfd; padding:10px; border-radius:8px; border:1px solid #eee; margin-top:10px;">
                <strong>Sobre mí:</strong> {u.quien_soy or "¡Hola! Soy nuevo aquí."}
            </p>
        </div>'''

    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>👥 Comunidad</h1>
            <div class="filtro">
                <input type="text" id="busc" placeholder="🔍 Ciudad (Zacatecoluca...)">
                <button class="btn" style="background:#ff4b6e;" onclick="filtrar()">Filtrar</button>
            </div>
            {cartas or "<p>No hay perfiles en esta zona.</p>"}
            <br><a href="/" class="btn" style="background:#bbb;">Volver</a>
            <script>
                function filtrar() {{
                    const c = document.getElementById('busc').value;
                    location.href = '/api/usuarios/ver' + (c ? '?ciudad='+c : '');
                }}
                async function darLike(id) {{
                    const res = await fetch(`/api/usuarios/like/${{id}}`, {{ method: 'POST' }});
                    if(res.ok) {{ 
                        const span = document.getElementById('like-'+id);
                        span.innerText = parseInt(span.innerText) + 1;
                    }}
                }}
                function prepararEdicion(user) {{
                    localStorage.setItem('temp_foto', user.f);
                    location.href = `/?edit=true&id=${{user.id}}&n=${{encodeURIComponent(user.n)}}&e=${{user.e}}&u=${{encodeURIComponent(user.u)}}&q=${{encodeURIComponent(user.q)}}`;
                }}
            </script>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: UserData):
    hora = datetime.now().strftime("%H:%M")
    await database.execute(usuarios_db.insert().values(nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, quien_soy=data.quien_soy, foto_url=data.foto, ultima_conexion=hora))

@app.put("/api/registrar")
async def actualizar(data: UserData):
    await database.execute(usuarios_db.update().where(usuarios_db.c.id == data.id).values(nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, quien_soy=data.quien_soy, foto_url=data.foto))

@app.post("/api/usuarios/like/{{u_id}}")
async def like_user(u_id: int):
    await database.execute(f"UPDATE usuarios_loveconnect SET corazones = corazones + 1 WHERE id = {u_id}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
