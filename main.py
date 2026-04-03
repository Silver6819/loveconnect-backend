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
        print("ERROR DB:", e)

# -------------------------
# TEMPLATES
# -------------------------
templates = Jinja2Templates(directory="templates")

templates.env.cache = None
templates.env.auto_reload = True

# 🔥 HELPER CORREGIDO FINAL
def render(template_name, request, context):
    return templates.TemplateResponse(
        request,
        template_name,
        context
    )

# -------------------------
# ERROR HANDLER
# -------------------------
def mostrar_error():
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

            # 🔥 NUEVO: FORZAR RECREACIÓN DE TABLA MENSAJES
            conn.execute(text("DROP TABLE IF EXISTS mensajes"))

            conn.execute(text("""
                CREATE TABLE mensajes (
                    id SERIAL PRIMARY KEY,
                    emisor TEXT,
                    receptor TEXT,
                    mensaje TEXT
                )
            """))

            conn.commit()

    except:
        print("ERROR STARTUP")

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
    except:
        return mostrar_error()

# -------------------------
# LOGOUT
# -------------------------
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

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

        return render("index.html", request, {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": None,
            "mensajes": []
        })

    except:
        return mostrar_error()

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

    except:
        return mostrar_error()

# -------------------------
# CHAT
# -------------------------
@app.get("/chat/{usuario}")
async def chat(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if usuario == usuario_actual:
            return RedirectResponse("/", status_code=303)

        if usuario_actual == "Invitado":
            return RedirectResponse("/", status_code=303)

        usuarios = []
        mensajes = []

        if engine:
            with engine.connect() as conn:

                result = conn.execute(text("SELECT nombre FROM usuarios"))
                usuarios = [row[0] for row in result.fetchall()]

                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE (emisor = :u1 AND receptor = :u2)
                       OR (emisor = :u2 AND receptor = :u1)
                """), {"u1": usuario_actual, "u2": usuario})

                mensajes = result.fetchall()

        return render("index.html", request, {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes
        })

    except:
        return mostrar_error()

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

    except:
        return mostrar_error()

# -------------------------
# API MENSAJES (AUTO-REFRESH)
# -------------------------
@app.get("/mensajes_privados/{usuario}")
async def obtener_mensajes_privados(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario")

        if not usuario_actual or usuario_actual == "Invitado":
            return {"mensajes": []}

        mensajes = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE (emisor = :u1 AND receptor = :u2)
                       OR (emisor = :u2 AND receptor = :u1)
                    ORDER BY id ASC
                """), {"u1": usuario_actual, "u2": usuario})

                mensajes = [
                    {"emisor": row[0], "mensaje": row[1]}
                    for row in result.fetchall()
                ]

        return {"mensajes": mensajes}

    except:
        return {"mensajes": []}
