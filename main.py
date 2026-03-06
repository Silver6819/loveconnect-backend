import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from datetime import datetime

# --- CONFIGURACIÓN ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
CLAVE_ADMIN = "admin123" 

# --- TABLAS (Usuarios, Encuestas y Sugerencias) ---
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

# --- FILTRO ---
PROHIBIDAS = ["coño", "mierda", "coger", "pendejo", "acosador", "puta", "gilipollas"]
def filtro_seguridad(t):
    for p in PROHIBIDAS:
        if t and p in t.lower(): return True
    return False

# --- ESTILOS ---
ESTILOS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; text-align: center; padding: 10px; color: #333; margin:0; }
    .card { background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin: 20px auto; max-width: 450px; }
    .input-field { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 16px; box-sizing: border-box; }
    .btn-pink { background: #ff4b6e; color: white; padding: 15px; width: 100%; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; font-size:16px; }
    .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 20px; box-sizing: border-box; }
    .modal-terminos { background: white; padding: 25px; border-radius: 20px; max-width: 500px; text-align: left; max-height: 80vh; overflow-y: auto; }
</style>
"""

# --- RUTA INICIO (Con Pantalla de Términos) ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head>
    <body>
        <div id='capa-terminos' class='overlay'>
            <div class='modal-terminos'>
                <h2 style='color:#ff4b6e; text-align:center;'>📜 Términos y Condiciones</h2>
                <p>Bienvenido a <b>LoveConnect Zacate</b>. Para continuar, acepta nuestras reglas:</p>
                <ul>
                    <li><b>Edad:</b> Solo mayores de 18 años.</li>
                    <li><b>Respeto:</b> El acoso o insultos resultan en <b>Sala de Castigo</b> inmediata.</li>
                    <li><b>Privacidad:</b> No compartas datos sensibles en público.</li>
                    <li><b>VIP:</b> El Check Azul ✅ es un servicio de distinción para la comunidad.</li>
                </ul>
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
                if(!d.nombre || !d.edad) return alert("Por favor, llena los campos principales.");
                if(d.edad < 18) return alert("Debes ser mayor de 18 años.");
                const res = await fetch('/api/reg', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(d) }});
                const r = await res.json();
                if(r.status == 'castigado') alert('⚠️ Lenguaje no permitido detectado.');
                location.href = r.url;
            }}
        </script>
    </body></html>
    """

@app.get("/comunidad", response_class=HTMLResponse)
async def comunidad():
    users = await database.fetch_all(usuarios.select().where(usuarios.c.estado == "activo"))
    lista = "".join([f"<div class='card' style='text-align:left;'><strong>{u.nombre} {'<span style=\"color:#00a2ff;\">✅</span>' if u.verificado else ''}</strong> ({u.edad})<p>{u.quien_soy}</p></div>" for u in users])
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>🌍 Comunidad</h1>{lista or 'Aún no hay perfiles.'}<br><a href='/encuesta' style='color:#ff4b6e; font-weight:bold;'>🗳️ Votar por mejoras</a><br><br><a href='/'>⬅️ Volver</a></body></html>"

@app.get("/encuesta", response_class=HTMLResponse)
async def encuesta():
    opts = await database.fetch_all(encuestas.select())
    html_votos = "".join([f"<div class='card'>{o.opcion}<br><a href='/api/votar/{o.id}' style='color:#ff4b6e; font-weight:bold;'>Votar este</a></div>" for o in opts])
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head><body><h1>🗳️ Mejoras</h1>{html_votos}<div class='card' style='border:2px dashed #ff4b6e;'><h3>💡 Sugiere algo</h3><input type='text' id='idea' class='input-field' placeholder='Tu propuesta...'><button class='btn-pink' style='background:#4b89ff;' onclick='enviarIdea()'>Enviar</button></div><script>async function enviarIdea() {{ const t = document.getElementById('idea').value; const res = await fetch('/api/sugerir', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{ idea: t }}) }}); alert('Sugerencia enviada'); location.reload(); }}</script></body></html>"

@app.get("/admin", response_class=HTMLResponse)
async def admin(key: str = ""):
    if key != CLAVE_ADMIN: return "Denegado"
    users = await database.fetch_all(usuarios.select())
    ideas = await database.fetch_all(sugerencias.select())
    filas = "".join([f"<tr><td>{u.nombre}</td><td><a href='/api/adm/v/{u.id}?key={key}'>✅ Verif</a></td></tr>" for u in users])
    sugs = "".join([f"<li>{i.idea}</li>" for i in ideas])
    return f"<html><body><h1>Admin Silver Breaker</h1><h3>Sugerencias:</h3><ul>{sugs}</ul><h3>Usuarios:</h3><table border='1'>{filas}</table></body></html>"

@app.post("/api/reg")
async def api_reg(data: dict):
    est = "castigado" if filtro_seguridad(data['nombre']) or filtro_seguridad(data['quien_soy']) else "activo"
    await database.execute(usuarios.insert().values(nombre=data['nombre'], edad=data['edad'], ubicacion=data['ubicacion'], quien_soy=data['quien_soy'], estado=est, verificado=False))
