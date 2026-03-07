import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- CONFIGURACIÓN ---
ADMIN_NAME = "Silver Breaker"
VERSION_MENSUAL = "Marzo 2026: Lanzamiento de 'El Espectro Infernal' en tiendas internacionales."

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, user: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user] = websocket

    def disconnect(self, user: str):
        if user in self.active_connections:
            del self.active_connections[user]

    async def broadcast(self, message: str, sender: str):
        display_msg = f"⭐ [ADMIN] {message}" if sender == ADMIN_NAME else message
        for connection in list(self.active_connections.values()):
            try: await connection.send_text(display_msg)
            except: pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LoveConnect</title>
        <style>
            body {{ font-family: sans-serif; background: #fff5f7; margin: 0; display: flex; flex-direction: column; height: 100vh; }}
            .header {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; }}
            #chat {{ flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 8px; }}
            .msg {{ background: white; padding: 10px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); width: fit-content; max-width: 85%; }}
            .menu-bar {{ display: flex; background: white; border-top: 1px solid #ddd; padding: 10px; justify-content: space-around; }}
            .btn {{ border: none; background: none; color: #FF4081; font-weight: bold; cursor: pointer; }}
            #input-area {{ padding: 10px; background: white; display: flex; gap: 5px; }}
            input {{ flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none; }}
            .modal {{ position: fixed; top:0; left:0; width:100%; height:100%; background:white; display: none; flex-direction: column; padding: 20px; box-sizing: border-box; z-index: 1000; }}
            #login-screen {{ position: fixed; top:0; left:0; width:100%; height:100%; background:#fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 2000; padding: 20px; text-align: center; }}
        </style>
    </head>
    <body>
        <div id="login-screen">
            <h1 style="color:#FF4081;">💖 LoveConnect</h1>
            <p>Ingresa tu nombre para entrar al chat</p>
            <input type="text" id="uName" placeholder="Nombre (ej: Silver Breaker)" style="max-width: 300px; margin-bottom: 20px;">
            <button class="btn" style="background:#FF4081; color:white; padding:15px 40px; border-radius:25px;" onclick="enterApp()">Entrar al Perfil</button>
        </div>

        <div class="header">💖 LoveConnect</div>
        <div id="chat"></div>
        
        <div id="input-area">
            <input type="text" id="m" placeholder="Escribe algo..." onkeypress="if(event.key==='Enter') send()">
            <button class="btn" onclick="send()">🚀</button>
        </div>

        <div class="menu-bar">
            <button class="btn" onclick="show('chat')">💬 Chat</button>
            <button class="btn" onclick="show('news')">📅 Updates</button>
            <button class="btn" onclick="show('suggest')">💡 Pedir</button>
            <button class="btn" onclick="location.reload()">👤 Salir</button>
        </div>

        <div id="news" class="modal">
            <h2>📅 Actualización Mensual</h2>
            <p>{VERSION_MENSUAL}</p>
            <button class="btn" onclick="show('chat')">Volver al Chat</button>
        </div>

        <div id="suggest" class="modal">
            <h2>💡 Sugerencias</h2>
            <textarea id="sugText" style="width:100%; height:100px; border-radius:10px; padding:10px;"></textarea>
            <button class="btn" onclick="sendSuggest()">Enviar Propuesta</button>
            <button class="btn" onclick="show('chat')">Volver</button>
        </div>

        <script>
            let ws;
            let user = "";
            
            function enterApp() {{
                user = document.getElementById('uName').value.trim();
                if(!user) return alert("Escribe un nombre");
                
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${{protocol}}//${{window.location.host}}/ws/${{encodeURIComponent(user)}}`);
                
                ws.onopen = () => {{
                    document.getElementById('login-screen').style.display = 'none';
                }};
                
                ws.onmessage = (e) => {{
                    let d = document.createElement('div');
                    d.className = 'msg';
                    d.innerText = e.data;
                    document.getElementById('chat').appendChild(d);
                    document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
                }};
                
                ws.onerror = () => alert("Conectando... espera 5s y reintenta.");
            }}

            function send() {{
                let i = document.getElementById('m');
                if(i.value && ws.readyState === 1) {{ ws.send(i.value); i.value = ""; }}
            }}

            function sendSuggest() {{
                let s = document.getElementById('sugText');
                if(s.value && ws.readyState === 1) {{ 
                    ws.send("💡 SUGERENCIA: " + s.value); 
                    s.value = ""; 
                    show('chat');
                    alert("¡Propuesta enviada!");
                }}
            }}

            function show(id) {{
                document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
                if(id !== 'chat') document.getElementById(id).style.display = 'flex';
            }}
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
            await manager.broadcast(f"{user}: {data}", user)
    except WebSocketDisconnect:
        manager.disconnect(user)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
