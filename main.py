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

# Ajuste para PostgreSQL (Render)
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
# STARTUP (seguro)
# -------------------------

@app.on_event("startup")
def startup():
    if not engine:
        print("⚠️ No DATABASE_URL")
        return

    try:
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT,
                    email TEXT UNIQUE
                )
            """))
            conn.commit()
        print("✅ Base de datos lista")
    except Exception as e:
        print("❌ Error DB en startup:", e)

# -------------------------
# HOME
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {"mensaje": None}
    )

# -------------------------
# REGISTRO
# -------------------------

@app.post("/registro", response_class=HTMLResponse)
async def registro(request: Request, nombre: str = Form(...), email: str = Form(...)):
    mensaje = None

    if not engine:
        mensaje = "Base de datos no disponible"
    else:
        try:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"),
                    {"nombre": nombre, "email": email}
                )
                conn.commit()

            mensaje = f"¡Hola {nombre}! Guardado en la base de datos 💘"

        except Exception:
            mensaje = "Ese correo ya está registrado ⚠️"

    return templates.TemplateResponse(
        request,
        "index.html",
        {"mensaje": mensaje}
    )
