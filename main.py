import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
CLAVE_ADMIN = "admin123" 

# --- TABLAS ---
usuarios = sqlalchemy.Table("usuarios_comunidad", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("nombre", sqlalchemy.String),
    sqlalchemy.Column("edad", sqlalchemy.Integer),
    sqlalchemy.Column("ubicacion", sqlalchemy.String),
    sqlalchemy.Column("quien_soy", sqlalchemy.Text),
    sqlalchemy.Column("verificado", sqlalchemy.Boolean, default=False),
    sqlalchemy.Column("estado", sqlalchemy.String, default="activo"))

encuestas = sqlalchemy.Table("mejoras_app", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("opcion", sqlalchemy.String),
    sqlalchemy.Column("votos", sqlalchemy.Integer, default=0))

sugerencias = sqlalchemy.Table("propuestas_libres", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("idea", sqlalchemy.String),
    sqlalchemy.Column("fecha", sqlalchemy.DateTime, default=datetime.now))

app = FastAPI()

@app.on_event("startup")
async def startup():
    if not database.is_connected: await database.connect()
    engine = sqlalchemy.create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://"))
    metadata.create_all(engine)
    count = await database.execute("SELECT count(*) FROM mejoras_app")
    if count == 0:
        opts = ["Videollamadas", "Stickers Locales", "Filtros VIP", "Modo Oscuro", "Chat de Voz", "Juegos Gratis"]
        for o in opts: await database.execute(encuestas.insert().values(opcion=o, votos=0))

# --- FILTRO DE SEGURIDAD ---
PROHIBIDAS = ["coño", "mierda", "coger", "pendejo", "acosador", "puta", "gilipollas", "hijo de puta"]
def filtro_seguridad(t):
    for p in PROHIBIDAS:
        if t and p in t.lower(): return True
    return False

