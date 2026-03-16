import os, uvicorn, time
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_2026")

# --- MEMORIA VOLÁTIL ---
profiles = {} 
chat_log = []

# Estilos ultra-ligeros para evitar errores de carga
CSS = """
<style>
    body { font-family: sans-serif; background: #fff5f8; text-align: center; margin: 0; padding: 20px; }
    .card { background: white; padding: 25px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
    .btn { background: #ff4fa3; color: white; border: none; padding: 12px 25px; border-radius: 25px; cursor: pointer; text-decoration: none; display: inline-block; font-weight: bold; }
    input, textarea { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; }
    .msg { background: #f1f2f6; padding: 10px; border-radius: 15px; margin: 5px; text-align: left; }
    .admin { color: #6c5ce7; font-weight: bold; }
</style>
"""

# --- RUTAS PRINCIPALES ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("user")
    if not user:
        return f"<html>{CSS}<body><div class='card'><h1>💖 LoveConnect</h1><form action='/login' method='post'><input name='u' placeholder='Tu nombre' required><br><button class='btn'>Entrar</button></form></div></body></html>"
    return RedirectResponse("/chat")

@app.post("/login")
async def do_login(request: Request, u: str = Form(...)):
    request.session["user"] = u.strip()
    if u not in profiles:
        profiles[u] = {"bio": "El Salvador", "lvl": "∞" if u == "Silver Breaker" else "1"}
    return RedirectResponse("/chat")

@app.get("/chat", response_class=HTMLResponse)
async def view_chat(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/")
    
    msgs_html = "".join([f"<div class='msg'><b>{m['u']}:</b> {m['t']}</div>" for m in chat_log])
    
    return f"""
    <html>{CSS}<body>
        <div class="card">
            <h3>Chat Grupal</h3>
            <div style="height:300px; overflow-y:auto; border:1px solid #eee; margin-bottom:10px;">{msgs_html}</div>
            <form action="/send" method="post">
                <input name="m" placeholder="Escribe algo..." required>
                <button class="btn">Enviar</button>
            </form>
            <br>
            <a href="/perfil" style="color:#ff4fa3; font-size:14px;">Mi Perfil</a>
        </div>
    </body></html>
    """

@app.post("/send")
async def send(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user:
        chat_log.append({"u": user, "t": m[:100]})
        if len(chat_log) > 20: chat_log.pop(0)
    return RedirectResponse("/chat", status_code=303)

@app.get("/perfil", response_class=HTMLResponse)
async def view_perfil(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"bio": "...", "lvl": "1"})
    
    # "Cerrar sesión" corregido según tu petición
    return f"""
    <html>{CSS}<body>
        <div class="card">
            <h2>{user}</h2>
            <p class="admin">Nivel: {p['lvl']}</p>
            <form action="/update" method="post">
                <textarea name="b">{p['bio']}</textarea><br>
                <button class="btn">Guardar Cambios</button>
            </form>
            <br><br>
            <a href="/logout" style="color:red; font-size:13px;">Cerrar sesión</a>
        </div>
    </body></html>
    """

@app.post("/update")
async def update(request: Request, b: str = Form(...)):
    user = request.session.get("user")
    if user in profiles: profiles[user]["bio"] = b[:100]
    return RedirectResponse("/perfil")

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
