import os, uvicorn, time
from fastapi import FastAPI, Form, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Llave secreta para mantener la sesión activa sin errores
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_ultra_2026")

# --- BASE DE DATOS EN MEMORIA (Optimizado para Railway Free) ---
chat_log = []
priv_chats = {} 
profiles = {} 
online = {}

# --- PUNTO 4: ESTILOS CON ANIMACIONES Y RANKING ---
ESTILOS = """
<style>
    :root { --p: #ff4fa3; --bg: #fff0f6; }
    body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin:0; text-align:center; color:#444; overflow-x:hidden; }
    .nav { background:#fff; padding:12px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; sticky; top:0; z-index:100; }
    .card { width:90%; max-width:340px; margin:20px auto; background:#fff; border-radius:25px; box-shadow:0 10px 30px rgba(0,0,0,0.08); transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); position:relative; }
    .card:active { transform: scale(1.05) rotate(2deg); }
    .btn { background: var(--p); color:#fff; border:none; padding:12px 25px; border-radius:25px; cursor:pointer; font-weight:bold; text-decoration:none; display:inline-block; }
    .chat-box { height:65vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column; gap:10px; }
    .bubble { padding:10px 15px; border-radius:20px; font-size:14px; max-width:80%; position:relative; animation: pop 0.3s ease; }
    @keyframes pop { from { transform:scale(0.8); opacity:0; } to { transform:scale(1); opacity:1; } }
    .mine { background: var(--p); color:#fff; align-self:flex-end; border-bottom-right-radius:2px; }
    .others { background:#fff; align-self:flex-start; border-bottom-left-radius:2px; box-shadow:0 2px 5px rgba(0,0,0,0.05); }
    .rank-badge { background:#ffd700; color:#000; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:bold; }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    online[user] = time.time()
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><b>💖 LoveConnect</b> <small id="on">🟢 --</small></div>
        <div id="sw" style="margin-top:20px;">
            <div class="card" id="main-card">
                <div style="height:250px; background:linear-gradient(45deg, #ff4fa3, #ff85b9); color:#fff; font-size:100px; display:flex; align-items:center; justify-content:center; border-radius:25px 25px 0 0;" id="av">👤</div>
                <div style="padding:20px; text-align:left;">
                    <h3 id="nom" style="margin:0;">Cargando...</h3>
                    <p id="bio" style="font-size:14px; color:#666; margin:10px 0;"></p>
                </div>
                <div style="padding:0 0 25px 0; display:flex; justify-content:center; gap:20px;">
                    <button class="btn" style="background:#eee; color:#444;" onclick="sig('left')">❌</button>
                    <button class="btn" onclick="like()">❤️</button>
                </div>
            </div>
        </div>
        <div style="position:fixed; bottom:20px; width:100%; display:flex; justify-content:center; gap:12px;">
            <a href="/chat" class="btn" style="background:#fff; color:var(--p); border:2px solid var(--p);">💬 Chat</a>
            <a href="/privados" class="btn" style="background:#333;">✉️ Privados</a>
            <a href="/perfil" class="btn" style="background:var(--p);">👤 Perfil</a>
        </div>
        <script>
            let ps = [], i = 0;
            async function load() {{
                const r = await fetch("/api/ps");
                ps = await r.json();
                show();
            }}
            function show() {{
                const card = document.getElementById("main-card");
                if (i >= ps.length) {{ document.getElementById("sw").innerHTML = "<h3>✨ ¡Has visto a todos!</h3><button onclick='location.reload()' class='btn'>Refrescar</button>"; return; }}
                document.getElementById("av").innerText = ps[i].nombre[0].toUpperCase();
                document.getElementById("nom").innerText = ps[i].nombre;
                document.getElementById("bio").innerText = ps[i].bio || "¡Hola! Quiero conocer gente nueva.";
            }}
            async function like() {{
                const r = await fetch("/api/like/"+ps[i].nombre);
                const d = await r.json();
                if (d.m) alert("💘 ¡MATCH CON " + ps[i].nombre + "!");
                sig('right');
            }}
            function sig(dir) {{
                i++; show();
            }}
            setInterval(async () => {{
                const r = await fetch("/api/st");
                const d = await r.json();
                document.getElementById("on").innerText = "🟢 " + d.o + " activos";
            }}, 5000);
            load();
        </script>
    </body></html>
    """)

