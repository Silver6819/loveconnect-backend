import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- CONFIGURACIÓN FINAL ---
ADMIN_NAME = "Silver Breaker"
PAYPAL_URL = "https://www.paypal.com/paypalme/silver676"
LIBRO_LINK = "https://books2read.com/u/mYG1X0"
ACTUALIZACION = "Marzo 2026: Lanzamiento de 'El Espectro Infernal' en tiendas internacionales."

class ConnectionManager:
    def __init__(self):
        self.active: dict = {}
    async def connect(self, user: str, ws: WebSocket):
        await ws.accept()
        self.active[user] = ws
    def disconnect(self, user: str):
        if user in self.active: del self.active[user]
    async def broadcast(self, msg: str):
        for ws in list(self.active.values()):
            try: await ws.send_text(msg)
            except: pass

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get():
    return f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LoveConnect</title>
        <style>
            body {{ font-family: sans-serif; margin: 0; background: #fff5f7; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
            .header {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; }}
            #chat {{ flex: 1; overflow-y: auto; padding: 15px; background: #fdfdfd; display: flex; flex-direction: column; gap: 8px; }}
            .m {{ background: white; padding: 10px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); max-width: 85%; word-wrap: break-word; font-size: 14px; }}
            #ui {{ padding: 10px; background: white; display: flex; gap: 5px; border-top: 1px solid #eee; }}
            input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; }}
            .menu {{ display: flex; background: white; border-top: 1px solid #ddd; padding: 10px; justify-content: space-around; }}
            .btn {{ border: none; background: none; color: #FF4081; font-weight: bold; cursor: pointer; }}
            #login {{ position: fixed; top:0; left:0; width:100%; height:100%; background:#fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 2000; text-align: center; }}
        </style>
    </head>
    <body>
        <div id="login">
            <h1 style="color:#FF4081;">💖 LoveConnect</h1>
            <p>Ingresa tu nombre</p>
            <input type="text" id="uName" placeholder="Ej: {ADMIN_NAME}" style="max-width: 250px; margin-bottom: 20px;">
            <button onclick="start()" style="background:#FF4081; color:white; padding:15px 40px; border:none; border-radius:25px; font-weight:bold;">ENTRAR</button>
        </div>

        <div class="header">💖 LoveConnect</div>
        <div id="chat"></div>
        <div id="ui"><input type="text" id="msg" placeholder="Escribe..." onkeypress="if(event.key==='Enter') send()"> <button class="btn" onclick="send()">🚀</button></div>
        
        <div class="menu">
            <button class="btn" onclick="alert('{ACTUALIZACION}\\n\\nCompra aquí: {LIBRO_LINK}')">📅 Obra</button>
            <button class="btn" onclick="window.open('{PAYPAL_URL}')">💳 PayPal</button>
            <button class="btn" onclick="location.reload()">👤 Salir</button>
        </div>

        <script>
            let ws; let user = "";
            function start() {{
                user = document.getElementById('uName').value.trim();
                if(!user) return;
                connect();
            }}
            function connect() {{
                const prot = location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${{prot}}//${{location.host}}/ws/${{encodeURIComponent(user)}}`);
                ws.onopen = () => document.getElementById('login').style.display = 'none';
                ws.onmessage = (e) => {{
                    if(e.data === "CLEAR") {{ document.getElementById('chat').innerHTML = ""; }}
                    else {{
                        let d = document.createElement('div'); d.className = 'm'; d.innerText = e.data;
                        let c = document.getElementById('chat'); c.appendChild(d); c.scrollTop = c.scrollHeight;
                    }}
                }};
                ws.onclose = () => setTimeout(connect, 2000);
            }}
            function send() {{
                let i = document.getElementById('msg');
                if(i.value && ws.readyState === 1) {{ ws.send(i.value); i.value = ""; }}
            }}
        </script>
    </body>
    </html>
    """

@app.websocket("/ws/{{user}}")
async def websocket_endpoint(websocket: WebSocket, user: str):
    await manager.connect(user, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "/limpiar" and user == ADMIN_NAME:
                await manager.broadcast("CLEAR")
            else:
                prefix = "⭐ [ADMIN]" if user == ADMIN_NAME else user
                await manager.broadcast(f"{{prefix}}: {{data}}")
    except WebSocketDisconnect:
        manager.disconnect(user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
