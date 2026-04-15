import os
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware
import urllib.parse
import urllib.request

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
    return templates.TemplateResponse(request, template_name, context)

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
                ALTER TABLE usuarios
                ADD COLUMN IF NOT EXISTS ultimo_mensaje_visto INTEGER DEFAULT 0;
            """))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    emisor TEXT,
                    receptor TEXT,
                    mensaje TEXT
                )
            """))

            conn.execute(text("""
                ALTER TABLE mensajes
                ADD COLUMN IF NOT EXISTS fecha TIMESTAMP DEFAULT NOW();
            """))

            conn.commit()

    except:
        print("ERROR STARTUP")

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
# CHAT PRIVADO
# -------------------------
@app.get("/chat/{usuario}", response_class=HTMLResponse)
async def chat(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

        mensajes = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, receptor, mensaje
                    FROM mensajes
                    WHERE (emisor = :yo AND receptor = :otro)
                       OR (emisor = :otro AND receptor = :yo)
                    ORDER BY fecha ASC
                """), {
                    "yo": usuario_actual,
                    "otro": usuario
                })

                mensajes = [
                    {
                        "emisor": row[0],
                        "receptor": row[1],
                        "mensaje": row[2]
                    }
                    for row in result.fetchall()
                ]

        return render("index.html", request, {
            "usuarios": [],
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes,
            "es_premium": False
        })

    except:
        return mostrar_error()

# -------------------------
# 🌍 CHAT GLOBAL
# -------------------------
@app.get("/global", response_class=HTMLResponse)
async def global_chat(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if usuario_actual != "Invitado":
            actualizar_actividad(usuario_actual)

        mensajes = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje
                    FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY fecha ASC
                """))

                mensajes = [
                    {
                        "emisor": row[0],
                        "receptor": "GLOBAL",
                        "mensaje": row[1]
                    }
                    for row in result.fetchall()
                ]

        return render("index.html", request, {
            "usuarios": [],
            "usuario_actual": usuario_actual,
            "chat_con": "GLOBAL",
            "mensajes": mensajes,
            "es_premium": False
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

        # 🔥 FIX GLOBAL
        if receptor == "GLOBAL":
            receptor = "GLOBAL"

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

        return {"ok": True}

    except:
        return {"ok": False}

# -------------------------
# 🌍 MENSAJES GLOBAL (REFRESH)
# -------------------------
@app.get("/mensajes_global")
async def mensajes_global():
    try:
        mensajes = []

        if engine:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje
                    FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY fecha ASC
                """))

                mensajes = [
                    {"emisor": row[0], "mensaje": row[1]}
                    for row in result.fetchall()
                ]

        return {"mensajes": mensajes}

    except:
        return {"mensajes": []}

# -------------------------
# 🔔 NOTIFICACIONES
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
                    SELECT ultimo_mensaje_visto 
                    FROM usuarios 
                    WHERE nombre = :usuario
                """), {"usuario": usuario_actual}).fetchone()

                ultimo_visto = result[0] if result else 0

                result = conn.execute(text("""
                    SELECT id, emisor, mensaje 
                    FROM mensajes
                    WHERE receptor = :usuario
                    AND id > :ultimo_visto
                    ORDER BY id ASC
                    LIMIT 5
                """), {
                    "usuario": usuario_actual,
                    "ultimo_visto": ultimo_visto
                })

                rows = result.fetchall()

                nuevos = [
                    {"id": row[0], "emisor": row[1], "mensaje": row[2]}
                    for row in rows
                ]

                if rows:
                    ultimo_id = rows[-1][0]

                    conn.execute(text("""
                        UPDATE usuarios
                        SET ultimo_mensaje_visto = :ultimo
                        WHERE nombre = :usuario
                    """), {
                        "ultimo": ultimo_id,
                        "usuario": usuario_actual
                    })
                    conn.commit()

        return {"nuevos": nuevos}

    except:
        return {"nuevos": []}

# -------------------------
# 💰 PAYPAL REAL
# -------------------------
PAYPAL_VERIFY_URL = "https://ipnpb.paypal.com/cgi-bin/webscr"

@app.post("/paypal_ipn")
async def paypal_ipn(request: Request):
    try:
        form = await request.form()
        data = dict(form)

        verify_data = {"cmd": "_notify-validate"}
        verify_data.update(data)

        encoded = urllib.parse.urlencode(verify_data).encode()
        req = urllib.request.Request(PAYPAL_VERIFY_URL, data=encoded)

        with urllib.request.urlopen(req) as response:
            verification = response.read().decode()

        if verification != "VERIFIED":
            return {"ok": False}

        if data.get("receiver_email") != "mr6874823@gmail.com":
            return {"ok": False}

        if data.get("payment_status") == "Completed":
            usuario = data.get("custom")

            if engine and usuario:
                with engine.connect() as conn:
                    conn.execute(text("""
                        UPDATE usuarios
                        SET premium = TRUE
                        WHERE nombre = :usuario
                    """), {"usuario": usuario})
                    conn.commit()

        return {"ok": True}

    except:
        return {"ok": False}