# --- PUNTO 3: PROTECCIÓN ANTI-SPAM Y PERFIL ---
@app.get("/perfil")
async def perfil_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    p = profiles.get(user, {"bio": "Sin bio", "points": 0})
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><a href="/" style="text-decoration:none;">⬅️</a> <b>Mi Perfil</b> <span></span></div>
        <div class="card" style="padding:25px; margin-top:30px;">
            <div style="width:100px; height:100px; background:var(--p); border-radius:50%; margin:0 auto; font-size:50px; color:#fff; display:flex; align-items:center; justify-content:center;">{user[0].toUpperCase()}</div>
            <h2 style="margin:15px 0;">{user} <span class="rank-badge">LVL {1 + (p['points']//10)}</span></h2>
            <p>Puntos: <b>{p['points']}</b></p>
            <form action="/update-bio" method="post">
                <textarea name="bio" maxlength="100" style="width:100%; height:80px; border-radius:15px; border:1px solid #ddd; padding:10px; font-family:inherit;">{p['bio']}</textarea>
                <button class="btn" style="width:100%; margin-top:10px;">Actualizar Bio</button>
            </form>
        </div>
    </body></html>
    """)

@app.post("/update-bio")
async def update_bio(request: Request, bio: str = Form(...)):
    user = request.session.get("user")
    if user in profiles: profiles[user]["bio"] = bio[:100]
    return RedirectResponse("/perfil", status_code=303)

# --- CHATS PRIVADOS (Admin & Matches) ---
@app.get("/privados")
async def list_priv(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    
    # Silver Breaker (Admin) puede ver a todos
    if user == "Silver Breaker":
        contacts = [u for u in profiles.keys() if u != user]
    else:
        # Solo aparecen si hay match mutuo
        contacts = [u for u in profiles[user]["likes"] if user in profiles.get(u, {}).get("likes", set())]
    
    links = "".join([f'<a href="/chat/{u}" class="card" style="display:block; padding:15px; text-decoration:none; color:#444;">💬 Chat con {u}</a>' for u in contacts])
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><a href='/'>⬅️</a><b>Mensajes Privados</b><span></span></div>{links if links else '<p style=margin-top:50px;>No tienes chats privados aún. ¡Consigue un match!</p>'}</body></html>")

@app.get("/chat/{target}")
async def private_chat(request: Request, target: str):
    user = request.session.get("user")
    pair = tuple(sorted((user, target)))
    msgs = priv_chats.get(pair, [])
    html_msgs = "".join([f'<div class="bubble {"mine" if m["u"]==user else "others"}"><b>{m["u"] if m["u"]!=user else ""}</b><br>{m["t"]}</div>' for m in msgs])
    return HTMLResponse(f"""
    <html>{ESTILOS}<body>
        <div class="nav"><a href="/privados">⬅️</a><b>{target}</b><span></span></div>
        <div class="chat-box" id="cb">{html_msgs}<div id="e"></div></div>
        <form action="/send-p/{target}" method="post" style="display:flex; padding:15px; background:#fff; border-top:1px solid #eee;">
            <input name="msg" placeholder="Escribe..." required style="flex:1; padding:12px; border-radius:20px; border:1px solid #ddd; outline:none;">
            <button class="btn" style="margin-left:10px;">➤</button>
        </form>
        <script>document.getElementById("e").scrollIntoView();</script>
    </body></html>
    """)

@app.post("/send-p/{target}")
async def send_p(request: Request, target: str, msg: str = Form(...)):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    # Limitar longitud para evitar saturación
    msg = msg.strip()[:200]
    if not msg: return RedirectResponse(f"/chat/{target}")
    
    pair = tuple(sorted((user, target)))
    if pair not in priv_chats: priv_chats[pair] = []
    priv_chats[pair].append({"u": user, "t": msg})
    return RedirectResponse(f"/chat/{target}", status_code=303)

# --- API Y RUTAS BASE ---
@app.get("/api/ps")
def api_ps(request: Request):
    u = request.session.get("user")
    # No mostrarse a sí mismo ni a los que ya les dio like
    return [{"nombre": n, "bio": p["bio"]} for n, p in profiles.items() if n != u and n not in profiles.get(u, {}).get("likes", set())]

@app.get("/api/like/{t}")
def api_like(request: Request, t: str):
    u = request.session.get("user")
    if u not in profiles: return {"m": False}
    profiles[u]["likes"].add(t)
    # Match si el otro también dio like
    is_match = u in profiles.get(t, {}).get("likes", set())
    if is_match: profiles[u]["points"] += 5; profiles[t]["points"] += 5
    return {"m": is_match}

@app.get("/api/st")
def api_st():
    act = len([t for t in online.values() if time.time() - t < 60])
    return {"o": act}

@app.get("/chat")
async def chat_g(request: Request):
    u = request.session.get("user")
    if not u: return RedirectResponse("/login")
    msgs = "".join([f'<div class="bubble {"mine" if m["u"]==u else "others"}"><small><b>{m["u"]}</b></small><br>{m["t"]}</div>' for m in chat_log])
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><a href='/'>⬅️</a><b>Chat Grupal</b><span></span></div><div class='chat-box'>{msgs}<div id='e'></div></div><form action='/sg' method='post' style='display:flex; padding:15px; background:#fff;'><input name='m' placeholder='Mensaje...' required style='flex:1; padding:12px; border-radius:20px; border:1px solid #ddd;'><button class='btn' style='margin-left:10px;'>➤</button></form><script>document.getElementById('e').scrollIntoView();</script></body></html>")

@app.post("/sg")
async def sg(request: Request, m: str = Form(...)):
    u = request.session.get("user")
    # Anti-spam: Max 150 caracteres y limpiar espacios
    clean_m = m.strip()[:150]
    if u and clean_m:
        chat_log.append({"u": u, "t": clean_m})
        if len(chat_log) > 25: chat_log.pop(0) # Mantener solo 25 para no saturar
    return RedirectResponse("/chat", status_code=303)

@app.get("/login")
def log_p(): 
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='card' style='padding:30px; margin-top:100px;'><h2>💖 LoveConnect</h2><form action='/login' method='post'><input name='u' placeholder='Tu Nombre' required style='padding:12px; width:85%; border-radius:15px; border:1px solid #ddd; outline:none;'><br><br><button class='btn' style='width:90%'>Empezar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, u: str = Form(...)):
    user_id = u.strip()[:15] # Limitar nombre a 15 caracteres
    request.session["user"] = user_id
    if user_id not in profiles: 
        profiles[user_id] = {"likes": set(), "points": 0, "bio": "¡Hola! Estoy en LoveConnect."}
    return RedirectResponse("/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
