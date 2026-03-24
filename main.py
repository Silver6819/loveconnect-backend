import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_ultra_minimalist_2026")

# --- BASE DE DATOS EN MEMORIA (Para que sea rápido como antes) ---
# En una versión futura usaremos SQL, pero esto arreglará el "Cargando" ahora.
USUARIOS_REGISTRADOS = {"silver breaker": "123"} # Diccionario de {usuario: clave}
CHAT_GLOBAL = []
MENSAJES_PRIVADOS = [] 
GALERIA_VIDEOS = []   

# --- ESTÉTICA NEON (Tu diseño actual) ---
ESTILOS = """
<style>
    body { background: #0b0b0f; color: #ececf1; font-family: sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; }
    .app-container { width: 100%; max-width: 500px; min-height: 100vh; display: flex; flex-direction: column; background: #000; border: 1px solid #1a1a1a; }
    .neon-logo { color: #00f7ff; text-shadow: 0 0 10px #00f7ff; text-align: center; font-size: 18px; padding: 10px 0; margin: 0; }
    .input-field { background:#16161d; margin-bottom:10px; padding:15px; width:100%; border-radius:8px; border:1px solid #333; color:white; outline:none; }
    .btn-pink { background:#ff00c8; color:white; border:none; padding:15px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer; }
    .tabs { display: flex; background: #111; border-bottom: 1px solid #2d2d3a; }
    .tab { flex: 1; padding: 12px; text-align: center; color: gray; cursor: pointer; text-decoration: none; font-size: 11px; font-weight: bold; text-transform: uppercase; }
    .tab.active { color: #ff00c8; border-bottom: 2px solid #ff00c8; background: #16161d; }
    .content-area { flex-grow: 1; padding: 15px; overflow-y: auto; height: 350px; }
    .msg-bubble { background: #16161d; border-radius: 8px; padding: 10px; margin-bottom: 8px; border-left: 3px solid #00f7ff; }
    .msg-meta { font-size: 10px; color: #00f7ff; font-weight: bold; margin-bottom: 3px; display: block; }
</style>
"""

# --- RUTAS DE ACCESO (LOGIN Y REGISTRO) ---

@app.get("/login", response_class=HTMLResponse)
async def login_p():
    return f"""<html>{ESTILOS}<body style='display:flex; align-items:center; justify-content:center; background:#000;'>
    <form action='/login' method='post' style='background:#111; padding:30px; border-radius:15px; text-align:center; border:1px solid #333; width:80%;'>
        <h2 class='neon-logo' style='font-size:25px;'>INGRESAR</h2>
        <input name='u' placeholder='Usuario' required class='input-field'><br>
        <input name='p' type='password' placeholder='Contraseña' required class='input-field'><br>
        <button class='btn-pink'>ENTRAR A LOVE CONNECT</button>
        <p style='font-size:12px; margin-top:15px;'>¿No tienes cuenta? <a href='/signup' style='color:#00f7ff;'>Regístrate aquí</a></p>
    </form></body></html>"""

@app.get("/signup", response_class=HTMLResponse)
async def signup_p():
    return f"""<html>{ESTILOS}<body style='display:flex; align-items:center; justify-content:center; background:#000;'>
    <form action='/signup' method='post' style='background:#111; padding:30px; border-radius:15px; text-align:center; border:1px solid #333; width:80%;'>
        <h2 class='neon-logo' style='font-size:25px; color:#ff00c8; text-shadow: 0 0 10px #ff00c8;'>REGISTRO</h2>
        <input name='u' placeholder='Crea tu Usuario' required class='input-field'><br>
        <input name='p' type='password' placeholder='Crea tu Contraseña' required class='input-field'><br>
        <button class='btn-pink' style='background:#00f7ff; color:black;'>CREAR CUENTA GRATIS</button>
        <br><a href='/login' style='color:gray; font-size:12px; text-decoration:none; display:block; margin-top:10px;'>Ya tengo cuenta</a>
    </form></body></html>"""

@app.post("/signup")
async def signup(u: str = Form(...), p: str = Form(...)):
    user_clean = u.lower().strip()
    if user_clean not in USUARIOS_REGISTRADOS:
        USUARIOS_REGISTRADOS[user_clean] = p
    return RedirectResponse("/login", status_code=303)

@app.post("/login")
async def login(u: str = Form(...), p: str = Form(...), request: Request = None):
    user_clean = u.lower().strip()
    if user_clean in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[user_clean] == p:
        request.session["u"] = u.strip() # Guardamos el nombre tal cual lo escribió
        return RedirectResponse("/", status_code=303)
    return HTMLResponse("<script>alert('Usuario o clave incorrecta'); window.location.href='/login';</script>")

# --- (El resto de tus rutas @app.get("/") y @app.post("/send") se mantienen igual) ---
