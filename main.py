import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime

# --- CONFIGURACIÓN FIJA ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# CLAVE DE ADMINISTRADOR FIJA
CLAVE_ADMIN = "admin123" 

# --- TABLAS ---
usuarios = sqlalchemy.Table(
    "usuarios_v2",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("verificado", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("estado", sqlalchemy.String, default="activo"), # activo, castigado, baneado
)

encuestas = sqlalchemy.Table(
    "encuestas",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("opcion", sqlalchemy.String),
    sqlalchemy.Column("votos", sqlalchemy.Integer, default=0)
)

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    # Crear opciones de encuesta si la tabla está vacía
    query_check = "SELECT count(*) FROM encuestas"
    count = await database.execute(query_check)
    if count == 0:
        opciones = ["Videollamadas", "Stickers VIP", "Filtros Locales", "Modo Oscuro", "Chat de Voz", "Juegos de Pareja"]
        for opt in opciones:
            await database.execute(encuestas.insert().values(opcion=opt, votos=0))

# --- FILTRO DE SEGURIDAD (España y Latam) ---
PALABRAS_PROHIBIDAS = ["coño", "mierda", "coger", "pendejo", "acosador", "puta", "gilipollas"]

def hay_insulto(texto):
    if not texto: return False
    for p in PALABRAS_PROHIBIDAS:
        if p in texto.lower(): return True
    return False

# --- ESTILOS VISUALES ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; text-align: center; padding: 15px; }
    .card { background: white; border-radius: 20px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin: 15px auto; max-width: 450px; }
    .btn { padding: 12px 25px; border-radius: 12px; border: none; cursor: pointer; font-weight: bold; text-decoration: none; display: inline-block; transition: 0.3s; }
    .btn-reg { background: #ff4b6e; color: white; width: 100%; }
    .btn-admin { background: #00a2ff; color: white; font-size: 0.8em; margin: 2px; }
    .check-azul { color: #00a2ff; font-weight: bold; }
    .sala-castigo { background: #333; color: #ffcc00; padding: 20px; border-radius: 20px; }
    .banner-update { background: #fff3cd; color: #856404; padding: 10px; border: 1px solid #ffeeba; margin-bottom: 20px; font-weight: bold; border-radius: 10px; }
</style>
"""

# --- RUTAS DE LA APP ---

@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">{ESTILOS}</head>
    <body>
        <h1 style='color:#ff4b6e'>💖 LoveConnect</h1>
        <div class='card'>
            <h3>Registro Seguro (18+)</h3>
            <input type='text' id='n' placeholder='Tu nombre' style='width:100%; padding:10px; margin:5px 0;'><br>
            <input type='number' id='e' placeholder='Edad' style='width:100%; padding:10px; margin:5px 0;'><br>
            <textarea id='q' placeholder='Tu descripción...' style='width:100%; padding:10px; margin:5px 0; height:80px;'></textarea><br>
            <button class='btn btn-reg' onclick='registrar()'>Unirse a la Comunidad</button>
        </div>
        <a href='/comunidad' style='color:#ff4b6e; font-weight:bold; text-decoration:none;'>Ver quién está cerca 🌍</a>
        <script>
            async function registrar() {{
                const d = {{ nombre: document.getElementById('n').value, edad: parseInt(document.getElementById('e').value), quien_soy: document.getElementById('q').value }};
                if(!d.nombre || !d.edad) return alert("Completa los datos");
                if(d.edad < 18) return alert("Solo para mayores de edad.");
                const res = await fetch('/api/registrar', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(d) }});
                const r = await res.json();
                if(r.status == 'castigado') alert("⚠️ LENGUAJE NO PERMITIDO. Has sido enviado a la Sala de Castigo.");
                location.href = r.url;
            }}
        </script>
    </body></html>
    """

@app.get("/comunidad", response_class=HTMLResponse)
async def ver_comunidad():
    # Mensaje de actualización (puedes activarlo/desactivarlo aquí)
    banner = "<div class='banner-update'>🚀 Estamos trabajando en el Top 3 de mejoras. ¡Gracias por tu paciencia!</div>"
    
    users = await database.fetch_all(usuarios.select().where(usuarios.c.estado == "activo"))
    cartas = ""
    for u in users:
        verif = "<span class='check-azul'>✅</span>" if u.verificado else ""
        cartas += f"<div class='card' style='text-align:left;'><strong>{u.nombre} {verif}</strong> ({u.edad} años)<p style='color:#666;'>{u.quien_soy}</p></div>"
    
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body>{banner}<h1>👥 Comunidad</h1>{cartas or 'No hay usuarios activos.'}<br><a href='/'>⬅️ Volver</a><br><br><a href='/encuesta' style='color:#ff4b6e;'>🗳️ Votar por mejoras</a></body></html>"

@app.get("/sala-castigo", response_class=HTMLResponse)
async def castigo():
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div class='sala-castigo'><h1>⛓️ Sala de Castigo</h1><p>Tu cuenta ha sido aislada temporalmente por lenguaje ofensivo o acoso. Solo puedes hablar con otros infractores aquí.</p><p>Tiempo restante: 1 Semana</p></div><br><a href='/'>Volver al Inicio</a></body></html>"

@app.get("/encuesta", response_class=HTMLResponse)
async def ver_encuesta():
    opts = await database.fetch_all(encuestas.select())
    lista = ""
    for o in opts:
        lista += f"<div class='card'>{o.opcion} <br> <a href='/api/votar/{o.id}' class='btn' style='background:#ff4b6e; color:white; padding:5px 10px; margin-top:10px;'>Votar</a></div>"
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>🗳️ ¿Qué quieres ver el próximo mes?</h1><p>Elige tu mejora favorita:</p>{lista}<a href='/comunidad'>Regresar</a></body></html>"

# --- PANEL DE ADMINISTRACIÓN (TÚ) ---

@app.get("/admin", response_class=HTMLResponse)
async def panel_admin(key: str = ""):
    if key != CLAVE_ADMIN: return "<h1>Acceso Denegado</h1>"
    users = await database.fetch_all(usuarios.select())
    votos = await database.fetch_all(encuestas.select().order_by(encuestas.c.votos.desc()))
    
    tabla = "<table border='1' style='width:100%'><tr><th>Nombre</th><th>Estado</th><th>Acciones</th></tr>"
    for u in users:
        tabla += f"<tr><td>{u.nombre}</td><td>{u.estado}</td><td><a href='/api/admin/verificar/{u.id}?key={key}' class='btn btn-admin'>Verificar</a><a href='/api/admin/castigar/{u.id}?key={key}' class='btn btn-admin' style='background:orange;'>Castigar</a></td></tr>"
    tabla += "</table>"
    
    top3 = "<h3>📊 Top 3 Mejoras (Encuesta):</h3><ul>"
    for v in votos[:3]:
        top3 += f"<li>{v.opcion} ({v.votos} votos)</li>"
    top3 += "</ul>"

    return f"<html><head>{ESTILOS}</head><body><h1>Admin: Silver Breaker</h1>{top3}{tabla}</body></html>"

# --- LOGICA API ---

@app.post("/api/registrar")
async def api_registrar(data: dict):
    estado = "activo"
    url = "/comunidad"
    if hay_insulto(data['nombre']) or hay_insulto(data['quien_soy']):
        estado = "castigado"
        url = "/sala-castigo"
    
    await database.execute(usuarios.insert().values(
        nombre=data['nombre'], edad=data['edad'], quien_soy=data['quien_soy'], 
        estado=estado, verificado=False
    ))
    return {"status": estado, "url": url}

@app.get("/api/votar/{oid}")
async def votar(oid: int):
    await database.execute("UPDATE encuestas SET votos = votos + 1 WHERE id = :id", {"id": oid})
    return HTMLResponse("<script>alert('Voto registrado'); location.href='/encuesta';</script>")

@app.get("/api/admin/verificar/{uid}")
async def verificar_user(uid: int, key: str):
    if key == CLAVE_ADMIN:
        await database.execute(usuarios.update().where(usuarios.c.id == uid).values(verificado=True))
    return HTMLResponse("<script>history.back();</script>")

@app.get("/api/admin/castigar/{uid}")
async def castigar_user(uid: int, key: str):
    if key == CLAVE_ADMIN:
        await database.execute(usuarios.update().where(usuarios.c.id == uid).values(estado="castigado"))
    return HTMLResponse("<script>history.back();</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
