import os, uvicorn, time
from fastapi import FastAPI, Form, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-breaker-2026")

# --- DB MINIMALISTA ---
chat_log = [] # Grupal
priv_chats = {} # {(u1, u2): [mensajes]}
profiles = {} # {user: {"likes": set(), "points": 0, "bio": ""}}
online = {} # {user: timestamp}

ESTILOS = """
<style>
    body { font-family: sans-serif; background:#fff0f6; margin:0; text-align:center; color:#444; }
    .nav { background:#fff; padding:10px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; position:sticky; top:0; }
    .card { width:90%; max-width:320px; margin:20px auto; background:#fff; border-radius:20px; box-shadow:0 4px 15px rgba(0,0,0,0.05); overflow:hidden; }
    .btn { background:#ff4fa3; color:#fff; border:none; padding:10px 20px; border-radius:20px; cursor:pointer; text-decoration:none; font-weight:bold; }
    .chat-box { height:65vh; overflow-y:auto; padding:10px; display:flex; flex-direction:column; background:#fefefe; }
    .bubble { margin:5px; padding:8px 12px; border-radius:15px; max-width:75%; font-size:14px; }
    .mine { background:#ff4fa3; color:#fff; align-self:flex-end; }
    .others { background:#eee; align-self:flex-start; }
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
        <div id="sw">
            <div class="card">
                <div style="height:200px; background:#ff4fa3; color:#fff; font-size:80px; display:flex; align-items:center; justify-content:center;" id="av">👤</div>
                <div style="padding:15px; text-align:left;">
                    <h3 id="nom" style="margin:0;">Buscando...</h3>
                    <p id="bio" style="font-size:13px; color:#777;"></p>
                </div>
                <div style="padding-bottom:15px;">
                    <button class="btn" style="background:#ccc;" onclick="sig()">❌</button>
                    <button class="btn" onclick="like()">❤️</button>
                </div>
            </div>
        </div>
        <div style="position:fixed; bottom:15px; width:100%; display:flex; justify-content:center; gap:10px;">
            <a href="/chat" class="btn" style="background:#fff; color:#ff4fa3; border:1px solid #ff4fa3;">💬 Chat</a>
            <a href="/privados" class="btn" style="background:#444;">✉️ Privados</a>
        </div>
        <script>
            let ps = [], i = 0;
            async function load() {{
                const r = await fetch("/api/ps");
                ps = await r.json();
                show();
            }}
            function show() {{
                if (i >= ps.length) {{ document.getElementById("sw").innerHTML = "<p>¡No hay más perfiles!</p>"; return; }}
                document.getElementById("av").innerText = ps[i].nombre[0].toUpperCase();
                document.getElementById("nom").innerText = ps[i].nombre;
                document.getElementById("bio").innerText = ps[i].bio;
            }}
            async function like() {{
                const r = await fetch("/api/like/"+ps[i].nombre);
                const d = await r.json();
                if (d.m) alert("💘 MATCH CON " + ps[i].nombre);
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

# --- CHATS PRIVADOS (Tu petición especial) ---
@app.get("/privados")
async def list_priv(request: Request):
    user = request.session.get("user")
    # Si eres Silver Breaker, puedes ver a todos. Si no, solo tus matches.
    if user == "Silver Breaker":
        contacts = [u for u in profiles.keys() if u != user]
    else:
        contacts = [u for u in profiles[user]["likes"] if user in profiles[u]["likes"]]
    
    links = "".join([f'<a href="/chat/{u}" class="card" style="display:block; padding:15px; text-decoration:none; color:#444;">👤 {u}</a>' for u in contacts])
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><a href='/'>⬅️</a><b>Privados</b><span></span></div>{links if links else '<p>No hay chats aún</p>'}</body></html>")

@app.get("/chat/{target}")
async def private_chat(request: Request, target: str):
    user = request.session.get("user")
    pair = tuple(sorted((user, target)))
    msgs = priv_chats.get(pair, [])
    html_msgs = "".join([f'<div class="bubble {"mine" if m["u"]==user else "others"}">{m["t"]}</div>' for m in msgs])
    return HTMLResponse(f"""
    <html>{ESTILOS}<body>
        <div class="nav"><a href="/privados">⬅️</a><b>{target}</b><span></span></div>
        <div class="chat-box">{html_msgs}<div id="e"></div></div>
        <form action="/send-p/{target}" method="post" style="display:flex; padding:10px;">
            <input name="msg" style="flex:1; padding:10px; border-radius:20px; border:1px solid #ddd;">
            <button class="btn" style="margin-left:5px;">➤</button>
        </form>
        <script>document.getElementById("e").scrollIntoView();</script>
    </body></html>
    """)

@app.post("/send-p/{target}")
async def send_p(request: Request, target: str, msg: str = Form(...)):
    user = request.session.get("user")
    pair = tuple(sorted((user, target)))
    if pair not in priv_chats: priv_chats[pair] = []
    priv_chats[pair].append({"u": user, "t": msg})
    return RedirectResponse(f"/chat/{target}", status_code=303)

# --- API Y RUTAS ---
@app.get("/api/ps")
def api_ps(request: Request):
    u = request.session.get("user")
    return [{"nombre": n, "bio": p["bio"]} for n, p in profiles.items() if n != u and n not in profiles[u]["likes"]]

@app.get("/api/like/{t}")
def api_like(request: Request, t: str):
    u = request.session.get("user")
    profiles[u]["likes"].add(t)
    match = u in profiles[t]["likes"]
    return {"m": match}

@app.get("/api/st")
def api_st():
    act = len([t for t in online.values() if time.time() - t < 60])
    return {"o": act}

@app.get("/chat")
async def chat_g(request: Request):
    u = request.session.get("user")
    msgs = "".join([f'<div class="bubble {"mine" if m["u"]==u else "others"}"><small>{m["u"]}</small><br>{m["t"]}</div>' for m in chat_log])
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><a href='/'>⬅️</a><b>Grupal</b><span></span></div><div class='chat-box'>{msgs}<div id='e'></div></div><form action='/sg' method='post' style='display:flex; padding:10px;'><input name='m' style='flex:1; padding:10px;'><button class='btn'>➤</button></form><script>document.getElementById('e').scrollIntoView();</script></body></html>")

@app.post("/sg")
async def sg(request: Request, m: str = Form(...)):
    u = request.session.get("user")
    chat_log.append({"u": u, "t": m})
    if len(chat_log) > 20: chat_log.pop(0)
    return RedirectResponse("/chat", status_code=303)

@app.get("/login")
def log_p(): return HTMLResponse(f"<html>{ESTILOS}<body><div class='card' style='padding:20px;'><h2>💖 LoveConnect</h2><form action='/login' method='post'><input name='u' placeholder='Nombre' required style='padding:10px; width:80%;'><br><br><button class='btn'>Entrar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, u: str = Form(...)):
    request.session["user"] = u
    if u not in profiles: profiles[u] = {"likes": set(), "points": 0, "bio": "¡Hola!"}
    return RedirectResponse("/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
