import os, uvicorn, time, random
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-breaker-ultra-2026")

# --- BASES DE DATOS ---
ADMIN_NAME = "Silver Breaker"
chat_log = []
punished_users = {}
profiles = {} # {user: {"votes": 0, "bio": "", "likes": set(), "points": 0}}
private_chats = {} # {"user1_user2": [mensajes]}
stats = {"messages_today": 0, "matches_today": 0}
last_msg_time = {}

# --- ESTILOS PROFESIONALES ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background:#fff0f6; margin:0; padding-bottom:70px; }
    .nav { background:white; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; position:sticky; top:0; z-index:100; }
    .card { max-width:380px; margin:20px auto; padding:25px; background:white; border-radius:25px; box-shadow:0 10px 25px rgba(0,0,0,0.05); text-align:center; }
    .bubble { padding:12px 18px; border-radius:20px; margin:8px; max-width:75%; font-size:14px; line-height:1.4; }
    .mine { align-self: flex-end; background:#ff4fa3; color:white; border-bottom-right-radius:4px; }
    .others { align-self: flex-start; background:#f1f1f1; color:#333; border-bottom-left-radius:4px; }
    .btn-pink { background:#ff4fa3; color:white; border:none; padding:12px 20px; border-radius:25px; font-weight:bold; cursor:pointer; text-decoration:none; display:block; margin:10px auto; width:80%; }
    .btn-sec { background:#eee; color:#666; border:none; padding:10px; border-radius:15px; cursor:pointer; }
    .stats { font-size:11px; color:#ff4fa3; text-align:center; padding:10px; font-weight:bold; }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")
    if user in punished_users and datetime.utcnow() < punished_users[user]:
        return HTMLResponse("<body style='background:black;color:red;text-align:center;padding-top:100px;'><h1>🚫 SALA DE CASTIGO</h1><p>Vuelve en 24 horas.</p></body>")

    chat_html = "".join([f'<div style="display:flex; flex-direction:column; {"align-items:flex-end" if m["user"]==user else ""}">'+
                         f'<div class="bubble {"mine" if m["user"]==user else "others"}"><small style="font-size:10px; opacity:0.6;">{m["user"]}</small><br>{m["text"]}</div></div>' for m in chat_log])

    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><b style="color:#ff4fa3;">💖 LoveConnect</b> <div><a href="/encuentros" style="text-decoration:none; margin-right:15px;">🔥</a><a href="/perfil" style="text-decoration:none;">👤</a></div></div>
        <div id="chat" style="display:flex; flex-direction:column; padding:10px; min-height:70vh;">{chat_html if chat_html else '<p style="text-align:center;color:#ccc;">Empieza la conversación...</p>'}<div id="end"></div></div>
        <div class="stats">🔥 {stats['messages_today']} mensajes | ❤️ {stats['matches_today']} matches hoy</div>
        <form action="/send" method="post" style="position:fixed; bottom:0; width:100%; background:white; padding:10px; display:flex; box-sizing:border-box; border-top:1px solid #eee;">
            <input name="msg" placeholder="Escribe algo..." required style="flex:1; border:1px solid #eee; padding:12px; border-radius:25px; outline:none;">
            <button style="background:#ff4fa3; color:white; border:none; width:45px; height:45px; border-radius:50%; margin-left:8px; cursor:pointer;">➤</button>
        </form>
        <script>document.getElementById('end').scrollIntoView();</script>
    </body></html>
    """)

@app.get("/encuentros")
async def encuentros(request: Request):
    user = request.session.get("user")
    others = [u for u in profiles.keys() if u != user and u not in profiles[user].get("likes", set())]
    if not others:
        return HTMLResponse(f"<html>{ESTILOS}<body><div class='card'><h3>¡Vaya!</h3><p>No hay más personas por ahora. ¡Vuelve más tarde!</p><a href='/' class='btn-pink'>Volver al Chat</a></div></body></html>")
    
    target = random.choice(others)
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="card">
            <div style="width:100px; height:100px; background:#ff4fa3; border-radius:50%; margin:0 auto 15px; display:flex; align-items:center; justify-content:center; color:white; font-size:40px;">👤</div>
            <h2>{target}</h2>
            <p style="color:#666;">"¡Hola! Busco conocer gente nueva en LoveConnect."</p>
            <div style="display:flex; justify-content:space-around;">
                <a href="/encuentros" class="btn-sec" style="width:40%; text-decoration:none; text-align:center;">⏭️ Saltar</a>
                <form action="/like/{target}" method="post" style="width:40%;"><button class="btn-pink" style="width:100%; margin:0;">❤️ Like</button></form>
            </div>
        </div>
    </body></html>
    """)

@app.post("/like/{target}")
async def give_like(request: Request, target: str):
    user = request.session.get("user")
    if user and target in profiles:
        profiles[user].setdefault("likes", set()).add(target)
        # Verificar Match
        if user in profiles[target].get("likes", set()):
            stats["matches_today"] += 1
            return HTMLResponse(f"<html>{ESTILOS}<body style='background:#ff4fa3; color:white; text-align:center; padding-top:100px;'><h1>💘 ¡ES UN MATCH!</h1><p>Tú y {target} se gustan.</p><a href='/perfil' class='btn-pink' style='background:white; color:#ff4fa3;'>Ver mi Perfil</a></body></html>")
    return RedirectResponse("/encuentros", status_code=303)

@app.get("/perfil")
async def perfil(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"votes": 0, "points": 0})
    # Buscar matches
    matches = [u for u in profiles.keys() if u != user and target_in_user := (user in profiles[u].get("likes", set())) and user_in_target := (u in profiles[user].get("likes", set()))]
    
    matches_html = "".join([f"<div style='border-bottom:1px solid #eee; padding:10px; display:flex; justify-content:space-between; align-items:center;'><span>{m}</span> <a href='/chat-privado/{m}' style='text-decoration:none;'>💬 Hablar</a></div>" for m in matches])

    return HTMLResponse(f"""
    <html>{ESTILOS}<body>
        <div class="card">
            <a href="/" style="float:left; text-decoration:none;">⬅️</a>
            <h2 style="color:#ff4fa3;">{user}</h2>
            <div style="background:#fff0f6; padding:15px; border-radius:20px; margin-bottom:20px;">
                <span style="font-size:20px;">⭐</span><br><b>{p.get('points', 0)} Puntos</b>
            </div>
            <h3 style="text-align:left; font-size:14px; color:#999;">MIS MATCHES 💘</h3>
            <div style="text-align:left;">{matches_html if matches_html else "<p style='color:#ccc; font-size:12px;'>Aún no tienes matches. ¡Ve a Encuentros!</p>"}</div>
            <a href="/encuentros" class="btn-pink">🔥 Buscar Pareja</a>
        </div>
    </body></html>
    """)

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    ahora = time.time()
    if user in last_msg_time and ahora - last_msg_time[user] < 2: return RedirectResponse("/", status_code=303)
    if user and msg.strip():
        last_msg_time[user] = ahora
        chat_log.append({"user": user, "text": msg})
        stats["messages_today"] += 1
        if len(chat_log) > 40: chat_log.pop(0)
    return RedirectResponse("/", status_code=303)

@app.get("/login-page")
async def login_page():
    return HTMLResponse(f"<html>{ESTILOS}<body style='display:flex; align-items:center; justify-content:center; height:100vh;'><div class='card'><h1>💖</h1><h2>LoveConnect</h2><form action='/login' method='post'><input name='username' placeholder='Tu nombre' required style='padding:12px; border-radius:15px; border:1px solid #eee; width:85%;'><br><button class='btn-pink'>Entrar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles: profiles[username] = {"votes": 0, "likes": set(), "points": 0}
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
