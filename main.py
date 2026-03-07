import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
ADMIN_NAME = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "El Espectro Infernal: https://books2read.com/u/mYG1X0"

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
            body {{ font-family: sans-serif; margin: 0; background: #fff5f7; display: flex; flex-direction: column; height: 100vh; }}
            #chat {{ flex: 1; overflow-y: auto; padding: 10px; }}
            .m {{ background: white; padding: 8px; border-radius: 10px; margin-bottom: 5px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); width: fit-content; max-width: 90%; }}
            #ui {{ padding: 10px; background: white; border-top: 1px solid #ddd; display: flex; gap: 5px; }}
            .menu {{ display: flex; justify-content: space-around; background: white; padding: 10px; border-top: 1px solid #ddd; }}
            button {{ border: none; background: none; color: #FF4081; font-weight: bold; cursor: pointer; }}
            #login {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 100; }}
        </style>
    </head>
    <body>
        <div id="login">
            <h2 style="color:#FF4081">💖 LoveConnect</h2>
            <input type="text" id="user" placeholder="Tu Nombre" style="padding:10px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px;">
            <button onclick="start()" style="background:#FF4081; color:white; padding:10px 20px; border-radius:20px;">Entrar</button>
        </div>
        <div id="chat"></div>
        <div id="ui"><input type="text" id="msg" style="flex:1; padding:8px; border-radius:15px; border:1px solid #ddd;" onkeypress="if(event.key==='Enter') send()"> <button onclick="send()">🚀</button></div>
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
                ws = new WebSocket(`${{location.protocol==='https:'?'wss:':'ws:'}}//${{location.host}}/ws/${{encodeURIComponent(nick)}}`);
                ws.onopen = () => document.getElementById('login').style.display = 'none';
                ws.onmessage = (e) => {{
                    if(e.data === "CLEAR") {{ document.getElementById('chat').innerHTML = ""; }}
                    else {{ let d = document.createElement('div'); d.className='m'; d.innerText=e.data; document.getElementById('chat').appendChild(d); document.getElementById('chat').scrollTop=99999; }}
                }};
                ws.onerror = () => alert("Reconectando...");
            }}
            function send() {{ let i=document.getElementById('msg'); if(i.value && ws.readyState===1) {{ ws.send(i.value); i.value=""; }} }}
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
