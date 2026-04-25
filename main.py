import os
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware
import base64

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="supersecreto")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = None

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
    except Exception as e:
        print("ERROR DB:", e)

templates = Jinja2Templates(directory="templates")

def render(request, template_name, context):
    if not isinstance(context, dict):
        context = dict(context)

    return templates.TemplateResponse(
        request,
        template_name,
        context
    )

def mostrar_error():
    return HTMLResponse("<h3>Error interno</h3><pre>" + traceback.format_exc() + "</pre>")

@app.on_event("startup")
def startup():
    try:
        if not engine:
            return

        with engine.connect() as conn:
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

            conn.commit()
    except:
        print(traceback.format_exc())

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        usuarios = []

        if engine:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT nombre FROM usuarios"))
                    usuarios = [{"nombre": r[0], "online": True} for r in result.fetchall()]
            except:
                print("DB ERROR HOME:", traceback.format_exc())

        return render(request, "index.html", {
            "usuarios": usuarios,
            "usuario_actual": request.session.get("usuario", "Invitado"),
            "chat_con": None,
            "mensajes": [],
            "es_premium": False
        })
    except:
        return mostrar_error()

@app.post("/set_usuario")
async def set_usuario(request: Request, usuario: str = Form(...)):
    try:
        request.session["usuario"] = usuario

        if engine:
            try:
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO usuarios (nombre)
                        VALUES (:nombre)
                        ON CONFLICT (nombre) DO NOTHING
                    """), {"nombre": usuario})
                    conn.commit()
            except:
                print("DB ERROR SET USUARIO:", traceback.format_exc())

        return RedirectResponse("/", status_code=303)
    except:
        return mostrar_error()

@app.get("/chat/{usuario}", response_class=HTMLResponse)
async def chat(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []
        usuarios = []

        if engine:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT emisor, mensaje
                        FROM mensajes
                        WHERE (emisor = :yo AND receptor = :otro)
                           OR (emisor = :otro AND receptor = :yo)
                        ORDER BY fecha ASC
                    """), {"yo": usuario_actual, "otro": usuario})

                    mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]

                    result_users = conn.execute(text("SELECT nombre FROM usuarios"))
                    usuarios = [{"nombre": r[0], "online": True} for r in result_users.fetchall()]
            except:
                print("DB ERROR CHAT:", traceback.format_exc())

        return render(request, "index.html", {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes,
            "es_premium": False
        })
    except:
        return mostrar_error()

@app.post("/mensaje")
async def enviar_mensaje(request: Request, receptor: str = Form(...), mensaje: str = Form(...)):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        if engine:
            try:
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO mensajes (emisor, receptor, mensaje)
                        VALUES (:e, :r, :m)
                    """), {"e": usuario_actual, "r": receptor, "m": mensaje})
                    conn.commit()
            except:
                print("DB ERROR MENSAJE:", traceback.format_exc())

        return {"ok": True}
    except:
        return mostrar_error()

# 🔄 AUTO REFRESH PRIVADO (HTML)
@app.get("/mensajes_privados_html/{usuario}", response_class=HTMLResponse)
async def mensajes_privados_html(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []

        if engine:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT emisor, mensaje
                        FROM mensajes
                        WHERE (emisor = :yo AND receptor = :otro)
                           OR (emisor = :otro AND receptor = :yo)
                        ORDER BY fecha ASC
                    """), {"yo": usuario_actual, "otro": usuario})

                    mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
            except:
                print("DB ERROR PRIVADO HTML:", traceback.format_exc())

        return render(request, "private_messages.html", {
            "mensajes": mensajes,
            "usuario_actual": usuario_actual
        })
    except:
        return mostrar_error()

# 🔄 AUTO REFRESH GLOBAL
@app.get("/mensajes_globales_html", response_class=HTMLResponse)
async def mensajes_globales_html(request: Request):
    try:
        mensajes = []

        if engine:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT emisor, mensaje
                        FROM mensajes
                        WHERE receptor = 'GLOBAL'
                        ORDER BY fecha ASC
                    """))

                    mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
            except:
                print("DB ERROR GLOBAL:", traceback.format_exc())

        return render(request, "global_messages.html", {
            "mensajes": mensajes
        })
    except:
        return mostrar_error()

@app.get("/mensajes_privados/{usuario}")
async def mensajes_privados(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []

        if engine:
            try:
                with engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT emisor, mensaje
                        FROM mensajes
                        WHERE (emisor = :yo AND receptor = :otro)
                           OR (emisor = :otro AND receptor = :yo)
                        ORDER BY fecha ASC
                    """), {"yo": usuario_actual, "otro": usuario})

                    mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
            except:
                print("DB ERROR PRIVADO JSON:", traceback.format_exc())

        return {"mensajes": mensajes}
    except:
        return mostrar_error()

@app.post("/enviar_foto")
async def enviar_foto(request: Request, data: dict = Body(...)):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")

        imagen = data.get("imagen")
        receptor = data.get("receptor")

        if not imagen or not receptor:
            return {"ok": False}

        imagen = imagen.split(",")[1]
        imagen_bytes = base64.b64decode(imagen)

        os.makedirs("static", exist_ok=True)

        nombre = f"foto_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        ruta = f"static/{nombre}"

        with open(ruta, "wb") as f:
            f.write(imagen_bytes)

        if engine:
            try:
                with engine.connect() as conn:
                    conn.execute(text("""
                        INSERT INTO mensajes (emisor, receptor, mensaje)
                        VALUES (:e, :r, :m)
                    """), {
                        "e": usuario_actual,
                        "r": receptor,
                        "m": f"[FOTO]{ruta}"
                    })
                    conn.commit()
            except:
                print("DB ERROR FOTO:", traceback.format_exc())

        return {"ok": True}
    except:
        return mostrar_error()

@app.post("/enviar_imagen")
async def enviar_imagen(request: Request, data: dict = Body(...)):
    try:
        return await enviar_foto(request, data)
    except:
        return mostrar_error()

# 🚪 LOGOUT (ARREGLADO)
@app.get("/logout")
async def logout(request: Request):
    try:
        request.session.clear()
        return RedirectResponse(url="/", status_code=302)
    except:
        return mostrar_error()
