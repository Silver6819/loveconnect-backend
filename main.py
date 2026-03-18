import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_multimedia_2026")

# --- ALMACENAMIENTO ---
CHAT_GLOBAL = [] # Mensajes ilimitados
GALERIA = []     # Enlaces de fotos
SUGERENCIAS = []
USUARIO_ADMIN = "silver breaker"
CLAVE_ADMIN = "123"

ESTILOS = """
<style>
    body { background: #0b0b0f; color: #ececf1; font-family: 'Inter', sans-serif; margin: 0; }
    .app-container { max-width: 600px; margin: auto; min-height: 100vh; display: flex; flex-direction: column; border-left: 1px solid #2d2d3a; border-right: 1px solid #2d2d3a; }
    .neon-logo { color: #00f7ff; text-shadow: 0 0 15px #00f7ff; text-align: center; padding: 15px; font-size: 22px; }
    
    /* Pestañas */
    .tabs { display: flex; background: #16161d; border-bottom: 1px solid #2d2d3a; }
    .tab { flex: 1; padding: 15px; text-align: center; color: gray; cursor: pointer; text-decoration: none; font-size: 13px; font-weight: bold; }
    .tab.active { color: #ff00c8; border-bottom: 2px solid #ff00c8; }

    /* Galería */
    .gallery-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; padding: 15px; }
    .photo-card { border-radius: 10px; overflow: hidden; border: 1px solid #333; background: #111; }
    .photo-card img { width: 100%; height: 150px; object-fit: cover; }

    /* Chat */
    .chat-area { flex-grow: 1; padding: 15px; overflow-y: auto; height: 400px; }
    .msg { background: #202123; border-radius: 12px; padding: 12px; margin-bottom: 10px; border-left: 4px solid #00f7ff; }
    
    /* Footer */
    .footer { padding: 15px; background: #0b0b0f; border-top: 1px solid #2d2d3a; position: sticky; bottom: 0; }
    .input-row { display: flex; gap: 8px; background: #2d2d3a; padding: 8px; border-radius: 10px; }
    input { background: transparent; border: none; color: white; flex-grow: 1; outline: none; }
    .btn-pay { background: #ffc439; color: #003087; padding: 8px; border-radius: 20px; text-decoration: none; font-size: 11px; font-weight: bold; display: block; text-align: center; margin-top: 5px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, tab: str = "chat"):
    user = request.session.get("u")
    if not user: return RedirectResponse("/login_page")
    if not request.session.get("plus18"): return RedirectResponse("/check18")

    # Contenido según la pestaña
    content = ""
    if tab == "chat":
        msjs = "".join([f'<div class="msg"><b style="color:#00f7ff; font-size:11px;">{m["u"]}</b><br>{m["m"]}</div>' for m in CHAT_GLOBAL])
        content = f'<div class="chat-area">{msjs if CHAT_GLOBAL else "No hay mensajes..."}</div>'
    else:
        fotos = "".join([f'<div class="photo-card"><img src="{f}"></div>' for f in GALERIA])
        content = f'<div class="gallery-grid">{fotos if GALERIA else "Galería vacía..."}</div>'

    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>{ESTILOS}<body>
    <div class="app-container">
        <h1 class="neon-logo">LOVE CONNECT</h1>
        <div class="tabs">
            <a href="/?tab=chat" class="tab {"active" if tab=="chat" else ""}">CHAT GLOBAL</a>
            <a href="/?tab=fotos" class="tab {"active" if tab=="fotos" else ""}">GALERÍA VIP</a>
        </div>

        {content}

        <div class="footer">
            {"" if tab=="chat" else ""}
            <form action="/{"send" if tab=="chat" else "upload"}" method="post" class="input-row">
                <input name="data" placeholder="{"Escribe un mensaje..." if tab=="chat" else "Pega link de foto..."}" required>
                <button style="background:none; border:none; color:#00f7ff; font-size:20px;">🚀</button>
            </form>
            
            <div style="margin-top:10px; display:flex; gap:10px; align-items:center;">
                <div style="flex:1;"><a href="https://www.paypal.me/silver676" target="_blank" class="btn-pay">💎 SUBIR A PREMIUM</a></div>
                <div style="flex:1; font-size:10px; text-align:right;">
                    <a href="/logout" style="color:gray;">Cerrar Sesión</a>
                </div>
            </div>
        </div>
    </div></body></html>"""

# --- RUTAS DE ACCIÓN ---

@app.get("/login_page", response_class=HTMLResponse)
async def login_p():
    return f"<html>{ESTILOS}<body style='display:flex; align-items:center; justify-content:center;'><form action='/login' method='post' style='background:#16161d; padding:30px; border-radius:15px; text-align:center;'><h2 class='neon-logo'>ENTRAR</h2><input name='u' placeholder='Usuario' style='background:#2d2d3a; margin-bottom:10px; padding:10px; width:100%; border-radius:5px; border:none; color:white;'><br><input name='p' type='password' placeholder='Clave' style='background:#2d2d3a; margin-bottom:10px; padding:10px; width:100%; border-radius:5px; border:none; color:white;'><br><button style='background:#ff00c8; color:white; border:none; padding:10px 20px; border-radius:5px; width:100%;'>INGRESAR</button></form></body></html>"

@app.post("/login")
async def login(u: str = Form(...), p: str = Form(...), request: Request = None):
    if u.lower().strip() == USUARIO_ADMIN and p == CLAVE_ADMIN:
        request.session["u"] = "Silver Breaker"
    return RedirectResponse("/", status_code=303)

@app.get("/check18", response_class=HTMLResponse)
async def check18():
    return f"<html>{ESTILOS}<body style='display:flex; align-items:center; justify-content:center; text-align:center;'><div style='border:2px solid #ff00c8; padding:30px; border-radius:20px;'><h1 style='color:#ff00c8;'>+18</h1><p>Contenido Adulto</p><a href='/accept' style='background:#ff00c8; color:white; padding:10px 20px; text-decoration:none; border-radius:10px;'>ACEPTAR</a></div></body></html>"

@app.get("/accept")
async def accept(request: Request):
    request.session["plus18"] = True
    return RedirectResponse("/")

@app.post("/send")
async def send(data: str = Form(...), request: Request = None):
    if request.session.get("u"): CHAT_GLOBAL.append({"u": request.session["u"], "m": data})
    return RedirectResponse("/", status_code=303)

@app.post("/upload")
async def upload(data: str = Form(...), request: Request = None):
    if request.session.get("u"): GALERIA.append(data)
    return RedirectResponse("/?tab=fotos", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")
