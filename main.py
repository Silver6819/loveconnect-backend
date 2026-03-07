import os
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import sqlalchemy

# --- CONFIGURACIÓN DE BASE DE DATOS LIGERA ---
DB_URL = "sqlite:///./love.db"
engine = sqlalchemy.create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = sqlalchemy.MetaData()

msg_t = sqlalchemy.Table(
    "m", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("u", sqlalchemy.String(50)), # Usuario
    sqlalchemy.Column("t", sqlalchemy.String(500)) # Texto
)
metadata.create_all(engine)

app = FastAPI()

# --- LÓGICA DE ADMINISTRADOR Y SEGURIDAD ---
ADMIN_NAME = "Silver Breaker"
PALABRAS_PROHIBIDAS = ["insulto1", "ofensa2", "spam", "toxicidad"]

class ConnectionManager:
    def __init__(self):
        # Diccionario para rastrear usuarios por nombre y enviar privados
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user] = websocket

    def disconnect(self, user: str):
        if user in self.active_connections:
            del self.active_connections[user]

    async def broadcast(self, message: str, sender: str):
        # Si el emisor eres tú, se añade el rango visual
        display_msg = f"⭐ [ADMIN] {message}" if sender == ADMIN_NAME else message
        for user_id, connection in self.active_connections.items():
            await connection.send_text(display_msg)

    async def send_private(self, message: str, target_user: str, sender: str):
        if target_user in self.active_connections:
            private_msg = f"🔒 [PRIVADO de {sender}]: {message}"
            await self.active_connections[target_user].send_text(private_msg)
            await self.active_connections[sender].send_text(private_msg)
        else:
            await self.active_connections[sender].send_text(f"❌ El usuario '{target_user}' no está en línea.")

manager = ConnectionManager()

# --- INTERFAZ DE USUARIO (HTML/CSS/JS) ---
@app.get("/", response_class=HTMLResponse)
async def get():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LoveConnect</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; height: 100vh; overflow: hidden; display: flex; justify-content: center; align-items: center; }
            
            /* MODAL REGLAS (EFECTO BLUR) */
            .modal-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(255, 255, 255, 0.3); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                display: flex; justify-content: center; align-items: center; z-index: 3000;
            }
            .modal-box {
                background: white; padding: 30px; border-radius: 30px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 85%; max-width: 380px; text-align: center;
            }
            
            /* REGISTRO DE PERFIL */
            #profile-registration { 
                display: none; background: white; padding: 30px; border-radius: 30px; width: 90%; max-width: 400px; 
                flex-direction: column; gap: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); z-index: 1000;
            }
            
            /* APP PRINCIPAL */
            #main-app { display: none; width: 100%; height: 100vh; flex-direction: column; background: #f0f2f5; }
            .header { background: white; padding: 15px; text-align: center; font-weight: bold; color: #FF4081; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
            
            /* CHAT */
            #messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
            .msg { background: white; padding: 10px 15px; border-radius: 15px; align-self: flex-start; max-width: 80%; box-shadow: 0 2px 4px rgba(0,0,0,0.05); font-size: 15px; }
            
            /* BOTONES Y INPUTS */
            .btn-pink { background: #FF4081; color: white; border: none; padding: 15px; border-radius: 15px; font-weight: bold; cursor: pointer; font-size: 16px; }
            input, textarea { padding: 12px; border: 1px solid #ddd; border-radius: 15px; outline: none; }
        </style>
    </head>
    <body>
        <div id="rulesModal" class="modal-overlay">
            <div class="modal-box">
                <h1 style="color: #FF4081; margin-top:0;">📜 Reglas LoveConnect</h1>
                <ul style="text-align: left; line-height: 1.8; color: #444;">
                    <li>✅ Solo mayores de 18 años.</li>
                    <li>✅ Respeto total (Sala de Castigo activa).</li>
                    <li>✅ Privados: escribe /@nombre mensaje</li>
                </ul>
                <button class="btn-pink" style="width: 100%;" onclick="showRegister()">Aceptar y Entrar</button>
            </div>
        </div>

        <div id="profile-registration">
            <h2 style="color: #FF4081; text-align: center; margin-top:0;">💖 Registro de Perfil</h2>
            <input type="text" id="regName" placeholder="Nombre completo">
            <input type="number" id="regAge" placeholder="Edad">
            <input type="text" id="regLoc" placeholder="Ubicación (Ej: Zacatecoluca)">
            <textarea id="regBio" placeholder="¿Quién soy?" rows="3"></textarea>
            <button class="btn-pink" onclick="startChat()">Publicar y Entrar</button>
        </div>

        <div id="main-app">
            <div class="header">
                <span>💬 Comunidad</span>
                <span>LoveConnect</span>
                <span onclick="location.reload()" style="cursor:pointer; font-size:12px;">Cerrar Sesión</span>
            </div>
            <div id="messages"></div>
            <div style="padding: 15px; background: white; display: flex; gap: 10px; border-top: 1px solid #eee;">
                <input type="text" id="chatInput" style="flex: 1;" placeholder="Mensaje o /@nombre..." onkeypress="if(event.key==='Enter') send()">
                <button onclick="send()" style="background: none; border: none; font-size: 24px; cursor: pointer;">🚀</button>
            </div>
        </div>

        <script>
            let ws;
            let myUserName = "";

            function showRegister() {
                document.getElementById('rulesModal').style.display = 'none';
                document.getElementById('profile-registration').style.display = 'flex';
            }

            function startChat() {
                myUserName = document.getElementById('regName').value.trim();
                if(!myUserName) return alert("Por favor, ingresa tu nombre.");
                
                // Conectar al WebSocket con el nombre de usuario
                ws = new WebSocket(`ws://${window.location.host}/ws/${myUserName}`);
                
                document.getElementById('profile-registration').style.display = 'none';
                document.getElementById('main-app').style.display = 'flex';

                ws.onmessage = (event) => {
                    let log = document.getElementById('messages');
                    let div = document.createElement('div');
                    div.className = 'msg';
                    div.innerText = event.data;
                    log.appendChild(div);
                    log.scrollTop = log.scrollHeight;
                };
            }

            function send() {
                let input = document.getElementById('chatInput');
                if(input.value.trim()) {
                    ws.send(input.value);
                    input.value = "";
                }
            }
        </script>
    </body>
    </html>
    """

@app.websocket("/ws/{user}")
async def websocket_endpoint(websocket: WebSocket, user: str):
    await manager.connect(user, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            # 1. Filtro Sala de Castigo
            if any(word in data.lower() for word in PALABRAS_PROHIBIDAS):
                await websocket.send_text("⚠️ SALA DE CASTIGO: Tu mensaje contiene palabras no permitidas.")
            
            # 2. Lógica de Mensaje Privado (/@nombre mensaje)
            elif data.startswith("/@"):
                try:
                    parts = data.split(" ", 1)
                    target = parts[0][2:] # Extrae el nombre después de /@
                    private_msg = parts[1]
                    await manager.send_private(private_msg, target, user)
                except:
                    await websocket.send_text("❌ Error en formato privado. Usa: /@nombre mensaje")
            
            # 3. Mensaje Público
            else:
                await manager.broadcast(f"{user}: {data}", user)
                
    except WebSocketDisconnect:
        manager.disconnect(user)
