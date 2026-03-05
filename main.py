import os
import uvicorn
import databases
import sqlalchemy
from datetime import datetime
from fastapi import FastAPI, HTTPException
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
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("corazones", sqlalchemy.Integer, default=0),
    sqlalchemy.Column("foto_url", sqlalchemy.Text),
    sqlalchemy.Column("video_url", sqlalchemy.Text),
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    try:
        await database.execute("ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS video_url TEXT;")
    except: pass

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; }
    .card { background: white; border-radius: 15px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; position: relative; border: 1px solid #ffeef2; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 12px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 5px; transition: 0.3s; }
    .btn:active { transform: scale(0.98); }
    .btn-delete { position: absolute; top: 10px; right: 10px; background: #ff4444; color: white; border: none; border-radius: 50%; width: 30px; height: 30px; cursor: pointer; font-weight: bold; z-index: 10; display: flex; align-items: center; justify-content: center; }
    .heart-btn { background: white; border: 2px solid #ff4b6e; color: #ff4b6e; padding: 5px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; transition: 0.2s; }
    .heart-btn:active { transform: scale(1.3); color: red; border-color: red; }
    video { width: 100%; border-radius: 10px; margin-top: 10px; background: #000; }
    input, textarea { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
    .timer { color: #ff4b6e; font-size: 1.5rem; font-weight: bold; margin: 10px 0; display: none; }
</style>
"""

class UserData(BaseModel):
    id: Optional[int] = None
    nombre: str; edad: int; ubicacion: str; quien_soy: str; foto: str; video: Optional[str] = ""

@app.get("/", response_class=HTMLResponse)
async def inicio():
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>💖 LoveConnect Multimedia</h1>
            <div class="card">
                <h3>Crear Perfil Pro</h3>
                <input type="text" id="n" placeholder="Nombre completo">
                <input type="number" id="e" placeholder="Edad">
                <input type="text" id="u" placeholder="Ubicación (Ej: Zacatecoluca)">
                <textarea id="q" placeholder="¿Quién soy? Cuéntanos algo interesante..."></textarea>
                
                <div id="timer" class="timer">10:00</div>
                <video id="webcam" autoplay muted style="display:none;"></video>
                <video id="reproductor" controls style="display:none;"></video>
                
                <button class="btn" style="background:#4b7bff;" onclick="iniciarGrabacion()" id="btn_grab">🎥 Grabar Video (10 min)</button>
                <button class="btn" style="background:#ff4444; display:none;" onclick="detenerGrabacion()" id="btn_stop">⏹️ Detener Grabación</button>
                
                <button class="btn" style="background:#f50057; margin-top:15px;" onclick="enviarTodo()">🚀 Publicar Perfil</button>
            </div>
            <a href="/api/usuarios/ver" style="color:#ff4b6e; text-decoration:none; font-weight:bold;">Ir a la Comunidad</a>

            <script>
                let mediaRecorder; let chunks = []; let tiempo = 600; let intervalo; let videoBase64 = "";

                async function iniciarGrabacion() {{
                    chunks = [];
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                    document.getElementById('webcam').srcObject = stream;
                    document.getElementById('webcam').style.display = "block";
                    document.getElementById('btn_grab').style.display = "none";
                    document.getElementById('btn_stop').style.display = "block";
                    document.getElementById('timer').style.display = "block";

                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.ondataavailable = e => chunks.push(e.data);
                    mediaRecorder.onstop = () => {{
                        const blob = new Blob(chunks, {{ type: 'video/webm' }});
                        const reader = new FileReader();
                        reader.onloadend = () => {{ 
                            videoBase64 = reader.result;
                            document.getElementById('reproductor').src = videoBase64;
                            document.getElementById('reproductor').style.display = "block";
                        }};
                        reader.readAsDataURL(blob);
                    }};
                    mediaRecorder.start();
                    intervalo = setInterval(() => {{
                        tiempo--;
                        let min = Math.floor(tiempo / 60); let seg = tiempo % 60;
                        document.getElementById('timer').innerText = `${{min}}:${{seg < 10 ? '0' : ''}}${{seg}}`;
                        if(tiempo <= 0) detenerGrabacion();
                    }}, 1000);
                }}

                function detenerGrabacion() {{
                    clearInterval(intervalo);
                    mediaRecorder.stop();
                    document.getElementById('webcam').srcObject.getTracks().forEach(t => t.stop());
                    document.getElementById('webcam').style.display = "none";
                    document.getElementById('btn_stop').style.display = "none";
                    document.getElementById('timer').style.display = "none";
                }}

                async function enviarTodo() {{
                    const data = {{
                        nombre: document.getElementById('n').value,
                        edad: parseInt(document.getElementById('e').value),
                        ubicacion: document.getElementById('u').value,
                        quien_soy: document.getElementById('q').value,
                        foto: "https://via.placeholder.com/150",
                        video: videoBase64
                    }};
                    await fetch('/api/registrar', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(data)
                    }});
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
        video_html = f'<video src="{u.video_url}" controls></video>' if u.video_url else "<p>Sin video</p>"
        cartas += f'''
        <div class="card" id="card-{u.id}">
            <button class="btn-delete" onclick="eliminarPerfil({u.id})">X</button>
            <div style="text-align:left;">
                <strong style="font-size:1.2em;">{u.nombre} ({u.edad})</strong><br>
                <small>📍 {u.ubicacion}</small>
                <p style="background:#f9f9f9; padding:8px; border-radius:5px;">{u.quien_soy}</p>
            </div>
            {video_html}
            <div style="margin-top:10px;">
                <button class="heart-btn" onclick="darLike({u.id})">❤️ <span id="like-{u.id}">{u.corazones}</span></button>
            </div>
        </div>'''
    
    return f"""
    <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
        <body>
            <h1>👥 Comunidad</h1>
            {cartas or "<p>No hay perfiles aún.</p>"}
            <br><a href="/" class="btn" style="background:#bbb; text-decoration:none;">Volver al Inicio</a>
            <script>
                async function darLike(id) {{
                    const res = await fetch(`/api/usuarios/like/${{id}}`, {{ method: 'POST' }});
                    if(res.ok) {{
                        const s = document.getElementById('like-'+id);
                        s.innerText = parseInt(s.innerText) + 1;
                    }}
                }}
                async function eliminarPerfil(id) {{
                    if(!confirm("¿Seguro que quieres eliminar este perfil permanentemente?")) return;
                    const res = await fetch(`/api/usuarios/eliminar/${{id}}`, {{ method: 'DELETE' }});
                    if(res.ok) document.getElementById('card-'+id).remove();
                }}
            </script>
        </body>
    </html>
    """

@app.post("/api/registrar")
async def registrar(data: UserData):
    await database.execute(usuarios_db.insert().values(
        nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, 
        quien_soy=data.quien_soy, foto_url=data.foto, video_url=data.video,
        ultima_conexion=datetime.now().strftime("%H:%M")
    ))

@app.post("/api/usuarios/like/{{u_id}}")
async def like_user(u_id: int):
    await database.execute(f"UPDATE usuarios_loveconnect SET corazones = corazones + 1 WHERE id = {u_id}")

@app.delete("/api/usuarios/eliminar/{{u_id}}")
async def eliminar(u_id: int):
    await database.execute(usuarios_db.delete().where(usuarios_db.c.id == u_id))
    return {{"status": "borrado"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