# --- ESTILOS VISUALES ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; text-align: center; padding: 10px; color: #333; margin:0; }
    .card { background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin: 20px auto; max-width: 450px; }
    .input-field { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
    .btn-pink { background: #ff4b6e; color: white; padding: 15px; width: 100%; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; text-decoration:none; display:block; margin: 10px auto; }
    .btn-admin-nav { background: #444; color: white; padding: 10px 20px; border-radius: 10px; text-decoration: none; font-weight: bold; font-size: 0.9em; display: inline-block; margin-bottom: 20px; }
    .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .modal-terminos { background: white; padding: 25px; border-radius: 20px; max-width: 500px; text-align: left; }
    table { width: 100%; border-collapse: collapse; margin-top: 10px; background: white; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 0.9em; }
    .check-azul { color: #00a2ff; font-weight: bold; }
</style>
"""

# --- VISTA PRINCIPAL (REGISTRO) ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head>
    <body>
        <div id='capa-terminos' class='overlay'>
            <div class='modal-terminos'>
                <h2 style='color:#ff4b6e; text-align:center;'>📜 Reglas LoveConnect</h2>
                <p>Bienvenido a la comunidad de Zacatecoluca. Acepta para continuar:</p>
                <ul><li>Solo para mayores de 18 años.</li><li>Respeto total (Sala de Castigo activa).</li><li>Privacidad responsable con tus datos.</li></ul>
                <button class='btn-pink' onclick='aceptar()'>Aceptar y Entrar</button>
            </div>
        </div>
        <h2 style='color:#ff4b6e'>💖 LoveConnect</h2>
        <div class='card'>
            <h3>Registro de Perfil</h3>
            <input type='text' id='n' class='input-field' placeholder='Nombre completo'>
            <input type='number' id='e' class='input-field' placeholder='Edad'>
            <input type='text' id='u' class='input-field' placeholder='Ubicación'>
            <textarea id='q' class='input-field' style='height:80px' placeholder='¿Quién soy?'></textarea>
            <button class='btn-pink' onclick='enviar()'>Publicar</button>
        </div>
        <a href='/comunidad' style='color:#ff4b6e; text-decoration:none; font-weight:bold;'>Ir a la Comunidad 🌍</a>
        <script>
            function aceptar() {{ document.getElementById('capa-terminos').style.display = 'none'; }}
            async function enviar() {{ 
                const d = {{ nombre: document.getElementById('n').value, edad: parseInt(document.getElementById('e').value), ubicacion: document.getElementById('u').value, quien_soy: document.getElementById('q').value }};
                if(!d.nombre || !d.edad) return alert("Por favor, llena los campos.");
                if(d.edad < 18) return alert("Solo para mayores de edad.");
                const res = await fetch('/api/reg', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(d) }});
                const r = await res.json();
                if(r.status == 'castigado') alert('⚠️ Lenguaje no permitido detectado.');
                location.href = r.url;
            }}
        </script>
    </body></html>
    """

# --- VISTA COMUNIDAD ---
@app.get("/comunidad", response_class=HTMLResponse)
async def comunidad():
    users = await database.fetch_all(usuarios.select().where(usuarios.c.estado == "activo"))
    lista = "".join([f"<div class='card' style='text-align:left;'><strong>{u.nombre} {'<span class=\"check-azul\">✅</span>' if u.verificado else ''}</strong> ({u.edad}) - {u.ubicacion}<p style='color:#666;'>{u.quien_soy}</p></div>" for u in users])
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>🌍 Comunidad</h1>{lista or 'No hay perfiles.'}<br><a href='/encuesta' style='color:#ff4b6e; font-weight:bold;'>🗳️ Votar por mejoras</a><br><br><a href='/' style='text-decoration:none; color:#666;'>⬅️ Volver al Inicio</a></body></html>"

# --- VISTA ENCUESTAS Y SUGERENCIAS ---
@app.get("/encuesta", response_class=HTMLResponse)
async def encuesta():
    opts = await database.fetch_all(encuestas.select())
    html_votos = "".join([f"<div class='card'>{o.opcion}<br><a href='/api/votar/{o.id}' style='color:#ff4b6e; font-weight:bold;'>Votar este</a></div>" for o in opts])
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head>
    <body>
        <h1>🗳️ Mejoras del Mes</h1>
        {html_votos}
        <div class='card' style='border:2px dashed #ff4b6e;'>
            <h3>💡 Sugiere algo</h3>
            <input type='text' id='idea' class='input-field' placeholder='Tu propuesta...'>
            <button class='btn-pink' style='background:#4b89ff;' onclick='enviarIdea()'>Enviar</button>
            <br>
            <a href='/comunidad' style='text-decoration:none; color:#666; font-size:0.9em; display:block; margin-top:15px;'>⬅️ Volver a la Comunidad</a>
        </div>
        <script>
            async function enviarIdea() {{ 
                const t = document.getElementById('idea').value; 
                if(!t) return alert("Escribe tu idea.");
                await fetch('/api/sugerir', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{ idea: t }}) }}); 
                alert('Sugerencia enviada'); location.reload(); 
            }}
        </script>
    </body></html>
    """

# --- PANEL ADMIN (PARA TI, SILVER BREAKER) ---
@app.get("/admin", response_class=HTMLResponse)
async def admin(key: str = ""):
    if key != CLAVE_ADMIN: return "<h1>Acceso Denegado</h1>"
    users = await database.fetch_all(usuarios.select())
    ideas = await database.fetch_all(sugerencias.select().order_by(sugerencias.c.id.desc()))
    filas = "".join([f"<tr><td>{u.nombre}</td><td>{u.estado}</td><td><a href='/api/adm/v/{u.id}?key={key}'>✅</a> | <a href='/api/adm/c/{u.id}?key={key}'>⛓️</a></td></tr>" for u in users])
    lista_ideas = "".join([f"<li>{i.idea} <small>({i.fecha.strftime('%d/%m')})</small></li>" for i in ideas])
    return f"""
    <html><head>{ESTILOS}</head>
    <body style='max-width:800px; margin:auto; padding:20px; text-align:left;'>
        <a href='/' class='btn-admin-nav'>⬅️ Ir a Vista Pública</a>
        <h1 style='color:#ff4b6e;'>👑 Panel Silver Breaker</h1>
        <div class='card' style='max-width:100%;'><h3>💡 Sugerencias de Usuarios:</h3><ul>{lista_ideas or 'Sin sugerencias.'}</ul></div>
        <div class='card' style='max-width:100%;'><h3>👥 Gestión de Usuarios:</h3><table><tr><th>Nombre</th><th>Estado</th><th>Acciones</th></tr>{filas}</table></div>
    </body></html>
    """

@app.get("/sala-castigo", response_class=HTMLResponse)
async def sala_castigo():
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><div class='card' style='background:#333; color:white;'><h1>⛓️ Sala de Castigo</h1><p>Has sido aislado por lenguaje inapropiado.</p></div><a href='/'>Volver al Inicio</a></body></html>"

# --- API ---
@app.post("/api/reg")
async def api_reg(data: dict):
    est = "castigado" if filtro_seguridad(data['nombre']) or filtro_seguridad(data['quien_soy']) else "activo"
    await database.execute(usuarios.insert().values(nombre=data['nombre'], edad=data['edad'], ubicacion=data['ubicacion'], quien_soy=data['quien_soy'], estado=est, verificado=False))
    return {"status": est, "url": "/comunidad" if est == "activo" else "/sala-castigo"}

@app.post("/api/sugerir")
async def api_sug(data: dict):
    if filtro_seguridad(data['idea']): return {"status": "castigado"}
    await database.execute(sugerencias.insert().values(idea=data['idea']))
    return {"status": "ok"}

@app.get("/api/votar/{oid}")
async def api_vot(oid: int):
    await database.execute("UPDATE mejoras_app SET votos = votos + 1 WHERE id = :id", {"id": oid})
    return HTMLResponse("<script>history.back();</script>")

@app.get("/api/adm/v/{uid}")
async def api_v(uid: int, key: str):
    if key == CLAVE_ADMIN: await database.execute(usuarios.update().where(usuarios.c.id == uid).values(verificado=True))
    return HTMLResponse("<script>history.back();</script>")

@app.get("/api/adm/c/{uid}")
async def api_c(uid: int, key: str):
    if key == CLAVE_ADMIN: await database.execute(usuarios.update().where(usuarios.c.id == uid).values(estado="castigado"))
    return HTMLResponse("<script>history.back();</script>")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
