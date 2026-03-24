import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Llave secreta para que la sesión no falle
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_debug_2026")

# Base de datos temporal para pruebas
USUARIOS = {"silver breaker": "123"} 

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("u")
    if not user: 
        return RedirectResponse("/login", status_code=303)
    
    return f"""
    <html><body>
        <h1>Bienvenido, {user}</h1>
        <p>Estás dentro de LoveConnect (Modo Vanilla)</p>
        <a href="/logout">Cerrar Sesión</a>
    </body></html>
    """

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    return """
    <html><body>
        <h2>Ingresar</h2>
        <form action="/login" method="post">
            <input name="u" placeholder="Usuario" required><br>
            <input name="p" type="password" placeholder="Clave" required><br>
            <button type="submit">Entrar</button>
        </form>
        <p>¿No tienes cuenta? <a href="/signup">Regístrate</a></p>
    </body></html>
    """

@app.post("/login")
async def login_logic(request: Request, u: str = Form(...), p: str = Form(...)):
    user_key = u.lower().strip()
    if user_key in USUARIOS and USUARIOS[user_key] == p:
        request.session["u"] = u
        return RedirectResponse("/", status_code=303)
    return "Error: Usuario o clave incorrectos. <a href='/login'>Volver</a>"

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    return """
    <html><body>
        <h2>Registro</h2>
        <form action="/signup" method="post">
            <input name="u" placeholder="Nuevo Usuario" required><br>
            <input name="p" type="password" placeholder="Nueva Clave" required><br>
            <button type="submit">Crear Cuenta</button>
        </form>
        <a href="/login">Ya tengo cuenta</a>
    </body></html>
    """

@app.post("/signup")
async def signup_logic(u: str = Form(...), p: str = Form(...)):
    user_key = u.lower().strip()
    if user_key not in USUARIOS:
        USUARIOS[user_key] = p
        # Redirigimos al login con 303 para forzar al navegador a cambiar de página
        return RedirectResponse("/login", status_code=303)
    return "El usuario ya existe. <a href='/signup'>Intentar otro</a>"

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
