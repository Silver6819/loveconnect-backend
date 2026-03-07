import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlalchemy
import databases

# Configuración ligera de Base de Datos
DATABASE_URL = "sqlite:///./loveconnect.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

mensajes = sqlalchemy.Table(
    "mensajes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("usuario", sqlalchemy.String(50)),
    sqlalchemy.Column("texto", sqlalchemy.String(500)),
)

engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()
    # Limpieza automática al iniciar para evitar saturación
    await database.execute(mensajes.delete())

@app.get("/leer")
async def leer():
    return await database.fetch_all(mensajes.select().order_by(mensajes.c.id.desc()).limit(10))

@app.post("/enviar")
async def enviar(usuario: str = Form(...), texto: str = Form(...)):
    await database.execute(mensajes.insert().values(usuario=usuario, texto=texto))
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
async def home():
    # Aquí pondremos el diseño en el siguiente paso
    return "Servidor activo. Esperando el diseño..."
