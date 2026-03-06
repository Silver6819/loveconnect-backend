import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

# --- CONFIGURACIÓN ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# TABLA ACTUALIZADA
usuarios_v2 = sqlalchemy.Table(
    "usuarios_final", # Nombre nuevo para evitar conflictos
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("verificado", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("estado", sqlalchemy.String, default="activo"),
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    
    # --- LLAVE MAESTRA: REPARA LA BASE DE DATOS ---
    engine = sqlalchemy.create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))
    # Esto borra lo viejo que causa el crash y crea lo nuevo
    metadata.drop_all(engine) 
    metadata.create_all(engine)
    print("✅ Base de datos reconstruida con éxito")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #fff5f7; text-align: center; padding: 20px; }
        .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
        .btn { background: #ff4b6e; color: white; padding: 15px; border: none; border-radius: 10px; width: 100%; cursor: pointer; font-weight: bold; }
    </style>
    </head>
    <body>
        <h1 style='color:#ff4b6e'>💖 LoveConnect v2</h1>
        <div class='card'>
            <h3>¡App Reparada!</h3>
            <p>La base de datos se ha actualizado correctamente.</p>
            <button class='btn' onclick="location.href='/admin?key=admin123'">Entrar al Panel Admin</button>
        </div>
    </body>
    </html>
    """

# --- PANEL ADMIN SEGURO ---
@app.get("/admin", response_class=HTMLResponse)
async def admin(key: str = ""):
    if key != "admin123": return "<h1>Acceso Denegado</h1>"
    return "<h1>Bienvenido Silver Breaker</h1><p>La app está en línea y limpia.</p>"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
