import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases
import uvicorn

# 1. Configuración de la Base de Datos (Conexión al "elefante")
URL_ELEFANTE = "postgresql://loveconnect_db_user:o8hYijuhIHVR3id8sVOdbWa3V3jQ4GrW@dpg-d71crdn5gffc73fobmpg-a/loveconnect_db"
DATABASE_URL = os.getenv("DATABASE_URL", URL_ELEFANTE)
database = databases.Database(DATABASE_URL)

app = FastAPI()

# 2. Configuración de Templates (Ruta absoluta para Render)
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.on_event("startup")
async def startup():
    try:
        await database.connect()
        # Creamos la tabla si no existe
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

# 3. RUTA CORREGIDA: Eliminamos el error de "tuple"
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    # Definimos el diccionario de datos claramente
    datos_para_la_web = {"request": request}
    
    # Usamos nombres de argumentos explícitos para evitar errores internos
    return templates.TemplateResponse(
        name="index.html", 
        context=datos_para_la_web
    )

# 4. Ruta de Registro
@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    try:
        query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
        await database.execute(query=query, values={"nombre": nombre, "email": email})
        return {"status": "success", "message": f"¡Hola {nombre}! Bienvenido a LoveConnect."}
    except Exception as e:
        return {"
