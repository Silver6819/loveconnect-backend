import os, uvicorn, time, random
from datetime import datetime
from fastapi import FastAPI, Form, Request, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-breaker-ultra-v2")

# --- BASES DE DATOS ---
chat_log = []
profiles = {} # {user: {"likes": set(), "points": 0, "bio": "", "avatar": ""}}
online_users = set()
stats = {"msgs": 0, "matches": 0}

# --- ESTILOS "PREMIUM" ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background:#fff0f6; margin:0; text-align:center; color: #444; }
    .nav { background:white; padding:15px; border-bottom:1px solid #eee; display:flex; justify-content:space-between; position:sticky; top:0; z-index:100; }
    .card-swipe { width:320px; margin:40px auto; background:white; border-radius:30px; box-shadow:0 15px 35px rgba(0,0,0,0.1); overflow:hidden; transition: 0.3s; }
    .avatar-big { width:100%; height:320px; background:#ff4fa3; display:flex; align-items:center; justify-content:center; font-size:100px; color:white; }
    .info-box { padding:20px; text-align:left; }
    .btn-circle { width:60px; height:60px; border-radius:50%; border:none; cursor:pointer; font-size:24px; box-shadow:0 5px 15px rgba(0,0,0,0.1); transition:0.2s; }
    .btn-circle:active { transform: scale(0.9); }
    .btn-no { background:white; color:#ff4444; }
    .btn-yes { background:#ff4fa3; color:white; }
    #online-tag { color: #2ecc71; font-weight: bold; font-size:14px; }
    .btn-main { background:#ff4fa3; color:white; border:none; padding:12px 25px; border-radius:25px; text-decoration:none; font-weight:bold; }
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
        
        <div style="padding:20px;">
            <h2 style="color:#ff4fa3;">¿A quién conocerás hoy?</h2>
            <div id="swipe-area">
                <div class="card-swipe" id="perfil-card">
                    <div class="avatar-big" id="avatar-view">👤</div>
                    <div class="info-box">
                        <h2 id="nombre-view">Buscando...</h2>
                        <p id="bio-view">Cargando perfiles disponibles...</p>
                    </div>
                    <div style="display:flex; justify-content:space-evenly; padding-bottom:25px;">
                        <button class="btn-circle btn-no" onclick="siguiente()">❌</button>
                        <button class="btn-circle btn-yes" onclick="darLike()">❤️</button>
                    </div>
                </div>
            </div>
        </div>

        <div style="position:fixed; bottom:20px; width:100%; display:flex; justify-content:center; gap:10px;">
            <a href="/chat" class="btn-main" style="background:white; color:#ff4fa3; border:1px solid #ff4fa3;">💬 Chat</a>
            <a href="/perfil" class="btn-main">👤 Mi Perfil</a>
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
                    document.getElementById("swipe-area").innerHTML = "<div class='card-swipe' style='padding:40px;'><h3>🎉 ¡Has visto a todos por hoy!</h3><p>Vuelve más tarde o invita amigos.</p></div>";
                    return;
                }}
                let p = perfiles[index];
                document.getElementById("avatar-view").innerText = p.nombre[0].toUpperCase();
                document.getElementById("nombre-view").innerText = p.nombre;
                document.getElementById("bio-view").innerText = p.bio || "¡Hola! Estoy usando LoveConnect.";
            }}

            async function darLike() {{
                let target = perfiles[index].nombre;
                const res = await fetch("/api/like", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: JSON.stringify({{target: target}})
                }});
                const data = await res.json();
                if (data.match) alert("💘 ¡ES UN MATCH CON " + target + "!");
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

# --- API ENDPOINTS (PUNTO 1 Y 2) ---

@app.get("/api/perfiles")
def get_perfiles(request: Request):
    user = request.session.get("user")
    # Filtramos: que no sea yo mismo y a los que NO les he dado like
    disponibles = [
        {{"nombre": u, "bio": p.get("bio", "")}} 
        for u, p in profiles.items() 
        if u != user and u not in profiles[user]["likes"]
    ]
    return disponibles

@app.post("/api/like")
async def api_like(request: Request, data: dict = Body(...)):
    user = request.session.get("user")
    target = data.get("target")
    is_match = False
    
    if user and target in profiles:
        profiles[user]["likes"].add(target)
        # Verificar Match Real
        if user in profiles[target]["likes"]:
            stats["matches"] += 1
            is_match = True
            
    return {"status": "ok", "match": is_match}

@app.get("/api/stats")
def get_stats():
    return {"online": len(online_users), "matches": stats["matches"]}

# --- RUTAS DE APOYO ---

@app.get("/chat")
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse("/login-page")
    # (Aquí iría tu código de chat de ayer)
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='nav'><b>Chat Grupal</b><a href='/'>🏠 Inicio</a></div><p>Área de chat en construcción con el nuevo diseño...</p></body></html>")

@app.get("/login-page")
async def login_p():
    return HTMLResponse(f"<html>{ESTILOS}<body><div class='card-swipe' style='margin-top:100px; padding:30px;'><h2>💖 LoveConnect</h2><form action='/login' method='post'><input name='username' placeholder='Tu nombre' required style='padding:12px; width:80%; border-radius:15px; border:1px solid #eee;'><br><br><button class='btn-main'>Entrar</button></form></div></body></html>")

@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles:
        profiles[username] = {"likes": set(), "points": 0, "bio": "Explorando LoveConnect 🚀"}
    return RedirectResponse("/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
