import os
import traceback
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# -------------------------
# SESIONES
# -------------------------
app.add_middleware(SessionMiddleware, secret_key="supersecreto")

# -------------------------
# BASE DE DATOS
# -------------------------
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
        print("ERROR CONECTANDO DB:", e)

# -------------------------
# TEMPLATES (CORREGIDO)
# -------------------------
templates = Jinja2Templates(directory="templates")

# 🔥 CONFIGURACIÓN SEGURA (sin romper FastAPI)
templates.env.cache = {}
templates.env.auto_reload = True

# -------------------------
# FUNCIÓN PARA MOSTRAR ERRORES
# -------------------------
def mostrar_error(e):
    return HTMLResponse(f"""
    <h1>💥 ERROR DETECTADO</h1>
    <pre>{traceback.format_exc()}</pre>
    """)

# -------------------------
# STARTUP
# -------------------------
@app.on_event("startup")
def startup():
    try:
        if not engine:
            return

        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT,
                    email TEXT UNIQUE
                )
            """))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    emisor TEXT,
                    receptor TEXT,
                    mensaje TEXT
                )
            """))

            conn.commit()

    except Exception as e:
        print("ERROR STARTUP:", e)

# -------------------------
# TEST
# -------------------------
@app.get("/test")
def test():
    return {"status": "ok"}

# -------------------------
# LOGIN
# -------------------------
@app.post("/set_usuario")
async def set_usuario(request: Request, usuario: str = Form(...)):
    try:
        request.session["usuario"] = usuario
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        return mostrar_error(e)

# -------------------------
# HOME
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        usuarios = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT nombre FROM usuarios"))
                usuarios = [row[0] for row in result.fetchall()]

        return templates.TemplateResponse("index.html", {
            "request": request,
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": None,
            "mensajes": []
        })

    except Exception as e:
        return mostrar_error(e)

# -------------------------
# REGISTRO
# -------------------------
@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    try:
        if engine:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO usuarios (nombre, email) VALUES (:nombre, :email)"),
                    {"nombre": nombre, "email": email}
                )
                conn.commit()

        return RedirectResponse("/", status_code=303)

    except Exception as e:
        return mostrar_error(e)

# -------------------------
# CHAT
# -------------------------
@app.get("/chat/{usuario}")
async def chat(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        # evitar chatear contigo mismo
        if usuario == usuario_actual:
            return RedirectResponse("/", status_code=303)

        # evitar usuario no logueado
        if usuario_actual == "Invitado":
            return RedirectResponse("/", status_code=303)

        usuarios = []
        mensajes = []

        if engine:
            with engine.connect() as conn:

                # usuarios
                result = conn.execute(text("SELECT nombre FROM usuarios"))
                usuarios = [row[0] for row in result.fetchall()]

                # mensajes
                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE (emisor = :u1 AND receptor = :u2)
                       OR (emisor = :u2 AND receptor = :u1)
                """), {"u1": usuario_actual, "u2": usuario})

                mensajes = result.fetchall()

        return templates.TemplateResponse("index.html", {
            "request": request,
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes
        })

    except Exception as e:
        return mostrar_error(e)

# -------------------------
# MENSAJE
# -------------------------
@app.post("/mensaje")
async def enviar_mensaje(request: Request, receptor: str = Form(...), mensaje: str = Form(...)):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if usuario_actual == "Invitado":
            return RedirectResponse("/", status_code=303)

        if engine:
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO mensajes (emisor, receptor, mensaje)
                    VALUES (:emisor, :receptor, :mensaje)
                """), {
                    "emisor": usuario_actual,
                    "receptor": receptor,
                    "mensaje": mensaje
                })
                conn.commit()

        return RedirectResponse(f"/chat/{receptor}", status_code=303)

    except Exception as e:
        return mostrar_error(e)
