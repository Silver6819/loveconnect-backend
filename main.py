import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Llave de sesión robusta para evitar errores de autenticación
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_key_2026")

# --- BASE DE DATOS TEMPORAL ---
# Usamos diccionarios simples para que Railway no se bloquee
db_users = {}
chat_history = []

# --- DISEÑO LIMPIO Y RESPONSIVO ---
CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff0f5; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .container { background: white; width: 90%; max-width: 400px; padding: 20px; border-radius: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; }
    .btn { background: #ff4fa3; color: white; border: none; padding: 12px 20px; border-radius: 50px; cursor: pointer; text-decoration: none; font-weight: bold; width: 100%; display: block; margin-top: 10px; }
    input, textarea { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #eee; border-radius: 15px; box-sizing: border-box; }
    .chat-box { height: 300px; overflow-y: auto; border: 1px solid #f9f9f9; padding: 10px; margin-bottom: 10px; background: #fafafa; border-radius: 15px; }
    .msg { background: #ffe4ee; padding: 8px 12px; border-radius: 15px; margin: 5px 0; text-align: left; font-size: 14px; }
    .admin-tag { background: #6c5ce7; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; }
</style>
"""

# --- RUTAS DE NAVEGACIÓN ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if user:
        return RedirectResponse(url="/main_chat")
    
    # Pantalla de Login corregida
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS}</head>
    <body><div class='container'>
        <h1>💖 LoveConnect</h1>
        <form action="/login_action" method="post">
            <input type="text" name="username" placeholder="Tu nombre o apodo" required>
            <button type="submit" class="btn">Entrar</button>
        </form>
    </div></body></html>
    """

@app.post("/login_action")
async def login_action(request: Request, username: str = Form(...)):
    clean_name = username.strip()
    request.session["user"] = clean_name
    if clean_name not in db_users:
        db_users[clean_name] = {"bio": "¡Hola! Estoy en LoveConnect.", "status": "Activo"}
    return RedirectResponse(url="/main_chat", status_code=303)

@app.get("/main_chat", response_class=HTMLResponse)
async def main_chat(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")

    # Generar mensajes
    msgs = "".join([f"<div class='msg'><b>{m['u']}:</b> {m['t']}</div>" for m in chat_history])
    
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS}</head>
    <body><div class='container'>
        <h3>Chat Grupal 🟢</h3>
        <div class="chat-box">{msgs}</div>
        <form action="/send_msg" method="post">
            <input type="text" name="text" placeholder="Escribe un mensaje..." required>
            <button type="submit" class="btn">Enviar</button>
        </form>
        <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
        <div style="display:flex; gap:10px;">
            <a href="/my_profile" class="btn" style="background:#eee; color:#333;">Mi Perfil</a>
            <a href="/logout" class="btn" style="background:#ffeded; color:red;">Salir</a>
        </div>
    </div></body></html>
    """

@app.post("/send_msg")
async def send_msg(request: Request, text: str = Form(...)):
    user = request.session.get("user")
    if user:
        chat_history.append({"u": user, "t": text[:100]})
        if len(chat_history) > 30: chat_history.pop(0)
    return RedirectResponse(url="/main_chat", status_code=303)

@app.get("/my_profile", response_class=HTMLResponse)
async def my_profile(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    profile = db_users.get(user, {"bio": "..."})
    admin_label = "<span class='admin-tag'>ADMIN</span>" if user == "Silver Breaker" else ""

    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS}</head>
    <body><div class='container'>
        <h2>{user} {admin_label}</h2>
        <form action="/update_profile" method="post">
            <p>Tu Biografía:</p>
            <textarea name="new_bio" rows="3">{profile['bio']}</textarea>
            <button type="submit" class="btn">Guardar Cambios</button>
        </form>
        <br>
        <a href="/main_chat" style="color:#ff4fa3; text-decoration:none;">← Volver al chat</a>
    </div></body></html>
    """

@app.post("/update_profile")
async def update_profile(request: Request, new_bio: str = Form(...)):
    user = request.session.get("user")
    if user in db_users:
        db_users[user]["bio"] = new_bio[:150]
    return RedirectResponse(url="/my_profile", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
