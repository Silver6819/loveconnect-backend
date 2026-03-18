import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# CLAVE DE SESIÓN (Para que el Login no se borre al recargar)
app.add_middleware(SessionMiddleware, secret_key="SILVER_BREAKER_KEY_99")

# --- BASE DE DATOS EN MEMORIA (LIMPIEZA DE CRASH) ---
mensajes_globales = []
# Usuario maestro configurado
USUARIOS = {"Silver676": "1234"} 

# --- MOTOR DE DISEÑO (SIN LLAVES RARAS) ---
def generar_html(usuario=None, pagina="login"):
    # Estilos Neón Unificados
    estilos = """
    <style>
        body { background:#000; color:white; font-family:sans-serif; text-align:center; margin:0; }
        .neon-blue { color:#00f7ff; text-shadow:0 0 10px #00f7ff; }
        .neon-pink { color:#ff00c8; text-shadow:0 0 10px #ff00c8; }
        .container { max-width:400px; margin:20px auto; padding:20px; border:1px solid #222; border-radius:15px; background:#0a0a0a; }
        input { width:80%; padding:10px; margin:10px 0; background:#111; border:1px solid #333; color:white; border-radius:5px; }
        .btn-pink { background:transparent; border:2px solid #ff00c8; color:#ff00c8; padding:10px 20px; cursor:pointer; font-weight:bold; width:90%; }
        .chat-box { height:300px; overflow-y:auto; background:#000; border:1px solid #111; text-align:left; padding:10px; margin:10px 0; font-size:14px; }
        .logout { color:gray; font-size:10px; text-decoration:none; margin-top:20px; display:block; }
    </style>
    """
    
    if pagina == "login":
        return f"""
        <html>{estilos}<body>
            <div class="container">
                <h1 class="neon-pink">❤️ LoveConnect</h1>
                <form action="/login" method="post">
                    <input type="text" name="user" placeholder="Usuario" required><br>
                    <input type="password" name="password" placeholder="Clave" required><br>
                    <button type="submit" class="btn-pink">ENTRAR</button>
                </form>
            </div>
        </body></html>
        """
    
    if pagina == "chat":
        msjs = ""
        for m in mensajes_globales:
            msjs += f"<p style='border-bottom:1px solid #111; padding:5px;'><b class='neon-blue'>{m['user']}:</b> {m['msg']}</p>"
        
        return f"""
        <html>{estilos}<body>
            <div class="container">
                <h2 class="neon-blue">LOVE CONNECT</h2>
                <p>Hola, <b>{usuario}</b> <span class="neon-pink">[LvL: ∞]</span></p>
                
                <div class="chat-box">{msjs if msjs else "Sin mensajes..."}</div>
                
                <form action="/enviar" method="post" style="display:flex; gap:5px;">
                    <input type="text" name="msg" placeholder="Escribe..." required>
                    <button type="submit" style="background:#00f7ff; border:none; padding:10px; cursor:pointer;">🚀</button>
                </form>

                <a href="/borrar" style="color:red; font-size:10px; display:block; margin-top:10px;">[GOD MODE: LIMPIAR CHAT]</a>
                <a href="/logout" class="logout">Cerrar Sesión</a>
            </div>
        </body></html>
        """

# --- RUTAS DE LÓGICA ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if not user:
        return generar_html(pagina="login")
    return generar_html(usuario=user, pagina="chat")

@app.post("/login")
async def login(request: Request, user: str = Form(...), password: str = Form(...)):
    if user in USUARIOS and USUARIOS[user] == password:
        request.session["user"] = user
        return RedirectResponse("/", status_code=303)
    return HTMLResponse("<h2>Clave incorrecta</h2><a href='/'>Volver</a>")

@app.post("/enviar")
async def enviar(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    if user:
        mensajes_globales.append({"user": user, "msg": msg})
    return RedirectResponse("/", status_code=303)

@app.get("/borrar")
async def borrar(request: Request):
    if request.session.get("user") == "Silver676":
        mensajes_globales.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
