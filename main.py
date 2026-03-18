from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Llave de seguridad para la sesión
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_reset_2026")

# --- CONFIGURACIÓN DE ACCESO REAL ---
# Usuario: Silver Breaker | Clave: 0000
CREDENCIALES = {"usuario": "Silver Breaker", "clave": "0000"}
CHAT = []

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    user = request.session.get("u")
    if not user:
        return """
        <body style="background:#000; color:#ff00c8; text-align:center; padding-top:50px; font-family:sans-serif;">
            <h1>❤️ LOVE CONNECT</h1>
            <p style="color:#00f7ff;">Identidad: Silver Breaker</p>
            <form action="/login" method="post" style="display:inline-block; background:#111; padding:20px; border-radius:10px; border: 1px solid #222;">
                <input name="u" placeholder="Nombre de Usuario" style="margin:5px; padding:12px; width:200px;"><br>
                <input name="p" type="password" placeholder="Contraseña" style="margin:5px; padding:12px; width:200px;"><br>
                <button style="background:#ff00c8; color:white; border:none; padding:10px 20px; cursor:pointer; font-weight:bold; width:100%; margin-top:10px;">ENTRAR</button>
            </form>
        </body>
        """
    
    # Renderizado simple de mensajes
    historial = "".join([f"<p style='color:white; border-bottom:1px solid #222; padding:5px;'><b>{m['u']}:</b> {m['m']}</p>" for m in CHAT])
    
    return f"""
    <body style="background:#000; color:white; font-family:sans-serif; padding:20px;">
        <h2 style="color:#00f7ff;">Bienvenido, {user} (Creador)</h2>
        <div style="background:#111; height:250px; overflow-y:auto; padding:15px; border:1px solid #333; border-radius:10px;">
            {historial if CHAT else "<p style='color:gray;'>El servidor ha sido limpiado. No hay mensajes.</p>"}
        </div><br>
        <form action="/enviar" method="post" style="display:flex; gap:10px;">
            <input name="m" placeholder="Escribir mensaje grupal..." style="flex-grow:1; padding:12px; background:#000; color:white; border:1px solid #00f7ff;">
            <button style="padding:12px 20px; background:#00f7ff; border:none; font-weight:bold; cursor:pointer;">🚀</button>
        </form><br>
        <div style="margin-top:20px; border-top:1px solid #222; padding-top:10px;">
            <a href="/limpiar" style="color:red; text-decoration:none; font-weight:bold;">[🔥 BORRAR TODO EL CHAT]</a> 
            <span style="color:#333; margin: 0 10px;">|</span>
            <a href="/salir" style="color:gray; text-decoration:none;">Cerrar Sesión</a>
        </div>
    </body>
    """

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    # Verificación estricta con tu nombre
    if u == CREDENCIALES["usuario"] and p == CREDENCIALES["clave"]:
        request.session["u"] = u
        return RedirectResponse("/", status_code=303)
    return HTMLResponse("<body style='background:black;color:red;text-align:center;padding-top:50px;'><h2>Acceso Denegado</h2><p>Verifica el nombre Silver Breaker y la clave.</p><a href='/'>Volver a intentar</a></body>")

@app.post("/enviar")
async def enviar(request: Request, m: str = Form(...)):
    if request.session.get("u"):
        CHAT.append({"u": request.session["u"], "m": m})
    return RedirectResponse("/", status_code=303)

@app.get("/limpiar")
async def limpiar(request: Request):
    # Solo tú puedes limpiar
    if request.session.get("u") == "Silver Breaker":
        CHAT.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/salir")
async def salir(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
