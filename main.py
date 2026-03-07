import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlalchemy
import databases
from datetime import datetime

# 1. CONFIGURACIÓN DE BASE DE DATOS
DATABASE_URL = "sqlite:///./loveconnect.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# Tabla de mensajes de la comunidad
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

# 2. RUTAS DEL BACKEND
@app.get("/obtener-mensajes")
async def obtener_mensajes():
    query = mensajes_comunidad.select().order_by(mensajes_comunidad.c.id.desc()).limit(20)
    return await database.fetch_all(query)

@app.post("/enviar-mensaje")
async def enviar_mensaje(usuario: str = Form(...), texto: str = Form(...)):
    fecha_actual = datetime.now().strftime("%H:%M")
    query = mensajes_comunidad.insert().values(usuario=usuario, texto=texto, fecha=fecha_actual)
    await database.execute(query)
    return {"status": "ok"}

# 3. INTERFAZ DE USUARIO (FRONTEND)
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LoveConnect - Comunidad</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #fffafa; display: flex; flex-direction: column; align-items: center; margin: 0; padding: 20px; }
            .header { text-align: center; margin-bottom: 20px; }
            .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
            input[type="text"], textarea { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }
            .btn { background-color: #ff4d6d; color: white; border: none; padding: 12px; border-radius: 10px; cursor: pointer; width: 100%; font-weight: bold; }
            .chat-box { margin-top: 20px; height: 300px; overflow-y: auto; border-top: 1px solid #eee; padding-top: 10px; }
            .mensaje { background: #f9f9f9; padding: 8px; border-radius: 10px; margin-bottom: 10px; font-size: 0.9em; border-left: 4px solid #ff4d6d; }
            .msg-admin { border-left: 4px solid #ffd700; background: #fffdf0; }
            .meta { font-size: 0.7em; color: #888; display: block; }
            #logout-btn { color: #888; text-decoration: none; font-size: 0.8em; margin-top: 15px; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌎 Comunidad</h1>
        </div>

        <div id="login-section" class="card">
            <input type="text" id="username" placeholder="Tu nombre de usuario">
            <label><input type="checkbox" id="rememberMe"> Recordarme</label>
            <button class="btn" onclick="entrar()">Entrar y Aceptar Reglas</button>
        </div>

        <div id="chat-section" class="card" style="display:none;">
            <div id="chat-display" class="chat-box"></div>
            <textarea id="msg-input" placeholder="Escribe algo a la comunidad..."></textarea>
            <button class="btn" onclick="enviarMsg()">Enviar Mensaje</button>
            <center><a id="logout-btn" onclick="cerrarSesion()">Cerrar Sesión</a></center>
        </div>

        <script>
            const VERSION = "1.2";
            const ADMIN_NAME = "Silver Breaker"; // Tu nombre de autor

            window.onload = function() {
                if(localStorage.getItem("app_v") !== VERSION) {
                    alert("Gracias por la espera, se encuentra la app actualizada ya puede ingresar.");
                    localStorage.setItem("app_v", VERSION);
                }
                const savedUser = localStorage.getItem("user_rc");
                if(savedUser) { 
                    document.getElementById("username").value = savedUser;
                    document.getElementById("rememberMe").checked = true;
                }
            };

            function entrar() {
                const user = document.getElementById("username").value;
                if(!user) return alert("Ingresa un nombre");
                
                if(document.getElementById("rememberMe").checked) localStorage.setItem("user_rc", user);
                else localStorage.removeItem("user_rc");

                sessionStorage.setItem("active_user", user);
                document.getElementById("login-section").style.display = "none";
                document.getElementById("chat-section").style.display = "block";
                cargarMensajes();
                setInterval(cargarMensajes, 5000); // Actualiza cada 5 seg
            }

            async function cargarMensajes() {
                const res = await fetch("/obtener-mensajes");
                const datos = await res.json();
                const display = document.getElementById("chat-display");
                display.innerHTML = "";
                datos.forEach(m => {
                    const isAdmin = m.usuario === ADMIN_NAME ? "msg-admin" : "";
                    display.innerHTML += `<div class="mensaje ${isAdmin}">
                        <strong>${m.usuario}</strong> <span class="meta">${m.fecha}</span>
                        <div>${m.texto}</div>
                    </div>`;
                });
            }

            async function enviarMsg() {
                const texto = document.getElementById("msg-input").value;
                const usuario = sessionStorage.getItem("active_user");
                if(!texto) return;

                const formData = new FormData();
                formData.append("usuario", usuario);
                formData.append("texto", texto);

                await fetch("/enviar-mensaje", { method: "POST", body: formData });
                document.getElementById("msg-input").value = "";
                cargarMensajes();
            }

            function cerrarSesion() {
                sessionStorage.clear();
                location.reload();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
