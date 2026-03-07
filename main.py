import os, sqlalchemy, databases
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

# DB Ligera
DB_URL = "sqlite:///./love.db"
db = databases.Database(DB_URL)
meta = sqlalchemy.MetaData()
msg = sqlalchemy.Table("m", meta, sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True), sqlalchemy.Column("u", sqlalchemy.String(50)), sqlalchemy.Column("t", sqlalchemy.String(500)))
eng = sqlalchemy.create_engine(DB_URL, connect_args={"check_same_thread": False})
meta.create_all(eng)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await db.connect()
    await db.execute(msg.delete()) # Limpieza de seguridad

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; background: #fffafa; display: flex; flex-direction: column; align-items: center; margin: 0; }
            .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 90%; max-width: 350px; margin-top: 20px; text-align: center; }
            .modal { display: none; position: fixed; top: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.4); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px); z-index: 1000; justify-content: center; align-items: center; }
            .m-c { background: white; padding: 25px; border-radius: 20px; width: 80%; max-width: 300px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
            .btn { background: #ff4d6d; color: white; border: none; padding: 12px; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div id="login" class="card">
            <h1>🌎 Comunidad</h1>
            <input type="text" id="user" placeholder="Usuario" style="width:90%; padding:10px; border-radius:8px; border:1px solid #ddd;">
            <label style="display:block; margin:10px;"><input type="checkbox" id="rem"> Recordarme</label>
            <button class="btn" onclick="shM()">Entrar</button>
        </div>

        <div id="modal" class="modal">
            <div class="m-c">
                <h2 style="color:#ff4d6d; margin:0;">📜 Reglas</h2>
                <ul style="text-align:left; font-size:0.85em; margin:15px 0;">
                    <li>• +18 años solamente.</li>
                    <li>• Sala de Castigo activa.</li>
                    <li>• Privacidad responsable.</li>
                </ul>
                <button class="btn" onclick="go()">Aceptar y Entrar</button>
            </div>
        </div>

        <div id="chat" class="card" style="display:none;">
            <div id="box" style="height:200px; overflow-y:auto; text-align:left; border-bottom:1px solid #eee;"></div>
            <textarea id="in" placeholder="Mensaje..." style="width:90%; margin-top:10px; border-radius:8px;"></textarea>
            <button class="btn" onclick="send()">Enviar</button>
            <a onclick="location.reload()" style="display:block; margin-top:10px; color:#888; font-size:0.7em; cursor:pointer;">Cerrar Sesión</a>
        </div>

        <script>
            const V = "1.2";
            window.onload = () => {
                if(localStorage.getItem("v") !== V) { alert("Gracias por la espera, app actualizada."); localStorage.setItem("v", V); }
                if(localStorage.getItem("u")) { document.getElementById("user").value = localStorage.getItem("u"); document.getElementById("rem").checked = true; }
            };
            function shM() { if(!document.getElementById("user").value) return alert("Nombre?"); document.getElementById("modal").style.display="flex"; }
            function go() {
                const u = document.getElementById("user").value;
                if(document.getElementById("rem").checked) localStorage.setItem("u", u); else localStorage.removeItem("u");
                sessionStorage.setItem("usr", u);
                document.getElementById("modal").style.display="none"; document.getElementById("login").style.display="none"; document.getElementById("chat").style.display="block";
                setInterval(load, 5000); load();
            }
            async function send() {
                const t = document.getElementById("in").value; const u = sessionStorage.getItem("usr");
                if(!t) return;
                const f = new FormData(); f.append("u", u); f.append("t", t);
                await fetch("/send", {method:"POST", body:f}); document.getElementById("in").value=""; load();
            }
            async function load() {
                const r = await fetch("/read"); const data = await r.json();
                document.getElementById("box").innerHTML = data.map(i => `<div style="margin-bottom:5px; font-size:0.9em;"><b>${i.u}:</b> ${i.t}</div>`).join('');
            }
        </script>
    </body>
    </html>
    """

@app.get("/read")
async def read(): return await db.fetch_all(msg.select().order_by(msg.c.id.desc()).limit(10))

@app.post("/send")
async def send(u: str = Form(...), t: str = Form(...)):
    await db.execute(msg.insert().values(u=u, t=t))
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
