import os, uvicorn, time, random
from datetime import datetime
from fastapi import FastAPI, Form, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-breaker-ultra-v3")

# --- BASES DE DATOS ---
chat_log = []
profiles = {} # {user: {"likes": set(), "points": 0, "bio": "", "avatar": ""}}
online_users = set()
stats = {"msgs": 0, "matches": 0}

# --- ESTILOS "PREMIUM" UNIFICADOS ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background:#fff0f6; margin:0; text-align:center; color: #444; }
    .nav { background:white; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; position:sticky; top:0; z-index:100; align-items:center; }
    .card-swipe { width:320px; margin:20px auto; background:white; border-radius:30px; box-shadow:0 15px 35px rgba(0,0,0,0.1); overflow:hidden; transition: 0.3s; }
    .avatar-big { width:100%; height:320px; background:#ff4fa3; display:flex; align-items:center; justify-content:center; font-size:100px; color:white; }
    .info-box { padding:20px; text-align:left; }
    .btn-circle { width:60px; height:60px; border-radius:50%; border:none; cursor:pointer; font-size:24px; box-shadow:0 5px 15px rgba(0,0,0,0.1); transition:0.2s; display:flex; align-items:center; justify-content:center; }
    .btn-circle:active { transform: scale(0.9); }
    .btn-no { background:white; color:#ff4444; }
    .btn-yes { background:#ff4fa3; color:white; }
    #online-tag { color: #2ecc71; font-weight: bold; font-size:14px; }
    .btn-main { background:#ff4fa3; color:white; border:none; padding:12px 25px; border-radius:25px; text-decoration:none; font-weight:bold; display:inline-block; }
    .chat-msg { margin:10px; display:flex; flex-direction:column; }
    .bubble { display:inline-block; padding:10px 15px; border-radius:20px; box-shadow:0 2px 5px rgba(0,0,0,0.05); max-width:80%; line-height:1.4; }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")
    online_users.add(user)
    
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav">
            <b style="color:#ff4fa3;">💖 LoveConnect</b>
            <span id="online-tag">🟢 Cargando...</span>
        </div>
        
        <div style="padding:10px;">
            <div id="swipe-area">
                <div class="card-swipe" id="perfil-card">
                    <div class="avatar-big" id="avatar-view">👤</div>
                    <div class="info-box">
                        <h2 id="nombre-view" style="margin:0;">Buscando...</h2>
                        <p id="bio-view" style="color:#666;">Cargando perfiles...</p>
                    </div>
                    <div style="display:flex; justify-content:space-evenly; padding-bottom:25px;">
                        <button class="btn-circle btn-no" onclick="siguiente()">❌</button>
                        <button class="btn-circle btn-yes" onclick="darLike()">❤️</button>
                    </div>
                </div>
            </div>
        </div>

        <div style="position:fixed; bottom:20px; width:100%; display:flex; justify-content:center; gap:10px; z-index:10;">
            <a href="/chat" class="btn-main" style="background:white; color:#ff4fa3; border:1px solid #ff4fa3; box-shadow:0 4px 10px rgba(0,0,0,0.1);">💬 Chat</a>
            <a href="/perfil" class="btn-main" style="box-shadow:0 4px 10px rgba(255,79,163,0.3);">👤 Perfil</a>
        </div>

        <script>
            let perfiles = [];
            let index = 0;

            async function cargarPerfiles() {{
                const res = await fetch("/api/perfiles");
                perfiles = await res.json();
                mostrarPerfil();
            }}

            function mostrarPerfil() {{
                if (index >= perfiles.length) {{
                    document.getElementById("swipe-area").innerHTML = "<div class='card-swipe' style='padding:40px;'><h3>🎉 ¡Has visto a todos!</h3><p>Vuelve más tarde.</p><button onclick='location.reload()' class='btn-main'>Refrescar</button></div>";
                    return;
                }}
                let p = perfiles[index];
                document.getElementById("avatar-view").innerText = p.nombre[0].toUpperCase();
                document.getElementById("nombre-view").innerText = p.nombre;
                document.getElementById("bio-view").innerText = p.bio || "Explorando LoveConnect 🚀";
            }}

            async function darLike() {{
                let target = perfiles[index].nombre;
                const res = await fetch("/api/like", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{target: target}})
                }});
                const data = await res.json();
                if (data.match) {{
                    alert("💘 ¡ES UN MATCH CON " + target + "!");
                }}
                siguiente();
            }}

            function siguiente() {{
                index++;
                mostrarPerfil();
            }}

            function updateOnline() {{
                fetch("/api/stats").then(r=>r.json()).then(d=>{{
                    document.getElementById("online-tag").innerText = "🟢 " + d.online + " activos";
                }});
            }}

            setInterval(updateOnline, 5000);
            updateOnline();
            cargarPerfiles();
        </script>
    </body></html>
    """)

# --- VISTAS ADICIONALES ---

@app.get("/perfil")
async def perfil_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")
    p = profiles.get(user, {})
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><a href="/" style="text-decoration:none;">⬅️</a> <b>Mi Perfil</b> <span></span></div>
        <div class="card-swipe" style="margin-top:20px; padding:20px;">
            <div class="avatar-big" style="height:120px; width:120px; border-radius:50%; margin: 0 auto; font-size:50px;">{user[0].toUpperCase()}</div>
            <h2 style="color:#ff4fa3; margin:10px 0;">{user}</h2>
            <div style="background:#fff0f6; padding:10px; border-radius:15px; margin-bottom:15px;">⭐ Puntos: {p.get('points', 0)}</div>
            <form action="/update-bio" method="post" style="text-align:left;">
                <label style="font-size:12px; color:#999; margin-left:10px;">MI BIOGRAFÍA</label>
                <textarea name="bio" style="width:100%; height:100px; border-radius:15px; border:1px solid #eee; padding:15px; box-sizing:border-box; margin-top:5px; font-family:inherit;">{p.get('bio', '')}</textarea>
                <button class="btn-main" style="width:100%; margin-top:15px;">Guardar Cambios</button>
            </form>
        </div>
    </body></html>
    """)

