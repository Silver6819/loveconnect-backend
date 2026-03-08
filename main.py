import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "https://books2read.com/u/mYG1X0"

html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <title>LoveConnect</title>
    <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body, html {{ height: 100%; margin: 0; background: #fff5f7; font-family: sans-serif; overflow: hidden; position: fixed; width: 100%; }}
        .app-container {{ display: flex; flex-direction: column; height: 100vh; height: -webkit-fill-available; }}
        .h {{ background: #FF4081; color: white; height: 50px; line-height: 50px; text-align: center; font-weight: bold; flex-shrink: 0; }}
        #c {{ flex: 1; overflow-y: auto; background: white; padding: 10px; }}
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 15px; margin-bottom: 8px; width: fit-content; max-width: 85%; font-size: 14px; color: #333; }}
        .u {{ background: white; padding: 10px; border-top: 1px solid #eee; display: flex; gap: 10px; flex-shrink: 0; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; font-size: 16px; }}
        .s {{ border: none; background: #FF4081; color: white; border-radius: 50%; width: 45px; height: 45px; cursor: pointer; font-size: 20px; }}
        .f {{ background: white; display: flex; justify-content: space-around; padding: 10px; border-top: 1px solid #eee; flex-shrink: 0; }}
        .b {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 12px; }}
        #l {{ position: fixed; inset: 0; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 999; }}
    </style>
</head>
<body>
    <div id="l">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="user" placeholder="Tu Nombre" style="max-width:200px; margin-bottom:15px; border-radius:10px;">
        <button onclick="start()" style="background:#FF4081; color:white; border:none; padding:12px 40px; border-radius:25px; font-weight:bold;">ENTRAR</button>
    </div>
    <div class="app-container">
        <div class="h">💖 LoveConnect</div>
        <div id="c"></div>
        <div class="u">
            <input type="text" id="msg" placeholder="Escribe..." autocomplete="off">
            <button class="s" onclick="send()">🚀</button>
        </div>
        <div class="f">
            <button class="b" onclick="alert('{OBRA}')">📅 MI OBRA</button>
            <button class="b" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
            <button class="b" onclick="location.reload()">👤 SALIR</button>
        </div>
    </div>
    <script>
        let ws; let nick = "";
        const chat = document.getElementById('c');
        const input = document.getElementById('msg');

        function start() {{
            nick = document.getElementById('user').value.trim() || "Usuario";
            document.getElementById('l').style.display = 'none';
            connect();
        }}

        function connect() {{
            const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(proto + "//" + location.host + "/ws/" + encodeURIComponent(nick));
            ws.onmessage = (e) => {{
                if(e.data === "CLR") chat.innerHTML = "";
                else {{
                    const d = document.createElement('div'); d.className='m'; d.textContent=e.data;
                    chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
                }}
            }};
            ws.onclose = () => setTimeout(connect, 1000);
        }}

        function send() {{
            const val = input.value.trim();
            if(val && ws && ws.readyState === 1) {{
                ws.send(val);
                input.value = "";
                input.focus();
            }}
        }}

        input.addEventListener("keypress", (e) => {{ if(e.key === "Enter") send(); }});
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
