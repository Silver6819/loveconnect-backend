import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_god_mode_2026")

usuarios_registrados = {"Silver Breaker": "1234"} 
chat_global = []
chats_privados = []
usuarios_activos = set()
castigados = set() 
CLAVE_ADMIN = "SB2026"

# --- CSS & JS ENGINE ---
HEADER_COMUN = """
<meta name='viewport' content='width=device-width, initial-scale=1'>
<style>
:root {
  --bg-dark: #050510;
  --neon-pink: #ff2e88;
  --electric-blue: #00e5ff;
  --cosmic-purple: #9b5cff;
  --danger-red: #ff3b3b;
}

body { 
    margin: 0; padding: 20px; font-family: 'Segoe UI', sans-serif; 
    background: var(--bg-dark); color: #fff; min-height: 100vh;
    overflow-x: hidden;
}

#starfield {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: -1; opacity: 0.6;
}

.container {
  background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 25px;
  padding: 25px; max-width: 450px; margin: auto; position: relative;
}

.btn-main {
  padding: 15px; border: none; border-radius: 30px; width: 100%;
  background: linear-gradient(135deg, var(--neon-pink), var(--cosmic-purple));
  color: white; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px;
  box-shadow: 0 0 15px var(--neon-pink);
}

.message { padding: 12px; margin: 8px 0; border-radius: 15px; animation: fadeIn 0.4s; }
.self { background: linear-gradient(90deg, var(--electric-blue), var(--cosmic-purple)); margin-left: 20%; }
.other { background: rgba(255,255,255,0.1); margin-right: 20%; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; } }

.admin-badge { background: var(--neon-pink); color: white; padding: 2px 6px; border-radius: 5px; font-size: 10px; }
</style>
"""

JS_STARS = """
<canvas id="starfield"></canvas>
<script>
const canvas = document.getElementById('starfield');
const ctx = canvas.getContext('2d');
let stars = [];

function init() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    stars = [];
    for(let i=0; i<100; i++) {
        stars.append({x: Math.random()*canvas.width, y: Math.random()*canvas.height, s: Math.random()*2});
    }
}

function draw() {
    ctx.clearRect(0,0,canvas.width, canvas.height);
    ctx.fillStyle = "white";
    stars.forEach(star => {
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.s, 0, Math.PI*2);
        ctx.fill();
        star.y += 0.2;
        if(star.y > canvas.height) star.y = 0;
    });
    requestAnimationFrame(draw);
}
window.addEventListener('resize', init);
init(); draw();
</script>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return f"<html><head>{HEADER_COMUN}</head><body>{JS_STARS}<div class='container'><h1>❤️ LoveConnect</h1><p>INICIAR PROTOCOLO CÓSMICO</p><form action='/login' method='post'><input name='u' placeholder='Usuario Interestelar' style='width:100%; padding:10px; border-radius:10px; margin-bottom:10px;'><br><input name='p' type='password' placeholder='Código de Acceso' style='width:100%; padding:10px; border-radius:10px;'><br><button class='btn-main'>ENTRAR</button></form></div></body></html>"

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    user = u.strip()
    if user not in usuarios_registrados: usuarios_registrados[user] = p
    if usuarios_registrados[user] == p:
        request.session["user"] = user
        return RedirectResponse(url="/chat", status_code=303)
    return "Error de acceso."

@app.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    msgs = "".join([f"<div class='message {'self' if m['u']==user else 'other'}'><b>{m['u']}:</b> {m['t']} <a href='/ventana_privada?con={m['u']}' style='text-decoration:none;'>✉️</a></div>" for m in chat_global])
    
    admin_panel = ""
    if user == "Silver Breaker":
        admin_panel = f"<div style='border-top:1px solid #444; margin-top:20px; padding-top:10px;'><p style='color:var(--electric-blue); font-size:12px;'>GOD MODE ACTIVADO</p><a href='/admin_db' class='btn-main' style='display:block; text-align:center; text-decoration:none; background:var(--bg-dark); border:1px solid var(--electric-blue);'>VER REGISTRO DE ALMAS</a></div>"

    return f"<html><head>{HEADER_COMUN}</head><body>{JS_STARS}<div class='container'><h3>CANAL GLOBAL</h3><div style='height:300px; overflow-y:auto;'>{msgs}</div><form action='/postear' method='post'><input name='m' placeholder='Transmitir...' style='width:100%; padding:10px;'><button class='btn-main'>ENVIAR</button></form>{admin_panel}<br><a href='/logout' style='color:red;'>Cerrar Sesión</a></div></body></html>"

@app.get("/admin_db", response_class=HTMLResponse)
async def admin_db(request: Request):
    if request.session.get("user") != "Silver Breaker": return "ACCESO PROHIBIDO"
    items = "".join([f"<li><b>{u}</b>: {p}</li>" for u, p in usuarios_registrados.items()])
    return f"<html><head>{HEADER_COMUN}</head><body><div class='container'><h2>BASE DE DATOS</h2><ul>{items}</ul><br><a href='/chat' class='btn-main'>VOLVER</a></div></body></html>"

@app.post("/postear")
async def postear(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user: chat_global.append({"u": user, "t": m})
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
