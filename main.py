import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text

app = FastAPI()

# -------------------------
# BASE DE DATOS
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = create_engine(
    DATABASE_URL,
    connect_args={"sslmode": "require"}
) if DATABASE_URL else None

# -------------------------
# TEMPLATES
# -------------------------

templates = Jinja2Templates(directory="templates")

# -------------------------
# STARTUP
# -------------------------

@app.on_event("startup")
def startup():
    if not engine:
        print("⚠️ No DATABASE_URL")
        return

    try:
        with engine.connect() as conn:
            # Usuarios
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT,
                    email TEXT UNIQUE
                )
            """))

            # Mensajes
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT,
                    mensaje TEXT
                )
            """))

            conn.commit()

        print("✅ DB lista")

    except Exception as e:
        print("❌ Error DB:", e)

# -------------------------
# HOME
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    usuarios = []
    mensajes = []

    if engine:
        try:
            with engine.connect() as conn:
                # Usuarios
                result = conn.execute(text("SELECT nombre FROM usuarios ORDER BY id DESC"))
                usuarios = [row[0] for row in result.fetchall()]

                # Mensajes
                result = conn.execute(text("SELECT nombre, mensaje FROM mensajes ORDER BY id DESC LIMIT 20"))
                mensajes = result.fetchall()

        except Exception as e:
            print("Error:", e)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "mensaje": None,
            "usuarios": usuarios,
            "mensajes": mensajes
        }
    )

# -------------------------
# REGISTRO
# -------------------------

@app.post("/registro", response_class=HTMLResponse)
async def registro(request: Request, nombre: str = Form(...), email: str = Form(...)):
    mensaje = None
    usuarios = []
    mensajes = []

    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"),
                    {"nombre": nombre, "email": email}
                )
                conn.commit()

            mensaje = f"¡Hola {nombre}! Bienvenido 💘"

        except Exception:
            mensaje = "Ese correo ya está registrado ⚠️"

    # Recargar datos
    try:
        with engine.connect() as conn:
            usuarios = [row[0] for row in conn.execute(text("SELECT nombre FROM usuarios ORDER BY id DESC"))]
            mensajes = conn.execute(text("SELECT nombre, mensaje FROM mensajes ORDER BY id DESC LIMIT 20")).fetchall()
    except Exception as e:
        print(e)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "mensaje": mensaje,
            "usuarios": usuarios,
            "mensajes": mensajes
        }
    )

# -------------------------
# ENVIAR MENSAJE
# -------------------------

@app.post("/mensaje", response_class=HTMLResponse)
async def enviar_mensaje(request: Request, nombre: str = Form(...), mensaje: str = Form(...)):
    usuarios = []
    mensajes = []

    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO mensajes(nombre, mensaje) VALUES (:nombre, :mensaje)"),
                    {"nombre": nombre, "mensaje": mensaje}
                )
                conn.commit()
        except Exception as e:
            print("Error guardando mensaje:", e)

    # Recargar datos
    try:
        with engine.connect() as conn:
            usuarios = [row[0] for row in conn.execute(text("SELECT nombre FROM usuarios ORDER BY id DESC"))]
            mensajes = conn.execute(text("SELECT nombre, mensaje FROM mensajes ORDER BY id DESC LIMIT 20")).fetchall()
    except Exception as e:
        print(e)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "mensaje": None,
            "usuarios": usuarios,
            "mensajes": mensajes
        }
    )
