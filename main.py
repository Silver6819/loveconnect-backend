import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlalchemy

# 1. Configuración de Base de Datos SQLite (Ultra estable)
DB_URL = "sqlite:///./love.db"
engine = sqlalchemy.create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = sqlalchemy.MetaData()

# Definición de tabla minimalista
msg_t = sqlalchemy.Table(
    "m", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("u", sqlalchemy.String(50)),
    sqlalchemy.Column("t", sqlalchemy.String(500))
)
metadata.create_all(engine)

app = FastAPI()

# 2. Interfaz con Difuminado Moderno
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #fffafa; display: flex; flex-direction: column; align-items: center; margin: 0; }
            .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 90%; max-width: 350px; margin-top: 20px; text-align: center; }
            .modal { display: none; position: fixed; top: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.4); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); z-index: 1000; justify-content: center; align-items: center; }
            .m-c { background: white; padding: 25px; border-radius: 20px; width: 80%; max-width: 300px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
            .btn { background: #ff4d6d; color: white; border: none; padding: 12px; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 10px; }
            #box { height: 200px; overflow-y: auto; text-align: left; border-bottom: 1px solid #eee; margin-bottom: 10px; padding: 5px; font-size: 0.9em; }
        </style>
    </head>
    <body>
        <div id="login" class="card">
            <h1>🌎 Comunidad</h1>
            <input type="text" id="user" placeholder="Usuario" style="width:90%; padding:10px; border-radius:8px; border:1px solid #ddd;">
            <label style="display:block; margin:10px;"><input type="checkbox" id="rem"> Recordarme</label>
            <button class="btn" onclick="shM()">Entrar</button>
        </div>

        <div id="modal" class="modal"><div class="m-c">
            <h2 style="color:#ff4d6d; margin:0;">📜 Reglas</h2>
            <ul style="text-align:left; font-size:0.85em; margin:15px 0;">
                <li>• Solo para mayores de 18 años.</li>
                <li>• Respeto total (Sala de Castigo).</li>
                <li>• Privacidad responsable.</li>
            </ul>
            <button class="btn" onclick="go()">Aceptar y Entrar</button>
        </div></div>

        <div id="chat" class="card" style="display:none;">
            <div id="box"></div>
            <textarea id="in" placeholder="Mensaje..." style="width:90%; border-radius:8px; padding:8px; border:1px solid #ddd;"></textarea>
            <button class="btn" onclick="send()">Enviar</button>
            <a onclick="location.reload()" style="display:block; margin-top:10px; color:#888; font-size:0.75em; cursor:pointer;">Cerrar Sesión</a>
        </div>

        <script>
            function shM() { if(!document.getElementById("user").value) return alert("¿Tu nombre?"); document.getElementById("modal").style.display="flex"; }
            function go() {
                const u = document.getElementById("user").value;
                if(document.getElementById("rem").checked) localStorage.setItem("u", u);
                sessionStorage.setItem("usr", u);
                document.getElementById("modal").style.display="none"; 
                document.getElementById("login").style.display="none"; 
                document.getElementById("chat").style.display="block";
                load(); setInterval(load, 4000);
            }
            async function send() {
                const t = document.getElementById("in").value; const u = sessionStorage.getItem("usr");
                if(!t) return;
                const f = new FormData(); f.append("u", u); f.append("t", t);
                await fetch("/send", {method:"POST", body:f}); 
                document.getElementById("in").value=""; 
                load();
            }
            async function load() {
                const r = await fetch("/read"); const data = await r.json();
                document.getElementById("box").innerHTML = data.map(i => `<div><b>${i.u}:</b> ${i.t}</div>`).join('');
                const b = document.getElementById("box"); b.scrollTop = b.scrollHeight;
            }
            window.onload = () => {
                if(localStorage.getItem("u")) { document.getElementById("user").value = localStorage.getItem("u"); document.getElementById("rem").checked = true; }
            };
        </script>
    </body>
    </html>
    """

# 3. Lógica de Datos Simplificada
@app.get("/read")
def read():
    with engine.connect() as conn:
        res = conn.execute(msg_t.select().order_by(msg_t.c.id.desc()).limit(15))
        return [{"u": r.u, "t": r.t} for r in res][::-1]

@app.post("/send")
def send(u: str = Form(...), t: str = Form(...)):
    with engine.connect() as conn:
        conn.execute(msg_t.insert().values(u=u, t=t))
        conn.commit()
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
