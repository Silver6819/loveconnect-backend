import os
import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, Column, String, Integer, create_engine
from databases import Database

# 1. Configuración de Variables de Entorno y Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)

# 2. Definición de la Tabla 'users'
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(50), unique=True),
    Column("password", String(50)),
)

# 3. Inicialización de FastAPI
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 4. Eventos de Conexión Segura (Sugerido por ChatGPT)
@app.on_event("startup")
async def startup():
    # Conecta a la DB asíncrona
    await database.connect()
    # Crea las tablas físicamente en el elefante de Render
    metadata.create_all(engine)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# 5. Rutas de la Aplicación
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/signup")
async def signup(username: str = Form(...), password: str = Form(...)):
    try:
        query = users.insert().values(username=username, password=password)
        await database.execute(query)
        # 303 es el código correcto para redirección tras un POST
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return f"Error en el registro: {str(e)}"

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        query = users.select().where(users.c.username == username, users.c.password == password)
        user = await database.fetch_one(query)
        if user:
            return f"¡Bienvenido a LoveConnect, {username}!"
        return "Usuario o contraseña incorrectos."
    except Exception as e:
        return f"Error en el servidor: {str(e)}"

# 6. Configuración de Puerto para Render
if __name__ == "__main__":
    # Render asigna un puerto dinámico, usualmente el 10000
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
