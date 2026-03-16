import os, uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
# Clave nueva para limpiar cualquier error de sesión previo
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_fix_2026")

# --- MEMORIA ---
chat_global = []

CSS = """
<style>
    body { font-family: sans-serif; background: #fff0f5; text-align: center; padding: 20px; }
    .box { background: white; padding: 25px; border-radius: 20px; max-width: 400px; margin: auto; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
    .btn { background: #ff4fa3; color: white; border: none; padding: 12px; border-radius: 20px; cursor: pointer; width: 80%; font-weight: bold; margin-top: 10px; }
    input { width: 80%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; }
    .msg { background: #f9f9f9; padding: 8px; border-radius: 10px; margin: 5px 0; text-align: left; border-left: 4px solid #ff4fa3; font-size: 14px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.session.get("user"): return RedirectResponse(url="/chat")
    return f"<html><body>{CSS}<div class='box'><h1>💖 LoveConnect</h1><form action='/login' method='post'><input name='u' placeholder='Tu nombre' required><br><button class='btn'>Entrar</button></form></div></body></html>"

@app.post("/login")
async def login(request: Request, u: str = Form(...)):
    request.session["user"] = u.strip()
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    user = request.session.get("user")
    if not user: return RedirectResponse(url="/")
    mensajes = "".join([f"<div class='msg'><b>{m['u']}:</b> {m['t']}</div>" for m in chat_global])
    return f"<html><body>{CSS}<div class='box'><h3>Chat Grupal</h3><div style='height:250px; overflow-y:auto;'>{mensajes}</div><form action='/postear' method='post'><input name='m' placeholder='Mensaje...' required><button class='btn'>Enviar</button></form><br><a href='/logout' style='color:red; font-size:12px; text-decoration:none;'>Cerrar Sesión</a></div></body></html>"

@app.post("/postear")
async def postear(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user:
        chat_global.append({"u": user, "t": m[:100]})
        if len(chat_global) > 20: chat_global.pop(0)
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    # Verificación minuciosa del puerto
    port_env = os.environ.get("PORT")
    puerto_final = int(port_env) if port_env else 8080
    uvicorn.run(app, host="0.0.0.0", port=puerto_final)
