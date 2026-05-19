import os
import traceback
from datetime import datetime, date
from fastapi import FastAPI, Request, Form, Body
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, text
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import base64
import re
import uuid
from urllib.parse import unquote

app = FastAPI()

# ========== CONFIGURACIÓN INICIAL ==========
os.makedirs("static", exist_ok=True)
os.makedirs("static/perfiles", exist_ok=True)  # para fotos de perfil
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

# ========== INICIO: CREAR TABLAS Y COLUMNAS ==========
@app.on_event("startup")
def startup():
    if not engine:
        print("⚠️ Startup: No hay conexión a DB, no se crearán tablas.")
        return
    try:
        with engine.begin() as conn:
            # Tablas principales
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
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS likes (
                    id SERIAL PRIMARY KEY,
                    usuario_emisor TEXT,
                    usuario_receptor TEXT,
                    fecha TIMESTAMP DEFAULT NOW(),
                    UNIQUE(usuario_emisor, usuario_receptor)
                )
            """))
            
            # Añadir columnas a usuarios (si no existen)
            for col in ["fecha_nacimiento DATE", "foto_perfil TEXT", "genero TEXT", "plan TEXT DEFAULT 'basico'", "premium_hasta TIMESTAMP"]:
                try:
                    conn.execute(text(f"ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS {col}"))
                except Exception as e:
                    print(f"Nota: columna {col} puede que ya exista - {e}")
        
        print("✅ Tablas y columnas verificadas/creadas.")
    except Exception as e:
        debug_error("STARTUP", e)

# ========== ENDPOINTS PRINCIPALES ==========

@app.get("/mensajes_privados/{usuario}")
async def mensajes_privados(request: Request, usuario: str):
    if not engine:
        return {"mensajes": [], "error": "Base de datos no conectada"}
    try:
        usuario = unquote(usuario)
        usuario_actual = request.session.get("usuario", "Invitado")
        
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
        
        return {"ok": True}
    except Exception as e:
        debug_error("MENSAJE", e)
        return {"ok": False, "error": str(e)}

# ========== CHAT GLOBAL Y PRIVADO ==========
@app.get("/global", response_class=HTMLResponse)
async def chat_global(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []
        usuarios = []
        
        if engine:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT emisor, mensaje FROM mensajes WHERE receptor = 'GLOBAL' ORDER BY fecha ASC"))
                mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
                result_users = conn.execute(text("SELECT nombre, foto_perfil, fecha_nacimiento FROM usuarios"))
                usuarios = []
                for r in result_users.fetchall():
                    edad = None
                    if r[2]:
                        try:
                            hoy = date.today()
                            nac = r[2]
                            edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                        except:
                            pass
                    usuarios.append({
                        "nombre": r[0],
                        "foto_perfil": r[1],
                        "edad": edad
                    })
        
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

@app.get("/chat/{usuario}", response_class=HTMLResponse)
async def chat_privado(request: Request, usuario: str):
    usuario = unquote(usuario)
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []
        usuarios = []
        
        if engine:
            with engine.begin() as conn:
                result = conn.execute(text("""
                    SELECT emisor, mensaje FROM mensajes
                    WHERE (emisor = :yo AND receptor = :otro) 
                       OR (emisor = :otro AND receptor = :yo)
                    ORDER BY fecha ASC
                """), {"yo": usuario_actual, "otro": usuario})
                mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
                result_users = conn.execute(text("SELECT nombre, foto_perfil, fecha_nacimiento FROM usuarios"))
                usuarios = []
                for r in result_users.fetchall():
                    edad = None
                    if r[2]:
                        try:
                            hoy = date.today()
                            nac = r[2]
                            edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                        except:
                            pass
                    usuarios.append({
                        "nombre": r[0],
                        "foto_perfil": r[1],
                        "edad": edad
                    })
        
        return render(request, "index.html", {
            "usuarios": usuarios,
            "usuario_actual": usuario_actual,
            "chat_con": usuario,
            "mensajes": mensajes,
            "es_premium": False
        })
    except Exception as e:
        debug_error("CHAT_PRIVADO", e)
        return mostrar_error()

# ========== PERFIL DE USUARIO ==========
@app.get("/mi_perfil")
async def mi_perfil(request: Request):
    usuario_actual = request.session.get("usuario", "Invitado")
    if not engine:
        return {"error": "DB no conectada"}
    with engine.begin() as conn:
        result = conn.execute(text("SELECT nombre, fecha_nacimiento, foto_perfil, genero, plan, premium_hasta FROM usuarios WHERE nombre = :n"), {"n": usuario_actual})
        user = result.fetchone()
    if not user:
        return {"error": "Usuario no encontrado"}
    return {
        "nombre": user[0],
        "fecha_nacimiento": str(user[1]) if user[1] else None,
        "foto_perfil": user[2],
        "genero": user[3],
        "plan": user[4],
        "premium_hasta": str(user[5]) if user[5] else None
    }

@app.post("/actualizar_perfil")
async def actualizar_perfil(request: Request, fecha_nacimiento: str = Form(None), genero: str = Form(None), foto_perfil: str = Form(None)):
    usuario_actual = request.session.get("usuario", "Invitado")
    if not engine:
        return {"ok": False, "error": "DB no conectada"}
    
    foto_ruta = None
    if foto_perfil and foto_perfil.startswith("data:image"):
        try:
            formato = foto_perfil.split(";")[0].split("/")[-1]
            data = foto_perfil.split(",")[1]
            img_bytes = base64.b64decode(data)
            nombre_archivo = f"perfil_{usuario_actual}_{uuid.uuid4().hex}.{formato}"
            ruta = f"static/perfiles/{nombre_archivo}"
            os.makedirs("static/perfiles", exist_ok=True)
            with open(ruta, "wb") as f:
                f.write(img_bytes)
            foto_ruta = f"/{ruta}"
        except Exception as e:
            debug_error("FOTO_PERFIL", e)
    
    with engine.begin() as conn:
        if foto_ruta:
            conn.execute(text("UPDATE usuarios SET foto_perfil = :foto WHERE nombre = :n"), {"foto": foto_ruta, "n": usuario_actual})
        if fecha_nacimiento:
            conn.execute(text("UPDATE usuarios SET fecha_nacimiento = :fecha WHERE nombre = :n"), {"fecha": fecha_nacimiento, "n": usuario_actual})
        if genero:
            conn.execute(text("UPDATE usuarios SET genero = :g WHERE nombre = :n"), {"g": genero, "n": usuario_actual})
    return {"ok": True}

@app.get("/perfil", response_class=HTMLResponse)
async def perfil_form(request: Request):
    usuario_actual = request.session.get("usuario", "Invitado")
    return templates.TemplateResponse("perfil.html", {"request": request, "usuario_actual": usuario_actual})

# ========== LIKES Y MATCHES ==========
@app.post("/dar_like")
async def dar_like(request: Request, data: dict = Body(...)):
    if not engine:
        return {"ok": False, "error": "DB no conectada"}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        receptor = data.get("receptor")
        if not receptor or receptor == usuario_actual:
            return {"ok": False, "error": "No puedes darte like a ti mismo"}
        
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO likes (usuario_emisor, usuario_receptor)
                VALUES (:e, :r) ON CONFLICT DO NOTHING
            """), {"e": usuario_actual, "r": receptor})
            
            result = conn.execute(text("""
                SELECT 1 FROM likes
                WHERE usuario_emisor = :r AND usuario_receptor = :e
            """), {"e": usuario_actual, "r": receptor})
            match = result.fetchone() is not None
        
        return {"ok": True, "match": match}
    except Exception as e:
        debug_error("DAR_LIKE", e)
        return {"ok": False, "error": str(e)}

