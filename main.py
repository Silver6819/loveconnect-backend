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

usuarios_db = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("foto_url", sqlalchemy.Text), 
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String)
)

try:
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
except Exception as e:
    print(f"Aviso DB: {e}")

app = FastAPI()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 15px; text-align: center; color: #333; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 20px; position: relative; border: 1px solid #ffeef2; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 12px; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 10px; text-decoration: none; display: block; box-sizing: border-box; }
    .btn-edit { background: #4b7bff; width: auto; padding: 5px 10px; position: absolute; top: 10px; right: 50px; font-size: 0.8em; border-radius: 5px; color: white; border:none; cursor:pointer; }
    .btn-delete { background: #ff4444; width: auto; padding: 5px 10px; position: absolute; top: 10px; right: 10px; font-size: 0.8em; border-radius: 5px; color: white; border:none; cursor:pointer; }
    .preview { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #ff4b6e; display: none; margin: 10px auto; }
    input { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
</style>
"""

class UserData(BaseModel):
    id: Optional[int] = None
    nombre: str; edad: int; ubicacion: str; foto: str

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()

@app.get("/", response_class=HTMLResponse)
async def inicio(edit_id: Optional[int] = None):
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1 id="titulo">💖 LoveConnect</h1>
            <div class="card">
                <h3 id="form_title">Crear Perfil</h3>
                <input type="hidden" id="user_id">
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="number" id="e" placeholder="Edad">
                <input type="text" id="u" placeholder="Ubicación">
                <img id="img_prev" class="preview">
                <button class="btn" style="background:#4b7bff;" onclick="document.getElementById('f').click()">📷 Cambiar Foto</button>
                <input type="file" id="f" accept="image/*" style="display:none" onchange="processImage()">
                <button class="btn" id="btn_reg" onclick="enviarDatos()">Registrarme</button>
                <button id="btn_cancel" class="btn" style="background:#bbb; display:none;" onclick="cancelarEdicion()">Cancelar</button>
            </div>
            <a href="/api/usuarios/ver" style="color:#ff4b6e;">Ver Comunidad</a>
            <script>
                let b64 = "";
                // Cargar datos si venimos de editar
                const urlParams = new URLSearchParams(window.location.search);
                if(urlParams.has('edit')) {{
                    document.getElementById('form_title').innerText = "Editar Perfil";
                    document.getElementById('btn_reg').innerText = "Actualizar Datos";
                    document.getElementById('btn_cancel').style.display = "block";
                    // Los datos se pasan por la URL para esta versión simple
                    document.getElementById('user_id').value = urlParams.get('id');
                    document.getElementById('n').value = urlParams.get('n');
                    document.getElementById('e').value = urlParams.get('e');
                    document.getElementById('u').value = urlParams.get('u');
                    b64 = localStorage.getItem('temp_foto');
                    if(b64) {{
                        document.getElementById('img_prev').src = b64;
                        document.getElementById('img_prev').style.display = "block";
                    }}
                }}

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
                            document.getElementById('img_prev').src = b64;
                            document.getElementById('img_prev').style.display = "block";
                        }};
                        img.src = e.target.result;
                    }};
                    reader.readAsDataURL(file);
                }}

                async function enviarDatos() {{
                    const id = document.getElementById('user_id').value;
                    const n = document.getElementById('n').value;
                    const e = document.getElementById('e').value;
                    const u = document.getElementById('u').value;
                    if(!n || !b64) return alert("Faltan datos o foto");
                    
                    const metodo = id ? 'PUT' : 'POST';
                    const res = await fetch('/api/registrar', {{
                        method: metodo,
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: id ? parseInt(id) : null, nombre:n, edad:parseInt(e), ubicacion:u, foto:b64 }})
                    }});
                    if(res.ok) {{
                        localStorage.removeItem('temp_foto');
                        location.href = '/api/usuarios/ver';
                    }} else alert("Error al guardar");
                }}

                function cancelarEdicion() {{ location.href = "/"; }}
            </script>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: UserData):
    hora = datetime.now().strftime("%H:%M")
    query = usuarios_db.insert().values(nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, foto_url=data.foto, ultima_conexion=hora)
    await database.execute(query)
    return {{"status": "ok"}}

@app.put("/api/registrar")
async def actualizar(data: UserData):
    query = usuarios_db.update().where(usuarios_db.c.id == data.id).values(nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, foto_url=data.foto)
    await database.execute(query)
    return {{"status": "actualizado"}}

@app.delete("/api/usuarios/borrar/{{usuario_id}}")
async def borrar_usuario(usuario_id: int):
    query = usuarios_db.delete().where(usuarios_db.c.id == usuario_id)
    await database.execute(query)
    return {{"status": "borrado"}}

@app.get("/api/usuarios/ver", response_class=HTMLResponse)
async def ver():
    rows = await database.fetch_all(usuarios_db.select())
    cartas = ""
    for r in rows:
        # Escapamos la foto para pasarla al editor temporalmente
        cartas += f'''
        <div class="card" style="display:flex; align-items:center; gap:15px; text-align:left;">
            <button class="btn-edit" onclick="prepararEdicion({{id:{r.id}, n:'{r.nombre}', e:{r.edad}, u:'{r.ubicacion}', f:'{r.foto_url}'}})">✏️</button>
            <button class="btn-delete" onclick="borrarPerfil({r.id})">🗑️</button>
            <img src="{r.foto_url}" style="width:60px; height:60px; border-radius:50%; object-fit:cover;">
            <div>
                <strong>{r.nombre}</strong><br>
                <small>{r.ubicacion} | {r.edad} años</small>
            </div>
        </div>'''
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>👥 Comunidad</h1>
            {cartas or "<p>No hay perfiles.</p>"}
            <br><a href="/" class="btn" style="background:#bbb;">Volver</a>
            <script>
                async function borrarPerfil(id) {{
                    if(confirm("¿Eliminar este perfil?")) {{
                        await fetch(`/api/usuarios/borrar/${{id}}`, {{ method: 'DELETE' }});
                        location.reload();
                    }}
                }}
                function prepararEdicion(user) {{
                    localStorage.setItem('temp_foto', user.f);
                    location.href = `/?edit=true&id=${{user.id}}&n=${{encodeURIComponent(user.n)}}&e=${{user.e}}&u=${{encodeURIComponent(user.u)}}`;
                }}
            </script>
        </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
