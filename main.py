import os, uvicorn, time, random
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-breaker-final-key")

# --- BASES DE DATOS ---
chat_log = []
profiles = {} # {user: {"likes": set(), "points": 0}}
online_users = set()
stats = {"msgs": 0, "matches": 0}

# --- ESTILOS ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background:#fff0f6; margin:0; text-align:center; }
    .card { max-width:350px; margin:20px auto; padding:20px; background:white; border-radius:25px; box-shadow:0 10px 20px rgba(0,0,0,0.05); }
    .btn-pink { background:#ff4fa3; color:white; border:none; padding:12px; border-radius:20px; width:90%; font-weight:bold; cursor:pointer; text-decoration:none; display:inline-block; }
    #online { color: #2ecc71; font-weight: bold; font-size: 14px; padding: 10px; }
    .bubble { padding:10px; margin:5px; border-radius:15px; max-width:80%; clear:both; }
    .mine { background:#ff4fa3; color:white; float:right; }
    .others { background:#eee; color:#333; float:left; }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")
    
    online_users.add(user) # Usuario entra a la lista de conectados
    
    chat_html = "".join([f'<div class="bubble {"mine" if m["user"]==user else "others"}"><b>{m["user"]}:</b> {m["text"]}</div>' for m in chat_log])

    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div style="background:white; border-bottom:1px solid #eee;">
            <div id="online">🟢 0 personas conectadas</div>
            <div style="font-size:10px; color:#ff4fa3; padding-bottom:5px;">🔥 {stats['msgs']} mensajes hoy | ❤️ {stats['matches']} matches</div>
        </div>
        
        <div id="chat-box" style="height:55vh; overflow-y:auto; padding:15px;">{chat_html}<div id="end"></div></div>
        
        <form action="/send" method="post" style="padding:10px; background:white; display:flex;">
            <input name="msg" placeholder="Mensaje..." required style="flex:1; padding:10px; border-radius:20px; border:1px solid #eee;">
            <button style="background:#ff4fa3; color:white; border:none; border-radius:50%; width:40px; margin-left:5px;">➤</button>
        </form>
        
        <div style="padding:10px;">
            <a href="/swipe" class="btn-pink" style="width:45%; font-size:12px;">🔥 Swipe</a>
            <a href="/perfil" class="btn-pink" style="width:45%; font-size:12px; background:#666;">👤 Perfil</a>
        </div>

        <script>
            document.getElementById('end').scrollIntoView();
            // MEJORA CHATGPT: Actualizar online cada 5 segundos
            function actualizarOnline(){{
                fetch("/online_count").then(r=>r.json()).then(data=>{{
                    document.getElementById("online").innerText = "🟢 " + data.online + " personas conectadas ahora";
                }});
            }}
            setInterval(actualizarOnline, 5000);
            actualizarOnline();
        </script>
    </body></html>
    """)

@app.get("/online_count")
def online_count():
    return {"online": len(online_users)}

@app.get("/swipe")
async def swipe_page(request: Request):
    user = request.session.get("user")
    others = [u for u in profiles.keys() if u != user and u not in profiles[user].get("likes", set())]
    if not others:
        return HTMLResponse(f"<html>{ESTILOS}<body><div class='card'><h3>¡No hay más perfiles!</h3><a href='/' class='btn-pink'>Volver</a></div></body></html>")
    
    target = random.choice(others)
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="card">
            <h1>👤</h1>
            <h2>{target}</h2>
            <p>¿Te gusta este perfil?</p>
            <div style="display:flex; justify-content:space-between;">
                <button class="btn-pink" style="background:#ccc; width:45%;" onclick="location.reload()">⏭️ No</button>
                <form action="/like/{target}" method="post" style="width:45%;"><button class="btn-pink">❤️ Sí</button></form>
            </div>
        </div>
    </body></html>
    """)

@app.post("/like/{target}")
async def like_user(request: Request, target: str):
    user = request.session.get("user")
    if user:
        profiles[user]["likes"].add(target)
        # SISTEMA DE MATCH REAL:
        if user in profiles[target]["likes"]:
            stats["matches"] += 1
            return HTMLResponse(f"<html>{ESTILOS}<body style='background:#ff4fa3; color:white; text-align:center; padding-top:100px;'><h1>💘 ¡MATCH REAL!</h1><p>Ahora puedes hablar con {target}</p><a href='/' class='btn-pink' style='background:white; color:#ff4fa3;'>Ir al Chat</a></body></html>")
    return RedirectResponse("/swipe", status_code=303)

@app.get("/perfil")
async def perfil(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"points": 0})
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='card'><h2>{user}</h2><p>Puntos: {p['points']}</p><a href='/' class='btn-pink'>Volver</a></div></body></html>")

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    if user and msg.strip():
        chat_log.append({"user": user, "text": msg})
        stats["msgs"] += 1
        if len(chat_log) > 25: chat_log.pop(0)
    return RedirectResponse("/", status_code=303)

@app.get("/login-page")
async def login_p():
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='card'><h2>💖 LoveConnect</h2><form action='/login' method='post'><input name='username' required placeholder='Tu nombre'><br><br><button class='btn-pink'>Entrar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles: profiles[username] = {"likes": set(), "points": 0}
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
