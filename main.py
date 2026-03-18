import asyncio
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# --- CONFIGURACIÓN DE VIDEOS ---
VIDEO_LIMIT = 10
EXPIRATION_MINUTES = 5
videos_db = [] # Lista en memoria para rapidez
if not os.path.exists("static/videos"):
    os.makedirs("static/videos", exist_ok=True)

# --- BASE DE DATOS DE ALMAS ---
usuarios_db = {
    "Silver676": {"lvl": "∞", "rango": "Creador", "tipo": "Premium", "castigado": False}
}
mensajes_globales = []

# --- LIMPIEZA AUTOMÁTICA DE VIDEOS (Cada 60 seg) ---
async def cleanup_videos():
    while True:
        now = datetime.now()
        for v in videos_db[:]:
            if v["expires_at"] < now:
                try:
                    os.remove(v["path"])
                except: pass
                videos_db.remove(v)
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_videos())

# --- HTML UNIFICADO (CYBER-NEON) ---
HTML_BASE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LoveConnect v7.0</title>
    <style>
        body { background:#000; color:white; font-family:sans-serif; margin:0; text-align:center; overflow-x:hidden; }
        :root { --blue:#00f7ff; --pink:#ff00c8; }
        .neon-blue { color:var(--blue); text-shadow:0 0 10px var(--blue); }
        .neon-pink { color:var(--pink); text-shadow:0 0 10px var(--pink); }

        /* PROTOCOLO +18 */
        #interrogation { position:fixed; width:100%; height:100%; background:black; display:flex; 
                         flex-direction:column; justify-content:center; align-items:center; z-index:9999; }
        
        /* SALA DE CASTIGO */
        #prison { position:fixed; width:100%; height:100%; background:#000; display:{{ show_prison }}; 
                  justify-content:center; align-items:center; z-index:9998; }
        .cell { border:2px solid var(--blue); padding:40px; box-shadow:0 0 20px var(--blue); }
        .glitch { animation: glitch 1s infinite; font-size: 30px; }

        /* CONTENEDORES */
        .container { max-width:450px; margin:20px auto; padding:15px; border:1px solid #222; border-radius:15px; background:#0a0a0a; }
        .pink-btn { border:2px solid var(--pink); color:var(--pink); background:transparent; padding:10px; cursor:pointer; font-weight:bold; width:90%; transition:0.3s; }
        .pink-btn:hover { box-shadow:0 0 20px var(--pink); background:var(--pink); color:white; }
        
        /* GOD MODE */
        .god-mode { position:fixed; bottom:10px; right:10px; padding:8px; border:2px solid red; color:red; background:black; cursor:pointer; font-size:10px; }

        @keyframes glitch{ 0%{text-shadow:2px 0 red;} 50%{text-shadow:-2px 0 blue;} 100%{text-shadow:0 0 10px white;} }
    </style>
</head>
<body>

    <div id="interrogation">
        <h1 class="neon-pink">PROTOCOLO +18</h1>
        <p style="max-width:300px;">Comunidad para adultos. Faltas resultan en aislamiento en la SALA DE CASTIGO.</p>
        <button class="pink-btn" onclick="document.getElementById('interrogation').style.display='none'">ACEPTAR Y ENTRAR</button>
    </div>

    <div id="prison">
        <div class="cell">
            <h1 class="neon-pink glitch">HAS SIDO AISLADO</h1>
            <p>Por orden del Creador</p>
        </div>
    </div>

    <div class="container">
        <h2 class="neon-blue">LoveConnect</h2>
        <p>Usuario: <b>{{ user }}</b> <span class="neon-pink">LvL: {{ lvl }}</span></p>

        <div style="border:1px dashed var(--pink); padding:10px; margin-bottom:15px;">
            <h3 class="neon-pink">Zona de Videos</h3>
            <p style="font-size:10px; color:gray;">⚠️ Los videos desaparecen en 5 minutos</p>
            <form action="/upload-video" method="post" enctype="multipart/form-data">
                <input type="file" name="file" style="font-size:10px;">
                <button type="submit" class="pink-btn" style="width:50%; margin-top:5px;">Subir (Premium)</button>
            </form>
        </div>

        <div id="chat" style="text-align:left; height:200px; overflow-y:auto; background:black; padding:10px; border:1px solid #222;">
            {% for m in mensajes %}
                <p><b>{{ m.user }}:</b> {{ m.msg }}</p>
            {% endfor %}
        </div>

        <form action="/send" method="post" style="margin-top:10px;">
            <input type="text" name="msg" placeholder="Mensaje..." style="width:70%; background:#000; color:white; border:1px solid var(--blue); padding:5px;">
            <button type="submit" style="background:var(--blue); border:none; padding:6px;">🚀</button>
        </form>

        {% if user == "Silver676" %}
            <a href="/clear-chat"><button class="god-mode">BORRAR HISTORIAL GRUPAL</button></a>
        {% endif %}
    </div>

</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    u = usuarios_db["Silver676"]
    prison_display = "flex" if u["castigado"] else "none"
    html = HTML_BASE.replace("{{ user }}", "Silver676").replace("{{ lvl }}", u["lvl"]).replace("{{ show_prison }}", prison_display)
    return html

@app.post("/send")
async def send_msg(msg: str = Form(...)):
    mensajes_globales.append({"user": "Silver676", "msg": msg})
    return RedirectResponse("/", status_code=303)

@app.get("/clear-chat")
async def clear_chat():
    mensajes_globales.clear()
    return RedirectResponse("/", status_code=303)

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    # VALIDACIÓN CRÍTICA: Solo Premium
    user_type = usuarios_db["Silver676"]["tipo"]
    if user_type != "Premium":
        return {"error": "Solo usuarios Premium pueden subir videos."}
    
    if len(videos_db) >= VIDEO_LIMIT:
        return {"error": "Límite de 10 videos alcanzado. Espera a que expiren."}

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
