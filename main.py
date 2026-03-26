import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases

# -------------------------
# 1. BASE DE DATOS
# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("⚠️ DATABASE_URL no configurada")

# Corrección para asyncpg (MUY IMPORTANTE)
if DATABASE_URL and (
    DATABASE_URL.startswith("postgres://") or
    DATABASE_URL.startswith("postgresql://")
):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://") \
                               .replace("postgresql://", "postgresql+asyncpg://")

database = databases.Database(DATABASE_URL) if DATABASE_URL else None

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

            print("✅ Base de datos conectada correctamente")

        except Exception as e:
            print(f"❌ Error en DB (la app sigue funcionando): {e}")
    else:
        print("⚠️ No hay conexión a base de datos")

@app.on_event("shutdown")
async def shutdown():
    if database:
        await database.disconnect()

# -------------------------
# 4. HOME
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )
    except Exception as e:
        return HTMLResponse(f"<h1>Error cargando HTML: {e}</h1>")

# -------------------------
# 5. REGISTRO
# -------------------------

@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    if not database:
        return {"status": "error", "message": "Base de datos no disponible"}

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
