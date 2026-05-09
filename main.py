import os
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import base64

app = FastAPI()

# 🔥 STATIC
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(SessionMiddleware, secret_key="supersecreto")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

# 🔥 DEBUG CENTRAL
def debug_log(modulo, mensaje):
    print(f"[DEBUG - {modulo}] {mensaje}")

def debug_error(modulo, e):
    print(f"[ERROR - {modulo}] {e}")
    print(traceback.format_exc())

# 🔥 CONEXIÓN REAL
engine = None

try:
    debug_log("DB", "Intentando conectar base de datos")

    if not DATABASE_URL:
        raise Exception("DATABASE_URL no existe")

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    debug_log("DB", "Base de datos conectada correctamente")
    print("✅ DB CONECTADA CORRECTAMENTE")

except Exception as e:
    print("❌ ERROR REAL DB:")
    debug_error("DB", e)
    engine = None

templates = Jinja2Templates(directory="templates")

def render(request, template_name, context):
    return templates.TemplateResponse(
        name=template_name,
        context=context,
        request=request
    )

def mostrar_error():
    return HTMLResponse(
        "<h3>Error interno</h3><pre>" + traceback.format_exc() + "</pre>"
    )

@app.on_event("startup")
def startup():
    try:
        debug_log("STARTUP", "Iniciando LoveConnect")

        if not engine:
            debug_log("STARTUP", "DB no disponible")
            return

        with engine.begin() as conn:

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS mensajes (
                    id SERIAL PRIMARY KEY,
                    emisor TEXT,
                    receptor TEXT,
                    mensaje TEXT,
                    fecha TIMESTAMP DEFAULT NOW()
                )
            """))

            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id SERIAL PRIMARY KEY,
                    nombre TEXT UNIQUE
                )
            """))

        debug_log("STARTUP", "Tablas verificadas correctamente")

    except Exception as e:
        debug_error("STARTUP", e)

