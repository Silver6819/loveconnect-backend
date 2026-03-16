import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_ultra_2026")

# --- BASES DE DATOS (En memoria para velocidad) ---
usuarios_registrados = {"Silver Breaker": "1234"} # Usuario admin por defecto
chat_global = []
usuarios_activos = set()

CLAVE_ADMIN = "SB2026"

CSS = f"""
<style>
    body {{ font-family: 'Segoe UI', sans-serif; background: #fff5f8; text-align: center; padding: 20px; margin: 0; }}
    .box {{ background: white; padding: 40px 30px; border-radius: 30px; max-width: 400px; margin: 20px auto; box-shadow: 0 15px 35px rgba(255, 79, 163, 0.1); }}
    h1 {{ color: #333; font-size: 32px; margin-bottom: 20px; }}
    .btn {{ background: #ff4fa3; color: white; border: none; padding: 15px; border-radius: 50px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px; margin-top: 15px; text-decoration: none; display: block; }}
    .btn-admin {{ background: #6c5ce7; margin-top: 10px; font-size: 13px; }}
    input {{ width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #eee; border-radius: 15px; box-sizing: border-box; background: #fafafa; }}
    .msg-list {{ height: 300px; overflow-y: auto; background: #fafafa; padding: 15px; border-radius: 20px; margin-bottom: 15px; }}
    .msg-item {{ background: #ffeef4; padding: 10px 15px; border-radius: 18px; margin: 8px 0; text-align: left; font-size: 14px; border-bottom-left-radius: 4px; }}
    .admin-tag {{ background: #ff4fa3; color: white; padding: 2px 8px; border-radius: 8px; font-size: 10px; font-weight: bold; margin-left: 5px; }}
    .online-count {{ background: #e3ffed; color: #27ae60; padding: 5px 15px; border-radius: 20px; font-size: 12px; font-weight: bold; display: inline-block; margin-bottom: 10px; }}
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.session.get("user"): return RedirectResponse(url="/chat")
    # Pantalla de bienvenida grande y limpia
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS}</head>
    <body><div class='box'>
        <h1>❤️ LoveConnect</h1>
        <p style='color:#666;'>Inicia sesión o regístrate</p>
        <form action='/login' method='post'>
            <input name='u' placeholder='Usuario' required>
            <input name='p' type='password' placeholder='Contraseña' required>
            <button class='btn'>Entrar</button>
        </form>
        <p style='font-size: 12px; margin-top: 20px; color: #aaa;'>Si el usuario no existe, se creará automáticamente.</p>
    </div></body></html>
    """

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    user = u.strip()
    # Registro automático simplificado
    if user not in usuarios_registrados:
        usuarios_registrados[user] = p
    
    # Verificación de contraseña
    if usuarios_registrados[user] == p:
        request.session["user"] = user
        usuarios_activos.add(user)
        return RedirectResponse(url="/chat", status_code=303)
    else:
        return "Contraseña incorrecta. Regresa e intenta de nuevo."

@app.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    # Contador de usuarios
    conteo = len(usuarios_activos)
    
    mensajes_html = ""
    for m in chat_global:
        tag = "<span class='admin-tag'>ADMIN</span>" if m['u'] == "Silver Breaker" else ""
        mensajes_html += f"<div class='msg-item'><b>{m['u']}{tag}:</b> {m['t']}</div>"
    
    boton_admin = ""
    if user == "Silver Breaker":
        boton_admin = f"<a href='/limpiar?clave={CLAVE_ADMIN}' class='btn btn-admin'>🗑️ Borrar historial (Solo yo veo esto)</a>"
    
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS}</head>
    <body><div class='box'>
        <div class='online-count'>● {conteo} Usuarios en línea</div>
        <h3>Chat Grupal</h3>
        <div class="msg-list">{mensajes_html}</div>
        <form action="/postear" method="post">
            <input name="m" placeholder="Escribe un mensaje..." required autocomplete="off">
            <button class="btn">Enviar</button>
        </form>
        {boton_admin}
        <br><a href="/logout" style="color:#aaa; font-size:12px; text-decoration:none;">Cerrar Sesión</a>
    </div></body></html>
    """

@app.post("/postear")
async def postear(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user:
        clean_text = m.replace("<", "&lt;").replace(">", "&gt;")[:120]
        chat_global.append({"u": user, "t": clean_text})
        if len(chat_global) > 25: chat_global.pop(0)
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/limpiar")
async def limpiar_chat(clave: str):
    if clave == CLAVE_ADMIN:
        chat_global.clear()
        return RedirectResponse(url="/chat")
    return "Error."

@app.get("/logout")
async def logout(request: Request):
    user = request.session.get("user")
    if user in usuarios_activos: usuarios_activos.remove(user)
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
