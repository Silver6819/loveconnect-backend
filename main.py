import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Tablas
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

mensajes_db = sqlalchemy.Table(
    "mensajes_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("usuario_id", sqlalchemy.Integer), # A quién va el mensaje
    sqlalchemy.Column("texto", sqlalchemy.Text),
    sqlalchemy.Column("fecha", sqlalchemy.String)
)

try:
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)
except Exception as e:
    print(f"Aviso DB: {e}")

app = FastAPI()

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; color: #333; }
    .card { background: white; border-radius: 15px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; position: relative; border: 1px solid #ffeef2; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 10px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 5px; text-decoration: none; display: block; box-sizing: border-box; font-size: 0.9em; }
    .btn-edit { background: #4b7bff; width: 35px; height: 35px; position: absolute; top: 10px; right: 50px; border-radius: 5px; color: white; border:none; cursor:pointer; }
    .btn-delete { background: #ff4444; width: 35px; height: 35px; position: absolute; top: 10px; right: 10px; border-radius: 5px; color: white; border:none; cursor:pointer; }
    .msg-box { background: #f9f9f9; border-radius: 10px; padding: 10px; margin-top: 10px; text-align: left; font-size: 0.85em; border-left: 4px solid #ff4b6e; position: relative; }
    .preview { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid #ff4b6e; display: none; margin: 10px auto; }
    input, textarea { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-family: inherit; }
</style>
"""

class UserData(BaseModel):
    id: Optional[int] = None
    nombre: str; edad: int; ubicacion: str; foto: str

class MsgData(BaseModel):
    id: Optional[int] = None
    usuario_id: int; texto: str

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>💖 LoveConnect</h1>
            <div class="card">
                <h3 id="form_title">Crear Perfil</h3>
                <input type="hidden" id="user_id">
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="number" id="e" placeholder="Edad">
                <input type="text" id="u" placeholder="Ubicación">
                <img id="img_prev" class="preview">
                <button class="btn" style="background:#4b7bff;" onclick="document.getElementById('f').click()">📷 Foto</button>
                <input type="file" id="f" accept="image/*" style="display:none" onchange="processImage()">
                <button class="btn" id="btn_reg" onclick="enviarDatos()">Registrarme</button>
                <button id="btn_cancel" class="btn" style="background:#bbb; display:none;" onclick="location.href='/'">Cancelar</button>
            </div>
            <a href="/api/usuarios/ver" style="color:#ff4b6e; font-weight:bold;">Ir a la Comunidad</a>
            <script>
                let b64 = "";
                const params = new URLSearchParams(window.location.search);
                if(params.has('edit')) {{
                    document.getElementById('form_title').innerText = "Editar Perfil";
                    document.getElementById('btn_reg').innerText = "Actualizar Datos";
                    document.getElementById('btn_cancel').style.display = "block";
                    document.getElementById('user_id').value = params.get('id');
                    document.getElementById('n').value = params.get('n');
                    document.getElementById('e').value = params.get('e');
                    document.getElementById('u').value = params.get('u');
                    b64 = localStorage.getItem('temp_foto');
                    if(b64) {{ document.getElementById('img_prev').src = b64; document.getElementById('img_prev').style.display = "block"; }}
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
                            document.getElementById('img_prev').src = b64; document.getElementById('img_prev').style.display = "block";
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
                    if(!n || !b64) return alert("Faltan datos");
                    const res = await fetch('/api/registrar', {{
                        method: id ? 'PUT' : 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ id: id ? parseInt(id) : null, nombre:n, edad:parseInt(e), ubicacion:u, foto:b64 }})
                    }});
                    if(res.ok) location.href = '/api/usuarios/ver';
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
        # Cargar mensajes de este usuario
        msgs = await database.fetch_all(mensajes_db.select().where(mensajes_db.c.usuario_id == u.id))
        html_msgs = ""
        for m in msgs:
            html_msgs += f'''
            <div class="msg-box">
                {m.texto} <br><small style="color:#999;">{m.fecha}</small>
                <button onclick="editarMsg({m.id}, '{m.texto}')" style="border:none; background:none; cursor:pointer; float:right;">✏️</button>
                <button onclick="borrarMsg({m.id})" style="border:none; background:none; cursor:pointer; float:right;">🗑️</button>
            </div>'''
        
        cartas += f'''
        <div class="card">
            <button class="btn-edit" onclick="prepararEdicion({{id:{u.id}, n:'{u.nombre}', e:{u.edad}, u:'{u.ubicacion}', f:'{u.foto_url}'}})">✏️</button>
            <button class="btn-delete" onclick="borrarPerfil({u.id})">🗑️</button>
            <div style="display:flex; align-items:center; gap:15px; text-align:left; margin-bottom:10px;">
                <img src="{u.foto_url}" style="width:60px; height:60px; border-radius:50%; object-fit:cover;">
                <div><strong>{u.nombre}</strong><br><small>{u.ubicacion} | {u.edad} años</small></div>
            </div>
            <div id="muro-{u.id}">{html_msgs}</div>
            <textarea id="input-msg-{u.id}" placeholder="Escribe un mensaje..."></textarea>
            <button class="btn" style="background:#4b7bff;" onclick="enviarMsg({u.id})">Enviar Mensaje</button>
        </div>'''
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>👥 Comunidad</h1>
            {cartas or "<p>No hay perfiles.</p>"}
            <br><a href="/" class="btn" style="background:#bbb;">Volver al Inicio</a>
            <script>
                async function enviarMsg(u_id) {{
                    const txt = document.getElementById('input-msg-'+u_id).value;
                    if(!txt) return;
                    await fetch('/api/mensajes', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ usuario_id: u_id, texto: txt }})
                    }});
                    location.reload();
                }}
                async function editarMsg(m_id, viejoTxt) {{
                    const nuevo = prompt("Corregir mensaje:", viejoTxt);
                    if(nuevo && nuevo !== viejoTxt) {{
                        await fetch('/api/mensajes', {{
                            method: 'PUT',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ id: m_id, usuario_id:0, texto: nuevo }})
                        }});
                        location.reload();
                    }}
                }}
                async function borrarMsg(m_id) {{
                    if(confirm("¿Borrar mensaje?")) {{
                        await fetch(`/api/mensajes/${{m_id}}`, {{ method: 'DELETE' }});
                        location.reload();
                    }}
                }}
                async function borrarPerfil(id) {{
                    if(confirm("¿Eliminar perfil?")) {{
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

@app.post("/api/registrar")
async def registrar(data: UserData):
    hora = datetime.now().strftime("%H:%M")
    await database.execute(usuarios_db.insert().values(nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, foto_url=data.foto, ultima_conexion=hora))
    return {{"status": "ok"}}

@app.put("/api/registrar")
async def actualizar(data: UserData):
    await database.execute(usuarios_db.update().where(usuarios_db.c.id == data.id).values(nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, foto_url=data.foto))
    return {{"status": "ok"}}

@app.delete("/api/usuarios/borrar/{{usuario_id}}")
async def borrar_usuario(usuario_id: int):
    await database.execute(usuarios_db.delete().where(usuarios_db.c.id == usuario_id))
    await database.execute(mensajes_db.delete().where(mensajes_db.c.usuario_id == usuario_id))
    return {{"status": "ok"}}

@app.post("/api/mensajes")
async def msg_post(data: MsgData):
    fecha = datetime.now().strftime("%d/%m %H:%M")
    await database.execute(mensajes_db.insert().values(usuario_id=data.usuario_id, texto=data.texto, fecha=fecha))
    return {{"status": "ok"}}

@app.put("/api/mensajes")
async def msg_put(data: MsgData):
    await database.execute(mensajes_db.update().where(mensajes_db.c.id == data.id).values(texto=data.texto))
    return {{"status": "ok"}}

@app.delete("/api/mensajes/{{m_id}}")
async def msg_del(m_id: int):
    await database.execute(mensajes_db.delete().where(mensajes_db.c.id == m_id))
    return {{"status": "ok"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
