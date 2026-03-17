import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_cosmic_final_2026")

# --- BASES DE DATOS ---
usuarios_registrados = {"Silver Breaker": "1234"} 
chat_global = []
chats_privados = []
usuarios_activos = set()
castigados = set() 
CLAVE_ADMIN = "SB2026"

# --- EL CSS MAGISTRAL DE CHATGPT + AJUSTES ---
CSS_CHATGPT = """
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
body { 
    margin: 0; padding: 20px; font-family: 'Segoe UI', sans-serif; 
    background: var(--bg-dark); color: #fff; min-height: 100vh;
}
.container {
  background: var(--glass-bg); backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border); border-radius: 25px;
  padding: 25px; max-width: 450px; margin: auto;
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.1);
}
.message {
  padding: 12px 18px; margin: 10px 0; border-radius: 20px;
  background: linear-gradient(135deg, var(--cosmic-purple), var(--neon-pink));
  box-shadow: 0 0 10px rgba(255, 46, 136, 0.4); font-size: 14px; text-align: left;
}
.message.self { background: linear-gradient(135deg, var(--electric-blue), var(--cosmic-purple)); }

/* MODO CASTIGO SCP */
.punishment-mode .container { border: 2px solid var(--danger-red); box-shadow: 0 0 30px var(--danger-red); }
.punishment-mode .message {
  background: #0b0b0b; border: 1px solid var(--danger-red);
  color: #ffb3b3; font-family: monospace; box-shadow: none;
}

input {
  width: 100%; padding: 12px; border-radius: 20px; border: 1px solid transparent;
  background: rgba(255,255,255,0.08); color: #fff; outline: none; transition: 0.3s; box-sizing: border-box;
}
input:focus {
  border: 1px solid var(--neon-pink);
  box-shadow: 0 0 10px var(--neon-pink), 0 0 20px var(--electric-blue);
}
.btn-main {
  padding: 12px; border: none; border-radius: 30px; width: 100%;
  background: linear-gradient(135deg, var(--neon-pink), var(--cosmic-purple));
  color: white; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px;
}
.btn-admin {
  background: #111; border: 1px solid var(--electric-blue); color: var(--electric-blue);
  padding: 8px; border-radius: 10px; font-family: monospace; font-size: 10px; cursor: pointer; text-decoration: none;
}
.threat-level { font-size: 10px; color: var(--electric-blue); text-transform: uppercase; letter-spacing: 1px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS_CHATGPT}</head><body><div class='container'><h1>❤️ LoveConnect</h1><form action='/login' method='post'><input name='u' placeholder='Usuario Interestelar' required><br><br><input name='p' type='password' placeholder='Código de Acceso' required><br><button class='btn-main'>INICIAR PROTOCOLO</button></form></div></body></html>"

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    user = u.strip()
    if user not in usuarios_registrados: usuarios_registrados[user] = p
    if usuarios_registrados[user] == p:
        request.session["user"] = user
        usuarios_activos.add(user)
        return RedirectResponse(url="/chat", status_code=303)
    return "ACCESO DENEGADO."

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
        
        is_me = "self" if m['u'] == user else ""
        btn_ban = f"<a href='/castigar?u={m['u']}' class='btn-admin'>[CONTAIN]</a>" if user == "Silver Breaker" and m['u'] != "Silver Breaker" else ""
        btn_priv = f"<a href='/ventana_privada?con={m['u']}' style='text-decoration:none;'> ✉️</a>" if m['u'] != user else ""
        
        msgs_html += f"<div class='message {is_me}'><b>{m['u']}:</b> {m['t']} {btn_priv} {btn_ban}</div>"

    # Mostrar chats privados activos
    priv_list = ""
    mis_p = [m for m in chats_privados if m['para'] == user or m['de'] == user]
    if mis_p:
        vistos = set()
        for p in mis_p:
            otro = p['de'] if p['para'] == user else p['para']
            if otro not in vistos:
                priv_list += f"<a href='/ventana_privada?con={otro}' class='btn-admin' style='margin-right:5px;'>MSG: {otro}</a>"
                vistos.add(otro)

    return f"""
    <html class='{clase_body}'><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS_CHATGPT}</head>
    <body class='{clase_body}'><div class='container'>
        <div class='threat-level'>NIVEL DE AMENAZA: { "MÁXIMA (EUCLID)" if es_castigado else "BAJA (SAFE)" }</div>
        <h3>CANAL GLOBAL (● {len(usuarios_activos)})</h3>
        <div style='height:300px; overflow-y:auto;'>{msgs_html}</div>
        <form action="/postear" method="post">
            <input name="m" placeholder="Transmitir mensaje..." required autocomplete="off">
            <button class="btn-main">ENVIAR</button>
        </form>
        <div style='margin-top:10px;'>{priv_list}</div>
        {f"<a href='/limpiar?clave={CLAVE_ADMIN}' class='btn-admin' style='display:block; margin-top:10px; text-align:center;'>LIMPIEZA DE DATOS</a>" if user == "Silver Breaker" else ""}
        <br><a href="/logout" style='color:var(--neon-pink); font-size:10px;'>CERRAR SESIÓN</a>
    </div></body></html>
    """

@app.get("/ventana_privada", response_class=HTMLResponse)
async def ventana_privada(request: Request, con: str):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    mensajes_chat = [m for m in chats_privados if (m['de'] == user and m['para'] == con) or (m['de'] == con and m['para'] == user)]
    html_msgs = "".join([f"<div class='message {'self' if m['de']==user else ''}'><b>{m['de']}:</b> {m['t']}</div>" for m in mensajes_chat])
    
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS_CHATGPT}</head><body>
    <div class='container'>
        <h3>ARCHIVO PRIVADO: {con}</h3>
        <div style='height:300px; overflow-y:auto;'>{html_msgs}</div>
        <form action="/enviar_privado" method="post">
            <input type="hidden" name="para" value="{con}">
            <input name="m" placeholder="Mensaje encriptado..." required>
            <button class="btn-main">ENVIAR PRIVADO</button>
        </form>
        <br><a href="/chat" class='btn-admin'>VOLVER AL CANAL GLOBAL</a>
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
