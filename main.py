import os
import traceback
from datetime import datetime
from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware
import urllib.parse
import urllib.request
import base64  # 📷 NUEVO

app = FastAPI()

# -------------------------

# ESCRIBIENDO (typing)

# -------------------------

usuarios_escribiendo = {}

# -------------------------

# SESIONES

# -------------------------

app.add_middleware(SessionMiddleware, secret_key="supersecreto")

# -------------------------

# BASE DE DATOS

# -------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

engine = None

if DATABASE_URL:
try:
engine = create_engine(
DATABASE_URL,
connect_args={"sslmode": "require"}
)
except Exception as e:
print("ERROR DB:", e)

# -------------------------

# TEMPLATES

# -------------------------

templates = Jinja2Templates(directory="templates")
templates.env.cache = None
templates.env.auto_reload = True

def render(template_name, request, context):
return templates.TemplateResponse(request, template_name, context)

# -------------------------

# FUNCIÓN ACTIVIDAD

# -------------------------

def actualizar_actividad(usuario):
if engine:
with engine.connect() as conn:
conn.execute(text("""
UPDATE usuarios
SET ultima_actividad = NOW()
WHERE nombre = :usuario
"""), {"usuario": usuario})
conn.commit()

# -------------------------

# ERROR HANDLER

# -------------------------

def mostrar_error():
return HTMLResponse(f""" <h1>💥 ERROR DETECTADO</h1> <pre>{traceback.format_exc()}</pre>
""")

# -------------------------

# STARTUP

# -------------------------

@app.on_event("startup")
def startup():
try:
if not engine:
return

```
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nombre TEXT,
                email TEXT UNIQUE,
                ultima_actividad TIMESTAMP,
                premium BOOLEAN DEFAULT FALSE
            )
        """))

        conn.execute(text("""
            ALTER TABLE usuarios
            ADD COLUMN IF NOT EXISTS ultima_actividad TIMESTAMP;
        """))

        conn.execute(text("""
            ALTER TABLE usuarios
            ADD COLUMN IF NOT EXISTS premium BOOLEAN DEFAULT FALSE;
        """))

        conn.execute(text("""
            ALTER TABLE usuarios
            ADD COLUMN IF NOT EXISTS ultimo_mensaje_visto INTEGER DEFAULT 0;
        """))

        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mensajes (
                id SERIAL PRIMARY KEY,
                emisor TEXT,
                receptor TEXT,
                mensaje TEXT
            )
        """))

        conn.execute(text("""
            ALTER TABLE mensajes
            ADD COLUMN IF NOT EXISTS fecha TIMESTAMP DEFAULT NOW();
        """))

        conn.commit()

except:
    print("ERROR STARTUP")
```

# -------------------------

# 📷 GUARDAR FOTO (NUEVO)

# -------------------------

@app.post("/enviar_foto")
async def enviar_foto(request: Request, data: dict = Body(...)):
try:
usuario_actual = request.session.get("usuario", "Invitado")

```
    imagen_base64 = data.get("imagen")
    receptor = data.get("receptor")

    if not imagen_base64:
        return {"error": "No hay imagen"}

    imagen_base64 = imagen_base64.split(",")[1]
    imagen_bytes = base64.b64decode(imagen_base64)

    nombre_archivo = f"foto_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    ruta = f"static/{nombre_archivo}"

    os.makedirs("static", exist_ok=True)

    with open(ruta, "wb") as f:
        f.write(imagen_bytes)

    # 🔥 guardar como mensaje (tipo WhatsApp)
    if engine:
        with engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO mensajes (emisor, receptor, mensaje)
                VALUES (:emisor, :receptor, :mensaje)
            """), {
                "emisor": usuario_actual,
                "receptor": receptor,
                "mensaje": f"[FOTO]{ruta}"
            })
            conn.commit()

    return {"ok": True, "ruta": ruta}

except:
    return {"ok": False}
```

# -------------------------

# LOGIN

# -------------------------

@app.post("/set_usuario")
async def set_usuario(request: Request, usuario: str = Form(...)):
try:
request.session["usuario"] = usuario

```
    if engine:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT * FROM usuarios WHERE nombre = :usuario
            """), {"usuario": usuario}).fetchone()

            if not result:
                conn.execute(text("""
                    INSERT INTO usuarios (nombre, email, ultima_actividad)
                    VALUES (:nombre, :email, NOW())
                """), {
                    "nombre": usuario,
                    "email": f"{usuario}@temp.com"
                })
                conn.commit()

    return RedirectResponse("/", status_code=303)

except:
    return mostrar_error()
```

# -------------------------

# LOGOUT

# -------------------------

@app.get("/logout")
async def logout(request: Request):
request.session.clear()
return RedirectResponse("/", status_code=303)

# -------------------------

# FUNCIÓN USUARIOS

# -------------------------

def obtener_usuarios():
usuarios = []
if engine:
with engine.connect() as conn:
result = conn.execute(text("""
SELECT nombre,
CASE
WHEN ultima_actividad > NOW() - INTERVAL '10 seconds'
THEN true
ELSE false
END as en_linea
FROM usuarios
"""))
usuarios = [{"nombre": row[0], "online": row[1]} for row in result.fetchall()]
return usuarios

# -------------------------

# HOME

# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
try:
usuario_actual = request.session.get("usuario", "Invitado")

```
    if usuario_actual != "Invitado":
        actualizar_actividad(usuario_actual)

    usuarios = obtener_usuarios()
    es_premium = False

    return render("index.html", request, {
        "usuarios": usuarios,
        "usuario_actual": usuario_actual,
        "chat_con": None,
        "mensajes": [],
        "es_premium": es_premium
    })

except:
    return mostrar_error()
```

# (TODO lo demás queda EXACTAMENTE igual que tu código)
