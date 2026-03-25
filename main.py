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

# 2. Configuración de Rutas para Templates
base_dir = os.path.dirname(os.path.realpath(__file__))
templates_path = os.path.join(base_dir, "templates")
templates = Jinja2Templates(directory=templates_path)

@app.on_event("startup")
async def startup():
    print("🚀 INFO: Iniciando aplicación LoveConnect...")
    try:
        print(f"🔗 INFO: Intentando conectar a la DB en: {DATABASE_URL[:20]}...")
        await database.connect()
        print("✅ ÉXITO: Base de datos conectada correctamente")

        query = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            email TEXT UNIQUE
        )
        """
        await database.execute(query)
        print("✅ ÉXITO: Tabla 'usuarios' verificada/creada")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN STARTUP: {e}")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    print("📂 INFO: Accediendo a la ruta principal (/)")
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        print(f"❌ ERROR AL CARGAR INDEX.HTML: {e}")
        return HTMLResponse(content=f"Error interno: No se encuentra el diseño. {e}", status_code=500)

@app.post("/registro")
async def registro(nombre: str = Form(...), email: str = Form(...)):
    try:
        query = "INSERT INTO usuarios(nombre, email) VALUES (:nombre, :email)"
        await database.execute(query=query, values={"nombre": nombre, "email": email})
        return {"status": "success", "message": f"¡Hola {nombre}! Registro exitoso."}
    except Exception as e:
        print(f"❌ ERROR EN REGISTRO: {e}")
        return {"status": "error", "message": f"Error: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
