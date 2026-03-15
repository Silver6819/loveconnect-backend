import os, uvicorn, time
from fastapi import FastAPI, Form, Request, Body, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Llave de sesión estable para evitar errores de "None"
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_2026_key")

# --- BASE DE DATOS ---
chat_log = []
priv_chats = {} 
profiles = {} 
online = {}

# --- DISEÑO ACTUALIZADO CON SOPORTE PARA FOTOS ---
ESTILOS = """
<style>
    :root { --p: #ff4fa3; --bg: #fff0f6; }
    body { font-family: 'Segoe UI', sans-serif; background: var(--bg); margin:0; text-align:center; color:#444; }
    .nav { background:#fff; padding:12px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; position:sticky; top:0; z-index:100; }
    .card { width:90%; max-width:340px; margin:20px auto; background:#fff; border-radius:25px; box-shadow:0 10px 30px rgba(0,0,0,0.08); overflow:hidden; }
    .btn { background: var(--p); color:#fff; border:none; padding:12px 25px; border-radius:25px; cursor:pointer; font-weight:bold; text-decoration:none; display:inline-block; }
    .img-perfil { width:100%; height:300px; object-fit: cover; background:#eee; display:flex; align-items:center; justify-content:center; font-size:80px; }
    .chat-box { height:60vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column; gap:10px; }
    .bubble { padding:10px 15px; border-radius:20px; font-size:14px; max-width:80%; }
    .mine { background: var(--p); color:#fff; align-self:flex-end; border-bottom-right-radius:2px; }
    .others { background:#fff; align-self:flex-start; border-bottom-left-radius:2px; box-shadow:0 2px 5px rgba(0,0,0,0.05); }
</style>
"""

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login")
    if user not in profiles: profiles[user] = {"likes": set(), "points": 0, "bio": "El Salvador", "foto": ""}
    online[user] = time.time()
    
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><b>💖 LoveConnect</b> <small id="on">🟢 --</small></div>
        <div id="sw">
            <div class="card" id="main-card">
                <div id="pic_cont"></div>
                <div style="padding:20px; text-align:left;">
                    <h3 id="nom" style="margin:0;">Buscando...</h3>
                    <p id="bio" style="font-size:14px; color:#666;"></p>
                </div>
                <div style="padding:0 0 25px 0; display:flex; justify-content:center; gap:20px;">
                    <button class="btn" style="background:#ddd; color:#333;" onclick="sig()">❌</button>
                    <button class="btn" onclick="like()">❤️</button>
                </div>
            </div>
        </div>
        <div style="position:fixed; bottom:20px; width:100%; display:flex; justify-content:center; gap:10px;">
            <a href="/chat" class="btn" style="background:#fff; color:var(--p); border:1px solid var(--p);">💬 Chat</a>
            <a href="/privados" class="btn" style="background:#333;">✉️</a>
            <a href="/perfil" class="btn">👤 Mi Perfil</a>
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
                    document.getElementById("sw").innerHTML = "<div class='card' style='padding:40px;'><h3>✨ ¡Has visto a todos!</h3><button onclick='location.reload()' class='btn'>Refrescar</button></div>"; 
                    return; 
                }}
                document.getElementById("nom").innerText = ps[i].nombre;
                document.getElementById("bio").innerText = ps[i].bio;
                const cont = document.getElementById("pic_cont");
                if(ps[i].foto) {{
                    cont.innerHTML = `<img src="${{ps[i].foto}}" class="img-perfil">`;
                }} else {{
                    cont.innerHTML = `<div class="img-perfil">👤</div>`;
                }}
            }}
            async function like() {{
                const r = await fetch("/api/like/"+ps[i].nombre);
                const d = await r.json();
                if (d.m) alert("💘 ¡Es un Match!");
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
    p = profiles.get(user, {"bio": "", "points": 0, "foto": ""})
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="nav"><a href="/" style="text-decoration:none;">⬅️</a> <b>Mi Perfil</b> <span></span></div>
        <div class="card" style="padding:20px;">
            <form action="/update-perfil" method="post">
                <p>URL de tu Foto (Facebook/Instagram/Imgur):</p>
                <input name="foto" value="{p.get('foto','')}" placeholder="https://..." style="width:100%; padding:10px; border-radius:10px; border:1px solid #ddd;">
                <p>Tu Bio / Ubicación:</p>
                <textarea name="bio" style="width:100%; height:60px; border-radius:10px; border:1px solid #ddd;">{p.get('bio','')}</textarea>
                <br><br>
                <button class="btn" style="width:100%;">Guardar Cambios</button>
            </form>
            <hr>
            <p>Puntos de Nivel: <b>{p.get('points',0)}</b></p>
            <a href="/login" style="color:red; font-size:12px;">Cerrar Sesión</a>
        </div>
    </body></html>
    """)

@app.post("/update-perfil")
async def update_perfil(request: Request, bio: str = Form(...), foto: str = Form(...)):
    user = request.session.get("user")
    if user in profiles:
        profiles[user]["bio"] = bio[:100]
        profiles[user]["foto"] = foto.strip()
    return RedirectResponse("/perfil", status_code=303)

@app.get("/login")
def login_page():
    return HTMLResponse(f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">{ESTILOS}</head>
    <body>
        <div class="card" style="margin-top:100px; padding:30px;">
            <h2>💖 LoveConnect</h2>
            <form action="/login" method="post">
                <input name="u" placeholder="Tu nombre" required style="width:100%; padding:12px; border-radius:15px; border:1px solid #ddd;">
                <br><br>
                <button class="btn" style="width:100%;">Entrar</button>
            </form>
        </div>
    </body></html>
    """)

@app.post("/login")
async def do_login(request: Request, u: str = Form(...)):
    user = u.strip()[:15]
    request.session["user"] = user
    if user not in profiles:
        profiles[user] = {"likes": set(), "points": 0, "bio": "El Salvador", "foto": ""}
    return RedirectResponse("/", status_code=303)

# --- APIs DE SOPORTE ---
@app.get("/api/ps")
def get_peers(request: Request):
    user = request.session.get("user")
    return [{"nombre": n, "bio": p["bio"], "foto": p["foto"]} for n, p in profiles.items() if n != user]

@app.get("/api/like/{target}")
def add_like(request: Request, target: str):
    user = request.session.get("user")
    if user not in profiles or target not in profiles: return {"m": False}
    profiles[user]["likes"].add(target)
    match = user in profiles[target]["likes"]
    if match: profiles[user]["points"] += 10
    return {"m": match}

@app.get("/api/st")
def get_stats():
    active = len([t for t in online.values() if time.time() - t < 60])
    return {"o": active}

@app.get("/chat")
async def chat_view(request: Request):
    u = request.session.get("user")
    if not u: return RedirectResponse("/login")
    msgs = "".join([f'<div class="bubble {"mine" if m["u"]==u else "others"}"><b>{m["u"]}</b><br>{m["t"]}</div>' for m in chat_log])
    return HTMLResponse(f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1.0'>{ESTILOS}</head><body><div class='nav'><a href='/'>⬅️</a><b>Chat Grupal</b><span></span></div><div class='chat-box'>{msgs}</div><form action='/send' method='post' style='padding:15px; display:flex;'><input name='m' style='flex:1; padding:10px; border-radius:20px; border:1px solid #ddd;'><button class='btn' style='margin-left:5px;'>➤</button></form></body></html>")

@app.post("/send")
async def send_msg(request: Request, m: str = Form(...)):
    u = request.session.get("user")
    if u and m: chat_log.append({"u": u, "t": m[:100]})
    return RedirectResponse("/chat", status_code=303)

@app.get("/privados")
async def priv_list(request: Request):
    user = request.session.get("user")
    # Para Silver Breaker: ver a todos. Para otros: solo sus matches.
    if user == "Silver Breaker":
        chats = [n for n in profiles.keys() if n != user]
    else:
        chats = [n for n in profiles[user]["likes"] if user in profiles.get(n,{}).get("likes",set())]
    
    lista = "".join([f'<a href="/chat_p/{c}" class="card" style="display:block; padding:15px; text-decoration:none; color:black;">Chat con {c}</a>' for c in chats])
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><a href='/'>⬅️</a><b>Privados</b><span></span></div>{lista if lista else '<p>No hay chats aún</p>'}</body></html>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
