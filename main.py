import os, uvicorn, time, random
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-viral-key-2026")

# --- BASES DE DATOS EN MEMORIA ---
ADMIN_NAME = "Silver Breaker"
chat_log = []
punished_users = {}
profiles = {} # {user: {"votes": 0, "bio": "", "likes": set(), "points": 0}}
suggestions = []
last_msg_time = {} # Anti-Spam
stats = {"messages_today": 0, "matches_today": 0}

# --- LÓGICA DE APOYO ---
def get_matches(user):
    my_matches = []
    if user not in profiles: return []
    for other, data in profiles.items():
        if other != user:
            if user in data.get("likes", set()) and other in profiles[user].get("likes", set()):
                my_matches.append(other)
    return my_matches

# --- ESTILOS MEJORADOS (ChatGPT + Gemini) ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background:#f4f4f4; margin:0; padding-bottom: 60px; }
    .card { max-width:400px; margin:20px auto; padding:20px; background:white; border-radius:20px; box-shadow:0 5px 15px rgba(0,0,0,0.05); text-align:center; }
    .bubble { padding:10px 15px; border-radius:18px; margin:5px; max-width:75%; font-size:14px; box-shadow:0 2px 5px rgba(0,0,0,0.03); }
    .mine { align-self: flex-end; background:#ff4fa3; color:white; border-bottom-right-radius:2px; }
    .others { align-self: flex-start; background:#eee; color:#333; border-bottom-left-radius:2px; }
    .btn-main { background:#ff4fa3; color:white; border:none; padding:12px 25px; border-radius:25px; font-weight:bold; cursor:pointer; width: 100%; margin-top:10px; }
    .stats-bar { font-size:11px; color:#999; text-align:center; padding:10px; }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")

    # Anti-Castigo
    if user in punished_users and datetime.utcnow() < punished_users[user]:
        return HTMLResponse("<body style='background:black;color:red;text-align:center;'><h1>🚫 ZONA DE CONTENCIÓN</h1></body>")

    # Render Chat
    chat_html = "".join([f'<div style="display:flex; flex-direction:{"column" if m["user"]!=user else "column; align-items:flex-end"}"><div class="bubble {"mine" if m["user"]==user else "others"}"><small>{m["user"]}</small><br>{m["text"]}</div></div>' for m in chat_log])

    # Stats Reales
    stats_html = f"<div class='stats-bar'>🔥 {stats['messages_today']} mensajes hoy | ❤️ {stats['matches_today']} matches hoy</div>"

    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <header style="background:white; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between;">
            <b style="color:#ff4fa3;">💖 LoveConnect</b>
            <a href="/perfil" style="text-decoration:none;">👤 Perfil</a>
        </header>
        <div id="chat" style="height:60vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column;">{chat_html}<div id="end"></div></div>
        <form action="/send" method="post" style="padding:10px; display:flex; background:white; position:fixed; bottom:0; width:100%; box-sizing:border-box;">
            <input name="msg" placeholder="Escribe algo..." required style="flex:1; padding:12px; border-radius:20px; border:1px solid #eee;">
            <button style="background:#ff4fa3; color:white; border:none; border-radius:50%; width:45px; height:45px; margin-left:5px;">➤</button>
        </form>
        {stats_html}
        <script>document.getElementById('end').scrollIntoView();</script>
    </body></html>
    """)

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    ahora = time.time()
    
    # --- MEJORA 3: ANTI-SPAM ---
    if user in last_msg_time and ahora - last_msg_time[user] < 3:
        return HTMLResponse("<script>alert('¡No tan rápido! Espera 3 segundos.'); window.location='/';</script>")
    
    if user and msg.strip():
        last_msg_time[user] = ahora
        chat_log.append({"user": user, "text": msg})
        stats["messages_today"] += 1
        if len(chat_log) > 30: chat_log.pop(0)
    return RedirectResponse(url="/", status_code=303)

@app.get("/perfil")
async def view_profile(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"votes": 0, "points": 0})
    matches = get_matches(user)
    
    matches_html = "".join([f"<li style='color:#ff4fa3; list-style:none;'>💘 Match con {m} <a href='/chat-privado/{m}'>💬</a></li>" for m in matches])

    return HTMLResponse(f"""
    <html>{ESTILOS}<body>
        <div class="card">
            <button onclick="history.back()" style="float:left; border:none; background:none; cursor:pointer;">⬅️</button>
            <h2 style="color:#ff4fa3;">{user}</h2>
            <div style="background:#fff0f6; padding:10px; border-radius:15px; margin-bottom:15px;">
                <b>⭐ Puntos de Viralidad: {p.get('points', 0)}</b><br>
                <small>Invita amigos para ganar puntos</small>
            </div>
            <h3>Mis Matches:</h3>
            <ul>{matches_html if matches_html else "Aún no hay matches mutuamente."}</ul>
            <hr>
            <form action="/invite" method="post">
                <input name="friend" placeholder="Nombre del amigo" style="padding:8px; border-radius:10px; border:1px solid #eee;">
                <button class="btn-main" style="padding:8px; font-size:12px;">Invitar y ganar puntos</button>
            </form>
        </div>
    </body></html>""")

# --- MEJORA VIRAL (30 líneas) ---
@app.post("/invite")
async def invite(request: Request, friend: str = Form(...)):
    user = request.session.get("user")
    if user:
        profiles[user]["points"] = profiles[user].get("points", 0) + 10
        return HTMLResponse(f"<script>alert('¡Invitación enviada a {friend}! Ganaste 10 puntos.'); window.location='/perfil';</script>")

@app.get("/login-page")
async def lp():
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='card'><h2>LoveConnect</h2><form action='/login' method='post'><input name='username' placeholder='Nombre' required style='padding:12px; width:80%'><br><button class='btn-pink btn-main'>Entrar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles: profiles[username] = {"votes": 0, "likes": set(), "points": 0}
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
