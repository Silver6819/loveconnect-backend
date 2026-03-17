import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_god_mode_2026")

# --- BASES DE DATOS ---
usuarios_registrados = {"Silver Breaker": "1234"} 
chat_global = []
chats_privados = []
usuarios_activos = set()
castigados = set() 
CLAVE_ADMIN = "SB2026"

# --- CSS EVOLUCIONADO (ChatGPT + Silver Breaker Lore) ---
CSS_FINAL = """
<style>
:root {
  --bg-dark: linear-gradient(135deg, #050510, #0a0f2c, #140a1f);
  --neon-pink: #ff2e88;
  --electric-blue: #00e5ff;
  --cosmic-purple: #9b5cff;
  --danger-red: #ff3b3b;
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
}

@keyframes pulseGlow {
  0% { box-shadow: 0 0 10px var(--neon-pink); }
  50% { box-shadow: 0 0 25px var(--cosmic-purple); }
  100% { box-shadow: 0 0 10px var(--neon-pink); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

body { 
    margin: 0; padding: 20px; font-family: 'Segoe UI', sans-serif; 
    background: var(--bg-dark); color: #fff; min-height: 100vh;
    transition: 0.5s;
}

.container {
  background: var(--glass-bg); backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border); border-radius: 25px;
  padding: 25px; max-width: 450px; margin: auto;
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.1);
}

.message {
  padding: 12px 18px; margin: 10px 0; border-radius: 20px;
  font-size: 14px; text-align: left; animation: fadeInUp 0.3s ease;
}

/* TUS MENSAJES */
.message.self { 
    background: linear-gradient(135deg, var(--electric-blue), var(--cosmic-purple));
    box-shadow: 0 0 15px rgba(0, 229, 255, 0.3);
    margin-left: 20px;
}

/* MENSAJES DE OTROS (Neutral) */
.message.other {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    margin-right: 20px;
}

/* MODO CASTIGO (CELDA SCP) */
.punishment-mode { filter: grayscale(40%) contrast(120%); }
.punishment-mode .container { border: 2px solid var(--danger-red); box-shadow: 0 0 25px rgba(255,0,0,0.3); }
.punishment-mode .message { background: #0b0b0b; border: 1px solid var(--danger-red); color: #ffb3b3; font-family: monospace; }

input {
  width: 100%; padding: 12px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.08); color: #fff; outline: none; transition: 0.3s; box-sizing: border-box;
}

input:focus {
  border: 1px solid var(--neon-pink);
  box-shadow: 0 0 8px var(--neon-pink), 0 0 16px var(--electric-blue);
}

.btn-main {
  padding: 15px; border: none; border-radius: 30px; width: 100%;
  background: linear-gradient(135deg, var(--neon-pink), var(--cosmic-purple));
  color: white; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px;
  animation: pulseGlow 2.5s infinite;
}

.btn-admin {
  background: #111; border: 1px solid var(--electric-blue); color: var(--electric-blue);
  padding: 8px; border-radius: 10px; font-family: monospace; font-size: 10px; cursor: pointer; text-decoration: none; display: inline-block;
}

.threat-level { font-size: 10px; color: var(--electric-blue); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS_FINAL}</head><body><div class='container'><h1>❤️ LoveConnect</h1><p style='font-size:12px; color:#aaa;'>SISTEMA DE EMPAREJAMIENTO CUÁNTICO</p><form action='/login' method='post'><input name='u' placeholder='ID de Usuario' required><br><br><input name='p' type='password' placeholder='Contraseña' required><br><button class='btn-main'>INICIAR PROTOCOLO</button></form></div></body></html>"

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    user = u.strip()
    if user not in usuarios_registrados: usuarios_registrados[user] = p
    if usuarios_registrados[user] == p:
        request.session["user"] = user
        usuarios_activos.add(user)
        return RedirectResponse(url="/chat", status_code=303)
    return "ACCESO DENEGADO AL ARCHIVO."

@app.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    es_castigado = user in castigados
    clase_body = "punishment-mode" if es_castigado else ""
    
    msgs_html = ""
    for m in chat_global:
        if es_castigado and m['u'] != user: continue
        if not es_castigado and m['u'] in castigados: continue
        
        tipo_msg = "self" if m['u'] == user else "other"
        btn_ban = f"<a href='/castigar?u={m['u']}' class='btn-admin'>[CONTAIN]</a>" if user == "Silver Breaker" and m['u'] != "Silver Breaker" else ""
        btn_priv = f"<a href='/ventana_privada?con={m['u']}' style='text-decoration:none;'> ✉️</a>" if m['u'] != user else ""
        
        msgs_html += f"<div class='message {tipo_msg}'><b>{m['u']}:</b> {m['t']} {btn_priv} {btn_ban}</div>"

    return f"""
    <html class='{clase_body}'><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS_FINAL}</head>
    <body class='{clase_body}'><div class='container'>
        <div class='threat-level'>ESTADO: { "☢️ NIVEL EUCLID" if es_castigado else "✅ NIVEL SAFE" }</div>
        <h3>CANAL DE COMUNICACIÓN</h3>
        <div style='height:350px; overflow-y:auto; padding-right:5px;'>{msgs_html}</div>
        <form action="/postear" method="post">
            <input name="m" placeholder="Escribir mensaje..." required autocomplete="off">
            <button class="btn-main">TRANSMITIR</button>
        </form>
        <br>
        {f"<a href='/limpiar?clave={CLAVE_ADMIN}' class='btn-admin' style='width:100%; text-align:center;'>LIMPIAR BASE DE DATOS</a>" if user == "Silver Breaker" else ""}
        <br><br><a href="/logout" style='color:var(--neon-pink); font-size:10px; text-decoration:none;'>TERMINAR SESIÓN</a>
    </div></body></html>
    """

@app.get("/ventana_privada", response_class=HTMLResponse)
async def ventana_privada(request: Request, con: str):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    mensajes_chat = [m for m in chats_privados if (m['de'] == user and m['para'] == con) or (m['de'] == con and m['para'] == user)]
    html_msgs = "".join([f"<div class='message {'self' if m['de']==user else 'other'}'><b>{m['de']}:</b> {m['t']}</div>" for m in mensajes_chat])
    
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS_FINAL}</head><body>
    <div class='container'>
        <div class='threat-level'>ARCHIVO PRIVADO: {con}</div>
        <div style='height:350px; overflow-y:auto;'>{html_msgs}</div>
        <form action="/enviar_privado" method="post">
            <input type="hidden" name="para" value="{con}">
            <input name="m" placeholder="Mensaje cifrado..." required>
            <button class="btn-main">ENVIAR</button>
        </form>
        <br><a href="/chat" class='btn-admin'>VOLVER</a>
    </div></body></html>
    """

@app.post("/enviar_privado")
async def enviar_privado(request: Request, para: str = Form(...), m: str = Form(...)):
    user = request.session.get("user")
    if user: chats_privados.append({"de": user, "para": para, "t": m[:100]})
    return RedirectResponse(url=f"/ventana_privada?con={para}", status_code=303)

@app.post("/postear")
async def postear(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user: chat_global.append({"u": user, "t": m.replace("<","&lt;")[:100]})
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/castigar")
async def castigar_user(request: Request, u: str):
    if request.session.get("user") == "Silver Breaker":
        if u in castigados: castigados.remove(u)
        else: castigados.add(u)
    return RedirectResponse(url="/chat")

@app.get("/limpiar")
async def limpiar(clave: str):
    if clave == CLAVE_ADMIN: chat_global.clear()
    return RedirectResponse(url="/chat")

@app.get("/logout")
async def logout(request: Request):
    u = request.session.get("user")
    if u in usuarios_activos: usuarios_activos.remove(u)
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
