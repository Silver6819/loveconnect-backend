import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import sqlalchemy
import databases
from datetime import datetime

# 1. CONFIGURACIÓN DE BASE DE DATOS
DATABASE_URL = "sqlite:///./loveconnect.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

mensajes_comunidad = sqlalchemy.Table(
    "mensajes_comunidad",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("usuario", sqlalchemy.String(50)),
    sqlalchemy.Column("texto", sqlalchemy.String(500)),
    sqlalchemy.Column("fecha", sqlalchemy.String(20)),
)

engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata.create_all(engine)

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# 2. RUTAS DE DATOS
@app.get("/obtener-mensajes")
async def obtener_mensajes():
    query = mensajes_comunidad.select().order_by(mensajes_comunidad.c.id.desc()).limit(20)
    return await database.fetch_all(query)

@app.post("/enviar-mensaje")
async def enviar_mensaje(usuario: str = Form(...), texto: str = Form(...)):
    query = mensajes_comunidad.insert().values(
        usuario=usuario, 
        texto=texto, 
        fecha=datetime.now().strftime("%H:%M")
    )
    await database.execute(query)
    return {"status": "ok"}

# 3. INTERFAZ (FRONTEND)
@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LoveConnect</title>
        <style>
            body { font-family: sans-serif; background-color: #fffafa; margin: 0; display: flex; flex-direction: column; align-items: center; }
            .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 90%; max-width: 380px; margin-top: 20px; text-align: center; }
            .btn { background-color: #ff4d6d; color: white; border: none; padding: 12px; border-radius: 10px; cursor: pointer; width: 100%; font-weight: bold; margin-top: 10px; }
            
            /* MODAL TIPO CAPTURA */
            .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 1000; justify-content: center; align-items: center; }
            .modal-content { background: white; padding: 30px; border-radius: 25px; width: 80%; max-width: 300px; position: relative; }
            .rules-list { text-align: left; list-style: none; padding: 0; margin: 20px 0; }
            
            .chat-box { height: 250px; overflow-y: auto; border-top: 1px solid #eee; padding: 10px; text-align: left; }
            .mensaje { background: #f1f1f1; padding: 8px; border-radius: 10px; margin-bottom: 8px; border-left: 4px solid #ff4d6d; }
            .msg-admin { border-left-color: #ffd700; background: #fffdf0; }
        </style>
    </head>
    <body>
        <h1 style="margin-top:30px;">🌎 Comunidad</h1>

        <div id="login-section" class="card">
            <input type="text" id="username" placeholder="Nombre de usuario" style="width:90%; padding:10px; border-radius:8px; border:1px solid #ddd;">
            <label style="display:block; margin:10px;"><input type="checkbox" id="rememberMe"> Recordarme</label>
            <button class="btn" onclick="abrirModal()">Entrar</button>
        </div>

        <div id="modal-rules" class="modal-overlay">
            <div class="modal-content">
                <h2 style="color:#ff4d6d; margin:0;">📜 Reglas LoveConnect</h2>
                <p>Bienvenido. Acepta para continuar:</p>
                <ul class="rules-list">
                    <li>• Solo para mayores de 18 años.</li>
                    <li>• Respeto total (Sala de Castigo activa).</li>
                    <li>• Privacidad responsable.</li>
                </ul>
                <button class="btn" onclick="aceptarYEntrar()">Aceptar y Entrar</button>
            </div>
        </div>

        <div id="chat-section" class="card" style="display:none;">
            <div id="chat-display" class="chat-box"></div>
            <textarea id="msg-input" placeholder="Mensaje..." style="width:90%; margin-top:10px; border-radius:8px;"></textarea>
            <button class="btn" onclick="enviarMsg()">Enviar</button>
            <a onclick="cerrarSesion()" style="display:block; margin-top:10px; color:#888; font-size:0.8em; cursor:pointer;">Cerrar Sesión</a>
        </div>

        <script>
            const VERSION = "1.2";
            const ADMIN = "Silver Breaker";

            window.onload = () => {
                if(localStorage.getItem("v") !== VERSION) {
                    alert("Gracias por la espera, se encuentra la app actualizada ya puede ingresar.");
                    localStorage.setItem("v", VERSION);
                }
                const saved = localStorage.getItem("u");
                if(saved) { 
                    document.getElementById("username").value = saved;
                    document.getElementById("rememberMe").checked = true;
                }
            };

            function abrirModal() {
                if(!document.getElementById("username").value) return alert("Escribe tu nombre");
                document.getElementById("modal-rules").style.display = "flex";
            }

            async function aceptarYEntrar() {
                const u = document.getElementById("username").value;
                if(document.getElementById("rememberMe").checked) localStorage.setItem("u", u);
                else localStorage.removeItem("u");

                sessionStorage.setItem("user", u);
                document.getElementById("modal-rules").style.display = "none";
                document.getElementById("login-section").style.display = "none";
                document.getElementById("chat-section").style.display = "block";
                actualizarChat();
                setInterval(actualizarChat, 5000);
            }

            async function actualizarChat() {
                const r = await fetch("/obtener-mensajes");
                const m = await r.json();
                const d = document.getElementById("chat-display");
                d.innerHTML = m.map(msg => `
                    <div class="mensaje ${msg.usuario === ADMIN ? 'msg-admin' : ''}">
                        <strong>${msg.usuario}</strong> <small style="color:#999">${msg.fecha}</small><br>${msg.texto}
                    </div>
                `).join('');
            }

            async function enviarMsg() {
                const t = document.getElementById("msg-input").value;
                const u = sessionStorage.getItem("user");
                if(!t) return;
                const f = new FormData(); f.append("usuario", u); f.append("texto", t);
                await fetch("/enviar-mensaje", { method: "POST", body: f });
                document.getElementById("msg-input").value = "";
                actualizarChat();
            }

            function cerrarSesion() { sessionStorage.clear(); location.reload(); }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
