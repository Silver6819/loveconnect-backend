import os, uvicorn, time, random
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Llave secreta para las sesiones
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_master_ultra_2026")

# --- BASE DE DATOS TEMPORAL (Se reinicia al apagar el server) ---
chat_log = []
priv_chats = {} 
profiles = {} 
online = {}
blacklist = set() # Usuarios en la Sala de Castigo

ESTILOS = """
<style>
    :root { --p: #ff4fa3; --admin: #6c5ce7; --bg: #fff5f8; --dark: #1e272e; }
    body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin:0; text-align:center; color:#333; }
    .nav { background:#fff; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; position:sticky; top:0; z-index:100; align-items:center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .card { width:92%; max-width:360px; margin:20px auto; background:#fff; border-radius:30px; box-shadow:0 12px 40px rgba(0,0,0,0.1); overflow:hidden; }
    .btn { background: var(--p); color:#fff; border:none; padding:14px 28px; border-radius:30px; cursor:pointer; font-weight:bold; text-decoration:none; display:inline-block; transition: 0.3s; font-size: 15px; }
    .btn:active { transform: scale(0.92); }
    .btn-sec { background:#fff; color:var(--p); border:2px solid var(--p); }
    .img-perfil { width:100%; height:350px; object-fit: cover; background:#f0f0f0; display:flex; align-items:center; justify-content:center; font-size:100px; }
    .chat-box { height:62vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column; gap:12px; background:#fff; }
    .bubble { padding:12px 16px; border-radius:22px; font-size:14px; max-width:75%; line-height:1.5; }
    .mine { background: var(--p); color:#fff; align-self:flex-end; border-bottom-right-radius:4px; }
    .others { background:#f1f2f6; align-self:flex-start; border-bottom-left-radius:4px; }
    .badge-admin { background: var(--admin); color: white; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold; }
    .lvl-tag { color: var(--p); font-weight: bold; font-size: 14px; }
    .castigado-bg { background: var(--dark); color: #ff4757; height: 100vh; display: flex; align-items: center; justify-content: center; flex-direction: column; padding: 20px; }
</style>
"""

# --- MIDDLEWARE DE SEGURIDAD (Check de Ban y Sesión) ---
@app.middleware("http")
async def check_ban(request: Request, call_next):
    user = request.session.get("user")
    # Si está baneado y no está ya en la página de castigo, lo mandamos allá
    if user in blacklist and not request.url.path.startswith("/castigo") and not request.url.path.startswith("/login"):
        return RedirectResponse("/castigo")
    return await call_next(request)

# --- RUTAS DE ACCESO (WELCOME, LOGIN, REGISTRO) ---
@app.get("/")
def root(request: Request):
    if not request.session.get("user"): return RedirectResponse("/welcome")
    return RedirectResponse("/swipe")

@app.get("/welcome")
def welcome_page():
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body style="display:flex; align-items:center; justify-content:center; height:100vh; margin:0;">
        <div class="card" style="padding:40px; box-shadow:none; background:transparent;">
            <h1 style="color:var(--p); font-size:35px; margin:0;">❤️ LoveConnect</h1>
            <p style="color:#888; margin-bottom:40px;">Encuentra tu match hoy</p>
            <a href="/login" class="btn" style="width:100%; margin-bottom:15px;">Empezar</a><br>
            <a href="/registro" class="btn btn-sec" style="width:100%;">Crear cuenta</a>
        </div>
    </body></html>
    """)

@app.get("/login")
def login_view():
    return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='card' style='margin-top:100px; padding:40px;'><h2>Iniciar Sesión</h2><form action='/login' method='post'><input name='u' placeholder='Tu nombre' required style='width:100%; padding:15px; border-radius:15px; border:1px solid #ddd; outline:none; text-align:center;'><br><br><button class='btn' style='width:100%'>Entrar</button></form><br><a href='/welcome' style='color:#aaa; text-decoration:none; font-size:12px;'>Volver</a></div></body></html>")

@app.post("/login")
async def do_login(request: Request, u: str = Form(...)):
    user = u.strip()[:15]
    request.session["user"] = user
    if user not in profiles: profiles[user] = {"likes": set(), "points": 0, "bio": "El Salvador", "foto": "", "matches": 0}
    return RedirectResponse("/swipe", status_code=303)

@app.get("/registro")
def registro_view():
    return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='card' style='margin-top:50px; padding:40px;'><h2>Crea tu Perfil</h2><form action='/login' method='post'><input name='u' placeholder='Nombre de usuario' required style='width:100%; padding:15px; border-radius:15px; border:1px solid #ddd; margin-bottom:15px;'><br><button class='btn' style='width:100%'>Registrarme</button></form></div></body></html>")

# --- SALA DE CASTIGO ---
@app.get("/castigo")
def castigo_page():
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body><div class="castigado-bg">
        <h1 style="font-size:50px; margin:0;">⛓️</h1>
        <h2 style="color:white;">SALA DE CASTIGO</h2>
        <p style="color:#666; max-width:300px;">Has sido restringido por el Administrador Silver Breaker debido a mal comportamiento.</p>
        <br><a href="/login" class="btn" style="background:#444;">Intentar entrar</a>
    </div></body></html>
    """)

