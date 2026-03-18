import asyncio
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# --- 1. CONFIGURACIÓN DE SEGURIDAD Y VIDEOS ---
VIDEO_LIMIT = 10
EXPIRATION_MINUTES = 5
videos_db = [] # Base de datos temporal de videos
mensajes_globales = [] # Memoria del chat
sugerencias_db = [] # Memoria de sugerencias

# Crear carpetas necesarias para que Render no dé error
if not os.path.exists("static/videos"):
    os.makedirs("static/videos", exist_ok=True)

# --- 2. BASE DE DATOS DE USUARIOS (ALMAS) ---
# Aquí controlas quién es Premium y quién está castigado
usuarios_db = {
    "Silver676": {
        "lvl": "∞", 
        "rango": "Creador", 
        "tipo": "Premium", 
        "castigado": False
    }
}

# --- 3. MOTOR DE LIMPIEZA AUTOMÁTICA ---
async def cleanup_videos():
    while True:
        now = datetime.now()
        for v in videos_db[:]:
            if v["expires_at"] < now:
                try:
                    if os.path.exists(v["path"]):
                        os.remove(v["path"])
                except: pass
                videos_db.remove(v)
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_videos())

# --- 4. DISEÑO UNIFICADO (HTML + CSS CYBER-NEON) ---
HTML_BASE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LoveConnect v7.1</title>
    <style>
        body { background:#000; color:white; font-family:sans-serif; margin:0; text-align:center; }
        :root { --blue:#00f7ff; --pink:#ff00c8; }
        .neon-blue { color:var(--blue); text-shadow:0 0 10px var(--blue); }
        .neon-pink { color:var(--pink); text-shadow:0 0 10px var(--pink); }

        /* PANTALLAS ESPECIALES */
        #interrogation { position:fixed; width:100%; height:100%; background:black; display:flex; 
                         flex-direction:column; justify-content:center; align-items:center; z-index:9999; }
        
        #prison { position:fixed; width:100%; height:100%; background:#000; display:{{ show_prison }}; 
                  justify-content:center; align-items:center; z-index:9998; }
        .cell { border:2px solid var(--blue); padding:40px; box-shadow:0 0 20px var(--blue); }
        .glitch { animation: glitch 1s infinite; font-size: 30px; }

        /* CONTENEDORES */
        .container { max-width:450px; margin:20px auto; padding:15px; border:1px solid #222; border-radius:15px; background:#0a0a0a; }
        input, button { border-radius: 5px; margin: 5px 0; }
        .pink-btn { border:2px solid var(--pink); color:var(--pink); background:transparent; padding:10px; cursor:pointer; font-weight:bold; width:95%; transition:0.3s; }
        .pink-btn:hover { box-shadow:0 0 20px var(--pink); background:var(--pink); color:white; }
        
        /* CHAT Y VIDEOS */
        #chat { text-align:left; height:200px; overflow-y:auto; background:black; padding:10px; border:1px solid #222; margin:10px 0; }
        .god-mode { position:fixed; bottom:10px; right:10px; padding:8px; border:2px solid red; color:red; background:black; cursor:pointer; font-size:10px; box-shadow: 0 0 10px red; }

        @keyframes glitch{ 0%{text-shadow:2px 0 red;} 50%{text-shadow:-2px 0 blue;} 100%{text-shadow:0 0 10px white;} }
    </style>
</head>
<body>

    <div id="interrogation">
        <h1 class="neon-pink">PROTOCOLO +18</h1>
        <p style="max-width:300px; color:#ccc;">Comunidad para adultos. Faltas resultan en aislamiento en la SALA DE CASTIGO.</p>
        <button class="pink-btn" onclick="document.getElementById('interrogation').style.display='none'">ACEPTAR Y ENTRAR</button>
    </div>

    <div id="prison">
        <div class="cell">
            <h1 class="neon-pink glitch">HAS SIDO AISLADO</h1>
            <p>Por orden del Creador</p>
        </div>
    </div>

    <div class="container">
        <h1 class="neon-blue" style="letter-spacing:2px;">LOVE CONNECT</h1>
        <p>Usuario: <b>{{ user }}</b> <span class="neon-pink">[LvL: {{ lvl }}]</span></p>

        <div style="display:flex; gap:10px; margin:15px 0;">
            <div style="border:1px solid var(--blue); padding:10px; width:50%; font-size:12px;">
                <b class="neon-blue">Básico</b><br>Chat/Audio/Fotos<br><b>ILIMITADO</b>
            </div>
            <div style="border:1px solid var(--pink); padding:10px; width:50%; font-size:12px;">
                <b class="neon-pink">Premium</b><br>Todo + Videos<br>
                <a href="https://www.paypal.me/silver676" target="_blank" style="color:var(--pink); text-decoration:none;"><b>COMPRAR</b></a>
            </div>
        </div>

        <div style="border:1px dashed var(--pink); padding:10px;">
            <h3 class="neon-pink" style="margin:5px;">Zona de Videos</h3>
            <p style="font-size:10px; color:gray;">⚠️ Expiración: 5 minutos</p>
            <form action="/upload-video" method="post" enctype="multipart/form-data">
                <input type="file" name="file" style="font-size:10px; width:100%;">
                <button type="submit" class="pink-btn" style="margin-top:5px;">Subir (Premium)</button>
            </form>
        </div>

        <div id="chat">
            {% for m in mensajes %}
                <p style="margin:5px 0; border-bottom:1px solid #111;">
                    <b class="neon-blue">{{ m.user }}:</b> {{ m.msg }} 
                    <span style="float:right; cursor:pointer;">❤️ 🔗</span>
                </p>
            {% endfor %}
        </div>

        <form action="/send" method="post">
            <input type="text" name="msg" placeholder="Escribe al mundo..." style="width:75%; background:#111; color:white; border:1px solid var(--blue); padding:8px;" required>
            <button type="submit" style="background:var(--blue); border:none; padding:8px 12px; cursor:pointer;">🚀</button>
        </form>

        <form action="/sugerencia" method="post" style="margin-top:10px;">
            <input type="text" name="sug" placeholder="Sugerir mejora..." style="width:60%; font-size:10px; background:none; border:1px solid #333; color:white;">
            <button type="submit" style="font-size:10px; background:#222; color:white; border:none;">Pedir</button>
        </form>

        {% if user == "Silver676" %}
            <a href="/clear-chat"><button class="god-mode">BORRAR HISTORIAL GRUPAL</button></a>
        {% endif %}
    </div>

</body>
</html>
"""

# --- 5. RUTAS DEL SERVIDOR (LOGICA) ---

@app.get("/", response_class=HTMLResponse)
async def home():
    u = usuarios_db["Silver676"]
    prison_display = "flex" if u["castigado"] else "none"
    
    # Construcción dinámica de mensajes
    msj_html = ""
    for m in mensajes_globales:
        msj_html += f"<p><b>{m['user']}:</b> {m['msg']} <span style='float:right;'>❤️ 🔗</span></p>"
    
    # Reemplazo de variables en el Template
    content = HTML_BASE.replace("{{ user }}", "Silver676")
    content = content.replace("{{ lvl }}", u["lvl"])
    content = content.replace("{{ show_prison }}", prison_display)
    
    # Inyectar mensajes (Esto evita el error de Jinja2 si no usas carpetas)
    if mensajes_globales:
        content = content.replace("{% for m in mensajes %}{% endfor %}", msj_html)
    else:
        content = content.replace("{% for m in mensajes %}{% endfor %}", "<p style='color:gray;'>No hay mensajes aún...</p>")
        
    return content

@app.post("/send")
async def send_msg(msg: str = Form(...)):
    mensajes_globales.append({"user": "Silver676", "msg": msg})
    return RedirectResponse("/", status_code=303)

@app.post("/sugerencia")
async def send_sug(sug: str = Form(...)):
    sugerencias_db.append(sug)
    return RedirectResponse("/", status_code=303)

@app.get("/clear-chat")
async def clear_chat():
    mensajes_globales.clear()
    return RedirectResponse("/", status_code=303)

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    # Validación Premium
    if usuarios_db["Silver676"]["tipo"] != "Premium":
        return HTMLResponse("<h2>ERROR: Solo usuarios Premium pueden subir videos.</h2><a href='/'>Volver</a>")
    
    if len(videos_db) >= VIDEO_LIMIT:
        return HTMLResponse("<h2>ERROR: Límite de 10 videos alcanzado.</h2><a href='/'>Volver</a>")

    path = f"static/videos/{file.filename}"
    with open(path, "wb") as f:
        f.write(await file.read())
    
    videos_db.append({
        "filename": file.filename,
        "path": path,
        "expires_at": datetime.now() + timedelta(minutes=EXPIRATION_MINUTES)
    })
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
