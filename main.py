import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
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
        return

    with engine.connect() as conn:
        # Usuarios
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                email TEXT UNIQUE
            )
        """))

        # Mensajes privados
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id SERIAL PRIMARY KEY,
                emisor TEXT,
                receptor TEXT,
                mensaje TEXT
            )
        """))

        conn.commit()

# -------------------------
# HOME
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    usuarios = []

    if engine:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT nombre FROM usuarios"))
            usuarios = [row[0] for row in result.fetchall()]

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "usuarios": usuarios,
            "chat_con": None,
            "mensajes": []
        }
    )

# -------------------------
# REGISTRO
# -------------------------

@app.post("/registro", response_class=HTMLResponse)
async def registro(request: Request, nombre: str = Form(...), email: str = Form(...)):
    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"),
                    {"nombre": nombre, "email": email}
                )
                conn.commit()
        except:
            pass

    return RedirectResponse("/", status_code=303)

# -------------------------
# ABRIR CHAT
# -------------------------

@app.get("/chat/{usuario}", response_class=HTMLResponse)
async def chat(request: Request, usuario: str):
    usuarios = []
    mensajes = []

    # 👇 TU USUARIO (simple por ahora)
    usuario_actual = "Marcos Ramírez"

    if engine:
        with engine.connect() as conn:
            usuarios = [row[0] for row in conn.execute(text("SELECT nombre FROM usuarios"))]

            result = conn.execute(text("""
                SELECT emisor, mensaje FROM mensajes
                WHERE (emisor = :yo AND receptor = :otro)
                   OR (emisor = :otro AND receptor = :yo)
                ORDER BY id ASC
            """), {"yo": usuario_actual, "otro": usuario})

            mensajes = result.fetchall()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "usuarios": usuarios,
            "chat_con": usuario,
            "mensajes": mensajes
        }
    )

# -------------------------
# ENVIAR MENSAJE PRIVADO
# -------------------------

@app.post("/mensaje", response_class=HTMLResponse)
async def enviar_mensaje(
    request: Request,
    receptor: str = Form(...),
    mensaje: str = Form(...)
):
    usuario_actual = "Marcos Ramírez"

    if engine:
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO mensajes (emisor, receptor, mensaje)
                    VALUES (:emisor, :receptor, :mensaje)
                """),
                {
                    "emisor": usuario_actual,
                    "receptor": receptor,
                    "mensaje": mensaje
                }
            )
            conn.commit()

    return RedirectResponse(f"/chat/{receptor}", status_code=303)
