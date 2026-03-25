import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import databases
import uvicorn

# 1. Configuración de la Base de Datos
URL_ELEFANTE = "postgresql://loveconnect_db_user:o8hYijuhIHVR3id8sVOdbWa3V3jQ4GrW@dpg-d71crdn5gffc73fobmpg-a/loveconnect_db"
DATABASE_URL = os.getenv("DATABASE_URL", URL_ELEFANTE)
database = databases.Database(DATABASE_URL)

app = FastAPI()

# 2. Configuración de Rutas para Templates (Ruta absoluta segura)
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

@app.on_event("startup")
async def startup():
    print("🚀 INFO: Iniciando conexión con el elefante...")
    try:
        await database.connect()
        query = "CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, nombre TEXT, email TEXT UNIQUE)"
        await database.execute(query)
        print("✅ ÉXITO: Base de datos lista.")
    except Exception as e:
        print(f"❌ ERROR DB: {e}")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# 3. RUTA CORREGIDA (Aquí es donde estaba el error del log)
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    print("📂 INFO: Cargando index.html...")
    # Enviamos el contexto de forma explícita para evitar el error de 'tuple'
    return templates.TemplateResponse(
        name="index.html", 
        context={"request": request}
    )

# 4. Registro de usuarios
@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    try:
        query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
        await database.execute(query=query, values={"nombre": nombre, "email": email})
        return {"status": "success", "message": f"¡Hola {nombre}! Bienvenido a LoveConnect."}
    except Exception as e:
        return {"status": "error", "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
