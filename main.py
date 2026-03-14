import os, uvicorn, time, random
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-secret-key")

# --- BASES DE DATOS EN MEMORIA ---
ADMIN_NAME = "Silver Breaker"
chat_log = []
punished_users = {}
profiles = {} # {usuario: {"bio": "", "votes": 0}}
suggestions = []

def is_punished(username):
    if username in punished_users:
        if datetime.utcnow() < punished_users[username]: return True
        else: del punished_users[username]
    return False

# --- RUTA PRINCIPAL (CHAT Y LOGIN) ---
@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    
    if not user:
        return HTMLResponse("""
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body{font-family:sans-serif; background:#fff0f6; display:flex; justify-content:center; align-items:center; height:100vh; margin:0;}
            .reg-card{background:white; padding:30px; border-radius:30px; box-shadow:0 10px 25px rgba(0,0,0,0.05); text-align:center; width:85%; max-width:350px;}
            video{width:100%; border-radius:15px; background:#000; margin-bottom:10px;}
            input{width:100%; padding:12px; margin:10px 0; border:1px solid #eee; border-radius:12px;}
            .btn{background:#ff4fa3; color:white; border:none; padding:15px; width:100%; border-radius:12px; font-weight:bold;}
        </style></head>
        <body>
            <div class="reg-card">
                <h2 style="color:#ff4fa3;">💖 LoveConnect</h2>
                <video id="video" autoplay></video>
                <button onclick="takePhoto()" style="font-size:11px; margin-bottom:10px;">📷 Activar Cámara</button>
                <form action="/login" method="post">
                    <input name="username" placeholder="Tu nombre artístico" required autocomplete="off">
                    <button type="submit" class="btn">Entrar al Chat</button>
                </form>
            </div>
            <script>
                function takePhoto() {
                    navigator.mediaDevices.getUserMedia({ video: true }).then(s => document.getElementById("video").srcObject = s);
                }
            </script>
        </body></html>
        """)

    if is_punished(user):
        return HTMLResponse("<body style='text-align:center;padding-top:50px;'><h1>🚫 Sala de Castigo</h1><p>Has sido restringido por 24h.</p></body>")

    # GENERAR BURBUJAS DE CHAT (Lógica Messenger)
    mensajes_html = ""
    for m in chat_log:
        es_mio = m["user"] == user
        es_admin = m["user"] == ADMIN_NAME
        clase = "derecha" if es_mio else "izquierda"
        estrella = "🌟" if es_admin else ""
        color = "#ff4fa3" if es_mio else "#eee"
        texto_color = "white" if es_mio else "#333"
        
        mensajes_html += f'''
        <div style="display:flex; flex-direction:{'row-reverse' if es_mio else 'row'}; margin-bottom:10px; align-items:flex-end;">
            <div style="background:{color}; color:{texto_color}; padding:10px 15px; border-radius:18px; max-width:75%; font-size:14px; box-shadow:0 2px 5px rgba(0,0,0,0.05);">
                <small style="font-size:10px; opacity:0.8;">{m["user"]} {estrella}</small><br>{m["text"]}
            </div>
        </div>
        '''

    # PANEL DE CONTROL SOLO PARA SILVER BREAKER
    admin_tools = ""
    if user == ADMIN_NAME:
        admin_tools = """
        <form action="/punish" method="post" style="background:#333; padding:10px; border-radius:10px; margin:10px;">
            <input name="target" placeholder="Nombre a castigar" style="width:60%; padding:5px;">
            <button style="background:red; color:white; border:none; padding:5px;">Castigar 24h</button>
        </form>
        """

    return HTMLResponse(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body{{margin:0; font-family:sans-serif; background:#fff0f6;}}
        header{{background:white; padding:15px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; position:sticky; top:0;}}
        #chat-box{{height:70vh; overflow-y:auto; padding:15px; display:flex; flex-direction:column;}}
        .input-area{{background:white; padding:10px; display:flex; border-top:1px solid #eee;}}
        input{{flex:1; padding:12px; border:1px solid #eee; border-radius:25px; outline:none;}}
        .send-btn{{background:#ff4fa3; color:white; border:none; padding:10px 20px; border-radius:25px; margin-left:5px;}}
    </style></head>
    <body>
        <header>
            <b style="color:#ff4fa3;">💖 LoveConnect</b>
            <a href="/perfil" style="text-decoration:none; font-size:14px;">👤 Perfil</a>
        </header>
        <div id="chat-box">
            {mensajes_html if mensajes_html else '<p style="text-align:center; color:gray;">No hay mensajes. ¡Sé el primero!</p>'}
            <div id="anchor"></div>
        </div>
        <form action="/send" method="post" class="input-area">
            <input name="msg" placeholder="Escribe un mensaje..." required autocomplete="off">
            <button class="send-btn">Enviar</button>
        </form>
        <div style="text-align:center; padding:5px;">
            <a href="/match" style="font-size:12px; color:#ff4fa3; text-decoration:none;">💘 Match Rápido</a>
        </div>
        {admin_tools}
        <script>window.onload = () => {{ document.getElementById('anchor').scrollIntoView(); }};</script>
    </body></html>
    """)

# --- RUTAS DE ACCIÓN ---
@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles:
        profiles[username] = {"bio": "¡Hola! Estoy usando LoveConnect.", "votes": 0}
    return RedirectResponse(url="/", status_code=303)

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user")
    if user and msg.strip():
        chat_log.append({"user": user, "text": msg})
        if len(chat_log) > 50: chat_log.pop(0)
    return RedirectResponse(url="/", status_code=303)

@app.get("/perfil")
async def view_profile(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"bio": "Sin bio", "votes": 0})
    return HTMLResponse(f"""
    <body style="font-family:sans-serif; text-align:center; padding:20px; background:#fff0f6;">
        <button onclick="history.back()" style="float:left;">⬅ Regresar</button><br><br>
        <div style="background:white; padding:20px; border-radius:20px;">
            <h2>{user}</h2>
            <p>{p['bio']}</p>
            <h3 style="color:#ff4fa3;">Votos: {p['votes']} 👍</h3>
            <form action="/vote/{user}" method="post"><button style="padding:10px 20px;">❤️ Dar Corazón</button></form>
        </div>
        <div style="margin-top:20px; background:white; padding:15px; border-radius:20px;">
            <h4>¿Qué actualización necesitas?</h4>
            <form action="/suggestion" method="post">
                <textarea name="text" style="width:100%; border-radius:10px;"></textarea><br>
                <button type="submit">Enviar Sugerencia</button>
            </form>
        </div>
    </body>
    """)

@app.post("/vote/{target}")
async def vote(target: str):
    if target in profiles: profiles[target]["votes"] += 1
    return RedirectResponse(url="/perfil", status_code=303)

@app.post("/suggestion")
async def suggest(request: Request, text: str = Form(...)):
    user = request.session.get("user")
    suggestions.append({"user": user, "text": text})
    return RedirectResponse(url="/perfil", status_code=303)

@app.get("/match")
async def quick_match():
    if not profiles: return RedirectResponse(url="/")
    lucky = random.choice(list(profiles.keys()))
    return HTMLResponse(f"""
        <body style="text-align:center; padding-top:100px; font-family:sans-serif; background:#fff0f6;">
            <h1 style="font-size:50px;">💘</h1>
            <h2>¡Tu match es: {lucky}!</h2>
            <button onclick="history.back()" style="padding:15px 30px; border-radius:20px; border:none; background:#ff4fa3; color:white;">Regresar</button>
        </body>
    """)

@app.post("/punish")
async def punish(target: str = Form(...)):
    punished_users[target] = datetime.utcnow() + timedelta(hours=24)
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
