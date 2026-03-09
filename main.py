import os, uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()
ADMIN = "Silver Breaker"
PAYPAL = "https://www.paypal.com/paypalme/silver676"
OBRA = "https://books2read.com/u/mYG1X0"

html = f"""
<!DOCTYPE html>
<html style="height:100%; overflow:hidden;">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0">
    <style>
        * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
        body {{ margin: 0; background: #fff5f7; font-family: sans-serif; height: 100%; display: flex; flex-direction: column; }}
        .h {{ background: #FF4081; color: white; padding: 15px; text-align: center; font-weight: bold; flex-shrink: 0; }}
        #c {{ flex: 1; overflow-y: auto; background: white; padding: 15px; -webkit-overflow-scrolling: touch; }}
        .m {{ background: #f1f1f1; padding: 10px; border-radius: 12px; margin-bottom: 10px; max-width: 85%; font-size: 14px; width: fit-content; }}
        .u {{ padding: 10px; background: white; border-top: 1px solid #eee; display: flex; gap: 8px; flex-shrink: 0; align-items: center; }}
        input {{ flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 20px; outline: none; font-size: 16px; }}
        .s {{ border: none; background: #FF4081; color: white; border-radius: 10px; min-width: 80px; height: 45px; cursor: pointer; font-weight: bold; box-shadow: 0 4px #c2185b; }}
        .s:active {{ box-shadow: 0 0 #c2185b; transform: translateY(4px); }}
        .n {{ display: flex; justify-content: space-around; background: white; padding: 10px; border-top: 1px solid #eee; flex-shrink: 0; }}
        .b {{ border: none; background: none; color: #FF4081; font-weight: bold; font-size: 11px; }}
        #l {{ position: fixed; inset: 0; background: #fff5f7; display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 1000; }}
    </style>
</head>
<body>
    <div id="l">
        <h2 style="color:#FF4081">💖 LoveConnect</h2>
        <input type="text" id="un" placeholder="Tu Nombre" style="max-width:200px; margin-bottom:15px; padding:12px; border-radius:10px; border:1px solid #ddd;">
        <button onclick="st()" style="background:#FF4081; color:white; border:none; padding:12px 40px; border-radius:25px; font-weight:bold;">ENTRAR</button>
    </div>
    <div class="h">💖 LoveConnect</div>
    <div id="c"></div>
    <div class="u">
        <input type="text" id="mi" placeholder="Escribe..." autocomplete="off">
        <button type="button" class="s" id="sendBtn">ENVIAR</button>
    </div>
    <div class="n">
        <button class="b" onclick="alert('Obra: {OBRA}')">📅 MI OBRA</button>
        <button class="b" onclick="window.open('{PAYPAL}')">💳 PAYPAL</button>
        <button class="b" onclick="location.reload()">👤 SALIR</button>
    </div>
    <script>
        let ws; let nick = "";
        const chat = document.getElementById('c');
        const inp = document.getElementById('mi');
        const btn = document.getElementById('sendBtn');

        function st() {{
            nick = document.getElementById('un').value.trim() || "Usuario";
            document.getElementById('l').style.display = 'none';
            co();
        }}

        function co() {{
            const p = location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(p + "//" + location.host + "/ws/" + encodeURIComponent(nick));
            ws.onmessage = (e) => {{
                let d = document.createElement('div'); d.className = 'm'; d.textContent = e.data;
                chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
            }};
            ws.onclose = () => setTimeout(co, 1000);
        }}

        // LIMPIEZA INTERNA DEL BOTÓN: Evento puro sin intermediarios
        btn.onclick = () => {{
            const val = inp.value.trim();
            if (val && ws && ws.readyState === 1) {{
                ws.send(val);
                inp.value = "";
                inp.focus();
            }}
        }};

        inp.onkeypress = (e) => {{ if(e.key === "Enter") btn.click(); }};
    </script>
</body>
</html>
"""

# MOTOR DE SERVIDOR SIMPLIFICADO
clients = []

@app.get("/")
async def get(): return HTMLResponse(html)

@app.websocket("/ws/{{u}}")
async def ws(websocket: WebSocket, u: str):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            tag = "⭐ [ADMIN]" if u == ADMIN else u
            msg = f"{{tag}}: {{data}}"
            # Enviar a todos los conectados de forma limpia
            for client in list(clients):
                try: await client.send_text(msg)
                except: clients.remove(client)
    except:
        if websocket in clients: clients.remove(websocket)

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=puerto)
