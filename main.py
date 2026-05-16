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
import re

app = FastAPI()

# ========== CONFIGURACIÓN INICIAL ==========
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="supersecreto", https_only=False)

# ========== VARIABLE DE ENTORNO DATABASE_URL ==========
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    if re.search(r'@[^:]+:\d+/', DATABASE_URL) is None:
        DATABASE_URL = re.sub(r'@([^/]+)/', r'@\1:5432/', DATABASE_URL)
    
    if "sslmode" not in DATABASE_URL:
        if "?" in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
        else:
            DATABASE_URL += "?sslmode=require"

print(f"🔗 DATABASE_URL configurada")
if DATABASE_URL:
    masked = re.sub(r':[^@]+@', ':****@', DATABASE_URL)
    print(f"   → {masked}")

# ========== LOGGERS ==========
def debug_log(modulo, mensaje):
    print(f"[DEBUG - {modulo}] {mensaje}")

def debug_error(modulo, e):
    print(f"[ERROR - {modulo}] {e}")
    print(traceback.format_exc())

# ========== CONEXIÓN A LA BASE DE DATOS ==========
engine = None

if not DATABASE_URL:
    print("❌ CRÍTICO: Variable DATABASE_URL no definida en el entorno.")
else:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Base de datos PostgreSQL conectada correctamente (SSL activo)")
    except Exception as e:
        print("❌ ERROR FATAL conectando a la base de datos:")
        debug_error("DB_INIT", e)

# ========== TEMPLATES ==========
templates = Jinja2Templates(directory="templates")

def render(request, template_name, context):
    return templates.TemplateResponse(name=template_name, context=context, request=request)

def mostrar_error(mensaje="Error interno del servidor"):
    return HTMLResponse(f"<h3>{mensaje}</h3><pre>{traceback.format_exc()}</pre>")

# ========== INICIO: CREAR TABLAS ==========
@app.on_event("startup")
def startup():
    if not engine:
        print("⚠️ Startup: No hay conexión a DB, no se crearán tablas.")
        return
    try:
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
        print("✅ Tablas 'mensajes' y 'usuarios' verificadas/creadas.")
    except Exception as e:
        debug_error("STARTUP", e)

# ========== ENDPOINTS PRINCIPALES ==========

@app.get("/mensajes_privados/{usuario}")
async def mensajes_privados(request: Request, usuario: str):
    if not engine:
        return {"mensajes": [], "error": "Base de datos no conectada"}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        debug_log("PRIVADO", f"{usuario_actual} -> {usuario}")
        
        with engine.begin() as conn:
            if usuario == "GLOBAL":
                result = conn.execute(text("""
                    SELECT emisor, mensaje, fecha FROM mensajes
                    WHERE receptor = 'GLOBAL'
                    ORDER BY fecha ASC
                """))
            else:
                result = conn.execute(text("""
                    SELECT emisor, mensaje, fecha FROM mensajes
                    WHERE (emisor = :yo AND receptor = :otro)
                       OR (emisor = :otro AND receptor = :yo)
                    ORDER BY fecha ASC
                """), {"yo": usuario_actual, "otro": usuario})
            
            mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
        
        debug_log("PRIVADO", f"Devueltos {len(mensajes)} mensajes")
        return {"mensajes": mensajes}
    except Exception as e:
        debug_error("PRIVADO", e)
        return {"mensajes": [], "error": str(e)}

