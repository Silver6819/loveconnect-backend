import os
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware
import base64

app = FastAPI()

# SESIONES
app.add_middleware(SessionMiddleware, secret_key="supersecreto")

# BASE DE DATOS
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = None

if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"sslmode": "require"}
        )
    except Exception as e:
        print("ERROR DB:", e)

# TEMPLATES
templates = Jinja2Templates(directory="templates")

# 🔥 FIX REAL AQUÍ
def render(request, template_name, context):
    return templates.TemplateResponse(
        request,
        template_name,
        context
    )

# ERROR
def mostrar_error():
    return HTMLResponse(f"<pre>{traceback.format_exc()}</pre>")

# STARTUP
@app.on_event("startup")
def startup():
    try:
        if not engine:
            return

        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    emisor TEXT,
                    receptor TEXT,
                    mensaje TEXT,
                    fecha TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.commit()
    except:
        print(traceback.format_exc())

# HOME
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        return render(request, "index.html", {
            "usuarios": [],
            "usuario_actual": request.session.get("usuario", "Invitado"),
            "chat_con": None,
            "mensajes": [],
            "es_premium": False
        })
    except:
        return mostrar_error()

# LOGIN
@app.post("/set_usuario")
async def set_usuario(request: Request, usuario: str = Form(...)):
    try:
        request.session["usuario"] = usuario
        return RedirectResponse("/", status_code=303)
    except:
        return mostrar_error()

# CHAT
@app.get("/chat/{usuario}", response_class=HTMLResponse)
async def chat(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje
                    FROM mensajes
                    WHERE (emisor = :yo AND receptor = :otro)
                       OR (emisor = :otro AND receptor = :yo)
                    ORDER BY fecha ASC
                """), {"yo": usuario_actual, "otro": usuario})

                mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]

        return render(request, "index.html", {
            "usuarios": [],
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes,
            "es_premium": False
        })
    except:
        return mostrar_error()

# ENVIAR MENSAJE
@app.post("/mensaje")
async def enviar_mensaje(request: Request, receptor: str = Form(...), mensaje: str = Form(...)):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if engine:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO mensajes (emisor, receptor, mensaje)
                    VALUES (:e, :r, :m)
                """), {"e": usuario_actual, "r": receptor, "m": mensaje})
                conn.commit()

        return {"ok": True}
    except:
        return mostrar_error()

# REFRESH
@app.get("/mensajes_privados/{usuario}")
async def mensajes_privados(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje
                    FROM mensajes
                    WHERE (emisor = :yo AND receptor = :otro)
                       OR (emisor = :otro AND receptor = :yo)
                    ORDER BY fecha ASC
                """), {"yo": usuario_actual, "otro": usuario})

                mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]

        return {"mensajes": mensajes}
    except:
        return mostrar_error()

# FOTO
@app.post("/enviar_foto")
async def enviar_foto(request: Request, data: dict = Body(...)):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        imagen = data.get("imagen")
        receptor = data.get("receptor")

        if not imagen:
            return {"ok": False}

        imagen = imagen.split(",")[1]
        imagen_bytes = base64.b64decode(imagen)

        os.makedirs("static", exist_ok=True)

        nombre = f"foto_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta = f"static/{nombre}"

        with open(ruta, "wb") as f:
            f.write(imagen_bytes)

        if engine:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO mensajes (emisor, receptor, mensaje)
                    VALUES (:e, :r, :m)
                """), {
                    "e": usuario_actual,
                    "r": receptor,
                    "m": f"[FOTO]{ruta}"
                })
                conn.commit()

        return {"ok": True}
    except:
        return mostrar_error()
