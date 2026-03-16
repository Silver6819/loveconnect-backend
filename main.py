import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_prison_2026")

# --- BASES DE DATOS ---
usuarios_registrados = {"Silver Breaker": "1234"} 
chat_global = []
usuarios_activos = set()
castigados = set() # Usuarios en el "calabozo"
sugerencias = []

CLAVE_ADMIN = "SB2026"

def get_css(modo_oscuro=False):
    bg = "#1a1a1a" if modo_oscuro else "#fff5f8"
    box_bg = "#2d2d2d" if modo_oscuro else "white"
    text = "#eee" if modo_oscuro else "#333"
    return f"""
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: {bg}; text-align: center; padding: 20px; color: {text}; transition: 0.5s; }}
        .box {{ background: {box_bg}; padding: 30px; border-radius: 30px; max-width: 400px; margin: 20px auto; shadow: 0 10px 25px rgba(0,0,0,0.2); border: {"2px solid #444" if modo_oscuro else "none"}; }}
        .btn {{ background: #ff4fa3; color: white; border: none; padding: 12px; border-radius: 50px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 10px; display: block; text-decoration: none; }}
        .btn-castigo {{ background: #444; font-size: 10px; padding: 5px; width: auto; display: inline-block; margin-left: 5px; }}
        .msg-list {{ height: 250px; overflow-y: auto; background: {"#222" if modo_oscuro else "#fafafa"}; padding: 15px; border-radius: 20px; margin-bottom: 15px; border: {"1px solid #ff0000" if modo_oscuro else "none"}; }}
        .msg-item {{ background: {"#3d3d3d" if modo_oscuro else "#ffeef4"}; padding: 10px; border-radius: 15px; margin: 8px 0; text-align: left; font-size: 13px; color: {text}; }}
        .admin-tag {{ background: #ff4fa3; color: white; padding: 2px 6px; border-radius: 5px; font-size: 9px; }}
        .online {{ color: #27ae60; font-size: 12px; font-weight: bold; }}
        .status-bar {{ background: #333; color: #ff0000; font-size: 10px; padding: 5px; border-radius: 10px; margin-bottom: 10px; {"display: block;" if modo_oscuro else "display: none;"} }}
    </style>
    """

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.session.get("user"): return RedirectResponse(url="/chat")
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{get_css()}</head><body><div class='box'><h1>❤️ LoveConnect</h1><form action='/login' method='post'><input name='u' placeholder='Usuario' style='width:100%; padding:10px; margin:5px 0;' required><br><input name='p' type='password' placeholder='Clave' style='width:100%; padding:10px; margin:5px 0;' required><button class='btn'>Entrar / Registrar</button></form></div></body></html>"

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    user = u.strip()
    if user not in usuarios_registrados: usuarios_registrados[user] = p
    if usuarios_registrados[user] == p:
        request.session["user"] = user
        usuarios_activos.add(user)
        return RedirectResponse(url="/chat", status_code=303)
    return "Error de clave."

@app.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    es_castigado = user in castigados
    mensajes_html = ""
    
    # Filtrar mensajes: Los castigados solo ven lo suyo. Los demás NO ven lo del castigado.
    for m in chat_global:
        if es_castigado and m['u'] != user: continue # Si estoy castigado, solo veo mis ecos
        if not es_castigado and m['u'] in castigados: continue # Si soy normal, no veo a los castigados
        
        tag = "<span class='admin-tag'>ADMIN</span>" if m['u'] == "Silver Breaker" else ""
        btn_ban = f"<a href='/castigar?u={m['u']}' class='btn btn-castigo'>🚫</a>" if user == "Silver Breaker" and m['u'] != "Silver Breaker" else ""
        mensajes_html += f"<div class='msg-item'><b>{m['u']}{tag}:</b> {m['t']} {btn_ban}</div>"

    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{get_css(es_castigado)}</head>
    <body><div class='box'>
        <div class='status-bar'>⚠️ CELDA DE CONTENCIÓN ACTIVA ⚠️</div>
        <div class='online'>● {len(usuarios_activos)} en línea</div>
        <h3>{"Zona de Castigo" if es_castigado else "Chat Grupal"}</h3>
        <div class="msg-list">{mensajes_html}</div>
        <form action="/postear" method="post">
            <input name="m" placeholder="Escribe..." required style='width:70%; padding:10px;'>
            <button style='width:25%; padding:10px;'>Enviar</button>
        </form>
        {f"<a href='/limpiar?clave={CLAVE_ADMIN}' class='btn' style='background:#6c5ce7'>🗑️ Borrar Todo</a>" if user == "Silver Breaker" else ""}
        <hr>
        <p style='font-size:10px;'>💡 Sugerencias del mes:</p>
        <form action="/sugerir" method="post">
            <input name="s" placeholder="¿Qué mejorar?" style='width:70%; font-size:10px;'>
            <button style='font-size:10px;'>Enviar</button>
        </form>
        <br><a href="/logout" style='color:#aaa; font-size:10px;'>Cerrar Sesión</a>
    </div></body></html>
    """

@app.post("/postear")
async def postear(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user:
        clean_text = m.replace("<", "&lt;")[:100]
        chat_global.append({"u": user, "t": clean_text})
        if len(chat_global) > 30: chat_global.pop(0)
    return RedirectResponse(url="/chat", status_code=303)

@app.post("/sugerir")
async def sugerir(s: str = Form(...)):
    sugerencias.append(s[:100])
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
