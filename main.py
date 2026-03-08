import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- CONFIGURACIÓN ---
ADMIN_NAME = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "El Espectro Infernal: https://books2read.com/u/mYG1X0"

# HTML en una variable simple para evitar errores de lectura
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LoveConnect</title>
    <style>
        body {{ font-family: sans-serif; margin: 0; background: #fff5f7; display: flex; flex-direction: column; height: 100vh; }}
        .header {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; }}
        #chat {{ flex: 1; overflow-y: auto; padding: 15px; background: white; }}
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 10px; margin-bottom: 8px; width: fit-content; max-width: 80%; font-size: 14px; }}
        #ui {{ padding: 10px; background: white; display: flex; gap: 5px; border-top: 1px solid #eee; }}
        .menu {{ display: flex; justify-content: space-around; background: white; padding: 10px; border-top: 1px solid #ddd; }}
        button {{ border: none; background: none; color: #FF4081; font-weight: bold; cursor: pointer; }}
        #login {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 100; }}
    </style>
</head>
<body>
    <div id="login">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="user" placeholder="Tu Nombre" style="padding:12px; border-radius:10px; border:1px solid #ddd; margin-bottom:15px; width:200px;">
        <button onclick="start()" style="background:#FF4081; color:white; padding:15px 30px; border-radius:20px;">ENTRAR</button>
    </div>
    <div class="header">💖 LoveConnect</div>
    <div id="chat"></div>
    <div id="ui">
        <input type="text" id="msg" style="flex:1; padding:10px; border-radius:20px; border:1px solid #ddd;" onkeypress="if(event.key==='Enter') send()">
        <button onclick="send()">🚀</button>
    </div>
    <div class="menu">
        <button onclick="alert('{OBRA}')">📅 Obra</button>
        <button onclick="window.open('{PAYPAL}')">💳 PayPal</button>
        <button onclick="location.reload()">👤 Salir</button>
    </div>
    <script>
        let ws; let nick = "";
        function start() {{
            nick = document.getElementById('user').value.trim();
            if(!nick) return;
            document.getElementById('login').style.display = 'none';
            const prot = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(prot + "//" + location.host + "/ws/" + encodeURIComponent(nick));
            ws.onmessage = (e) => {{
                if(e.data === "CLEAR") {{ document.getElementById('chat').innerHTML = ""; }}
                else {{
                    let d = document.createElement('div'); d.className='m'; d.innerText=e.data;
                    let c = document.getElementById('chat'); c.appendChild(d); c.scrollTop = 99999;
                }}
            }};
            ws.onclose = () => setTimeout(start, 2000);
        }}
        function send() {{
            let i = document.getElementById('msg');
            if(i.value && ws && ws.readyState === 1) {{ ws.send(i.value); i.value = ""; }}
        }}
    </script>
</body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active = {}
    async def connect(self, user, ws):
        await ws.accept()
        self.active[user] = ws
    def disconnect(self, user):
        if user in self.active: del self.active[user]
    async def broadcast(self, msg):
        for ws in list(self.active.values()):
            try: await ws.send_text(msg)
            except: pass

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(content=html_content)

@app.websocket("/ws/{{user}}")
async def websocket_endpoint(websocket: WebSocket, user: str):
    await manager.connect(user, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "/limpiar" and user == ADMIN_NAME:
                await manager.broadcast("CLEAR")
            else:
                tag = "⭐ [ADMIN]" if user == ADMIN_NAME else user
                await manager.broadcast(f"{{tag}}: {{data}}")
    except WebSocketDisconnect:
        manager.disconnect(user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
