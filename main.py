import os
import uvicorn
import databases
import sqlalchemy
from fastapi import FastAPI, Request
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
        opts = ["Chat de Voz", "Juegos Gratis", "Videollamadas", "Stickers Locales", "Filtros VIP", "Modo Oscuro"]
        for o in opts: await database.execute(encuestas.insert().values(opcion=o, votos=0))

# --- FILTRO Y ESTILOS ---
PROHIBIDAS = ["coño", "mierda", "coger", "pendejo", "acosador", "puta", "gilipollas", "hijo de puta"]
def filtro_seguridad(t):
    for p in PROHIBIDAS:
        if t and p in t.lower(): return True
    return False

ESTILOS = """
<style>
    body { 
        font-family: 'Segoe UI', sans-serif; background: #fff5f7; 
        margin: 0; display: flex; justify-content: center; align-items: center; 
        min-height: 100vh; flex-direction: column;
    }
    .app-container { width: 100%; max-width: 420px; padding: 20px; box-sizing: border-box; text-align: center; }
    .card { background: white; border-radius: 25px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .input-field { width: 100%; padding: 14px; margin: 8px 0; border: 1px solid #ddd; border-radius: 12px; font-size: 16px; box-sizing: border-box; outline: none; }
    .btn-pink { background: #ff4b6e; color: white; padding: 16px; width: 100%; border: none; border-radius: 15px; font-weight: bold; cursor: pointer; font-size: 16px; }
    .btn-blue { background: #4b89ff; color: white; padding: 15px; border: none; border-radius: 12px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 10px; }
    .btn-grey { background: #636363; color: white; padding: 15px; border-radius: 12px; width: 100%; font-weight: bold; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 10px; }
    .overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .modal-rules { background: white; padding: 30px; border-radius: 25px; max-width: 400px; text-align: left; box-shadow: 0 15px 35px rgba(0,0,0,0.2); }
    .check-azul { color: #00a2ff; font-weight: bold; }
    .dashed-box { border: 2px dashed #ff4b6e; border-radius: 30px; padding: 25px; background: white; margin-top: 10px; }
</style>
"""

# --- RUTAS ---
@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head>
    <body>
        <div id='capa-terminos' class='overlay'>
            <div class='modal-rules'>
                <h2 style='color:#ff4b6e; text-align:center;'>📜 Reglas LoveConnect</h2>
                <p>Bienvenido. Acepta para continuar:</p>
                <ul style='list-style: none; padding: 0;'>
                    <li>• Solo para mayores de 18 años.</li>
                    <li>• Respeto total (Sala de Castigo activa).</li>
                    <li>• Privacidad responsable.</li>
                </ul>
                <button class='btn-pink' onclick='aceptar()'>Aceptar y Entrar</button>
            </div>
        </div>
        <div class='app-container'>
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
        </div>
        <script>
            function aceptar() {{ document.getElementById('capa-terminos').style.display = 'none'; }}
            async function enviar() {{ 
                const d = {{ nombre: document.getElementById('n').value, edad: parseInt(document.getElementById('e').value), ubicacion: document.getElementById('u').value, quien_soy: document.getElementById('q').value }};
                if(!d.nombre || !d.edad) return alert("Llena los campos.");
                const res = await fetch('/api/reg', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify(d) }});
                const r = await res.json();
                location.href = r.url;
            }}
        </script>
    </body></html>
    """

@app.get("/comunidad", response_class=HTMLResponse)
async def comunidad():
    users = await database.fetch_all(usuarios.select().where(usuarios.c.estado == "activo"))
    lista = "".join([f"<div class='card' style='text-align:left;'><strong>{u.nombre} {'<span class=\"check-azul\">✅</span>' if u.verificado else ''}</strong> ({u.edad})<p>{u.quien_soy}</p></div>" for u in users])
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head>
    <body>
        <div class='app-container'>
            <h1>🌍 Comunidad</h1>
            {lista or 'No hay perfiles.'}
            <br><a href='/encuesta' style='color:#ff4b6e; font-weight:bold; font-size:1.1em;'>🗳️ Votar por mejoras</a>
            <br><br><a href='/' style='text-decoration:none; color:#666;'>⬅️ Volver al Inicio</a>
        </div>
    </body></html>
    """

@app.get("/encuesta", response_class=HTMLResponse)
async def encuesta():
    opts = await database.fetch_all(encuestas.select())
    html_votos = "".join([f"<div class='card'>{o.opcion}<br><a href='/api/votar/{o.id}' style='color:#ff4b6e; font-weight:bold;'>Votar</a></div>" for o in opts])
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>{ESTILOS}</head>
    <body>
        <div class='app-container'>
            <h1>🗳️ Mejoras del Mes</h1>
            {html_votos}
            <div class='dashed-box'>
                <h3>💡 Sugiere algo</h3>
                <input type='text' id='idea' class='input-field' placeholder='Tu idea...'>
                <button class='btn-blue' onclick='enviarIdea()'>Enviar Sugerencia</button>
                <a href='/comunidad' class='btn-grey'>⬅️ Volver a la Comunidad</a>
            </div>
            <br><a href='/' style='color:#666; text-decoration:none;'>🏠 Ir al Inicio</a>
        </div>
        <script>
            async function enviarIdea() {{ 
                const t = document.getElementById('idea').value; 
                if(!t) return alert("Escribe tu idea.");
                await fetch('/api/sugerir', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body:JSON.stringify({{ idea: t }}) }}); 
                alert('Enviada'); location.reload(); 
            }}
        </script>
    </body></html>
    """

# --- API LOGIC (Sin cambios, solo integración) ---
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

@app.get("/sala-castigo", response_class=HTMLResponse)
async def sala_castigo():
    return f"<html><body style='text-align:center; padding-top:50px;'><h1>⛓️ Sala de Castigo</h1><p>Tu perfil contiene lenguaje no permitido.</p><a href='/'>Volver</a></body></html>"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
