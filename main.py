import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases
import uvicorn

# Render usa a veces DATABASE_URL o a veces te da una interna.
# Esta línea intenta agarrar la de Render primero.
DATABASE_URL = os.environ.get("DATABASE_URL")

database = databases.Database(DATABASE_URL)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def startup():
    if not database.is_connected:
        await database.connect()
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
    if database.is_connected:
        await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
    await database.execute(query=query, values={"nombre": nombre, "email": email})
    return {"status": "success", "message": f"¡Hola {nombre}! Registro completado."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
