import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases
import uvicorn

# 1. Dirección del elefante (directa para evitar errores de NoneType)
URL_ELEFANTE = "postgresql://loveconnect_db_user:o8hYijuhIHVR3id8sVOdbWa3V3jQ4GrW@dpg-d71crdn5gffc73fobmpg-a/loveconnect_db"
DATABASE_URL = os.getenv("DATABASE_URL", URL_ELEFANTE)

database = databases.Database(DATABASE_URL)
app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    await database.connect()
    # Creamos la tabla con la columna 'es_premium' lista para el futuro
    query = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        email TEXT UNIQUE,
        es_premium BOOLEAN DEFAULT FALSE
    )
    """
    await database.execute(query)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    # Esto cargará tu index.html original
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    try:
        query = "INSERT INTO usuarios(nombre, email, es_premium) VALUES (:nombre, :email, :premium)"
        await database.execute(query=query, values={"nombre": nombre, "email": email, "premium": False})
        return {"status": "success", "message": f"¡Hola {nombre}! Ya eres parte de LoveConnect."}
    except Exception as e:
        return {"status": "error", "message": "El correo ya existe o hubo un problema."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
