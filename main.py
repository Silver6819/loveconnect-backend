import os, uvicorn, time, random
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-super-secret-2026")

# --- BASES DE DATOS VOLÁTILES ---
ADMIN_NAME = "Silver Breaker"
chat_log = []
profiles = {} # {user: {"points": 0, "likes": set()}}
online_users = {} # {user: last_seen}
stats = {"msgs": 0}

# --- ESTILOS TIPO TINDER (Mejoras Visuales de ChatGPT) ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background:#fff0f6; margin:0; text-align:center; }
    .card { max-width:350px; margin:20px auto; padding:20px; background:white; border-radius:25px; box-shadow:0 10px 20px rgba(0,0,0,0.05); }
    .btn-viral { background:#ff4fa3; color:white; border:none; padding:12px; border-radius:20px; width:90%; font-weight:bold; cursor:pointer; }
    .online-tag { color: #2ecc71; font-size: 12px; font-weight: bold; }
    .chat-bubble { padding:10px 15px; border-radius:18px; margin:5px; max-width:80%; font-size:14px; display:inline-block; }
    .mine { background:#ff4fa3; color:white; text-align:right; float:right; clear:both; }
    .others { background:#eee; color:#333; text-align:left; float:left; clear:both; }
</style>
"""

@app.get("/")
async def home(request: Request, ref: str = None):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")
    
    # Sistema Viral: Si vienes por un link de alguien
    if ref and ref in profiles and ref != user:
        profiles[ref]["points"] = profiles[ref].get("points", 0) + 1

    online_users[user] = time.time()
    activos = len([u for u, t in online_users.items() if time.time() - t < 60])

    chat_html = "".join([f'<div class="chat-bubble {"mine" if m["user"]==user else "others"}"><small>{m["user"]}</small><br>{m["text"]}</div>' for m in chat_log])

    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div style="background:white; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between;">
            <b style="color:#ff4fa3;">💖 LoveConnect</b>
            <span class="online-tag">🟢 {activos} activos</span>
        </div>
        <div id="box" style="height:60vh; overflow-y:auto; padding:15px;">{chat_html}<div id="e"></div></div>
        <form action="/send" method="post" style="padding:10px; background:white; display:flex;">
            <input name="msg" placeholder="Mensaje..." required style="flex:1; padding:10px; border-radius:20px; border:1px solid #eee;">
            <button style="background:#ff4fa3; color:white; border:none; border-radius:50%; width:40px; margin-left:5px;">➤</button>
        </form>
        <div style="padding:10px;"><a href="/perfil" style="color:#ff4fa3; text-decoration:none; font-size:12px;">👤 Ver Mi Perfil y Puntos</a></div>
        <script>document.getElementById('e').scrollIntoView();</script>
    </body></html>
    """)

@app.get("/perfil")
async def view_profile(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"points": 0})
    link_viral = f"https://{request.url.netloc}/?ref={user}"
    
    return HTMLResponse(f"""
    <html>{ESTILOS}<body>
        <div class="card">
            <h2 style="color:#ff4fa3;">{user}</h2>
            <div style="background:#fff0f6; padding:15px; border-radius:20px;">
                <span style="font-size:25px;">⭐</span><br>
                <b>Puntos de Viralidad: {p.get('points', 0)}</b>
            </div>
            <p style="font-size:12px; color:#666; margin-top:15px;">Comparte tu link para ganar puntos:</p>
            <input value="{link_viral}" readonly style="width:90%; padding:10px; border-radius:10px; border:1px solid #eee; font-size:10px;">
            <br><br>
            <button class="btn-viral" onclick="history.back()">Volver al Chat</button>
        </div>
    </body></html>
    """)

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    if user and msg.strip():
        chat_log.append({"user": user, "text": msg})
        if len(chat_log) > 30: chat_log.pop(0)
    return RedirectResponse("/", status_code=303)

@app.get("/login-page")
async def login_p():
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='card'><h2>💖 LoveConnect</h2><form action='/login' method='post'><input name='username' placeholder='Tu Nombre' required style='padding:10px; width:80%;'><br><br><button class='btn-viral'>Entrar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles: profiles[username] = {"points": 0, "likes": set()}
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
