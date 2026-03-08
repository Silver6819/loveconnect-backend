import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "https://books2read.com/u/mYG1X0"

html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>LoveConnect</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; background: #fff5f7; font-family: sans-serif; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}
        .header {{ background: #FF4081; color: white; height: 50px; line-height: 50px; text-align: center; font-weight: bold; flex-shrink: 0; }}
        #chat {{ flex: 1; overflow-y: scroll; background: white; padding: 10px; display: block; border-bottom: 1px solid #eee; }}
        .msg-box {{ background: #f1f1f1; padding: 8px 12px; border-radius: 15px; margin-bottom: 8px; width: fit-content; max-width: 85%; font-size: 14px; color: #333; }}
        .input-bar {{ height: 70px; background: white; display: flex; align-items: center; padding: 0 10px; gap: 8px; flex-shrink: 0; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; font-size: 16px; }}
        .send-btn {{ border: none; background: #FF4081; color: white; border-radius: 50%; width: 45px; height: 45px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 20px; }}
        .footer {{ height: 50px; background: white; display: flex; justify-content: space-around; align-items: center; border-top: 1px solid #eee; flex-shrink: 0; }}
        .nav-btn {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 12px; cursor: pointer; }}
        #login {{ position: fixed; inset: 0; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 999; }}
    </style>
</head>
<body>
    <div id="login">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="user" placeholder="Tu Nombre" style="max-width:200px; margin-bottom:15px; border-radius:10px;">
        <button onclick="start()" style="background:#FF4081; color:white; border:none; padding:12px 40px; border-radius:25px; font-weight:bold;">ENTRAR</button>
    </div>
    <div class="header">💖 LoveConnect</div>
    <div id="chat"></div>
    <div class="input-bar">
        <input type="text" id="msg" placeholder="Escribe..." onkeypress="if(event.key==='Enter') send()">
        <button class="send-btn" onclick="send()">🚀</button>
    </div>
    <div class="footer">
        <button class="nav-btn" onclick="alert('Lee mi obra aquí: {OBRA}')">📅 MI OBRA</button>
        <button class="nav-btn" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
        <button class="nav-btn" onclick="location.reload()">👤 SALIR</button>
    </div>
    <script>
        let ws; let nick = "";
        function start() {{
            const val = document.getElementById('user').value.trim();
            nick = val || "Usuario";
            document.getElementById('login').style.display = 'none';
            connect();
        }}
        function connect() {{
            const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(proto + "//" + location.host + "/ws/" + encodeURIComponent(nick));
            ws.onmessage = (e) => {{
                if(e.data === "CLR") document.getElementById('chat').innerHTML = "";
                else {{
                    const d = document.createElement('div'); d.className='msg-box'; d.textContent=e.data;
                    const c = document.getElementById('chat'); c.appendChild(d); c.scrollTop = c.scrollHeight;
                }}
            }};
            ws.onclose = () => setTimeout(connect, 1500);
        }}
        function send() {{
            const i = document.getElementById('msg');
            if(i.value && ws && ws.readyState === 1) {{ ws.send(i.value); i.value = ""; }}
            else if(i.value) {{ connect(); setTimeout(() => {{ if(ws.readyState===1) {{ ws.send(i.value); i.value=""; }} }}, 500); }}
        }}
    </script>
</body>
</html>
"""

class Manager:
    def __init__(self): self.clients = {}
    async def connect(self, u, w): await w.accept(); self.clients[u] = w
    def disconnect(self, u):
        if u in self.clients: del self.clients[u]
    async def broadcast(self, m):
        for w in list(self.clients.values()):
            try: await w.send_text(m)
            except: pass

m = Manager()
@app.get("/")
async def get(): return HTMLResponse(html)

@app.websocket("/ws/{{u}}")
async def ws_endpoint(websocket: WebSocket, u: str):
    await m.connect(u, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "/limpiar" and u == ADMIN: await m.broadcast("CLR")
            else: await m.broadcast(f"{{'⭐ [ADMIN]' if u==ADMIN else u}}: {{data}}")
    except: m.disconnect(u)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
