import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases

app = FastAPI()

# -------------------------
# BASE DE DATOS
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and (
    DATABASE_URL.startswith("postgres://") or
    DATABASE_URL.startswith("postgresql://")
):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://") \
                               .replace("postgresql://", "postgresql+asyncpg://")

database = databases.Database(DATABASE_URL) if DATABASE_URL else None

# -------------------------
# TEMPLATES
# -------------------------

base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# -------------------------
# EVENTOS
# -------------------------

@app.on_event("startup")
async def startup():
    if database:
        try:
            await database.connect()

            query = """
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                email TEXT UNIQUE
            )
            """
            await database.execute(query)

        except Exception as e:
            print("Error DB:", e)

@app.on_event("shutdown")
async def shutdown():
    if database:
        await database.disconnect()

# -------------------------
# HOME
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------
# REGISTRO
# -------------------------

@app.post("/registro", response_class=HTMLResponse)
async def registro(request: Request, nombre: str = Form(...), email: str = Form(...)):
    mensaje = ""

    if not database:
        mensaje = "Base de datos no disponible"
    else:
        try:
            query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
            await database.execute(query=query, values={"nombre": nombre, "email": email})
            mensaje = f"¡Hola {nombre}! Guardado en la base de datos 💘"
        except Exception:
            mensaje = "Ese correo ya está registrado ⚠️"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "mensaje": mensaje
    })
