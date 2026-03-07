import os
from typing import List, Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import sqlalchemy
import uvicorn

# --- BASE DE DATOS ---
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

# --- ADMIN Y SEGURIDAD ---
ADMIN_NAME = "Silver Breaker"
PALABRAS_PROHIBIDAS = ["insulto1", "ofensa2", "spam"] 

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user] = websocket

    def disconnect(self, user: str):
        if user in self.active_connections:
            del self.active_connections[user]

    async def broadcast(self, message: str, sender: str):
        display_msg = f"⭐ [ADMIN] {message}" if sender == ADMIN_NAME else message
        for connection in list(self.active_connections.values()):
            try:
                await connection.send_text(display_msg)
            except:
                pass

    async def send_private(self, message: str, target_user: str, sender: str):
        if target_user in self.active_connections:
            msg = f"🔒 [PRIVADO de {sender}]: {message}"
            await self.active_connections[target_user].send_text(msg)
            await self.active_connections[sender].send_text(msg)
        else:
            await self.active_connections[sender].send_text(f"❌ {target_user} no está en línea.")

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
            body { font-family: 'Segoe UI', sans-serif; background: #fff5f7; margin: 0; height: 100vh; display: flex; justify-content: center; align-items: center; }
            .modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); display: flex; justify-content: center; align-items: center; z-index: 3000; }
            .modal-box { background: white; padding: 30px; border-radius: 30px; box-shadow: 0 15px 35px rgba(0,0,0,0.1); width: 85%; max-width: 380px; text-align: center; }
            #profile-reg { display: none; background: white; padding: 30px; border-radius: 30px; width: 90%; max-width: 400px; flex-direction: column; gap: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); }
            .btn-pink { background: #FF4081; color: white; border: none; padding: 15px; border-radius: 15px; font-weight: bold; cursor: pointer; width: 100%; font-size: 18px; }
            #main-app { display: none; width: 100%; height: 100vh; flex-direction: column; background: #f0f2f5; }
            .header { background: white; padding: 15px; text-align: center; font-weight: bold; color: #FF4081; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; }
            #messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 10px; }
            .msg { background: white; padding: 10px 15px; border-radius: 15px; max-width: 80%; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            input, textarea { padding: 12px 20px; border: 1px solid #ddd; border-radius: 15px; outline: none; width: 100%; box-sizing: border-box; }
            #vote-panel { display: none; padding: 20px; flex: 1; overflow-y: auto; }
            .suggest-box { border: 2px dashed #FF4081; padding: 20px; border-radius: 25px; background: white; text-align: center; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div id="rulesModal" class="modal-overlay">
            <div class="modal-box">
                <h2 style="color:#FF4081;">📜 Reglas LoveConnect</h2>
                <ul style="text-align:left; font-size:14px;">
                    <li>✅ Solo mayores de 18 años.</li>
                    <li>✅ Respeto total (Sala de Castigo).</li>
                    <li>✅ Privados: escribe /@nombre mensaje</li>
                </ul>
                <button class="btn-pink" onclick="showRegister()">Aceptar y Entrar</button>
            </div>
        </div>

        <div id="profile-reg">
            <h2 style="color:#FF4081; text-align:center;">💖 Registro de Perfil</h2>
            <input type="text" id="regName" placeholder="Tu Nombre">
            <input type="number" id="regAge" placeholder="Edad">
            <input type="text" id="regLoc" placeholder="Ubicación">
            <textarea id="regBio" placeholder="¿Quién soy?" rows="3"></textarea>
            <button class="btn-pink" id="btnJoin" onclick="startApp()">Publicar y Entrar</button>
        </div>

        <div id="main-app">
            <div class="header">
                <span onclick="toggleView('chat')" style="cursor:pointer">💬 Chat</span>
                <span>LoveConnect</span>
                <span onclick="toggleView('vote')" style="cursor:pointer">💡 Votar</span>
            </div>
            <div id="chat-room" style="display:flex; flex:1; flex-direction:column;">
                <div id="messages"></div>
                <div style="padding:15px; background:white; display:flex; gap:10px;">
                    <input type="text" id="chatInput" placeholder="Escribe aquí..." onkeypress="if(event.key==='Enter') send()">
                    <button onclick="send()" style="background:none; border:none; font-size:24px;">🚀</button>
                </div>
            </div>
            <div id="vote-panel">
                <div class="suggest-box">
                    <h3>💡 Sugiere algo</h3>
                    <input type="text" placeholder="Tu propuesta...">
                    <button class="btn-pink" style="margin-top:10px; background:#4A90E2;">Enviar</button>
                </div>
            </div>
        </div>

        <script>
            let ws;
            let user = "";

            function showRegister() {
                document.getElementById('rulesModal').style.display = 'none';
                document.getElementById('profile-reg').style.display = 'flex';
            }

            function startApp() {
                user = document.getElementById('regName').value.trim();
                if(!user) return alert("Ingresa tu nombre");
                
                document.getElementById('btnJoin').innerText = "Conectando...";

                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const host = window.location.host;
                const wsUrl = `${protocol}//${host}/ws/${encodeURIComponent(user)}`;
                
                try {
                    ws = new WebSocket(wsUrl);

                    ws.onopen = () => {
                        document.getElementById('profile-reg').style.display = 'none';
                        document.getElementById('main-app').style.display = 'flex';
                    };

                    ws.onmessage = (e) => {
                        let d = document.createElement('div');
                        d.className = 'msg';
                        d.innerText = e.data;
                        const msgBox = document.getElementById('messages');
                        msgBox.appendChild(d);
                        msgBox.scrollTop = msgBox.scrollHeight;
                    };

                    ws.onerror = (err) => {
                        document.getElementById('btnJoin').innerText = "Publicar y Entrar";
                        alert("⚠️ Error de conexión. El servidor de Railway está despertando, intenta en 10 segundos.");
                    };
                } catch (e) {
                    alert("Error crítico de WebSocket");
                }
            }

            function toggleView(v) {
                document.getElementById('chat-room').style.display = v === 'chat' ? 'flex' : 'none';
                document.getElementById('vote-panel').style.display = v === 'vote' ? 'block' : 'none';
            }

            function send() {
                let i = document.getElementById('chatInput');
                if(i.value.trim() && ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(i.value);
                    i.value = "";
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
            if any(w in data.lower() for w in PALABRAS_PROHIBIDAS):
                await websocket.send_text("⚠️ Bloqueado por Sala de Castigo.")
            elif data.startswith("/@"):
                try:
                    parts = data.split(" ", 1)
                    target = parts[0][2:]
                    await manager.send_private(parts[1], target, user)
                except:
                    await websocket.send_text("❌ Usa: /@nombre mensaje")
            else:
                await manager.broadcast(f"{user}: {data}", user)
    except WebSocketDisconnect:
        manager.disconnect(user)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
