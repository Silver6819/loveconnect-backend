import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_ultra_minimalist_2026")

# --- BASE DE DATOS TEMPORAL (Se limpia si reinicias Render) ---
CHAT_GLOBAL = []
MENSAJES_PRIVADOS = [] # Estructura: {"de": "user1", "para": "user2", "m": "hola"}
GALERIA_VIDEOS = []   # Estructura: {"u": "user1", "link": "url_video"}
SUGERENCIAS = []
USUARIO_ADMIN = "silver breaker"
CLAVE_ADMIN = "123"

# --- ESTÉTICA EXTREMADAMENTE LIGERA ---
ESTILOS = """
<style>
    body { background: #0b0b0f; color: #ececf1; font-family: sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; }
    .app-container { width: 100%; max-width: 500px; min-height: 100vh; display: flex; flex-direction: column; background: #000; border: 1px solid #1a1a1a; }
    .neon-logo { color: #00f7ff; text-shadow: 0 0 10px #00f7ff; text-align: center; font-size: 18px; padding: 10px 0; margin: 0; }
    
    /* Sistema de Pestañas */
    .tabs { display: flex; background: #111; border-bottom: 1px solid #2d2d3a; }
    .tab { flex: 1; padding: 12px; text-align: center; color: gray; cursor: pointer; text-decoration: none; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .tab.active { color: #ff00c8; border-bottom: 2px solid #ff00c8; background: #16161d; }

    /* Áreas de Contenido */
    .content-area { flex-grow: 1; padding: 15px; overflow-y: auto; height: 350px; }
    .msg-bubble { background: #16161d; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 3px solid #00f7ff; }
    .msg-meta { font-size: 10px; color: #00f7ff; font-weight: bold; margin-bottom: 3px; display: block; }
    .private-bubble { border-left-color: #ff00c8; background: #1a0012; }

    /* Galería de Videos */
    .video-card { background: #111; border: 1px solid #333; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
    .video-iframe-container { position: relative; width: 100%; height: 0; padding-bottom: 56.25%; border-radius: 5px; overflow: hidden; }
    .video-iframe-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }

    /* Footer y Formularios */
    .footer { padding: 10px; background: #0b0b0f; border-top: 1px solid #2d2d3a; position: sticky; bottom: 0; }
    .input-row { display: flex; gap: 5px; background: #16161d; padding: 5px; border-radius: 8px; border: 1px solid #333; }
    input { background: transparent; border: none; color: white; padding: 8px; flex-grow: 1; outline: none; font-size: 13px; }
    .btn-send { background: none; border: none; color: #00f7ff; font-size: 18px; cursor: pointer; padding: 0 10px; }
    .btn-pay { background: #ffc439; color: #003087; padding: 10px; border-radius: 20px; text-decoration: none; font-size: 11px; font-weight: bold; display: block; text-align: center; margin-top: 8px; transition: 0.2s; }
    .btn-pay:active { transform: translateY(1px); }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def main_interface(request: Request, tab: str = "chat"):
    user = request.session.get("u")
    if not user: return RedirectResponse("/login")
    if not request.session.get("plus18"): return RedirectResponse("/check18")

    # Contenido dinámico según la pestaña activa
    content = ""
    form_action = "/send"
    placeholder = "Escribe al mundo..."
    
    if tab == "chat":
        # CHAT GLOBAL
        msjs = "".join([f'<div class="msg-bubble"><span class="msg-meta">{m["u"]}</span>{m["m"]}</div>' for m in CHAT_GLOBAL])
        content = f'<div class="content-area">{msjs if CHAT_GLOBAL else "<p style=\'color:gray; text-align:center;\'>Canal despejado.</p>"}</div>'
    
    elif tab == "privados":
        # CHATS PRIVADOS (Muestra solo los mensajes de/para el usuario)
        mis_privados = [m for m in MENSAJES_PRIVADOS if m['de'] == user or m['para'] == user]
        msjs = "".join([f'<div class="msg-bubble private-bubble"><span class="msg-meta" style="color:#ff00c8;">{m["de"]} → {m["para"]}</span>{m["m"]}</div>' for m in mis_privados])
        content = f"""<div class="content-area">
            <form action="/send_private" method="post" class="input-row" style="margin-bottom:10px;">
                <input name="para" placeholder="Nombre del usuario..." required style="width:30%; flex-grow:0; border-right:1px solid #333;">
                <input name="m" placeholder="Mensaje privado..." required>
                <button class="btn-send">📩</button>
            </form>
            {msjs if mis_privados else "<p style=\'color:gray; text-align:center; font-size:11px;\'>Formato: [NombreUsuario] [Mensaje]. <br>No tienes mensajes privados.</p>"}
        </div>"""
        form_action = None # Desactiva el formulario del footer para esta pestaña

    elif tab == "videos":
        # GALERÍA DE VIDEOS (Reproduce links externos)
        videos_html = ""
        for v in GALERIA_VIDEOS:
            link = v['link']
            # Lógica minimalista para incrustar YouTube (puedes añadir TikTok/Drive luego)
            if "youtube.com/watch?v=" in link:
                video_id = link.split("v=")[1]
                embed_url = f"https://www.youtube.com/embed/{video_id}"
                videos_html += f'<div class="video-card"><span class="msg-meta">{v["u"]} subió:</span><div class="video-iframe-container"><iframe src="{embed_url}" allowfullscreen></iframe></div></div>'
            else:
                videos_html += f'<div class="video-card"><span class="msg-meta">{v["u"]} compartió link:</span><a href="{link}" target="_blank" style="color:#00f7ff; font-size:12px;">{link}</a></div>'
        
        content = f'<div class="content-area">{videos_html if GALERIA_VIDEOS else "<p style=\'color:gray; text-align:center;\'>Galería de videos vacía.</p>"}</div>'
        form_action = "/upload_video"
        placeholder = "Pega enlace de YouTube, TikTok, Drive..."

    # Constructor de la Interfaz con Pestañas
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"></head>{ESTILOS}<body>
    <div class="app-container">
        <h1 class="neon-logo">LOVE CONNECT</h1>
        
        <div class="tabs">
            <a href="/?tab=chat" class="tab {"active" if tab=="chat" else ""}">GLOBAL</a>
            <a href="/?tab=privados" class="tab {"active" if tab=="privados" else ""}">PRIVADOS</a>
            <a href="/?tab=videos" class="tab {"active" if tab=="videos" else ""}">VIDEOS VIP</a>
        </div>

        {content}

        <div class="footer">
            {f'<form action="{form_action}" method="post" class="input-row"><input name="data" placeholder="{placeholder}" required autocomplete="off"><button class="btn-send">🚀</button></form>' if form_action else ""}
            <a href="https://www.paypal.me/silver676" target="_blank" class="btn-pay">💎 ACTIVAR PREMIUM VIP</a>
            <div style="text-align:center; font-size:9px; margin-top:8px; display:flex; justify-content:space-between;">
                <a href="/admin/sugerencias" style="color:#00f7ff; text-decoration:none;">Mejoras</a>
                <a href="/logout" style="color:gray; text-decoration:none;">Cerrar Sesión (Silver Breaker)</a>
            </div>
        </div>
    </div></body></html>"""