@app.get("/chat")
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")
    
    chat_html = "".join([f'<div class="chat-msg" style="align-items:{"flex-end" if m["user"]==user else "flex-start"}">' +
                         f'<div class="bubble" style="background:{"#ff4fa3" if m["user"]==user else "white"}; color:{"white" if m["user"]==user else "#444"}">' +
                         f'<small style="font-size:10px; opacity:0.7;">{m["user"]}</small><br>{m["text"]}</div></div>' for m in chat_log])
    
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><a href="/" style="text-decoration:none;">⬅️</a> <b>Chat Grupal</b> <span id="online-tag" style="font-size:10px;">🟢</span></div>
        <div id="chat-box" style="height:75vh; overflow-y:auto; padding:10px; display:flex; flex-direction:column; background:#f9f9f9;">{chat_html}<div id="end"></div></div>
        <form action="/send-chat" method="post" style="position:fixed; bottom:0; width:100%; display:flex; padding:10px; background:white; box-sizing:border-box; border-top:1px solid #eee;">
            <input name="msg" placeholder="Escribe un mensaje..." required style="flex:1; padding:12px; border-radius:25px; border:1px solid #eee; outline:none;">
            <button class="btn-circle btn-yes" style="width:45px; height:45px; margin-left:10px; font-size:18px;">➤</button>
        </form>
        <script>document.getElementById("end").scrollIntoView();</script>
    </body></html>
    """)

# --- LÓGICA DE BACKEND ---

@app.post("/update-bio")
async def update_bio(request: Request, bio: str = Form(...)):
    user = request.session.get("user")
    if user in profiles: profiles[user]["bio"] = bio
    return RedirectResponse("/perfil", status_code=303)

@app.post("/send-chat")
async def send_chat(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    if user and msg.strip():
        chat_log.append({"user": user, "text": msg})
        if len(chat_log) > 40: chat_log.pop(0)
    return RedirectResponse("/chat", status_code=303)

@app.get("/api/perfiles")
def get_perfiles(request: Request):
    user = request.session.get("user")
    disponibles = [{"nombre": u, "bio": p.get("bio", "")} for u, p in profiles.items() if u != user and u not in profiles[user]["likes"]]
    return disponibles

@app.post("/api/like")
async def api_like(request: Request, data: dict = Body(...)):
    user = request.session.get("user")
    target = data.get("target")
    is_match = False
    if user and target in profiles:
        profiles[user]["likes"].add(target)
        if user in profiles[target]["likes"]:
            stats["matches"] += 1
            is_match = True
    return {"status": "ok", "match": is_match}

@app.get("/api/stats")
def get_stats():
    return {"online": len(online_users), "matches": stats["matches"]}

@app.get("/login-page")
async def login_p():
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='card-swipe' style='margin-top:100px; padding:30px;'><h2>💖 LoveConnect</h2><form action='/login' method='post'><input name='username' placeholder='Tu nombre' required style='padding:12px; width:80%; border-radius:15px; border:1px solid #eee;'><br><br><button class='btn-main'>Entrar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles:
        profiles[username] = {"likes": set(), "points": 0, "bio": "¡Hola! Estoy usando LoveConnect."}
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