# --- SWIPE Y ALGORITMO ---
@app.get("/swipe")
async def swipe_page(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/welcome")
    online[user] = time.time()
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><b>💖 LoveConnect</b> <small id="on">🟢 --</small></div>
        <div id="sw"><div class="card"><div id="pic_cont"></div><div style="padding:20px; text-align:left;"><div style="display:flex; justify-content:space-between;"><h3 id="nom" style="margin:0;">...</h3><span id="lvl_display" class="lvl-tag"></span></div><p id="bio" style="font-size:14px; color:#777; margin-top:8px;"></p></div><div style="padding:0 0 30px 0; display:flex; justify-content:center; gap:25px;"><button class="btn" style="background:#f0f0f0; color:#444;" onclick="sig()">❌</button><button class="btn" onclick="like()">❤️</button></div></div></div>
        <div style="position:fixed; bottom:20px; width:100%; display:flex; justify-content:center; gap:12px;">
            <a href="/chat" class="btn" style="background:#fff; color:var(--p); border:2px solid var(--p);">💬 Chat</a>
            <a href="/privados" class="btn" style="background:#333;">✉️ Match</a>
            <a href="/perfil" class="btn">👤 Perfil</a>
        </div>
        <script>
            let ps = [], i = 0;
            async function load() {{ const r = await fetch("/api/ps"); ps = await r.json(); show(); }}
            function show() {{
                if (i >= ps.length) {{ document.getElementById("sw").innerHTML = "<div class='card' style='padding:60px;'><h3>✨ ¡No hay más perfiles!</h3><button onclick='location.reload()' class='btn'>Refrescar</button></div>"; return; }}
                let p = ps[i];
                document.getElementById("nom").innerText = p.nombre;
                document.getElementById("bio").innerText = p.bio;
                document.getElementById("lvl_display").innerText = "LVL " + p.lvl;
                document.getElementById("pic_cont").innerHTML = p.foto ? `<img src="${{p.foto}}" class="img-perfil">` : `<div class="img-perfil">👤</div>`;
            }}
            async function like() {{ const r = await fetch("/api/like/"+ps[i].nombre); const d = await r.json(); if (d.m) alert("💘 ¡ES UN MATCH!"); sig(); }}
            function sig() {{ i++; show(); }}
            setInterval(async () => {{ const r = await fetch("/api/st"); const d = await r.json(); document.getElementById("on").innerText = "🟢 " + d.o + " activos"; }}, 5000);
            load();
        </script>
    </body></html>
    """)

@app.get("/api/ps")
def api_peers(request: Request):
    user = request.session.get("user")
    output = []
    for n, p in profiles.items():
        if n == user or n in profiles.get(user, {}).get("likes", set()): continue
        if n in blacklist: continue # No mostrar baneados
        
        # Algoritmo de Score
        lvl_num = 999 if n == "Silver Breaker" else (1 + (p.get('points', 0) // 50))
        score = (lvl_num * 20) + (p.get('matches', 0) * 10) + random.randint(0, 50)
        
        output.append({"nombre": n, "bio": p["bio"], "foto": p["foto"], "lvl": "∞" if n == "Silver Breaker" else lvl_num, "score": score})
    return sorted(output, key=lambda x: x["score"], reverse=True)

# --- PERFIL Y CERRAR SESIÓN ---
@app.get("/perfil")
async def perfil_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/welcome")
    p = profiles.get(user, {})
    lvl = "∞" if user == "Silver Breaker" else (1 + (p.get('points', 0) // 50))
    badge = f'<span class="badge-admin">👑 LVL ∞</span>' if user == "Silver Breaker" else f'<span class="lvl-tag">LVL {lvl}</span>'
    
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><a href="/swipe" style="text-decoration:none; color:var(--p); font-size:20px;">⬅️</a> <b>Mi Perfil</b> <span></span></div>
        <div class="card" style="padding:30px;">
            <h2 style="margin:0;">{user}</h2>
            <div style="margin:10px 0 25px 0;">{badge}</div>
            <form action="/update-perfil" method="post" style="text-align:left;">
                <label style="font-size:11px; color:#aaa; font-weight:bold;">URL DE FOTO:</label>
                <input name="foto" value="{p.get('foto','')}" style="width:100%; padding:12px; border-radius:12px; border:1px solid #ddd; margin-bottom:15px; outline:none;">
                <label style="font-size:11px; color:#aaa; font-weight:bold;">BIO / UBICACIÓN:</label>
                <textarea name="bio" style="width:100%; height:90px; border-radius:12px; border:1px solid #ddd; padding:12px; outline:none; font-family:inherit;">{p.get('bio','')}</textarea>
                <button class="btn" style="width:100%; margin-top:25px;">Guardar Cambios</button>
            </form>
            <br><br><a href="/logout" style="color:#f44336; font-size:13px; text-decoration:none; font-weight:bold;">Cerrar Sesión</a>
        </div>
    </body></html>
    """)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/welcome")

