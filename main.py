import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
# Configuración original de Silver Breaker
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "https://books2read.com/u/mYG1X0"

html_final = f"""
<!DOCTYPE html>
<html style="height:100%; overflow:hidden;">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body {{ margin: 0; background: #fff5f7; font-family: sans-serif; height: 100%; display: flex; flex-direction: column; }}
        .header {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; flex-shrink: 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        #chat_area {{ flex: 1; overflow-y: auto; background: white; padding: 15px; display: flex; flex-direction: column; }}
        .msg {{ background: #f1f1f1; padding: 10px 15px; border-radius: 18px; margin-bottom: 8px; max-width: 85%; font-size: 15px; width: fit-content; line-height: 1.4; }}
        .input_bar {{ padding: 10px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; flex-shrink: 0; align-items: center; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 25px; outline: none; font-size: 16px; background: #fafafa; }}
        .btn_send {{ border: none; background: #FF4081; color: white; border-radius: 12px; min-width: 85px; height: 45px; cursor: pointer; font-weight: bold; box-shadow: 0 4px #c2185b; transition: 0.1s; }}
        .btn_send:active {{ box-shadow: 0 0 #c2185b; transform: translateY(4px); }}
        .nav {{ display: flex; justify-content: space-around; background: white; padding: 10px; border-top: 1px solid #eee; flex-shrink: 0; }}
        .nav_btn {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 11px; text-transform: uppercase; }}
        #splash {{ position: fixed; inset: 0; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 1000; }}
    </style>
</head>
<body>
    <div id="splash">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="nick" placeholder="Tu Nombre" style="max-width:200px; margin-bottom:15px; padding:12px; border-radius:12px; border:1px solid #ddd; text-align:center;">
        <button onclick="entrar()" style="background:#FF4081; color:white; border:none; padding:12px 50px; border-radius:30px; font-weight:bold; font-size:16px;">ENTRAR</button>
    </div>
    <div class="header">💖 LoveConnect</div>
    <div id="chat_area"></div>
    <div class="input_bar">
        <input type="text" id="mensaje" placeholder="Escribe un mensaje..." autocomplete="off">
        <button type="button" class="btn_send" onclick="enviar()">ENVIAR</button>
    </div>
    <div class="nav">
        <button class="nav_btn" onclick="alert('Obra: {OBRA}')">📖 MI OBRA</button>
        <button class="nav_btn" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
        <button class="nav_btn" onclick="location.reload()">👤 SALIR</button>
    </div>
    <script>
        let ws; let miNick = "";
        const chat = document.getElementById('chat_area');
        const inp = document.getElementById('mensaje');

        function entrar() {{
            miNick = document.getElementById('nick').value.trim() || "Usuario";
            document.getElementById('splash').style.display = 'none';
            conectar();
        }}
        function conectar() {{
            const p = location.protocol === 'https:' ? 'wss:' : 'ws:';
            // USAMOS RUTA VIRGEN: /chat_final para evitar el bloqueo anterior
            ws = new WebSocket(p + "//" + location.host + "/chat_final/" + encodeURIComponent(miNick));
            ws.onmessage = (e) => {{
                let d = document.createElement('div'); d.className = 'msg'; d.textContent = e.data;
                chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
            }};
            ws.onclose = () => setTimeout(conectar, 1500);
        }}
        function enviar() {{
            if (inp.value.trim() && ws && ws.readyState === 1) {{
                ws.send(inp.value.trim());
                inp.value = "";
                inp.focus();
            }}
        }}
        inp.onkeypress = (e) => {{ if(e.key === "Enter") enviar(); }};
    </script>
</body>
</html>
"""

# MOTOR DE CHAT REFORZADO
class Lobby:
    def __init__(self): self.users = []
    async def add(self, w): await w.accept(); self.users.append(w)
    def remove(self, w): 
        if w in self.users: self.users.remove(w)
    async def broadcast(self, m):
        for w in list(self.users):
            try: await w.send_text(m)
            except: self.remove(w)

lobby = Lobby()

@app.get("/")
async def get_index(): return HTMLResponse(html_final)

@app.websocket("/chat_final/{{u}}")
async def socket_chat(websocket: WebSocket, u: str):
    await lobby.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            tag = "⭐ [ADMIN]" if u == ADMIN else u
            await lobby.broadcast(f"{{tag}}: {{data}}")
    except: lobby.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
