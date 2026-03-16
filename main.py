import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_master_key_2026")

chat_global = []

# --- CONFIGURACIÓN ---
CLAVE_ADMIN = "SB2026" # Esta es la clave por si necesitas usar la URL directa

CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f8; text-align: center; padding: 20px; margin: 0; }
    .box { background: white; padding: 30px; border-radius: 25px; max-width: 400px; margin: 20px auto; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
    .btn { background: #ff4fa3; color: white; border: none; padding: 12px; border-radius: 50px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px; margin-top: 15px; text-decoration: none; display: block; }
    .btn-admin { background: #6c5ce7; margin-top: 10px; font-size: 13px; } /* Color morado para el admin */
    input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #eee; border-radius: 15px; box-sizing: border-box; }
    .msg-list { height: 300px; overflow-y: auto; background: #fafafa; padding: 10px; margin-bottom: 15px; border-radius: 15px; }
    .msg-item { background: #ffeef4; padding: 10px; border-radius: 15px; margin: 8px 0; text-align: left; font-size: 14px; position: relative; }
    .admin-tag { background: #ff4fa3; color: white; padding: 2px 6px; border-radius: 8px; font-size: 9px; margin-left: 5px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.session.get("user"): return RedirectResponse(url="/chat")
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS}</head><body><div class='box'><h1>❤️ LoveConnect</h1><form action='/login' method='post'><input name='u' placeholder='Tu nombre' required><button class='btn'>Entrar</button></form></div></body></html>"

@app.post("/login")
async def login(request: Request, u: str = Form(...)):
    request.session["user"] = u.strip()
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    
    mensajes_html = ""
    for m in chat_global:
        tag = "<span class='admin-tag'>ADMIN</span>" if m['u'] == "Silver Breaker" else ""
        mensajes_html += f"<div class='msg-item'><b>{m['u']}{tag}:</b> {m['t']}</div>"
    
    # --- LÓGICA DEL BOTÓN MÁGICO ---
    boton_admin = ""
    if user == "Silver Breaker":
        # Este botón solo se construye si el usuario es Silver Breaker
        boton_admin = f"<a href='/limpiar?clave={CLAVE_ADMIN}' class='btn btn-admin'>🗑️ Borrar historial (Solo yo veo esto)</a>"
    
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{CSS}</head>
    <body><div class='box'>
        <h3>Chat Grupal</h3>
        <div class="msg-list">{mensajes_html}</div>
        <form action="/postear" method="post">
            <input name="m" placeholder="Escribe un mensaje..." required autocomplete="off">
            <button class="btn">Enviar</button>
        </form>
        {boton_admin}
        <br><a href="/logout" style="color:#aaa; font-size:12px; text-decoration:none;">Cerrar Sesión</a>
    </div></body></html>
    """

@app.post("/postear")
async def postear(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user:
        clean_text = m.replace("<", "&lt;").replace(">", "&gt;")[:120]
        chat_global.append({"u": user, "t": clean_text})
        if len(chat_global) > 25: chat_global.pop(0)
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/limpiar")
async def limpiar_chat(clave: str):
    if clave == CLAVE_ADMIN:
        chat_global.clear()
        return RedirectResponse(url="/chat") # Te regresa al chat después de borrar
    return "Error de acceso."

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
