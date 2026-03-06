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

# CLAVE ADMINISTRADOR FIJA
CLAVE_ADMIN = "admin123" 

# --- TABLAS DE LA COMUNIDAD ---
usuarios = sqlalchemy.Table(
    "usuarios_comunidad",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("verificado", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("estado", sqlalchemy.String, default="activo"), # activo o castigado
)

encuestas = sqlalchemy.Table(
    "mejoras_app",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("opcion", sqlalchemy.String),
    sqlalchemy.Column("votos", sqlalchemy.Integer, default=0)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    engine = sqlalchemy.create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))
    # CREAR SI NO EXISTEN (Sin borrar)
    metadata.create_all(engine)
    
    # Inicializar las 6 opciones de encuesta
    count = await database.execute("SELECT count(*) FROM mejoras_app")
    if count == 0:
        opts = ["Videollamadas", "Stickers Locales", "Filtros VIP", "Modo Oscuro", "Chat de Voz", "Juegos Gratis"]
        for o in opts:
            await database.execute(encuestas.insert().values(opcion=o, votos=0))

# --- FILTRO DE SEGURIDAD (Moderación de Silver Breaker) ---
PROHIBIDAS = ["coño", "mierda", "coger", "pendejo", "acosador", "puta", "gilipollas", "hijo de puta"]

def filtro_seguridad(texto):
    if not texto: return False
    for p in PROHIBIDAS:
        if p in texto.lower(): return True
    return False

# --- ESTILOS VISUALES ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; text-align: center; padding: 10px; color: #333; }
    .card { background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin: 20px auto; max-width: 450px; }
    .input-field { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
    .btn-registrar { background: #ff4b6e; color: white; padding: 15px; width: 100%; border: none; border-radius: 12px; font-weight: bold; font-size: 18px; cursor: pointer; margin-top: 10px; }
    .check-azul { color: #00a2ff; font-weight: bold; }
    .banner-admin { background: #fff3cd; padding: 10px; border-radius: 10px; font-size: 0.9em; margin-bottom: 15px; color: #856404; }
</style>
"""

# --- RUTAS PRINCIPALES ---

@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
    <body>
        <h2 style='color:#ff4b6e'>💖 LoveConnect</h2>
        <div class='card'>
            <h3 style='margin-top:0;'>Registro de Perfil</h3>
            <input type='text' id='n' class='input-field' placeholder='Nombre completo'>
            <input type='number' id='e' class='input-field' placeholder='Edad'>
            <input type='text' id='u' class='input-field' placeholder='Ubicación (Ej: Zacatecoluca)'>
            <textarea id='q' class='input-field' style='height:80px' placeholder='¿Quién soy?'></textarea>
            <button class='btn-registrar' onclick='enviar()'>Publicar</button>
        </div>
        <a href='/comunidad' style='color:#ff4b6e; text-decoration:none; font-weight:bold;'>Ir a la Comunidad 🌍</a>
        <script>
            async function enviar() {{
                const d = {{ nombre: document.getElementById('n').value, edad: parseInt(document.getElementById('e').value), ubicacion: document.getElementById('u').value, quien_soy: document.getElementById('q').value }};
                if(d.edad < 18) return alert("App solo para mayores de 18 años.");
                const res = await fetch('/api/reg', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(d) }});
                const r = await res.json();
                if(r.status == 'castigado') alert("⚠️ LENGUAJE NO PERMITIDO detectado. Redirigiendo a Sala de Castigo.");
                location.href = r.url;
            }}
        </script>
    </body></html>
    """

@app.get("/comunidad", response_class=HTMLResponse)
async def ver_comunidad():
    users = await database.fetch_all(usuarios.select().where(usuarios.c.estado == "activo"))
    cartas = ""
    for u in users:
        v = " <span class='check-azul'>✅</span>" if u.verificado else ""
        cartas += f"<div class='card' style='text-align:left;'><strong>{u.nombre}{v}</strong> ({u.edad}) - {u.ubicacion}<p style='color:#666;'>{u.quien_soy}</p></div>"
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>🌍 Comunidad</h1>{cartas or 'Aún no hay perfiles.'}<br><a href='/encuesta' style='color:#ff4b6e; font-weight:bold;'>🗳️ Votar por mejoras</a><br><br><a href='/'>⬅️ Volver</a></body></html>"

@app.get("/sala-castigo", response_class=HTMLResponse)
async def sala_castigo():
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div class='card' style='background:#333; color:white;'><h1>⛓️ Sala de Castigo</h1><p>Has sido aislado temporalmente por usar lenguaje inapropiado o por denuncias de acoso. Reflexiona durante 1 semana.</p></div><br><a href='/'>Volver</a></body></html>"

@app.get("/encuesta", response_class=HTMLResponse)
async def encuesta_view():
    opts = await database.fetch_all(encuestas.select())
    lista = ""
    for o in opts:
        lista += f"<div class='card'>{o.opcion}<br><a href='/api/votar/{o.id}' style='color:#ff4b6e; font-weight:bold;'>Votar este</a></div>"
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>🗳️ Mejoras del Mes</h1>{lista}<a href='/comunidad'>Regresar</a></body></html>"

# --- PANEL ADMIN (Acceso: /admin?key=admin123) ---

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(key: str = ""):
    if key != CLAVE_ADMIN: return "<h1>Acceso Denegado</h1>"
    users = await database.fetch_all(usuarios.select())
    votos = await database.fetch_all(encuestas.select().order_by(encuestas.c.votos.desc()))
    
    filas = ""
    for u in users:
        filas += f"<tr><td>{u.nombre}</td><td>{u.estado}</td><td><a href='/api/adm/v/{u.id}?key={key}'>✅ Check</a> | <a href='/api/adm/c/{u.id}?key={key}'>⛓️ Castigo</a></td></tr>"
    
    top3 = "<h3>📊 Top 3 Más Votados:</h3><ul>"
    for v in votos[:3]:
        top3 += f"<li>{v.opcion} ({v.votos} votos)</li>"
    top3 += "</ul>"

    return f"<html><body><h1>Admin: Silver Breaker</h1>{top3}<table border='1' style='width:100%'><tr><th>Usuario</th><th>Estado</th><th>Acciones</th></tr>{filas}</table></body></html>"

# --- LÓGICA DE API ---

@app.post("/api/reg")
async def api_registro(data: dict):
    est = "castigado" if filtro_seguridad(data['nombre']) or filtro_seguridad(data['quien_soy']) else "activo"
    url = "/sala-castigo" if est == "castigado" else "/comunidad"
    await database.execute(usuarios.insert().values(nombre=data['nombre'], edad=data['edad'], ubicacion=data['ubicacion'], quien_soy=data['quien_soy'], estado=est, verificado=False))
    return {"status": est, "url": url}

@app.get("/api/votar/{oid}")
async def api_votar(oid: int):
    await database.execute("UPDATE mejoras_app SET votos = votos + 1 WHERE id = :id", {"id": oid})
    return HTMLResponse("<script>alert('¡Voto contado!'); location.href='/encuesta';</script>")

@app.get("/api/adm/v/{uid}")
async def api_verif(uid: int, key: str):
    if key == CLAVE_ADMIN: await database.execute(usuarios.update().where(usuarios.c.id == uid).values(verificado=True))
    return HTMLResponse("<script>history.back();</script>")

@app.get("/api/adm/c/{uid}")
async def api_cast(uid: int, key: str):
    if key == CLAVE_ADMIN: await database.execute(usuarios.update().where(usuarios.c.id == uid).values(estado="castigado"))
    return HTMLResponse("<script>history.back();</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
