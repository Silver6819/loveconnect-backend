import os, uvicorn, time, random
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver-secret-key")

# --- BASES DE DATOS TEMPORALES ---
ADMIN_NAME = "Silver Breaker"
chat_log = []
punished_users = {}
profiles = {} # {usuario: {"bio": "", "photo": "", "votes": 0}}
suggestions = []

# --- LÓGICA DE MÓDULOS (Propuesta ChatGPT integrada) ---
def is_punished(username):
    if username in punished_users:
        if datetime.utcnow() < punished_users[username]: return True
        else: del punished_users[username]
    return False

# --- RUTAS PRINCIPALES ---

@app.get("/")
async def home(request: Request):
    user = request.session.get("user")
    
    if not user:
        # Registro con Cámara (JS) + Galería (HTML)
        return HTMLResponse("""
        <html>
        <head><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>body{font-family:sans-serif; background:#fff0f6; text-align:center; padding:20px;}</style></head>
        <body>
            <h2>📸 Registro LoveConnect</h2>
            <video id="video" autoplay style="width:100%; max-width:300px; border-radius:20px;"></video><br>
            <button onclick="takePhoto()" style="padding:10px; margin:10px;">📷 Tomar Foto</button>
            <form action="/login" method="post">
                <input name="username" placeholder="Tu nombre" required style="padding:10px; border-radius:10px;"><br>
                <input type="file" accept="image/*" style="margin:10px;"><br>
                <button type="submit" style="background:#ff4fa3; color:white; border:none; padding:15px 30px; border-radius:15px;">Entrar al Chat</button>
            </form>
            <script>
                navigator.mediaDevices.getUserMedia({ video: true }).then(s => document.getElementById("video").srcObject = s);
                function takePhoto() { alert("¡Foto capturada!"); }
            </script>
        </body></html>
        """)

    if is_punished(user):
        return HTMLResponse("<h1>🚫 Sala de Castigo</h1><p>Vuelve en 24 horas.</p><button onclick='history.back()'>⬅ Regresar</button>")

    # Render del Chat e Interfaz
    return HTMLResponse(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        .nav-btn {{ background:#ff4fa3; color:white; padding:10px; border-radius:10px; text-decoration:none; font-size:12px; }}
    </style></head>
    <body style="margin:0; font-family:sans-serif;">
        <header style="background:#ff4fa3; color:white; padding:15px; display:flex; justify-content:space-between; align-items:center;">
            <span>💖 LoveConnect</span>
            <a href="/perfil" class="nav-btn">👤 Mi Perfil</a>
        </header>
        <div id="chat" style="height:60vh; overflow-y:auto; padding:10px; background:#f9f9f9;">
            <p>Bienvenido, {user} 🌟</p>
        </div>
        <form action="/send" method="post" style="display:flex; padding:10px;">
            <input name="msg" style="flex:1; border-radius:20px; padding:10px;" placeholder="Escribe...">
            <button style="border:none; background:#ff4fa3; color:white; border-radius:20px; padding:10px 20px;">Enviar</button>
        </form>
        <div style="text-align:center; padding:10px;">
            <a href="/match" style="color:#ff4fa3; font-weight:bold; text-decoration:none;">💘 Match Rápido</a>
        </div>
    </body></html>
    """)

# --- RUTAS DE PERFIL Y VOTOS ---

@app.get("/perfil")
async def view_profile(request: Request):
    user = request.session.get("user")
    p = profiles.get(user, {"bio": "Sin bio", "votes": 0})
    return HTMLResponse(f"""
    <body style="font-family:sans-serif; text-align:center; background:#fff0f6;">
        <button onclick="history.back()" style="position:absolute; left:10px; top:10px;">⬅ Regresar</button>
        <h2>Perfil de {user}</h2>
        <div style="background:white; margin:20px; padding:20px; border-radius:20px;">
            <p>{p['bio']}</p>
            <h3>Votos: {p['votes']} 👍</h3>
            <form action="/vote/{user}" method="post"><button>Votar por mí</button></form>
        </div>
        <hr>
        <h3>💡 Sugerir Actualización</h3>
        <form action="/suggestion" method="post">
            <textarea name="text" placeholder="¿Qué le falta a la app?"></textarea><br>
            <button type="submit">Enviar Sugerencia</button>
        </form>
    </body>
    """)

@app.post("/vote/{target}")
async def vote(target: str):
    if target in profiles: profiles[target]["votes"] += 1
    return RedirectResponse(url="/perfil", status_code=303)

@app.post("/suggestion")
async def add_suggest(request: Request, text: str = Form(...)):
    user = request.session.get("user")
    suggestions.append({"user": user, "text": text})
    return RedirectResponse(url="/perfil", status_code=303)

@app.get("/match")
async def quick_match():
    if not profiles: return HTMLResponse("No hay perfiles aún. <button onclick='history.back()'>Regresar</button>")
    lucky = random.choice(list(profiles.keys()))
    return HTMLResponse(f"<h1>💘 Match con: {lucky}</h1><button onclick='history.back()'>Regresar</button>")

# --- LÓGICA DE LOGIN Y ENVÍO ---
@app.post("/login")
async def login(request: Request, username: str = Form(...)):
    request.session["user"] = username
    if username not in profiles:
        profiles[username] = {"bio": "¡Hola! Soy nuevo aquí.", "votes": 0}
    return RedirectResponse(url="/", status_code=303)

@app.post("/send")
async def send(request: Request, msg: str = Form(...)):
    user = request.session.get("user", "Anónimo")
    chat_log.append({"user": user, "text": msg})
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
