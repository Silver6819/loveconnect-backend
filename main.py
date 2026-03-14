import os, uvicorn, random
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-breaker-2026-key")

# --- BASE DE DATOS (En Memoria) ---
ADMIN_NAME = "Silver Breaker"
chat_log = []
punished_users = {}
profiles = {}
suggestions = []
online_users = set()

# --- CSS GLOBAL ESTILO TINDER/MESSENGER ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background:#fff0f6; margin:0; }
    .card { max-width:400px; margin:20px auto; padding:20px; background:white; border-radius:20px; box-shadow:0 10px 20px rgba(0,0,0,0.05); text-align:center; }
    .btn-pink { background:#ff4fa3; color:white; border:none; padding:12px 25px; border-radius:25px; font-weight:bold; cursor:pointer; text-decoration:none; display:inline-block; }
    .back-btn { background:#eee; border:none; padding:8px 15px; border-radius:12px; cursor:pointer; color:#666; font-size:12px; }
    #chat-box { height:60vh; overflow-y:auto; padding:15px; background:white; display:flex; flex-direction:column; }
    .bubble { padding:10px 15px; border-radius:18px; margin:5px; max-width:75%; font-size:14px; position:relative; }
    .mine { align-self: flex-end; background:#ff4fa3; color:white; border-bottom-right-radius:2px; }
    .others { align-self: flex-start; background:#f1f1f1; color:#333; border-bottom-left-radius:2px; }
    .admin-panel { background:#222; color:#0f0; padding:15px; font-family:monospace; font-size:12px; border-radius:15px; margin:10px; }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user:
        return HTMLResponse(f"<html>{ESTILOS}<body><div class='card'><h2>💖 LoveConnect</h2><form action='/login' method='post'><input name='username' placeholder='Tu nombre' required style='padding:12px; border-radius:10px; border:1px solid #ddd; width:80%'><br><br><button class='btn-pink'>Entrar al Chat</button></form></div></body></html>")

    # Verificar Castigo
    if user in punished_users and datetime.utcnow() < punished_users[user]:
        return HTMLResponse(f"<html>{ESTILOS}<body style='background:#000; color:red; text-align:center; padding-top:100px;'><h1>🚫 SALA DE CASTIGO</h1><p>Fuiste restringido por 24h.</p></body></html>")

    online_users.add(user)

    # Dibujar Chat
    chat_html = ""
    for m in chat_log:
        clase = "mine" if m["user"] == user else "others"
        estrella = "🌟" if m["user"] == ADMIN_NAME else ""
        chat_html += f'<div class="bubble {clase}"><small style="display:block; font-size:10px; opacity:0.7;">{m["user"]} {estrella}</small>{m["text"]}</div>'

    # Panel Secreto Silver Breaker
    admin_tools = ""
    if user == ADMIN_NAME:
        admin_tools = f"""
        <div class="admin-panel">
            <b>SISTEMA DE CONTROL ADMIN</b><br>
            🔥 En línea: {len(online_users)}<br>
            📬 Sugerencias: {len(suggestions)}<br>
            <form action="/punish" method="post" style="margin-top:10px;">
                <input name="target" placeholder="Usuario a castigar" style="background:#000; color:#0f0; border:1px solid #0f0; width:60%">
                <button style="background:#400; color:red; border:none;">BAN</button>
            </form>
            <form action="/clear" method="post" style="margin-top:5px;"><button style="color:yellow; background:none; border:none; cursor:pointer;">[Limpiar Todo el Chat]</button></form>
        </div>"""

    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <header style="background:white; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; align-items:center;">
            <b style="color:#ff4fa3;">LoveConnect</b>
            <div>
                <span style="font-size:10px; color:gray;">🔥 {len(online_users)} online</span>
                <a href="/perfil" style="text-decoration:none; margin-left:10px;">👤</a>
            </div>
        </header>
        <div id="chat-box">{chat_html}<div id="end"></div></div>
        <form action="/send" method="post" style="display:flex; padding:10px; background:white;">
            <input name="msg" placeholder="Escribe..." required style="flex:1; padding:12px; border-radius:20px; border:1px solid #eee; outline:none;">
            <button style="background:#ff4fa3; color:white; border:none; border-radius:50%; width:45px; height:45px; margin-left:5px;">➤</button>
        </form>
        <div style="text-align:center; padding:10px;">
            <a href="/match" class="btn-pink" style="padding:8px 15px; font-size:12px;">💘 Match Rápido</a>
        </div>
        {admin_tools}
        <script>document.getElementById('end').scrollIntoView();</script>
    </body></html>
    """)

# --- RUTAS DE ACCIÓN ---
@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles: profiles[username] = {"votes": 0, "bio": "¡Hola!"}
    return RedirectResponse(url="/", status_code=303)

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    if user and msg.strip():
        # AQUÍ ESTABA EL ERROR: Se corrigió la estructura del diccionario
        chat_log.append({"user": user, "text": msg})
        if len(chat_log) > 40: chat_log.pop(0)
    return RedirectResponse(url="/", status_code=303)

@app.get("/perfil")
async def view_profile(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"votes": 0, "bio": "Sin bio"})
    return HTMLResponse(f"""
    <html>{ESTILOS}<body>
        <div class="card">
            <button class="back-btn" onclick="history.back()">⬅ Regresar</button>
            <h2 style="color:#ff4fa3;">{user}</h2>
            <p>{p['bio']}</p>
            <h3>❤️ {p['votes']} Corazones</h3>
            <form action="/vote/{user}" method="post"><button class="btn-pink">Dar Corazón</button></form>
            <hr style="border:0; border-top:1px solid #eee; margin:20px 0;">
            <form action="/suggestion" method="post">
                <textarea name="text" placeholder="¿Qué debería mejorar?" style="width:100%; border-radius:10px; border:1px solid #eee;"></textarea><br>
                <button style="background:none; border:none; color:#ff4fa3; cursor:pointer;">Enviar Sugerencia</button>
            </form>
        </div>
    </body></html>""")

@app.post("/vote/{target}")
async def vote(target: str):
    if target in profiles: profiles[target]["votes"] += 1
    return RedirectResponse(url="/perfil", status_code=303)

@app.post("/suggestion")
async def suggest(request: Request, text: str = Form(...)):
    user = request.session.get("user")
    suggestions.append({"user": user, "text": text})
    return RedirectResponse(url="/perfil", status_code=303)

@app.get("/match")
async def quick_match():
    if not profiles: return RedirectResponse(url="/")
    lucky = random.choice(list(profiles.keys()))
    return HTMLResponse(f"<html>{ESTILOS}<body style='text-align:center; padding-top:100px;'><h1>💘</h1><h2>Match con: {lucky}</h2><button class='btn-pink' onclick='history.back()'>Regresar</button></body></html>")

@app.post("/punish")
async def punish(target: str = Form(...)):
    punished_users[target] = datetime.utcnow() + timedelta(hours=24)
    return RedirectResponse(url="/", status_code=303)

@app.post("/clear")
async def clear_chat(request: Request):
    if request.session.get("user") == ADMIN_NAME:
        chat_log.clear()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
