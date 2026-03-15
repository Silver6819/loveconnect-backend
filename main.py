import os, uvicorn, time, random
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_omega_2026")

# --- BASE DE DATOS TEMPORAL ---
chat_log = []
priv_chats = {} 
profiles = {} 
online = {}

ESTILOS = """
<style>
    :root { --p: #ff4fa3; --admin: #6c5ce7; --bg: #fff5f8; }
    body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin:0; text-align:center; color:#333; }
    .nav { background:#fff; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; position:sticky; top:0; z-index:100; align-items:center; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .card { width:92%; max-width:360px; margin:20px auto; background:#fff; border-radius:30px; box-shadow:0 12px 40px rgba(0,0,0,0.1); overflow:hidden; }
    .btn { background: var(--p); color:#fff; border:none; padding:12px 28px; border-radius:30px; cursor:pointer; font-weight:bold; text-decoration:none; display:inline-block; transition: 0.3s; }
    .btn:active { transform: scale(0.92); }
    .img-perfil { width:100%; height:350px; object-fit: cover; background:#f0f0f0; display:flex; align-items:center; justify-content:center; font-size:100px; }
    .chat-box { height:62vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column; gap:12px; }
    .bubble { padding:12px 16px; border-radius:22px; font-size:14px; max-width:75%; line-height:1.5; }
    .mine { background: var(--p); color:#fff; align-self:flex-end; border-bottom-right-radius:4px; }
    .others { background:#fff; align-self:flex-start; border-bottom-left-radius:4px; box-shadow:0 3px 8px rgba(0,0,0,0.06); }
    .badge-admin { background: var(--admin); color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; }
    .lvl-tag { color: var(--p); font-weight: bold; font-size: 13px; }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    if user not in profiles: profiles[user] = {"likes": set(), "points": 0, "bio": "El Salvador", "foto": "", "matches": 0}
    online[user] = time.time()
    
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><b>💖 LoveConnect</b> <small id="on">🟢 --</small></div>
        <div id="sw">
            <div class="card">
                <div id="pic_cont"></div>
                <div style="padding:20px; text-align:left;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 id="nom" style="margin:0; font-size: 22px;">...</h3>
                        <span id="lvl_display" class="lvl-tag"></span>
                    </div>
                    <p id="bio" style="font-size:14px; color:#777; margin-top:8px;"></p>
                </div>
                <div style="padding:0 0 30px 0; display:flex; justify-content:center; gap:25px;">
                    <button class="btn" style="background:#f0f0f0; color:#444;" onclick="sig()">❌</button>
                    <button class="btn" onclick="like()">❤️</button>
                </div>
            </div>
        </div>
        <div style="position:fixed; bottom:20px; width:100%; display:flex; justify-content:center; gap:12px;">
            <a href="/chat" class="btn" style="background:#fff; color:var(--p); border:2px solid var(--p);">💬 Chat</a>
            <a href="/privados" class="btn" style="background:#333;">✉️ Match</a>
            <a href="/perfil" class="btn">👤 Perfil</a>
        </div>
        <script>
            let ps = [], i = 0;
            async function load() {{
                const r = await fetch("/api/ps");
                ps = await r.json();
                show();
            }}
            function show() {{
                if (i >= ps.length) {{ 
                    document.getElementById("sw").innerHTML = "<div class='card' style='padding:60px;'><h3>✨ ¡Visto todo!</h3><button onclick='location.reload()' class='btn'>Refrescar</button></div>"; 
                    return; 
                }}
                let p = ps[i];
                document.getElementById("nom").innerText = p.nombre;
                document.getElementById("bio").innerText = p.bio;
                document.getElementById("lvl_display").innerText = "LVL " + p.lvl;
                const cont = document.getElementById("pic_cont");
                cont.innerHTML = p.foto ? `<img src="${{p.foto}}" class="img-perfil">` : `<div class="img-perfil">👤</div>`;
            }}
            async function like() {{
                const r = await fetch("/api/like/"+ps[i].nombre);
                const d = await r.json();
                if (d.m) alert("💘 ¡ES UN MATCH!");
                sig();
            }}
            function sig() {{ i++; show(); }}
            setInterval(async () => {{
                const r = await fetch("/api/st");
                const d = await r.json();
                document.getElementById("on").innerText = "🟢 " + d.o + " activos";
            }}, 5000);
            load();
        </script>
    </body></html>
    """)