@app.get("/mensajes_privados/{usuario}")
async def mensajes_privados(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        debug_log(
            "PRIVADO",
            f"{usuario_actual} cargando chat con {usuario}"
        )

        mensajes = []

        if engine:
            with engine.begin() as conn:

                if usuario == "GLOBAL":

                    result = conn.execute(text("""
                        SELECT emisor, mensaje
                        FROM mensajes
                        WHERE receptor = 'GLOBAL'
                        ORDER BY fecha ASC
                    """))

                else:

                    result = conn.execute(text("""
                        SELECT emisor, mensaje
                        FROM mensajes
                        WHERE (emisor = :yo AND receptor = :otro)
                           OR (emisor = :otro AND receptor = :yo)
                        ORDER BY fecha ASC
                    """), {
                        "yo": usuario_actual,
                        "otro": usuario
                    })

                mensajes = [
                    {
                        "emisor": r[0],
                        "mensaje": r[1]
                    }
                    for r in result.fetchall()
                ]

        debug_log(
            "PRIVADO",
            f"Mensajes encontrados: {len(mensajes)}"
        )

        return {"mensajes": mensajes}

    except Exception as e:
        debug_error("PRIVADO", e)
        return {"mensajes": [], "error": str(e)}

# 🔥 NUEVA RUTA GLOBAL FETCH
@app.get("/mensajes")
async def obtener_mensajes(request: Request):

    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        debug_log(
            "FETCH",
            f"{usuario_actual} solicitando mensajes GLOBAL"
        )

        mensajes = []

        if engine:
            with engine.begin() as conn:

                result = conn.execute(text("""
                    SELECT emisor, mensaje
                    FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY fecha ASC
                """))

                mensajes = [
                    {
                        "emisor": r[0],
                        "mensaje": r[1]
                    }
                    for r in result.fetchall()
                ]

        debug_log(
            "FETCH",
            f"Mensajes encontrados: {len(mensajes)}"
        )

        return {"mensajes": mensajes}

    except Exception as e:
        debug_error("FETCH", e)
        return {
            "mensajes": [],
            "error": str(e)
        }

@app.post("/mensaje")
async def enviar_mensaje(
    request: Request,
    receptor: str = Form(...),
    mensaje: str = Form(...)
):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        debug_log(
            "MENSAJE",
            f"{usuario_actual} -> {receptor}"
        )

        if not mensaje.strip():
            debug_log("MENSAJE", "Mensaje vacío")
            return {"ok": False}

        if not receptor:
            debug_log("MENSAJE", "Receptor vacío")
            return {"ok": False}

        receptor_final = "GLOBAL" if receptor == "GLOBAL" else receptor

        if engine:
            with engine.begin() as conn:

                conn.execute(text("""
                    INSERT INTO mensajes (emisor, receptor, mensaje)
                    VALUES (:e, :r, :m)
                """), {
                    "e": usuario_actual,
                    "r": receptor_final,
                    "m": mensaje
                })

        debug_log("MENSAJE", "Mensaje enviado correctamente")

        return {"ok": True}

    except Exception as e:
        debug_error("MENSAJE", e)
        return {"ok": False, "error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        debug_log("HOME", f"Entrando usuario: {usuario_actual}")

        mensajes = []
        usuarios = []

        if engine:
            with engine.begin() as conn:

                result = conn.execute(text("""
                    SELECT emisor, mensaje
                    FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY fecha ASC
                """))

                mensajes = [
                    {
                        "emisor": r[0],
                        "mensaje": r[1]
                    }
                    for r in result.fetchall()
                ]

                result_users = conn.execute(
                    text("SELECT nombre FROM usuarios")
                )

                usuarios = [
                    {
                        "nombre": r[0],
                        "online": True
                    }
                    for r in result_users.fetchall()
                ]

        return render(request, "index.html", {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": "GLOBAL",
            "mensajes": mensajes,
            "es_premium": False
        })

    except Exception as e:
        debug_error("HOME", e)
        return mostrar_error()

@app.get("/global", response_class=HTMLResponse)
async def global_chat(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        debug_log(
            "GLOBAL",
            f"{usuario_actual} entrando al chat global"
        )

        mensajes = []
        usuarios = []

        if engine:
            with engine.begin() as conn:

                result = conn.execute(text("""
                    SELECT emisor, mensaje
                    FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY fecha ASC
                """))

                mensajes = [
                    {
                        "emisor": r[0],
                        "mensaje": r[1]
                    }
                    for r in result.fetchall()
                ]

                result_users = conn.execute(
                    text("SELECT nombre FROM usuarios")
                )

                usuarios = [
                    {
                        "nombre": r[0],
                        "online": True
                    }
                    for r in result_users.fetchall()
                ]

        debug_log(
            "GLOBAL",
            f"Mensajes globales: {len(mensajes)}"
        )

        return render(request, "index.html", {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": "GLOBAL",
            "mensajes": mensajes,
            "es_premium": False
        })

    except Exception as e:
        debug_error("GLOBAL", e)
        return mostrar_error()

@app.post("/enviar_foto")
async def enviar_foto(request: Request, data: dict = Body(...)):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        debug_log(
            "IMAGEN",
            f"{usuario_actual} enviando imagen"
        )

        imagen = data.get("imagen")
        receptor = data.get("receptor")

        if not imagen or not receptor:
            debug_log("IMAGEN", "Datos incompletos")
            return {"ok": False}

        imagen = imagen.split(",")[1]
        imagen_bytes = base64.b64decode(imagen)

        nombre = f"foto_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta = f"static/{nombre}"

        with open(ruta, "wb") as f:
            f.write(imagen_bytes)

        debug_log(
            "IMAGEN",
            f"Imagen guardada: {ruta}"
        )

        if engine:
            with engine.begin() as conn:

                conn.execute(text("""
                    INSERT INTO mensajes (emisor, receptor, mensaje)
                    VALUES (:e, :r, :m)
                """), {
                    "e": usuario_actual,
                    "r": receptor,
                    "m": f"[FOTO]{ruta}"
                })

        debug_log("IMAGEN", "Imagen enviada correctamente")

        return {"ok": True}

    except Exception as e:
        debug_error("IMAGEN", e)
        return mostrar_error()

@app.post("/enviar_imagen")
async def enviar_imagen(request: Request, data: dict = Body(...)):
    return await enviar_foto(request, data)

@app.get("/logout")
async def logout(request: Request):
    try:
        debug_log("LOGIN", "Cierre de sesión")

        request.session.clear()

        return RedirectResponse(
            url="/",
            status_code=303
        )

    except Exception as e:
        debug_error("LOGIN", e)
        return mostrar_error()

@app.get("/test")
async def test():
    debug_log("TEST", "Ruta test funcionando")
    return {"ok": True}

@app.post("/set_usuario")
async def set_usuario(request: Request, usuario: str = Form(...)):
    try:

        debug_log("LOGIN", f"Usuario entrando: {usuario}")

        request.session["usuario"] = usuario

        if engine:
            with engine.begin() as conn:

                conn.execute(text("""
                    INSERT INTO usuarios (nombre)
                    VALUES (:n)
                    ON CONFLICT (nombre) DO NOTHING
                """), {
                    "n": usuario
                })

        return RedirectResponse(
            url="/global",
            status_code=303
        )

    except Exception as e:
        debug_error("LOGIN", e)
        return mostrar_error()
