import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Clave de seguridad para mantener la sesión activa
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_secure_2026")

# --- BASE DE DATOS EN MEMORIA ---
usuarios = {}
mensajes_globales = []

# --- ESTILO VISUAL (Basado en tus capturas favoritas) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #fff0f6; margin: 0; padding: 20px; color: #333; }
    .card { background: white; max-width: 450px; margin: 20px auto; padding: 30px; border-radius: 30px; box-shadow: 0 10px 30px rgba(255, 79, 163, 0.1); text-align: center; }
    h1 { color: #ff4fa3; font-size: 24px; }
    .btn-principal { background: #ff4fa3; color: white; border: none; padding: 15px 30px; border-radius: 50px; cursor: pointer; font-weight: bold; width: 100%; font-size: 16px; text-decoration: none; display: block; margin: 10px 0; }
    .btn-secundario { background: #f0f0f0; color: #555; border: none; padding: 10px 20px; border-radius: 50px; cursor: pointer; text-decoration: none; display: inline-block; margin: 5px; font-size: 14px; }
    input, textarea { width: 100%; padding: 15px; margin: 10px 0; border: 1px solid #ffe0ed; border-radius: 15px; box-sizing: border-box; font-size: 14px; }
    .chat-container { height: 350px; overflow-y: auto; background: #fafafa; border-radius: 20px; padding: 15px; margin-bottom: 15px; border: 1px solid #f0f0f0; }
    .burbuja { background: #ff4fa3; color: white; padding: 10px 15px; border-radius: 20px 20px 5px 20px; margin: 8px 0; text-align: right; margin-left: auto; width: fit-content; max-width: 80%; }
    .nombre-admin { color: #ff4fa3; font-weight: bold; display: block; font-size: 12px; margin-bottom: 4px; }
</style>
"""

# --- RUTAS DE NAVEGACIÓN (Simplificadas para evitar "Not Found") ---

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    user = request.session.get("user")
    if user: return RedirectResponse(url="/sala-chat")
    
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">{CSS}</head>
    <body><div class="card">
        <h1>💖 LoveConnect</h1>
        <form action="/entrar" method="post">
            <input type="text" name="nombre" placeholder="¿Cómo te llamas?" required>
            <button type="submit" class="btn-principal">Empezar</button>
        </form>
    </div></body></html>
    """

@app.post("/entrar")
async def entrar(request: Request, nombre: str = Form(...)):
    user_id = nombre.strip()
    request.session["user"] = user_id
    if user_id not in usuarios:
        usuarios[user_id] = {"bio": "El Salvador", "foto": ""}
    return RedirectResponse(url="/sala-chat", status_code=303)

@app.get("/sala-chat", response_class=HTMLResponse)
async def sala_chat(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    # Construir burbujas de chat
    chat_html = ""
    for m in mensajes_globales:
        clase_admin = "👑 " if m['u'] == "Silver Breaker" else ""
        chat_html += f"<div class='burbuja'><span style='font-size:10px; opacity:0.8;'>{clase_admin}{m['u']}</span><br>{m['t']}</div>"

    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">{CSS}</head>
    <body><div class="card">
        <h3>Chat Grupal 🟢</h3>
        <div class="chat-container">{chat_html}</div>
        <form action="/enviar-msg" method="post">
            <input type="text" name="msg" placeholder="Escribe un mensaje..." required>
            <button type="submit" class="btn-principal">Enviar</button>
        </form>
        <div style="margin-top:20px;">
            <a href="/mi-perfil" class="btn-secundario">👤 Perfil</a>
            <a href="/salir" class="btn-secundario" style="color:red;">✖ Salir</a>
        </div>
    </div></body></html>
    """

@app.post("/enviar-msg")
async def enviar_msg(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    if user:
        mensajes_globales.append({"u": user, "t": msg[:150]})
        if len(mensajes_globales) > 25: mensajes_globales.pop(0)
    return RedirectResponse(url="/sala-chat", status_code=303)

@app.get("/mi-perfil", response_class=HTMLResponse)
async def mi_perfil(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    datos = usuarios.get(user, {"bio": "Sin biografía"})
    admin_tag = "<span style='background:#6c5ce7; color:white; padding:3px 10px; border-radius:10px; font-size:12px;'>LVL: ∞ ADMIN</span>" if user == "Silver Breaker" else ""

    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">{CSS}</head>
    <body><div class="card">
        <h1>{user}</h1>
        {admin_tag}
        <form action="/actualizar-perfil" method="post" style="margin-top:20px;">
            <p>Tu Bio:</p>
            <textarea name="nueva_bio">{datos['bio']}</textarea>
            <button type="submit" class="btn-principal">Guardar Cambios</button>
        </form>
        <br>
        <a href="/sala-chat" style="color:#ff4fa3; text-decoration:none; font-weight:bold;">← Volver al Chat</a>
    </div></body></html>
    """

@app.post("/actualizar-perfil")
async def actualizar_perfil(request: Request, nueva_bio: str = Form(...)):
    user = request.session.get("user")
    if user in usuarios:
        usuarios[user]["bio"] = nueva_bio[:200]
    return RedirectResponse(url="/mi-perfil", status_code=303)

@app.get("/salir")
async def salir(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
