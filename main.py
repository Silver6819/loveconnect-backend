import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- CONFIGURACIÓN ---
ADMIN_NAME = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "El Espectro Infernal: https://books2read.com/u/mYG1X0"

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LoveConnect</title>
    <style>
        html, body {{ height: 100%; margin: 0; padding: 0; background: #fff5f7; overflow: hidden; }}
        table {{ width: 100%; height: 100%; border-collapse: collapse; table-layout: fixed; }}
        .header {{ height: 60px; background: #FF4081; color: white; text-align: center; font-weight: bold; font-size: 20px; }}
        .chat-area {{ background: white; vertical-align: top; height: auto; }}
        #chat {{ height: 100%; overflow-y: auto; padding: 10px; display: block; }}
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 10px; margin-bottom: 8px; width: fit-content; max-width: 85%; font-family: sans-serif; font-size: 14px; }}
        .input-area {{ height: 60px; background: white; border-top: 1px solid #ddd; padding: 5px; }}
        .footer {{ height: 50px; background: white; border-top: 1px solid #ddd; text-align: center; }}
        input {{ width: 80%; padding: 10px; border-radius: 20px; border: 1px solid #ddd; outline: none; }}
        button {{ border: none; background: none; color: #FF4081; font-weight: bold; cursor: pointer; padding: 10px; }}
        #login {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 1000; }}
    </style>
</head>
<body>
    <div id="login">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="u" placeholder="Tu Nombre" style="width: 200px; margin-bottom: 20px;">
        <button onclick="entrar()" style="background:#FF4081; color:white; border-radius:20px; padding: 10px 30px;">ENTRAR</button>
    </div>

    <table>
        <tr class="header"><td>💖 LoveConnect</td></tr>
        <tr class="chat-area">
            <td>
                <div id="chat"></div>
            </td>
        </tr>
        <tr class="input-area">
            <td>
                <input type="text" id="m" placeholder="Escribe..." onkeypress="if(event.key==='Enter') enviar()">
                <button onclick="enviar()">🚀</button>
            </td>
        </tr>
        <tr class="footer">
            <td>
                <button onclick="alert('{OBRA}')">📅 OBRA</button>
                <button onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
                <button onclick="location.reload()">👤 SALIR</button>
            </td>
        </tr>
    </table>

    <script>
        let socket; let user = "";
        function entrar() {{
            user = document.getElementById('u').value.trim();
            if(!user) return;
            document.getElementById('login').style.display = 'none';
            conectar();
        }}
        function conectar() {{
            const p = location.protocol === 'https:' ? 'wss:' : 'ws:';
            socket = new WebSocket(p + "//" + location.host + "/ws/" + encodeURIComponent(user));
            socket.onmessage = (e) => {{
                if(e.data === "CLEAR") {{ document.getElementById('chat').innerHTML = ""; }}
                else {{
                    const d = document.createElement('div');
                    d.className = 'm'; d.textContent = e.data;
                    const c = document.getElementById('chat');
                    c.appendChild(d); c.scrollTop = c.scrollHeight;
                }}
            }};
            socket.onclose = () => setTimeout(conectar, 2000);
        }}
        function enviar() {{
            const i = document.getElementById('m');
            if(i.value && socket && socket.readyState === 1) {{
                socket.send(i.value); i.value = "";
            }} else if (i.value) {{
                conectar();
                setTimeout(() => {{ if(socket.readyState===1) {{ socket.send(i.value); i.value=""; }} }}, 500);
            }}
        }}
    </script>
</body>
</html>
"""

class ConnectionManager:
    def __init__(self): self.active = {}
    async def connect(self, user, ws): await ws.accept(); self.active[user] = ws
    def disconnect(self, user):
        if user in self.active: del self.active[user]
    async def broadcast(self, msg):
        for ws in list(self.active.values()):
            try: await ws.send_text(msg)
            except: pass

manager = ConnectionManager()

@app.get("/")
async def get(): return HTMLResponse(content=html_content)

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
    except WebSocketDisconnect: manager.disconnect(user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
