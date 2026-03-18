import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_omega_2026")

# --- BASE DE DATOS TEMPORAL ---
CHAT = []
SUGERENCIAS = []
USUARIO_ADMIN = "silver breaker"
CLAVE_ADMIN = "123"

# --- ESTILOS NEÓN Y CHATGPT ---
ESTILOS = """
<style>
    body { background: #050505; color: #e0e0e0; font-family: 'Segoie UI', sans-serif; margin: 0; display: flex; justify-content: center; }
    .app-container { width: 100%; max-width: 500px; background: #0a0a0a; min-height: 100vh; padding: 20px; border-left: 1px solid #1a1a1a; border-right: 1px solid #1a1a1a; }
    .neon-text { color: #00f7ff; text-shadow: 0 0 10px #00f7ff; }
    .card-plus18 { background: #000; border: 2px solid #ff00c8; padding: 30px; border-radius: 15px; text-align: center; margin-top: 50px; }
    .btn-premium { background: #ff00c8; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; cursor: pointer; width: 100%; }
    .chat-box { background: #111; border-radius: 10px; height: 350px; overflow-y: auto; padding: 15px; border: 1px solid #222; margin-bottom: 15px; }
    .msg { margin-bottom: 10px; padding: 10px; border-radius: 8px; background: #1a1a1a; border-left: 4px solid #00f7ff; }
    .input-group { display: flex; gap: 10px; margin-bottom: 20px; }
    input { background: #1a1a1a; border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; flex-grow: 1; }
    .plan-box { display: flex; gap: 10px; margin-bottom: 15px; }
    .plan { flex: 1; padding: 10px; border-radius: 8px; font-size: 12px; text-align: center; border: 1px solid #333; }
    .basic { border-color: #00f7ff; color: #00f7ff; }
    .premium { border-color: #ff00c8; color: #ff00c8; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("u")
    plus18 = request.session.get("plus18")

    if not user:
        return f"""<html>{ESTILOS}<body><div class="app-container">
            <h1 style="color:#ff00c8; text-align:center;">❤️ LoveConnect</h1>
            <form action="/login" method="post" style="display:flex; flex-direction:column; gap:10px;">
                <input name="u" placeholder="Usuario (Silver Breaker)" required>
                <input name="p" type="password" placeholder="Contraseña" required>
                <button class="btn-premium">ENTRAR</button>
            </form></div></body></html>"""

    if not plus18:
        return f"""<html>{ESTILOS}<body><div class="app-container">
            <div class="card-plus18">
                <h1 style="color:#ff00c8;">PROTOCOLO +18</h1>
                <p>Comunidad para adultos. Faltas resultan en aislamiento.</p>
                <a href="/accept_plus18" style="text-decoration:none;"><button class="btn-premium">ACEPTAR Y ENTRAR</button></a>
            </div></div></body></html>"""

    # VISTA PRINCIPAL
    msjs_html = "".join([f"<div class='msg'><b>{m['u']}:</b> {m['m']}</div>" for m in CHAT])
    return f"""<html>{ESTILOS}<body><div class="app-container">
        <h2 class="neon-text">LOVE CONNECT <span style="font-size:12px; color:gray;">[User: {user}]</span></h2>
        
        <div class="plan-box">
            <div class="plan basic"><b>Básico</b><br>Chat Ilimitado</div>
            <div class="plan premium"><b>Premium</b><br>Todo + Videos</div>
        </div>

        <div class="chat-box">{msjs_html if CHAT else "No hay mensajes en el mundo..."}</div>
        
        <form action="/send" method="post" class="input-group">
            <input name="m" placeholder="Escribe al mundo..." required>
            <button style="background:#00f7ff; border:none; border-radius:8px; padding:10px;">🚀</button>
        </form>

        <form action="/sugerencia" method="post" class="input-group" style="background:#111; padding:10px; border-radius:8px;">
            <input name="s" placeholder="Sugerir mejora..." style="font-size:12px;">
            <button style="background:white; color:black; border:none; padding:5px 10px; border-radius:5px; font-size:12px;">Pedir</button>
        </form>

        <div style="text-align:center; margin-top:20px;">
            <a href="/clear" style="color:red; font-size:12px; text-decoration:none;">[BORRAR HISTORIAL]</a> | 
            <a href="/logout" style="color:gray; font-size:12px; text-decoration:none;">Cerrar Sesión</a>
        </div>
    </div></body></html>"""

# --- RUTAS DE ACCIÓN ---

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    if u.lower().strip() == USUARIO_ADMIN and p == CLAVE_ADMIN:
        request.session["u"] = "Silver Breaker"
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/", status_code=303)

@app.get("/accept_plus18")
async def accept(request: Request):
    request.session["plus18"] = True
    return RedirectResponse("/", status_code=303)

@app.post("/send")
async def send(request: Request, m: str = Form(...)):
    if request.session.get("u"):
        CHAT.append({"u": request.session["u"], "m": m})
    return RedirectResponse("/", status_code=303)

@app.post("/sugerencia")
async def sugerencia(request: Request, s: str = Form(...)):
    if request.session.get("u"):
        SUGERENCIAS.append({"user": request.session["u"], "idea": s})
    return RedirectResponse("/", status_code=303)

@app.get("/clear")
async def clear():
    CHAT.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
