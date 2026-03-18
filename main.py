import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_final_2026")

# --- ALMACENAMIENTO DE DATOS ---
CHAT = []
SUGERENCIAS = []
USUARIO_ADMIN = "silver breaker"
CLAVE_ADMIN = "123"

# --- ESTÉTICA CHATGPT + PAYPAL ---
ESTILOS = """
<style>
    body { background: #0b0b0f; color: #ececf1; font-family: 'Inter', sans-serif; margin: 0; display: flex; justify-content: center; }
    .app-container { width: 100%; max-width: 600px; min-height: 100vh; display: flex; flex-direction: column; padding: 10px; box-sizing: border-box; }
    .neon-logo { color: #00f7ff; text-shadow: 0 0 15px #00f7ff; text-align: center; letter-spacing: 2px; }
    
    /* Cards de Planes */
    .plan-container { display: flex; gap: 10px; margin: 15px 0; }
    .plan-card { flex: 1; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #3e3e4a; }
    .plan-card.basic { border-color: #00f7ff33; color: #00f7ff; background: #00f7ff0a; }
    .plan-card.premium { border-color: #ff00c8; color: #ff00c8; background: #ff00c80a; position: relative; }
    
    /* Botón PayPal */
    .btn-pay { background: #ffb800; color: #111; border: none; padding: 8px 12px; border-radius: 20px; font-weight: bold; cursor: pointer; font-size: 11px; margin-top: 10px; display: inline-block; text-decoration: none; }
    
    /* Chat Area */
    .chat-area { flex-grow: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
    .message-row { max-width: 85%; padding: 12px; border-radius: 15px; background: #2d2d3a; border-left: 3px solid #00f7ff; margin-bottom: 5px; }
    .meta-user { font-size: 10px; color: #00f7ff; font-weight: bold; display: block; margin-bottom: 4px; }

    /* Input Moderno */
    .footer-input { background: #0b0b0f; padding: 15px; border-top: 1px solid #2d2d3a; position: sticky; bottom: 0; }
    .input-wrapper { background: #202123; border: 1px solid #565869; border-radius: 12px; display: flex; align-items: center; padding: 5px 15px; }
    input { background: transparent; border: none; color: white; padding: 12px; flex-grow: 1; outline: none; }
    
    .overlay-18 { text-align: center; padding: 50px 20px; background: #000; min-height: 100vh; }
    .btn-pink { background: #ff00c8; color: white; border: none; padding: 15px 30px; border-radius: 30px; font-weight: bold; cursor: pointer; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def main(request: Request):
    user = request.session.get("u")
    plus18 = request.session.get("plus18")

    if not user:
        return f"""<html>{ESTILOS}<body><div class="app-container" style="justify-content:center; text-align:center;">
            <h1 class="neon-logo">LOVE CONNECT</h1>
            <form action="/login" method="post" style="display:flex; flex-direction:column; gap:10px;">
                <input name="u" placeholder="Usuario" required>
                <input name="p" type="password" placeholder="Clave" required>
                <button class="btn-pink">ENTRAR</button>
            </form></div></body></html>"""

    if not plus18:
        return f"""<html>{ESTILOS}<body><div class="overlay-18">
            <h1 style="color:#ff00c8;">SISTEMA +18</h1>
            <p>Acceso restringido para adultos.</p>
            <a href="/accept_18"><button class="btn-pink">CONFIRMAR MAYORÍA DE EDAD</button></a>
        </div></body></html>"""

    # VISTA DE CHAT
    msjs_html = "".join([f'<div class="message-row"><span class="meta-user">{m["u"]}</span>{m["m"]}</div>' for m in CHAT])
    
    return f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>{ESTILOS}<body>
    <div class="app-container">
        <h1 class="neon-logo" style="font-size:18px;">LOVE CONNECT</h1>

        <div class="plan-container">
            <div class="plan-card basic"><b>BÁSICO</b><br><small>Chat Activo</small></div>
            <div class="plan-card premium">
                <b>PREMIUM</b><br><small>Videos y más</small><br>
                <a href="https://www.paypal.me/silver676" target="_blank" class="btn-pay">PAGAR CON PAYPAL</a>
            </div>
        </div>

        <div class="chat-area">
            {msjs_html if CHAT else '<p style="color:gray; text-align:center;">No hay mensajes aún.</p>'}
        </div>

        <div class="footer-input">
            <form action="/send" method="post" class="input-wrapper">
                <input name="m" placeholder="Escribe un mensaje..." required autocomplete="off">
                <button style="background:none; border:none; cursor:pointer; font-size:20px;">🚀</button>
            </form>
            <form action="/suggest" method="post" style="margin-top:10px; display:flex; gap:5px;">
                <input name="s" placeholder="Mejorar la app..." style="font-size:11px; padding:5px; background:#1a1a1a; border-radius:5px;">
                <button style="background:#444; color:white; border:none; border-radius:5px; font-size:11px; padding:0 10px;">Pedir</button>
            </form>
            <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:10px;">
                <a href="/admin/sugerencias" style="color:#00f7ff; text-decoration:none;">[VER SUGERENCIAS]</a>
                <a href="/clear" style="color:red; text-decoration:none;">[LIMPIAR]</a>
                <a href="/logout" style="color:gray; text-decoration:none;">Salir</a>
            </div>
        </div>
    </div></body></html>"""

# --- RUTAS DE ADMINISTRACIÓN ---

@app.get("/admin/sugerencias", response_class=HTMLResponse)
async def ver_sugerencias(request: Request):
    if request.session.get("u") != "Silver Breaker":
        return RedirectResponse("/")
    
    lista = "".join([f"<li><b>{s['u']}:</b> {s['s']}</li>" for s in SUGERENCIAS])
    return f"""<html>{ESTILOS}<body><div class="app-container">
        <h2 class="neon-logo">SUGERENCIAS RECIBIDAS</h2>
        <ul style="color:white; background:#111; padding:20px; border-radius:10px;">
            {lista if SUGERENCIAS else "No hay sugerencias todavía."}
        </ul>
        <a href="/" style="color:#00f7ff; text-align:center; display:block;">Volver al Chat</a>
    </div></body></html>"""

# --- LOGICA DE FUNCIONAMIENTO ---

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    if u.lower().strip() == USUARIO_ADMIN and p == CLAVE_ADMIN:
        request.session["u"] = "Silver Breaker"
        return RedirectResponse("/", status_code=303)
    return RedirectResponse("/", status_code=303)

@app.get("/accept_18")
async def accept_18(request: Request):
    request.session["plus18"] = True
    return RedirectResponse("/", status_code=303)

@app.post("/send")
async def send(request: Request, m: str = Form(...)):
    if request.session.get("u"):
        CHAT.append({"u": request.session["u"], "m": m})
    return RedirectResponse("/", status_code=303)

@app.post("/suggest")
async def suggest(request: Request, s: str = Form(...)):
    if request.session.get("u"):
        SUGERENCIAS.append({"u": request.session["u"], "s": s})
    return RedirectResponse("/", status_code=303)

@app.get("/clear")
async def clear():
    CHAT.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
