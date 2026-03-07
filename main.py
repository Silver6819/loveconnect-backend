import os
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import HTMLResponse
import sqlalchemy

# --- CONFIGURACIÓN DE BASE DE DATOS (SQLite Ligera) ---
DB_URL = "sqlite:///./love.db"
engine = sqlalchemy.create_engine(DB_URL, connect_args={"check_same_thread": False})
metadata = sqlalchemy.MetaData()

msg_t = sqlalchemy.Table(
    "m", metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("u", sqlalchemy.String(50)),
    sqlalchemy.Column("t", sqlalchemy.String(500))
)
metadata.create_all(engine)

app = FastAPI()

# --- GESTOR DE CONEXIONES EN TIEMPO REAL ---
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

# --- RUTA PRINCIPAL (Interfaz con Diseño Premium) ---
@app.get("/", response_class=HTMLResponse)
async def get():
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LoveConnect Live</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; height: 100vh; display: flex; flex-direction: column; }
            
            /* MODAL CON EFECTO BLUR (Estilo tu captura reciente) */
            .modal-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
                display: flex; justify-content: center; align-items: center; z-index: 2000;
            }
            .modal-box {
                background: white; padding: 35px; border-radius: 25px;
                box-shadow: 0 15px 35px rgba(0,0,0,0.1); text-align: center; width: 85%; max-width: 380px;
            }
            .modal-box h1 { color: #FF4081; font-size: 22px; margin-bottom: 15px; }
            .modal-box ul { text-align: left; color: #444; margin-bottom: 25px; line-height: 1.8; }
            
            /* BOTÓN ROSA (Estilo implementado anteriormente) */
            .btn-pink {
                background: #FF4081; color: white; border: none; width: 100%;
                padding: 15px; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 16px;
            }

            /* INTERFAZ DE CHAT */
            #chat-container { flex: 1; display: flex; flex-direction: column; padding: 20px; overflow-y: auto; }
            .message { background: white; padding: 10px 15px; border-radius: 15px; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); max-width: 80%; }
            .input-area { padding: 15px; background: white; display: flex; gap: 10px; border-top: 1px solid #ddd; }
            input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; }
        </style>
    </head>
    <body>
        <div id="rulesModal" class="modal-overlay">
            <div class="modal-box">
                <h1>📜 Reglas LoveConnect</h1>
                <ul>
                    <li>✅ Solo para mayores de 18 años.</li>
                    <li>✅ Respeto total (Sala de Castigo activa).</li>
                    <li>✅ Privacidad responsable.</li>
                </ul>
                <button class="btn-pink" onclick="acceptRules()">Aceptar y Entrar</button>
            </div>
        </div>

        <div id="chat-container"></div>

        <div class="input-area">
            <input type="text" id="messageText" placeholder="Escribe un mensaje..." autocomplete="off">
            <button onclick="sendMessage()" style="background:none; border:none; font-size:24px; cursor:pointer;">🚀</button>
        </div>

        <script>
            let ws = new WebSocket(`ws://${window.location.host}/ws`);
            let username = "Usuario_" + Math.floor(Math.random() * 1000);

            function acceptRules() {
                document.getElementById('rulesModal').style.display = 'none';
            }

            ws.onmessage = function(event) {
                let container = document.getElementById('chat-container');
                let msgDiv = document.createElement('div');
                msgDiv.className = 'message';
                msgDiv.innerText = event.data;
                container.appendChild(msgDiv);
                container.scrollTop = container.scrollHeight;
            };

            function sendMessage() {
                let input = document.getElementById("messageText");
                if(input.value.trim() !== "") {
                    ws.send(`${username}: ${input.value}`);
                    input.value = '';
                }
            }
        </script>
    </body>
    </html>
    """

# --- ENDPOINT PARA TIEMPO REAL (WebSockets) ---
@app.websocket("/ws")
async def websocket_
