import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Middleware para manejar las sesiones de usuario
app.add_middleware(SessionMiddleware, secret_key="debug_key_silver_2026")

# Base de datos temporal (Se borra si reinicias Render)
USUARIOS = {"silver breaker": "123"} 
CHAT = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("u")
    if not user: 
        return RedirectResponse("/login", status_code=303)
    
    mensajes = "".join([f"<li><b>{m['u']}:</b> {m['m']}</li>" for m in CHAT])
    return f"""
    <html><body>
        <h1>LoveConnect - MODO PRUEBA</h1>
        <p>Usuario actual: {user} | <a href="/logout">Cerrar Sesion</a></p>
        <hr>
        <ul>{mensajes if CHAT else "No hay mensajes."}</ul>
        <form action="/send" method="post">
            <input name="msg" placeholder="Mensaje" required>
            <button type="submit">Enviar</button>
        </form>
    </body></html>
    """

@app.get("/login", response_class=HTMLResponse)
async def login_p():
    return """
    <html><body>
        <h2>Ingresar</h2>
        <form action="/login" method="post">
            <input name="u" placeholder="Usuario" required><br>
            <input name="p" type="password" placeholder="Clave" required><br>
            <button type="submit">Entrar</button>
        </form>
        <p><a href="/signup">Registrarse</a></p>
    </body></html>
    """

@app.post("/login")
async def login_logic(request: Request, u: str = Form(...), p: str = Form(...)):
    u_key = u.lower().strip()
    if u_key in USUARIOS and USUARIOS[u_key] == p:
        request.session["u"] = u
        return RedirectResponse("/", status_code=303)
    return "Error: Credenciales invalidas. <a href='/login'>Volver</a>"

@app.get("/signup", response_class=HTMLResponse)
async def signup_p():
    return """
    <html><body>
        <h2>Crear Cuenta</h2>
        <form action="/signup" method="post">
            <input name="u" placeholder="Nuevo Usuario" required><br>
            <input name="p" type="password" placeholder="Nueva Clave" required><br>
            <button type="submit">Registrar</button>
        </form>
        <p><a href="/login">Ya tengo cuenta</a></p>
    </body></html>
    """

@app.post("/signup")
async def signup_logic(u: str = Form(...), p: str = Form(...)):
    u_key = u.lower().strip()
    if u_key not in USUARIOS:
        USUARIOS[u_key] = p
        return RedirectResponse("/login", status_code=303)
    return "El usuario ya existe. <a href='/signup'>Volver</a>"

@app.post("/send")
async def send_msg(request: Request, msg: str = Form(...)):
    user = request.session.get("u")
    if user:
        CHAT.append({"u": user, "m": msg})
    return RedirectResponse("/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