@app.get("/mis_matches")
async def mis_matches(request: Request):
    if not engine:
        return {"matches": []}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT DISTINCT l1.usuario_receptor AS match_user
                FROM likes l1
                JOIN likes l2 ON l1.usuario_receptor = l2.usuario_emisor 
                             AND l1.usuario_emisor = l2.usuario_receptor
                WHERE l1.usuario_emisor = :usuario
            """), {"usuario": usuario_actual})
            matches = [r[0] for r in result.fetchall()]
        return {"matches": matches}
    except Exception as e:
        debug_error("MIS_MATCHES", e)
        return {"matches": []}

@app.get("/mis_likes_dados")
async def mis_likes_dados(request: Request):
    if not engine:
        return {"likes": []}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        with engine.begin() as conn:
            result = conn.execute(text("""
                SELECT usuario_receptor FROM likes
                WHERE usuario_emisor = :usuario
            """), {"usuario": usuario_actual})
            likes = [r[0] for r in result.fetchall()]
        return {"likes": likes}
    except Exception as e:
        debug_error("MIS_LIKES", e)
        return {"likes": []}

# ========== MIS CHATS DIRECTOS ==========
@app.get("/mis_chats")
async def mis_chats(request: Request):
    if not engine:
        return {"chats": []}
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        
        with engine.begin() as conn:
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

# ========== IMÁGENES EN CHAT ==========
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
        
        return {"ok": True}
    except Exception as e:
        debug_error("IMAGEN", e)
        return {"ok": False, "error": str(e)}

@app.post("/enviar_imagen")
async def enviar_imagen(request: Request, data: dict = Body(...)):
    return await enviar_foto(request, data)

# ========== LOGOUT Y SET USUARIO ==========
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/")
async def home(request: Request):
    try:
        usuario_actual = request.session.get("usuario", "Invitado")
        mensajes = []
        usuarios = []
        
        if engine:
            with engine.begin() as conn:
                result = conn.execute(text("SELECT emisor, mensaje FROM mensajes WHERE receptor = 'GLOBAL' ORDER BY fecha ASC"))
                mensajes = [{"emisor": r[0], "mensaje": r[1]} for r in result.fetchall()]
                result_users = conn.execute(text("SELECT nombre, foto_perfil, fecha_nacimiento FROM usuarios"))
                usuarios = []
                for r in result_users.fetchall():
                    edad = None
                    if r[2]:
                        try:
                            hoy = date.today()
                            nac = r[2]
                            edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                        except:
                            pass
                    usuarios.append({
                        "nombre": r[0],
                        "foto_perfil": r[1],
                        "edad": edad
                    })
        
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
