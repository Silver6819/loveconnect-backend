import os, uvicorn
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_infinity_2026")

# --- BASE DE DATOS ACTUALIZADA CON TU INFO ---
usuarios_db = {
    "Silver Breaker": {"p": "1234", "lvl": "∞", "join": datetime.utcnow(), "is_pre": True, "img": ""}
} 
chat_global = []
sugerencias_mejoras = []

# CONFIGURACIÓN DE TU PAYPAL (SEGÚN CAPTURA)
PAYPAL_BUSINESS_ID = "@silver676" 

def es_premium(user):
    u = usuarios_db.get(user)
    if not u: return False
    if u["is_pre"] or user == "Silver Breaker": return True
    return datetime.utcnow() < u["join"] + timedelta(days=3)

CSS_ESTELAR = """
<style>
:root { --pink: #ff2e88; --blue: #00e5ff; --purp: #9b5cff; }
body { background: #050510; color: white; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 15px; }
.container { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 20px; max-width: 450px; margin: auto; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 0 20px rgba(0,229,255,0.1); }
.lvl { background: var(--blue); color: #000; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
.btn-premium { background: linear-gradient(90deg, #f39c12, #e67e22); border: none; color: white; padding: 12px; width: 100%; border-radius: 25px; cursor: pointer; font-weight: bold; margin-top: 10px; }
.msg { background: rgba(255,255,255,0.08); padding: 10px; border-radius: 15px; margin-bottom: 10px; border-left: 3px solid var(--pink); animation: slideIn 0.3s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
input { width: 100%; padding: 10px; border-radius: 15px; border: 1px solid #333; background: #111; color: white; margin-bottom: 10px; }
</style>
"""

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return f"<html><head>{CSS_ESTELAR}</head><body><div class='container'><h1>❤️ LoveConnect</h1><form action='/login' method='post'><input name='u' placeholder='Usuario' required><input name='p' type='password' placeholder='Clave' required><button style='width:100%; background:var(--pink); border:none; color:white; padding:10px; border-radius:20px;'>ENTRAR</button></form></div></body></html>"

@app.post("/login")
async def login(request: Request, u: str = Form(...), p: str = Form(...)):
    if u not in usuarios_db:
        usuarios_db[u] = {"p": p, "lvl": 1, "join": datetime.utcnow(), "is_pre": False, "img": ""}
    if usuarios_db[u]["p"] == p:
        request.session["user"] = u
        return RedirectResponse(url="/chat", status_code=303)
    return "Credenciales incorrectas."

@app.get("/chat", response_class=HTMLResponse)
async def chat_view(request: Request):
    me = request.session.get("user")
    if not me: return RedirectResponse(url="/")
    
    u_data = usuarios_db[me]
    bloqueado = not es_premium(me)
    
    msgs = "".join([f"<div class='msg'><b>{m['u']} [LvL:{usuarios_db[m['u']]['lvl']}]:</b> {m['t']}</div>" for m in chat_global])

    # SISTEMA DE PAGO PAYPAL REAL
    paypal_html = ""
    if bloqueado:
        paypal_html = f"""
        <div style='background:rgba(255,0,0,0.1); border:1px solid red; padding:15px; border-radius:15px; text-align:center;'>
            <p>☢️ TU ACCESO GRATUITO HA EXPIRADO</p>
            <form action="https://www.paypal.com/cgi-bin/webscr" method="post" target="_top">
                <input type="hidden" name="cmd" value="_xclick">
                <input type="hidden" name="business" value="{PAYPAL_BUSINESS_ID}">
                <input type="hidden" name="item_name" value="LoveConnect Premium - {me}">
                <input type="hidden" name="amount" value="5.00">
                <input type="hidden" name="currency_code" value="USD">
                <button class='btn-premium'>DESBLOQUEAR PREMIUM (PayPal)</button>
            </form>
        </div>"""

    admin_panel = f"<hr><a href='/admin_db' style='color:var(--blue); font-size:12px; text-decoration:none;'>[GOD MODE: REGISTRO DE ALMAS]</a>" if me == "Silver Breaker" else ""

    return f"""
    <html><head>{CSS_ESTELAR}</head><body>
    <div class='container'>
        <div style='display:flex; justify-content:space-between;'><b>{me}</b> <span class='lvl'>LvL {u_data['lvl']}</span></div>
        <hr>
        {paypal_html if bloqueado else f'<div style="height:300px; overflow-y:auto; margin-bottom:10px;">{msgs}</div><form action="/postear" method="post"><input name="m" placeholder="Escribir mensaje..." required><button style="width:100%; background:var(--blue); border:none; padding:8px; border-radius:15px;">ENVIAR</button></form>'}
        
        <div style='margin-top:20px;'>
            <p style='font-size:11px; color:#888;'>SUGERIR MEJORA:</p>
            <form action='/sugerir' method='post'><input name='s' style='width:70%; font-size:12px;'><button style='width:25%; font-size:12px;'>Pedir</button></form>
        </div>
        {admin_panel}
        <br><a href='/logout' style='font-size:10px; color:grey;'>Cerrar Sesión</a>
    </div></body></html>
    """

@app.get("/admin_db", response_class=HTMLResponse)
async def admin_db(request: Request):
    if request.session.get("user") != "Silver Breaker": return "ACCESO DENEGADO"
    items = "".join([f"<li><b>{u}</b>: {d['p']} (LvL {d['lvl']})</li>" for u, d in usuarios_db.items()])
    return f"<html><head>{CSS_ESTELAR}</head><body><div class='container'><h2>BASE DE DATOS</h2><ul>{items}</ul><br><a href='/chat' style='color:var(--blue);'>Volver</a></div></body></html>"

@app.post("/postear")
async def postear(request: Request, m: str = Form(...)):
    user = request.session.get("user")
    if user and es_premium(user):
        chat_global.append({"u": user, "t": m.replace("<","&lt;")})
    return RedirectResponse(url="/chat", status_code=303)

@app.post("/sugerir")
async def sugerir(s: str = Form(...)):
    sugerencias_mejoras.append(s)
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