@app.get("/mensajes")
async def obtener_mensajes_global(request: Request):
    if not engine:
        return {"mensajes": [], "error": "DB no conectada"}
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT emisor, mensaje FROM mensajes
                WHERE receptor = 'GLOBAL'
                ORDER BY fecha ASC
            """))
            mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
        return {"mensajes": mensajes}
    except Exception as e:
        debug_error("FETCH_GLOBAL", e)
        return {"mensajes": [], "error": str(e)}

@app.post("/mensaje")
async def enviar_mensaje(
    request: Request,
    receptor: str = Form(...),
    mensaje: str = Form(...)
):
    if not engine:
        debug_log("MENSAJE", "DB no conectada - mensaje rechazado")
        return {"ok": False, "error": "Base de datos no disponible"}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        if not mensaje.strip():
            return {"ok": False, "error": "Mensaje vacío"}
        
        receptor_final = "GLOBAL" if receptor == "GLOBAL" else receptor
        
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO mensajes (emisor, receptor, mensaje)
                VALUES (:e, :r, :m)
            """), {"e": usuario_actual, "r": receptor_final, "m": mensaje})
        
        debug_log("MENSAJE", f"{usuario_actual} -> {receptor_final}: {mensaje[:30]}")
        return {"ok": True}
    except Exception as e:
        debug_error("MENSAJE", e)
        return {"ok": False, "error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []
        usuarios = []
        
        if engine:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT emisor, mensaje FROM mensajes WHERE receptor = 'GLOBAL' ORDER BY fecha ASC"))
                mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
                result_users = conn.execute(text("SELECT nombre FROM usuarios"))
                usuarios = [{"nombre": r[0], "online": True} for r in result_users.fetchall()]
        
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
@app.get("/chat/{usuario}", response_class=HTMLResponse)
async def chat_privado_o_global(request: Request, usuario: str):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []
        usuarios = []
        
        if engine:
            with engine.begin() as conn:
                if usuario == "GLOBAL":
                    result = conn.execute(text("SELECT emisor, mensaje FROM mensajes WHERE receptor = 'GLOBAL' ORDER BY fecha ASC"))
                else:
                    result = conn.execute(text("""
                        SELECT emisor, mensaje FROM mensajes
                        WHERE (emisor = :yo AND receptor = :otro) 
                           OR (emisor = :otro AND receptor = :yo)
                        ORDER BY fecha ASC
                    """), {"yo": usuario_actual, "otro": usuario})
                
                mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
                result_users = conn.execute(text("SELECT nombre FROM usuarios"))
                usuarios = [{"nombre": r[0], "online": True} for r in result_users.fetchall()]
        
        return render(request, "index.html", {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes,
            "es_premium": False
        })
    except Exception as e:
        debug_error("CHAT", e)
        return mostrar_error()

# ========== NUEVO ENDPOINT: MIS CHATS DIRECTOS ==========
@app.get("/mis_chats")
async def mis_chats(request: Request):
    if not engine:
        return {"chats": []}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        
        with engine.begin() as conn:
            # Obtener usuarios con los que ha habido conversación (excluyendo GLOBAL)
            result = conn.execute(text("""
                SELECT DISTINCT 
                    CASE 
                        WHEN emisor = :usuario THEN receptor
                        ELSE emisor
                    END as otro_usuario,
                    (SELECT mensaje FROM mensajes m2 
                     WHERE ((m2.emisor = :usuario AND m2.receptor = otro_usuario)
                        OR (m2.emisor = otro_usuario AND m2.receptor = :usuario))
                        AND m2.receptor != 'GLOBAL'
                     ORDER BY m2.fecha DESC LIMIT 1) as ultimo_mensaje
                FROM mensajes
                WHERE (emisor = :usuario OR receptor = :usuario)
                    AND receptor != 'GLOBAL'
                ORDER BY fecha DESC
            """), {"usuario": usuario_actual})
            
            chats = []
            for r in result.fetchall():
                if r[0] and r[0] != "GLOBAL" and r[0] != usuario_actual:
                    ultimo = r[1] if r[1] else ""
                    if len(ultimo) > 50:
                        ultimo = ultimo[:50] + "..."
                    chats.append({
                        "usuario": r[0],
                        "ultimo_mensaje": ultimo
                    })
            
        return {"chats": chats}
    except Exception as e:
        debug_error("MIS_CHATS", e)
        return {"chats": []}

@app.post("/enviar_foto")
async def enviar_foto(request: Request, data: dict = Body(...)):
    if not engine:
        return {"ok": False, "error": "DB no conectada"}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        imagen = data.get("imagen")
        receptor = data.get("receptor")
        
        if not imagen or not receptor:
            return {"ok": False, "error": "Datos incompletos"}
        
        if "," in imagen:
            imagen = imagen.split(",")[1]
        
        imagen_bytes = base64.b64decode(imagen)
        nombre = f"foto_{datetime.now().strftime('%Y%m%d%H%M%S')}_{usuario_actual}.png"
        ruta = f"static/{nombre}"
        
        with open(ruta, "wb") as f:
            f.write(imagen_bytes)
        
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO mensajes (emisor, receptor, mensaje)
                VALUES (:e, :r, :m)
            """), {"e": usuario_actual, "r": receptor, "m": f"[FOTO]{ruta}"})
        
        debug_log("IMAGEN", f"Imagen guardada: {ruta}")
        return {"ok": True}
    except Exception as e:
        debug_error("IMAGEN", e)
        return {"ok": False, "error": str(e)}

@app.post("/enviar_imagen")
async def enviar_imagen(request: Request, data: dict = Body(...)):
    return await enviar_foto(request, data)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/test")
async def test():
    return {"ok": True, "db_connected": engine is not None}

@app.post("/set_usuario")
async def set_usuario(request: Request, usuario: str = Form(...)):
    try:
        request.session["usuario"] = usuario
        if engine:
            with engine.begin() as conn:
                conn.execute(text("INSERT INTO usuarios (nombre) VALUES (:n) ON CONFLICT (nombre) DO NOTHING"), {"n": usuario})
        return RedirectResponse(url="/global", status_code=303)
    except Exception as e:
        debug_error("LOGIN", e)
        return mostrar_error()

# ========== FIN ==========
