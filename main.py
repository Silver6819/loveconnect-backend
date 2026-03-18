from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_ultra_reset")

# CHAT Y CREDENCIALES
CHAT = []
USUARIO_CORRECTO = "silver breaker" # Lo compararemos en minúsculas para que no falle
CLAVE_CORRECTA = "123" # Clave ultra corta

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    user = request.session.get("u")
    if not user:
        return """
        <body style="background:#000; color:#ff00c8; text-align:center; padding-top:50px; font-family:sans-serif;">
            <h1>❤️ LOVE CONNECT</h1>
            <p style="color:gray;">Acceso para: Silver Breaker</p>
            <form action="/login" method="post" style="display:inline-block; background:#111; padding:20px; border-radius:10px;">
                <input name="u" placeholder="Usuario" required style="padding:10px;"><br><br>
                <input name="p" type="password" placeholder="Clave" required style="padding:10px;"><br><br>
                <button style="background:#ff00c8; color:white; border:none; padding:10px 20px; cursor:pointer;">ENTRAR</button>
            </form>
        </body>
        """
    msjs = "".join([f"<p style='color:white;'><b>{m['u']}:</b> {m['m']}</p>" for m in CHAT])
    return f"""
    <body style="background:#000; color:white; font-family:sans-serif; padding:20px;">
        <h2 style="color:#00f7ff;">Panel: {user}</h2>
        <div style="background:#111; height:200px; overflow-y:auto; padding:10px; border:1px solid #333;">{msjs if CHAT else 'Limpio.'}</div><br>
        <form action="/enviar" method="post"><input name="m" style="width:70%; padding:10px;"><button>🚀</button></form><br>
        <a href="/limpiar" style="color:red;">[BORRAR CHAT]</a> | <a href="/salir" style="color:gray;">Salir</a>
    </body>
    """

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    # .lower() hace que no importe si escribes SILVER o silver
    if u.lower().strip() == USUARIO_CORRECTO and p == CLAVE_CORRECTA:
        request.session["u"] = "Silver Breaker"
        return RedirectResponse("/", status_code=303)
    # Si falla, te dice qué escribiste para que sepas el error
    return HTMLResponse(f"<body style='background:black;color:red;'><h2>Clave '{p}' incorrecta para '{u}'</h2><a href='/'>Volver</a></body>")

@app.post("/enviar")
async def enviar(request: Request, m: str = Form(...)):
    if request.session.get("u"): CHAT.append({"u": request.session["u"], "m": m})
    return RedirectResponse("/", status_code=303)

@app.get("/limpiar")
async def limpiar():
    CHAT.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/salir")
async def salir(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
