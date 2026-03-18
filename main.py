import asyncio
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# --- BASE DE DATOS TEMPORAL ---
VIDEO_LIMIT = 10
EXPIRATION_MINUTES = 5
videos_db = [] 
mensajes_globales = []
sugerencias_db = []

# --- USUARIO MAESTRO ---
# Asegúrate de usar exactamente este nombre al probar
usuarios_db = {
    "Silver676": {"lvl": "∞", "rango": "Creador", "tipo": "Premium", "castigado": False}
}

# --- MOTOR DE LIMPIEZA ---
async def cleanup_videos():
    while True:
        now = datetime.now()
        for v in videos_db[:]:
            if v["expires_at"] < now:
                try:
                    if os.path.exists(v["path"]): os.remove(v["path"])
                except: pass
                videos_db.remove(v)
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_videos())

# --- DISEÑO REPARADO ---
HTML_BASE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LoveConnect v7.3</title>
    <style>
        body { background:#000; color:white; font-family:sans-serif; margin:0; text-align:center; }
        :root { --blue:#00f7ff; --pink:#ff00c8; }
        .neon-blue { color:var(--blue); text-shadow:0 0 10px var(--blue); }
        .neon-pink { color:var(--pink); text-shadow:0 0 10px var(--pink); }
        #interrogation { position:fixed; width:100%; height:100%; background:black; display:flex; 
                         flex-direction:column; justify-content:center; align-items:center; z-index:9999; }
        .container { max-width:450px; margin:10px auto; padding:15px; border:1px solid #222; border-radius:15px; background:#0a0a0a; }
        .pink-btn { border:2px solid var(--pink); color:var(--pink); background:transparent; padding:10px; cursor:pointer; width:95%; font-weight:bold; }
        #chat-box { text-align:left; height:250px; overflow-y:auto; background:black; padding:10px; border:1px solid #111; margin:10px 0; }
        .god-mode { position:fixed; bottom:15px; right:15px; padding:10px; border:2px solid red; color:red; background:black; cursor:pointer; font-size:10px; }
    </style>
</head>
<body>

    <div id="interrogation">
        <h1 class="neon-pink">PROTOCOLO +18</h1>
        <p style="color:#ccc;">Comunidad para adultos.</p>
        <button class="pink-btn" onclick="document.getElementById('interrogation').style.display='none'">ACEPTAR Y ENTRAR</button>
    </div>

    <div class="container">
        <h1 class="neon-blue">LOVE CONNECT</h1>
        <p>Usuario: <b>Silver676</b> <span class="neon-pink">[LvL: ∞]</span></p>

        <div id="chat-box">
            {{ MENSAJES_AQUI }}
        </div>

        <form action="/enviar-mensaje" method="post" style="display:flex; gap:5px;">
            <input type="text" name="msg" placeholder="Mensaje..." style="flex-grow:1; background:#111; color:white; border:1px solid var(--blue); padding:8px;" required>
            <button type="submit" style="background:var(--blue); border:none; padding:8px 15px; cursor:pointer;">🚀</button>
        </form>

        <form action="/enviar-sugerencia" method="post" style="margin-top:15px;">
            <input type="text" name="sug" placeholder="Sugerir mejora..." style="width:60%; background:none; border:1px solid #333; color:white; font-size:10px;">
            <button type="submit" style="font-size:10px; background:#222; color:white; border:none; padding:5px;">Pedir</button>
        </form>

        <a href="/borrar-todo"><button class="god-mode">BORRAR HISTORIAL GRUPAL</button></a>
    </div>
</body>
</html>
"""

# --- RUTAS DE ACCIÓN ---

@app.get("/", response_class=HTMLResponse)
async def home():
    # Creamos el HTML de los mensajes dinámicamente
    msj_html = ""
    for m in mensajes_globales:
        msj_html += f"<p style='margin:5px 0;'><b class='neon-blue'>{m['user']}:</b> {m['msg']} <span style='float:right;'>❤️ 🔗</span></p>"
    
    if not mensajes_globales:
        msj_html = "<p style='color:gray; text-align:center;'>No hay mensajes...</p>"
    
    return HTML_BASE.replace("{{ MENSAJES_AQUI }}", msj_html)

@app.post("/enviar-mensaje")
async def handle_msg(msg: str = Form(...)):
    mensajes_globales.append({"user": "Silver676", "msg": msg})
    return RedirectResponse(url="/", status_code=303)

@app.post("/enviar-sugerencia")
async def handle_sug(sug: str = Form(...)):
    sugerencias_db.append(sug)
    # Podríamos imprimirlo en consola para que lo veas en Render
    print(f"NUEVA SUGERENCIA: {sug}")
    return RedirectResponse(url="/", status_code=303)

@app.get("/borrar-todo")
async def handle_clear():
    mensajes_globales.clear()
    return RedirectResponse(url="/", status_code=303)

@app.post("/upload-video")
async def handle_video(file: UploadFile = File(...)):
    # Lógica de video simplificada para estabilidad
    path = f"static/videos/{file.filename}"
    with open(path, "wb") as f: f.write(await file.read())
    videos_db.append({"path": path, "expires_at": datetime.now() + timedelta(minutes=5)})
    return RedirectResponse(url="/", status_code=303)
