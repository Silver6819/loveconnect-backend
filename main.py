import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- DATOS DE AUTOR ---
ADMIN_NAME = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "¡Lee 'El Espectro Infernal' aquí: https://books2read.com/u/mYG1X0"

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
            .header {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; font-size: 20px; }}
            #chat {{ flex: 1; overflow-y: auto; padding: 15px; background: #ffffff; display: block; }}
            .m {{ background: #f1f1f1; padding: 10px; border-radius: 12px; margin-bottom: 8px; width: fit-content; max-width: 85%; font-size: 15px; color: #333; border: 1px solid #eee; }}
            #ui {{ padding: 10px; background: white; border-top: 2px solid #fff5f7; display: flex; gap: 8px; }}
            input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; }}
            .menu {{ display: flex; justify-content: space-around; background: white; padding: 12px; border-top: 1px solid #eee; }}
            .btn {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 14px; cursor: pointer; }}
            #login {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 9999; }}
        </style>
    </head>
    <body>
        <div id="login">
            <h1 style="color:#FF4081;">💖 LoveConnect</h1>
            <input type="text" id="u" placeholder="Tu Nombre" style="padding:12px; border-radius:10px; border:1px solid #ddd; width: 250px; margin-bottom: 20px;">
            <button onclick="entrar()" style="background:#FF4081; color:white; padding:15px 40px; border:none; border-radius:25px; font-weight:bold;">ENTRAR AL CHAT</button>
        </div>

        <div class="header">💖 LoveConnect</div>
        <div id="chat"></div>
        
        <div id="ui">
            <input type="text" id="m" placeholder="Escribe un mensaje..." onkeypress="if(event.key==='Enter') enviar()">
            <button onclick="enviar()" style="border:none; background:none; font-size:20px;">🚀</button>
        </div>

        <div class="menu">
            <button class="btn" onclick="alert('{OBRA}')">📅 OBRA</button>
            <button class="btn" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
            <button class="btn" onclick="location.reload()">👤 SALIR</button>
        </div>

        <script>
            let socket; let user = "";
            function entrar() {{
                user = document.getElementById('u').value.trim();
                if(!user) return alert("Pon un nombre");
                document.getElementById('login').style.display = 'none';
                conectar();
            }}
            function conectar() {{
                const p = location.protocol === 'https:' ? 'wss:' : 'ws:';
                socket = new WebSocket(p + "//" + location.host + "/ws/" + encodeURIComponent(user));
                socket.onmessage = (e) => {{
                    if(e.data === "CLEAR") {{ document.getElementById('chat').innerHTML = ""; }}
                    else {{
                        const box = document.createElement('div');
                        box.className = 'm';
                        box.textContent = e.data;
                        const c = document.getElementById('chat');
                        c.appendChild(box);
                        c.scrollTop = c.scrollHeight;
                    }}
                }};
                socket.onclose = () => setTimeout(conectar, 2000);
            }}
            function enviar() {{
                const i = document.getElementById('m');
                if(i.value && socket.readyState === 1) {{
                    socket.send(i.value);
                    i.value = "";
                }}
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
                tag = "⭐ [ADMIN]" if user == ADMIN_NAME else user
                await manager.broadcast(f"{{tag}}: {{data}}")
    except WebSocketDisconnect:
        manager.disconnect(user)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
