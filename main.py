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
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("corazones", sqlalchemy.Integer, default=0),
    sqlalchemy.Column("foto_url", sqlalchemy.Text),
    sqlalchemy.Column("video_url", sqlalchemy.Text), # NUEVO: Para guardar el video/audio
    sqlalchemy.Column("ultima_conexion", sqlalchemy.String)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    # Autocorrección de tabla para el campo de video
    try:
        await database.execute("ALTER TABLE usuarios_loveconnect ADD COLUMN IF NOT EXISTS video_url TEXT;")
    except: pass

ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; padding: 10px; text-align: center; }
    .card { background: white; border-radius: 15px; padding: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; border: 1px solid #ffeef2; }
    .btn { background: #ff4b6e; color: white; border: none; padding: 10px; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 5px; }
    .timer { color: red; font-weight: bold; font-size: 1.2em; margin: 10px 0; display: none; }
    video, audio { width: 100%; border-radius: 10px; margin-top: 10px; background: #000; }
    .preview { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid #ff4b6e; margin: 10px auto; display:block; }
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
                <input type="text" id="n" placeholder="Nombre">
                <input type="number" id="e" placeholder="Edad">
                <input type="text" id="u" placeholder="Ubicación (Zacatecoluca)">
                <textarea id="q" placeholder="Sobre mí..."></textarea>
                
                <div id="timer" class="timer">10:00</div>
                <video id="webcam" autoplay muted style="display:none;"></video>
                <video id="reproductor" controls style="display:none;"></video>
                
                <button class="btn" style="background:#4b7bff;" onclick="iniciarGrabacion()" id="btn_grab">🎥 Grabar Video (Max 10 min)</button>
                <button class="btn" style="background:#ff4444; display:none;" onclick="detenerGrabacion()" id="btn_stop">⏹️ Detener</button>
                
                <button class="btn" onclick="enviarTodo()">🚀 Publicar Perfil</button>
            </div>
            <a href="/api/usuarios/ver">Ver Comunidad</a>

            <script>
                let mediaRecorder;
                let chunks = [];
                let tiempo = 600; // 10 minutos en segundos
                let intervalo;
                let videoBase64 = "";

                async function iniciarGrabacion() {{
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
                    document.getElementById('webcam').srcObject = stream;
                    document.getElementById('webcam').style.display = "block";
                    document.getElementById('btn_grab').style.display = "none";
                    document.getElementById('btn_stop').style.display = "block";
                    document.getElementById('timer').style.display = "block";

                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.ondataavailable = e => chunks.push(e.data);
                    mediaRecorder.onstop = async () => {{
                        const blob = new Blob(chunks, {{ type: 'video/webm' }});
                        if(blob.size > 2000000000) alert("Archivo demasiado grande (Límite 2GB)");
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
                        let min = Math.floor(tiempo / 60);
                        let seg = tiempo % 60;
                        document.getElementById('timer').innerText = `${{min}}:${{seg < 10 ? '0' : ''}}${{seg}}`;
                        if(tiempo <= 0) detenerGrabacion();
                    }}, 1000);
                }}

                function detenerGrabacion() {{
                    clearInterval(intervalo);
                    mediaRecorder.stop();
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
                        foto: "https://via.placeholder.com/150", // Foto por defecto para prueba
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
        video_html = f'<video src="{u.video_url}" controls></video>' if u.video_url else "<p>Sin video de presentación</p>"
        cartas += f'''
        <div class="card">
            <strong>{u.nombre}</strong><br>
            <small>📍 {u.ubicacion}</small>
            <p>{u.quien_soy}</p>
            {video_html}
        </div>'''
    return f"<html><head>{ESTILOS}</head><body><h1>Comunidad</h1>{cartas}<br><a href='/'>Volver</a></body></html>"

@app.post("/api/registrar")
async def registrar(data: UserData):
    await database.execute(usuarios_db.insert().values(
        nombre=data.nombre, edad=data.edad, ubicacion=data.ubicacion, 
        quien_soy=data.quien_soy, foto_url=data.foto, video_url=data.video,
        ultima_conexion=datetime.now().strftime("%H:%M")
    ))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
