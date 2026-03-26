import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases

# -------------------------
# 1. BASE DE DATOS
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

# Fix para Render (muy importante)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

database = databases.Database(DATABASE_URL)

app = FastAPI()

# -------------------------
# 2. TEMPLATES
# -------------------------

base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# -------------------------
# 3. EVENTOS
# -------------------------

@app.on_event("startup")
async def startup():
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
        print(f"Error en base de datos: {e}")


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# -------------------------
# 4. RUTA PRINCIPAL
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# -------------------------
# 5. REGISTRO
# -------------------------

@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    try:
        query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
        await database.execute(query=query, values={"nombre": nombre, "email": email})

        return {
            "status": "success",
            "message": f"¡Hola {nombre}! Bienvenido a LoveConnect."
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
