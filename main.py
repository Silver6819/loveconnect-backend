import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

# 1. Configuración de la Base de Datos Real
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Si no hay DB configurada, usaremos una local de prueba para que no explote
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./test.db"

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Definición de la tabla de usuarios
usuarios_tabla = sqlalchemy.Table(
    "usuarios_loveconnect",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("usuario", sqlalchemy.String, unique=True),
    sqlalchemy.Column("clave", sqlalchemy.String),
    sqlalchemy.Column("ubicacion", sqlalchemy.String, default="Zacatecoluca")
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="silver_breaker_prod_2026")

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# --- RUTAS LÓGICAS ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = request.session.get("u")
    if not user: return RedirectResponse("/login", status_code=303)
    return f"<html><body><h1>LoveConnect: Base de Datos Conectada</h1><p>Hola, {user}</p><a href='/logout'>Salir</a></body></html>"

@app.get("/login", response_class=HTMLResponse)
async def login_p():
    return """
    <html><body><h2>Ingresar</h2>
    <form action="/login" method="post">
        <input name="u" placeholder="Usuario" required><br>
        <input name="p" type="password" placeholder="Clave" required><br>
        <button type="submit">Entrar</button>
    </form>
    <p><a href="/signup">Registrarse</a></p></body></html>
    """

@app.post("/login")
async def login_logic(request: Request, u: str = Form(...), p: str = Form(...)):
    u_clean = u.lower().strip()
    query = usuarios_tabla.select().where(usuarios_tabla.c.usuario == u_clean)
    user_db = await database.fetch_one(query)
    
    if user_db and user_db["clave"] == p:
        request.session["u"] = u
        return RedirectResponse("/", status_code=303)
    return "Error: Datos incorrectos. <a href='/login'>Volver</a>"

@app.get("/signup", response_class=HTMLResponse)
async def signup_p():
    return """
    <html><body><h2>Registro Real (SQL)</h2>
    <form action="/signup" method="post">
        <input name="u" placeholder="Tu Usuario" required><br>
        <input name="p" type="password" placeholder="Tu Clave" required><br>
        <button type="submit">Crear Cuenta Permanente</button>
    </form></body></html>
    """

@app.post("/signup")
async def signup_logic(u: str = Form(...), p: str = Form(...)):
    u_clean = u.lower().strip()
    try:
        query = usuarios_tabla.insert().values(usuario=u_clean, clave=p)
        await database.execute(query)
        return RedirectResponse("/login", status_code=303)
    except Exception as e:
        return f"Error: El usuario ya existe o hubo un problema. <a href='/signup'>Volver</a>"

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