# --- LÓGICA DE ACCIONES Y SEGURIDAD ---

@app.get("/login", response_class=HTMLResponse)
async def login_p():
    return f"<html>{ESTILOS}<body style='display:flex; align-items:center; justify-content:center; background:#000;'><form action='/login' method='post' style='background:#111; padding:30px; border-radius:15px; text-align:center; border:1px solid #333; width:80%;'><h2 class='neon-logo' style='font-size:25px;'>INGRESAR</h2><input name='u' placeholder='Usuario' required style='background:#16161d; margin-bottom:10px; padding:15px; width:100%; border-radius:8px; border:1px solid #333; color:white;'><br><input name='p' type='password' placeholder='Contraseña' required style='background:#16161d; margin-bottom:15px; padding:15px; width:100%; border-radius:8px; border:1px solid #333; color:white;'><br><button style='background:#ff00c8; color:white; border:none; padding:15px 20px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer;'>ENTRAR A LOVE CONNECT</button></form></body></html>"

@app.post("/login")
async def login(u: str = Form(...), p: str = Form(...), request: Request = None):
    if u.lower().strip() == USUARIO_ADMIN and p == CLAVE_ADMIN:
        request.session["u"] = "Silver Breaker"
    return RedirectResponse("/", status_code=303)

@app.get("/check18", response_class=HTMLResponse)
async def check18():
    return f"<html>{ESTILOS}<body style='display:flex; align-items:center; justify-content:center; text-align:center; background:#000;'><div style='border:2px solid #ff00c8; padding:30px; border-radius:20px; background:#111; box-shadow: 0 0 20px #ff00c844;'><h1 style='color:#ff00c8; margin:0;'>PROTOCOLO +18</h1><p style='color:#ccc; margin:15px 0;'>Contenido solo para adultos.<br>El respeto es obligatorio.</p><a href='/accept_18' style='background:#ff00c8; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block;'>ACEPTAR Y ENTRAR</a></div></body></html>"

@app.get("/accept_18")
async def accept_18(request: Request):
    request.session["plus18"] = True
    return RedirectResponse("/")

@app.post("/send")
async def send_global(data: str = Form(...), request: Request = None):
    user = request.session.get("u")
    if user: CHAT_GLOBAL.append({"u": user, "m": data})
    return RedirectResponse("/?tab=chat", status_code=303)

@app.post("/send_private")
async def send_private(para: str = Form(...), m: str = Form(...), request: Request = None):
    de = request.session.get("u")
    if de: MENSAJES_PRIVADOS.append({"de": de, "para": para.strip(), "m": m})
    return RedirectResponse("/?tab=privados", status_code=303)

@app.post("/upload_video")
async def upload_video(data: str = Form(...), request: Request = None):
    user = request.session.get("u")
    if user: GALERIA_VIDEOS.append({"u": user, "link": data.strip()})
    return RedirectResponse("/?tab=videos", status_code=303)

@app.get("/admin/sugerencias", response_class=HTMLResponse)
async def admin_view(request: Request):
    if request.session.get("u") != "Silver Breaker": return RedirectResponse("/")
    sug_list = "".join([f"<li style='margin-bottom:10px; color:white; border-bottom:1px solid #333;'>{s['s']}</li>" for s in SUGERENCIAS])
    return f"<html>{ESTILOS}<body><div class='app-container'><h2 class='neon-logo'>MEJORAS SOLICITADAS</h2><ul style='background:#1a1a1a; padding:20px; border-radius:10px; list-style:none;'>{sug_list if SUGERENCIAS else 'No hay peticiones.'}</ul><br><a href='/' style='color:#00f7ff; text-align:center; display:block; text-decoration:none;'>VOLVER AL CHAT</a></div></body></html>"

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")
