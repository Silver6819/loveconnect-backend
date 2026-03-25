import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import databases
import uvicorn

# Configuración de la Base de Datos
DATABASE_URL = os.getenv("DATABASE_URL")
database = databases.Database(DATABASE_URL)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    await database.connect()
    # Creamos la tabla si no existe (Solo Nombre y Email)
    query = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        email TEXT UNIQUE
    )
    """
    await database.execute(query)

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
    await database.execute(query=query, values={"nombre": nombre, "email": email})
    return {"message": f"¡Hola {nombre}! Te has registrado con éxito en LoveConnect."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
