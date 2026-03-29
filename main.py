import os
from urllib.parse import unquote
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

# -------------------------
# HOME
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    usuarios = []
    usuario_actual = "Marcos Ramírez"

    if engine:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM usuarios"))
            usuarios = [u[1] for u in result.fetchall()]
    return templates.TemplateResponse("index.html", {
        "request": request,
        "usuarios": usuarios,
        "usuario_actual": usuario_actual
    })
