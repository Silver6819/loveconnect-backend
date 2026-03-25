import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases
import uvicorn

# 1. Configuración de la Base de Datos (El Elefante de Railway)
URL_ELEFANTE = "postgresql://loveconnect_db_user:o8hYijuhIHVR3id8sVOdbWa3V3jQ4GrW@dpg-d71crdn5gffc73fobmpg-a/loveconnect_db"
DATABASE_URL = os.getenv("DATABASE_URL", URL_ELEFANTE)
database = databases.Database(DATABASE_URL)

app = FastAPI()

# 2. Configuración de Rutas para Templates (Corrección de ruta absoluta)
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.on_event("startup")
async def startup():
    await database.connect()
    # Tabla simplificada para asegurar que funcione la conexión
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

# 3. RUTA CORREGIDA: Aquí estaba el error del "Internal Server Error"
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    # Asegúrate de que esta línea no tenga comas extras al final
    return templates.TemplateResponse("index.html", {"request": request})

# 4. Ruta de Registro
@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    try:
        query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
        await database.execute(query=query, values={"nombre": nombre, "email": email})
        return {"status": "success", "message": f"¡Hola {nombre}! Bienvenido a LoveConnect."}
    except Exception as e:
        # Esto te ayudará a ver qué pasa si falla el registro
        return {"status": "error", "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    # Render asigna el puerto dinámicamente
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