@app.get("/perfil")
async def perfil_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    p = profiles.get(user, {})
    lvl = "∞" if user == "Silver Breaker" else (1 + (p.get('points', 0) // 50))
    badge = f'<span class="badge-admin">👑 LVL ∞</span>' if user == "Silver Breaker" else f'<span class="lvl-tag">LVL {lvl}</span>'
    
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><a href="/" style="text-decoration:none; color:var(--p); font-size:20px;">⬅️</a> <b>Mi Perfil</b> <span></span></div>
        <div class="card" style="padding:30px;">
            <h2 style="margin:0;">{user}</h2>
            <div style="margin:10px 0 25px 0;">{badge}</div>
            <form action="/update-perfil" method="post" style="text-align:left;">
                <label style="font-size:11px; color:#aaa; font-weight:bold;">URL DE FOTO:</label>
                <input name="foto" value="{p.get('foto','')}" placeholder="https://..." style="width:100%; padding:12px; border-radius:12px; border:1px solid #ddd; margin-bottom:15px; outline:none;">
                <label style="font-size:11px; color:#aaa; font-weight:bold;">BIO / UBICACIÓN:</label>
                <textarea name="bio" style="width:100%; height:90px; border-radius:12px; border:1px solid #ddd; padding:12px; outline:none; font-family:inherit;">{p.get('bio','')}</textarea>
                <button class="btn" style="width:100%; margin-top:25px;">Guardar Cambios</button>
            </form>
            <br><br>
            <a href="/login" style="color:#f44336; font-size:13px; text-decoration:none; font-weight:bold;">Cerrar Sesión</a>
        </div>
    </body></html>
    """)

# --- APIs CON ALGORITMO DE SCORE ---
@app.get("/api/ps")
def api_peers(request: Request):
    user = request.session.get("user")
    output = []
    for n, p in profiles.items():
        if n == user or n in profiles.get(user, {}).get("likes", set()): continue
        
        # Algoritmo de Score (Sugerencia ChatGPT + Modo Admin)
        lvl_num = 999 if n == "Silver Breaker" else (1 + (p.get('points', 0) // 50))
        score = (lvl_num * 20) + (p.get('matches', 0) * 10) + random.randint(0, 50)
        
        output.append({
            "nombre": n, "bio": p["bio"], "foto": p["foto"], 
            "lvl": "∞" if n == "Silver Breaker" else lvl_num,
            "score": score
        })
    
    # Ordenar por Score (Los más altos primero)
    return sorted(output, key=lambda x: x["score"], reverse=True)

@app.get("/api/like/{target}")
def api_like(request: Request, target: str):
    user = request.session.get("user")
    if user not in profiles: return {"m": False}
    profiles[user]["likes"].add(target)
    match = user in profiles.get(target,{}).get("likes",set())
    if match: 
        profiles[user]["points"] += 15
        profiles[user]["matches"] = profiles[user].get("matches",0) + 1
        profiles[target]["matches"] = profiles[target].get("matches",0) + 1
    return {"m": match}

# --- RESTO DE FUNCIONES (SOPORTE) ---
@app.post("/update-perfil")
async def update_perfil(request: Request, bio: str = Form(...), foto: str = Form(...)):
    user = request.session.get("user")
    if user in profiles:
        profiles[user]["bio"] = bio[:150]
        profiles[user]["foto"] = foto.strip()
    return RedirectResponse("/perfil", status_code=303)

@app.get("/privados")
async def priv_list(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    if user == "Silver Breaker":
        chats = [n for n in profiles.keys() if n != user]
    else:
        chats = [n for n in profiles[user]["likes"] if user in profiles.get(n,{}).get("likes",set())]
    lista = "".join([f'<a href="/chat_p/{c}" class="card" style="display:block; padding:18px; text-decoration:none; color:black; border-left:6px solid var(--p); text-align:left;">Chat con <b>{c}</b></a>' for c in chats])
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><a href='/' style='text-decoration:none; color:var(--p); font-size:20px;'>⬅️</a><b>Mis Mensajes</b><span></span></div>{lista if lista else '<p style=margin-top:60px; color:#aaa;>No tienes matches aún.</p>'}</body></html>")

@app.get("/chat_p/{target}")
async def private_chat(request: Request, target: str):
    user = request.session.get("user")
    pair = tuple(sorted((user, target)))
    msgs = priv_chats.get(pair, [])
    html_msgs = "".join([f'<div class="bubble {"mine" if m["u"]==user else "others"}"><b>{m["u"]}</b><br>{m["t"]}</div>' for m in msgs])
    return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='nav'><a href='/privados' style='text-decoration:none; color:var(--p); font-size:20px;'>⬅️</a><b>{target}</b><span></span></div><div class='chat-box' id='cb'>{html_msgs}</div><form action='/send_p/{target}' method='post' style='display:flex; padding:15px; background:#fff; border-top:1px solid #eee;'><input name='msg' autocomplete='off' placeholder='Escribe un mensaje...' required style='flex:1; padding:12px; border-radius:25px; border:1px solid #ddd; outline:none;'><button class='btn' style='margin-left:10px;'>➤</button></form></body></html>")

@app.post("/send_p/{target}")
async def send_p(request: Request, target: str, msg: str = Form(...)):
    user = request.session.get("user")
    pair = tuple(sorted((user, target)))
    if pair not in priv_chats: priv_chats[pair] = []
    priv_chats[pair].append({"u": user, "t": msg[:250]})
    return RedirectResponse(f"/chat_p/{target}", status_code=303)

@app.get("/api/st")
def api_st():
    act = len([t for t in online.values() if time.time() - t < 60])
    return {"o": act}

@app.get("/chat")
async def chat_g(request: Request):
    u = request.session.get("user")
    if not u: return RedirectResponse("/login")
    msgs = "".join([f'<div class="bubble {"mine" if m["u"]==u else "others"}"><b>{m["u"]} {"👑" if m["u"]=="Silver Breaker" else ""}</b><br>{m["t"]}</div>' for m in chat_log])
    return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='nav'><a href='/' style='text-decoration:none; color:var(--p); font-size:20px;'>⬅️</a><b>Chat Grupal</b><span></span></div><div class='chat-box'>{msgs}</div><form action='/send' method='post' style='padding:15px; display:flex; background:#fff;'><input name='m' autocomplete='off' placeholder='Mensaje público...' style='flex:1; padding:12px; border-radius:25px; border:1px solid #ddd; outline:none;'><button class='btn' style='margin-left:8px;'>➤</button></form></body></html>")

@app.post("/send")
async def send_msg(request: Request, m: str = Form(...)):
    u = request.session.get("user")
    if u and m: chat_log.append({"u": u, "t": m[:150]})
    if len(chat_log) > 25: chat_log.pop(0)
    return RedirectResponse("/chat", status_code=303)

@app.get("/login")
def login_p(): return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='card' style='margin-top:120px; padding:40px;'><h2>💖 LoveConnect</h2><p style='color:#888; font-size:14px;'>Encuentra tu match hoy</p><br><form action='/login' method='post'><input name='u' placeholder='Escribe tu nombre' required style='width:100%; padding:14px; border-radius:15px; border:1px solid #ddd; outline:none; text-align:center; font-size:16px;'><br><br><button class='btn' style='width:100%; padding:15px;'>Empezar</button></form></div></body></html>")

@app.post("/login")
async def do_login(request: Request, u: str = Form(...)):
    user = u.strip()[:15]
    request.session["user"] = user
    if user not in profiles: profiles[user] = {"likes": set(), "points": 0, "bio": "El Salvador", "foto": "", "matches": 0}
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
