import os
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# -------------------------
# ESCRIBIENDO (typing)
# -------------------------
usuarios_escribiendo = {}

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

def render(template_name, request, context):
    return templates.TemplateResponse(
        request,
        template_name,
        context
    )

# -------------------------
# FUNCIÓN ACTIVIDAD
# -------------------------
def actualizar_actividad(usuario):
    if engine:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE usuarios
                SET ultima_actividad = NOW()
                WHERE nombre = :usuario
            """), {"usuario": usuario})
            conn.commit()

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
                    email TEXT UNIQUE,
                    ultima_actividad TIMESTAMP,
                    premium BOOLEAN DEFAULT FALSE
                )
            """))

            conn.execute(text("""
                ALTER TABLE usuarios
                ADD COLUMN IF NOT EXISTS ultima_actividad TIMESTAMP;
            """))

            conn.execute(text("""
                ALTER TABLE usuarios
                ADD COLUMN IF NOT EXISTS premium BOOLEAN DEFAULT FALSE;
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

        if engine:
            with engine.connect() as conn:

                result = conn.execute(text("""
                    SELECT * FROM usuarios WHERE nombre = :usuario
                """), {"usuario": usuario}).fetchone()

                if not result:
                    conn.execute(text("""
                        INSERT INTO usuarios (nombre, email, ultima_actividad)
                        VALUES (:nombre, :email, NOW())
                    """), {
                        "nombre": usuario,
                        "email": f"{usuario}@temp.com"
                    })
                    conn.commit()

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

        if usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

        usuarios = []
        es_premium = False

        if engine:
            with engine.connect() as conn:

                result = conn.execute(text("""
                    SELECT nombre,
                    CASE 
                        WHEN ultima_actividad > NOW() - INTERVAL '10 seconds'
                        THEN true
                        ELSE false
                    END as en_linea
                    FROM usuarios
                """))

                usuarios = [{"nombre": row[0], "online": row[1]} for row in result.fetchall()]

                if usuario_actual != "Invitado":
                    result = conn.execute(text("""
                        SELECT premium FROM usuarios WHERE nombre = :usuario
                    """), {"usuario": usuario_actual}).fetchone()

                    if result:
                        es_premium = result[0]

        return render("index.html", request, {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": None,
            "mensajes": [],
            "es_premium": es_premium
        })

    except:
        return mostrar_error()

# -------------------------
# CHAT GLOBAL
# -------------------------
@app.get("/global")
async def chat_global(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

        usuarios = []
        mensajes = []
        es_premium = False

        if engine:
            with engine.connect() as conn:

                result = conn.execute(text("""
                    SELECT nombre,
                    CASE 
                        WHEN ultima_actividad > NOW() - INTERVAL '10 seconds'
                        THEN true
                        ELSE false
                    END as en_linea
                    FROM usuarios
                """))

                usuarios = [{"nombre": row[0], "online": row[1]} for row in result.fetchall()]

                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY id ASC
                """))

                mensajes = [
                    {"emisor": row[0], "mensaje": row[1]}
                    for row in result.fetchall()
                ]

                if usuario_actual != "Invitado":
                    result = conn.execute(text("""
                        SELECT premium FROM usuarios WHERE nombre = :usuario
                    """), {"usuario": usuario_actual}).fetchone()

                    if result:
                        es_premium = result[0]

        return render("index.html", request, {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": "GLOBAL",
            "mensajes": mensajes,
            "es_premium": es_premium
        })

    except:
        return mostrar_error()

# -------------------------
# CHAT PRIVADO
# -------------------------
@app.get("/chat/{usuario}")
async def chat(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

        if usuario == usuario_actual:
            return RedirectResponse("/", status_code=303)

        if usuario_actual == "Invitado":
            return RedirectResponse("/", status_code=303)

        usuarios = []
        mensajes = []
        es_premium = False

        if engine:
            with engine.connect() as conn:

                result = conn.execute(text("""
                    SELECT nombre,
                    CASE 
                        WHEN ultima_actividad > NOW() - INTERVAL '10 seconds'
                        THEN true
                        ELSE false
                    END as en_linea
                    FROM usuarios
                """))

                usuarios = [{"nombre": row[0], "online": row[1]} for row in result.fetchall()]

                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE (emisor = :u1 AND receptor = :u2)
                       OR (emisor = :u2 AND receptor = :u1)
                """), {"u1": usuario_actual, "u2": usuario})

                mensajes = [
                    {"emisor": row[0], "mensaje": row[1]}
                    for row in result.fetchall()
                ]

                result = conn.execute(text("""
                    SELECT premium FROM usuarios WHERE nombre = :usuario
                """), {"usuario": usuario_actual}).fetchone()

                if result:
                    es_premium = result[0]

        return render("index.html", request, {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes,
            "es_premium": es_premium
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

        if usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

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

        if receptor == "GLOBAL":
            return RedirectResponse("/global", status_code=303)

        return RedirectResponse(f"/chat/{receptor}", status_code=303)

    except:
        return mostrar_error()

# -------------------------
# API PRIVADOS
# -------------------------
@app.get("/mensajes_privados/{usuario}")
async def obtener_mensajes_privados(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario")

        if usuario_actual and usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

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

# -------------------------
# API GLOBAL
# -------------------------
@app.get("/mensajes_global")
async def obtener_mensajes_global(request: Request):
    try:
        usuario_actual = request.session.get("usuario")

        if usuario_actual and usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

        mensajes = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY id ASC
                """))

                mensajes = [
                    {"emisor": row[0], "mensaje": row[1]}
                    for row in result.fetchall()
                ]

        return {"mensajes": mensajes}

    except:
        return {"mensajes": []}

# -------------------------
# 🔔 NOTIFICACIONES GLOBALES (NUEVO)
# -------------------------
@app.get("/notificaciones")
async def notificaciones(request: Request):
    try:
        usuario_actual = request.session.get("usuario")

        if not usuario_actual or usuario_actual == "Invitado":
            return {"nuevos": []}

        nuevos = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE receptor = :usuario
                    ORDER BY id DESC
                    LIMIT 5
                """), {"usuario": usuario_actual})

                nuevos = [
                    {"emisor": row[0], "mensaje": row[1]}
                    for row in result.fetchall()
                ]

        return {"nuevos": nuevos}

    except Exception as e:
        print("ERROR NOTIFICACIONES:", e)
        return {"nuevos": []}

# -------------------------
# TYPING
# -------------------------
@app.post("/typing")
async def typing(request: Request, receptor: str = Form(...)):
    try:
        usuario_actual = request.session.get("usuario")

        if not usuario_actual or usuario_actual == "Invitado":
            return {"ok": False}

        if usuario_actual == receptor:
            return {"ok": False}

        usuarios_escribiendo[(usuario_actual, receptor)] = True

        return {"ok": True}

    except:
        return {"ok": False}

@app.get("/typing_status/{usuario}")
async def typing_status(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario")

        if not usuario_actual:
            return {"typing": False}

        if usuario == usuario_actual:
            return {"typing": False}

        estado = usuarios_escribiendo.get((usuario, usuario_actual), False)

        usuarios_escribiendo[(usuario, usuario_actual)] = False

        return {"typing": estado}

    except:
        return {"typing": False}
