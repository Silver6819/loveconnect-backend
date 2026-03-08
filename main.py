import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

# --- CONFIGURACIÓN ---
ADMIN_NAME = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "¡Lee 'El Espectro Infernal' aquí: https://books2read.com/u/mYG1X0"

html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>LoveConnect</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: sans-serif; margin: 0; background: #fff5f7; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}
        .header {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; flex-shrink: 0; }}
        
        /* Contenedor de chat con altura fija para evitar que se ponga en blanco */
        #chat {{ flex: 1; overflow-y: auto; padding: 15px; background: white; display: flex; flex-direction: column; gap: 10px; }}
        
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 12px; width: fit-content; max-width: 85%; font-size: 14px; word-wrap: break-word; }}
        
        #ui {{ padding: 10px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; flex-shrink: 0; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; font-size: 16px; }}
        
        .menu {{ display: flex; justify-content: space-around; background: white; padding: 12px; border-top: 1px solid #eee; flex-shrink: 0; }}
        .btn {{ border: none; background: none; color: #FF4081; font-weight: bold; cursor: pointer; text-decoration: none; font-size: 14px; }}
        
        #login {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 9999; }}
    </style>
</head>
<body>
    <div id="login">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="u" placeholder="Tu Nombre" style="padding:12px; border-radius:10px; border:1px solid #ddd; width: 220px; margin-bottom: 15px;">
        <button onclick="entrar()" style="background:#FF4081; color:white; padding:15px 40px; border:none; border-radius:25px; font-weight:bold; cursor:pointer;">ENTRAR</button>
    </div>

    <div class="header">💖 LoveConnect</div>
    <div id="chat"></div>
    
    <div id="ui">
        <input type="text" id="m" placeholder="Escribe un mensaje..." onkeypress="if(event.key==='Enter') enviar()">
        <button onclick="enviar()" style="background:none; border:none; font-size:24px; cursor:pointer;">🚀</button>
    </div>

    <div class="menu">
        <button class="btn" onclick="alert('{OBRA}')">📅 OBRA</button>
        <button class="btn" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
        <button class="btn" onclick="location.reload()">👤 SALIR</button>
    </div>

    <script>
        let socket; let user = "";
        const chatDiv = document.getElementById('chat');

        function entrar() {{
            user = document.getElementById('u').value.trim();
            if(!user) return alert("Escribe tu nombre");
            document.getElementById('login').style.display = 'none';
            conectar();
        }}

        function conectar() {{
            const p = location.protocol === 'https:' ? 'wss:' : 'ws:';
            socket = new WebSocket(p + "//" + location.host + "/ws/" + encodeURIComponent(user));
            
            socket.onmessage = (e) => {{
                if(e.data === "CLEAR") {{
                    chatDiv.innerHTML = "";
                }} else {{
                    const box = document.createElement('div');
                    box.className = 'm';
                    box.textContent = e.data;
                    chatDiv.appendChild(box);
                    chatDiv.scrollTop = chatDiv.scrollHeight;
                }}
            }};
            
            socket.onclose = () => setTimeout(conectar, 2000);
        }}

        function enviar() {{
            const i = document.getElementById('m');
            if(!i.value) return;
            
            if(!socket || socket.readyState !== 1) {{
                conectar();
                // Intento rápido de envío tras reconexión
                setTimeout(() => {{ if(socket.readyState === 1) {{ socket.send(i.value); i.value = ""; }} }}, 500);
            }} else {{
                socket.send(i.value);
                i.value = "";
            }}
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