# --- ADMINISTRACIÓN DE CASTIGO (SECRET) ---
@app.get("/admin/castigar/{target}")
def ban_user(request: Request, target: str):
    if request.session.get("user") == "Silver Breaker":
        blacklist.add(target)
        return {"msg": f"{target} ha sido enviado a la Sala de Castigo"}
    return {"msg": "No eres Silver Breaker"}

# --- LÓGICA DE MATCH Y CHATS (COMO ANTES) ---
@app.get("/api/like/{target}")
def api_like(request: Request, target: str):
    user = request.session.get("user")
    profiles[user]["likes"].add(target)
    match = user in profiles.get(target,{}).get("likes",set())
    if match: 
        profiles[user]["points"] += 15
        profiles[user]["matches"] += 1
        profiles[target]["matches"] += 1
    return {"m": match}

@app.get("/api/st")
def api_st():
    act = len([t for t in online.values() if time.time() - t < 60])
    return {"o": act}

@app.post("/update-perfil")
async def update_perfil(request: Request, bio: str = Form(...), foto: str = Form(...)):
    user = request.session.get("user")
    profiles[user].update({"bio": bio[:150], "foto": foto.strip()})
    return RedirectResponse("/perfil", status_code=303)

@app.get("/privados")
async def priv_list(request: Request):
    user = request.session.get("user")
    if user == "Silver Breaker":
        chats = [n for n in profiles.keys() if n != user]
    else:
        chats = [n for n in profiles[user]["likes"] if user in profiles.get(n,{}).get("likes",set())]
    lista = "".join([f'<a href="/chat_p/{c}" class="card" style="display:block; padding:18px; text-decoration:none; color:black; border-left:6px solid var(--p); text-align:left;">Chat con <b>{c}</b></a>' for c in chats])
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><a href='/swipe'>⬅️</a><b>Mensajes</b><span></span></div>{lista if lista else '<p style=margin-top:60px;>No tienes matches aún.</p>'}</body></html>")

@app.get("/chat_p/{target}")
async def private_chat(request: Request, target: str):
    user = request.session.get("user")
    pair = tuple(sorted((user, target)))
    msgs = priv_chats.get(pair, [])
    html_msgs = "".join([f'<div class="bubble {"mine" if m["u"]==user else "others"}"><b>{m["u"]}</b><br>{m["t"]}</div>' for m in msgs])
    return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='nav'><a href='/privados'>⬅️</a><b>{target}</b><span></span></div><div class='chat-box' id='cb'>{html_msgs}</div><form action='/send_p/{target}' method='post' style='display:flex; padding:15px; background:#fff; border-top:1px solid #eee;'><input name='msg' autocomplete='off' required style='flex:1; padding:12px; border-radius:25px; border:1px solid #ddd; outline:none;'><button class='btn' style='margin-left:10px;'>➤</button></form><script>document.getElementById('cb').scrollTop = document.getElementById('cb').scrollHeight;</script></body></html>")

@app.post("/send_p/{target}")
async def send_p(request: Request, target: str, msg: str = Form(...)):
    user = request.session.get("user")
    pair = tuple(sorted((user, target)))
    if pair not in priv_chats: priv_chats[pair] = []
    priv_chats[pair].append({"u": user, "t": msg[:250]})
    return RedirectResponse(f"/chat_p/{target}", status_code=303)

@app.get("/chat")
async def chat_g(request: Request):
    u = request.session.get("user")
    msgs = "".join([f'<div class="bubble {"mine" if m["u"]==u else "others"}"><b>{m["u"]} {"👑" if m["u"]=="Silver Breaker" else ""}</b><br>{m["t"]}</div>' for m in chat_log])
    return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='nav'><a href='/swipe'>⬅️</a><b>Chat Grupal</b><span></span></div><div class='chat-box' id='cb'>{msgs}</div><form action='/send' method='post' style='padding:15px; display:flex; background:#fff;'><input name='m' autocomplete='off' style='flex:1; padding:12px; border-radius:25px; border:1px solid #ddd; outline:none;'><button class='btn' style='margin-left:8px;'>➤</button></form><script>document.getElementById('cb').scrollTop = document.getElementById('cb').scrollHeight;</script></body></html>")

@app.post("/send")
async def send_msg(request: Request, m: str = Form(...)):
    u = request.session.get("user")
    if u and m: chat_log.append({"u": u, "t": m[:150]})
    if len(chat_log) > 30: chat_log.pop(0)
    return RedirectResponse("/chat", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
