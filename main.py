import os
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import sqlalchemy

# --- CONFIGURACIÓN DE BASE DE DATOS LIGERA ---
DB_URL = "sqlite:///./love.db"
engine = sqlalchemy.create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = sqlalchemy.MetaData()

# Tablas para mensajes y sugerencias
msg_t = sqlalchemy.Table(
    "m", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("u", sqlalchemy.String(50)),
    sqlalchemy.Column("t", sqlalchemy.String(500))
)
metadata.create_all(engine)

app = FastAPI()

# --- LÓGICA DE LA SALA DE CASTIGO ---
PALABRAS_PROHIBIDAS = ["insulto1", "ofensa2", "spam"] 

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

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
            
            /* MODAL REGLAS (BLUR) */
            .modal-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(255, 255, 255, 0.3); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                display: flex; justify-content: center; align-items: center; z-index: 3000;
            }
            .modal-box {
                background: white; padding: 30px; border-radius: 30px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 85%; max-width: 380px; text-align: center;
            }

            /* REGISTRO DE PERFIL */
            #profile-reg { display: none; background: white; padding: 30px; border-radius: 30px; width: 90%; max-width: 400px; flex-direction: column; gap: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); z-index: 1000; }
            
            /* INTERFAZ PRINCIPAL */
            #main-app { display: none; width: 100%; height: 100vh; flex-direction: column; background: #f0f2f5; }
            .header { background: white; padding: 15px; text-align: center; font-weight: bold; color: #FF4081; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }
            
            /* VOTACIONES Y SUGERENCIAS (Estilo Capturas) */
            #vote-panel { display: none; flex: 1; padding: 20px; overflow-y: auto; background: #fff5f7; }
            .vote-card { background: white; padding: 20px; border-radius: 20px; margin-bottom: 15px; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
            .vote-link { color: #FF4081; text-decoration: underline; cursor: pointer; font-weight: bold; }
            .suggest-box { border: 2px dashed #FF4081; padding: 20px; border-radius: 25px; margin-top: 20px; }

            /* CHAT */
            #chat-room { display: flex; flex: 1; flex-direction: column; }
            #messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
            .msg { background: white; padding: 10px 15px; border-radius: 15px; max-width: 80%; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

            /* BOTONES Y INPUTS */
            .btn-pink { background: #FF4081; color: white; border: none; padding: 15px; border-radius: 15px; font-weight: bold; cursor: pointer; }
            input, textarea { padding: 12px; border: 1px solid #ddd; border-radius: 15px; outline: none; }
        </style>
    </head>
    <body>

        <div id="rulesModal" class="modal-overlay">
            <div class="modal-box">
                <h1 style="color: #FF4081;">📜 Reglas LoveConnect</h1>
                <ul style="text-align: left; line-height: 1.8;">
                    <li>✅ Solo mayores de 18 años.</li>
                    <li>✅ Respeto (Sala de Castigo activa).</li>
                    <li>✅ Privacidad responsable.</li>
                </ul>
                <button class="btn-pink" style="width:100%" onclick="goToRegister()">Aceptar y Entrar</button>
            </div>
        </div>

        <div id="profile-reg">
            <h2 style="color: #FF4081; text-align: center;">💖 Registro de Perfil</h2>
            <input type="text" id="regName" placeholder="Nombre completo">
            <input type="number" id="regAge" placeholder="Edad">
            <input type="text" id="regLoc" placeholder="Ubicación (Ej: Zacatecoluca)">
            <textarea id="regBio" placeholder="¿Quién soy?" rows="3"></textarea>
            <button class="btn-pink" onclick="goToApp()">Publicar</button>
        </div>

        <div id="main-app">
            <div class="header">
                <span onclick="showSection('chat')" style="cursor:pointer">💬 Chat</span>
                <span>LoveConnect</span>
                <span onclick="showSection('vote')" style="cursor:pointer">💡 Votar</span>
            </div>

            <div id="chat-room">
                <div id="messages"></div>
                <div style="padding:15px; background:white; display:flex; gap:10px;">
                    <input type="text" id="chatInput" style="flex:1" placeholder="Escribe..." onkeypress="if(event.key==='Enter') send()">
                    <button onclick="send()" style="background:none; border:none; font-size:24px;">🚀</button>
                </div>
            </div>

            <div id="vote-panel">
                <div class="vote-card"><h3>Filtros VIP</h3><span class="vote-link">Votar</span></div>
                <div class="vote-card"><h3>Modo Oscuro</h3><span class="vote-link">Votar</span></div>
                <div class="vote-card"><h3>Chat de Voz</h3><span class="vote-link">Votar</span></div>
                
                <div class="suggest-box">
                    <h3 style="text-align:center">💡 Sugiere algo</h3>
                    <input type="text" id="suggestInput" style="width:90%; margin-bottom:10px" placeholder="Tu propuesta...">
                    <button class="btn-pink" style="width:100%; background:#4A90E2" onclick="alert('¡Gracias por tu sugerencia!')">Enviar</button>
                </div>
            </div>
        </div>

        <script>
            let ws = new WebSocket(`ws://${window.location.host}/ws`);
            let user = "";

            function goToRegister() {
                document.getElementById('rulesModal').style.display = 'none';
                document.getElementById('profile-reg').style.display = 'flex';
            }

            function goToApp() {
                user = document.getElementById('regName').value.trim();
                if(!user) return alert("Ingresa tu nombre");
                document.getElementById('profile-reg').style.display = 'none';
                document.getElementById('main-app').style.display = 'flex';
            }

            function showSection(sec) {
                document.getElementById('chat-room').style.display = sec === 'chat' ? 'flex' : 'none';
                document.getElementById('vote-panel').style.display = sec === 'vote' ? 'block' : 'none';
            }

            ws.onmessage = (e) => {
                let d = document.createElement('div');
                d.className = 'msg';
                d.innerText = e.data;
                document.getElementById('messages').appendChild(d);
                document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
            };

            function send() {
                let i = document.getElementById('chatInput');
                if(i.value.trim()) { ws.send(user + ": " + i.value); i.value = ""; }
            }
        </script>
    </body>
    </html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if any(w in data.lower() for w in PALABRAS_PROHIBIDAS):
                await websocket.send_text("⚠️ SALA DE CASTIGO: Mensaje inapropiado.")
            else:
                await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
